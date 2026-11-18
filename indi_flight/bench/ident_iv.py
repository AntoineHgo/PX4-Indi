#!/usr/bin/env python3
"""Offline INDI identification estimator, methods M1 (effectiveness, IV) and M3 (latency), see
indi_flight/design/ident_concept.md sec 2 and indi_flight/design/i119_ident_iv.md.

Library:
  iv_effectiveness(y, x, z, lags=None, exclude=None)  instrumental-variables (2SLS) regression with intercept
  latency_by_xcorr(alpha, g1_du, dt, max_lag)         lag of max correlation, parabolic sub-sample refinement
  resample_to_grid / smooth_taps / apply_taps / prepare_regression   preprocessing

CLI (log audit only, see main()): python3 ident_iv.py audit flight.ulg
"""
import argparse
import sys

import numpy as np

# ----------------------------------------------------------------------------------------------------------------
# preprocessing


def resample_to_grid(t_src, v_src, t_grid):
    """Linear interpolation of a source signal onto the common simulation-time grid t_grid (seconds).

    Refuses (ValueError) when the source is slower than the grid (median source period > 1.05 grid periods):
    lesson "no zero-order hold of decimated topics". Interpolating up from a decimated topic would invent a
    staircase or a bandwidth the data does not have; the caller must choose a grid no finer than the slowest
    signal instead. Samples of the grid outside the source span are NaN.
    """
    t_src = np.asarray(t_src, float)
    v_src = np.asarray(v_src, float)
    t_grid = np.asarray(t_grid, float)
    if t_src.size < 2 or t_grid.size < 2:
        raise ValueError("need at least 2 samples")
    src_dt = float(np.median(np.diff(t_src)))
    grid_dt = float(np.median(np.diff(t_grid)))
    if src_dt > 1.05 * grid_dt:
        raise ValueError(f"source period {src_dt:.6f} s is longer than grid period {grid_dt:.6f} s: "
                         "refusing to up-sample a decimated signal (no zero-order hold)")
    out = np.interp(t_grid, t_src, v_src)
    out[(t_grid < t_src[0]) | (t_grid > t_src[-1])] = np.nan
    return out


def smooth_taps(n):
    """Linear FIR filter F shared by regressand and regressors: centred moving average of n (odd) taps."""
    if n < 1 or n % 2 == 0:
        raise ValueError("n must be odd and >= 1")
    return np.full(n, 1.0 / n)


def apply_taps(x, taps):
    """Zero-phase application of the FIR filter F (same length output, edge samples NaN)."""
    x = np.asarray(x, float)
    n = len(taps)
    out = np.convolve(x, taps, mode="same")
    h = n // 2
    if h:
        out[:h] = np.nan
        out[-h:] = np.nan
    return out


def prepare_regression(t_gyro, omega, t_u, du, t_grid, taps, saturated=None, t_sat=None, z=None, t_z=None):
    """Build the (y, x, z, exclude) arrays for iv_effectiveness on the common grid t_grid.

    The gyro is differentiated and then filtered with F; the regressor du (measured actuator increment) and the
    instrument z are filtered with the SAME linear filter F (apply_taps with the same taps). Using one filter on
    all of them keeps the regression y = G1 x exact for any F, because F is linear and time invariant; a
    different filter on regressand and regressor would bias G1 and shift the apparent latency.

    saturated (bool samples at t_sat) is resampled by nearest-previous and any grid sample at or next to a True
    sample (within the filter support) is excluded. All signals must be at least as fast as the grid
    (resample_to_grid raises otherwise).
    """
    w = resample_to_grid(t_gyro, omega, t_grid)
    dt = float(np.median(np.diff(t_grid)))
    alpha_raw = np.gradient(w, dt)
    y = apply_taps(alpha_raw, taps)
    x = apply_taps(resample_to_grid(t_u, du, t_grid), taps)
    zz = None if z is None else apply_taps(resample_to_grid(t_z, z, t_grid), taps)
    exclude = np.zeros(len(t_grid), bool)
    if saturated is not None:
        ts = np.asarray(t_sat, float)
        idx = np.clip(np.searchsorted(ts, t_grid, side="right") - 1, 0, len(ts) - 1)
        s = np.asarray(saturated, bool)[idx].astype(float)
        exclude |= np.convolve(s, np.ones(len(taps)), mode="same") > 0
    return y, x, zz, exclude


