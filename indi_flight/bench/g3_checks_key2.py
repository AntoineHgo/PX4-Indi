#!/usr/bin/env python3
"""Independent second implementation (key2) of GATES.md G3 items 1-6 + G4 command chatter (S226: windows from run.json,
items 4-6, S225 item-2 fault-window skip rule; see results/q30_tooling_s226/KEY2_README.md).
Item 2 = no sustained oscillation on p, q, r, position (GATES.md line 304). Command chatter is reported under "chatter" and as
top-level "g4_command_chatter_sustained" for G4 (GATES.md line ~361, Q14 A line ~553); it does not decide item 2 or the G3 "pass"."""
import sys, json, os, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g3_run_status
FS = 800.0
DSHOT_STEP = 5e-4  # Q14 A: line RMS floor = one DShot step (full scale 1)
LAND_NAV = (5, 18, 20)   # vehicle_status nav_state: AUTO_RTL, AUTO_LAND, AUTO_PRECLAND
NAV_SKIP_S = 3.0   # Q15 A: skip detector windows overlapping this long after a nav_state change
RATIO = 20.0   # peak / band-median threshold (spec); --break raises it to prove the self-test bites

STEP_WIN_S = 4.0   # item-2 rate-line window length (spec: 4 s windows, 1 s step)

def _brk(name):
    """Break-check hook: KEY2_BREAK=name[,name] disables one new rule so its self-test must fail (README)."""
    return name in os.environ.get("KEY2_BREAK", "").split(",")

def grid(t, y, fs=FS):
    """Resample onto a uniform grid (t in s, y shape (n,) or (n,k))."""
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    y = np.atleast_2d(y.T).T if y.ndim == 1 else y
    return tg, np.stack([np.interp(tg, t, y[:, i]) for i in range(y.shape[1])], 1)

def psd_windows(x, fs, f0, f1, win=4.0, step=1.0, rms_hz=None, t_off=0.0, skip=(), skipped=None, step_pts=(), reasons=None):
    """Yield (t_start, f_peak, ratio, rms_at_peak) per window: Hann PSD, one peak = band maximum.
    skip: intervals (c0, c1); a window [ta, ta+win] overlapping one is skipped (Q15 A, nav_state change).
    step_pts: absolute times of fault/gust step starts; a window with ta <= t < ta+win is skipped (S225 item 2 rule).
    A skipped window is emitted as (t, 0, 0, 0) so no line chains across it (sustained() resets on ratio 0).
    reasons: list that receives (ta, ta+win, reason, ratio_if_unskipped, rms_if_unskipped) per skipped window."""
    n, h = int(win * fs), int(step * fs); w = np.hanning(n); df = fs / n
    f = np.fft.rfftfreq(n, 1 / fs); b = np.where((f >= f0) & (f <= f1))[0]
    hb = 2 if rms_hz is None else int(round(rms_hz / df)); out = []
    for s in range(0, len(x) - n + 1, h):
        ta = t_off + s / fs   # absolute window span [ta, ta+win] vs skip intervals (t_change, t_change+NAV_SKIP_S)
        why = []
        if any(ta < c1 and ta + win > c0 for c0, c1 in skip): why.append("nav_state change within 3 s (Q15 A)")
        if not _brk("skip") and any(ta <= tp < ta + win for tp in step_pts): why.append("fault/gust step start inside window (S225)")
        seg = x[s:s + n]; seg = seg - seg.mean()
        P = np.abs(np.fft.rfft(seg * w)) ** 2 / (fs * np.sum(w ** 2)); P[1:-1] *= 2
        k = b[np.argmax(P[b])]
        rms = np.sqrt(P[max(k - hb, 0):k + hb + 1].sum() * df)
        if why:
            if skipped is not None: skipped.append(ta)
            if reasons is not None: reasons.append((ta, ta + win, "; ".join(why), float(P[k] / np.median(P[b])), float(rms)))
            if not _brk("chain"): out.append((s / fs, 0.0, 0.0, 0.0))   # break-check "chain": drop it so lines chain across
            continue
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

