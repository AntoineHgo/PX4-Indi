#!/usr/bin/env python3
"""A-33 tilt split (S73): standing attitude error in the last 10 s of a s5_loss08 / s5_gap085 run.

Usage: a33_tilt_split.py RUN_DIR [RUN_DIR ...]   (RUN_DIR holds flight.ulg and gap_check.json from s5_gap_check.py)

Per run, over [end_s - 10, end_s] (end_s from gap_check.json, log timestamp base): mean tilt of the attitude
setpoint and of the estimated attitude (angle of body z to NED down, per sample, own timestamps, no resampling),
mean per-sample angle between setpoint and actual body z (setpoint held to the nearest earlier attitude sample),
mean actuator_motors control[0..3], mean rate setpoint and rate (roll, pitch). Prints one row per run.
"""
import json
import os
import sys

import numpy as np
from pyulog import ULog


def body_z(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], axis=1)


def tilt_deg(bz):
    return np.degrees(np.arccos(np.clip(bz[:, 2] / np.linalg.norm(bz, axis=1), -1, 1)))


def topic(ulog, name):
    d = [x for x in ulog.data_list if x.name == name and x.multi_id == 0]
    return d[0].data if d else None


def window(d, t0, t1):
    t = d["timestamp"] * 1e-6
    return (t >= t0) & (t <= t1)


def main(runs):
    for run in runs:
        gc = json.load(open(os.path.join(run, "gap_check.json")))
        t1 = gc["end_s"]
        t0 = t1 - 10.0
        u = ULog(os.path.join(run, "flight.ulg"))
        sp, att = topic(u, "vehicle_attitude_setpoint"), topic(u, "vehicle_attitude")
        ms, ma = window(sp, t0, t1), window(att, t0, t1)
        qd = np.stack([sp[f"q_d[{i}]"][ms] for i in range(4)], axis=1)
        q = np.stack([att[f"q[{i}]"][ma] for i in range(4)], axis=1)
        bzd, bz = body_z(qd), body_z(q)
        # setpoint held to each attitude sample (zero-order hold of the setpoint, both topics >= 100 Hz)
        idx = np.searchsorted(sp["timestamp"][ms], att["timestamp"][ma], side="right") - 1
        ok = idx >= 0
        cosang = np.sum(bzd[idx[ok]] * bz[ok], axis=1) / (np.linalg.norm(bzd[idx[ok]], axis=1) * np.linalg.norm(bz[ok], axis=1))
        err = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
        am = topic(u, "actuator_motors")
        mm = window(am, t0, t1)
        mot = [float(np.mean(am[f"control[{i}]"][mm])) for i in range(4)]
        rs, av = topic(u, "vehicle_rates_setpoint"), topic(u, "vehicle_angular_velocity")
        mr, mv = window(rs, t0, t1), window(av, t0, t1)
        rsp = [float(np.mean(rs[k][mr])) for k in ("roll", "pitch")]
        rat = [float(np.mean(av[f"xyz[{i}]"][mv])) for i in range(2)]
        print(f"{run}: tilt_sp {np.mean(tilt_deg(bzd)):.2f} deg, tilt {np.mean(tilt_deg(bz)):.2f} deg, "
              f"sp-vs-actual {np.mean(err):.2f} deg, z_err_last10 {gc['z_err_last10']['mean']:+.3f} m, "
              f"motors {' '.join(f'{m:.3f}' for m in mot)}, rate_sp r/p {rsp[0]:+.3f} {rsp[1]:+.3f}, "
              f"rate r/p {rat[0]:+.3f} {rat[1]:+.3f} rad/s")


if __name__ == "__main__":
    main(sys.argv[1:])
