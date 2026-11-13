#!/usr/bin/env python3
"""Check INDI filter synchronisation from indi_rate_status in a ULog.

With synchronised filters and a correct effectiveness, the filtered
measured angular acceleration a_f and the filtered modelled actuator torque
t_f satisfy a_f ~= G1 * t_f + d_f, with d_f a slow disturbance term
(plan/architecture.md sec. 5). On sample-to-sample increments the offset
cancels: da_f[k] ~= G1 * dt_f[k - lag]. If the two filter chains and the
actuator model are in step, the best-fitting lag is 0 (or one controller
cycle, from the order of measurement and command within a cycle); a larger
lag means t_f leads a_f and the controller acts on stale cancellation.

Increments are taken over a span of n samples. With n = 1 the gyro noise in
a_f dominates and, through the feedback, biases G1 towards zero; a span of
about 40 ms (n = 10 at 250 Hz) keeps the step transients and averages the
noise. Only axes excited by the scenario give a meaningful G1 (check R^2).

For each axis and each lag in [-L, L] samples this prints the least-squares
G1 and the R^2 of the increment fit, and the lag maximising R^2. It also
reports the lag between nu and a_f (closed-loop acceleration tracking).

Usage: check_sync.py LOG.ulg [--span 10] [--max-lag 15] [--json OUT.json]
"""
import argparse
import json

import numpy as np
from pyulog import ULog

AXES = ("roll", "pitch", "yaw")


def load(path):
    ulog = ULog(path, ["indi_rate_status"])
    d = ulog.get_dataset("indi_rate_status").data
    t = d["timestamp"] * 1e-6
    sig = {}
    for name in ("nu", "angular_accel_filtered", "torque_filtered"):
        sig[name] = np.column_stack([d[f"{name}[{i}]"] for i in range(3)])
    sig["fault"] = d["fault"].astype(bool)
    return t, sig


def lag_fit(y, x, lag):
    """Fit y[k] = g * x[k - lag] by least squares; return (g, R^2)."""
    if lag > 0:
        y, x = y[lag:], x[:-lag]
    elif lag < 0:
        y, x = y[:lag], x[-lag:]
    sxx = float(np.dot(x, x))
    syy = float(np.dot(y, y))
    if sxx <= 0.0 or syy <= 0.0:
        return float("nan"), float("nan")
    g = float(np.dot(x, y)) / sxx
    r2 = 1.0 - float(np.dot(y - g * x, y - g * x)) / syy
    return g, r2


def scan(y, x, max_lag):
    rows = [(lag,) + lag_fit(y, x, lag) for lag in range(-max_lag, max_lag + 1)]
    best = max(rows, key=lambda r: -np.inf if np.isnan(r[2]) else r[2])
    return rows, best


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("log")
    ap.add_argument("--span", type=int, default=10, help="increment span in samples")
    ap.add_argument("--max-lag", type=int, default=15)
    ap.add_argument("--json")
    args = ap.parse_args()

    t, sig = load(args.log)
    ok = ~sig["fault"]
    dts = np.diff(t)
    print(f"{args.log}: {len(t)} samples, median dt {np.median(dts) * 1e3:.2f} ms, "
          f"faults {int((~ok).sum())}")

    n = args.span
    out = {"log": args.log, "span": n, "samples": int(len(t)), "median_dt_s": float(np.median(dts)), "axes": {}}
    for i, axis in enumerate(AXES):
        a = sig["angular_accel_filtered"][ok, i]
        tf = sig["torque_filtered"][ok, i]
        nu = sig["nu"][ok, i]
        da = a[n:] - a[:-n]
        rows, best = scan(da, tf[n:] - tf[:-n], args.max_lag)
        g0 = next(r for r in rows if r[0] == 0)
        _, best_nu = scan(da, nu[n:] - nu[:-n], args.max_lag)
        print(f"{axis:5s} a_f vs t_f: best lag {best[0]:+d} (G1 {best[1]:.1f}, R2 {best[2]:.3f}); "
              f"lag 0: G1 {g0[1]:.1f}, R2 {g0[2]:.3f} | a_f vs nu: best lag {best_nu[0]:+d} "
              f"(R2 {best_nu[2]:.3f})")
        out["axes"][axis] = {
            "torque_lag_scan": [{"lag": r[0], "g1": r[1], "r2": r[2]} for r in rows],
            "best_torque_lag": best[0], "g1_at_best": best[1], "r2_at_best": best[2],
            "best_nu_lag": best_nu[0], "r2_nu_at_best": best_nu[2],
        }

    if args.json:
        with open(args.json, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
