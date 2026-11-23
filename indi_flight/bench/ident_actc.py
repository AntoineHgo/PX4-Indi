#!/usr/bin/env python3
"""Motor time-constant identification (ACT_TC) by output error, one ulg or arrays.

Per motor: y = (rpm / rpm_max)^2 against the command u = actuator_motors.control[i].
Model: x = asymmetric first-order lag of u delayed by d samples, d fractional (linear interpolation of the command) (tau_up while the delayed command is above x,
tau_down otherwise, exact discretisation alpha = 1 - exp(-dt/tau)); y_hat = a + b x, (a, b) by linear least squares
given x. (d, tau_up, tau_down) by a vectorised integer-d grid search, then a local pattern-search refinement
(d continuous, step halved down to ~0.01 sample) (no scipy needed).
A symmetric fit (tau_up = tau_down) is reported as tau_sym.

Alignment: both signals go onto one uniform grid of the median esc_status period. Each grid point takes the latest
sample at or before it, but only if that sample is younger than 1.5 periods; older points are invalid (NaN), never
held across a gap. Invalid or saturated (command <= 0.01 or >= 0.99) samples, and the LAG_WINDOW_S after them and
after the start of the window, are excluded from the residual; the model state is carried through them by holding
the last valid command.

Usage: ident_actc.py LOG.ulg [--t0 S --t1 S] [--rpm-max RPM] [--json OUT.json]   (times: seconds since log start)
Exit status 0 if the median identification passes the fit-quality check, 1 otherwise."""
import argparse
import json
import sys

import numpy as np

# fit-quality thresholds, chosen from the synthetic self-test (bench/tests/SELFTEST_IDENT_ACTC_S208.md)
MAX_NORM_RESIDUAL = 0.35   # rms(residual) / std(y_hat): noise and model error relative to the excited signal
MAX_STRUCTURE = 0.08       # largest residual autocorrelation magnitude at 25..125 ms lags
MIN_NORM_FOR_STRUCTURE = 0.05  # below this the residual is numerical noise and its shape means nothing
MAX_REL_SE_TAU = 0.10      # 1-sigma relative standard error of tau_up and tau_down from the curvature at the minimum
MAX_SE_DELAY_SAMPLES = 1.5  # 1-sigma standard error of the delay
MIN_CMD_STD = 0.004        # command excitation (std of u over the valid samples)
SAT_LO, SAT_HI = 0.01, 0.99
LAG_WINDOW_S = 0.25
D_MAX_S = 0.020
TAU_MIN_S, TAU_MAX_S = 0.005, 0.200
RPM_MAX_PARAMS = ("SIM_GZ_RPM_MAX", "MC_INDI_RPM_MAX", "ESC_RPM_MAX")


def align(t_cmd, cmd, t_rpm, rpm, t0, t1):
    """Uniform grid at the median rpm period; latest-sample-at-or-before with an age limit. Returns t, u, rpm, dt."""
    t_cmd, t_rpm = np.asarray(t_cmd, float), np.asarray(t_rpm, float)
    dt = float(np.median(np.diff(t_rpm)))
    g = np.arange(max(t0, t_rpm[0], t_cmd[0]), min(t1, t_rpm[-1], t_cmd[-1]), dt)

    def latest(t, v):
        tol = 0.01 * dt                      # a sample stamped a rounding error late still counts as "at"
        i = np.clip(np.searchsorted(t, g + tol, side="right") - 1, 0, len(t) - 1)
        out = np.asarray(v, float)[i].copy()
        out[g - t[i] > 1.5 * dt] = np.nan
        return out

    return g, latest(t_cmd, cmd), latest(t_rpm, rpm), dt


def _x0(u, dt):
    """Initial lag state: the mean command over the excluded start-up window (the rotor starts near it)."""
    return float(np.mean(u[: max(int(round(LAG_WINDOW_S / dt)), 1)]))


def _stats(u, y, valid, d, tu, td, dt):
    """Sufficient statistics of the LS fit y ~ a + b x for a batch of (d, tau_up, tau_down); returns SSE, a, b."""
    d, tu, td = (np.atleast_1d(np.asarray(v, float)) for v in (d, tu, td))
    di = np.floor(d).astype(int)            # fractional delay: linear interpolation between u[k-di] and u[k-di-1]
    fr = d - di
    au, ad = 1 - np.exp(-dt / tu), 1 - np.exp(-dt / td)
    n = len(u)
    pad = int(di.max()) + 1
    up = np.concatenate([np.full(pad, u[0]), u])
    x = np.full(len(d), _x0(u, dt))
    s1 = sx = sxx = sxy = 0.0
    for k in range(n):
        i0 = pad + k - di
        ud = (1 - fr) * up[i0] + fr * up[i0 - 1]
        x = x + np.where(ud > x, au, ad) * (ud - x)
        if valid[k]:
            s1 += 1.0
            sx = sx + x
            sxx = sxx + x * x
            sxy = sxy + x * y[k]
    sy, syy = y[valid].sum(), (y[valid] ** 2).sum()
    det = s1 * sxx - sx * sx
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    b = (s1 * sxy - sx * sy) / det
    a = (sy - b * sx) / s1
    sse = syy - a * sy - b * sxy
    return np.maximum(sse, 0.0), a, b