# ----------------------------------------------------------------------------------------------------------------
# M1: instrumental variables


def _shift(a, k):
    """b[t] = a[t-k] (k >= 0), first k entries NaN."""
    b = np.full(a.shape, np.nan)
    if k == 0:
        b[:] = a
    else:
        b[k:] = a[:-k]
    return b


def _ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    s2 = float(res @ res) / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    return beta, np.sqrt(np.diag(cov)), res


def iv_effectiveness(y, x, z, lags=None, exclude=None):
    """Two-stage least squares of y on [1, x] with instruments [1, z(t-l) for l in lags].

    y        (n,) angular acceleration about one axis, rad/s^2 (already filtered, see prepare_regression)
    x        (n,) or (n,k) regressors: measured normalised actuator increment du, optionally a second column
             d(du)/dt (yaw spin-up G2). Must be filtered with the same filter as y.
    z        (n,) injected excitation signal (same filter). Uncorrelated with the process disturbance by
             construction (it is generated by the injector), correlated with x through the actuator.
    lags     instrument lags in samples (default 0,1,2,3 ... enough that instruments >= regressors; extended
             automatically to k+1 lags when fewer). z(t-l) are the lagged copies.
    exclude  optional bool (n,), True = drop the sample (saturated); lags use the unmasked series, rows dropped
             after building the instrument matrix. Non-finite rows are dropped too.

    Returns dict: beta (k,), intercept, se (k,), se_intercept, n, f_first (first-stage F of the excluded
    instruments, per regressor), f_min, ols{beta, intercept, se, se_intercept}.
    """
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[:, None]
    z = np.asarray(z, float)
    k = x.shape[1]
    lags = list(range(max(4, k + 1))) if lags is None else list(lags)
    if len(lags) < k:
        raise ValueError("fewer instruments than regressors")
    Z = np.column_stack([_shift(z, l) for l in lags])
    keep = np.isfinite(y) & np.isfinite(x).all(1) & np.isfinite(Z).all(1)
    if exclude is not None:
        keep &= ~np.asarray(exclude, bool)
    n = int(keep.sum())
    if n < 3 * (len(lags) + 1) + 10:
        raise ValueError(f"too few usable samples ({n})")
    y, x, Z = y[keep], x[keep], Z[keep]
    one = np.ones((n, 1))
    X = np.hstack([one, x])
    Zf = np.hstack([one, Z])
    # first stage. Never form the n x n projector Zf pinv(Zf): at n ~ 48k it is 19 GB (I119 OOM, S119).
    # proj(A) = Zf (pinv(Zf) A) costs O(n q) memory.
    Zf_pinv = np.linalg.pinv(Zf)  # (q+1, n)

    def proj(a):
        return Zf @ (Zf_pinv @ a)

    Xh = proj(X)
    beta = np.linalg.solve(Xh.T @ X, Xh.T @ y)
    res = y - X @ beta
    s2 = float(res @ res) / max(n - X.shape[1], 1)
    cov = s2 * np.linalg.inv(Xh.T @ Xh)
    se = np.sqrt(np.diag(cov))
    # first-stage F (excluded instruments) per regressor, each regressed alone on [1, Z]
    q = Z.shape[1]
    f_first = []
    for j in range(k):
        xj = x[:, j]
        r1 = xj - proj(xj)
        r0 = xj - xj.mean()
        rss1, rss0 = float(r1 @ r1), float(r0 @ r0)
        f_first.append(((rss0 - rss1) / q) / (rss1 / max(n - q - 1, 1)) if rss1 > 0 else np.inf)
    ob, ose, _ = _ols(X, y)
    return dict(beta=beta[1:], intercept=float(beta[0]), se=se[1:], se_intercept=float(se[0]), n=n,
                f_first=np.array(f_first), f_min=float(min(f_first)),
                ols=dict(beta=ob[1:], intercept=float(ob[0]), se=ose[1:], se_intercept=float(ose[0])))


