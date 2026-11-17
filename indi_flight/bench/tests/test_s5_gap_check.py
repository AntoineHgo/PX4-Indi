#!/usr/bin/env python3
"""Self-test of s5_gap_check.analyze on synthetic data with a known answer (run: python3 test_s5_gap_check.py)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import s5_gap_check as S  # noqa: E402


def test_known_sag():
    t = np.arange(0, 60e6, 10e3)                      # 100 Hz, 60 s
    ev = 20e6
    ts = t * 1e-6
    # z error: 0 before ev, then 0.37 m below hold (NED z positive down) reached by an exponential, small ripple
    z = -10.0 + np.where(ts < 20, 0.0, 0.37 * (1 - np.exp(-(ts - 20) / 2.0))) + 0.01 * np.sin(2 * np.pi * ts)
    thr = np.where(ts < 20, 0.5, 0.5 / 0.85)
    p = {"MPC_Z_P": 1.0, "MPC_Z_VEL_P_ACC": 4.0, "MPC_USE_HTE": 0}
    r = S.analyze(t, z, -10.0, ev, t, thr, p, scale=0.85)
    exp = (1 - 0.85) * S.G / 4.0
    assert abs(r["prediction_m"] - exp) < 1e-9 and abs(exp - 0.3677) < 1e-3
    assert abs(r["z_err_ev10_20"]["mean"] - 0.37) < 0.01, r["z_err_ev10_20"]
    assert abs(r["z_err_last10"]["mean"] - 0.37) < 0.01
    assert 0.35 < r["max_abs_z_dev_after"] < 0.39
    assert abs(r["z_err_before"]["mean"]) < 0.01
    assert abs(r["thrust_before"] - 0.5) < 1e-9 and abs(r["thrust_after_last10"] - 0.5 / 0.85) < 1e-9
    assert 0.0 < r["z_err_last10"]["std"] < 0.02


if __name__ == "__main__":
    test_known_sag()
    print("ok s5_gap_check synthetic")
