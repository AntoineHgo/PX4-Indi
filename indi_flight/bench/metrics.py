#!/usr/bin/env python3
"""Metrics for one SITL benchmark run. Pure numpy + pyulog. Runs on the host or in the container.

  metrics.py flight.ulg [--run-json run.json] [--out metrics.json]

Evaluation window = [ULog offboard anchor + OFFBOARD_SETTLE_S, + run.json duration] (sim time = ULog time base),
intersected with the span where vehicle_status.nav_state is 14 (offboard) or 23 (external INDI position mode registered
through the external mode API). The anchor is the first armed vehicle_status sample with nav_state in that set (the real
PX4 transition); run.json t_window_start_us (MAVLink heartbeat at 1 Hz + 3.0 s, jitters by up to ~1 s between same-seed
runs) is only recorded as window.runjson_start_s, and used as fallback if the log has no such sample. The window END is
start + the run.json duration (t_window_end_us - t_window_start_us), so the window length is the same in every run.
Without run.json only the span is used.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

# ULog is imported lazily in main() so the module (and its self-test) works without pyulog.

AXES = ("roll", "pitch", "yaw")


def topic(ulog, name, multi_id=0):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == multi_id:
            return d.data
    return None


def tstamp(d):
    """Sample time [us] of a logged topic dict: timestamp_sample when the field exists and is filled (all > 0), else
    timestamp. Controller-rate topics must use this: their publish stamp `timestamp` jitters by one tick and forms
    zero-dt pairs (a16_s22), the sample stamp does not. Event topics (vehicle_status, ...) keep `timestamp`."""
    ts = d.get("timestamp_sample")
    if ts is not None and len(ts) and np.all(np.asarray(ts) > 0):
        return np.asarray(ts)
    return np.asarray(d["timestamp"])


def ctrl_topic(ulog, name, notes=None, multi_id=0):
    """Controller-rate topic with its time axis replaced: returns a copy of the topic dict whose "timestamp" is tstamp(d)
    (sorted, with every column, when that stamp is not monotonic). notes[name] records the stamp used, whether a sort was
    needed and the number of zero-dt pairs left. The original publish stamp is kept as "timestamp_publish"."""
    d = topic(ulog, name, multi_id)
    if d is None:
        return None
    t = tstamp(d)
    used = "timestamp_sample" if (d.get("timestamp_sample") is not None and t is not d["timestamp"]
                                  and np.array_equal(t, np.asarray(d["timestamp_sample"]))) else "timestamp"
    out = dict(d)
    out["timestamp_publish"] = np.asarray(d["timestamp"])
    sorted_ = bool(len(t) > 1 and (np.diff(t.astype(np.int64)) < 0).any())
    if sorted_:
        o = np.argsort(t, kind="stable")
        out = {k: (np.asarray(v)[o] if np.ndim(v) == 1 and len(v) == len(t) else v) for k, v in out.items()}
        t = t[o]
    out["timestamp"] = t
    if notes is not None:
        notes[name] = {"stamp": used, "sorted": sorted_, "zero_dt_pairs": int((np.diff(t.astype(np.int64)) == 0).sum()) if len(t) > 1 else 0}
    return out


def truth_local_position(ulog, notes=None):
    """Simulator ground-truth position/velocity (NED). Returns (topic dict, source name).
    sim_ground_truth (queue 16, logged at every physics step) when in the log; archived logs fall back to the stock
    vehicle_local_position_groundtruth (queue 1, decimated by the logger); (None, None) if neither."""
    for name in ("sim_ground_truth", "vehicle_local_position_groundtruth"):
        d = ctrl_topic(ulog, name, notes)
        if d is not None:
            return d, name
    return None, None


def rms(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.sqrt(np.mean(x ** 2))) if x.size else None


def zoh(t_src, v_src, t_dst):
    """Zero-order-hold resample of (t_src, v_src) at t_dst; NaN before the first sample."""
    idx = np.searchsorted(t_src, t_dst, side="right") - 1
    out = np.asarray(v_src)[np.clip(idx, 0, None)].astype(float)
    out[idx < 0] = np.nan
    return out


def quat_to_euler(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def qcols(d, prefix):
    return np.column_stack([d[f"{prefix}[{i}]"] for i in range(4)])


OFFBOARD_NAV_STATES = (14, 23)  # 14 offboard, 23 external mode slot used by the INDI position mode


OFFBOARD_SETTLE_S = 3.0  # runner's offboard_settle segment: scenario window starts this long after the transition


def offboard_anchor_us(ulog):
    """Timestamp (us) of the first armed vehicle_status sample with nav_state in OFFBOARD_NAV_STATES; None if none.
    Armed = arming_state == 2 (ARMING_STATE_ARMED); if the topic has no arming_state, every sample counts as armed."""
    s = topic(ulog, "vehicle_status")
    if s is None:
        return None
    ok = np.isin(s["nav_state"], OFFBOARD_NAV_STATES)
    if "arming_state" in s:
        ok &= (np.asarray(s["arming_state"]) == 2)
    idx = np.where(ok)[0]
    return int(s["timestamp"][idx[0]]) if idx.size else None


def offboard_span(ulog):
    s = topic(ulog, "vehicle_status")
    if s is None:
        return None
    t, n = s["timestamp"], s["nav_state"]
    on = np.where(np.isin(n, OFFBOARD_NAV_STATES))[0]
    if not on.size:
        return None
    end = t[on[-1] + 1] if on[-1] + 1 < len(t) else t[-1]
    return int(t[on[0]]), int(end)


def step_metrics(t, x, t0, dur, value, amp_floor):
    """Normalised step response of signal x (time t, s) for a step starting at t0 (s) lasting dur (s)."""
    pre = (t >= t0 - 0.05) & (t <= t0)
    if not pre.any():
        return None
    x0 = float(np.median(x[pre]))
    amp = value - x0
    if abs(amp) < amp_floor:
        return {"amplitude": amp, "note": "amplitude below floor, skipped"}
    m = (t >= t0) & (t <= t0 + dur)
    tt, y = t[m] - t0, (x[m] - x0) / amp

    def first_cross(level):
        i = np.where(y >= level)[0]
        if not i.size:
            return None
        i = i[0]
        if i == 0:
            return float(tt[0])
        return float(tt[i - 1] + (level - y[i - 1]) * (tt[i] - tt[i - 1]) / (y[i] - y[i - 1]))

    t10, t90 = first_cross(0.1), first_cross(0.9)
    out_band = np.where(np.abs(y - 1.0) > 0.05)[0]
    if out_band.size and out_band[-1] == len(y) - 1:
        settle = None  # not settled within the segment
    else:
        settle = float(tt[out_band[-1] + 1]) if out_band.size else 0.0
    return {"amplitude": float(amp), "delay_10pct_s": t10, "rise_10_90_s": (t90 - t10) if t10 is not None and t90 is not None else None,
            "overshoot_pct": float(max(0.0, (y.max() - 1.0) * 100.0)), "settle_5pct_s": settle,
            "final_error_pct": float((y[-1] - 1.0) * 100.0)}


REC_BAND_M = 0.1   # recovery: position error back within this band ...
REC_HOLD_S = 2.0   # ... and staying there for this long


def disturbance_metrics(dist, lp, att, run, w1):
    """Peak deviations and recovery time after the disturbance onset (run.json["disturbance"]["onset_us"], ULog time).

    attitude deviation: tilt angle between the body z axis and its pre-onset value (median of the last 1 s before onset),
      and peak |roll|,|pitch| deviation from the pre-onset median (deg).
    position deviation: from the hold position; horizontal norm for gust_x and gust_diag, |vertical| for payload_add and com_shift.
    recovery_s: from onset to the earliest time t >= t_peak such that the error stays <= REC_BAND_M for REC_HOLD_S
      (up to the end of the evaluation window); None if it never does."""
    t0 = dist["onset_us"]
    prof = dist["profile"]
    res = {"profile": prof, "onset_s": t0 * 1e-6, "recovery_band_m": REC_BAND_M, "recovery_hold_s": REC_HOLD_S}
    # attitude
    ta = att["timestamp"]
    q = qcols(att, "q")
    pre = (ta >= t0 - 1_000_000) & (ta <= t0)
    post = (ta >= t0) & (ta <= w1)
    if pre.any() and post.any():
        roll, pitch, _ = quat_to_euler(q)
        r0, p0 = np.median(roll[pre]), np.median(pitch[pre])
        dr, dp = np.degrees(roll[post] - r0), np.degrees(pitch[post] - p0)

        def zaxis(qq):  # body z axis in world frame
            w, x, y, z = qq[:, 0], qq[:, 1], qq[:, 2], qq[:, 3]
            return np.column_stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])
        z0 = zaxis(q[pre]).mean(axis=0)
        z0 /= np.linalg.norm(z0)
        tilt = np.degrees(np.arccos(np.clip(zaxis(q[post]) @ z0, -1, 1)))
        res.update({"peak_attitude_dev_deg": float(tilt.max()), "peak_roll_dev_deg": float(np.abs(dr).max()),
                    "peak_pitch_dev_deg": float(np.abs(dp).max())})
    # position
    t = lp["timestamp"]
    m = (t >= t0) & (t <= w1)
    ref = run.get("hold_pos_ned") or [float(lp[k][t >= t0][0]) for k in ("x", "y", "z")]
    if m.any():
        dx, dy, dz = lp["x"][m] - ref[0], lp["y"][m] - ref[1], lp["z"][m] - ref[2]
        err = np.abs(dz) if prof in ("payload_add", "com_shift") else np.hypot(dx, dy)
        tt = t[m] * 1e-6
        i_pk = int(np.argmax(err))
        res.update({"position_error_kind": "vertical" if prof in ("payload_add", "com_shift") else "horizontal",
                    "peak_position_dev_m": float(err[i_pk]), "t_peak_s": float(tt[i_pk] - t0 * 1e-6),
                    "peak_dev_north_m": float(dx[np.argmax(np.abs(dx))]), "peak_dev_east_m": float(dy[np.argmax(np.abs(dy))]),
                    "peak_dev_down_m": float(dz[np.argmax(np.abs(dz))]),
                    "final_position_error_m": float(err[-1])})
        rec = None
        for i in range(i_pk, len(tt)):
            if err[i] > REC_BAND_M:
                continue
            # error must stay within the band over [tt[i], tt[i] + REC_HOLD_S]
            j = np.searchsorted(tt, tt[i] + REC_HOLD_S)
            if j >= len(tt):
                break  # window ends before the hold time can be verified
            if not (err[i:j + 1] > REC_BAND_M).any():
                rec = float(tt[i] - t0 * 1e-6)
                break
        res["recovery_s"] = rec
        res["recovered"] = rec is not None
    return res


def motor_fault_metrics(mf, att, asp, am, lp, w1):
    """Post-event metrics for a weakened motor (run.json["motor_fault"]["event_us"], ULog time), window event..w1.

    tilt error: angle between the body z axis and the setpoint z axis (from vehicle_attitude_setpoint q_d), deg.
    attitude_rms_deg: RMS of the tilt error; peak_tilt_error_deg: its max; saturation_time_s: time with any motor
      >= 0.99 or <= 0.01 while airborne; faulty_motor_high_sat_s: time the faulty motor is >= 0.99.
    motor_mean_*: mean actuator_motors control of the faulty motor vs the mean of the others (post event, in the window)."""
    t0, k = mf["event_us"], mf["motor"]
    ks = mf.get("motors") or [k]  # several weakened motors (V' W3): faulty_* metrics cover all of them
    res = {"event_s": t0 * 1e-6, "motor": k, "thrust_scale": mf["thrust_scale"]}
    if len(ks) > 1:
        res["motors"] = list(ks)

    def zaxis(qq):
        w, x, y, z = qq[:, 0], qq[:, 1], qq[:, 2], qq[:, 3]
        return np.column_stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])
    if att is not None and asp is not None:
        ta = att["timestamp"]
        m = (ta >= t0) & (ta <= w1)
        if m.any():
            qd = np.column_stack([asp[f"q_d[{i}]"] for i in range(4)])
            idx = np.clip(np.searchsorted(asp["timestamp"], ta[m], side="right") - 1, 0, len(qd) - 1)
            tilt = np.degrees(np.arccos(np.clip((zaxis(qcols(att, "q")[m]) * zaxis(qd[idx])).sum(axis=1), -1, 1)))
            res.update({"attitude_rms_deg": rms(tilt), "peak_tilt_error_deg": float(tilt.max())})
    if am is not None:
        t = am["timestamp"]
        m = (t >= t0) & (t <= w1)
        cols = [c for c in sorted(c for c in am if c.startswith("control[")) if np.isfinite(am[c]).any()]
        if m.any() and len(cols) > max(ks):
            u = np.column_stack([am[c] for c in cols])[m]
            tm = t[m] * 1e-6
            dt = np.diff(tm, append=tm[-1])
            z = zoh(lp["timestamp"], lp["z"], t[m]) if lp is not None else np.full(len(tm), -5.0)
            air = z < -1.0
            sat = ((u >= 0.99) | (u <= 0.01)).any(axis=1) & air
            res.update({"saturation_time_s": float(dt[sat].sum()),
                        "faulty_motor_high_sat_s": float(dt[(u[:, ks] >= 0.99).any(axis=1) & air].sum()),
                        "motor_mean_faulty": float(u[:, ks].mean()),
                        "motor_mean_others": float(np.delete(u, ks, axis=1).mean())})
    return res




# ---- analytic trajectory (verbatim copy of indi_project/bench/run_scenario.py:323-358; keep in sync) ----
def traj_phase(traj, t):
    """Phase of a closed trajectory: phase rate ramps 0 -> w (smoothstep, ramp_s), cruises, ramps back to 0, and the
    total phase is laps * 2 pi, so the path starts and ends at the hold position with zero velocity."""
    w, tr = traj["w"], traj["ramp_s"]
    tc = 2 * math.pi * traj["laps"] / w - tr
    if t <= 0:
        return 0.0
    if t < tr:
        u = t / tr
        return w * tr * (u ** 3 - u ** 4 / 2)
    if t < tr + tc:
        return w * tr / 2 + w * (t - tr)
    if t < 2 * tr + tc:
        u = (2 * tr + tc - t) / tr
        return 2 * math.pi * traj["laps"] - w * tr * (u ** 3 - u ** 4 / 2)
    return 2 * math.pi * traj["laps"]


def traj_pos(traj, phi):
    """NED offset from the hold position at phase phi (zero at phi = 0)."""
    if traj["shape"] == "lemniscate":  # Gerono lemniscate, size_x x size_y
        return [traj["ax"] * math.sin(phi), traj["ay"] * math.sin(2 * phi), 0.0]
    if traj["shape"] == "circle":  # circle of radius r through the start point, plus a vertical sine (NED z: up = -)
        r = traj["r"]
        return [r * (math.cos(phi) - 1.0), r * math.sin(phi), -traj["z_amp"] * math.sin(phi)]
    if traj["shape"] == "zmulti":  # vertical multisine, harmonics k of the phase with amplitudes a (m)
        return [0.0, 0.0, -sum(a * math.sin(k * phi) for k, a in zip(traj["harm"], traj["amps"]))]
    raise ValueError(traj["shape"])


def traj_pva(traj, t, h=1e-3):
    """Position, velocity and acceleration setpoints (velocity/acceleration by central differences of the path)."""
    p0, pm, pp = (traj_pos(traj, traj_phase(traj, tt)) for tt in (t, t - h, t + h))
    vel = [(pp[i] - pm[i]) / (2 * h) for i in range(3)]
    acc = [(pp[i] - 2 * p0[i] + pm[i]) / (h * h) for i in range(3)]
    return p0, vel, acc


def rate_hz(t_us):
    t_us = np.asarray(t_us, float)
    return float(1e6 / np.median(np.diff(t_us))) if t_us.size > 1 else None


def error_stats(d):
    """d: (N,3) NED error. Same keys as the legacy trajectory block."""
    dh = np.hypot(d[:, 0], d[:, 1])
    d3 = np.linalg.norm(d, axis=1)
    return {"n": int(len(d)), "rms_3d_m": rms(d3), "rms_horizontal_m": rms(dh), "rms_vertical_m": rms(d[:, 2]),
            "max_dev_3d_m": float(np.nanmax(d3)) if len(d3) else None}


def analytic_reference(traj, t0_us, hold_pos, t_us):
    """Analytic NED reference position at ULog timestamps t_us (us): hold_pos + traj_pva(traj, (t_us - t0_us) * 1e-6)[0].
    (traj_pos(traj_phase(.)) is exactly traj_pva(...)[0]; it skips the two finite-difference evaluations.)"""
    ts = (np.asarray(t_us, float) - t0_us) * 1e-6
    off = np.array([traj_pos(traj, traj_phase(traj, float(s))) for s in ts]).reshape(-1, 3)
    return np.asarray(hold_pos, float)[None, :] + off


def trajectory_error_analytic(t_us, pos_ned, traj, t0_us, hold_pos):
    """Error stats of measured NED positions pos_ned (N,3), sampled at ULog times t_us, against the analytic reference.
    No dependence on the logged trajectory_setpoint rate."""
    return error_stats(np.asarray(pos_ned, float) - analytic_reference(traj, t0_us, hold_pos, t_us))


def trajectory_error_zoh(t_us, pos_ned, sp_t_us, sp_pos):
    """LEGACY (defective) error: reference = zero-order hold of the logged trajectory_setpoint position (5 Hz in the
    bench logger, so the held reference lags the true one by ~100 ms on average)."""
    ref = np.column_stack([zoh(sp_t_us, np.asarray(sp_pos)[:, i], t_us) for i in range(3)])
    return error_stats(np.asarray(pos_ned, float) - ref)


def compute(ulog, run):
    out = {"scenario": run.get("scenario"), "controller": run.get("controller"), "seed": run.get("seed"),
           "speed": run.get("speed"), "warnings": []}
    ob = offboard_span(ulog)
    w0, w1 = run.get("t_window_start_us"), run.get("t_window_end_us")
    rj_start = w0
    anchor = offboard_anchor_us(ulog)
    src = "runjson"
    if w0 is None and ob is None:
        raise SystemExit("no scenario window (no run.json window and no offboard span in log)")
    if w0 is None:
        w0, w1 = ob
        src = "offboard_span"
    elif anchor is not None:
        dur = w1 - w0  # nominal duration; both run.json bounds carry the same heartbeat offset
        w0 = int(anchor + OFFBOARD_SETTLE_S * 1e6)
        w1 = w0 + dur
        src = f"ulog_nav_state+{OFFBOARD_SETTLE_S:.1f}"
        if ob is not None:
            w1 = min(w1, ob[1])
    elif ob is not None:
        w0, w1 = max(w0, ob[0]), min(w1, ob[1])
    else:
        out["warnings"].append("no nav_state in (14 offboard, 23 external INDI mode) span found in vehicle_status")
    if src == "runjson":
        out["warnings"].append("window start from run.json (no armed offboard nav_state sample in ULog)")
    out["window"] = {"start_s": w0 * 1e-6, "end_s": w1 * 1e-6, "duration_s": (w1 - w0) * 1e-6,
                     "offboard_span_s": [ob[0] * 1e-6, ob[1] * 1e-6] if ob else None,
                     "start_source": src, "runjson_start_s": rj_start * 1e-6 if rj_start is not None else None,
                     "ulog_anchor_s": anchor * 1e-6 if anchor is not None else None}
    inwin = lambda t: (t >= w0) & (t <= w1)  # noqa: E731

    # ---- rate tracking ----
    out["stamps"] = {}  # per controller-rate topic: stamp used (timestamp_sample | timestamp), sorted?, zero-dt pairs left
    ctl = lambda n: ctrl_topic(ulog, n, out["stamps"])  # noqa: E731
    av, rsp = ctl("vehicle_angular_velocity"), ctl("vehicle_rates_setpoint")
    am = ctl("actuator_motors")
    if av is not None and rsp is not None:
        ta = av["timestamp"]
        m = inwin(ta)
        rt = {}
        for i, ax in enumerate(AXES):
            sp = zoh(rsp["timestamp"], rsp[ax], ta[m])
            rt[ax + "_rms_rad_s"] = rms(sp - av[f"xyz[{i}]"][m])
        out["rate_tracking"] = rt

    # ---- attitude tracking ----
    att, asp = ctl("vehicle_attitude"), ctl("vehicle_attitude_setpoint")
    # INDI POS publishes rates, not vehicle_attitude_setpoint: its q_d is logged in indi_pos_status
    ips = ctl("indi_pos_status")
    if ips is not None and "q_d[0]" in ips:
        asp = ips
    euler = None
    if att is not None:
        ta = att["timestamp"]
        q = qcols(att, "q")
        euler = dict(zip(AXES, quat_to_euler(q)))
        if asp is not None:
            m = inwin(ta)
            qs = np.column_stack([zoh(asp["timestamp"], asp[f"q_d[{i}]"], ta[m]) for i in range(4)])
            ok = np.isfinite(qs).all(axis=1)
            dot = np.abs(np.sum(q[m][ok] * qs[ok], axis=1))
            ang = 2 * np.arccos(np.clip(dot, 0, 1))
            esp = dict(zip(AXES, quat_to_euler(qs[ok])))
            at = {"rotation_angle_rms_deg": math.degrees(rms(ang)) if ang.size else None}
            for ax in AXES:
                e = euler[ax][m][ok] - esp[ax]
                if ax == "yaw":
                    e = wrap(e)
                at[ax + "_rms_deg"] = math.degrees(rms(e)) if e.size else None
            out["attitude_tracking"] = at

    # ---- steps ----
    steps = []
    hold_yaw = run.get("hold_yaw_rad", 0.0)
    for ev in run.get("events", []):
        if not ev.get("step"):
            continue
        t0, dur = ev["t_us"] * 1e-6, ev["dur_s"]
        for ax in (("roll", "pitch") if ev["axis"] == "rollpitch" else (ev["axis"],)):
            if ev["mode"] == "attitude" and euler is not None:
                x = euler[ax]
                if ax == "yaw":
                    x = wrap(x - hold_yaw)
                x = np.degrees(x)
                tt, floor = att["timestamp"] * 1e-6, 1.0
            elif ev["mode"] == "rate" and av is not None:
                x = np.degrees(av[f"xyz[{AXES.index(ax)}]"])
                tt, floor = av["timestamp"] * 1e-6, 10.0
            else:
                continue
            r = step_metrics(tt, x, t0, dur, ev["value"], floor)
            if r is not None:
                name = ev["name"] if ev["axis"] != "rollpitch" else f'{ev["name"]}_{ax}'
                steps.append({"name": name, "t0_s": t0, "dur_s": dur, "from": ev["prev"], "to": ev["value"], **r})
    out["steps"] = steps
    summ = {}
    for k in ("delay_10pct_s", "rise_10_90_s", "overshoot_pct", "settle_5pct_s"):
        v = [s[k] for s in steps if s.get(k) is not None]
        summ[k + "_mean"] = float(np.mean(v)) if v else None
        summ[k + "_max"] = float(np.max(v)) if v else None
        summ[k + "_n"] = len(v)
    summ["n_steps"] = len(steps)
    summ["n_not_settled"] = sum(1 for s in steps if "amplitude" in s and "settle_5pct_s" in s and s["settle_5pct_s"] is None)
    if steps:
        out["step_summary"] = summ

    # ---- position ----
    lp = topic(ulog, "vehicle_local_position")
    if lp is not None:
        t = lp["timestamp"]
        m = inwin(t)
        ref = run.get("hold_pos_ned") or [float(lp[k][m][0]) for k in ("x", "y", "z")]
        d = np.column_stack([lp["x"][m] - ref[0], lp["y"][m] - ref[1], lp["z"][m] - ref[2]])
        dh = np.hypot(d[:, 0], d[:, 1])
        d3 = np.linalg.norm(d, axis=1)
        out["position"] = {"ref_ned": list(map(float, ref)), "rms_3d_m": rms(d3), "rms_horizontal_m": rms(dh),
                           "rms_vertical_m": rms(d[:, 2]), "max_dev_3d_m": float(d3.max()),
                           "max_dev_horizontal_m": float(dh.max()), "max_dev_vertical_m": float(np.abs(d[:, 2]).max())}

    # ---- trajectory scenarios ----
    # trajectory.truth / .estimate: error against the ANALYTIC reference hold_pos_ned + traj_pva(traj, t - t0)[0] at each
    # position sample time (no dependence on the 5 Hz trajectory_setpoint log). truth = sim_ground_truth (every physics
    # step), else vehicle_local_position_groundtruth for archived logs (out["truth_source"]), when logged, estimate = vehicle_local_position. trajectory.zoh_legacy = old ZOH-of-trajectory_setpoint result, kept for
    # the errata only (it rewards a lagging vehicle). The old top-level rms_* keys are gone on purpose.
    tsp = topic(ulog, "trajectory_setpoint")
    gt, out["truth_source"] = truth_local_position(ulog, out["stamps"])
    traj = run.get("trajectory")
    if traj and lp is not None:
        tr = {}
        t0_us, hold = traj.get("t0_us"), run.get("hold_pos_ned")
        if t0_us is None or hold is None:
            tr["time_base"] = {"status": "UNUSABLE", "reason": "run.json trajectory.t0_us or hold_pos_ned missing"}
            out["warnings"].append("trajectory: analytic reference not computed (t0_us / hold_pos_ned missing)")
        else:
            # t0_us = int(sim.t * 1e6), sim.t = MAVLink ATTITUDE time_boot_ms (run_scenario.py:229,563-565): PX4 boot/sim
            # time, the ULog time base, NOT host wall-clock. Guard: it must lie inside the evaluation window.
            ok_tb = w0 <= t0_us <= w1
            tr["time_base"] = {"t0_us": t0_us, "source": "sim time (MAVLink time_boot_ms), same base as t_window_*_us",
                               "status": "ok" if ok_tb else "SUSPECT: t0_us outside evaluation window"}
            if not ok_tb:
                out["warnings"].append("trajectory: t0_us outside the evaluation window, time base suspect; analytic result not trusted")
            for key, d in (("estimate", lp), ("truth", gt)):
                if d is None:
                    tr[key] = None
                    continue
                t = d["timestamp"]
                m = inwin(t)
                if not m.any():
                    tr[key] = None
                    continue
                pos = np.column_stack([d[k][m] for k in ("x", "y", "z")])
                tr[key] = {**trajectory_error_analytic(t[m], pos, traj, t0_us, hold), "rate_hz": rate_hz(t[m])}
            if gt is None:
                out["warnings"].append("trajectory: neither sim_ground_truth nor vehicle_local_position_groundtruth in log, no truth error")
            elif tr.get("truth") is not None:
                # diagnostic only (NOT applied): truth - estimate over the last 1 s before t0, to expose an origin mismatch
                tg = gt["timestamp"]
                mm = (tg >= t0_us - 1_000_000) & (tg <= t0_us)
                if mm.any():
                    off = [float(np.median(gt[k][mm] - zoh(lp["timestamp"], lp[k], tg[mm]))) for k in ("x", "y", "z")]
                    tr["truth_minus_estimate_pre_t0_ned_m"] = off
        if tsp is not None:
            t = lp["timestamp"]
            m = inwin(t)
            pos = np.column_stack([lp[k][m] for k in ("x", "y", "z")])
            sp = np.column_stack([tsp[f"position[{i}]"] for i in range(3)])
            tr["zoh_legacy"] = {**trajectory_error_zoh(t[m], pos, tsp["timestamp"], sp), "setpoint_rate_hz": rate_hz(tsp["timestamp"])}
        out["trajectory"] = tr
    # ---- disturbance scenarios (gust_x, payload_add): only when run.json carries a "disturbance" record ----
    dist = run.get("disturbance")
    if dist and lp is not None and att is not None:
        out["disturbance"] = disturbance_metrics(dist, lp, att, run, w1)

    # ---- plant-fault scenarios (motor_loss_0): only when run.json carries a "motor_fault" record ----
    mf = run.get("motor_fault")
    if mf and "event_us" in mf:
        out["motor_fault"] = motor_fault_metrics(mf, att, ctl("vehicle_attitude_setpoint"), am, lp, w1)

    # ---- control effort + saturation ----
    nmot = 4
    if am is not None:
        t = am["timestamp"]
        cols = [k for k in sorted(k for k in am if k.startswith("control[")) if np.isfinite(am[k]).any()]
        u = np.column_stack([am[k] for k in cols])
        m = inwin(t)
        tm, um = t[m] * 1e-6, u[m]
        dt = np.diff(tm)
        good = dt > 0
        du = np.diff(um, axis=0)[good] / dt[good, None]
        eff = {"n_motors": len(cols), "motor_rate_rms_per_s": rms(du),
               "motor_spread_mean_abs": float(np.mean(np.abs(um - um.mean(axis=1, keepdims=True)))),
               "motor_mean": float(um.mean())}
        z = zoh(lp["timestamp"], lp["z"], t[m]) if lp is not None else np.full(len(tm), -5.0)
        air = z < -1.0
        sat_any = ((um >= 0.99) | (um <= 0.01)).any(axis=1)
        eff["saturation_frac_motors"] = float(sat_any[air].mean()) if air.any() else None
        eff["saturation_frac_high"] = float((um >= 0.99).any(axis=1)[air].mean()) if air.any() else None
        eff["saturation_frac_low"] = float((um <= 0.01).any(axis=1)[air].mean()) if air.any() else None
        nmot = len(cols)
        out["effort"] = eff
    ca = topic(ulog, "control_allocator_status")
    if ca is not None:
        m = inwin(ca["timestamp"])
        if m.any():
            sat = np.column_stack([ca[f"actuator_saturation[{i}]"][m] for i in range(nmot)])
            out["allocator"] = {"n_samples": int(m.sum()), "frac_any_actuator_saturation": float((sat != 0).any(axis=1).mean()),
                                "frac_torque_not_achieved": float((ca["torque_setpoint_achieved"][m] == 0).mean())}
    else:
        out["warnings"].append("control_allocator_status not in log")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ulog")
    ap.add_argument("--run-json")
    ap.add_argument("--out")
    a = ap.parse_args()
    d = os.path.dirname(os.path.abspath(a.ulog))
    rj = a.run_json or os.path.join(d, "run.json")
    run = json.load(open(rj)) if os.path.exists(rj) else {}
    from pyulog import ULog
    res = compute(ULog(a.ulog), run)
    out = a.out or os.path.join(d, "metrics.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
