"""Synthetic self-test of bench/ratesp_csv.py (arrays only, no ulog).

Known loop L0(s) = K e^{-s tau} / s  =>  w_c = K, PM = 90 deg - K*tau (rad) in degrees, f_c = K / 2 pi.
Signals are built in the frequency domain per excited bin (exactly periodic): x = d / (1 + L0), y = -L0 x,
so x = y + d.  Swapped x/y gives L' = 1/L0 (|L'| < 1 below w_c, no crossing): must be detected as wrong.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import margins_est as me  # noqa: E402
import ratesp_csv as rc  # noqa: E402

TP, FS = 10.0, 400.0
K, TAU = 2 * np.pi * 2.0, 0.02          # f_c = 2 Hz, PM = 90 - 2pi*2*0.02 rad = 90 - 14.4 deg = 75.6 deg
PM_REF, FC_REF = 90.0 - np.degrees(K * TAU), K / (2 * np.pi)
TOL_PM, TOL_FC = 1.0, 0.05              # deg, relative


def synth(npd=5, dly=3.0, swap=False, noise=0.0):
    ks = np.asarray(me.log_bins(0.2, 20.0, TP), int)   # the estimator's own excited grid
    t = np.arange(int(npd * TP * FS)) / FS
    ph = -np.pi * np.arange(len(ks)) ** 2 / len(ks)           # Schroeder phases
    d = np.zeros_like(t); x = np.zeros_like(t)
    for k, p in zip(ks, ph):
        w = 2 * np.pi * k / TP
        L0 = K * np.exp(-1j * w * TAU) / (1j * w)
        d += 0.05 * np.cos(w * t + p)
        x += 0.05 * np.real(np.exp(1j * (w * t + p)) / (1 + L0))
    y = x - d
    rng = np.random.default_rng(1)
    x = x + noise * rng.standard_normal(len(t)); y = y + noise * rng.standard_normal(len(t))
    if swap:
        x, y = y, x
    return np.column_stack([t + dly, d, x, y])


def run(a):
    res, mg, fs = rc.estimate(a, TP, 0.2, 20.0)
    return mg, rc.validity(a, TP)


def test_known_loop():
    a = synth()
    mg, v = run(a)
    assert abs(mg["pm_deg"] - PM_REF) < TOL_PM, (mg["pm_deg"], PM_REF)
    assert abs(mg["crossings"][0]["f_c"] / FC_REF - 1) < TOL_FC
    assert v["max_abs_x_minus_y_minus_d"] < 1e-9 and v["n_periods_complete"] >= 4


def test_with_noise():
    mg, _ = run(synth(noise=1e-3))
    assert abs(mg["pm_deg"] - PM_REF) < 3.0


def test_swapped_xy_detected():
    a = synth(swap=True)
    mg, v = run(a)
    wrong = not (abs(mg["pm_deg"] - PM_REF) < TOL_PM) or not mg["crossings"]
    assert wrong, "swapped x/y gave the correct margin"
    assert v["max_abs_x_minus_y_minus_d"] > 1e-3      # the validity check also flags it


def test_window_gate():
    t = np.arange(100) * 0.01
    d = np.zeros(100); d[20:70] = 1.0
    w = rc.window(t, d, d.copy(), np.zeros(100))
    assert w.shape[0] == 50 and w[0, 0] == t[20]


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
