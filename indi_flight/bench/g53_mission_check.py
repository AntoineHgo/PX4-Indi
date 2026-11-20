#!/usr/bin/env python3
"""G5.3 mission part (GATES.md 5b, S139): every mission waypoint reached and cruise speed respected.

  python3 indi_flight/bench/g53_mission_check.py RUN_DIR [--json OUT.json]

Per waypoint: min truth horizontal distance over the mission window <= WP_TOL (1.0 m). Max truth horizontal speed over
the mission window <= 1.1 x MPC_XY_CRUISE (ULog initial parameters; the item speed is not set by the runner).
Frame: truth = vehicle_local_position_groundtruth (NED, origin at home/spawn: truth at rest on the ground is ~0,0),
run.json mission.wps_ne_m are metres north/east of home, so x=N, y=E with no offset (frame check printed as 'origin').
"""
import argparse
import json
import os
import sys

import numpy as np

WP_TOL = 1.0
SPD_FACTOR = 1.1


def check(t, x, y, vx, vy, wps, t0, t1, cruise, tol=WP_TOL, fac=SPD_FACTOR):
    m = (t >= t0) & (t <= t1)
    d = [float(np.min(np.hypot(x[m] - w[0], y[m] - w[1]))) for w in wps]
    vmax = float(np.max(np.hypot(vx[m], vy[m])))
    lim = fac * cruise
    ok_wp = [v <= tol for v in d]
    return {"wp_min_dist_m": d, "wp_ok": ok_wp, "vmax_mps": vmax, "vmax_limit_mps": lim, "speed_ok": vmax <= lim,
            "pass": all(ok_wp) and vmax <= lim}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    from pyulog import ULog
    u = ULog(os.path.join(a.run_dir, "flight.ulg"))
    meta = json.load(open(os.path.join(a.run_dir, "run.json")))
    g = [d for d in u.data_list if d.name == "vehicle_local_position_groundtruth"][0].data
    pt = {p["name"]: p["t_us"] * 1e-6 for p in meta["auto_phases"]}
    t = g["timestamp"] * 1e-6
    r = check(t, g["x"], g["y"], g["vx"], g["vy"], meta["mission"]["wps_ne_m"], pt["mission_start"], pt["mission_end"],
              float(u.initial_parameters["MPC_XY_CRUISE"]))
    r.update(run=a.run_dir, wps=meta["mission"]["wps_ne_m"], cruise=float(u.initial_parameters["MPC_XY_CRUISE"]),
             nav_acc_rad=float(u.initial_parameters.get("NAV_ACC_RAD", -1)),
             origin=[float(g["x"][t < pt["takeoff_cmd"]][-1]), float(g["y"][t < pt["takeoff_cmd"]][-1])],
             window=[pt["mission_start"], pt["mission_end"]])
    print(json.dumps(r))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