def osc_rates(t, w, nav_t=(), step_t=()):   # w: (n,3) rad/s, truth p,q,r; nav_t: nav_state change times; step_t: fault/gust step starts
    tg, g = grid(t, np.degrees(w)); res = {}; skip = [(c, c + NAV_SKIP_S) for c in nav_t]
    for i, a in enumerate("pqr"):
        sk = []; rs = []
        wins = psd_windows(g[:, i], FS, 2, 40, t_off=tg[0], skip=skip, skipped=sk, step_pts=tuple(step_t), reasons=rs)
        s = sustained(wins, rms_min=5.0)
        res[a] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins),
                  "skipped_windows_t": sk,
                  "skipped_windows": [{"start_s": r[0], "end_s": r[1], "reason": r[2],
                                       "flagged_if_unskipped": bool(r[3] > RATIO and r[4] > 5.0)} for r in rs],
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

def interp_sp(tm, sp_t, cols):
    """Linearly interpolate setpoint columns (n,k) onto times tm; usable only where both bracketing samples are finite and
    tm lies inside the setpoint time range. Returns (values (len(tm),k), good mask)."""
    if sp_t is None or cols is None or len(sp_t) < 2: return None, np.zeros(len(tm), bool)
    o = np.argsort(sp_t); st = np.asarray(sp_t, float)[o]; c = np.asarray(cols, float)[o]
    hi = np.clip(np.searchsorted(st, tm, side="right"), 1, len(st) - 1); lo = hi - 1
    fin = np.isfinite(c).all(1); good = (tm >= st[0]) & (tm <= st[-1]) & fin[lo] & fin[hi]
    w = ((tm - st[lo]) / np.where(st[hi] > st[lo], st[hi] - st[lo], 1.0))[:, None]
    return c[lo] * (1 - w) + c[hi] * w, good

def steady_state(t, q, pos, h, hold0, hold1, mode, wind, sag, sp_t, sp_xy, sp_z, win_s):
    """G3 item 3 from the written spec (GATES.md 'Pass per run' 3 and 'Steady-state window').
    Window: win_s = (t0, t1) on the truth clock if given (command line --t0/--t1), else the last 10 s of the hold.
    Reference (spec: 'horizontal RMS' of a hold = scatter about the hold point, which is the commanded position hold):
      position mode: the logged trajectory_setpoint (x, y, and z for altitude) interpolated onto the truth samples;
      attitude mode: no position setpoint exists, so horizontal and altitude are measured about the window truth mean
      (scatter only) and are NOT gated; only roll/pitch |mean| is gated (spec: 'in attitude mode').
    Limits: horizontal 0.30 with wind/gust else 0.15; altitude 0.20 with sag/weak motor else 0.10 (the two conditions are
    independent in the spec); roll/pitch 1.0 deg in attitude mode. Altitude error = mean(h) - mean(-setpoint z) (NED)."""
    t0, t1 = win_s if win_s is not None else (hold1 - 10, hold1)
    win = (t >= t0) & (t <= t1); gated_xy = mode == "position"
    ro, pi = roll_pitch(q[win]); ref_src = None
    if gated_xy:
        sp, good = interp_sp(t[win], sp_t, None if sp_xy is None else np.column_stack([sp_xy, np.zeros(len(sp_xy)) if sp_z is None else sp_z]))
        if sp is not None and good.any() and sp_z is not None:
            ref_src = "trajectory_setpoint interpolated per truth sample"
            px, hh = pos[win][good], h[win][good]
            e = np.hypot(px[:, 0] - sp[good, 0], px[:, 1] - sp[good, 1])
            hz_rms = float(np.sqrt(np.mean(e ** 2))); alt = float(np.mean(hh) + np.mean(sp[good, 2]))   # h_sp = -z_sp
            n_used = int(good.sum())
        else: gated_xy = False
    if not gated_xy:
        ref_src = ref_src or "window truth mean (no position setpoint; ungated)"
        pw = pos[win]; hz_rms = float(np.sqrt(np.mean((pw[:, 0] - pw[:, 0].mean()) ** 2 + (pw[:, 1] - pw[:, 1].mean()) ** 2)))
        alt = 0.0; n_used = int(win.sum())
    L = {"horiz": 0.30 if wind else 0.15, "alt": 0.20 if sag else 0.10, "rollpitch": 1.0 if mode == "attitude" else None}
    rp = max(abs(ro.mean()), abs(pi.mean())) if win.any() else float("nan")
    ok = (not gated_xy or (hz_rms <= L["horiz"] and abs(alt) <= L["alt"])) and (L["rollpitch"] is None or rp <= L["rollpitch"])
    return {"window_s": [float(t0), float(t1)], "mode": mode, "wind": bool(wind), "sag": bool(sag), "ref_source": ref_src,
            "gated_horiz_alt": bool(gated_xy), "n_samples": int(win.sum()), "n_used": n_used,
            "horiz_rms_m": hz_rms, "alt_mean_m": alt, "roll_mean_deg": float(ro.mean()), "pitch_mean_deg": float(pi.mean()),
            "h_window_min_m": float(h[win].min()), "limits": L, "pass": bool(ok)}

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

