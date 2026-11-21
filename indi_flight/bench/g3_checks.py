#!/usr/bin/env python3
"""G3 per-run checker, pass items 1-3 (GATES.md section 3 "Pass per run" and section 2 shared definitions), plus the G4
command chatter line (GATES.md G4 "Additional": actuator_motors, band 20-100 Hz, peak > 20 x median). Truth only
(sim_ground_truth: x,y,z NED, q FRD->NED, angular_velocity FRD); never the EKF, never the logged command for items 1-3.

  g3_checks.py LOG --t0 T0 --t1 T1 [--wind] [--sag] [--mode position|attitude] [--json OUT]
  T0, T1: steady-state window on the ulog time base (seconds since start_timestamp; stamps are timestamp_sample, as
  g4_metrics.py). The window is used as given (spec: last 10 s of a hold >= 20 s after the last transient; the caller picks).

Item 1 LOC (airborne, truth): tilt > 60 deg for > 0.2 s; height below the height at T0 by > 2.0 m (t >= T0);
  ground contact while airborne (height < 0.1 m between take-off and last time above 1 m); NaN in truth or in the four
  motor commands while airborne; horizontal excursion > 5 m from the reference (position mode only).
Item 2 sustained oscillation: truth p,q,r on the uniform grid (g4_metrics.uniform, starts on the first raw sample), Hann PSD,
  4 s windows, 1 s step, band 2-40 Hz; window flagged when the PSD peak > 20 x band median and the rate RMS at the peak
  > 5 deg/s; sustained = flagged in >= 3 consecutive windows with peak frequency within +-10 %. Position limit cycle:
  linearly detrended truth x,y,z, peak-to-peak > 0.3 m in 3 consecutive 10 s windows. Command chatter (G4): the same
  window detector on actuator_motors control[0..3], band 20-100 Hz, peak > 20 x median, no RMS criterion.
Item 3 steady-state on [T0,T1]: horizontal RMS about the reference <= 0.15 m calm / 0.30 m with --wind; altitude |mean error|
  <= 0.10 m calm / 0.20 m with --sag; roll/pitch |mean| <= 1.0 deg in attitude mode.

PROPOSED readings (undefined in the spec, minimal choice):
  - airborne = from the first truth sample with height (-z minus -z[0]) > 1.0 m to the last such sample; "whole flight after
    take-off" is that span (landing and disarm excluded). Not airborne at all = items 1 and 2 fail.
  - "outside land/RTL" (GATES 246) applies to the item-1 height-drop, ground-contact and excursion rules only: those use
    the airborne span cut at the first vehicle_status nav_state in LAND_NAV_STATES (RTL 5, AUTO_LAND 18). Item-1 tilt/NaN
    and item 2 use the whole airborne span, commanded descent included (GATES 304 "whole flight", D-G3-SPAN, A-55).
  - "height below segment start": segment start = T0 (height at the first sample >= T0).
  - ground contact = height < 0.1 m inside the airborne span (commanded landing is outside it by construction).
  - reference = median of trajectory_setpoint position over [T0,T1] (hold point commanded; stamps timestamp); if the log has no
    trajectory_setpoint it falls back to the truth window mean (reported as ref_source) -- then horizontal RMS is a spread only.
  - mode position gates horizontal RMS and altitude mean (roll/pitch reported); mode attitude gates roll/pitch only (no
    position reference exists; horizontal excursion LOC skipped).
  - "within +-10 %": each flagged window within 10 % of the first window of the run.
  - position limit-cycle windows: consecutive non-overlapping 10 s windows from T0 to the end of the airborne span.
  - controller fault flag: NOT implemented (no flag defined in the spec); NaN check only.
  - rate RMS at the peak: sqrt(sum of the density PSD over peak +-2 bins * df) (Hann main lobe).
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g4_metrics import uniform  # noqa: E402

TILT_DEG, TILT_S = 60.0, 0.2
DROP_M, CONTACT_M, AIRBORNE_M, EXCURSION_M = 2.0, 0.1, 1.0, 5.0
WIN_S, STEP_S, PEAK_RATIO, RMS_DEG_S, FREQ_TOL, MIN_WINDOWS = 4.0, 1.0, 20.0, 5.0, 0.10, 3
RATE_BAND, CMD_BAND = (2.0, 40.0), (20.0, 100.0)
CMD_LINE_RMS = 5e-4        # Q14 A: one DShot step of full scale; chatter needs line RMS >= this as well as ratio > 20
NAV_SKIP_S = 3.0           # Q15 A: rate windows overlapping the 3 s after a nav_state change are skipped
POS_WIN_S, POS_P2P_M = 10.0, 0.3
HORIZ_RMS = (0.15, 0.30)   # calm, wind
ALT_MEAN = (0.10, 0.20)    # calm, sag
RP_MEAN_DEG = 1.0
LAND_NAV_STATES = (5, 18)  # RTL, AUTO_LAND (vehicle_status.nav_state)


def euler_rp(q):
    """roll, pitch [rad] from q (n,4) w,x,y,z FRD->NED."""
    w, x, y, z = q.T
    return np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)), np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))


def tilt_rad(q):
    return np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1))


def longest_run_s(t, mask):
    """longest continuous true run of mask, as duration between its first and last sample."""
    best, i, n = 0.0, 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            best = max(best, t[j] - t[i])
            i = j + 1
        else:
            i += 1
    return best


def line_detector(xg, fs, band, min_rms=None, t_start=0.0, skip=()):
    """xg (n,) uniform, first sample at time t_start. Returns dict: sustained bool, lines [(f_hz, first_window_start_index,
    n_windows)], flagged windows. skip: [(ta, tb)] intervals; a window overlapping one is not evaluated (counts as unflagged,
    so it breaks a run) and is counted in skipped_windows (Q15). Also reports max_ratio (largest peak/median over the evaluated
    windows) with the line RMS (peak +-2 bins) of that window, and max_rms_ratio_flagged (largest line RMS among windows with
    ratio > PEAK_RATIO; None if none) (Q14)."""
    from scipy.signal import periodogram
    n, step = int(round(WIN_S * fs)), int(round(STEP_S * fs))
    flags = []  # per window: peak freq if flagged else None
    skipped, max_ratio, rms_at_max, max_rms_fl = 0, 0.0, None, None
    for s in range(0, len(xg) - n + 1, step):
        w0, w1 = t_start + s / fs, t_start + (s + n) / fs
        if any(w0 < tb and w1 > ta for ta, tb in skip):
            skipped += 1
            flags.append(None)
            continue
        f, P = periodogram(xg[s:s + n], fs, window="hann", detrend="constant", scaling="density")
        b = (f >= band[0]) & (f <= band[1])
        fb, Pb = f[b], P[b]
        k = int(np.argmax(Pb))
        ratio = float(Pb[k] / np.median(Pb))
        kk = np.flatnonzero(b)[k]
        rms = float(np.sqrt(np.sum(P[max(kk - 2, 0):kk + 3]) * (f[1] - f[0])))
        if ratio > max_ratio:
            max_ratio, rms_at_max = ratio, rms
        ok = Pb[k] > PEAK_RATIO * np.median(Pb)
        if ok:
            max_rms_fl = rms if max_rms_fl is None else max(max_rms_fl, rms)
        if ok and min_rms is not None:
            ok = rms >= min_rms
        flags.append(float(fb[k]) if ok else None)
    lines, i = [], 0
    while i < len(flags):
        if flags[i] is None:
            i += 1
            continue
        j = i
        while j + 1 < len(flags) and flags[j + 1] is not None and abs(flags[j + 1] - flags[i]) <= FREQ_TOL * flags[i]:
            j += 1
        if j - i + 1 >= MIN_WINDOWS:
            lines.append((flags[i], i * STEP_S, j - i + 1))
        i = j + 1
    return {"sustained": bool(lines), "lines": lines, "flagged_windows": sum(f is not None for f in flags), "windows": len(flags),
            "skipped_windows": skipped, "max_ratio": max_ratio, "rms_at_max_ratio": rms_at_max,
            "max_rms_ratio_flagged": max_rms_fl}


def position_limit_cycle(t, pos, ta, te):
    """pos (n,3). 3 consecutive 10 s windows (from ta) with detrended peak-to-peak > 0.3 m on any axis."""
    from scipy.signal import detrend
    flags, s = [], ta
    while s + POS_WIN_S <= te:
        m = (t >= s) & (t < s + POS_WIN_S)
        p2p = float(max(np.ptp(detrend(pos[m, a])) for a in range(3))) if m.sum() > 10 else 0.0
        flags.append(p2p > POS_P2P_M)
        s += POS_WIN_S
    run = best = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return {"sustained": best >= MIN_WINDOWS, "max_consecutive_windows": best, "windows": len(flags)}


def evaluate(tt, pos, q, w, tm, cmd, ref, t0, t1, wind=False, sag=False, mode="position", ref_source="given", t_land=None, nav_changes=None):
    """nav_changes: times [s] of vehicle_status.nav_state changes; if given (G4, Q15) the rate detector skips windows
    overlapping [t, t + NAV_SKIP_S]. tt (n,), pos (n,3) NED, q (n,4), w (n,3) rad/s truth; tm (m,), cmd (m,4); ref (3,) NED hold point or None."""
    h = -pos[:, 2]
    h = h - h[0] if np.isfinite(h[0]) else h
    up = np.flatnonzero(np.isfinite(h) & (h > AIRBORNE_M))
    res = {"window_s": [t0, t1], "mode": mode, "wind": wind, "sag": sag, "ref_source": ref_source}
    if up.size == 0:
        res["airborne"] = None
        res["item1_loc"] = {"pass": False, "reason": "never airborne"}
        res["item2_oscillation"] = {"pass": False, "reason": "never airborne"}
    else:
        ta, te = float(tt[up[0]]), float(tt[up[-1]])
        tl = min(te, t_land) if t_land is not None else te  # end of the span outside land/RTL (item-1 drop/contact/exc)
        res["airborne"] = [ta, te]
        res["t_land"] = t_land
        a = (tt >= ta) & (tt <= te)
        al = (tt >= ta) & (tt <= tl)
        # item 1
        tilt = np.degrees(tilt_rad(np.nan_to_num(q[a], nan=1.0)))
        tilt_s = longest_run_s(tt[a], tilt > TILT_DEG)
        i0 = int(np.searchsorted(tt, t0))
        drop = float(h[i0] - np.nanmin(h[max(i0, 0):][tt[max(i0, 0):] <= tl])) if i0 < len(tt) and tt[i0] <= tl else 0.0
        contact = bool(np.any(h[al] < CONTACT_M))
        am = (tm >= ta) & (tm <= te)
        nan = bool(not np.isfinite(pos[a]).all() or not np.isfinite(q[a]).all() or not np.isfinite(w[a]).all()
                   or not np.isfinite(cmd[am][:, :4]).all())
        exc = None
        if mode == "position" and ref is not None:
            exc = float(np.nanmax(np.hypot(pos[al, 0] - ref[0], pos[al, 1] - ref[1])))
        loc = {"tilt_over_60deg_longest_s": tilt_s, "tilt_max_deg": float(np.max(tilt)), "height_drop_m": drop,
               "ground_contact": contact, "nan": nan, "horizontal_excursion_m": exc}
        loc["pass"] = bool(tilt_s <= TILT_S and drop <= DROP_M and not contact and not nan and (exc is None or exc <= EXCURSION_M))
        res["item1_loc"] = loc
        # item 2
        fin = np.isfinite(pos[a]).all(axis=1) & np.isfinite(w[a]).all(axis=1)
        osc = {}
        tg, wg, fs = uniform(tt[a][fin], np.degrees(w[a][fin]), ta, te)
        skip = [(c, c + NAV_SKIP_S) for c in (nav_changes or [])]
        for i, name in enumerate("pqr"):
            osc[name] = line_detector(wg[i], fs, RATE_BAND, RMS_DEG_S, float(tg[0]), skip)
        osc["position"] = position_limit_cycle(tt[a][fin], pos[a][fin], max(ta, t0), te)
        okm = np.isfinite(cmd[am][:, :4]).all(axis=1)
        _, cg, fsc = uniform(tm[am][okm], cmd[am][okm][:, :4], ta, te)
        chat = [line_detector(cg[i], fsc, CMD_BAND, CMD_LINE_RMS) for i in range(4)]
        osc["command_chatter"] = {"motors": chat, "sustained": any(c["sustained"] for c in chat)}
        osc["pass"] = not any(osc[k]["sustained"] for k in ("p", "q", "r", "position", "command_chatter"))
        res["item2_oscillation"] = osc
    # item 3
    m = (tt >= t0) & (tt <= t1) & np.isfinite(pos).all(axis=1)
    rr, pp = euler_rp(q[m])
    if ref is None:
        ref = np.nanmean(pos[m], axis=0)
        res["ref_source"] = "truth window mean"
    horiz = float(np.sqrt(np.mean((pos[m, 0] - ref[0]) ** 2 + (pos[m, 1] - ref[1]) ** 2)))
    alt = float(np.mean(-pos[m, 2] + ref[2]))
    rp = [float(np.degrees(np.mean(rr))), float(np.degrees(np.mean(pp)))]
    it3 = {"horizontal_rms_m": {"value": horiz, "threshold": HORIZ_RMS[wind], "gated": mode == "position"},
           "altitude_mean_m": {"value": alt, "threshold": ALT_MEAN[sag], "gated": mode == "position"},
           "roll_pitch_mean_deg": {"value": rp, "threshold": RP_MEAN_DEG, "gated": mode == "attitude"}, "samples": int(m.sum())}
    ok = True
    if mode == "position":
        ok = horiz <= HORIZ_RMS[wind] and abs(alt) <= ALT_MEAN[sag]
    else:
        ok = max(abs(rp[0]), abs(rp[1])) <= RP_MEAN_DEG
    it3["pass"] = bool(ok and m.sum() > 0)
    res["item3_steady_state"] = it3
    res["pass"] = bool(res["item1_loc"]["pass"] and res["item2_oscillation"]["pass"] and it3["pass"])
    return res


def load(log, t0, t1):
    from pyulog import ULog
    u = ULog(log, ["sim_ground_truth", "actuator_motors", "trajectory_setpoint", "vehicle_status"])
    ts = u.start_timestamp

    def stamps(d):
        k = "timestamp_sample" if "timestamp_sample" in d else "timestamp"
        return (d[k].astype(np.int64) - ts) * 1e-6

    g = u.get_dataset("sim_ground_truth").data
    o = np.argsort(stamps(g), kind="stable")
    tt = stamps(g)[o]
    pos = np.stack([g[k][o] for k in "xyz"], axis=1).astype(float)
    q = np.stack([g[f"q[{i}]"][o] for i in range(4)], axis=1).astype(float)
    w = np.stack([g[f"angular_velocity[{i}]"][o] for i in range(3)], axis=1).astype(float)
    am = u.get_dataset("actuator_motors").data
    o = np.argsort(stamps(am), kind="stable")
    tm = stamps(am)[o]
    cmd = np.stack([am[f"control[{i}]"][o] for i in range(4)], axis=1).astype(float)
    t_land, nav_changes = None, []
    if "vehicle_status" in [d.name for d in u.data_list]:
        vs = u.get_dataset("vehicle_status").data
        tv = (vs["timestamp"].astype(np.int64) - ts) * 1e-6
        ln = np.flatnonzero(np.isin(vs["nav_state"], LAND_NAV_STATES))
        t_land = float(tv[ln[0]]) if ln.size else None
        nav_changes = [float(x) for x in tv[1:][np.diff(vs["nav_state"]) != 0]]
    ref, src = None, None
    try:
        sp = u.get_dataset("trajectory_setpoint").data
        t = (sp["timestamp"].astype(np.int64) - ts) * 1e-6
        mk = (t >= t0) & (t <= t1)
        r = np.stack([sp[f"position[{i}]"][mk] for i in range(3)], axis=1)
        if np.isfinite(r).all(axis=1).any():
            ref, src = np.nanmedian(r[np.isfinite(r).all(axis=1)], axis=0), "trajectory_setpoint median over window"
    except (KeyError, IndexError):
        pass
    return tt, pos, q, w, tm, cmd, ref, src, t_land, nav_changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--t0", type=float, required=True)
    ap.add_argument("--t1", type=float, required=True)
    ap.add_argument("--wind", action="store_true")
    ap.add_argument("--sag", action="store_true")
    ap.add_argument("--mode", choices=("position", "attitude"), default="position")
    ap.add_argument("--skip-nav-change", action="store_true", help="G4 (Q15): skip rate windows within 3 s after a nav_state change")
    ap.add_argument("--json")
    a = ap.parse_args()
    tt, pos, q, w, tm, cmd, ref, src, t_land, navc = load(a.log, a.t0, a.t1)
    r = evaluate(tt, pos, q, w, tm, cmd, ref, a.t0, a.t1, a.wind, a.sag, a.mode, src or "none", t_land,
                 navc if a.skip_nav_change else None)
    r["log"] = a.log
    s = json.dumps(r, indent=1)
    if a.json:
        open(a.json, "w").write(s + "\n")
    print(s)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
