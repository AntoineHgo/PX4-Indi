#!/usr/bin/env python3
"""Time-base and origin check for the analytic trajectory metric (port 1a). Read-only.

Usage: python3 indi_flight/bench/timebase_check.py RUN_DIR [RUN_DIR ...]
RUN_DIR holds flight.ulg and run.json. The reference is hold_pos_ned + traj(t - (t0_us + lag)).
Positive lag = reference delayed. Origin offset = median(truth - estimate) in NED, cm, with the
estimate linearly interpolated onto the truth timestamps.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M  # noqa: E402
from pyulog import ULog  # noqa: E402

LAGS_MS = np.arange(-100, 101, 2)
AX = ("x", "y", "z")
LAG0 = int(np.where(LAGS_MS == 0)[0][0])


def pos_of(d, m):
    return np.column_stack([d[k][m] for k in AX])


def scan(t, pos, traj, t0, hold):
    return np.array([M.trajectory_error_analytic(t, pos, traj, t0 + int(lag) * 1000, hold)["rms_3d_m"]
                     for lag in LAGS_MS])


def fmt3(v):
    return " ".join(f"{x:+6.1f}" for x in v)


def check(d):
    run = json.load(open(os.path.join(d, "run.json")))
    ulog = ULog(os.path.join(d, "flight.ulg"))
    traj, hold, t0 = run["trajectory"], run["hold_pos_ned"], int(run["trajectory"]["t0_us"])
    w0, w1 = run["t_window_start_us"], run["t_window_end_us"]
    ob = M.offboard_span(ulog)
    if ob is not None:
        w0, w1 = max(w0, ob[0]), min(w1, ob[1])
    gt, lp = M.topic(ulog, "vehicle_local_position_groundtruth"), M.topic(ulog, "vehicle_local_position")
    if gt is None or lp is None:
        raise SystemExit(f"{d}: missing groundtruth or estimate topic")

    res = {}
    for name, src in (("truth", gt), ("est", lp)):
        m = (src["timestamp"] >= w0) & (src["timestamp"] <= w1)
        t, pos = src["timestamp"][m], pos_of(src, m)
        rms = scan(t, pos, traj, t0, hold)
        i = int(np.argmin(rms))
        res[name] = dict(lag=int(LAGS_MS[i]), rms0=rms[LAG0], rmin=rms[i], edge=i in (0, len(rms) - 1))
        if name == "truth":
            tt, pt = t, pos
    # trajectory_setpoint samples are point comparisons (no ZOH): control lag is not in them, so this isolates the time base
    sp = M.topic(ulog, "trajectory_setpoint")
    if sp is not None:
        spos = np.column_stack([sp[f"position[{i}]"] for i in range(3)])
        m = (sp["timestamp"] >= w0) & (sp["timestamp"] <= w1) & np.all(np.isfinite(spos), axis=1)
        rms = scan(sp["timestamp"][m], spos[m], traj, t0, hold)
        i = int(np.argmin(rms))
        res["sp"] = dict(lag=int(LAGS_MS[i]), rms0=rms[LAG0], rmin=rms[i], n=int(m.sum()))
    # origin offset, truth - estimate (estimate interpolated onto truth times inside its own time range)
    ok = (tt >= lp["timestamp"][0]) & (tt <= lp["timestamp"][-1])
    tt, pt = tt[ok], pt[ok]
    est_at = np.column_stack([np.interp(tt, lp["timestamp"], lp[k]) for k in AX])
    diff = (pt - est_at) * 100.0  # cm
    pre = tt <= t0
    off_pre = np.median(diff[pre], axis=0) if pre.any() else np.full(3, np.nan)
    off_win = np.median(diff, axis=0)
    tb = "ok" if w0 <= t0 <= w1 else "SUSPECT"
    return res, off_pre, off_win, int(pre.sum()), tb


def main(dirs):
    if not dirs:
        raise SystemExit(__doc__)
    print(f"{'run':<42}{'traj':<11}{'tb':<4}{'truthLag':>9}{'rms0':>7}{'rmsMin':>7}{'estLag':>7}"
          f"{'estRms0':>8}{'estMin':>7}{'spLag':>7}{'spRms0':>8}{'spMin':>7}   {'offPre N E D cm':<24}{'offWin N E D cm'}")
    for d in dirs:
        res, off_pre, off_win, n_pre, tb = check(d)
        run = json.load(open(os.path.join(d, "run.json")))
        name = "/".join(os.path.normpath(d).split(os.sep)[-3:])
        edge = " EDGE" if res["truth"]["edge"] or res["est"]["edge"] else ""
        sp = res.get("sp", dict(lag=0, rms0=np.nan, rmin=np.nan))
        print(f"{name:<42}{run['trajectory']['shape']:<11}{tb:<4}{res['truth']['lag']:>+9d}"
              f"{res['truth']['rms0']:>7.4f}{res['truth']['rmin']:>7.4f}{res['est']['lag']:>+7d}"
              f"{res['est']['rms0']:>8.4f}{res['est']['rmin']:>7.4f}{sp['lag']:>+7d}{sp['rms0']:>8.4f}"
              f"{sp['rmin']:>7.4f}   {fmt3(off_pre):<24}{fmt3(off_win)} n_pre={n_pre}{edge}")


if __name__ == "__main__":
    main(sys.argv[1:])