# ---- S226: windows from run.json, items 4-6 -------------------------------------------------------------------------------
ITEM3_S, ITEM6_S = 10.0, 20.0    # item 3 = last 10 s of the hold, item 6 = last 20 s of the hold (GATES S214)
TRACK_H, TRACK_V = 0.5, 0.3      # item 4 limits, m (horizontal RMS, vertical RMS)
REC_POS, REC_ATT, REC_T, REC_QUIET = 0.3, 3.0, 5.0, 5.0   # item 5: m, deg, s to return, s without re-excursion
RATE_RMS = 5.0                   # item 6 limit, deg/s
STICK_MODE_NAME = {"stabilized": "attitude", "acro": "rate"}

def windows_from_run(rj, legacy_win=None):
    """All G3 windows from run.json['events'] alone (S214; key 2 no longer takes key 1's t0/t1). Times are on the ulog clock
    (run.json t_us is the runner's sim.t, the same clock as the ulog / sim_ground_truth timestamp).
    main = first event named 'traj' (position scenarios) or 'stick' (stick scenarios); hold = LAST event named 'hold'.
    step_t = fault / gust step starts = the main-segment start (S214 correction). legacy_win = (t0, t1) overrides item 3 only."""
    ev = rj.get("events", [])
    main = next((e for e in ev if e.get("name") in ("traj", "stick")), None)
    holds = [e for e in ev if e.get("name") == "hold"]
    if not holds: raise ValueError("run.json has no 'hold' event")
    hd = holds[-1]; h0 = hd["t_us"] * 1e-6; h1 = h0 + float(hd["dur_s"])
    i3 = (h1 - ITEM3_S, h1) if not _brk("item3") else (h0, h0 + ITEM3_S)   # break-check: first 10 s of the hold
    r = {"hold": [h0, h1], "hold_dur_s": h1 - h0, "n_hold_events": len(holds),
         "item3": list(legacy_win) if legacy_win else list(i3), "item3_legacy_override": legacy_win is not None,
         "item6": [h1 - ITEM6_S, h1], "main_name": None, "main": None, "step_t": []}
    if main is not None:
        m0 = main["t_us"] * 1e-6
        r.update(main_name=main["name"], main=[m0, m0 + float(main.get("dur_s") or 0.0)], step_t=[m0])
    st = rj.get("stick") or {}
    if main is not None and main["name"] == "traj": r["mode"], r["mode_src"] = "position", "events: traj"
    elif main is not None and main["name"] == "stick":
        r["mode"] = STICK_MODE_NAME.get(st.get("mode"), st.get("mode") or "unknown"); r["mode_src"] = "run.json stick.mode=" + str(st.get("mode"))
    else: r["mode"], r["mode_src"] = None, "no traj/stick event"
    return r

def draw_flags(d):
    """wind / sag flags from g3_draw.json factors (item 3 limits): wind = steady or gust drawn; sag = thrust sag or weak motor on."""
    try: f = json.load(open(os.path.join(d, "g3_draw.json")))["draw"]["factors"]
    except (OSError, ValueError, KeyError): return None
    wd = f.get("wind", {}); wind = any(float(wd.get(k) or 0.0) > 0 for k in ("steady_ms", "gust_amp_ms", "gust_peak_total_ms"))
    sag = bool(f.get("thrust_sag", {}).get("on")) or bool(f.get("weak_motor", {}).get("on"))
    tel = []
    for k in ("tel_loss", "tel_frozen"):
        x = f.get(k, {})
        if x.get("on") and x.get("start_offset_s") is not None: tel.append((k, float(x["start_offset_s"])))
    return {"wind": wind, "sag": sag, "tel": tel}

