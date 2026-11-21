#!/usr/bin/env python3
"""Independent second implementation (key2) of GATES.md G3 items 1-3 + G4 command chatter."""
import sys, json, os, glob
import numpy as np
FS = 800.0
DSHOT_STEP = 5e-4  # Q14 A: line RMS floor = one DShot step (full scale 1)
LAND_NAV = (5, 18, 20)   # vehicle_status nav_state: AUTO_RTL, AUTO_LAND, AUTO_PRECLAND
NAV_SKIP_S = 3.0   # Q15 A: skip detector windows overlapping this long after a nav_state change
RATIO = 20.0   # peak / band-median threshold (spec); --break raises it to prove the self-test bites

def grid(t, y, fs=FS):
    """Resample onto a uniform grid (t in s, y shape (n,) or (n,k))."""
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    y = np.atleast_2d(y.T).T if y.ndim == 1 else y
    return tg, np.stack([np.interp(tg, t, y[:, i]) for i in range(y.shape[1])], 1)

def psd_windows(x, fs, f0, f1, win=4.0, step=1.0, rms_hz=None, t_off=0.0, skip=(), skipped=None):
    """Yield (t_start, f_peak, ratio, rms_at_peak) per window: Hann PSD, one peak = band maximum."""
    n, h = int(win * fs), int(step * fs); w = np.hanning(n); df = fs / n
    f = np.fft.rfftfreq(n, 1 / fs); b = np.where((f >= f0) & (f <= f1))[0]
    hb = 2 if rms_hz is None else int(round(rms_hz / df)); out = []
    for s in range(0, len(x) - n + 1, h):
        ta = t_off + s / fs   # absolute window span [ta, ta+win] vs skip intervals (t_change, t_change+NAV_SKIP_S)
        if any(ta < c1 and ta + win > c0 for c0, c1 in skip):
            out.append((s / fs, 0.0, 0.0, 0.0))
            if skipped is not None: skipped.append(ta)
            continue
        seg = x[s:s + n]; seg = seg - seg.mean()
        P = np.abs(np.fft.rfft(seg * w)) ** 2 / (fs * np.sum(w ** 2)); P[1:-1] *= 2
        k = b[np.argmax(P[b])]
        rms = np.sqrt(P[max(k - hb, 0):k + hb + 1].sum() * df)
        out.append((s / fs, f[k], P[k] / np.median(P[b]), rms))
    return out

def sustained(wins, rms_min=None, ratio=None):
    """>=3 consecutive flagged windows with peak freq within +-10 % of the first of the streak."""
    ratio = RATIO if ratio is None else ratio
    run, best, streak = [], None, []
    for t0, fp, r, rms in wins:
        ok = r > ratio and (rms_min is None or rms > rms_min)
        if ok and streak and abs(fp - streak[0]) <= 0.1 * streak[0]: streak.append(fp)
        elif ok: streak = [fp]
        else: streak = []
        if len(streak) >= 3 and best is None: best = (t0 - 2.0, streak[0])
    return best  # (start time of the 3-window streak, freq) or None

def osc_rates(t, w, nav_t=()):   # w: (n,3) rad/s, truth p,q,r; nav_t: times of nav_state changes
    tg, g = grid(t, np.degrees(w)); res = {}; skip = [(c, c + NAV_SKIP_S) for c in nav_t]
    for i, a in enumerate("pqr"):
        sk = []; wins = psd_windows(g[:, i], FS, 2, 40, t_off=tg[0], skip=skip, skipped=sk); s = sustained(wins, rms_min=5.0)
        res[a] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins), "skipped_windows_t": sk,
                  "max_rms_dps": max(x[3] for x in wins if x[2] > RATIO) if any(x[2] > RATIO for x in wins) else 0.0}
    return res

def pos_limit_cycle(t, pos, t0, t1):
    """peak-to-peak of linearly detrended position, 10 s windows in [t0,t1]; fail = >0.3 m in 3 consecutive."""
    p2p = []
    for a in np.arange(t0, t1 - 10 + 1e-9, 10.0):
        m = (t >= a) & (t < a + 10); tt = t[m]
        p2p.append([float(np.ptp(pos[m, i] - np.polyval(np.polyfit(tt, pos[m, i], 1), tt))) for i in range(3)])
    if not p2p: return {"sustained": False, "p2p_m": [], "note": "hold < 10 s, not evaluated"}
    p2p = np.array(p2p); bad = (p2p > 0.3).any(1); run = 0; flag = False
    for b in bad: run = run + 1 if b else 0; flag |= run >= 3
    return {"sustained": bool(flag), "p2p_m": p2p.tolist()}

