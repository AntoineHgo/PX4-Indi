#!/usr/bin/env python3
"""Self-test of bench/g55_check.py pure functions: python3 indi_flight/bench/tests/test_g55_check.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g55_check as C  # noqa: E402

assert C.traj_verdict(0.4, 0.2)["pass"]
assert not C.traj_verdict(0.6, 0.2)["pass"] and not C.traj_verdict(0.4, 0.31)["pass"]

t = np.arange(0, 20, 0.01)  # settle 0..3, step 3..8, hold 8..12 (end 12)
ts, th, te = 3.0, 8.0, 12.0
vx = np.where((t >= ts) & (t < th), 2.0 * (1 - np.exp(-(t - ts) / 0.3)), 0.0) * (t >= ts)
vx = np.where(t >= th, 2.0 * np.exp(-(t - th) / 0.3), vx)
z = np.full_like(t, 5.0)
r = C.vel_step_metrics(t, vx, z, 0.0, ts, th, te)
assert r["pass"], r
# bias of 0.3 m/s in the last 3 s of the step -> RMS gate fails only
v2 = np.where((t >= ts + 2) & (t < th), vx - 0.3, vx)
r = C.vel_step_metrics(t, v2, z, 0.0, ts, th, te)
assert not r["rms_ok"] and r["end_ok"] and r["dz_ok"] and not r["pass"], r
# residual drift 0.15 m/s at end of hold -> end gate fails only
v3 = np.where(t >= th, vx + 0.15, vx)
r = C.vel_step_metrics(t, v3, z, 0.0, ts, th, te)
assert not r["end_ok"] and not r["pass"], r
# height excursion 0.4 m -> dz gate fails
z4 = z + np.where((t > 6) & (t < 7), 0.4, 0.0)
r = C.vel_step_metrics(t, vx, z4, 0.0, ts, th, te)
assert not r["dz_ok"] and not r["pass"], r
print("OK")
