#!/usr/bin/env python3
"""Offline fit of the INDI control effectiveness G1 of one axis from an M3a injection hover log.

    python3 ident_fit.py flight.ulg --axis roll --t0 25 --t1 75

Model: alpha(t) = G1 * u_meas(t) + c, alpha = angular acceleration [rad/s^2] (differentiated gyro),
u_meas = actuator_torque_measured (normalised torque, (omega/W_MAX)^2 space, the units of G1 in the controller).
Level u (not increment) is regressed; with the intercept this equals the increment form.
Instrument = injected excitation indi_rate_status.inject (d), lagged copies. Regressand, regressor and instrument
go through the SAME FIR filter (condition iii). All timestamps are timestamp_sample (simulation time).
Method: ident_iv.py (iv_effectiveness). Exit code 1 and "IDENT FAILED" when a gate criterion fails.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ident_iv as iv  # noqa: E402

AXES = {"roll": 0, "pitch": 1, "yaw": 2}


# Physically justified latency scan (S124 K124 item 1/4): x(t) = u_meas(t + k/fs), k integer 800 Hz samples.
# Positive k = measured actuator arrives late (ESC telemetry, hold of the ~2.4 sample ZOH upstream, CAN/UART
# transport; ERPM_DLY order of 1-5 ms). Upper bound 12 samples = 15 ms, several times the largest plausible
# telemetry chain; lower bound -2 samples = -2.5 ms for timestamp jitter only (a measurement cannot precede the
# acceleration it caused). A minimum on either end of the scan is a FAIL (the shift would be absorbing misalignment).
SHIFT_MIN, SHIFT_MAX = -2, 12
CENTRAL_DIFF_MATCH = np.array([1.0, 4.0, 1.0]) / 6.0  # see _prepare, matches sinc(w dt) of np.gradient to O(w dt)^4
GATE = dict(f_min=10.0, j_ratio_max=20.0, chain_tol=0.01, ci_rel_max=0.15, excl_max=0.25, held_frac_min=0.25)


class HeldRegressorError(ValueError):
    """The regressor holds its value for more than 1/held_frac_min samples (ZOH upstream): refuse."""


def update_rate(u, min_frac):
    """Fraction of consecutive samples where u changes, and the true update period in samples (>= 1).
    Raises HeldRegressorError if the fraction is below min_frac (held samples dominate)."""
    ch = np.diff(np.asarray(u, float)) != 0
    frac = float(ch.mean()) if ch.size else 0.0
    if frac < min_frac:
        raise HeldRegressorError(f"regressor changes in only {100*frac:.1f} % of samples (< {100*min_frac:.0f} %): "
                                 "held (ZOH) samples dominate, refusing")
    return frac, max(1, int(np.floor(1.0 / frac + 1e-9)))


def robust_first_stage_f(x, z, lags, exclude, hac_lags, y=None):
    """HAC-robust effective first-stage F (Montiel Olea-Pflueger 2013, one endogenous regressor).

    x on [1, z(t-l)] gives pi (instrument coefficients) and its HAC covariance V = (Z'Z)^-1 S (Z'Z)^-1 (S: Newey-West
    long-run covariance of Z*e, same Bartlett kernel and lags as the second stage). F_eff = pi'(Z'Z)pi / tr((Z'Z) V).
    It equals the classical F when errors are homoskedastic and white, and it needs no inverse of V (the band-limited
    lags are nearly collinear, a Wald statistic on them is numerically unstable: tried, gave F ~ 1e13).
    Returns (F_eff, number of instruments)."""
    x = np.asarray(x, float)
    Z = np.column_stack([iv._shift(np.asarray(z, float), l) for l in lags])
    keep = np.isfinite(x) & np.isfinite(Z).all(1)
    if y is not None:
        keep &= np.isfinite(y)
    if exclude is not None:
        keep &= ~np.asarray(exclude, bool)
    Zf = np.hstack([np.ones((int(keep.sum()), 1)), Z[keep]])
    xk = x[keep]
    b, *_ = np.linalg.lstsq(Zf, xk, rcond=1e-10)
    e = xk - Zf @ b
    G = Zf.T @ Zf
    Qi = np.linalg.pinv(G, rcond=1e-10)
    V = Qi @ iv._hac(Zf * e[:, None], hac_lags) @ Qi
    # intercept partialled out: use the instrument block of G (centred) and V
    Gc = G[1:, 1:] - np.outer(G[1:, 0], G[0, 1:]) / G[0, 0]
    bz = b[1:]
    return float(bz @ Gc @ bz / np.trace(Gc @ V[1:, 1:])), len(lags)


def chain_mismatch(ntaps_y, ntaps_x, fmax=60.0, fs=800.0):
    """Max relative gain difference over 1..fmax Hz between the regressand chain (np.gradient x FIR_y) and the
    regressor chain (C x FIR_x). Both are zero-phase symmetric operations, so the gain suffices. Condition (iii)."""
    f = np.linspace(1.0, fmax, 120)
    th = 2 * np.pi * f / fs

    def fir(n):
        tp = iv.smooth_taps(n)
        h = len(tp) // 2
        return sum(tp[h + j] * np.cos(j * th) for j in range(-h, h + 1))
    hy = np.sin(th) / th * fir(ntaps_y)
    c = CENTRAL_DIFF_MATCH
    hx = (c[1] + 2.0 * c[0] * np.cos(th)) * fir(ntaps_x)
    return float(np.max(np.abs(hx / hy - 1.0)))


def _lead(a, k):
    """b[t] = a[t+k] (any integer k), NaN where undefined."""
    b = np.full(a.shape, np.nan)
    if k == 0:
        b[:] = a
    elif k > 0:
        b[:-k] = a[k:]
    else:
        b[-k:] = a[:k]
    return b


def _prepare(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs, ntaps_x, held_frac_min):
    """y, x, z on the 800 Hz grid, before any latency shift.

    One filter chain for both sides (condition iii): y = F[ D w ] with D = np.gradient (gain sinc(w dt));
    x = F[ C u ], z = F[ C z ] with C = [1,4,1]/6 which has gain 1 - (1/3)(1 - cos(w dt)) = sinc(w dt) + O((w dt)^4)
    (0.9637 vs 0.9638 at 60 Hz) and zero phase, so the differentiator gain is present on both sides. No fractional
    delay anywhere (shifts are integer samples, applied after filtering, which is exact for an LTI filter).
    Regressor rows: only samples where the value changed (true telemetry updates), linearly interpolated between."""
    dt = 1.0 / fs
    t_grid = np.arange(t0, t1, dt)
    taps = iv.smooth_taps(ntaps)
    taps_x = iv.smooth_taps(ntaps if ntaps_x is None else ntaps_x)
    w = iv.resample_to_grid(t_gyro, omega, t_grid)
    y = iv.apply_taps(np.gradient(w, dt), taps)
    t_u = np.asarray(t_u, float)
    u = np.asarray(u, float)
    chg = np.concatenate([[True], np.diff(u) != 0])
    xg = np.interp(t_grid, t_u[chg], u[chg])
    xg[(t_grid < t_u[0]) | (t_grid > t_u[-1])] = np.nan
    x = iv.apply_taps(iv.apply_taps(xg, CENTRAL_DIFF_MATCH), taps_x)
    zz = iv.apply_taps(iv.apply_taps(iv.resample_to_grid(t_z, z, t_grid), CENTRAL_DIFF_MATCH), taps)
    excl = np.zeros(len(t_grid), bool)
    if sat is not None:
        ts = np.asarray(t_sat, float)
        idx = np.clip(np.searchsorted(ts, t_grid, side="right") - 1, 0, len(ts) - 1)
        s = np.asarray(sat, bool)[idx].astype(float)
        excl |= np.convolve(s, np.ones(len(taps)), mode="same") > 0
    return y, x, zz, excl


def _fit_once(y, x, zz, excl, k, m, lags, hac_lags, with_f=True):
    """IV fit with the regressor shifted by k samples, rows decimated by m (true update period)."""
    xs = _lead(x, k)
    sl = slice(None, None, m)
    lg = sorted({max(0, int(round(l / m))) for l in lags})
    hl = max(1, hac_lags // m)
    r = iv.iv_effectiveness(y[sl], xs[sl], zz[sl], lags=lg, exclude=excl[sl], hac_lags=hl)
    ok = np.isfinite(y[sl]) & np.isfinite(xs[sl])
    fr, rank = robust_first_stage_f(xs[sl], zz[sl], lg, excl[sl], hl, y=y[sl]) if with_f else (np.nan, 0)
    return dict(g1=float(r["beta"][0]), se=float(r["se"][0]), ci95=1.96 * float(r["se"][0]), f=fr, f_rank=rank,
                f_classic=float(r["f_first"][0]), n=int(r["n"]), ols=float(r["ols"]["beta"][0]),
                ols_se=float(r["ols"]["se"][0]), intercept=r["intercept"], j=r["j_stat"], j_df=r["j_df"],
                excl_frac=float(excl[sl][ok].mean()) if ok.any() else 1.0, shift=k, decim=m)


def fit_axis(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat=None, t_sat=None, ntaps=15, fs=800.0,
             lags=None, hac_lags=400, scan_hac_lags=80, shift_range=None, compensate_latency=True, ntaps_x=None, gate=None):
    """Core pipeline on already extracted arrays (seconds, SI). Returns dict of results incl. `verdict`.

    The latency shift (integer samples in SHIFT_MIN..SHIFT_MAX, scan chosen by minimum Hansen J, same HAC lags
    in scan and final fit) is reported with the whole J curve; a minimum on a scan boundary is a gate FAIL.
    ntaps_x is a TEST HOOK (different FIR on the regressor only: deliberate mismatch).
    Gate (see `verdict`): robust first-stage F, Hansen J/df, shift interior, CI, excluded fraction."""
    g = dict(GATE, **(gate or {}))
    _, m = update_rate(u, g["held_frac_min"])
    lags = list(range(0, 33, 2)) if lags is None else list(lags)
    y, x, zz, excl = _prepare(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs, ntaps_x, g["held_frac_min"])
    lo, hi = shift_range if shift_range is not None else (SHIFT_MIN, SHIFT_MAX)
    cand = list(range(lo, hi + 1)) if compensate_latency else [0]
    # scan J with scan_hac_lags (cost: HAC at 400 lags is ~5 s per fit); the reported fit and the gate use hac_lags
    curve = [(k, _fit_once(y, x, zz, excl, k, m, lags, scan_hac_lags, with_f=False)) for k in cand]
    jv = np.array([r["j"] for _, r in curve])
    i = int(np.argmin(jv))
    r = _fit_once(y, x, zz, excl, cand[i], m, lags, hac_lags)
    r.update(j_curve=[(k, float(j)) for (k, _), j in zip(curve, jv)], shift_samples=cand[i], shift_s=cand[i] / fs,
             at_boundary=bool(compensate_latency and i in (0, len(cand) - 1)), update_frac=1.0 / m, dt=1.0 / fs,
             comp_lag_samples=float(cand[i]), comp_lag_s=cand[i] / fs)
    if 0 in cand:
        r0 = curve[cand.index(0)][1]
        r.update(g1_nocomp=r0["g1"], ols_nocomp=r0["ols"], j_nocomp=r0["j"])
    cm = chain_mismatch(ntaps, ntaps if ntaps_x is None else ntaps_x, fs=fs)
    jr = r["j"] / max(r["j_df"], 1)
    crit = [("robust first-stage F >= %g" % g["f_min"], r["f"], r["f"] >= g["f_min"]),
            ("Hansen J/df <= %g" % g["j_ratio_max"], jr, jr <= g["j_ratio_max"]),
            ("latency shift interior to scan [%d,%d]" % (lo, hi), cand[i], not r["at_boundary"]),
            ("95%% CI/|G1| <= %g" % g["ci_rel_max"], r["ci95"] / abs(r["g1"]), r["ci95"] / abs(r["g1"]) <= g["ci_rel_max"]),
            ("filter-chain gain match (regressor vs regressand) <= %g" % g["chain_tol"], cm, cm <= g["chain_tol"]),
            ("excluded fraction <= %g" % g["excl_max"], r["excl_frac"], r["excl_frac"] <= g["excl_max"])]
    r["verdict"] = dict(criteria=crit, passed=all(c[2] for c in crit))
    return r


def load(path, axis):
    from pyulog import ULog
    ul = ULog(path, ["sensor_gyro", "actuator_torque_measured", "indi_rate_status", "control_allocator_status"])
    d = {m.name: m.data for m in ul.data_list}
    k = AXES[axis]
    ts = lambda m: np.asarray(m["timestamp_sample"], float) * 1e-6  # noqa: E731
    g, a, s, c = d["sensor_gyro"], d["actuator_torque_measured"], d["indi_rate_status"], d["control_allocator_status"]
    tg = ts(g)
    t_start = ul.start_timestamp * 1e-6
    out = dict(t_gyro=tg, omega=np.asarray(g["xyz"[k]], float), t_u=ts(a),
               u=np.asarray(a["torque[%d]" % k], float), t_z=ts(s), z=np.asarray(s["inject[%d]" % k], float),
               t_sat=np.asarray(c["timestamp"], float) * 1e-6,
               sat=~np.asarray(c["torque_setpoint_achieved[%d]" % k] if ("torque_setpoint_achieved[%d]" % k) in c
                               else c["torque_setpoint_achieved"], bool), t_log0=t_start)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulg")
    ap.add_argument("--axis", default="roll", choices=list(AXES))
    ap.add_argument("--t0", type=float, required=True, help="window start, log seconds (since log start)")
    ap.add_argument("--t1", type=float, required=True)
    ap.add_argument("--ntaps", type=int, default=15)
    a = ap.parse_args(argv)
    D = load(a.ulg, a.axis)
    t0l = D.pop("t_log0")
    for key in ("t_gyro", "t_u", "t_z", "t_sat"):
        D[key] = D[key] - t0l
    try:
        r = fit_axis(D["t_gyro"], D["omega"], D["t_u"], D["u"], D["t_z"], D["z"], a.t0, a.t1,
                     sat=D["sat"], t_sat=D["t_sat"], ntaps=a.ntaps)
    except HeldRegressorError as e:
        print(f"FAIL  regressor held: {e}")
        return 1
    print(f"axis {a.axis}  window {a.t0}-{a.t1} s  taps {a.ntaps}  row decimation {r['decim']}")
    print(f"G1 (IV)        {r['g1']:.1f} rad/s^2  se {r['se']:.1f}  95% CI +-{r['ci95']:.1f} ({100*r['ci95']/abs(r['g1']):.1f} %)")
    print(f"G1 (OLS)       {r['ols']:.1f}  se {r['ols_se']:.1f}")
    print(f"first-stage F  effective HAC (MOP, {r['f_rank']} instruments) {r['f']:.1f}   classical {r['f_classic']:.1f}")
    print(f"samples        {r['n']}  excluded (saturated) fraction {r['excl_frac']:.4f}")
    print(f"Hansen J       {r['j']:.1f} (df {r['j_df']})  intercept {r['intercept']:.3f}")
    print(f"latency shift (min Hansen J) {r['shift_samples']} samples = {1e3*r['shift_s']:.2f} ms; J curve "
          + " ".join(f"{k}:{j:.0f}" for k, j in r["j_curve"]))
    for name, val, ok in r["verdict"]["criteria"]:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  (value {val:.4g})")
    print("IDENT " + ("PASS" if r["verdict"]["passed"] else "FAILED"))
    return 0 if r["verdict"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
