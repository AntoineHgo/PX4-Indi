#!/usr/bin/env python3
"""Independent second implementation (key2) of GATES.md G3 items 1-3 + G4 command chatter."""
import sys, json, os, glob
import numpy as np
FS = 800.0
RATIO = 20.0   # peak / band-median threshold (spec); --break raises it to prove the self-test bites

def grid(t, y, fs=FS):
    """Resample onto a uniform grid (t in s, y shape (n,) or (n,k))."""
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    y = np.atleast_2d(y.T).T if y.ndim == 1 else y
    return tg, np.stack([np.interp(tg, t, y[:, i]) for i in range(y.shape[1])], 1)

def psd_windows(x, fs, f0, f1, win=4.0, step=1.0):
    """Yield (t_start, f_peak, ratio, rms_at_peak) per window: Hann PSD, one peak = band maximum."""
    n, h = int(win * fs), int(step * fs); w = np.hanning(n); df = fs / n
    f = np.fft.rfftfreq(n, 1 / fs); b = np.where((f >= f0) & (f <= f1))[0]
    out = []
    for s in range(0, len(x) - n + 1, h):
        seg = x[s:s + n]; seg = seg - seg.mean()
        P = np.abs(np.fft.rfft(seg * w)) ** 2 / (fs * np.sum(w ** 2)); P[1:-1] *= 2
        k = b[np.argmax(P[b])]
        rms = np.sqrt(P[max(k - 2, 0):k + 3].sum() * df)
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

def osc_rates(t, w):   # w: (n,3) rad/s, truth p,q,r
    tg, g = grid(t, np.degrees(w)); res = {}
    for i, a in enumerate("pqr"):
        wins = psd_windows(g[:, i], FS, 2, 40); s = sustained(wins, rms_min=5.0)
        res[a] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins),
                  "max_rms_dps": max(x[3] for x in wins if x[2] > RATIO) if any(x[2] > RATIO for x in wins) else 0.0}
    return res

def pos_limit_cycle(t, pos, t0, t1):
    """peak-to-peak of linearly detrended position, 10 s windows in [t0,t1]; fail = >0.3 m in 3 consecutive."""
    p2p = []
    for a in np.arange(t0, t1 - 10 + 1e-9, 10.0):
        m = (t >= a) & (t < a + 10); tt = t[m]
        p2p.append([float(np.ptp(pos[m, i] - np.polyval(np.polyfit(tt, pos[m, i], 1), tt))) for i in range(3)])
    p2p = np.array(p2p); bad = (p2p > 0.3).any(1); run = 0; flag = False
    for b in bad: run = run + 1 if b else 0; flag |= run >= 3
    return {"sustained": bool(flag), "p2p_m": p2p.tolist()}

def chatter(t, u):  # u: (n,4) motor commands
    tg, g = grid(t, u); res = {}
    for i in range(4):
        wins = psd_windows(g[:, i], FS, 20, 100); s = sustained(wins)
        res[f"m{i}"] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins),
                        "f_at_max": max(wins, key=lambda x: x[2])[1]}
    return res

def tilt_deg(q):  # q = w,x,y,z ; angle between body z and world z, independent of ENU/NED
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))

def roll_pitch(q):
    w, x, y, z = q.T
    return (np.degrees(np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))),
            np.degrees(np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))))

def loc(t, q, pos, h, hold0, hold1, ground_contact_t):
    """Truth LOC rules over the airborne span; segment = the hold, reference = position at hold start."""
    tl = tilt_deg(q); dt = np.median(np.diff(t)); bad = tl > 60; longest = run = 0
    for b in bad: run = run + 1 if b else 0; longest = max(longest, run)
    m0 = np.argmin(abs(t - hold0)); seg = (t >= hold0) & (t <= hold1)
    hz = float(np.max(np.hypot(pos[seg, 0] - pos[m0, 0], pos[seg, 1] - pos[m0, 1])))
    drop = float(h[m0] - h[seg].min()); nan = bool(np.isnan(pos).any() or np.isnan(q).any())
    gc = [x for x in ground_contact_t if hold0 <= x <= hold1]
    r = {"tilt_max_deg": float(tl.max()), "tilt_gt60_s": longest * dt, "drop_m": drop, "max_horiz_m": hz,
         "nan": nan, "ground_contact_in_hold": len(gc), "controller_fault": "UNVERIFIED (no flag defined in spec)"}
    r["pass"] = not (longest * dt > 0.2 or drop > 2.0 or hz > 5.0 or nan or gc)
    return r

def analyse(t, q, w, pos, h, motors_t, motors, hold0, hold1, gc_t, wind=False, mode="position"):
    r1 = loc(t, q, pos, h, hold0, hold1, gc_t)
    air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]; a0, a1 = t[ia[0]], t[ia[-1]]  # airborne span
    m = (t >= a0) & (t <= a1)
    osc = osc_rates(t[m], w[m]); plc = pos_limit_cycle(t, pos, hold0, hold1)
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
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_land_detected"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    q = np.stack([g[f"q[{i}]"] for i in range(4)], 1); w = np.stack([g[f"angular_velocity[{i}]"] for i in range(3)], 1)
    pos = np.stack([g["x"], g["y"], g["z"]], 1)
    z0 = np.median(pos[:800, 2]); ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0); mo = D["actuator_motors"]
    ld = D["vehicle_land_detected"]; gc = list(ld["timestamp"][ld["ground_contact"] > 0] * 1e-6)
    return dict(t=t, q=q, w=w, pos=pos, h=h, motors_t=mo["timestamp"] * 1e-6,
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
    for d in (x for pat in a for x in sorted(glob.glob(pat)) if os.path.isdir(x)):
        kw, maxdt = load_run(d); r = analyse(**kw); r["max_dt_s"] = maxdt
        json.dump(r, open(os.path.join(d, "g3_checks_key2.json"), "w"), indent=1, default=float)
        print(os.path.basename(d.rstrip("/")), r["pass"], r["item1_loc"]["pass"], r["item2_oscillation"]["pass"], r["item3_steady_state"]["pass"], r["chatter"]["pass"])
