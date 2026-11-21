#!/usr/bin/env python3
"""Self-test of the S186 item-1 horizontal excursion (truth vs time-matched trajectory_setpoint x,y) in g3_checks.py.
  python3 indi_flight/bench/tests/test_g3_excursion_s186.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_checks as G  # noqa: E402

FS, T = 200.0, 90.0
T0, T1 = 40.0, 50.0
R = 20.0  # trajectory radius, well above the 5 m threshold


def run(off=1.0, depart=0.0, sp_nan=False, sp_rate=10.0, no_sp=False):
    t = np.arange(0, T, 1 / FS)
    n = len(t)
    h = np.minimum(t / 5.0, 1.0) * 5.0
    cx, cy = R * np.sin(0.2 * t), R * np.sin(0.4 * t)  # lemniscate-like moving setpoint
    pos = np.stack([cx + off, cy, -h], axis=1)
    pos[:, 0] += depart * ((t > 60) & (t < 61))
    q = np.tile([1.0, 0, 0, 0], (n, 1))
    w = np.zeros((n, 3))
    cmd = np.full((n, 4), 0.5)
    ts = np.arange(0, T, 1 / sp_rate)
    xy = np.stack([R * np.sin(0.2 * ts), R * np.sin(0.4 * ts)], axis=1)
    if sp_nan:
        xy[(ts > 20) & (ts < 30)] = np.nan
    ref = np.array([0.0, 0.0, -5.0])
    return G.evaluate(t, pos, q, w, t, cmd, ref, T0, T1, sp=None if no_sp else (ts, xy))["item1_loc"]


def main():
    bad = 0

    def chk(name, ok):
        nonlocal bad
        print(("PASS " if ok else "FAIL ") + name)
        bad += not ok
    a = run()
    chk("follow 1 m offset -> 1.0 m, pass (old code: ~trajectory radius %g m)" % R, abs(a["horizontal_excursion_m"] - 1.0) < 0.01 and a["pass"])
    b = run(depart=6.0)
    chk("6 m departure -> ~7 m, item 1 fails", b["horizontal_excursion_m"] > 6.5 and not b["pass"])
    c = run(sp_nan=True)
    chk("NaN setpoint samples excluded, frac reported", abs(c["horizontal_excursion_m"] - 1.0) < 0.01 and 0.05 < c["excursion_sp_nan_frac"] < 0.2)
    chk("no setpoint -> None", run(no_sp=True)["horizontal_excursion_m"] is None)
    return bad


if __name__ == "__main__":
    sys.exit(main())
