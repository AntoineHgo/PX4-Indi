#!/usr/bin/env python3
"""Self-test of bench/auto_smoke_check.py on synthetic signals (known thrust step, known dip, known descent speed).

  python3 indi_flight/bench/tests/test_auto_smoke_check.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import auto_smoke_check as C  # noqa: E402


def main():
    t = np.arange(0.0, 10.0, 0.004)
    edge = 5.0
    thr = np.where(t < edge, 0.50, 0.58)  # known step 0.08
    tz = np.arange(0.0, 10.0, 0.02)
    h = np.full(tz.size, 5.0)
    d = (tz >= edge) & (tz < edge + 0.5)
    h[d] = 5.0 - 0.3 * np.sin(np.pi * (tz[d] - edge) / 0.5)  # known dip 0.3 m
    step, dip = C.handover_metrics(t, thr, tz, -h, edge)
    assert abs(step - 0.08) < 1e-6, step
    assert abs(dip - 0.3) < 0.01, dip
    # no dip when climbing
    _, dip0 = C.handover_metrics(t, thr, tz, -(5.0 + 0.1 * (tz - edge)), edge)
    assert dip0 == 0.0, dip0
    # descent at 0.7 m/s from 6 m
    tl = np.arange(0.0, 8.0, 0.02)
    hl = np.clip(6.0 - 0.7 * tl, 0, None)
    vz = np.where(hl > 0, 0.7, 0.0)
    v, n = C.mean_descent_vz(tl, -hl, vz)
    assert abs(v - 0.7) < 1e-9 and n > 100, (v, n)
    # transitions and tracking
    assert C.transitions(np.arange(6.0), np.array([1, 1, 2, 2, 2, 1])) == [(2.0, 1, 2), (5.0, 2, 1)]
    ts = np.arange(0.0, 4.0, 0.1)
    gt = np.zeros((ts.size, 3)); gt[:, 0] = 0.3; gt[:, 2] = -0.1
    sp = np.zeros((ts.size, 3)); sp[5:8] = np.nan
    r = C.track_err(ts, gt, ts, sp, 0.0, 4.0)
    assert abs(r["xy_rms"] - 0.3) < 1e-9 and abs(r["z_max"] - 0.1) < 1e-9 and r["n"] == ts.size - 3, r
    print("test_auto_smoke_check OK")


if __name__ == "__main__":
    main()