def chatter(t, u):  # u: (n,4) motor commands
    tg, g = grid(t, u); res = {}
    for i in range(4):
        wins = psd_windows(g[:, i], FS, 20, 100, rms_hz=2.0); s = sustained(wins, rms_min=DSHOT_STEP)
        fl = [x for x in wins if x[2] > RATIO and x[3] >= DSHOT_STEP]  # Q14 A: both conditions
        b = max(fl, key=lambda x: x[3]) if fl else max(wins, key=lambda x: x[2])
        res[f"m{i}"] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins),
                        "f_at_max": max(wins, key=lambda x: x[2])[1], "report_f_hz": b[1], "report_ratio": b[2],
                        "report_rms": b[3], "n_flagged_windows": len(fl)}
    return res

def tilt_deg(q):  # q = w,x,y,z ; angle between body z and world z, independent of ENU/NED
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))

def roll_pitch(q):
    w, x, y, z = q.T
    return (np.degrees(np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))),
            np.degrees(np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))))

EXC_LIMIT = 5.0  # item-1 horizontal excursion threshold, m (unchanged)

def excursion(t, pos, s0, s1, sp_t, sp_xy):
    """S186 item-1 horizontal excursion: max over truth samples in [s0, s1] of the horizontal distance between truth
    (x, y) and the trajectory_setpoint (x, y) linearly interpolated onto the truth timestamps (no zero-order hold).
    A truth sample is usable only if the setpoint samples bracketing it in time both exist and have finite x and y
    (so NaN velocity/acceleration-only setpoints are excluded, and an interpolation never bridges a NaN sample or runs
    beyond the first/last setpoint sample).
    FRAME: trajectory_setpoint x,y is in the estimator local frame (NED, origin at the arming position). Truth
    (sim_ground_truth x,y) is used raw, exactly as the existing key-2 check uses truth against the estimator frame
    (no offset or rotation is applied anywhere in this file; both are NED, origins differ by the ~cm start estimate).
    Returns excursion_m (None = skipped), excursion_sp_nan_frac (fraction of span samples excluded for any reason,
    NaN-bracketed or outside the setpoint time range) and the split of that fraction."""
    skip = {"excursion_m": None, "excursion_sp_nan_frac": None, "excursion_sp_nan_only_frac": None,
            "excursion_sp_outside_frac": None, "span_s": [float(s0), float(s1)], "n_span": 0, "n_used": 0}
    if sp_t is None or len(sp_t) < 2 or s1 <= s0:
        return skip
    o = np.argsort(sp_t); sp_t = np.asarray(sp_t, float)[o]; sp_xy = np.asarray(sp_xy, float)[o]
    m = np.where((t >= s0) & (t <= s1))[0]; tm = t[m]; n = len(m)
    if n == 0:
        return skip
    fin = np.isfinite(sp_xy).all(1)
    inside = (tm >= sp_t[0]) & (tm <= sp_t[-1])
    hi = np.clip(np.searchsorted(sp_t, tm, side="right"), 1, len(sp_t) - 1); lo = hi - 1
    brk = fin[lo] & fin[hi]; good = inside & brk
    d = None
    if good.any():
        ta, tb = sp_t[lo[good]], sp_t[hi[good]]
        w = (tm[good] - ta) / np.where(tb > ta, tb - ta, 1.0)
        spx = sp_xy[lo[good], 0] * (1 - w) + sp_xy[hi[good], 0] * w
        spy = sp_xy[lo[good], 1] * (1 - w) + sp_xy[hi[good], 1] * w
        d = float(np.max(np.hypot(pos[m[good], 0] - spx, pos[m[good], 1] - spy)))
    nu = int(good.sum())
    return {"excursion_m": d, "excursion_sp_nan_frac": 1 - nu / n,
            "excursion_sp_nan_only_frac": float((inside & ~brk).sum() / n),
            "excursion_sp_outside_frac": float((~inside).sum() / n),
            "span_s": [float(s0), float(s1)], "n_span": int(n), "n_used": nu}

