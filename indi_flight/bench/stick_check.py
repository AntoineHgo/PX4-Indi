#!/usr/bin/env python3
"""S81 stick-path pre-test check: python3 stick_check.py RUN_DIR... -> stick_check.json per run and one line each.
Reads flight.ulg, run.json, sticks.csv. Reports manual_control_setpoint rate in the stick window, nav_state seen,
and whether the vertical velocity follows the demand (sticks.csv vz_up_demand): lag-compensated correlation and gain."""
import json
import os
import sys

import numpy as np
from pyulog import ULog


def check(d):
    meta = json.load(open(os.path.join(d, "run.json")))
    st = meta["stick"]
    t0, dur = st["t0_us"], st["dur_s"] * 1e6
    u = ULog(os.path.join(d, "flight.ulg"))
    ds = {x.name: x.data for x in u.data_list}
    w = lambda t: (t >= t0) & (t <= t0 + dur)  # noqa: E731
    mc = ds["manual_control_setpoint"]["timestamp"]
    mcw = mc[w(mc)]
    rate = (len(mcw) - 1) / ((mcw[-1] - mcw[0]) * 1e-6) if len(mcw) > 2 else 0.0
    vs = ds["vehicle_status"]
    sticks = np.genfromtxt(os.path.join(d, "sticks.csv"), delimiter=",", names=True)
    lp = ds["vehicle_local_position"]
    tl, vup = lp["timestamp"], -lp["vz"]
    sw = (sticks["t_sim_us"] >= t0) & (sticks["t_sim_us"] <= t0 + dur)
    ts, dem = sticks["t_sim_us"][sw], sticks["vz_up_demand_mps"][sw]
    best = None
    for lag_ms in range(0, 1001, 20):  # vehicle response lags the demand
        v = np.interp(ts + lag_ms * 1000, tl, vup)
        c = float(np.corrcoef(dem, v)[0, 1])
        if best is None or c > best[1]:
            gain = float(np.dot(dem, v) / np.dot(dem, dem))
            best = (lag_ms, c, gain, float(np.sqrt(np.mean((v - dem) ** 2))))
    res = {"run": os.path.basename(d.rstrip("/")), "nav_state_in_window": sorted({int(x) for x in vs["nav_state"][w(vs["timestamp"])]}),
           "nav_state_final_mode": int(vs["nav_state"][w(vs["timestamp"])][-1]) if w(vs["timestamp"]).any() else None,
           "manual_control_setpoint_hz": round(rate, 1), "sticks_sent": int(len(sticks["t_sim_us"])),
           "demand_peak_mps": float(np.max(np.abs(dem))), "best_lag_ms": best[0], "corr": round(best[1], 4),
           "gain_vz_per_demand": round(best[2], 3), "rms_err_mps_at_lag": round(best[3], 3),
           "follows_demand": bool(best[1] > 0.9 and 0.7 < best[2] < 1.3 and rate >= 40)}
    json.dump(res, open(os.path.join(d, "stick_check.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(json.dumps(check(d)))
