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
        r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_g2=(BREAK != 1))
        assert abs(r["g1"] - G1) < max(0.05 * G1, 1.5 * r["ci1"]), (g1_set, r["g1"], r["ci1"])  # within 5 % or its CI
        assert r["ci1"] / G1 < 0.10
        assert abs(r.get("g2", np.nan) - G2) / G2 < 0.08, (g1_set, r.get("g2"))
        assert r["verdict"]["passed"], r["verdict"]["criteria"]
        assert min(r["f_eff"]) > 10


def test_omitting_du_dt_biases_g1():
    t, w, um, d = _loop(G1, G2, 5)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, with_g2=(BREAK == 2))
    assert abs(r["g1"] - G1) / G1 > 0.10, r["g1"]  # S124 model: biased by more than 10 %


def test_no_spinup_gives_g2_zero():
    t, w, um, d = _loop(G1, 0.0, 7)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0)
    assert abs(r["g2"]) < 0.08 * G2 and abs(r["g1"] - G1) < max(0.05 * G1, 1.5 * r["ci1"]), (r["g1"], r["g2"])


def test_mismatched_filter_is_caught():
    t, w, um, d = _loop(G1, G2, 9)
    r = Y.fit_yaw(t, w, t, um, t, d, 4.0, 56.0, _x2_taps=(None if BREAK == 3 else 7))
    assert not r["verdict"]["passed"], "regressors filtered with 7 taps vs regressand 15 must fail a gate"
    bad = [c[0] for c in r["verdict"]["criteria"] if not c[2]]
    print("mismatch gates failing:", bad, "G1 %.1f G2 %.2f J/df %.1f" % (r["g1"], r["g2"], r["j"] / r["j_df"]))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
