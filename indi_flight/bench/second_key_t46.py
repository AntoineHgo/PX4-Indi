#!/usr/bin/env python3
"""Independent second-key check of the t46 metrics on a ULog flight.

Usage: second_key_t46.py <flight.ulg> <out.json>

Two windows are reported, both with 5.0 s margins:
  spec:       [first OFFBOARD (nav_state 14) sample + 5 s, last OFFBOARD sample - 5 s]
  contiguous: same, but using only the first contiguous run of nav_state 14
              (the run ends where nav_state first leaves 14).
"""
import json
import sys

import numpy as np
from pyulog import ULog

OFFBOARD = 14
MARGIN_US = 5_000_000
TOPICS = [
    "vehicle_status",
    "actuator_motors",
    "vehicle_angular_velocity",
    "vehicle_rates_setpoint",
    "sim_ground_truth",
    "sensor_gyro",
]


def load(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    raise KeyError(name)


def fd_rms(t_us, cols, lo, hi):
    """RMS of finite-difference derivative per column (units/s).

    Pairs with dt > 0 only; a pair belongs to its later sample, kept when that
    sample lies in [lo, hi]. Returns (per-column RMS, pairs kept).
    """
    dt = np.diff(t_us)
    keep = (dt > 0) & (t_us[1:] >= lo) & (t_us[1:] <= hi)
    rms = []
    for col in cols:
        d = np.diff(col)[keep] / (dt[keep] * 1e-6)
        rms.append(float(np.sqrt(np.mean(d * d))))
    return rms, int(keep.sum())


def max_gap_ms(t_us):
    return float(np.max(np.diff(t_us)) / 1e3) if t_us.size > 1 else float("nan")


def window_metrics(ulog, lo, hi, motor, av, rs, gyro, sgt):
    out = {"window_us": [int(lo), int(hi)], "window_duration_s": (hi - lo) * 1e-6}

    # actuator_motors: timestamp_sample axis (primary) and timestamp axis (check)
    for axis in ("timestamp_sample", "timestamp"):
        t = np.asarray(motor[axis]).astype(np.int64)
        o = np.argsort(t, kind="stable")
        t = t[o]
        cols = [np.asarray(motor[f"control[{i}]"], dtype=float)[o] for i in range(4)]
        rms, n = fd_rms(t, cols, lo, hi)
        out[f"motor_rate_rms_per_s_{axis}"] = {
            "per_motor": rms,
            "mean": float(np.mean(rms)),
            "pairs_in_window": n,
            "zero_dt_pairs_all": int(np.sum(np.diff(t) == 0)),
        }

    # rate tracking, vehicle_angular_velocity on timestamp_sample, ZOH setpoint on its timestamp
    ta = np.asarray(av["timestamp_sample"]).astype(np.int64)
    oa = np.argsort(ta, kind="stable")
    ta = ta[oa]
    xyz = np.stack([np.asarray(av[f"xyz[{i}]"], dtype=float)[oa] for i in range(3)], axis=1)
    tr = np.asarray(rs["timestamp"]).astype(np.int64)
    orr = np.argsort(tr, kind="stable")
    tr = tr[orr]
    sp = np.stack([np.asarray(rs[k], dtype=float)[orr] for k in ("roll", "pitch", "yaw")], axis=1)
    w = (ta >= lo) & (ta <= hi)
    idx = np.searchsorted(tr, ta[w], side="right") - 1
    v = idx >= 0
    err = xyz[w][v] - sp[idx[v]]
    out["rate_tracking_rms_rad_s"] = {
        "roll": float(np.sqrt(np.mean(err[:, 0] ** 2))),
        "pitch": float(np.sqrt(np.mean(err[:, 1] ** 2))),
        "yaw": float(np.sqrt(np.mean(err[:, 2] ** 2))),
        "samples_used": int(v.sum()),
        "samples_dropped_no_setpoint": int((~v).sum()),
    }

    # sample counts and max gaps inside the window (timestamp_sample axis)
    for name, d in (("sim_ground_truth", sgt), ("sensor_gyro", gyro)):
        t = np.sort(np.asarray(d["timestamp_sample"]).astype(np.int64))
        tw = t[(t >= lo) & (t <= hi)]
        out[f"{name}_window"] = {"count": int(tw.size), "max_gap_ms": max_gap_ms(tw)}
    return out


def main(ulog_path, out_path):
    ulog = ULog(ulog_path, message_name_filter_list=TOPICS)
    vs = load(ulog, "vehicle_status")
    vs_t = np.asarray(vs["timestamp"]).astype(np.int64)
    vs_ns = np.asarray(vs["nav_state"])
    order = np.argsort(vs_t, kind="stable")
    vs_t, vs_ns = vs_t[order], vs_ns[order]

    off = np.flatnonzero(vs_ns == OFFBOARD)
    if off.size == 0:
        raise SystemExit("no OFFBOARD samples")
    first_i = off[0]
    run_end_i = first_i
    while run_end_i + 1 < vs_t.size and vs_ns[run_end_i + 1] == OFFBOARD:
        run_end_i += 1

    spec_lo = int(vs_t[off[0]]) + MARGIN_US
    spec_hi = int(vs_t[off[-1]]) - MARGIN_US
    cont_lo = int(vs_t[first_i]) + MARGIN_US
    cont_hi = int(vs_t[run_end_i]) - MARGIN_US

    motor = load(ulog, "actuator_motors")
    av = load(ulog, "vehicle_angular_velocity")
    rs = load(ulog, "vehicle_rates_setpoint")
    gyro = load(ulog, "sensor_gyro")
    sgt = load(ulog, "sim_ground_truth")

    result = {
        "log": ulog_path,
        "offboard_first_us": int(vs_t[off[0]]),
        "offboard_last_us": int(vs_t[off[-1]]),
        "first_run_offboard_end_us": int(vs_t[run_end_i]),
        "spec": window_metrics(ulog, spec_lo, spec_hi, motor, av, rs, gyro, sgt),
        "contiguous_run": window_metrics(ulog, cont_lo, cont_hi, motor, av, rs, gyro, sgt),
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
