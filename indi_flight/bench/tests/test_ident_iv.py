"""Self-tests for indi_flight/bench/ident_iv.py (known-answer, including closed loop).

  cd indi_flight/bench && python3 -m pytest tests/test_ident_iv.py -q
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import ident_iv as I  # noqa: E402

DT = 0.002
G1 = 80.0  # rad/s^2 per unit normalised torque


def multisine(n, rng, amp=0.05, fmin=1.0, fmax=20.0, nc=15):
    t = np.arange(n) * DT
    f = np.linspace(fmin, fmax, nc)
    ph = rng.uniform(0, 2 * np.pi, nc)
    return amp * sum(np.sin(2 * np.pi * fi * t + p) for fi, p in zip(f, ph)) / np.sqrt(nc / 2)


def ar1(n, rng, tc, std):
    a = np.exp(-DT / tc)
    e = rng.standard_normal(n) * std * np.sqrt(1 - a * a)
    out = np.empty(n)
    out[0] = 0.0
    for i in range(1, n):
        out[i] = a * out[i - 1] + e[i]
    return out


def closed_loop(ghat_ratio, seed, n=60000, tau=0.033, K=15.0, c0=0.0):
    """alpha = G1*u_act + d + c0, u_act first-order of u = K(r - omega)/G1_hat + inj (u fed back into actuator)."""
    rng = np.random.default_rng(seed)
    inj = multisine(n, rng)
    d = ar1(n, rng, 0.2, 15.0)
    ghat = ghat_ratio * G1
    omega, uact = 0.0, 0.0
    a = np.exp(-DT / tau)
    alpha = np.empty(n)
    ua = np.empty(n)
    for i in range(n):
        u = K * (0.0 - omega) / ghat + inj[i]
        uact = a * uact + (1 - a) * u
        al = G1 * uact + d[i] + c0
        alpha[i], ua[i] = al, uact
        omega += al * DT
    return alpha, ua, inj


def test_a_open_loop_white():
    rng = np.random.default_rng(1)
    n = 20000
    z = rng.standard_normal(n) * 0.1
    u = np.empty(n)
    uc = 0.0
    a = np.exp(-DT / 0.033)
    for i in range(n):
        uc = a * uc + (1 - a) * z[i]
        u[i] = uc
    y = G1 * u + 0.5 * rng.standard_normal(n)
    r = I.iv_effectiveness(y, u, z)
    assert abs(r["beta"][0] / G1 - 1) < 0.02
    assert r["f_min"] > 10


@pytest.mark.parametrize("ratio", [0.5, 2.0])
def test_b_closed_loop_ols_biased_iv_recovers(ratio):
    alpha, ua, inj = closed_loop(ratio, seed=7)
    r = I.iv_effectiveness(alpha[2000:], ua[2000:], inj[2000:])
    ols_err = abs(r["ols"]["beta"][0] / G1 - 1)
    iv_err = abs(r["beta"][0] / G1 - 1)
    assert ols_err > 0.10, ols_err
    assert iv_err < 0.05, iv_err
    assert r["f_min"] > 10


def test_c_intercept():
    """Closed loop with intercept. One 120 s record has a seed-to-seed spread of ~11 % on this plant (K120: a single-seed
    5 % check was a seed lottery), so the test checks what the estimator owes: no bias (mean over 12 seeds within 3
    standard errors of the mean) and an honest standard error (HAC z-score spread near 1, classical one over-confident)."""
    errs, zs, ics = [], [], []
    for seed in range(11, 23):
        alpha, ua, inj = closed_loop(0.5, seed=seed, c0=12.0)
        r = I.iv_effectiveness(alpha[2000:], ua[2000:], inj[2000:])
        errs.append(r["beta"][0] / G1 - 1)
        zs.append((r["beta"][0] - G1) / r["se"][0])
        ics.append(r["intercept"])
    assert abs(np.mean(ics) - 12.0) < 1.0, ics
    # unbiased within its own precision (3 standard errors of the mean over seeds); the absolute 10 % accuracy is the
    # flight acceptance test of D-IDENT (i), set by record length and excitation, not by this plant
    assert abs(np.mean(errs)) < 3 * np.std(errs, ddof=1) / np.sqrt(len(errs)), errs
    zsd = float(np.sqrt(np.mean(np.square(zs))))
    assert 0.5 < zsd < 1.6, zsd


def test_d_latency_three_samples():
    rng = np.random.default_rng(3)
    du = rng.standard_normal(5000)
    alpha = G1 * du
    meas = np.concatenate([np.zeros(3), du[:-3]])  # measured signal arrives 3 samples late
    r = I.latency_by_xcorr(alpha, G1 * meas, DT, 10)
    assert r["lag_int"] == 3
    assert abs(r["lag_samples"] - 3) < 0.05
    assert abs(r["lag_s"] - 3 * DT) < 1e-4


def test_d2_fractional_latency_refined():
    rng = np.random.default_rng(4)
    t = np.arange(8000) * DT
    # smooth signal so a 2.4-sample delay is representable
    du = np.convolve(rng.standard_normal(8000), np.ones(9) / 9, mode="same")
    meas = np.interp(t - 2.4 * DT, t, du)
    r = I.latency_by_xcorr(G1 * du, G1 * meas, DT, 10)
    assert abs(r["lag_samples"] - 2.4) < 0.15, r["lag_samples"]


def test_e_yaw_two_regressors():
    rng = np.random.default_rng(5)
    n = 40000
    z = rng.standard_normal(n) * 0.1
    u = np.empty(n)
    uc = 0.0
    a = np.exp(-DT / 0.033)
    for i in range(n):
        uc = a * uc + (1 - a) * z[i]
        u[i] = uc
    du = np.gradient(u, DT)
    G2 = -0.6
    y = G1 * u + G2 * du + 0.3 * rng.standard_normal(n)
    r = I.iv_effectiveness(y, np.column_stack([u, du]), z)
    assert abs(r["beta"][0] / G1 - 1) < 0.03
    assert abs(r["beta"][1] / G2 - 1) < 0.10
    assert r["f_first"].shape == (2,)


def test_f_saturation_mask():
    rng = np.random.default_rng(6)
    n = 30000
    z = rng.standard_normal(n) * 0.1
    u = z.copy()
    sat = np.abs(u) > 0.12  # flagged samples: plant clipped the command, regressor still shows it
    applied = np.where(sat, np.sign(u) * 0.05, u)
    y = G1 * applied + 0.2 * rng.standard_normal(n)
    masked = I.iv_effectiveness(y, u, z, exclude=sat)
    unmasked = I.iv_effectiveness(y, u, z)
    assert abs(masked["beta"][0] / G1 - 1) < 0.02
    assert abs(unmasked["beta"][0] / G1 - 1) > 0.05  # the mask matters in this data
    assert masked["n"] < unmasked["n"]


def test_resample_refuses_decimated():
    t_slow = np.arange(0, 1, 0.02)
    t_grid = np.arange(0, 1, 0.002)
    with pytest.raises(ValueError):
        I.resample_to_grid(t_slow, np.sin(t_slow), t_grid)
    out = I.resample_to_grid(t_grid, np.sin(t_grid), t_slow)
    assert np.allclose(out, np.sin(t_slow), atol=1e-6)


def test_prepare_regression_same_filter():
    t = np.arange(0, 20, DT)
    rng = np.random.default_rng(8)
    z = rng.standard_normal(t.size) * 0.1
    u = np.zeros_like(t)
    a = np.exp(-DT / 0.033)
    for i in range(1, t.size):
        u[i] = a * u[i - 1] + (1 - a) * z[i]
    omega = np.cumsum(G1 * u) * DT
    sat = np.zeros(t.size, bool)
    sat[3000:3010] = True
    y, x, zz, ex = I.prepare_regression(t, omega, t, u, t, I.smooth_taps(5), saturated=sat, t_sat=t, z=z, t_z=t)
    assert ex[3005] and not ex[1000]
    r = I.iv_effectiveness(y, x, zz, exclude=ex)
    assert abs(r["beta"][0] / G1 - 1) < 0.03, r["beta"]