def tracking(t, pos, h, rw, sp_t, sp_xy, sp_z):
    """G3 item 4 (position scenarios): over the main segment [traj start, traj start + dur] horizontal RMS <= 0.5 m and vertical
    RMS <= 0.3 m of truth vs the logged trajectory_setpoint (x, y, z) interpolated onto the truth samples (as items 1 and 3)."""
    if rw["mode"] != "position": return {"applicable": False, "pass": True, "note": "item 4 is for the position scenario (traj) only"}
    a, b = rw["main"]; m = (t >= a) & (t <= b)
    sp, good = interp_sp(t[m], sp_t, None if sp_xy is None or sp_z is None else np.column_stack([sp_xy, sp_z]))
    if sp is None or not good.any():
        return {"applicable": True, "pass": False, "note": "no usable trajectory_setpoint in the traj window (fail closed)", "window_s": [a, b]}
    px, hh = pos[m][good], h[m][good]; g = sp[good]
    hr = float(np.sqrt(np.mean((px[:, 0] - g[:, 0]) ** 2 + (px[:, 1] - g[:, 1]) ** 2))); vr = float(np.sqrt(np.mean((hh + g[:, 2]) ** 2)))
    lh, lv = (TRACK_H, TRACK_V) if not _brk("item4") else (1e9, 1e9)
    return {"applicable": True, "window_s": [a, b], "n_used": int(good.sum()), "n_window": int(m.sum()), "horiz_rms_m": hr, "vert_rms_m": vr,
            "limits": {"horiz": TRACK_H, "vert": TRACK_V}, "pass": bool(hr <= lh and vr <= lv)}

def _zb(q):   # body z axis in the world frame, rows (n,3); q = w,x,y,z
    w, x, y, z = q.T
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)

def _angle_deg(a, b):
    return np.degrees(np.arccos(np.clip((a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)), -1, 1)))

