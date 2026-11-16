#!/usr/bin/env python3
"""EKF height error on the ground before arming: estimate z minus sim_ground_truth z, at fixed sim times.

Usage: prearm_zbias.py <out.txt> <flight.ulg>...
"""
import sys
import numpy as np
from pyulog import ULog

TIMES_S = (10, 20, 29)
out = ["log " + " ".join("bias_z_%ds_m" % t for t in TIMES_S)]
for f in sys.argv[2:]:
    u = ULog(f, ["sim_ground_truth", "vehicle_local_position"])
    g = u.get_dataset("sim_ground_truth").data
    lp = u.get_dataset("vehicle_local_position").data
    row = []
    for t in TIMES_S:
        i = min(np.searchsorted(g["timestamp"], t * 1e6), len(g["z"]) - 1)
        j = min(np.searchsorted(lp["timestamp"], t * 1e6), len(lp["z"]) - 1)
        row.append("%.2f" % (lp["z"][j] - g["z"][i]))
    out.append(f + " " + " ".join(row))
open(sys.argv[1], "w").write("\n".join(out) + "\n")
print("\n".join(out))