def _residual(u, y, valid, d, tu, td, dt, a, b):
    """Residual y - (a + b x) at the fitted parameters, valid samples only, in time order."""
    au, ad = 1 - np.exp(-dt / tu), 1 - np.exp(-dt / td)
    di = int(np.floor(d))
    fr = d - di
    x, xs = _x0(u, dt), np.empty(len(u))
    for k in range(len(u)):
        k0 = k - di
        ud = u[0] if k0 < 0 else (u[k0] if k0 == 0 else (1 - fr) * u[k0] + fr * u[k0 - 1])
        x += (au if ud > x else ad) * (ud - x)
        xs[k] = x
    return (y - (a + b * xs))[valid]


def structure(res, dt):
    """Largest |autocorrelation| of the residual at 25..125 ms lags. White measurement noise gives ~0; a model
    mismatch (delay, tau, missing dynamics) leaves slow structure. Short lags are skipped on purpose: telemetry
    holds and quantisation correlate the noise there."""
    r = res - res.mean()
    den = float(r @ r)
    lags = [int(round(l / dt)) for l in np.arange(0.025, 0.1251, 0.025)]
    return max(abs(float(r[:-l] @ r[l:])) / den for l in lags) if den > 0 else 1.0


def _refine(u, y, valid, dt, d0, tu0, td0, sym, force_d, ratio=1.25):
    """Pattern search on (ln tu, ln td, d) with d a continuous number of samples (linear interpolation of the
    delayed command); each iteration evaluates the 27 neighbours in one batch. d steps 1 sample, halved with tau's."""
    d, ltu, ltd, step = float(d0), np.log(tu0), np.log(td0), np.log(ratio)
    dstep = 1.0
    dmax = D_MAX_S / dt
    ds = [0] if force_d is not None else [-1, 0, 1]
    for _ in range(60):
        offs = [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in ds if not (sym and i != j)]
        dd = np.array([min(max(d + k * dstep, 0.0), dmax) for _, _, k in offs])
        lu = np.array([ltu + i * step for i, _, _ in offs])
        ld = np.array([ltd + j * step for _, j, _ in offs])
        lu, ld = np.clip(lu, np.log(TAU_MIN_S / 2), np.log(TAU_MAX_S * 2)), np.clip(ld, np.log(TAU_MIN_S / 2), np.log(TAU_MAX_S * 2))
        sse = _stats(u, y, valid, dd, np.exp(lu), np.exp(ld), dt)[0]
        m = int(np.argmin(sse))
        if sse[m] >= sse[offs.index((0, 0, 0))]:     # centre wins ties (clipped neighbours repeat it)
            step *= 0.5
            dstep *= 0.5
            if step < 0.002:
                break
        else:
            d, ltu, ltd = float(dd[m]), float(lu[m]), float(ld[m])
    return d, float(np.exp(ltu)), float(np.exp(ltd))


