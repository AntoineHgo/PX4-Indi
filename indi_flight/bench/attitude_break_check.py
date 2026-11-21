#!/usr/bin/env python3
"""Offline validity checks of one attitude-loop break flight (MC_INDI_INJ_PT = 1, design note attitude_break_s86.md
section 8, MAJOR 2 of the T185 review). Reads indi_rate_status of a ulog, prints PASS/FAIL with the numbers.

The check that the INDI law really received x = y + d does not use the module's own x - y - d bookkeeping (circular,
printed only as a consistency line). It uses two quantities that depend on what _indi.update() got:
  1. rate_sp_dot (logged by the law) equals the filtered, clamped derivative of the logged x, one step ahead:
       pred[k] = clip(r[k-1] + a ((x[k] - x[k-1]) / dt - r[k-1])), a = dt / (Tc + dt), Tc = kSetpointLeadTc = 0.03 s,
       clip = kMaxRateSpDot = 1000 rad/s^2 (src/lib/indi_rate_control/indi_rate_control.hpp:279,283, .cpp:399-404).
     Roll and pitch only: yaw differentiates the setpoint after the yaw error LPF (MC_INDI_YAW_CUT), not reproduced here,
     the yaw axis reports SKIP for this check.
  2. torque_sp_pre_inject (c) has more power at the excited bins f = k/Tp than at the unexcited integer bins in the
     same band (c responds to x). A law that never saw d shows no such line structure.
Usage: attitude_break_check.py <flight.ulg> <axis 0|1|2> [--Tp S --fmin HZ --fmax HZ]   exit 0 = all PASS
"""
import argparse
import sys

import numpy as np

K_TC = 0.03          # IndiRateControl::kSetpointLeadTc (0.01 before d65111154b)
K_MAX_DOT = 1000.0   # IndiRateControl::kMaxRateSpDot


def load(ulg, axis):
    from pyulog import ULog
    s = [d for d in ULog(ulg, ["indi_rate_status"]).data_list if d.name == "indi_rate_status"][0].data
    g = lambda n: np.asarray(s[n], float)  # noqa: E731
    return dict(t_us=np.asarray(s["timestamp_sample"], np.int64), d=g(f"rates_sp_inject[{axis}]"),
                x=g(f"rates_sp_applied[{axis}]"), y=g(f"rates_sp_pre_inject[{axis}]"),
                rdot=g(f"rate_sp_dot[{axis}]"), c=g(f"torque_sp_pre_inject[{axis}]"),
                fault=np.asarray(s["fault"], bool), stale=np.asarray(s["rate_sp_stale"], bool))


def predict_rate_sp_dot(t_us, x, rdot):
    """One step prediction of rate_sp_dot[k] from rate_sp_dot[k-1] and the logged x (k = 1..n-1)."""
    dt = np.diff(t_us) * 1e-6
    a = dt / (K_TC + dt)
    raw = np.diff(x) / dt
    return np.clip(rdot[:-1] + a * (raw - rdot[:-1]), -K_MAX_DOT, K_MAX_DOT)


def check_lead(S, axis, tol_rel=0.02):
    w = S["w"]
    if axis == 2:
        return "SKIP", "yaw: the law differentiates the yaw-LPF'd setpoint, not reproduced here"
    k = np.flatnonzero(w)[1:]                          # cycles inside the window with a predecessor
    pred = predict_rate_sp_dot(S["t_us"], S["x"], S["rdot"])[k - 1]
    err = S["rdot"][k] - pred
    rms_sig = float(np.sqrt(np.mean(S["rdot"][k] ** 2)))
    rms_err = float(np.sqrt(np.mean(err ** 2)))
    # what the law would show had it been fed y: same prediction from y
    pred_y = predict_rate_sp_dot(S["t_us"], S["y"], S["rdot"])[k - 1]
    rms_err_y = float(np.sqrt(np.mean((S["rdot"][k] - pred_y) ** 2)))
    ok = rms_sig > 0 and rms_err <= tol_rel * rms_sig
    return ("PASS" if ok else "FAIL"), (f"rms rate_sp_dot {rms_sig:.3f} rad/s^2, one-step error vs filtered d/dt of x "
                                        f"{rms_err:.4f} ({rms_err / max(rms_sig, 1e-12):.4f} of signal, limit {tol_rel}); "
                                        f"same error if the law had been fed y {rms_err_y:.4f}")


def bin_power(t, v, f_list):
    v = v - np.mean(v)
    return np.array([abs(np.sum(v * np.exp(-2j * np.pi * f * t))) ** 2 for f in f_list])


def check_response(S, Tp, fmin, fmax, ratio_min=4.0):
    w = np.flatnonzero(S["w"])
    t = S["t_us"][w] * 1e-6
    n_per = int(np.floor((t[-1] - t[0]) / Tp))
    if n_per < 1:
        return "FAIL", "window shorter than one period"
    keep = (t - t[0]) < n_per * Tp
    t, d, c = t[keep] - t[0], S["d"][w][keep], S["c"][w][keep]
    ks = np.arange(int(np.ceil(fmin * Tp)), int(np.floor(fmax * Tp)) + 1)
    f = ks / Tp
    pd = bin_power(t, d, f)
    exc = pd > 1e-3 * pd.max()
    if exc.sum() < 3 or (~exc).sum() < 3:
        return "FAIL", f"{exc.sum()} excited / {(~exc).sum()} unexcited bins in band, cannot compare"
    pc = bin_power(t, c, f)
    r = float(np.median(pc[exc]) / max(np.median(pc[~exc]), 1e-300))
    return ("PASS" if r >= ratio_min else "FAIL"), (f"median power of c at {exc.sum()} excited bins over {(~exc).sum()} "
                                                   f"unexcited bins {r:.1f} (limit {ratio_min}), {n_per} periods")


def analyse(S, axis, Tp, fmin, fmax):
    S = dict(S)
    S["w"] = S["d"] != 0.0
    out = []
    if not S["w"].any():
        return [("window", "FAIL", "no cycle with d != 0")]
    w = S["w"]
    out.append(("window", "PASS", f"{int(w.sum())} cycles with d != 0, fault in window {int(S['fault'][w].sum())}, "
                                  f"stale in window {int(S['stale'][w].sum())}"))
    if S["fault"][w].any() or S["stale"][w].any():
        out[-1] = ("window", "FAIL", out[-1][2])
    res = float(np.max(np.abs(S["x"] - S["y"] - S["d"])))
    out.append(("consistency x-y-d (circular, informative)", "PASS" if res <= 1e-6 else "FAIL", f"max {res:.2e}"))
    out.append(("law fed x: rate_sp_dot", *check_lead(S, axis)))
    out.append(("law fed x: c responds at excited bins", *check_response(S, Tp, fmin, fmax)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ulg")
    ap.add_argument("axis", type=int, choices=[0, 1, 2])
    ap.add_argument("--Tp", type=float, default=10.0)
    ap.add_argument("--fmin", type=float, default=0.2)
    ap.add_argument("--fmax", type=float, default=20.0)
    a = ap.parse_args(argv)
    rows = analyse(load(a.ulg, a.axis), a.axis, a.Tp, a.fmin, a.fmax)
    for name, verdict, text in rows:
        print(f"{verdict:5s} {name}: {text}")
    bad = [r for r in rows if r[1] == "FAIL"]
    print("RESULT", "FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
