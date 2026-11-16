#!/usr/bin/env python3
"""A-14 pre-arm check (S21): EKF z (vehicle_local_position) minus truth z (sim_ground_truth) from boot.

Prints residual at the first EKF sample, at arm, its pre-arm extremes and the post-arm extreme in 0-10 s.
Usage: a14_prearm.py ULOG [ULOG ...]
"""
import sys
import numpy as np
from pyulog import ULog


def residual(path):
    u = ULog(path, ["vehicle_local_position", "sim_ground_truth", "vehicle_status"])
    d = {m.name: m.data for m in u.data_list}
    lp, gt, st = d["vehicle_local_position"], d["sim_ground_truth"], d["vehicle_status"]
    t = lp["timestamp"]
    zt = np.interp(t, gt["timestamp"], gt["z"])
    r = lp["z"] - zt
    armed = st["timestamp"][st["arming_state"] == 2]
    ta = armed[0] if len(armed) else t[-1]
    pre, post = t < ta, (t >= ta) & (t < ta + 10e6)
    ia = np.searchsorted(t, ta)
    rp = r[pre] if pre.any() else np.array([np.nan])
    return dict(t0_s=t[0] * 1e-6, arm_s=ta * 1e-6, r_first=r[0], r_arm=r[min(ia, len(r) - 1)],
                pre_min=rp.min(), pre_max=rp.max(), post_absmax=np.abs(r[post]).max(),
                z_reset=int(lp["z_reset_counter"][-1] - lp["z_reset_counter"][0]))


if __name__ == "__main__":
    keys = None
    for p in sys.argv[1:]:
        v = residual(p)
        if keys is None:
            keys = list(v)
            print("| log | " + " | ".join(keys) + " |\n|" + "---|" * (len(keys) + 1))
        print(f"| {p} | " + " | ".join(f"{x:.3f}" if isinstance(x, float) else str(x) for x in v.values()) + " |")