def recovery(t, q, pos, h, rw, sp_t, sp_xy, sp_z, att_t, att_q, extra=()):
    """G3 item 5: after each injected event (gust / fault step = main-segment start; extra = reported-only (name, time) events)
    the vehicle is back within 0.3 m and 3 deg of the reference within 5 s and then has no re-excursion > 0.3 m for 5 s.
    Reference: position mode = the commanded reference (trajectory_setpoint position, vehicle_attitude_setpoint q_d), because the
    lemniscate is not a static hold; attitude mode = the pre-event attitude (median body z over the 2 s before the event);
    rate mode = not applicable (no position or attitude hold; item 6 covers it). Position error is 3-D (x, y, altitude), attitude
    error is the tilt angle between body z axes (yaw excluded, as item 3).  t_in = first sample with every applicable error within
    its limit; pass = t_in - t_event <= 5 s and no sample in (t_in, t_in+5 s] with the controlled error beyond its limit
    (position mode: 0.3 m; attitude mode: 3 deg, the only controlled quantity there)."""
    mode = rw["mode"]
    if mode not in ("position", "attitude"):
        return {"applicable": False, "pass": True, "events": [], "note": f"item 5 not applicable in mode {mode!r}"}
    evs = [("step@main_start", te, True) for te in rw["step_t"]] + [(n, te, False) for n, te in extra]
    out = []; ok = True
    zb_t = _zb(q)
    for name, te, gated in evs:
        m = (t >= te) & (t <= te + REC_T + REC_QUIET); r = {"event": name, "t_s": te, "gated": gated}
        if te + REC_T + REC_QUIET > t[-1] + 1e-9 or not m.any():
            r.update(pass_=False, note="flight ends before te + 10 s (fail closed)"); out.append(r)
            if gated: ok = False
            continue
        tw = t[m]; e_att = e_pos = None
        if mode == "position":
            sp, good = interp_sp(tw, sp_t, None if sp_xy is None or sp_z is None else np.column_stack([sp_xy, sp_z]))
            e_pos = np.where(good, np.sqrt((pos[m, 0] - np.where(good, sp[:, 0], 0)) ** 2 + (pos[m, 1] - np.where(good, sp[:, 1], 0)) ** 2
                                           + (h[m] + np.where(good, sp[:, 2], 0)) ** 2), np.nan) if sp is not None else np.full(len(tw), np.nan)
            if att_t is not None and att_q is not None and len(att_t) > 1:
                o = np.argsort(att_t); at = np.asarray(att_t, float)[o]; aq = np.asarray(att_q, float)[o]
                k = np.clip(np.searchsorted(at, tw, side="right") - 1, 0, len(at) - 1)
                ref = _zb(aq[k]); e_att = np.where((tw >= at[0]) & np.isfinite(aq[k]).all(1), _angle_deg(zb_t[m], ref), np.nan)
            else: e_att = np.full(len(tw), np.nan)
        else:
            pre = (t >= te - 2.0) & (t < te)
            if not pre.any(): r.update(pass_=False, note="no pre-event data (fail closed)"); out.append(r); ok = ok and not gated; continue
            ref = np.median(zb_t[pre], 0)[None, :]; e_att = _angle_deg(zb_t[m], np.repeat(ref, m.sum(), 0))
        valid = np.isfinite(e_att) & (np.isfinite(e_pos) if e_pos is not None else True)
        if valid.mean() < 0.5:
            r.update(pass_=False, note=f"reference missing for {1 - valid.mean():.0%} of the 10 s window (fail closed)"); out.append(r)
            if gated: ok = False
            continue
        within = valid & (e_att <= REC_ATT) & ((e_pos <= REC_POS) if e_pos is not None else True)
        if not within.any(): r.update(pass_=False, t_back_s=None, note="never back within limits in 10 s"); out.append(r); ok = ok and not gated; continue
        i0 = int(np.argmax(within)); tb = float(tw[i0] - te)
        q5 = (tw > tw[i0]) & (tw <= tw[i0] + REC_QUIET) & valid
        exc = (e_pos > REC_POS) if e_pos is not None else (e_att > REC_ATT)
        re_exc = bool((exc & q5).any()); peak = float(np.nanmax(np.where(q5, e_pos if e_pos is not None else e_att, np.nan))) if q5.any() else 0.0
        good_ev = (tb <= REC_T and not re_exc) or _brk("item5")
        r.update(pass_=bool(good_ev), t_back_s=tb, re_excursion=re_exc, max_err_after_return=peak,
                 max_pos_err_m=None if e_pos is None else float(np.nanmax(e_pos)), max_att_err_deg=float(np.nanmax(e_att)))
        out.append(r)
        if gated and not good_ev: ok = False
    for r in out: r["pass"] = r.pop("pass_", None)
    return {"applicable": True, "mode": mode, "events": out, "limits": {"pos_m": REC_POS, "att_deg": REC_ATT, "return_s": REC_T, "quiet_s": REC_QUIET},
            "pass": bool(ok)}

def rate_hold(t, w, rw):
    """G3 item 6 (rate mode, zero sticks): body rate RMS <= 5 deg/s over the last 20 s of the hold. RMS = sqrt(mean(p^2+q^2+r^2))
    (3-axis vector, not detrended, so a constant rate drift counts); per-axis RMS reported."""
    if rw["mode"] != "rate": return {"applicable": False, "pass": True, "note": "item 6 is for rate (acro) mode only"}
    a, b = rw["item6"]; m = (t >= a) & (t <= b)
    if rw["hold_dur_s"] < ITEM6_S - 1e-9 or not m.any():
        return {"applicable": True, "window_s": [a, b], "pass": False, "note": "hold shorter than 20 s or no data (fail closed)"}
    wd = np.degrees(w[m]); rms = float(np.sqrt(np.mean(np.sum(wd ** 2, 1)))); ax = np.sqrt(np.mean(wd ** 2, 0)).tolist()
    lim = RATE_RMS if not _brk("item6") else 1e9
    return {"applicable": True, "window_s": [a, b], "n_used": int(m.sum()), "rate_rms_dps": rms, "axis_rms_dps": ax,
            "axis_mean_dps": wd.mean(0).tolist(), "limit_dps": RATE_RMS, "pass": bool(rms <= lim)}

