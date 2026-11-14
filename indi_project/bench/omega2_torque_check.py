#!/usr/bin/env python3
"""Compare the eRPM-measured torque (actuator_torque_measured) with INDI's actuator model.

The model torque is the allocated torque setpoint (vehicle_torque_setpoint) through the first-order actuator
model of the controller, tau dx/dt = u - x with tau = MC_INDI_ACT_TC, as in the INDI library. Both are in the
normalised torque units of vehicle_torque_setpoint. For each axis this prints, over the samples where the
measurement is valid, the delay of the measurement behind the model (cross-correlation of increments over a
span), the least-squares gain meas ~ k * model at that delay, and the RMS of their difference. A gain near 1
and a small delay mean the model and the measured actuator state agree (u = (omega / CA_R_W_MAX)^2).

Usage: omega2_torque_check.py LOG.ulg [--span-ms 40] [--max-lag-ms 40] [--json OUT.json]
"""
import argparse
import json

import numpy as np
from pyulog import ULog

AXES = ("roll", "pitch", "yaw")
DT = 0.001  # resampling grid [s]


def topic(u, name):
    d = u.get_dataset(name).data
    return d["timestamp"] / 1e6, d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("log")
    ap.add_argument("--span-ms", type=float, default=40.0)
    ap.add_argument("--max-lag-ms", type=float, default=40.0)
    ap.add_argument("--json")
    a = ap.parse_args()

    u = ULog(a.log)
    params = u.initial_parameters
    tau = float(params.get("MC_INDI_ACT_TC", 0.0))
    tm, m = topic(u, "actuator_torque_measured")
    ts, s = topic(u, "vehicle_torque_setpoint")
    _, ar = topic(u, "actuator_armed")
    t_arm = ar["timestamp"][ar["armed"] == 1] / 1e6
    t0, t1 = max(tm[0], ts[0], t_arm[0] if len(t_arm) else tm[0]), min(tm[-1], ts[-1])
    grid = np.arange(t0, t1, DT)
    valid = np.interp(grid, tm, m["valid"].astype(float)) > 0.999
    span, max_lag = int(round(a.span_ms * 1e-3 / DT)), int(round(a.max_lag_ms * 1e-3 / DT))
    out = {"log": a.log, "act_tc_s": tau, "valid_frac": float(valid.mean()), "axes": {}}
    print(f"{a.log}: {len(grid) * DT:.1f} s armed, measurement valid {valid.mean() * 100:.1f} %, ACT_TC {tau * 1e3:.2f} ms")

    for i, ax in enumerate(AXES):
        sp = np.interp(grid, ts, s[f"xyz[{i}]"])
        model = np.empty_like(sp)
        alpha = DT / (tau + DT) if tau > 0 else 1.0
        model[0] = sp[0]
        for k in range(1, len(sp)):  # zero-order-hold input, backward-Euler first order lag
            model[k] = model[k - 1] + alpha * (sp[k] - model[k - 1])
        meas = np.interp(grid, tm, m[f"torque[{i}]"])
        best = None
        for lag in range(-max_lag, max_lag + 1):  # meas[k] vs model[k - lag]
            lo, hi = max(span, span + lag), min(len(grid), len(grid) + lag)
            y = meas[lo:hi] - meas[lo - span:hi - span]
            x = model[lo - lag:hi - lag] - model[lo - lag - span:hi - lag - span]
            ok = valid[lo:hi] & valid[lo - span:hi - span]
            if ok.sum() < 100 or not np.any(x[ok]):
                continue
            c = np.corrcoef(x[ok], y[ok])[0, 1]
            if best is None or c > best[1]:
                best = (lag, c)
        if best is None:
            continue
        lag = best[0]
        lo, hi = max(0, lag), min(len(grid), len(grid) + lag)
        x, y, ok = model[lo - lag:hi - lag], meas[lo:hi], valid[lo:hi]
        k = float(np.dot(x[ok], y[ok]) / np.dot(x[ok], x[ok]))
        r = {"delay_ms": lag * DT * 1e3, "incr_corr": float(best[1]), "gain": k,
             "rms_diff": float(np.sqrt(np.mean((y[ok] - x[ok]) ** 2))), "rms_model": float(np.sqrt(np.mean(x[ok] ** 2)))}
        out["axes"][ax] = r
        print(f"{ax:5s} delay {r['delay_ms']:+5.0f} ms (incr. corr {r['incr_corr']:.3f}), gain {k:.3f}, "
              f"rms(meas - model) {r['rms_diff']:.4f} vs rms(model) {r['rms_model']:.4f}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
