#!/usr/bin/env python3
"""S139: tilt-error / setpoint tilt-rate at g57 H->P edges (idx 5, 9) vs g52 posctl x-step stick edge (no mode switch).
python3 g57_lag_compare.py g57 RUN_DIR... | g52 RUN_DIR..."""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g57_check as g  # noqa: E402


def streams(d):
    _, ds = g.load(d)
    a, s = ds["vehicle_attitude_groundtruth"], ds["vehicle_attitude_setpoint"]
    att = {"t": g._t(a), "q": np.stack([a[f"q[{k}]"] for k in range(4)], axis=1)}
    asp = {"t": g._t(s), "q": np.stack([s[f"q_d[{k}]"] for k in range(4)], axis=1)}
    return ds, att, asp


mode, dirs = sys.argv[1], sys.argv[2:]
for d in dirs:
    name = os.path.basename(d.rstrip("/"))
    ds, att, asp = streams(d)
    if mode == "g57":
        import json
        r = json.load(open(os.path.join(d, "g57_check_leaveP.json")))
        for i in (5, 9):
            te = r["edges"][i]["t_s"]
            m = g.tilt_metrics(att, asp, te)
            print(f"{name} e{i + 1} H>P t={te:.2f} v {r['edges'][i]['speed']:.2f} tilt_err {m[0]:.2f} peak0.3 {m[1]:.2f} sp_rate_max {m[2]:.0f} deg/s")
    else:
        rows = list(csv.DictReader(open(os.path.join(d, "sticks.csv"))))
        te = next(float(x["t_sim_us"]) for x in rows if float(x["x"]) > 100) * 1e-6
        m = g.tilt_metrics(att, asp, te)
        print(f"{name} xstep t={te:.2f} tilt_err {m[0]:.2f} peak0.3 {m[1]:.2f} sp_rate_max {m[2]:.0f} deg/s")
