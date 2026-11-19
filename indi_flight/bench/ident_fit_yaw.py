#!/usr/bin/env python3
"""Offline two-regressor IV fit of the yaw effectiveness G1 and the rotor spin-up term G2 from an injection hover log.

    python3 ident_fit_yaw.py flight.ulg --axis yaw --t0 22.1 --t1 76.0

Model (firmware convention, src/lib/indi_rate_control/indi_rate_control.cpp:442-459 and .hpp:60-63):
    alpha(t) = G1 * u(t) + G2 * du/dt(t) + c,    (G1 + G2 s) Delta = nu - (1 + c) a_f
alpha [rad/s^2] = differentiated gyro; u = actuator_torque_measured.torque[axis] (normalised torque); du/dt in 1/s
(the firmware uses G2/dt * (Delta_k - Delta_k-1) = G2 * d(Delta)/dt, so G2 has units rad/s^2 per (unit torque / s),
i.e. rad/s, and is NOT a per-sample difference coefficient; u here is the measured one, the firmware term acts on the
commanded increment, same thing in the quasi-static band of the injection).
Instruments: injected excitation d = indi_rate_status.inject[axis] lagged copies AND d(d)/dt lagged copies.
Same filter chain on regressand, both regressors and instruments (see _prepare2), common integer-sample latency shift
on both regressors chosen by minimum Hansen J. First stage: Sanderson-Windmeijer conditional F per regressor
(classical and HAC effective). Helpers are imported from ident_fit.py (not modified).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ident_fit as base  # noqa: E402
import ident_iv as iv  # noqa: E402

GATE2 = dict(base.GATE, g2_ci_rel_max=0.5)


def _prepare2(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs):
    """y = F[D w]; x1 = F[C u]; x2 = F[D u] (true-derivative gain sinc(w dt), same as the D in y, so the G2 term
    enters y and x2 with the same gain); instruments z1 = F[C z], z2 = F[D z]. Held regressor rows are interpolated
    between the true updates as in ident_fit._prepare."""
    dt = 1.0 / fs
    t_grid = np.arange(t0, t1, dt)
    taps = iv.smooth_taps(ntaps)
    w = iv.resample_to_grid(t_gyro, omega, t_grid)
    y = iv.apply_taps(np.gradient(w, dt), taps)
    t_u = np.asarray(t_u, float)
    u = np.asarray(u, float)
    chg = np.concatenate([[True], np.diff(u) != 0])
    xg = np.interp(t_grid, t_u[chg], u[chg])
    xg[(t_grid < t_u[0]) | (t_grid > t_u[-1])] = np.nan
    x1 = iv.apply_taps(iv.apply_taps(xg, base.CENTRAL_DIFF_MATCH), taps)
    x2 = iv.apply_taps(np.gradient(xg, dt), taps)
    zg = iv.resample_to_grid(t_z, z, t_grid)
    z1 = iv.apply_taps(iv.apply_taps(zg, base.CENTRAL_DIFF_MATCH), taps)
    z2 = iv.apply_taps(np.gradient(zg, dt), taps)
    excl = np.zeros(len(t_grid), bool)
    if sat is not None:
        ts = np.asarray(t_sat, float)
        idx = np.clip(np.searchsorted(ts, t_grid, side="right") - 1, 0, len(ts) - 1)
        s = np.asarray(sat, bool)[idx].astype(float)
        excl |= np.convolve(s, np.ones(len(taps)), mode="same") > 0
    return y, np.column_stack([x1, x2]), z1, z2, excl


def _eff_f(xt, Zf, y_ok_keep, hac_lags):
    """HAC effective first-stage F (Montiel Olea-Pflueger form, as ident_fit.robust_first_stage_f) of the
    already residualised endogenous regressor xt on [1, Z]."""
    b, *_ = np.linalg.lstsq(Zf, xt, rcond=1e-10)
    e = xt - Zf @ b
    G = Zf.T @ Zf
    Qi = np.linalg.pinv(G, rcond=1e-10)
    V = Qi @ iv._hac(Zf * e[:, None], hac_lags) @ Qi
    Gc = G[1:, 1:] - np.outer(G[1:, 0], G[0, 1:]) / G[0, 0]
    bz = b[1:]
    return float(bz @ Gc @ bz / np.trace(Gc @ V[1:, 1:]))


def iv2(y, X, Zraw, hac_lags, with_f=True):
    """2SLS of y on [1, X] (X (n,2) endogenous) with instruments [1, Zraw] (Zraw (n,q), lags already built).
    Returns beta (2,), se (2,) HAC, J, df, SW F per regressor (classical, effective), n, OLS beta."""
    keep = np.isfinite(y) & np.isfinite(X).all(1) & np.isfinite(Zraw).all(1)
    return _iv2_keep(y, X, Zraw, keep, hac_lags, with_f)


def _iv2_keep(y, X, Zraw, keep, hac_lags, with_f):
    y, X, Z = y[keep], X[keep], Zraw[keep]
    n, k = X.shape
    one = np.ones((n, 1))
    Xf = np.hstack([one, X])
    Zf = np.hstack([one, Z])
    pinv = np.linalg.pinv(Zf, rcond=1e-10)

    def proj(a):
        return Zf @ (pinv @ a)
    Xh = proj(Xf)
    beta = np.linalg.solve(Xh.T @ Xf, Xh.T @ y)
    res = y - Xf @ beta
    A = np.linalg.inv(Xh.T @ Xh)
    se = np.sqrt(np.diag(A @ iv._hac(Xh * res[:, None], hac_lags) @ A))
    g = Zf * res[:, None]
    S = iv._hac(g, hac_lags)
    gm = g.sum(0)
    j = float(gm @ np.linalg.pinv(S, rcond=1e-10) @ gm)
    df = int(np.linalg.matrix_rank(S, tol=1e-10 * np.linalg.norm(S, 2))) - Xf.shape[1]
    ols, *_ = np.linalg.lstsq(Xf, y, rcond=None)
    out = dict(beta=beta[1:], se=se[1:], intercept=float(beta[0]), j=j, j_df=df, n=int(n), ols=ols[1:])
    if with_f:
        q = Z.shape[1]
        fc, fe = [], []
        for jx in range(k):
            oth = [i for i in range(k) if i != jx]
            xj = X[:, jx]
            xo_hat = proj(X[:, oth])  # fitted values of the other endogenous regressors
            Ho = np.hstack([one, xo_hat])
            gam, *_ = np.linalg.lstsq(Ho, xj, rcond=None)
            xt = xj - xo_hat @ gam[1:]  # Sanderson-Windmeijer: remove the part explained by the other fitted regressors
            r1 = xt - proj(xt)
            r0 = xt - xt.mean()
            rss1, rss0 = float(r1 @ r1), float(r0 @ r0)
            dfn = max(q - (k - 1), 1)
            fc.append(((rss0 - rss1) / dfn) / (rss1 / max(n - q - 1, 1)))
            fe.append(_eff_f(xt, Zf, None, hac_lags))
        out.update(f_sw=np.array(fc), f_eff=np.array(fe))
    return out


def _lead2(X, k):
    return np.column_stack([base._lead(X[:, i], k) for i in range(X.shape[1])])


def _build_Z(z1, z2, sl, lags1, lags2, m):
    cols = [iv._shift(z1[sl], max(0, int(round(l / m)))) for l in lags1]
    cols += [iv._shift(z2[sl], max(0, int(round(l / m)))) for l in lags2]
    return np.column_stack(cols)


def fit_yaw(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat=None, t_sat=None, ntaps=15, fs=800.0, lags1=None, lags2=None,
            hac_lags=400, scan_hac_lags=80, shift_range=None, compensate_latency=True, gate=None, with_g2=True,
            _x2_taps=None):
    """Returns dict with g1, g2, se, ci95, f (SW), j, shift, verdict. with_g2=False fits G1 only (the S124 model, for
    contrast). `_x2_taps` is a TEST HOOK: different FIR length on the regressors only (deliberate mismatch)."""
    g = dict(GATE2, **(gate or {}))
    _, m = base.update_rate(u, g["held_frac_min"])
    lags1 = list(range(0, 33, 2)) if lags1 is None else list(lags1)
    lags2 = list(range(0, 33, 4)) if lags2 is None else list(lags2)
    y, X, z1, z2, excl = _prepare2(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs)
    if _x2_taps is not None:  # mismatch hook: re-filter the regressors with another moving average
        tp = iv.smooth_taps(_x2_taps)
        X = np.column_stack([iv.apply_taps(X[:, i], tp) for i in range(2)])
    lo, hi = shift_range if shift_range is not None else (base.SHIFT_MIN, base.SHIFT_MAX)
    cand = list(range(lo, hi + 1)) if compensate_latency else [0]
    sl = slice(None, None, m)
    Zr = _build_Z(z1, z2, sl, lags1, lags2, m)
    hs = max(1, scan_hac_lags // m)
    hf = max(1, hac_lags // m)

    def run(k, hl, with_f):
        Xs = _lead2(X, k)[sl]
        Xs = Xs if with_g2 else Xs[:, :1]
        ok = np.isfinite(y[sl]) & np.isfinite(Xs).all(1) & np.isfinite(Zr).all(1) & ~excl[sl]
        if not with_g2:  # G1-only: reuse the same machinery with a single regressor
            return _fit1(y[sl], Xs, Zr, ok, hl)
        r = _iv2_keep(y[sl], Xs, Zr, ok, hl, with_f)
        r["excl_frac"] = float(excl[sl][np.isfinite(y[sl])].mean())
        return r
    curve = [(k, run(k, hs, False)) for k in cand]
    jv = np.array([r["j"] for _, r in curve])
    i = int(np.argmin(jv))
    r = run(cand[i], hf, True)
    r.update(j_curve=[(k, float(j)) for (k, _), j in zip(curve, jv)], shift_samples=cand[i], shift_s=cand[i] / fs,
             at_boundary=bool(compensate_latency and i in (0, len(cand) - 1)), decim=m, update_frac=1.0 / m)
    r["g1"], r["se1"] = float(r["beta"][0]), float(r["se"][0])
    r["ci1"] = 1.96 * r["se1"]
    if with_g2:
        r["g2"], r["se2"] = float(r["beta"][1]), float(r["se"][1])
        r["ci2"] = 1.96 * r["se2"]
    cm = base.chain_mismatch(ntaps, ntaps, fs=fs)
    jr = r["j"] / max(r["j_df"], 1)
    crit = []
    if with_g2:
        for nm, fv in zip(("G1", "G2"), r["f_eff"]):
            crit.append(("SW effective first-stage F (%s) >= %g" % (nm, g["f_min"]), float(fv), fv >= g["f_min"]))
    crit += [("Hansen J/df <= %g" % g["j_ratio_max"], jr, jr <= g["j_ratio_max"]),
             ("latency shift interior to scan [%d,%d]" % (lo, hi), cand[i], not r["at_boundary"]),
             ("95%% CI/|G1| <= %g" % g["ci_rel_max"], r["ci1"] / abs(r["g1"]), r["ci1"] / abs(r["g1"]) <= g["ci_rel_max"])]
    if with_g2:
        crit.append(("95%% CI/|G2| <= %g" % g["g2_ci_rel_max"], r["ci2"] / abs(r["g2"]),
                     r["ci2"] / abs(r["g2"]) <= g["g2_ci_rel_max"]))
    crit += [("filter-chain gain match (G1 column) <= %g" % g["chain_tol"], cm, cm <= g["chain_tol"]),
             ("excluded fraction <= %g" % g["excl_max"], r["excl_frac"], r["excl_frac"] <= g["excl_max"])]
    if _x2_taps is not None:  # honest chain gate for the deliberate mismatch
        cm2 = base.chain_mismatch(ntaps, _x2_taps, fs=fs)
        crit.append(("filter-chain gain match (regressor FIR %d vs %d) <= %g" % (_x2_taps, ntaps, g["chain_tol"]),
                     cm2, cm2 <= g["chain_tol"]))
    r["verdict"] = dict(criteria=crit, passed=all(c[2] for c in crit))
    return r


def _fit1(y, X1, Zr, ok, hl):
    """G1-only 2SLS with the full instrument set (contrast: the S124 model)."""
    yy, x, Z = y[ok], X1[ok], Zr[ok]
    n = len(yy)
    one = np.ones((n, 1))
    Xf, Zf = np.hstack([one, x]), np.hstack([one, Z])
    Xh = Zf @ (np.linalg.pinv(Zf, rcond=1e-10) @ Xf)
    b = np.linalg.solve(Xh.T @ Xf, Xh.T @ yy)
    res = yy - Xf @ b
    A = np.linalg.inv(Xh.T @ Xh)
    se = np.sqrt(np.diag(A @ iv._hac(Xh * res[:, None], hl) @ A))
    g = Zf * res[:, None]
    S = iv._hac(g, hl)
    gm = g.sum(0)
    j = float(gm @ np.linalg.pinv(S, rcond=1e-10) @ gm)
    df = int(np.linalg.matrix_rank(S, tol=1e-10 * np.linalg.norm(S, 2))) - Xf.shape[1]
    return dict(beta=b[1:], se=se[1:], j=j, j_df=df, n=n, intercept=float(b[0]), excl_frac=0.0,
                f_eff=np.array([np.nan]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulg")
    ap.add_argument("--axis", default="yaw", choices=list(base.AXES))
    ap.add_argument("--t0", type=float, required=True)
    ap.add_argument("--t1", type=float, required=True)
    ap.add_argument("--ntaps", type=int, default=15)
    ap.add_argument("--g1-only", action="store_true", help="contrast: drop the du/dt regressor (S124 model)")
    a = ap.parse_args(argv)
    D = base.load(a.ulg, a.axis)
    t0l = D.pop("t_log0")
    for key in ("t_gyro", "t_u", "t_z", "t_sat"):
        D[key] = D[key] - t0l
    try:
        r = fit_yaw(D["t_gyro"], D["omega"], D["t_u"], D["u"], D["t_z"], D["z"], a.t0, a.t1, sat=D["sat"],
                    t_sat=D["t_sat"], ntaps=a.ntaps, with_g2=not a.g1_only)
    except base.HeldRegressorError as e:
        print(f"FAIL  regressor held: {e}")
        return 1
    print(f"axis {a.axis} window {a.t0}-{a.t1} s taps {a.ntaps} decim {r['decim']} n {r['n']}")
    print(f"G1 {r['g1']:.2f} rad/s^2 per unit  95% CI +-{r['ci1']:.2f} ({100*r['ci1']/abs(r['g1']):.1f} %)")
    if not a.g1_only:
        print(f"G2 {r['g2']:.3f} (rad/s^2 per unit/s, firmware units)  95% CI +-{r['ci2']:.3f} ({100*r['ci2']/abs(r['g2']):.1f} %)")
        print(f"first stage SW F classical {r['f_sw'][0]:.1f} {r['f_sw'][1]:.1f}  HAC effective {r['f_eff'][0]:.1f} {r['f_eff'][1]:.1f}")
        print(f"OLS G1 {r['ols'][0]:.2f} G2 {r['ols'][1]:.3f}")
    print(f"Hansen J {r['j']:.1f} (df {r['j_df']}) intercept {r['intercept']:.3f} shift {r['shift_samples']} samples")
    print("J curve " + " ".join(f"{k}:{j:.0f}" for k, j in r["j_curve"]))
    for name, val, ok in r["verdict"]["criteria"]:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (value {val:.4g})")
    print("IDENT " + ("PASS" if r["verdict"]["passed"] else "FAILED"))
    return 0 if r["verdict"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
