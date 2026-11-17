#!/usr/bin/env python3
"""T127 second-key attitude-step metrics (independent re-implementation).

Usage: t127_step_metrics_key.py FLIGHT_DIR OUT_MD

FLIGHT_DIR holds flight.ulg and run.json (e.g. .../steps_seed1/step_roll_indi).
Writes a markdown table (one row per variant) to OUT_MD and prints it.

Variants per flight:
  est_det   estimator (vehicle_attitude), t_on detected from the setpoint
  est_fix   estimator, t_on = window start + 2.0 s
  gt_det    ground truth (vehicle_attitude_groundtruth), t_on as est_det
  gt_fix    ground truth, t_on = window start + 2.0 s
"""
import json
import os
import sys

import numpy as np
from pyulog import ULog

AMP = {"roll": 15.0, "pitch": 15.0, "yaw": 45.0}
T_STEP_US = 2.0e6
T_WIN_US = 3.0e6
T_REF_US = 1.5e6


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def quat_stack(data, prefix):
    q = np.stack([data[f"{prefix}[{i}]"] for i in range(4)], axis=1).astype(float)
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def euler_deg(q):
    """ZYX (yaw-pitch-roll) Euler angles of quaternion rows [w, x, y, z], degrees."""
    w, x, y, z = q.T
    roll = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return {"roll": np.degrees(roll), "pitch": np.degrees(pitch), "yaw": np.degrees(yaw)}


def unwrap_deg(a):
    return np.degrees(np.unwrap(np.radians(a)))


def first(mask):
    idx = np.nonzero(mask)[0]
    return int(idx[0]) if idx.size else None


def step_metrics(t_us, y, amp, t_on_us):
    m = (t_us >= t_on_us) & (t_us < t_on_us + T_WIN_US)
    tr = (t_us[m] - t_on_us) / 1000.0  # ms relative to t_on
    yy = y[m]
    i10 = first(yy >= 0.1 * amp)
    i90 = first(yy >= 0.9 * amp)
    rise = tr[i90] - tr[i10] if (i10 is not None and i90 is not None) else float("nan")
    overshoot = max(0.0, (yy.max() - amp) / amp * 100.0)
    bad = np.nonzero(np.abs(yy - amp) > 0.02 * amp)[0]
    if bad.size == 0:
        settle = 0.0
    elif bad[-1] + 1 < yy.size:
        settle = tr[bad[-1] + 1]
    else:
        settle = float("nan")
    return rise, overshoot, settle


def process(folder):
    run = json.load(open(os.path.join(folder, "run.json")))
    axis = run["scenario"].split("_")[1]
    amp = AMP[axis]
    t0 = int(run["t_window_start_us"])
    u = ULog(os.path.join(folder, "flight.ulg"))

    att = topic(u, "vehicle_attitude")
    sp = topic(u, "vehicle_attitude_setpoint")
    gt = topic(u, "vehicle_attitude_groundtruth")

    t_a = att["timestamp"].astype(np.int64)
    est = euler_deg(quat_stack(att, "q"))[axis]
    t_s = sp["timestamp"].astype(np.int64)
    setp = euler_deg(quat_stack(sp, "q_d"))[axis]
    if gt is not None:
        t_g = gt["timestamp"].astype(np.int64)
        tru = euler_deg(quat_stack(gt, "q"))[axis]

    offset = 0.0
    if axis == "yaw":
        est = unwrap_deg(est)
        setp = unwrap_deg(setp)
        if gt is not None:
            tru = unwrap_deg(tru)
        ref = setp[(t_s >= t0) & (t_s < t0 + T_REF_US)]
        offset = float(np.median(ref))
        est = est - offset
        setp = setp - offset
        if gt is not None:
            tru = tru - offset

    i_on = first((t_s >= t0) & (setp >= 0.5 * amp))
    if i_on is None:
        raise RuntimeError(f"{folder}: setpoint never crosses 50 % of amp")
    t_on_det = int(t_s[i_on])
    t_on_fix = t0 + int(T_STEP_US)
    on_offset_ms = (t_on_det - t_on_fix) / 1000.0
    sp_max = float(setp[(t_s >= t_on_det) & (t_s < t_on_det + T_WIN_US)].max())

    rows = []
    name = os.path.basename(os.path.normpath(folder))
    for label, t_on in (("det", t_on_det), ("fix", t_on_fix)):
        r, o, s = step_metrics(t_a, est, amp, t_on)
        rows.append((name, on_offset_ms, f"est_{label}", r, o, s))
        if gt is not None:
            r, o, s = step_metrics(t_g, tru, amp, t_on)
            rows.append((name, on_offset_ms, f"gt_{label}", r, o, s))
    return rows, sp_max, axis, amp


def main():
    folder, out_md = sys.argv[1], sys.argv[2]
    rows, sp_max, axis, amp = process(folder)
    lines = [
        f"<!-- {os.path.basename(os.path.normpath(folder))}: axis {axis}, amp {amp} deg, "
        f"setpoint max in window {sp_max:.2f} deg -->",
        "| flight | t_on - (start+2.0 s) [ms] | variant | rise 10-90 [ms] | overshoot [%] | settle 2 % [ms] |",
        "|---|---|---|---|---|---|",
    ]
    for name, off, var, r, o, s in rows:
        lines.append(f"| {name} | {off:+.1f} | {var} | {r:.1f} | {o:.2f} | {s:.1f} |")
    text = "\n".join(lines) + "\n"
    with open(out_md, "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
