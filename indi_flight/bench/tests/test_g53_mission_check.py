#!/usr/bin/env python3
"""Self-test of bench/g53_mission_check.py: python3 indi_flight/bench/tests/test_g53_mission_check.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g53_mission_check as C  # noqa: E402

wps = [[20.0, 0.0], [20.0, 20.0]]
t = np.arange(0, 20, 0.01)
x = np.minimum(20.0 * t / 4.0, 20.0)  # 5 m/s to wp1
y = np.clip(5.0 * (t - 4.0), 0, 20.0)  # then 5 m/s to wp2
vx, vy = np.gradient(x, t), np.gradient(y, t)


def run(x_, y_, vx_, vy_):
    return C.check(t, x_, y_, vx_, vy_, wps, 0, 20, 5.0)


r = run(x, y, vx, vy)
assert r["pass"], r
assert max(r["wp_min_dist_m"]) < 0.1
# corner cutting: wp2 missed by 3 m -> must fail on waypoint
r = run(x, np.minimum(y, 17.0), vx, np.gradient(np.minimum(y, 17.0), t))
assert not r["pass"] and r["wp_ok"] == [True, False], r
# too fast: 7 m/s cruise -> fail on speed only
r = run(x, y, vx * 1.4, vy * 1.4)
assert not r["speed_ok"] and all(r["wp_ok"]) and not r["pass"], r
print("OK")
