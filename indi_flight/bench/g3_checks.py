#!/usr/bin/env python3
"""G3 per-run checker, pass items 1-3 (GATES.md section 3 "Pass per run" and section 2 shared definitions), plus the G4
command chatter line (GATES.md G4 "Additional": actuator_motors, band 20-100 Hz, peak > 20 x median). Truth only
(sim_ground_truth: x,y,z NED, q FRD->NED, angular_velocity FRD); never the EKF, never the logged command for items 1-3.

  g3_checks.py LOG (--run-json RUN.json | --t0 T0 --t1 T1) [--wind] [--sag] [--mode position|attitude] [--rate-mode] [--json OUT]
  S214/S225 (Q30 B, Q32 A): with --run-json the windows come from run.json["events"] (times t_us are the PX4/ulog clock, minus the ulog
  start_timestamp): item 3 = last 10 s of the `hold` event, item 6 = last 20 s of it, item 4 = the main segment (`traj`),
  item 5 events and the item-2 fault/gust skip = the main-segment start when run.json records a motor fault or a disturbance
  (windows_from_run_json). --t0/--t1 (old use) still work and then none of the new windows exist.
  T0, T1: steady-state window on the ulog time base (seconds since start_timestamp; stamps are timestamp_sample, as
  g4_metrics.py). The window is used as given (spec: last 10 s of a hold >= 20 s after the last transient; the caller picks).

Item 1 LOC (airborne, truth): tilt > 60 deg for > 0.2 s; height below the height at T0 by > 2.0 m (t >= T0);
  ground contact while airborne (height < 0.1 m between take-off and last time above 1 m); NaN in truth or in the four
  motor commands while airborne; horizontal excursion > 5 m (position mode only). Horizontal excursion = max over the item-1
  span [airborne start, min(airborne end, land/RTL start)] of the horizontal distance between the truth position and the
  horizontal position setpoint (trajectory_setpoint x, y) at the same time (setpoint linearly interpolated onto the truth
  timestamps; no zero-order hold; truth samples outside the setpoint's first/last sample excluded; setpoint samples with NaN
  x or y excluded, excluded fraction of the span reported as excursion_sp_nan_frac; no usable sample -> excursion None, skipped).
Item 2 sustained oscillation: truth p,q,r on the uniform grid (g4_metrics.uniform, starts on the first raw sample), Hann PSD,
  4 s windows, 1 s step, band 2-40 Hz; window flagged when the PSD peak > 20 x band median and the rate RMS at the peak
  > 5 deg/s; sustained = flagged in >= 3 consecutive windows with peak frequency within +-10 %. Position limit cycle:
  linearly detrended truth x,y,z, peak-to-peak > 0.3 m in 3 consecutive 10 s windows. Command chatter (G4): the same
  window detector on actuator_motors control[0..3], band 20-100 Hz, peak > 20 x median, no RMS criterion.
  Chatter is computed and reported (item2_oscillation.command_chatter, top-level g4_command_chatter_sustained) for G4
  (GATES.md line ~361 and Q14 A, line ~553); it does NOT decide item 2 or the G3 verdict (item 2 = GATES.md line 304: p, q, r, position).
Item 3 steady-state on [T0,T1]: horizontal RMS about the reference <= 0.15 m calm / 0.30 m with --wind; altitude |mean error|
  (truth height re-zeroed to its median over the first 1 s at rest, D-G3-ZREF) <= 0.10 m calm / 0.20 m with --sag; roll/pitch |mean| <= 1.0 deg in attitude mode.

Item 2 fault windows (S225, Q32 A; Q33): every 4 s rate-line window [w0, w0 + 4) that contains a fault or gust step start is skipped (step_starts =
  t0 and the gust time t0 + 12 s on a Q33 run);
  a skipped window counts as unflagged, so no line chains across it. Telemetry loss/frozen starts are NOT step starts. The skipped
  windows are tabled in the JSON (item2_skipped_windows: start, end, reason; also the Q15 nav-change skips).
Item 4 tracking (position scenario; Q33: the main segment only = run.json g3_timeline [main_start, main_end], the event hover is not
  in it): truth vs trajectory_setpoint (linear interpolation, NaN / outside-range samples excluded), horizontal RMS <= 0.5 m and
  vertical RMS <= 0.3 m.
Item 5 recovery (see item5_recovery; Q33): events = fault start t0 (event hover start) and gust t0 + 12 s (run.json g3_timeline); per
  event (A and B, Q34 S243), A: back within the static reference in <= 5 s, then no excursion > the limit for 5 s; B: position error <= 0.3 m
  and tilt error vs q_d <= 3 deg on every sample in [event + 5 s, event + 10 s]. Reference per mode: position = hover setpoint
  (trajectory_setpoint, 3-D 0.3 m, plus tilt 3 deg vs q_d as in GATES 3 item 5); attitude / stabilized = q_d (level, zero sticks; tilt 3 deg); rate mode = n/a.
  The wind ramp is not scored.
Item 6 rate mode (--rate-mode, acro with zero sticks): per-axis truth body-rate RMS (p, q, r) <= 5 deg/s over the last 20 s of the hold.

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
    position reference exists; horizontal excursion LOC skipped). Horizontal excursion is measured against the time-matched
    position setpoint (see Item 1), not against the fixed hold reference.
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
CMD_RMS_HZ = 2.0           # Q14 rule: chatter line RMS integrated over peak +-2 Hz (S175 width fix; was +-2 bins = +-0.5 Hz)
CMD_LINE_RMS = 5e-4        # Q14 A: one DShot step of full scale; chatter needs line RMS >= this as well as ratio > 20
NAV_SKIP_S = 3.0           # Q15 A: rate windows overlapping the 3 s after a nav_state change are skipped
POS_WIN_S, POS_P2P_M = 10.0, 0.3
HORIZ_RMS = (0.15, 0.30)   # calm, wind
ALT_MEAN = (0.10, 0.20)    # calm, sag
RP_MEAN_DEG = 1.0
LAND_NAV_STATES = (5, 18)  # RTL, AUTO_LAND (vehicle_status.nav_state)
ITEM3_LAST_S, ITEM6_LAST_S = 10.0, 20.0      # S214: item 3 window = last 10 s of the hold, item 6 = last 20 s
TRACK_H_RMS_M, TRACK_V_RMS_M = 0.5, 0.3      # item 4
REC_POS_M, REC_TILT_DEG, REC_TIME_S, REC_QUIET_S = 0.3, 3.0, 5.0, 5.0   # item 5
REC_B_FROM_S, REC_B_TO_S = 5.0, 10.0   # item 5 part B window after the event (Q34, S243)
RATE_HOLD_RMS_DPS = 5.0                      # item 6
STEP_TOL_S = 0.5                             # two step starts closer than this are one event


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


def line_detector(xg, fs, band, min_rms=None, t_start=0.0, skip=(), rms_hz=None, skip_points=()):
    """xg (n,) uniform, first sample at time t_start. Returns dict: sustained bool, lines [(f_hz, first_window_start_index,
    n_windows)], flagged windows. skip: [(ta, tb)] intervals; a window overlapping one is not evaluated (counts as unflagged,
    so it breaks a run) and is counted in skipped_windows (Q15). Also reports max_ratio (largest peak/median over the evaluated
    windows) with the line RMS (peak +-2 bins) of that window, and max_rms_ratio_flagged (largest line RMS among windows with
    ratio > PEAK_RATIO; None if none) (Q14). rms_hz: line RMS integrated over peak +-rms_hz (bins = round(rms_hz/df));
    None keeps +-2 bins (rate detector). skip_points: [t] fault / gust step starts (S225): a window [w0, w0 + 4) with
    w0 <= t < w1 is skipped exactly like a skip interval; the skipped windows are returned as `skipped`: [(start, end, reason)]."""
    from scipy.signal import periodogram
    n, step = int(round(WIN_S * fs)), int(round(STEP_S * fs))
    hb = 2 if rms_hz is None else int(round(rms_hz * WIN_S))
    flags = []  # per window: peak freq if flagged else None
    skipped, skipped_tab, max_ratio, rms_at_max, max_rms_fl = 0, [], 0.0, None, None
    for s in range(0, len(xg) - n + 1, step):
        w0, w1 = t_start + s / fs, t_start + (s + n) / fs
        why = [f"fault/gust step start at {tp:.3f} s" for tp in skip_points if w0 <= tp < w1]
        why += [f"nav_state change within 3 s before {tb - NAV_SKIP_S:.3f} s" for ta, tb in skip if w0 < tb and w1 > ta]
        if why:
            skipped += 1
            skipped_tab.append((float(w0), float(w1), "; ".join(why)))
            flags.append(None)
            continue
        f, P = periodogram(xg[s:s + n], fs, window="hann", detrend="constant", scaling="density")
        b = (f >= band[0]) & (f <= band[1])
        fb, Pb = f[b], P[b]
        k = int(np.argmax(Pb))
        ratio = float(Pb[k] / np.median(Pb))
        kk = np.flatnonzero(b)[k]
        rms = float(np.sqrt(np.sum(P[max(kk - hb, 0):kk + hb + 1]) * (f[1] - f[0])))
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
            "skipped_windows": skipped, "skipped": skipped_tab, "max_ratio": max_ratio, "rms_at_max_ratio": rms_at_max,
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


def horizontal_excursion(t, pos, tsp, xysp):
    """Max |truth xy - setpoint xy| over the span samples t (n,), pos (n,3). Frame: no alignment is applied, truth
    (sim_ground_truth x,y NED) and trajectory_setpoint x,y are compared as logged -- the same direct comparison the
    existing check makes between truth and the setpoint-derived hold reference (item 3, ref from trajectory_setpoint).
    Returns (excursion or None, excluded fraction of the span). Span samples bracketed by a setpoint sample with NaN x or y, outside the first/last setpoint sample, or with
    non-finite truth are excluded."""
    n = len(t)
    if n == 0:
        return None, None
    tsp, xysp = np.asarray(tsp, float), np.asarray(xysp, float)
    o = np.argsort(tsp, kind="stable")
    ts, xs, ys = tsp[o], xysp[o, 0], xysp[o, 1]
    if len(ts) == 0 or not (np.isfinite(xs) & np.isfinite(ys)).any():
        return None, 1.0
    # np.interp over ALL raw samples: a truth sample bracketed by a NaN setpoint sample gets NaN and is excluded
    # (no interpolation across NaN gaps).
    sx, sy = np.interp(t, ts, xs), np.interp(t, ts, ys)
    inside = (t >= ts[0]) & (t <= ts[-1]) & np.isfinite(sx) & np.isfinite(sy) & np.isfinite(pos[:, :2]).all(axis=1)
    frac = float(1.0 - inside.sum() / n)
    if not inside.any():
        return None, frac
    d = np.hypot(pos[inside, 0] - sx[inside], pos[inside, 1] - sy[inside])
    return float(np.max(d)), frac


def windows_from_run_json(rj, start_s):
    """S214 / S225 windows from run.json (pure). rj: run.json dict; start_s: ulog start_timestamp in seconds. run.json event times
    (events[].t_us, motor_fault, disturbance) are on the PX4 clock = ulog timestamps, so t_ulog = t_us * 1e-6 - start_s.
    Returns {main: {name, t, dur_s} | None, hold: {t, dur_s} | None, item3: [t0, t1] | None, item6: [t0, t1] | None,
    track: [t, t + dur] | None (position scenario only), step_starts: [t], item5_events: [t], fault, gust, timeline}. Main segment = the
    `traj` (position) or `stick` event; hold = the `hold` event; item 3 = last ITEM3_LAST_S s of the hold, item 6 = last ITEM6_LAST_S s.
    Q33 runs (run.json g3_timeline, written by g3_run.finalize): item 4 window = main segment [main_start, main_end] only; step_starts
    (item-2 skip points) = t0 when the run has a fault or a wind profile, plus the gust time t0 + 12 s when it has wind; item5_events =
    the fault start t0 (when a motor fault is on) and the gust time (when wind is on); the wind ramp and the sag are not events; every
    time comes from g3_timeline. Older runs (no g3_timeline, no `event` segment): the S225 reading, the main-segment start is the
    one step start and the one item 5 event. Telemetry loss / frozen and the sag ramp are never step starts."""
    ev = {e["name"]: e for e in rj.get("events", [])}
    main_name = "traj" if "traj" in ev else ("stick" if "stick" in ev else None)
    out = {"main": None, "hold": None, "item3": None, "item6": None, "track": None, "step_starts": [], "fault": False, "gust": False,
           "item5_events": []}
    tl = rj.get("g3_timeline")
    if "event" in ev and tl is None:   # Q33 scenario without the event times: fail loud, never score it with the S225 anchor
        raise ValueError("run.json has an 'event' segment but no g3_timeline (Q33 runs record it in finalize)")
    if main_name and tl is not None:   # Q33: every time is read from g3_timeline (us, run.json event clock), none re-derived
        c = lambda us: us * 1e-6 - start_s   # noqa: E731
        out["main"] = {"name": main_name, "t": c(tl["main_start_us"]), "dur_s": (tl["main_end_us"] - tl["main_start_us"]) * 1e-6}
        out["fault"], out["gust"] = bool(tl["fault_on"]), bool(tl["wind_on"])
        if main_name == "traj":
            out["track"] = [c(tl["main_start_us"]), c(tl["main_end_us"])]     # item 4: the main segment only, not the event hover
        t0 = c(tl["event_t0_us"])
        out["item5_events"] = ([t0] if out["fault"] else []) + ([c(tl["gust_us"])] if out["gust"] else [])   # fault start, gust
        out["step_starts"] = ([t0] if out["fault"] or out["gust"] else []) + ([c(tl["gust_us"])] if out["gust"] else [])
        out["timeline"] = {k[:-3] + "_s": (None if v is None else c(v)) for k, v in tl.items() if k.endswith("_us")}   # ulog base, s
    elif main_name:
        e = ev[main_name]
        out["main"] = {"name": main_name, "t": e["t_us"] * 1e-6 - start_s, "dur_s": float(e["dur_s"])}
        out["fault"] = bool(rj.get("motor_fault"))
        out["gust"] = bool(rj.get("disturbance"))
        if out["fault"] or out["gust"]:
            out["step_starts"] = [out["main"]["t"]]
        out["item5_events"] = list(out["step_starts"])
        if main_name == "traj":
            out["track"] = [out["main"]["t"], out["main"]["t"] + out["main"]["dur_s"]]
    if "hold" in ev:
        t = ev["hold"]["t_us"] * 1e-6 - start_s
        d = float(ev["hold"]["dur_s"])
        out["hold"] = {"t": t, "dur_s": d}
        if d >= ITEM6_LAST_S:
            out["item3"] = [t + d - ITEM3_LAST_S, t + d]
            out["item6"] = [t + d - ITEM6_LAST_S, t + d]
    return out


def _interp_sp(t, tsp, vals):
    """Linear interpolation of setpoint columns vals (k,m) onto t (n,); NaN where a bracketing sample is NaN, False in `inside`
    outside the first/last setpoint sample (same rule as horizontal_excursion)."""
    tsp, vals = np.asarray(tsp, float), np.asarray(vals, float)
    o = np.argsort(tsp, kind="stable")
    ts, v = tsp[o], vals[o]
    out = np.stack([np.interp(t, ts, v[:, j]) for j in range(v.shape[1])], axis=1)
    inside = (t >= ts[0]) & (t <= ts[-1]) & np.isfinite(out).all(axis=1) if len(ts) else np.zeros(len(t), bool)
    return out, inside


def item4_tracking(tt, pos, sp_xyz, win, z_rest):
    """Item 4: horizontal RMS <= TRACK_H_RMS_M and vertical RMS <= TRACK_V_RMS_M of the truth position against the time-matched
    trajectory_setpoint over win = [t_a, t_b] (the `traj` event). Height error = -(z - z_rest) + z_sp (D-G3-ZREF as item 3)."""
    if win is None or sp_xyz is None:
        return {"applicable": False, "pass": True, "note": "no traj event (stick scenario) or no trajectory_setpoint"}
    m = (tt >= win[0]) & (tt <= win[1]) & np.isfinite(pos).all(axis=1)
    sp, inside = _interp_sp(tt[m], sp_xyz[0], sp_xyz[1])
    if not inside.any():
        return {"applicable": True, "pass": False, "note": "no usable sample", "window_s": list(win)}
    d = pos[m][inside]
    dx, dy = d[:, 0] - sp[inside, 0], d[:, 1] - sp[inside, 1]
    dz = -(d[:, 2] - z_rest) + sp[inside, 2]
    h, v = float(np.sqrt(np.mean(dx ** 2 + dy ** 2))), float(np.sqrt(np.mean(dz ** 2)))
    return {"applicable": True, "window_s": list(win), "samples": int(inside.sum()),
            "horizontal_rms_m": {"value": h, "threshold": TRACK_H_RMS_M}, "vertical_rms_m": {"value": v, "threshold": TRACK_V_RMS_M},
            "pass": bool(h <= TRACK_H_RMS_M and v <= TRACK_V_RMS_M)}


def _tilt_error_deg(q, qd):
    """Angle [deg] between the body z axes of q and qd (n,4 w,x,y,z), yaw excluded."""
    def zax(a):
        w, x, y, z = a.T
        return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], axis=1)
    return np.degrees(np.arccos(np.clip(np.sum(zax(q) * zax(qd), axis=1), -1.0, 1.0)))


def item5_recovery(tt, pos, q, sp_xyz, att_sp, events, z_rest=0.0):
    """Item 5 (GATES 3: "after each injected event (gust, fault start) back within 0.3 m and 3 deg of the pre-event reference in <= 5 s
    and no re-excursion > 0.3 m for 5 s"). events: [t] injected-event times (fault start t0, gust t0 + 12 s; Q33).
    Reference = the time-matched setpoint (trajectory_setpoint position / vehicle_attitude_setpoint q_d): the events are in the event hover,
    where it is the static hover point / level attitude. The caller passes sp_xyz only in position mode and att_sp only in attitude mode
    (evaluate), so each mode has one reference. In band at time t = 3-D position error <= REC_POS_M (when sp_xyz) and tilt
    error <= REC_TILT_DEG (when att_sp). t_rec = first t >= event with the vehicle in band; pass when t_rec - event <= REC_TIME_S and the
    position error (tilt error when there is no position reference) stays <= its limit for REC_QUIET_S after t_rec. No reference at all
    or no event -> not applicable (pass)."""
    if not events:
        return {"applicable": False, "pass": True, "note": "no fault or gust step in this run", "events": []}
    ok = np.isfinite(pos).all(axis=1)
    err_pos = np.full(len(tt), np.nan)
    err_att = np.full(len(tt), np.nan)
    if sp_xyz is not None:
        sp, inside = _interp_sp(tt, sp_xyz[0], sp_xyz[1])
        d = np.stack([pos[:, 0] - sp[:, 0], pos[:, 1] - sp[:, 1], -(pos[:, 2] - z_rest) + sp[:, 2]], axis=1)
        err_pos = np.where(inside & ok, np.sqrt(np.sum(d ** 2, axis=1)), np.nan)
    if att_sp is not None and len(att_sp[0]):
        o = np.argsort(att_sp[0], kind="stable")
        ta_, qa = np.asarray(att_sp[0])[o], np.asarray(att_sp[1])[o]
        k = np.clip(np.searchsorted(ta_, tt, side="right") - 1, 0, len(ta_) - 1)
        err_att = np.where((tt >= ta_[0]) & np.isfinite(q).all(axis=1) & np.isfinite(qa[k]).all(axis=1), _tilt_error_deg(q, qa[k]), np.nan)
    have_pos, have_att = bool(np.isfinite(err_pos).any()), bool(np.isfinite(err_att).any())
    if not (have_pos or have_att):
        return {"applicable": False, "pass": True, "note": "no position or attitude reference in the log", "events": list(events)}
    quiet_err, quiet_lim = (err_pos, REC_POS_M) if have_pos else (err_att, REC_TILT_DEG)
    inband = np.ones(len(tt), bool)
    if have_pos:
        inband &= err_pos <= REC_POS_M
    if have_att:
        inband &= err_att <= REC_TILT_DEG
    rows, allok = [], True
    for te in events:
        after = np.flatnonzero((tt >= te) & inband)
        if after.size == 0:
            rows.append({"t_event": te, "t_recover_s": None, "pass_a": False, "pass": False, "reason": "never back in band"})
            allok = False
            continue
        tr = float(tt[after[0]])
        sel = (tt >= tr) & (tt <= tr + REC_QUIET_S)
        reex = float(np.nanmax(quiet_err[sel])) if np.isfinite(quiet_err[sel]).any() else None
        full = float(tt[-1]) >= tr + REC_QUIET_S - 1e-9
        good_a = bool(tr - te <= REC_TIME_S and full and (reex is not None and reex <= quiet_lim))
        # part B (Q34, S243): every sample in [te + 5, te + 10] has position error <= REC_POS_M and tilt error <= REC_TILT_DEG
        selb = (tt >= te + REC_B_FROM_S) & (tt <= te + REC_B_TO_S)
        fullb = float(tt[-1]) >= te + REC_B_TO_S - 1e-9
        b_pos = float(np.nanmax(err_pos[selb])) if have_pos and np.isfinite(err_pos[selb]).any() else None
        b_att = float(np.nanmax(err_att[selb])) if have_att and np.isfinite(err_att[selb]).any() else None
        good_b = bool(fullb and (not have_pos or (b_pos is not None and b_pos <= REC_POS_M)) and (not have_att or (b_att is not None and b_att <= REC_TILT_DEG)))
        good = good_a and good_b
        rows.append({"t_event": te, "t_recover_s": tr - te, "max_quiet_err": reex, "quiet_quantity": "position_m" if have_pos else "tilt_deg",
                     "log_covers_quiet_window": full, "pass_a": good_a, "b_max_pos_m": b_pos, "b_max_tilt_deg": b_att,
                     "log_covers_b_window": fullb, "pass_b": good_b, "pass": good})
        allok &= good
    return {"applicable": True, "events": rows, "limits": {"pos_m": REC_POS_M, "tilt_deg": REC_TILT_DEG, "time_s": REC_TIME_S,
            "quiet_s": REC_QUIET_S}, "uses": {"position": have_pos, "attitude": have_att}, "pass": bool(allok)}


def item6_rate_hold(tt, w, win):
    """Item 6 (rate mode, zero sticks): per-axis truth body-rate RMS over win (last ITEM6_LAST_S s of the hold) <= RATE_HOLD_RMS_DPS deg/s
    on each of p, q, r (no mean removal: a drift counts). Reports the vector RMS too (not gated)."""
    if win is None:
        return {"applicable": False, "pass": False, "note": "no hold window"}
    m = (tt >= win[0]) & (tt <= win[1]) & np.isfinite(w).all(axis=1)
    if not m.any():
        return {"applicable": True, "pass": False, "note": "no samples", "window_s": list(win)}
    d = np.degrees(w[m])
    rms = np.sqrt(np.mean(d ** 2, axis=0))
    return {"applicable": True, "window_s": list(win), "samples": int(m.sum()), "rms_dps": {"p": float(rms[0]), "q": float(rms[1]), "r": float(rms[2])},
            "vector_rms_dps": float(np.sqrt(np.sum(rms ** 2))), "threshold": RATE_HOLD_RMS_DPS, "pass": bool(np.all(rms <= RATE_HOLD_RMS_DPS))}


def evaluate(tt, pos, q, w, tm, cmd, ref, t0, t1, wind=False, sag=False, mode="position", ref_source="given", t_land=None, nav_changes=None, sp=None,
             step_starts=None, track_win=None, event_times=None, rate_mode=False, item6_win=None, sp_xyz=None, att_sp=None, hold_win=None):
    """nav_changes: times [s] of vehicle_status.nav_state changes; if given (G4, Q15) the rate detector skips windows
    overlapping [t, t + NAV_SKIP_S]. tt (n,), pos (n,3) NED, q (n,4), w (n,3) rad/s truth; tm (m,), cmd (m,4); ref (3,) NED hold point or None.
    sp: (t_sp (k,), xy_sp (k,2)) trajectory_setpoint x,y on the same time base and frame as tt/pos, or None.
    S214 / S225 (all optional, from windows_from_run_json): step_starts [t]: item-2 rate windows containing one are skipped; track_win
    [ta, tb] and sp_xyz (t_sp, xyz_sp (k,3)): item 4; event_times [t], sp_xyz, att_sp (t_qd, q_d (k,4)): item 5; rate_mode + item6_win
    [ta, tb]: item 6. hold_win [h0, h1] (S227): item-2 position limit cycle = 3 x 10 s windows from the hold start h0 (to min(h1, end of
    flight)); without it (old --t0/--t1 use) the windows start at max(airborne start, t0). Items 4-6 enter res["pass"] only when applicable."""
    h = -pos[:, 2]
    h = h - h[0] if np.isfinite(h[0]) else h
    up = np.flatnonzero(np.isfinite(h) & (h > AIRBORNE_M))
    res = {"window_s": [t0, t1], "mode": mode, "wind": wind, "sag": sag, "ref_source": ref_source}
    if up.size == 0:
        res["airborne"] = None
        res["item1_loc"] = {"pass": False, "reason": "never airborne"}
        res["item2_oscillation"] = {"pass": False, "reason": "never airborne"}
        res["g4_command_chatter_sustained"] = None
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
        exc, nan_frac = None, None
        if mode == "position" and sp is not None:
            exc, nan_frac = horizontal_excursion(tt[al], pos[al], sp[0], sp[1])
        loc = {"tilt_over_60deg_longest_s": tilt_s, "tilt_max_deg": float(np.max(tilt)), "height_drop_m": drop,
               "ground_contact": contact, "nan": nan, "horizontal_excursion_m": exc,
               "excursion_sp_nan_frac": nan_frac}
        loc["pass"] = bool(tilt_s <= TILT_S and drop <= DROP_M and not contact and not nan and (exc is None or exc <= EXCURSION_M))
        res["item1_loc"] = loc
        # item 2
        fin = np.isfinite(pos[a]).all(axis=1) & np.isfinite(w[a]).all(axis=1)
        osc = {}
        tg, wg, fs = uniform(tt[a][fin], np.degrees(w[a][fin]), ta, te)
        skip = [(c, c + NAV_SKIP_S) for c in (nav_changes or [])]
        for i, name in enumerate("pqr"):
            osc[name] = line_detector(wg[i], fs, RATE_BAND, RMS_DEG_S, float(tg[0]), skip, skip_points=list(step_starts or []))
        res["item2_skipped_windows"] = [{"start_s": a0, "end_s": a1, "reason": why} for a0, a1, why in osc["p"]["skipped"]]  # same windows for p, q, r
        res["item2_step_starts"] = list(step_starts or [])
        ps, pe = (max(ta, hold_win[0]), min(te, hold_win[1])) if hold_win else (max(ta, t0), te)   # S227: windows from the hold start
        osc["position"] = position_limit_cycle(tt[a][fin], pos[a][fin], ps, pe)
        okm = np.isfinite(cmd[am][:, :4]).all(axis=1)
        _, cg, fsc = uniform(tm[am][okm], cmd[am][okm][:, :4], ta, te)
        chat = [line_detector(cg[i], fsc, CMD_BAND, CMD_LINE_RMS, rms_hz=CMD_RMS_HZ) for i in range(4)]
        osc["command_chatter"] = {"motors": chat, "sustained": any(c["sustained"] for c in chat)}
        osc["pass"] = not any(osc[k]["sustained"] for k in ("p", "q", "r", "position"))  # GATES 304: chatter is G4, not item 2
        res["item2_oscillation"] = osc
        res["g4_command_chatter_sustained"] = bool(osc["command_chatter"]["sustained"])
    # item 3
    m = (tt >= t0) & (tt <= t1) & np.isfinite(pos).all(axis=1)
    rr, pp = euler_rp(q[m])
    if ref is None:
        ref = np.nanmean(pos[m], axis=0)
        res["ref_source"] = "truth window mean"
    horiz = float(np.sqrt(np.mean((pos[m, 0] - ref[0]) ** 2 + (pos[m, 1] - ref[1]) ** 2)))
    z_rest = float(np.nanmedian(pos[tt <= tt[0] + 1.0, 2]))   # D-G3-ZREF: estimator z origin = rest position
    alt = float(np.mean(-(pos[m, 2] - z_rest) + ref[2]))
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
    # items 4-6 (S214): only when the caller passes the windows (run.json); otherwise the old items-1-3 verdict
    sp_xyz_ok = sp_xyz if (sp_xyz is not None and len(sp_xyz[0])) else None
    if track_win is not None or event_times is not None or rate_mode:
        res["item4_tracking"] = item4_tracking(tt, pos, sp_xyz_ok, track_win, z_rest) if mode == "position" else \
            {"applicable": False, "pass": True, "note": "item 4 is for the position scenario only"}
        # Q33 reference: position mode = the hover setpoint (trajectory_setpoint, position only); attitude / stabilized = q_d (level,
        # zero sticks); rate mode (acro) = not applicable
        res["item5_recovery"] = {"applicable": False, "pass": True, "note": "rate mode: item 5 not applicable (Q33)", "events": list(event_times or [])} \
            if rate_mode else item5_recovery(tt, pos, q, sp_xyz_ok if mode == "position" else None, att_sp,
                                             event_times or [], z_rest)
        res["item6_rate_hold"] = item6_rate_hold(tt, w, item6_win) if rate_mode else {"applicable": False, "pass": True, "note": "not a rate-mode run"}
    p456 = all(res[k]["pass"] for k in ("item4_tracking", "item5_recovery", "item6_rate_hold") if k in res)
    res["pass"] = bool(res["item1_loc"]["pass"] and res["item2_oscillation"]["pass"] and it3["pass"] and p456)
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


def load_setpoint_xy(log):
    """(t_sp, xy_sp) trajectory_setpoint position x,y on the ulog time base (stamps timestamp), or None."""
    from pyulog import ULog
    u = ULog(log, ["trajectory_setpoint"])
    try:
        sp = u.get_dataset("trajectory_setpoint").data
    except (KeyError, IndexError, ValueError):
        return None
    t = (sp["timestamp"].astype(np.int64) - u.start_timestamp) * 1e-6
    return t, np.stack([sp["position[0]"], sp["position[1]"]], axis=1).astype(float)


def load_setpoint_xyz(log):
    """(t_sp, xyz_sp (k,3)) trajectory_setpoint position on the ulog time base, or None."""
    from pyulog import ULog
    u = ULog(log, ["trajectory_setpoint"])
    try:
        sp = u.get_dataset("trajectory_setpoint").data
    except (KeyError, IndexError, ValueError):
        return None
    t = (sp["timestamp"].astype(np.int64) - u.start_timestamp) * 1e-6
    return t, np.stack([sp[f"position[{i}]"] for i in range(3)], axis=1).astype(float)


def load_att_setpoint(log):
    """(t, q_d (k,4)) vehicle_attitude_setpoint on the ulog time base, or None."""
    from pyulog import ULog
    u = ULog(log, ["vehicle_attitude_setpoint"])
    try:
        d = u.get_dataset("vehicle_attitude_setpoint").data
    except (KeyError, IndexError, ValueError):
        return None
    t = (d["timestamp"].astype(np.int64) - u.start_timestamp) * 1e-6
    return t, np.stack([d[f"q_d[{i}]"] for i in range(4)], axis=1).astype(float)


def ulog_start_s(log):
    from pyulog import ULog
    return ULog(log, ["vehicle_status"]).start_timestamp * 1e-6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--run-json", help="S214: run.json of the run; derives the item 3 / 4 / 5 / 6 windows and the item-2 step starts")
    ap.add_argument("--t0", type=float, help="old use: steady-state window start (ulog base s); ignored for item 3 with --run-json")
    ap.add_argument("--t1", type=float, help="old use: steady-state window end")
    ap.add_argument("--rate-mode", action="store_true", help="item 6 applies (rate mode, zero sticks); needs --run-json")
    ap.add_argument("--wind", action="store_true")
    ap.add_argument("--sag", action="store_true")
    ap.add_argument("--mode", choices=("position", "attitude"), default="position")
    ap.add_argument("--skip-nav-change", action="store_true", help="G4 (Q15): skip rate windows within 3 s after a nav_state change")
    ap.add_argument("--json")
    a = ap.parse_args()
    kw, win = {}, None
    if a.run_json:
        win = windows_from_run_json(json.load(open(a.run_json)), ulog_start_s(a.log))
        if win["item3"] is None:
            ap.error("run.json has no hold event of >= 20 s: no S214 window (use --t0/--t1 for an old run)")
        a.t0, a.t1 = win["item3"]
        sp_xyz = load_setpoint_xyz(a.log)
        kw = dict(step_starts=win["step_starts"], track_win=win["track"], event_times=win["item5_events"], sp_xyz=sp_xyz,
                  att_sp=load_att_setpoint(a.log), rate_mode=a.rate_mode, item6_win=win["item6"],
                  hold_win=[win["hold"]["t"], win["hold"]["t"] + win["hold"]["dur_s"]])
    elif a.t0 is None or a.t1 is None or a.rate_mode:
        ap.error("give --run-json, or --t0 and --t1 (and no --rate-mode)")
    tt, pos, q, w, tm, cmd, ref, src, t_land, navc = load(a.log, a.t0, a.t1)
    r = evaluate(tt, pos, q, w, tm, cmd, ref, a.t0, a.t1, a.wind, a.sag, a.mode, src or "none", t_land,
                 navc if a.skip_nav_change else None, sp=load_setpoint_xy(a.log), **kw)
    if win is not None:
        r["windows_run_json"] = win
    r["log"] = a.log
    s = json.dumps(r, indent=1)
    if a.json:
        open(a.json, "w").write(s + "\n")
    print(s)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
