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


# ---------------------------------------------------------------------------------------------------------------
# S124 K124 fixes: gates, robust first-stage F, same filter chain, deliberate-mismatch self-tests (must FAIL)

def _ar(rng, n, a):
    e = rng.standard_normal(n)
    out = np.zeros(n)
    for i in range(1, n):
        out[i] = a * out[i - 1] + e[i]
    return out


def test_robust_f_known_answer():
    """(1) white errors, real first stage: F_eff ~ classical F. (2) x independent of z, both persistent AR(0.99):
    the true F is ~1; the classical F is inflated (spurious), the HAC effective F is not."""
    lags = [0, 2, 4, 6]
    n = 12000
    rng = np.random.default_rng(1)
    z = rng.standard_normal(n)
    x = 0.2 * z + rng.standard_normal(n)
    fr, _ = ident_fit.robust_first_stage_f(x, z, lags, None, 20)
    Z = np.column_stack([np.r_[np.full(l, np.nan), z[:n - l]] for l in lags])
    k = np.isfinite(Z).all(1)
    Zf = np.column_stack([np.ones(k.sum()), Z[k]])
    b = np.linalg.lstsq(Zf, x[k], rcond=None)[0]
    rss1 = ((x[k] - Zf @ b) ** 2).sum()
    rss0 = ((x[k] - x[k].mean()) ** 2).sum()
    fc = ((rss0 - rss1) / 4) / (rss1 / (k.sum() - 5))
    assert 0.7 < fr / fc < 1.3, (fr, fc)
    frs, fcs = [], []
    for s in range(8):
        r2 = np.random.default_rng(100 + s)
        z2, x2 = _ar(r2, n, 0.99), _ar(r2, n, 0.99)
        frs.append(ident_fit.robust_first_stage_f(x2, z2, lags, None, 400)[0])
        Z = np.column_stack([np.r_[np.full(l, np.nan), z2[:n - l]] for l in lags])
        k = np.isfinite(Z).all(1)
        Zf = np.column_stack([np.ones(k.sum()), Z[k]])
        b = np.linalg.lstsq(Zf, x2[k], rcond=None)[0]
        rss1 = ((x2[k] - Zf @ b) ** 2).sum()
        rss0 = ((x2[k] - x2[k].mean()) ** 2).sum()
        fcs.append(((rss0 - rss1) / 4) / (rss1 / (k.sum() - 5)))
    assert np.median(fcs) > 10 > np.median(frs), (np.median(fcs), np.median(frs))


def test_clean_run_passes_gate_and_reports_criteria():
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=3)
    r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0)
    assert r["verdict"]["passed"], r["verdict"]["criteria"]
    assert len(r["verdict"]["criteria"]) == 6 and not r["at_boundary"] and r["shift_samples"] == 2


def test_weak_instrument_fails_gate():
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=3)
    z = np.random.default_rng(9).standard_normal(len(t)) * 0.003  # unrelated to u: F ~ 1
    r = ident_fit.fit_axis(t, w, t, um, t, z, 4.0, 56.0)
    assert r["f"] < 10 and not r["verdict"]["passed"]


def test_mismatch_shift_beyond_scan_bound_fails():
    """(a) regressor delayed by 5 samples beyond the scan bound (12 + 5 = 17 total) must FAIL, not be absorbed."""
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=3, delay=ident_fit.SHIFT_MAX + 5)
    r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0)
    assert r["at_boundary"] and not r["verdict"]["passed"]


def test_mismatch_different_fir_on_regressor_fails():
    """(b) 5 taps on the regressor vs 15 on regressand and instrument: G1 collapses (-46 %), the gate must FAIL."""
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=3)
    r = ident_fit.fit_axis(t, w, t, um, t, d, 4.0, 56.0, ntaps_x=5)
    assert abs(r["g1"] - 1700.0) / 1700.0 > 0.2
    assert not r["verdict"]["passed"]


def test_regressand_regressor_same_gain_at_60hz():
    """The regressand carries the central-difference gain sinc(w dt); the regressor chain must carry the same."""
    f = 60.0
    th = 2 * np.pi * f / FS
    c = ident_fit.CENTRAL_DIFF_MATCH
    gain_c = c[1] + 2.0 * c[0] * np.cos(th)
    assert abs(gain_c - np.sin(th) / th) < 1e-3


def test_held_regressor_refused_and_short_hold_decimated():
    t, w, um, d = _closed_loop(1700.0, 1700.0, seed=3)
    held8 = np.repeat(um[::8], 8)[: len(um)]
    try:
        ident_fit.fit_axis(t, w, t, held8, t, d, 4.0, 56.0)
        raise AssertionError("held regressor not refused")
    except ident_fit.HeldRegressorError:
        pass
    held2 = np.repeat(um[::2], 2)[: len(um)]
    r = ident_fit.fit_axis(t, w, t, held2, t, d, 4.0, 56.0)
    assert r["decim"] == 2 and abs(r["g1"] - 1700.0) / 1700.0 < 0.08, (r["decim"], r["g1"])
