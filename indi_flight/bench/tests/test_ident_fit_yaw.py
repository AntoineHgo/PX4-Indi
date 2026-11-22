"""Synthetic closed-loop self-test of ident_fit_yaw.fit_yaw (G1, G2 two-regressor IV). Run as plain python.

BREAK=1|2|3 env var deliberately breaks one test (to show it can fail):
 1 test_recovers: fit without the du/dt regressor; 2 test_omitting_du_dt: fit WITH it; 3 test_mismatch: no mismatch."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import ident_fit_yaw as Y  # noqa: E402

FS = 800.0
G1, G2 = 200.0, 27.0
BREAK = int(os.environ.get("BREAK", "0"))


def _loop(g1, g2, seed, g1_set=200.0, T=60.0, delay=2, tau=0.02, dist_sd=1.5):
    """alpha = g1 u + g2 du/dt + coloured disturbance, rate feedback u_cmd = -kr w/g1_set + d (so u depends on the
    disturbance through w: closed loop), actuator = first order lag tau (so u and d are not proportional, u and du/dt
    are separable). Measured u = u delayed by `delay` samples."""
    rng = np.random.default_rng(seed)
    n, dt = int(T * FS), 1 / FS
    t = np.arange(n) * dt
    d = sum(0.03 * np.sin(2 * np.pi * fi * t + rng.uniform(0, 2 * np.pi)) for fi in np.linspace(1, 60, 18))
    dist = np.zeros(n)
    e = rng.standard_normal(n) * dist_sd
    for i in range(1, n):
        dist[i] = 0.9 * dist[i - 1] + e[i]
    w, u = np.zeros(n), np.zeros(n)
    kr, a = 25.0, np.exp(-dt / tau)
    for i in range(1, n):
        cmd = -kr * w[i - 1] / g1_set + d[i - 1]
        u[i] = a * u[i - 1] + (1 - a) * cmd
        w[i] = w[i - 1] + (g1 * u[i] + g2 * (u[i] - u[i - 1]) / dt + dist[i - 1]) * dt
    return t, w, np.roll(u, delay), d


def _fit(seed=3, g2=G2, **kw):
    t, w, um, d = _loop(G1, g2, seed, **{k: kw.pop(k) for k in list(kw) if k == "g1_set"})
    return Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, **kw)


def test_recovers():
    for g1_set in (100.0, 200.0, 400.0):
        t, w, um, d = _loop(G1, G2, 3, g1_set=g1_set)
        r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_g2=(BREAK != 1), with_rate=False)
        assert abs(r["g1"] - G1) < max(0.05 * G1, 1.5 * r["ci1"]), (g1_set, r["g1"], r["ci1"])  # within 5 % or its CI
        assert r["ci1"] / G1 < 0.10
        assert abs(r.get("g2", np.nan) - G2) / G2 < 0.08, (g1_set, r.get("g2"))
        assert r["verdict"]["passed"], r["verdict"]["criteria"]
        assert min(r["f_eff"]) > 10


def test_omitting_du_dt_biases_g1():
    t, w, um, d = _loop(G1, G2, 5)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_g2=(BREAK == 2), with_rate=False)
    assert abs(r["g1"] - G1) / G1 > 0.10, r["g1"]  # S124 model: biased by more than 10 %


def test_no_spinup_gives_g2_zero():
    t, w, um, d = _loop(G1, 0.0, 7)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_rate=False)
    assert abs(r["g2"]) < 0.08 * G2 and abs(r["g1"] - G1) < max(0.05 * G1, 1.5 * r["ci1"]), (r["g1"], r["g2"])


def test_mismatched_filter_is_caught():
    t, w, um, d = _loop(G1, G2, 9)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_rate=False, _x2_taps=(None if BREAK == 3 else 7))
    assert not r["verdict"]["passed"], "regressors filtered with 7 taps vs regressand 15 must fail a gate"
    bad = [c[0] for c in r["verdict"]["criteria"] if not c[2]]
    assert any(b.startswith("filter-chain gain match (regressor FIR") for b in bad), bad  # named gate (MAJOR-4)
    print("mismatch gates failing:", bad, "G1 %.1f G2 %.2f J/df %.1f" % (r["g1"], r["g2"], r["j"] / r["j_df"]))


def _plant4(seed=1, T=60.0, g1=205.3, g2=27.0, dr=1.4, c=2.0, tau=0.0125, K=0.15, amp=0.08, ctrl_hz=400):
    """S202 plant: 3200 Hz internal, alpha = g1 u + g2 du/dt - dr w + c (c = constant alpha offset, so a non-zero
    intercept), u = first-order lag (tau) of cmd, cmd = -K w + d at ctrl_hz (ZOH, closed loop through w) + multisine d
    (0.3-50 Hz). Logged: gyro and d at 800 Hz, u updates at ctrl_hz, held on the 800 Hz stamps (decimation m = 2)."""
    rng = np.random.default_rng(seed)
    H = 3200
    dt = 1.0 / H
    n = int(T * H)
    t = np.arange(n) * dt
    fr = np.linspace(0.3, 50, 120)
    ph = rng.uniform(0, 2 * np.pi, fr.size)
    dsig = amp * sum(np.sin(2 * np.pi * f * t + p) for f, p in zip(fr, ph)) / np.sqrt(fr.size / 2)
    w = um = cmd = 0.0
    W, U = np.zeros(n), np.zeros(n)
    for i in range(n):
        if i % (H // ctrl_hz) == 0:
            cmd = -K * w + dsig[i]
        um0 = um
        um += dt / tau * (cmd - um)
        w += (g1 * um + g2 * (um - um0) / dt - dr * w + c) * dt
        W[i], U[i] = w, um
    ig = np.arange(0, n, H // 800)
    uh = np.repeat(U[:: H // ctrl_hz], 800 // ctrl_hz)[: ig.size]  # u topic: 400 Hz updates held on the 800 Hz stamps
    return t[ig], W[ig] + 1e-4 * rng.standard_normal(ig.size), t[ig], uh, t[ig], dsig[ig]


def test_decimated_rate_intercept_closed_loop():
    """m = 2 (u at 400 Hz), damping Dr, non-zero intercept, closed loop: G1 within 2 % (and Dr, G2 sane)."""
    for seed in (1, 2):
        a = _plant4(seed)
        r = Y.fit_yaw(*a, 8.0, 60.0)
        assert r["decim"] == 2, r["decim"]
        assert abs(r["g1"] - 205.3) / 205.3 < 0.02, (seed, r["g1"], r["ci1"])
        assert abs(r["dr"] - 1.4) < 0.15 and abs(r["g2"] - 27.0) / 27.0 < 0.03, (r["dr"], r["g2"])
        assert r["verdict"]["passed"], [c for c in r["verdict"]["criteria"] if not c[2]]
        # No latency is injected in _plant4 and u is the plant state itself: the known answer is 0 samples. The scan is
        # evaluated on every m-th sample (m = 2), so the physical resolution is 2 samples; the old (-1, 0, 1) tolerance
        # hid an off-by-one. Pinned to 0 here; test_decimated_shift_exact pins injected non-zero latencies exactly.
        assert r["shift_samples"] == 0, r["shift_samples"]
        print("m=2 seed", seed, "G1 %.1f ci %.1f G2 %.2f Dr %.3f J/df %.1f" % (r["g1"], r["ci1"], r["g2"], r["dr"], r["j"] / r["j_df"]))


def test_decimated_shift_exact():
    """S205 (key-2 MINOR-4): m = 2 plant with an injected u latency of 2 and 4 samples (even, so the 400 Hz hold
    structure is preserved): recovered exactly, not within +-1. Odd delays are not tested: they break the 2-sample hold
    and the scan, evaluated on every m-th sample, cannot resolve them (that is the +-1 physical resolution)."""
    a = _plant4(1)
    for dl in (2, 4):
        b = list(a)
        b[3] = np.roll(a[3], dl)
        r = Y.fit_yaw(*b, 8.0, 40.0)
        assert r["decim"] == 2 and r["shift_samples"] == dl and not r["at_boundary"], (dl, r["shift_samples"], r["decim"])


def _noisy_g1_fit(sd, t1):
    a = list(_plant4(1))
    a[1] = a[1] + sd * np.random.default_rng(5).standard_normal(len(a[1]))  # white gyro noise, rad/s
    return Y.fit_yaw(*a, 8.0, t1)


def test_ci_too_wide_gate_fails_by_name():
    """S205 (key-2 MAJOR-1): gyro noise sd 0.2 rad/s on a 22 s window gives CI/G1 ~ 0.34 > 0.15: the gate
    '95% CI/|G1|' must fail by name and be the ONLY failing gate (F, J, df, shift, chain, excl are all fine, so this is
    not a side effect of a weak instrument). Counter-case (sd 0.03, same window and seed): CI/G1 ~ 0.05, passes, and
    every gate passes."""
    r = _noisy_g1_fit(0.2, 30.0)
    bad = [c for c in r["verdict"]["criteria"] if not c[2]]
    assert [c[0].startswith("95% CI/|G1|") for c in bad] == [True], bad
    assert r["ci1"] / abs(r["g1"]) > 0.15 and not r["verdict"]["passed"]
    ok = _noisy_g1_fit(0.03, 30.0)
    rel = ok["ci1"] / abs(ok["g1"])
    assert 0.0 < rel < 0.15, rel
    assert ok["verdict"]["passed"], [c for c in ok["verdict"]["criteria"] if not c[2]]
    assert any(c[0].startswith("95% CI/|G1|") and c[2] for c in ok["verdict"]["criteria"])


def _hac_direct(U, L):
    """Independent Newey-West/Bartlett long-run covariance (test-local, not ident_iv._hac)."""
    S = U.T @ U
    for l in range(1, L + 1):
        G = U[l:].T @ U[:-l]
        S = S + (1 - l / (L + 1)) * (G + G.T)
    return S


def test_gmm_j_is_two_step_not_2sls():
    """S205 (key-2 MINOR-1): heteroskedastic (exp(z0)) and AR(1) errors, valid instruments. The two-step efficient GMM J
    (independent direct computation in the test) differs from the J built on 2SLS residuals by ~50 %. _gmm_j must match
    the two-step value to rounding and must NOT match the 2SLS one."""
    rng = np.random.default_rng(1)
    n, L = 4000, 5
    z = rng.standard_normal((n, 4))
    v = rng.standard_normal(n)
    x = z @ np.array([1.0, 0.5, 0.3, 0.2]) + v
    s = rng.standard_normal(n)
    eps = np.zeros(n)
    for i in range(1, n):
        eps[i] = 0.6 * eps[i - 1] + s[i]
    y = 2.0 * x + 1.0 + (0.5 * v + eps) * np.exp(z[:, 0])
    X, Z = np.column_stack([np.ones(n), x]), np.column_stack([np.ones(n), z])
    Xh = Z @ np.linalg.lstsq(Z, X, rcond=None)[0]
    e1 = y - X @ np.linalg.solve(Xh.T @ X, Xh.T @ y)
    W = np.linalg.inv(_hac_direct(Z * e1[:, None], L))
    A = X.T @ Z
    e2 = y - X @ np.linalg.solve(A @ W @ A.T, A @ W @ (Z.T @ y))
    g2 = (Z * e2[:, None]).sum(0)
    j_two = float(g2 @ np.linalg.solve(_hac_direct(Z * e2[:, None], L), g2))
    g1 = (Z * e1[:, None]).sum(0)
    j_2sls = float(g1 @ np.linalg.solve(_hac_direct(Z * e1[:, None], L), g1))
    assert abs(j_two - j_2sls) / j_two > 0.2, (j_two, j_2sls)  # the DGP really separates the two
    j, df = Y._gmm_j(y, X, Z, e1, L)
    assert df == 3 and abs(j - j_two) / j_two < 1e-6, (j, j_two)
    assert abs(j - j_2sls) / j_two > 0.2, (j, j_2sls)


def test_rate_regressor_on_matched_grid():
    """S205 (key-2 MINOR-3): the rate regressor column of _prepare2 equals F[C w] with w the gyro SAMPLED AT u's update
    stamps and interpolated (matched grid), checked against an independent construction on a decimated (m = 2) log whose
    gyro carries a 300 Hz tone + noise, so a regressor built from the raw 800 Hz gyro differs by far more than the
    tolerance (asserted: the raw-built column is >5 % away, so the test can tell them apart)."""
    rng = np.random.default_rng(2)
    n = 6000
    t = np.arange(n) / FS
    om = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 300 * t + 1.0) + 0.3 * rng.standard_normal(n)
    u = np.repeat(rng.standard_normal(n // 2), 2)  # 400 Hz updates held on 800 Hz stamps
    d = np.sin(2 * np.pi * 3 * t)
    _, X, _, _, _ = Y._prepare2(t, om, t, u, t, d, 1.0, 6.0, None, None, 15, FS)
    taps = Y.iv.smooth_taps(15)
    tg = np.arange(1.0, 6.0, 1 / FS)
    chg = np.concatenate([[True], np.diff(u) != 0])
    tc = t[chg]
    w = np.interp(tg, tc, om[chg])
    w[(tg < tc[0]) | (tg > tc[-1])] = np.nan
    want = Y.iv.apply_taps(Y.iv.apply_taps(w, Y.base.CENTRAL_DIFF_MATCH), taps)
    raw = Y.iv.apply_taps(Y.iv.apply_taps(np.interp(tg, t, om), Y.base.CENTRAL_DIFF_MATCH), taps)
    ok = np.isfinite(want) & np.isfinite(X[:, 2]) & np.isfinite(raw)
    scale = np.std(want[ok])
    assert ok.sum() > 3000
    assert np.max(np.abs(X[ok, 2] - want[ok])) < 1e-9 * scale, np.max(np.abs(X[ok, 2] - want[ok])) / scale
    assert np.sqrt(np.mean((raw[ok] - want[ok]) ** 2)) > 0.05 * scale  # the test discriminates raw from matched


def test_omitting_rate_term_is_biased():
    """Contrast: without the rate regressor the same data give a G1 that is off by more than 10 % (the A-43 bias)."""
    r = Y.fit_yaw(*_plant4(1), 8.0, 60.0, with_rate=False)
    assert abs(r["g1"] - 205.3) / 205.3 > 0.10, r["g1"]


def test_shift_value_and_boundary_gate():
    """The injected 2-sample latency is recovered (shift_samples == delay) and a delay outside the scan range trips the
    boundary gate (and only that family of gates is asserted by name)."""
    t, w, um, d = _loop(G1, G2, 3)  # delay=2 samples, u at 800 Hz
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_rate=False)
    assert r["shift_samples"] == 2, r["shift_samples"]
    # True delay sits ON the scan edge (a truth fully outside the range gives a flat noise-level J curve whose argmin is
    # an arbitrary interior point, so that is not a boundary case): both edges must trip the boundary gate.
    for rng_ in ((2, 8), (-4, 2)):
        r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_rate=False, shift_range=rng_)
        assert r["shift_samples"] == 2, (rng_, r["shift_samples"])
        bad = [c[0] for c in r["verdict"]["criteria"] if not c[2]]
        assert any(b.startswith("latency shift interior") for b in bad), (rng_, bad)


def test_weak_instrument_gate_fails():
    """Instrument unrelated to the loop (pure noise; F is scale invariant so shrinking d does not weaken it): the first
    stage F gate must fail by name."""
    t, w, um, d = _loop(G1, G2, 3)
    z = np.random.default_rng(0).standard_normal(len(d))
    r = Y.fit_yaw(t, w, t, um, t, z, 4.0, 56.0, with_rate=False, shift_range=(0, 4))
    bad = [c[0] for c in r["verdict"]["criteria"] if not c[2]]
    assert any("first-stage F" in b for b in bad), bad


def test_df_gate_fails_when_df_below_one():
    """Two instrument columns for three parameters (G1, G2, intercept) -> df < 1 -> gate 'df >= 1' fails (MAJOR-2)."""
    t, w, um, d = _loop(G1, G2, 3)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_rate=False, lags1=[0], lags2=[0], shift_range=(0, 4))
    bad = [c[0] for c in r["verdict"]["criteria"] if not c[2]]
    assert r["j_df"] < 1 and any(b.startswith("Hansen df") for b in bad), (r["j_df"], bad)


def test_gmm_j_valid_vs_invalid_instrument():
    """MAJOR-1 known answer on iid data: valid instruments give J/df of order 1 and df = rank(Zf) - npar; one instrument
    correlated with the error (invalid) gives J far above the valid level."""
    rng = np.random.default_rng(0)
    n = 4000
    z = rng.standard_normal((n, 4))
    v = rng.standard_normal(n)
    x = z @ np.array([1.0, 0.5, 0.3, 0.2]) + v
    e = 0.5 * v + rng.standard_normal(n)  # x endogenous
    y = 2.0 * x + 1.0 + e
    X = x[:, None]
    jv, dfv = Y._gmm_j(y, np.hstack([np.ones((n, 1)), X]), np.hstack([np.ones((n, 1)), z]), _res2sls(y, X, z), 5)
    assert dfv == 3 and jv / dfv < 4.0, (jv, dfv)
    zb = z.copy()
    zb[:, 3] += 0.8 * e  # invalid instrument
    jb, dfb = Y._gmm_j(y, np.hstack([np.ones((n, 1)), X]), np.hstack([np.ones((n, 1)), zb]), _res2sls(y, X, zb), 5)
    assert dfb == 3 and jb > 10 * max(jv, 1.0) and jb / dfb > 20, (jb, jv)


def _res2sls(y, X, z):
    """2SLS residuals for the _gmm_j input (intercept + one regressor)."""
    n = len(y)
    Xf, Zf = np.hstack([np.ones((n, 1)), X]), np.hstack([np.ones((n, 1)), z])
    Xh = Zf @ np.linalg.lstsq(Zf, Xf, rcond=None)[0]
    return y - Xf @ np.linalg.solve(Xh.T @ Xf, Xh.T @ y)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
