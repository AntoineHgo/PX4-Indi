"""Synthetic closed-loop self-test of the ident_fit.py pipeline (not the ulog loading)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import ident_fit  # noqa: E402

FS = 800.0
DIST = 6.0  # disturbance drive, rad/s^2 per sample; sets the injection SNR (F ~ 1e3)


def _closed_loop(g1_true, g1_set, seed, T=60.0, delay=2):
    """alpha = g1_true*u_actual + coloured disturbance; u = rate feedback (g1_set based INDI-like) + injection.
    Measured u arrives `delay` samples after the actual one (telemetry latency)."""
    rng = np.random.default_rng(seed)
    n = int(T * FS)
    dt = 1 / FS
    t = np.arange(n) * dt
    # multisine injection 1..60 Hz, random phases, normalised torque units
    f = np.linspace(1, 60, 18)
    d = sum(0.003 * np.sin(2 * np.pi * fi * t + rng.uniform(0, 2 * np.pi)) for fi in f)
    dist = np.zeros(n)
    e = rng.standard_normal(n) * DIST
    for i in range(1, n):  # coloured disturbance, ~15 Hz corner, rad/s^2
        dist[i] = 0.9 * dist[i - 1] + e[i]
    w = np.zeros(n)
    u = np.zeros(n)
    kr = 25.0
    for i in range(1, n):
        u[i - 1] = -kr * w[i - 1] / g1_set + d[i - 1]
        w[i] = w[i - 1] + (g1_true * u[i - 1] + dist[i - 1]) * dt
    u[-1] = u[-2]
    um = np.roll(u, delay)
    return t, w, um, d


def test_recovers_g1_closed_loop():
    for g1_set in (0.5 * 1700.0, 1700.0, 2.0 * 1700.0):
        t, w, um, d = _closed_loop(1700.0, g1_set, seed=3)
        r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0)
        assert abs(r["g1"] - 1700.0) / 1700.0 < 0.05, (g1_set, r["g1"])
        assert r["f"] > 10
        assert r["ci95"] / r["g1"] < 0.10
        assert r["excl_frac"] == 0.0


def test_ols_is_biased_in_closed_loop_and_iv_is_not():
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=5)
    r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0)
    assert abs(r["g1"] - 1700.0) < abs(r["ols"] - 1700.0)


def test_saturated_samples_excluded():
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=7)
    sat = (t > 20.0) & (t < 25.0)
    r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0, sat=sat, t_sat=t)
    assert 0.05 < r["excl_frac"] < 0.15
    assert abs(r["g1"] - 1700.0) / 1700.0 < 0.05