def _grid(u, y, valid, dt, sym, force_d):
    dmax = int(round(D_MAX_S / dt))
    ds = np.array([force_d] if force_d is not None else np.arange(0, dmax + 1, max(1, dmax // 8)))
    taus = np.geomspace(TAU_MIN_S, TAU_MAX_S, 14)
    if sym:
        D, T = np.meshgrid(ds, taus, indexing="ij")
        D, TU, TD = D.ravel(), T.ravel(), T.ravel()
    else:
        D, TU, TD = (m.ravel() for m in np.meshgrid(ds, taus, taus, indexing="ij"))
    sse = _stats(u, y, valid, D, TU, TD, dt)[0]
    m = int(np.argmin(sse))
    return float(D[m]), float(TU[m]), float(TD[m])


def _fit(u, y, valid, dt, sym, force_d):
    d, tu, td = _grid(u, y, valid, dt, sym, force_d)
    d, tu, td = _refine(u, y, valid, dt, d, tu, td, sym, force_d)
    sse, a, b = (float(v[0]) for v in _stats(u, y, valid, d, tu, td, dt))
    return d, tu, td, sse, a, b


def _curvature(u, y, valid, dt, d, tu, td, sse, force_d, h=0.1):
    """Standard errors (ln tau_up, ln tau_down, d in samples) from the finite-difference Hessian of SSE / sigma^2."""
    n = int(valid.sum())
    sig2 = max(sse / max(n - 4, 1), 1e-300)
    free = [0, 1] if force_d is not None else [0, 1, 2]
    steps = np.array([h, h, 1.0])
    dmax = D_MAX_S / dt

    def pts(dl):
        th = np.array([np.log(tu), np.log(td), float(d)]) + dl
        return min(max(th[2], 0.0), dmax), np.exp(th[0]), np.exp(th[1])

    offs, keys = [np.zeros(3)], [("c",)]
    for i in free:
        for s in (-1, 1):
            e = np.zeros(3); e[i] = s * steps[i]; offs.append(e); keys.append((i, s))
        for j in free:
            if j > i:
                for si in (-1, 1):
                    for sj in (-1, 1):
                        e = np.zeros(3); e[i] = si * steps[i]; e[j] = sj * steps[j]; offs.append(e); keys.append((i, j, si, sj))
    P = [pts(o) for o in offs]
    f = _stats(u, y, valid, [p[0] for p in P], [p[1] for p in P], [p[2] for p in P], dt)[0] / sig2
    F = dict(zip(keys, f))
    k = len(free)
    H = np.zeros((k, k))
    for ii, i in enumerate(free):
        H[ii, ii] = (F[(i, 1)] + F[(i, -1)] - 2 * F[("c",)]) / steps[i] ** 2
        for jj, j in enumerate(free):
            if j > i:
                H[ii, jj] = H[jj, ii] = (F[(i, j, 1, 1)] - F[(i, j, 1, -1)] - F[(i, j, -1, 1)] + F[(i, j, -1, -1)]) / (4 * steps[i] * steps[j])
    try:
        w = np.linalg.eigvalsh(H)
        if w.min() <= 0:
            return None
        cov = 2 * np.linalg.inv(H)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        return None
    out = np.array([np.inf, np.inf, 0.0])
    out[free] = se
    return out


def identify_motor(t, u, rpm, rpm_max, dt, force_delay=None):
    """Fit one motor on aligned data (NaN = invalid). force_delay in samples fixes d (for the mismatch check)."""
    y = (np.asarray(rpm, float) / rpm_max) ** 2
    u = np.asarray(u, float)
    bad = np.isnan(u) | np.isnan(y) | (u <= SAT_LO) | (u >= SAT_HI)
    w = max(int(round(LAG_WINDOW_S / dt)), 1)
    excl = np.convolve(bad.astype(float), np.ones(w), mode="full")[: len(bad)] > 0   # sample and the lag window after it
    excl[:w] = True
    valid = ~excl
    uh = u.copy()                      # hold the last valid command through invalid samples
    for k in range(len(uh)):
        if np.isnan(uh[k]):
            uh[k] = uh[k - 1] if k else 0.0
    yh = np.where(np.isnan(y), 0.0, y)
    res = dict(n_valid=int(valid.sum()), n=len(u), excluded_frac=float(1 - valid.mean()), pass_=False, flags=[])
    if valid.sum() < 10 * w or np.std(uh[valid]) < MIN_CMD_STD:
        res["flags"].append("unexcited_or_too_few_samples")
        return res
    d, tu, td, sse, a, b = _fit(uh, yh, valid, dt, False, force_delay)
    _, tsym, _, _, _, _ = _fit(uh, yh, valid, dt, True, None)
    n = int(valid.sum())
    rms = float(np.sqrt(sse / n))
    # std of the modelled signal over the valid samples
    dsig = np.sqrt(max((y[valid] - y[valid].mean()).var() - rms ** 2, 0.0))
    norm = rms / dsig if dsig > 0 else np.inf
    st = structure(_residual(uh, yh, valid, d, tu, td, dt, a, b), dt)
    se = _curvature(uh, yh, valid, dt, d, tu, td, sse, force_delay)
    flags = []
    if not norm <= MAX_NORM_RESIDUAL:
        flags.append("residual_high")
    if norm > MIN_NORM_FOR_STRUCTURE and not st <= MAX_STRUCTURE:
        flags.append("residual_structured")
    if se is None:
        flags.append("curvature_not_positive_definite")
    else:
        if max(se[0], se[1]) > MAX_REL_SE_TAU:
            flags.append("tau_poorly_identified")
        if se[2] > MAX_SE_DELAY_SAMPLES:
            flags.append("delay_poorly_identified")
    dmax = D_MAX_S / dt
    if force_delay is None and d >= dmax - 1e-9:
        flags.append("delay_at_grid_edge")
    if any(np.isclose(v, b, rtol=1e-6) for v in (tu, td) for b in (TAU_MIN_S / 2, TAU_MAX_S * 2)):
        flags.append("tau_at_bound")
    res.update(tau_up=tu, tau_down=td, tau_sym=tsym, delay_samples=d, delay_ms=1e3 * d * dt, gain=b, intercept=a,
               residual=norm, residual_rms=rms, structure=st, se_ln_tau_up=None if se is None else float(se[0]),
               se_ln_tau_down=None if se is None else float(se[1]), se_delay_samples=None if se is None else float(se[2]),
               flags=flags, pass_=not flags)
    return res


def identify(t_cmd, cmd, t_rpm, rpm, rpm_max, t0=-np.inf, t1=np.inf, force_delay=None):
    """cmd, rpm: (N, M) arrays on their own time bases. Returns dict with per-motor results and the median."""
    motors = []
    for i in range(np.asarray(cmd).shape[1]):
        t, u, r, dt = align(t_cmd, cmd[:, i], t_rpm, np.abs(rpm[:, i]), t0, t1)
        motors.append(identify_motor(t, u, r, rpm_max, dt, force_delay))
    ok = [m for m in motors if "tau_up" in m]
    med = {k: float(np.median([m[k] for m in ok])) for k in ("tau_up", "tau_down", "tau_sym", "delay_ms", "gain", "intercept", "residual")} if ok else {}
    med["pass"] = bool(ok) and all(m["pass_"] for m in motors)
    return dict(motors=motors, median=med, rpm_max=rpm_max)


def load_ulg(path, rpm_max=None, esc_instance=0):
    from pyulog import ULog
    u = ULog(path, ["esc_status", "actuator_motors"])
    ts0 = u.start_timestamp
    if rpm_max is None:
        for p in RPM_MAX_PARAMS:
            if p in u.initial_parameters:
                rpm_max = float(u.initial_parameters[p])
                break
    esc = u.get_dataset("esc_status", esc_instance).data
    am = u.get_dataset("actuator_motors").data
    # same field for both topics: EscStatus has only `timestamp`, so ActuatorMotors uses `timestamp` too
    ke = kc = "timestamp"
    n = sum(1 for k in am if k.startswith("control[") and k[8:-1].isdigit())
    n = min(n, 4)
    cmd = np.stack([am[f"control[{i}]"] for i in range(n)], 1).astype(float)
    rpm = np.stack([esc[f"esc[{i}].esc_rpm"] for i in range(n)], 1).astype(float)
    return ((am[kc].astype(np.int64) - ts0) * 1e-6, cmd, (esc[ke].astype(np.int64) - ts0) * 1e-6, rpm, rpm_max)


def table_line(r):
    m = r["median"]
    if "tau_up" not in m:
        return "ACTC FAIL no motor identified"
    flags = sorted({f for x in r["motors"] for f in x["flags"]})
    return (f"ACTC {'PASS' if m['pass'] else 'FAIL'}  tau_up {1e3*m['tau_up']:.1f} ms  tau_down {1e3*m['tau_down']:.1f} ms  "
            f"tau_sym {1e3*m['tau_sym']:.1f} ms  delay {m['delay_ms']:.2f} ms  gain {m['gain']:.3f}  resid {m['residual']:.3f}"
            + (f"  flags {','.join(flags)}" if flags else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulg")
    ap.add_argument("--t0", type=float, default=-np.inf, help="window start, log seconds")
    ap.add_argument("--t1", type=float, default=np.inf)
    ap.add_argument("--rpm-max", type=float, default=None, help="rotor speed in rpm (the unit of esc_status esc_rpm) for y = (rpm/rpm_max)^2; default from log params")
    ap.add_argument("--esc-instance", type=int, default=0, help="esc_status multi_id; 0 = telemetry (SITL: simulated DShot telemetry), highest = simulator truth")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    tc, cmd, tr, rpm, rpm_max = load_ulg(a.ulg, a.rpm_max, a.esc_instance)
    if rpm_max is None:
        ap.error("--rpm-max is required: no rpm_max parameter in the log (%s)" % ", ".join(RPM_MAX_PARAMS))
    r = identify(tc, cmd, tr, rpm, rpm_max, a.t0, a.t1)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(r, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(table_line(r))
    return 0 if r["median"].get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
