#!/usr/bin/env python3
"""Trajectory-tracking diagnosis for a trajectory run (stage 8, session 55).

Rebuilds the analytic reference from run.json (same traj_phase/traj_pos as the runner, time base = ULog boot time)
and reports, over the cruise part of the path (|v_ref| > 1 m/s):
  - along-track (positive = ahead) and cross-track error against the analytic path at every local position sample,
  - the time shift tau of the vehicle along the path (positive = ahead) and the path-scale gain, by least squares
    p(t) - hold ~= g * ref(t + tau),
  - the staleness of the logged trajectory_setpoint against the analytic path (stream delay),
  - the along-track error per path-phase bin (12 bins of the lemniscate period),
  - for INDI POS runs, gain and lag of a_f against a_c and of a_c against a_ref (indi_pos_status).
Usage: s8_track_diag.py RUN_DIR [RUN_DIR ...]
"""
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_scenario import traj_phase, traj_pos  # noqa: E402


def ref_at(traj, t_s):
    """Analytic offset from the hold position and its velocity (central difference) at path times t_s (s)."""
    p = np.array([traj_pos(traj, traj_phase(traj, t)) for t in t_s])
    h = 1e-3
    pp = np.array([traj_pos(traj, traj_phase(traj, t + h)) for t in t_s])
    pm = np.array([traj_pos(traj, traj_phase(traj, t - h)) for t in t_s])
    return p, (pp - pm) / (2 * h)


def lag_gain(x, y, dt, max_lag_s=0.3):
    """Shift (s, positive = x ahead of y) and gain g minimising |x(t) - g y(t + shift)| over all axes."""
    best = None
    n = int(max_lag_s / dt)
    for k in range(-n, n + 1):
        if k >= 0:
            xs, ys = x[:len(x) - k], y[k:]
        else:
            xs, ys = x[-k:], y[:len(y) + k]
        g = float(np.sum(xs * ys) / np.sum(ys * ys))
        r = float(np.sqrt(np.mean((xs - g * ys) ** 2)))
        if best is None or r < best[2]:
            best = (k * dt, g, r)
    return best


def diag(run_dir):
    meta = json.load(open(os.path.join(run_dir, "run.json")))
    traj = meta["trajectory"]
    hold = np.array(meta["hold_pos_ned"])
    t0 = traj["t0_us"] * 1e-6
    u = ULog(os.path.join(run_dir, "flight.ulg"),
             ["vehicle_local_position", "trajectory_setpoint", "indi_pos_status"])
    d = {x.name: x.data for x in u.data_list}
    lp = d["vehicle_local_position"]
    t = lp["timestamp"] * 1e-6
    sel = (t >= t0) & (t <= t0 + traj["dur_s"])
    t = t[sel]
    p = np.column_stack([lp[k][sel] for k in ("x", "y", "z")]) - hold
    r, v = ref_at(traj, t - t0)
    cruise = np.linalg.norm(v[:, :2], axis=1) > 1.0
    e = p - r
    vh = v[:, :2] / np.linalg.norm(v[:, :2], axis=1, keepdims=True).clip(1e-6)
    along = np.sum(e[:, :2] * vh, axis=1)
    cross = vh[:, 0] * e[:, 1] - vh[:, 1] * e[:, 0]
    out = [f"## {run_dir}", "",
           f"cruise samples {cruise.sum()}: along mean {along[cruise].mean():+.3f} m, along rms "
           f"{np.sqrt(np.mean(along[cruise] ** 2)):.3f} m, cross mean {cross[cruise].mean():+.3f} m, cross rms "
           f"{np.sqrt(np.mean(cross[cruise] ** 2)):.3f} m, mean |v_ref| {np.linalg.norm(v[cruise, :2], axis=1).mean():.2f} m/s"]

    # uniform resampling for lag/gain fits
    dt = 0.01
    tu = np.arange(t[0], t[-1], dt)
    pu = np.column_stack([np.interp(tu, t, p[:, i]) for i in range(2)])
    ru, vu = ref_at(traj, tu - t0)
    cu = np.linalg.norm(vu[:, :2], axis=1) > 1.0
    tau, g, res = lag_gain(pu[cu].ravel(), ru[cu, :2].ravel(), dt) if False else (None, None, None)
    # per-axis fit over the cruise window (contiguous span between first and last cruise sample)
    i0, i1 = np.argmax(cu), len(cu) - np.argmax(cu[::-1])
    for ax, name in ((0, "x"), (1, "y")):
        tau, g, res = lag_gain(pu[i0:i1, ax], ru[i0:i1, ax], dt)
        out.append(f"pos {name}: vehicle shift {tau * 1e3:+.0f} ms (positive = ahead), gain {g:.3f}, residual rms {res:.3f} m")

    # logged setpoint staleness against the analytic path
    ts = d["trajectory_setpoint"]
    tst = ts["timestamp"] * 1e-6
    ss = (tst >= t0 + traj["ramp_s"]) & (tst <= t0 + traj["dur_s"] - traj["ramp_s"])
    sp = np.column_stack([ts[f"position[{i}]"][ss] for i in range(2)]) - hold[:2]
    best = None
    for lag in np.arange(-0.2, 0.2001, 0.002):
        rr, _ = ref_at(traj, tst[ss] - t0 - lag)
        err = float(np.sqrt(np.mean((sp - rr[:, :2]) ** 2)))
        if best is None or err < best[1]:
            best = (lag, err)
    out.append(f"logged trajectory_setpoint (n {ss.sum()}) = analytic path delayed by {best[0] * 1e3:+.0f} ms "
               f"(residual {best[1]:.4f} m)")

    # along-track error per path-phase bin (phase mod pi/... : one lemniscate period is 2 pi of phi)
    phi = np.array([traj_phase(traj, x) for x in t - t0]) % (2 * math.pi)
    bins = np.linspace(0, 2 * math.pi, 13)
    row = []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        m = cruise & (phi >= b0) & (phi < b1)
        row.append(f"{along[m].mean():+.2f}" if m.any() else "  -  ")
    out.append("along mean per phase bin (30 deg each, from phi 0): " + " ".join(row))

    if "indi_pos_status" in d:
        s = d["indi_pos_status"]
        tsi = s["timestamp"] * 1e-6
        m = (tsi >= t0 + traj["ramp_s"]) & (tsi <= t0 + traj["dur_s"] - traj["ramp_s"])
        tu2 = np.arange(tsi[m][0], tsi[m][-1], dt)
        ac = np.column_stack([np.interp(tu2, tsi[m], s[f"a_c[{i}]"][m]) for i in range(2)])
        af = np.column_stack([np.interp(tu2, tsi[m], s[f"a_f[{i}]"][m]) for i in range(2)])
        h = 1e-3
        aref = np.array([[(traj_pos(traj, traj_phase(traj, x + h))[i] - 2 * traj_pos(traj, traj_phase(traj, x))[i]
                           + traj_pos(traj, traj_phase(traj, x - h))[i]) / h ** 2 for i in range(2)]
                         for x in tu2 - t0])
        for ax, name in ((0, "x"), (1, "y")):
            tau, g, res = lag_gain(af[:, ax], ac[:, ax], dt)
            tau2, g2, res2 = lag_gain(ac[:, ax], aref[:, ax], dt)
            out.append(f"accel {name}: a_f vs a_c shift {tau * 1e3:+.0f} ms gain {g:.3f} res {res:.2f}; "
                       f"a_c vs analytic a_ref shift {tau2 * 1e3:+.0f} ms gain {g2:.3f} res {res2:.2f} m/s^2")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    for rd in sys.argv[1:]:
        print(diag(rd))
