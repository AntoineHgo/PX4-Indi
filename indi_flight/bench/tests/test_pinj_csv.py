#!/usr/bin/env python3
"""Synthetic self-test for indi_flight/bench/pinj_csv.py estimate() (outer-loop break window -> margins). No ulog, no sim.

  python3 -I indi_flight/bench/tests/test_pinj_csv.py      (numpy only; exit 0 = pass, 1 = failure)

Known loop: L(s) = K exp(-s tau) / (s (s/P + 1)), sampled at 100 Hz (ZOH plant, M samples of transport delay, so the
sampled loop is the continuous L with tau_eff = M Ts + Ts/2). d is the multisine of margins_est.multisine for the module
defaults used on the bench (Tp 10 s, 0.2 to 8 Hz, 3 periods, 0.05 m/s^2 per component). Convention of the module and of
pinj_csv.py: c = a_c_pre_inject = -(plant output) is what returns to the summation, u = a_c = c + d is the plant input,
so the window columns are t, d, x = u, y = c and L = -G_yd / G_xd.

Tolerances: PM 2 deg, crossover 3 percent (spline over 10 bins per decade plus the Ts/2 of the ZOH; measured values are
printed). BREAK CHECK (run once, then restored): swapping the x and y columns (u and c exchanged) makes the PM
check fail.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import margins_est as me  # noqa: E402
import pinj_csv  # noqa: E402

FS, TP, FMIN, FMAX, NP, AMP = 100.0, 10.0, 0.2, 8.0, 3, 0.05
K, P, M = 5.0, 10.0, 8  # gain [1/s], lag corner [rad/s], transport delay [samples]
TOL_PM_DEG, TOL_FC_REL = 2.0, 0.03


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def simulate(d, noise=0.0, seed=1):
    """Closed loop with the module's signs: u = c + d, c = -y, y = plant(u delayed M samples). Returns x = u, y = c."""
    h = 1.0 / FS
    e = np.exp(-P * h)
    # exact ZOH of states (y, dy/dt) of y'' = P (K u - y')
    ad = np.array([[1.0, (1.0 - e) / P], [0.0, e]])
    bd = np.array([K * (h - (1.0 - e) / P), K * (1.0 - e)])
    n = len(d)
    rng = np.random.default_rng(seed)
    x_state = np.zeros(2)
    u = np.zeros(n)
    c = np.zeros(n)
    for i in range(n):
        c[i] = -x_state[0] + noise * rng.standard_normal()
        u[i] = c[i] + d[i]
        x_state = ad @ x_state + bd * (u[i - M] if i >= M else 0.0)
    return u, c


def truth():
    """PM [deg] and crossover [rad/s] of the continuous L with tau_eff, by bisection on |L| = 1."""
    tau = M / FS + 0.5 / FS

    def mag(w):
        return K / (w * np.sqrt(1.0 + (w / P) ** 2))

    a, b = 0.1, 100.0
    for _ in range(200):
        m = 0.5 * (a + b)
        a, b = (m, b) if mag(m) > 1.0 else (a, m)
    wc = 0.5 * (a + b)
    return 90.0 - np.degrees(np.arctan(wc / P)) - np.degrees(wc * tau), wc


def window_array(noise=0.0):
    _, d = me.multisine(me.log_bins(FMIN, FMAX, TP) / TP, AMP, FS, TP, NP)
    u, c = simulate(d, noise)
    t = 1000.0 + np.arange(len(d)) / FS  # same layout as pinj_csv.window(): t, d, x = u, y = c
    return np.column_stack([t, d, u, c])


def run(a, label):
    pm0, wc0 = truth()
    res, mg, fs = pinj_csv.estimate(a, TP, FMIN, FMAX)
    cr = mg["crossings"]
    print("%s: truth PM %.2f deg wc %.3f rad/s | est PM %.2f deg wc %.3f rad/s fs %.1f" %
          (label, pm0, wc0, mg["pm_deg"], cr[0]["w_c"] if cr else float("nan"), fs))
    check(abs(fs - FS) < 1e-6, "fs from median dt")
    check(len(cr) == 1, "expected exactly one |L| = 1 crossing, got %d" % len(cr))
    check(abs(mg["pm_deg"] - pm0) <= TOL_PM_DEG, "%s: PM off (est %.2f, truth %.2f)" % (label, mg["pm_deg"], pm0))
    check(abs(cr[0]["w_c"] / wc0 - 1.0) <= TOL_FC_REL, "%s: crossover off" % label)
    check(bool(res["accepted"].all()), "%s: bins rejected" % label)


def test_clean():
    run(window_array(), "clean")


def test_noise():
    run(window_array(noise=0.002), "noise")


def test_extraction_is_the_window_only():
    a = window_array()
    check(a.shape[1] == 4 and np.all(np.diff(a[:, 0]) > 0), "layout t,d,x,y")
    check(np.allclose(a[:, 2] - a[:, 3], a[:, 1]), "u = c + d")


def main():
    fails = 0
    for name, f in sorted(globals().items()):
        if name.startswith("test_") and callable(f):
            try:
                f()
                print("PASS", name)
            except AssertionError as ex:
                fails += 1
                print("FAIL", name, ex)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
