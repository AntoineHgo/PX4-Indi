#!/usr/bin/env python3
"""Metrics for one SITL benchmark run. Pure numpy + pyulog. Runs on the host or in the container.

  metrics.py flight.ulg [--run-json run.json] [--out metrics.json]

Evaluation window = run.json [t_window_start_us, t_window_end_us] (sim time = ULog time base), intersected with the
span where vehicle_status.nav_state == 14 (offboard). Without run.json only the offboard span is used.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

AXES = ("roll", "pitch", "yaw")


def topic(ulog, name, multi_id=0):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == multi_id:
            return d.data
    return None


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


def offboard_span(ulog):
    s = topic(ulog, "vehicle_status")
    if s is None:
        return None
    t, n = s["timestamp"], s["nav_state"]
    on = np.where(n == 14)[0]
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
    position deviation: from the hold position; horizontal norm for gust_x, |vertical| for payload_add.
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
        err = np.abs(dz) if prof == "payload_add" else np.hypot(dx, dy)
        tt = t[m] * 1e-6
        i_pk = int(np.argmax(err))
        res.update({"position_error_kind": "vertical" if prof == "payload_add" else "horizontal",
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


def compute(ulog, run):
    out = {"scenario": run.get("scenario"), "controller": run.get("controller"), "seed": run.get("seed"),
           "speed": run.get("speed"), "warnings": []}
    ob = offboard_span(ulog)
    w0, w1 = run.get("t_window_start_us"), run.get("t_window_end_us")
    if w0 is None and ob is None:
        raise SystemExit("no scenario window (no run.json window and no offboard span in log)")
    if w0 is None:
        w0, w1 = ob
    elif ob is not None:
        w0, w1 = max(w0, ob[0]), min(w1, ob[1])
    else:
        out["warnings"].append("no nav_state==14 span found in vehicle_status")
    out["window"] = {"start_s": w0 * 1e-6, "end_s": w1 * 1e-6, "duration_s": (w1 - w0) * 1e-6,
                     "offboard_span_s": [ob[0] * 1e-6, ob[1] * 1e-6] if ob else None}
    inwin = lambda t: (t >= w0) & (t <= w1)  # noqa: E731

    # ---- rate tracking ----
    av, rsp = topic(ulog, "vehicle_angular_velocity"), topic(ulog, "vehicle_rates_setpoint")
    if av is not None and rsp is not None:
        ta = av["timestamp"]
        m = inwin(ta)
        rt = {}
        for i, ax in enumerate(AXES):
            sp = zoh(rsp["timestamp"], rsp[ax], ta[m])
            rt[ax + "_rms_rad_s"] = rms(sp - av[f"xyz[{i}]"][m])
        out["rate_tracking"] = rt

    # ---- attitude tracking ----
    att, asp = topic(ulog, "vehicle_attitude"), topic(ulog, "vehicle_attitude_setpoint")
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
        ax = ev["axis"]
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
            steps.append({"name": ev["name"], "t0_s": t0, "dur_s": dur, "from": ev["prev"], "to": ev["value"], **r})
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

    # ---- disturbance scenarios (gust_x, payload_add): only when run.json carries a "disturbance" record ----
    dist = run.get("disturbance")
    if dist and lp is not None and att is not None:
        out["disturbance"] = disturbance_metrics(dist, lp, att, run, w1)

    # ---- control effort + saturation ----
    am = topic(ulog, "actuator_motors")
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
    res = compute(ULog(a.ulog), run)
    out = a.out or os.path.join(d, "metrics.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
