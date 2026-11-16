#!/usr/bin/env python3
"""Compare sim_ground_truth with the stock groundtruth topics on matched timestamp_sample (A-15, S21).
Usage: python3 a15_truth_equal.py <flight.ulg>"""
import sys
import numpy as np
from pyulog import ULog

u = ULog(sys.argv[1])
g = lambda n: next(d for d in u.data_list if d.name == n).data
s, a, w, p = (g(n) for n in ("sim_ground_truth", "vehicle_attitude_groundtruth",
                              "vehicle_angular_velocity_groundtruth", "vehicle_local_position_groundtruth"))


def match(ref, other):
    r = np.asarray(ref["timestamp_sample"]); o = np.asarray(other["timestamp_sample"])
    common, ir, io = np.intersect1d(r, o, return_indices=True)
    return ir, io


def mx(x, y):
    return float(np.max(np.abs(np.asarray(x) - np.asarray(y)))) if len(x) else float("nan")


ir, io = match(s, a)
print(f"attitude: n_sim={len(s['timestamp'])} n_old={len(a['timestamp'])} matched={len(ir)}")
for i in range(4):
    print(f"  q[{i}] max|diff| = {mx(s[f'q[{i}]'][ir], a[f'q[{i}]'][io]):.3g}")
ir, io = match(s, w)
print(f"angvel: n_old={len(w['timestamp'])} matched={len(ir)}")
for i in range(3):
    print(f"  w[{i}] max|diff| = {mx(s[f'angular_velocity[{i}]'][ir], w[f'xyz[{i}]'][io]):.3g}")
ir, io = match(s, p)
print(f"local_position: n_old={len(p['timestamp'])} matched={len(ir)}")
for k in ("x", "y", "z", "vx", "vy", "vz"):
    print(f"  {k} max|diff| = {mx(s[k][ir], p[k][io]):.3g}")
print("timestamp==timestamp_sample in sim topic:", bool(np.all(np.asarray(s["timestamp"]) == np.asarray(s["timestamp_sample"]))))