def loc(t, q, pos, h, hold0, hold1, ground_contact_t, exc=None):
    """Truth LOC rules over the airborne span; segment = the hold. Horizontal excursion: see excursion() (exc)."""
    tl = tilt_deg(q); dt = np.median(np.diff(t)); bad = tl > 60; longest = run = 0
    for b in bad: run = run + 1 if b else 0; longest = max(longest, run)
    m0 = np.argmin(abs(t - hold0)); seg = (t >= hold0) & (t <= hold1)
    drop = float(h[m0] - h[seg].min()); nan = bool(np.isnan(pos).any() or np.isnan(q).any())
    gc = [x for x in ground_contact_t if hold0 <= x <= hold1]
    r = {"tilt_max_deg": float(tl.max()), "tilt_gt60_s": longest * dt, "drop_m": drop, "nan": nan, "ground_contact_in_hold": len(gc), "controller_fault": "UNVERIFIED (no flag defined in spec)"}
    exc = exc or {"excursion_m": None}; r.update(exc)   # excursion None = skipped (non-position mode / no setpoint)
    ex = exc["excursion_m"]
    r["pass"] = not (longest * dt > 0.2 or drop > 2.0 or (ex is not None and ex > EXC_LIMIT) or nan or gc)
    return r

def analyse(t, q, w, pos, h, motors_t, motors, hold0, hold1, gc_t, wind=False, mode="position", nav_t=(),
            sp_t=None, sp_xy=None, land_t=None, position_mode=False):
    air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]; a0, a1 = t[ia[0]], t[ia[-1]]  # airborne span
    exc = None
    if position_mode:   # item-1 span: [airborne start, min(airborne end, land/RTL start)]
        exc = excursion(t, pos, a0, a1 if land_t is None else min(a1, land_t), sp_t, sp_xy)
    r1 = loc(t, q, pos, h, hold0, hold1, gc_t, exc)
    m = (t >= a0) & (t <= a1)
    osc = osc_rates(t[m], w[m], nav_t); plc = pos_limit_cycle(t, pos, hold0, hold1)
    r2 = {"rates": osc, "position_limit_cycle": plc, "airborne_span_s": [float(a0), float(a1)],
          "pass": not (any(v["sustained"] for v in osc.values()) or plc["sustained"])}
    win = (t >= hold1 - 10) & (t <= hold1); ref = np.array([np.median(pos[(t >= hold0) & (t < hold0 + 1)][:, i]) for i in range(3)])
    hz_rms = float(np.sqrt(np.mean((pos[win, 0] - ref[0]) ** 2 + (pos[win, 1] - ref[1]) ** 2)))
    alt = float(np.mean(h[win]) - np.median(h[(t >= hold0) & (t < hold0 + 1)]))
    ro, pi = roll_pitch(q[win])
    r3 = {"window_s": [float(hold1 - 10), float(hold1)], "horiz_rms_m": hz_rms, "alt_mean_m": alt,
          "roll_mean_deg": float(ro.mean()), "pitch_mean_deg": float(pi.mean()),
          "h_window_min_m": float(h[win].min()), "airborne_in_window": bool(air[win].all()),
          "limits": {"horiz": 0.30 if wind else 0.15, "alt": 0.20 if wind else 0.10, "rollpitch": 1.0 if mode == "attitude" else None}}
    L = r3["limits"]; r3["pass"] = bool(hz_rms <= L["horiz"] and abs(alt) <= L["alt"] and
        (L["rollpitch"] is None or max(abs(ro.mean()), abs(pi.mean())) <= L["rollpitch"]))
    mm = (motors_t >= a0) & (motors_t <= a1); ch = chatter(motors_t[mm], motors[mm])
    rc = {"motors": ch, "pass": not any(v["sustained"] for v in ch.values())}
    return {"item1_loc": r1, "item2_oscillation": r2, "item3_steady_state": r3, "chatter": rc,
            "pass": bool(r1["pass"] and r2["pass"] and r3["pass"] and rc["pass"])}

