#!/usr/bin/env python3
"""Plot rpy and xyz, estimated vs setpoint, from a runner flight.ulg.
usage: plot_flight.py RUN_DIR OUT.png   (RUN_DIR has flight.ulg and run.json)"""
import json, sys, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyulog import ULog

def eul(q):  # q = w,x,y,z -> roll,pitch,yaw (deg), NED/FRD
    w, x, y, z = q.T
    r = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    p = np.arcsin(np.clip(2*(w*y-z*x), -1, 1))
    h = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return np.degrees(np.unwrap(np.c_[r, p, h], axis=0))

def main(run, out):
    u = ULog(os.path.join(run, "flight.ulg"))
    meta = json.load(open(os.path.join(run, "run.json")))
    g = lambda n: u.get_dataset(n).data
    att, ats = g("vehicle_attitude"), g("vehicle_attitude_setpoint")
    lp, lps = g("vehicle_local_position"), g("vehicle_local_position_setpoint")
    qa = np.c_[[att[f"q[{i}]"] for i in range(4)]].T
    qs = np.c_[[ats[f"q_d[{i}]"] for i in range(4)]].T
    ev = meta["events"]
    t0 = ev[0]["t_us"] - 2e6
    t1 = max(e["t_us"] + e["dur_s"]*1e6 for e in ev) + 1e6
    T = lambda d: (d["timestamp"] - t0)/1e6
    ea, es = eul(qa), eul(qs)
    fig, ax = plt.subplots(3, 2, figsize=(14, 9), sharex=True)
    for i, n in enumerate(["roll", "pitch", "yaw"]):
        a = ax[i, 0]
        a.plot(T(att), ea[:, i], label="estimated", lw=1.2)
        a.plot(T(ats), es[:, i], "--", label="setpoint", lw=1.2)
        a.set_ylabel(f"{n} [deg]"); a.grid(alpha=.3)
    for i, (n, k) in enumerate([("x north", "x"), ("y east", "y"), ("z down", "z")]):
        a = ax[i, 1]
        a.plot(T(lp), lp[k], label="estimated", lw=1.2)
        a.plot(T(lps), lps[k], "--", label="setpoint", lw=1.2)
        a.set_ylabel(f"{n} [m]"); a.grid(alpha=.3)
    for c in range(2):
        ax[0, c].legend(loc="upper right")
        ax[2, c].set_xlabel("time since first event - 2 s [s]")
        for e in ev:
            for a in ax[:, c]:
                a.axvline((e["t_us"]-t0)/1e6, color="gray", lw=.6, alpha=.5)
            ax[0, c].text((e["t_us"]-t0)/1e6, 1.02, e["name"], transform=ax[0, c].get_xaxis_transform(), fontsize=7, rotation=30)
    ax[0, 0].set_title(f'attitude: {meta["scenario"]} ({meta["controller"]})', pad=22)
    ax[0, 1].set_title("position", pad=22)
    for a in ax.ravel(): a.set_xlim(0, (t1-t0)/1e6)
    fig.tight_layout(); fig.savefig(out, dpi=110)

main(*sys.argv[1:3])
