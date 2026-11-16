#!/usr/bin/env python3
"""Extract the M3a injection window of one axis from a ulog as CSV t,d,x,y for margins_est.py.

t = indi_rate_status.timestamp_sample [s], d = inject, x = torque_sp (u = c + d, what the plant sees),
y = torque_sp_pre_inject (c, returned to the summation point), so L = -G_yd/G_xd (margins_est.py docstring).
Window = samples where d != 0 (the module zeroes d outside [t0, t0 + NP*Tp), D-G2-INJ).
Usage: m3a_csv.py <flight.ulg> <axis 0|1|2> <out.csv>
"""
import sys

import numpy as np
from pyulog import ULog


def main(ulg, axis, out):
    s = [d for d in ULog(ulg, ["indi_rate_status"]).data_list if d.name == "indi_rate_status"][0].data
    t = np.asarray(s["timestamp_sample"], float) * 1e-6
    d = np.asarray(s[f"inject[{axis}]"], float)
    nz = np.flatnonzero(d != 0.0)
    if nz.size == 0:
        raise SystemExit("no injection on this axis")
    w = slice(nz[0], nz[-1] + 1)
    x = np.asarray(s[f"torque_sp[{axis}]"], float)
    y = np.asarray(s[f"torque_sp_pre_inject[{axis}]"], float)
    np.savetxt(out, np.column_stack([t[w], d[w], x[w], y[w]]), delimiter=",", header="t,d,x,y", comments="",
               fmt="%.9g")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