def analyse(t, q, w, pos, h, motors_t, motors, hold0, hold1, gc_t, wind=False, mode="position", nav_t=(),
            sp_t=None, sp_xy=None, land_t=None, position_mode=False, sp_z=None, win_s=None, sag=False,
            runwin=None, att_t=None, att_q=None, tel_events=(), legacy=False):
    """runwin = windows_from_run(run.json): item 3 window, item 6 window, step starts for the item-2 skip, items 4-5.
    legacy (old CLI --t0/--t1): 'pass' = items 1-3 as before; items 4-6 are still computed and reported."""
    air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]; a0, a1 = t[ia[0]], t[ia[-1]]  # airborne span
    exc = None
    if position_mode:   # item-1 span: [airborne start, min(airborne end, land/RTL start)]
        exc = excursion(t, pos, a0, a1 if land_t is None else min(a1, land_t), sp_t, sp_xy)
    r1 = loc(t, q, pos, h, hold0, hold1, gc_t, exc)
    m = (t >= a0) & (t <= a1)
    step_t = tuple(runwin["step_t"]) if runwin else ()
    osc = osc_rates(t[m], w[m], nav_t, step_t); plc = pos_limit_cycle(t, pos, hold0, hold1)
    # table (start, end, reason) over the union of axes; the skip depends on time only, so all axes list the same windows
    table = [dict(x, axes=[a for a in "pqr" if any(y["start_s"] == x["start_s"] for y in osc[a]["skipped_windows"])],
                  flagged_if_unskipped=any(y["flagged_if_unskipped"] for a in "pqr" for y in osc[a]["skipped_windows"] if y["start_s"] == x["start_s"]))
             for x in osc["p"]["skipped_windows"]]
    r2 = {"rates": osc, "position_limit_cycle": plc, "airborne_span_s": [float(a0), float(a1)],
          "skipped_windows": table, "step_starts_s": list(step_t),
          "pass": not (any(v["sustained"] for v in osc.values()) or plc["sustained"])}
    if win_s is None and runwin is not None: win_s = tuple(runwin["item3"])
    r3 = steady_state(t, q, pos, h, hold0, hold1, mode, wind, sag, sp_t, sp_xy, sp_z, win_s)
    if runwin is not None and not runwin["item3_legacy_override"] and runwin["hold_dur_s"] < ITEM3_S - 1e-9:
        r3["pass"] = False; r3["note"] = "hold shorter than the 10 s item-3 window (fail closed)"
    mm = (motors_t >= a0) & (motors_t <= a1); ch = chatter(motors_t[mm], motors[mm])
    rc = {"motors": ch, "pass": not any(v["sustained"] for v in ch.values())}
    out = {"item1_loc": r1, "item2_oscillation": r2, "item3_steady_state": r3, "chatter": rc,
           "g4_command_chatter_sustained": not rc["pass"]}
    p123 = bool(r1["pass"] and r2["pass"] and r3["pass"])
    if runwin is not None:
        rw = dict(runwin, mode=runwin["mode"] if runwin["mode"] else mode)
        out["windows"] = rw
        out["item4_tracking"] = tracking(t, pos, h, rw, sp_t, sp_xy, sp_z)
        out["item5_recovery"] = recovery(t, q, pos, h, rw, sp_t, sp_xy, sp_z, att_t, att_q, extra=tel_events)
        out["item6_rate_hold"] = rate_hold(t, w, rw)
        p456 = bool(out["item4_tracking"]["pass"] and out["item5_recovery"]["pass"] and out["item6_rate_hold"]["pass"])
    else: p456 = True
    out["pass_items_1_3"] = p123   # S225 pass line (items 4-5 reported)
    out["pass"] = p123 if legacy else bool(p123 and p456)   # campaign pass = items 1-6
    return out

