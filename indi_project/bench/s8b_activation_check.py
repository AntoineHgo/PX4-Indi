#!/usr/bin/env python3
"""Stage-8 task B first activation check: summarise what mc_indi_pos_control did in one flight.ulg."""
import sys
import numpy as np
from pyulog import ULog


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name:
            return d.data
    return None


ulog = ULog(sys.argv[1])
st = topic(ulog, "vehicle_status")
if st is not None:
    ns, idx = np.unique(st["nav_state"], return_index=True)
    print("nav_states (first seen, s):", {int(n): round(float(st["timestamp"][i]) * 1e-6, 1) for n, i in zip(ns, idx)})
s = topic(ulog, "indi_pos_status")
if s is None:
    print("indi_pos_status: NOT LOGGED (mode never active?)")
    sys.exit(0)
t = s["timestamp"] * 1e-6
print(f"indi_pos_status: {len(t)} samples, {t[0]:.1f}-{t[-1]:.1f} s, mean rate {len(t) / max(t[-1] - t[0], 1e-6):.1f} Hz")
print("max hold_cycles", int(s["hold_cycles"].max()), "failure samples", int(s["failure"].sum()))
print("mean_u_valid fraction", float(s["mean_u_valid"].mean()), "mean_u median", float(np.nanmedian(s["mean_u"])))
print("jerk_source counts", np.bincount(s["jerk_source"].astype(int)).tolist())
print("thrust median/min/max", float(np.median(s["thrust"])), float(s["thrust"].min()), float(s["thrust"].max()))
for k in ("a_c", "a_f", "t_c", "t_f", "omega_ff"):
    v = np.stack([s[f"{k}[{i}]"] for i in range(3)], 1)
    print(f"{k} median {np.round(np.median(v, 0), 3).tolist()} std {np.round(v.std(0), 3).tolist()}")