def load_run(d):
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_land_detected", "vehicle_status", "trajectory_setpoint"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    q = np.stack([g[f"q[{i}]"] for i in range(4)], 1); w = np.stack([g[f"angular_velocity[{i}]"] for i in range(3)], 1)
    pos = np.stack([g["x"], g["y"], g["z"]], 1)
    z0 = np.median(pos[:800, 2]); ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0); mo = D["actuator_motors"]
    ld = D["vehicle_land_detected"]; gc = list(ld["timestamp"][ld["ground_contact"] > 0] * 1e-6)
    vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    nav_t = list(vt[1:][np.diff(ns) != 0])
    rj = json.load(open(os.path.join(d, "run.json")))
    sp = D.get("trajectory_setpoint"); sp_t = sp_xy = None
    if sp is not None:   # logged ~50 Hz (truth 800 Hz); NaN x/y rows kept here, excluded in excursion()
        sp_t = sp["timestamp"] * 1e-6; sp_xy = np.stack([sp["position[0]"], sp["position[1]"]], 1)
    # land/RTL start: first nav_state in LAND_NAV, or the logged land command if earlier
    lt = [vt[i] for i in range(len(ns)) if ns[i] in LAND_NAV]
    land_t = min(lt) if lt else None
    if rj.get("t_land_cmd_us"): land_t = rj["t_land_cmd_us"] * 1e-6 if land_t is None else min(land_t, rj["t_land_cmd_us"] * 1e-6)
    return dict(t=t, q=q, w=w, pos=pos, h=h, nav_t=nav_t, sp_t=sp_t, sp_xy=sp_xy, land_t=land_t,
                position_mode=rj.get("scenario") == "o1_lemniscate", motors_t=mo["timestamp"] * 1e-6,
                motors=np.stack([mo[f"control[{i}]"] for i in range(4)], 1), hold0=h0, hold1=h1, gc_t=gc,
                wind=False, mode=ev.get("mode", "position")), float(np.max(np.diff(t)))

def synth(osc_hz=None, osc_amp=8.0, chat_hz=None, seed=0):
    rng = np.random.default_rng(seed); t = np.arange(0, 120, 1 / FS); n = len(t)
    pos = np.stack([rng.normal(0, 0.02, n), rng.normal(0, 0.02, n), -10 + rng.normal(0, 0.01, n)], 1)
    pos[:, 2][t < 5] = np.linspace(0, -10, (t < 5).sum()); pos[:, 2][t < 5] -= 0  # takeoff, NED
    w = np.radians(rng.normal(0, 1.0, (n, 3)))
    if osc_hz: w[:, 0] += np.radians(osc_amp) * np.sin(2 * np.pi * osc_hz * t)
    u = 0.14 + rng.normal(0, 0.003, (n, 4))
    if chat_hz: u[:, 1] += 0.03 * np.sin(2 * np.pi * chat_hz * t)
    q = np.tile([1.0, 0, 0, 0], (n, 1))
    return dict(t=t, q=q, w=w, pos=pos, h=-pos[:, 2], motors_t=t, motors=u, hold0=30.0, hold1=110.0, gc_t=[])

def self_test():
    ok = True
    def chk(name, got, want):
        nonlocal ok; good = got == want; ok &= good; print(("PASS " if good else "FAIL ") + name, "got", got, "want", want)
    base = analyse(**synth())
    chk("clean run passes", base["pass"], True)
    chk("4 dps 30 Hz not flagged", analyse(**synth(30, 4.0))["item2_oscillation"]["rates"]["p"]["sustained"], False)
    o = analyse(**synth(30, 8.0))
    chk("8 dps 30 Hz flagged item2", o["item2_oscillation"]["rates"]["p"]["sustained"], True)
    chk("8 dps 30 Hz run fails", o["pass"], False)
    c = analyse(**synth(None, chat_hz=70))
    chk("70 Hz command line flagged", c["chatter"]["motors"]["m1"]["sustained"], True)
    chk("70 Hz only m1 flagged", [v["sustained"] for v in c["chatter"]["motors"].values()], [False, True, False, False])
    return ok

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--break" in a: RATIO = 1e9
    if "--self-test" in a: sys.exit(0 if self_test() else 1)
    out = None
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; a = a[:i] + a[i + 2:]   # --out DIR: DIR/<run>.json, no overwrite
    for d in (x for pat in a for x in sorted(glob.glob(pat)) if os.path.isdir(x)):
        kw, maxdt = load_run(d); r = analyse(**kw); r["max_dt_s"] = maxdt
        if out:
            os.makedirs(out, exist_ok=True); fn = os.path.join(out, os.path.basename(d.rstrip("/")) + ".json")
            if os.path.exists(fn): sys.exit("exists, not overwriting: " + fn)
        else: fn = os.path.join(d, "g3_checks_key2.json")
        json.dump(r, open(fn, "w"), indent=1, default=float)
        print(os.path.basename(d.rstrip("/")), r["pass"], r["item1_loc"]["pass"], r["item2_oscillation"]["pass"], r["item3_steady_state"]["pass"], r["chatter"]["pass"])
