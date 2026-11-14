#!/usr/bin/env python3
"""Split INDI torque-increment activity per axis into its nu and a_f terms in a hover ULog.

Over t0+15 s .. t0+45 s prints, per axis, std and per-sample-change RMS of nu/G1, a_f/G1, the increment
(nu - a_f)/G1 and t_f. G1 is read from the log parameters (MC_INDI_G1_R/P/Y).

Usage: indi_terms.py LOG.ulg [LOG.ulg ...]
"""
import sys, numpy as np
from pyulog import ULog
for p in sys.argv[1:]:
    u = ULog(p, ["indi_rate_status"])
    g1 = [u.initial_parameters[f"MC_INDI_G1_{a}"] for a in "RPY"]
    d = u.get_dataset("indi_rate_status").data
    t = d["timestamp"]*1e-6; m = (t > t[0]+15) & (t < t[0]+45)
    print(p.split('results/')[-1], f"YAW_CUT {u.initial_parameters.get('MC_INDI_YAW_CUT')}")
    s = lambda x: f"{x.std():.5f}/{np.sqrt(np.mean(np.diff(x)**2)):.5f}"
    for i, ax in enumerate("RPY"):
        nu = d[f"nu[{i}]"][m]/g1[i]; af = d[f"angular_accel_filtered[{i}]"][m]/g1[i]
        print(f"  {ax} std/drms  nu/G1 {s(nu)}  a_f/G1 {s(af)}  (nu-a_f)/G1 {s(nu-af)}  "
              f"t_f {s(d[f'torque_filtered[{i}]'][m])}  inc {s(d[f'torque_increment[{i}]'][m])}")