# ----------------------------------------------------------------------------------------------------------------
# M3: latency


def latency_by_xcorr(alpha, g1_du, dt, max_lag):
    """Lag of maximum correlation between alpha and G1*du_meas.

    Convention: lag k >= 0 maximises corr(alpha[t], g1_du[t+k]), i.e. the measured actuator signal is delayed by
    k samples with respect to the acceleration it caused (telemetry latency: alpha(t) responds to the true
    actuator, the measured du arrives k samples late). Means are removed, correlation is normalised by the
    overlap energies. Sub-sample refinement: parabola through the peak and its two neighbours.

    Returns dict: lag_samples (float, refined), lag_s, peak (normalised correlation), lag_int, corr (array
    over 0..max_lag).
    """
    a = np.asarray(alpha, float)
    g = np.asarray(g1_du, float)
    ok = np.isfinite(a) & np.isfinite(g)
    a = np.where(ok, a, 0.0)
    g = np.where(ok, g, 0.0)
    a = a - a[ok].mean()
    g = g - g[ok].mean()
    n = len(a)
    c = np.zeros(max_lag + 1)
    for k in range(max_lag + 1):
        aa, gg = a[:n - k], g[k:]
        den = np.sqrt((aa @ aa) * (gg @ gg))
        c[k] = (aa @ gg) / den if den > 0 else 0.0
    i = int(np.argmax(c))
    frac = 0.0
    if 0 < i < max_lag:
        denom = c[i - 1] - 2 * c[i] + c[i + 1]
        if denom != 0:
            frac = 0.5 * (c[i - 1] - c[i + 1]) / denom
    lag = i + frac
    return dict(lag_samples=float(lag), lag_s=float(lag * dt), peak=float(c[i]), lag_int=i, corr=c)


# ----------------------------------------------------------------------------------------------------------------
# CLI: log audit

# signal -> (topic, field, minimum rate Hz, why)
REQUIRED = [
    ("injection d", "indi_rate_status", "inject", 100.0, "instrument z"),
    ("measured actuator", "actuator_torque_measured", "torque", 100.0, "regressor du_meas (ESC telemetry bound)"),
    ("gyro", "vehicle_angular_velocity", "xyz", 100.0, "alpha by differentiation with the regressor filter"),
    ("saturation flag", "control_allocator_status", "torque_setpoint_achieved", 100.0, "exclusion mask"),
]


def audit(path, out=sys.stdout):
    from pyulog import ULog
    ul = ULog(path)
    ok = True
    for name, topic, field, min_hz, why in REQUIRED:
        ds = [d for d in ul.data_list if d.name == topic]
        if not ds:
            print(f"MISSING  {name:18s} {topic} not in log ({why})", file=out)
            ok = False
            continue
        d = max(ds, key=lambda e: len(e.data["timestamp"]))
        t = d.data["timestamp"] * 1e-6
        hz = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0
        good = hz >= min_hz
        ok &= good
        print(f"{'ok' if good else 'TOO SLOW':8s} {name:18s} {topic} {hz:8.1f} Hz (need >= {min_hz:.0f}), {why}", file=out)
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="check that the ulog carries the signals M1/M3 need at sufficient rate")
    a.add_argument("ulog")
    args = ap.parse_args(argv)
    if args.cmd == "audit":
        ok = audit(args.ulog)
        if not ok:
            print("estimation NOT run: required signals missing or too slow (see i119_ident_iv.md)")
            return 2
        print("signals adequate; the estimation step from a log is not implemented (UNVERIFIED path)")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