def load_run(d, t0=None, t1=None, mode=None, wind=False, sag=False):
    """t0/t1 (old CLI, seconds since the ulog start_timestamp) = legacy item-3 window; without them every window comes from run.json."""
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_land_detected", "vehicle_status", "trajectory_setpoint", "vehicle_attitude_setpoint"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    st = u.start_timestamp * 1e-6   # --t0/--t1 are seconds since the ulog start_timestamp
    q = np.stack([g[f"q[{i}]"] for i in range(4)], 1); w = np.stack([g[f"angular_velocity[{i}]"] for i in range(3)], 1)
    pos = np.stack([g["x"], g["y"], g["z"]], 1)
    rj = json.load(open(os.path.join(d, "run.json"))); legacy = t0 is not None
    rw = windows_from_run(rj, None if not legacy else (st + t0, st + t1)); h0, h1 = rw["hold"]
    z0 = np.median(pos[:800, 2])
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0); mo = D["actuator_motors"]
    ld = D["vehicle_land_detected"]; gc = list(ld["timestamp"][ld["ground_contact"] > 0] * 1e-6)
    vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    nav_t = list(vt[1:][np.diff(ns) != 0])
    sp = D.get("trajectory_setpoint"); sp_t = sp_xy = sp_z = None
    if sp is not None:   # logged ~50 Hz (truth 800 Hz); NaN x/y rows kept here, excluded in excursion()
        sp_t = sp["timestamp"] * 1e-6; sp_xy = np.stack([sp["position[0]"], sp["position[1]"]], 1); sp_z = sp["position[2]"]
    att = D.get("vehicle_attitude_setpoint"); att_t = att_q = None
    if att is not None: att_t = att["timestamp"] * 1e-6; att_q = np.stack([att[f"q_d[{i}]"] for i in range(4)], 1)
    # land/RTL start: first nav_state in LAND_NAV, or the logged land command if earlier
    lt = [vt[i] for i in range(len(ns)) if ns[i] in LAND_NAV]
    land_t = min(lt) if lt else None
    if rj.get("t_land_cmd_us"): land_t = rj["t_land_cmd_us"] * 1e-6 if land_t is None else min(land_t, rj["t_land_cmd_us"] * 1e-6)
    tel = []
    if not legacy:   # wind / sag / telemetry events from the draw (old CLI: only the --wind / --sag flags, as before)
        fl = draw_flags(d)
        if fl:
            wind, sag = wind or fl["wind"], sag or fl["sag"]
            if rw["main"]: tel = [(n, rw["main"][0] + o) for n, o in fl["tel"]]
    ss_mode = mode
    if mode: rw["mode"], rw["mode_src"] = mode, "--mode"
    elif legacy:   # old behaviour: item-3 mode = the hold event's own 'mode' field (default position)
        ss_mode = ([e for e in rj["events"] if e["name"] == "hold"][0]).get("mode", "position")
    elif rw["mode"] is None: rw["mode"], rw["mode_src"] = "position", "default (no traj/stick event)"
    return dict(t=t, q=q, w=w, pos=pos, h=h, nav_t=nav_t, sp_t=sp_t, sp_xy=sp_xy, sp_z=sp_z, land_t=land_t,
                position_mode=rj.get("scenario") == "o1_lemniscate" or rw["mode"] == "position", sag=sag,
                win_s=None if not legacy else (st + t0, st + t1), motors_t=mo["timestamp"] * 1e-6,
                motors=np.stack([mo[f"control[{i}]"] for i in range(4)], 1), hold0=h0, hold1=h1, gc_t=gc,
                wind=wind, mode=ss_mode or rw["mode"], runwin=rw, att_t=att_t, att_q=att_q, tel_events=tel, legacy=legacy), float(np.max(np.diff(t)))

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
    chk("chatter only: item2 passes", c["item2_oscillation"]["pass"], True)
    chk("chatter only: g4 flag True", c["g4_command_chatter_sustained"], True)
    chk("chatter only: G3 pass", c["pass"], True)
    chk("clean: g4 flag False", base["g4_command_chatter_sustained"], False)
    r2 = analyse(**synth(2, 15.0))
    chk("2 Hz rate oscillation fails item2", r2["item2_oscillation"]["pass"], False)
    chk("70 Hz only m1 flagged", [v["sustained"] for v in c["chatter"]["motors"].values()], [False, True, False, False])
    # S186 item 3: known hold point (3, -2, alt 10 m) and constant truth offset -> known RMS and altitude error.
    def ss(dx, dy, dh, wind=False, sag=False, win=(40.0, 50.0), mode="position"):
        t = np.arange(0, 60, 1 / FS); n = len(t); pos = np.stack([np.full(n, 3.0), np.full(n, -2.0), np.full(n, -10.0)], 1)
        m = (t >= 40) & (t <= 50); pos[m, 0] += dx; pos[m, 1] += dy; pos[m, 2] -= dh   # offset only inside the window
        pos[t < 40, 0] += 5.0   # far from the hold point before the window: must not matter
        q = np.tile([1.0, 0, 0, 0], (n, 1)); ts = np.arange(0, 60, 0.02)
        return steady_state(t, q, pos, -pos[:, 2], 30.0, 50.0, mode, wind, sag, ts, np.tile([3.0, -2.0], (len(ts), 1)),
                            np.full(len(ts), -10.0), win)
    a1 = ss(0.3, 0.4, 0.15)
    chk("item3 known RMS 0.5 m", round(a1["horiz_rms_m"], 9), 0.5)
    chk("item3 known altitude error 0.15 m", round(a1["alt_mean_m"], 9), 0.15)
    chk("item3 0.5 m fails calm and wind", (a1["pass"], ss(0.3, 0.4, 0.15, wind=True)["pass"]), (False, False))
    chk("item3 rms 0.2 passes with wind only", (ss(0.12, 0.16, 0.0)["pass"], ss(0.12, 0.16, 0.0, wind=True)["pass"]), (False, True))
    chk("item3 alt 0.15 needs sag", (ss(0, 0, 0.15, wind=True)["pass"], ss(0, 0, 0.15, sag=True)["pass"]), (False, True))
    chk("item3 window honoured", round(ss(0.0, 0.0, 0.0, win=(0.0, 20.0))["horiz_rms_m"], 6), round(float(np.sqrt(np.mean(np.where(np.arange(0, 20.0000001, 1 / FS) < 40, 25.0, 0)))), 6))
    return ok

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--break" in a: RATIO = 1e9
    if "--self-test" in a: sys.exit(0 if self_test() else 1)
    out = None
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; a = a[:i] + a[i + 2:]   # --out DIR: DIR/<run>.json, no overwrite
    def opt(name, conv=float):
        global a
        if name in a: i = a.index(name); v = conv(a[i + 1]); a = a[:i] + a[i + 2:]; return v
    t0, t1, mode = opt("--t0"), opt("--t1"), opt("--mode", str)
    wind, sag = "--wind" in a, "--sag" in a; a = [x for x in a if x not in ("--wind", "--sag")]
    for d in (x for pat in a for x in sorted(glob.glob(pat)) if os.path.isdir(x)):
        bad = g3_run_status.invalid_reason(d)  # Q27 item 8: a harness-aborted run is INVALID (re-fly), never PASS
        if bad:
            r = {"invalid": True, "invalid_reason": bad, "pass": None}
            if out:
                os.makedirs(out, exist_ok=True); fn = os.path.join(out, os.path.basename(d.rstrip("/")) + ".json")
                if os.path.exists(fn): sys.exit("exists, not overwriting: " + fn)
            else: fn = os.path.join(d, "g3_checks_key2.json")
            json.dump(r, open(fn, "w"), indent=1); print(os.path.basename(d.rstrip("/")), "INVALID", bad); continue
        kw, maxdt = load_run(d, t0, t1, mode, wind, sag); r = analyse(**kw); r["max_dt_s"] = maxdt
        if out:
            os.makedirs(out, exist_ok=True); fn = os.path.join(out, os.path.basename(d.rstrip("/")) + ".json")
            if os.path.exists(fn): sys.exit("exists, not overwriting: " + fn)
        else: fn = os.path.join(d, "g3_checks_key2.json")
        json.dump(r, open(fn, "w"), indent=1, default=float)
        print(os.path.basename(d.rstrip("/")), r["pass"], r["item1_loc"]["pass"], r["item2_oscillation"]["pass"], r["item3_steady_state"]["pass"], r["chatter"]["pass"],
              "i4", r.get("item4_tracking", {}).get("pass"), "i5", r.get("item5_recovery", {}).get("pass"), "i6", r.get("item6_rate_hold", {}).get("pass"))
        for x in r["item2_oscillation"]["skipped_windows"]:   # S225 / Q15 A: skipped item-2 windows (table)
            print("  item2 skipped window start %.3f end %.3f s  axes %s  reason: %s  (flagged if unskipped: %s)" % (
                x["start_s"], x["end_s"], "".join(x["axes"]), x["reason"], x["flagged_if_unskipped"]))
