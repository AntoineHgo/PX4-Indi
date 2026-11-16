#!/usr/bin/env python3
"""Pre-test check of sim_scenario_player (D-SCHED, session 24).

usage: player_check.py <flight.ulg> <out.json>

Checks (IMU period 1250 us, the 800 Hz sensor_gyro of the gz world):
  1. vehicle_status reaches arming_state 2 and nav_state 14 (offboard); the vehicle then holds the hover height.
  2. every sim_schedule_applied row: timestamp - t_sched_us in [0, 1250).
  3. the status change (arming / nav_state 14) is published within 2 IMU periods after the applied row.
"""
import json
import sys

import numpy as np
from pyulog import ULog

IMU_US = 1250
NAV_OFFBOARD = 14
ARMED = 2
KINDS = {1: "arm", 2: "disarm", 3: "mode_offboard", 4: "sp"}


def main(ulg, out):
    u = ULog(ulg, message_name_filter_list=["sim_schedule_applied", "vehicle_status", "vehicle_local_position",
                                            "trajectory_setpoint"])
    d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    res = {"ulg": ulg, "imu_period_us": IMU_US}
    ap = d["sim_schedule_applied"]
    vs = d["vehicle_status"]
    rows = []
    for i in range(len(ap["timestamp"])):
        rows.append({"row_index": int(ap["row_index"][i]), "kind": KINDS.get(int(ap["kind"][i]), "?"),
                     "t_sched_us": int(ap["t_sched_us"][i]), "t_applied_us": int(ap["timestamp"][i]),
                     "delay_us": int(ap["timestamp"][i]) - int(ap["t_sched_us"][i])})
    res["rows"] = rows

    def first(mask):
        idx = np.nonzero(mask)[0]
        return int(vs["timestamp"][idx[0]]) if len(idx) else None

    t_arm_st = first(vs["arming_state"] == ARMED)
    t_off_st = first(vs["nav_state"] == NAV_OFFBOARD)
    res["t_status_armed_us"], res["t_status_offboard_us"] = t_arm_st, t_off_st
    res["check1_armed_and_offboard"] = t_arm_st is not None and t_off_st is not None

    # hover: height over 10 s starting 3 s after the offboard status
    if t_off_st is not None:
        lp = d["vehicle_local_position"]
        m = (lp["timestamp"] >= t_off_st + 3_000_000) & (lp["timestamp"] <= t_off_st + 13_000_000)
        if m.any():
            z, x, y = lp["z"][m], lp["x"][m], lp["y"][m]
            res["hover"] = {"n": int(m.sum()), "z_mean": float(z.mean()), "z_min": float(z.min()),
                            "z_max": float(z.max()), "x_absmax": float(np.abs(x).max()),
                            "y_absmax": float(np.abs(y).max())}
            res["check1_hover"] = bool(abs(z.mean() + 5.0) < 0.5 and np.abs(x).max() < 1.0 and np.abs(y).max() < 1.0)
        else:
            res["check1_hover"] = False

    res["check2_max_delay_us"] = max((r["delay_us"] for r in rows), default=None)
    res["check2_min_delay_us"] = min((r["delay_us"] for r in rows), default=None)
    res["check2"] = bool(rows) and all(0 <= r["delay_us"] < IMU_US for r in rows)

    lat = {}
    for r in rows:
        t_st = {"arm": t_arm_st, "mode_offboard": t_off_st}.get(r["kind"])
        if t_st is not None:
            lat[r["kind"]] = t_st - r["t_applied_us"]
    res["check3_status_minus_applied_us"] = lat
    res["check3"] = bool(lat) and len(lat) == 2 and all(0 <= v <= 2 * IMU_US for v in lat.values())
    res["pass"] = all(res.get(k) for k in ("check1_armed_and_offboard", "check1_hover", "check2", "check3"))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
