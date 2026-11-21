#!/usr/bin/env python3
"""omega_ff peak (|omega_ff| norm and per-axis max, deg/s) from indi_pos_status.omega_ff and indi_rate_feedforward (valid only) per phase.
Usage: omega_ff_peaks.py RUN_DIR   (phases from run.json auto_phases; offboard runs: nav_state 14 span)"""
import sys, json, numpy as np
from pyulog import ULog
d = sys.argv[1]; ul = ULog(d + "/flight.ulg"); rj = json.load(open(d + "/run.json"))
t0 = ul.start_timestamp
def get(name):
    for x in ul.data_list:
        if x.name == name: return x
    return None
ps = get("indi_pos_status"); rf = get("indi_rate_feedforward"); vs = get("vehicle_status")
print("topics:", "indi_pos_status" if ps else "-", "indi_rate_feedforward" if rf else "-")
ph = rj.get("auto_phases")
if ph:
    P = {p["name"]: (p["t_us"] - 0) / 1e6 for p in ph}
    # run.json t_us is in log time already? print both for the sanity check
    segs = []
    names = [p["name"] for p in ph]
    def seg(n, a, b):
        if a in P and b in P: segs.append((n, P[a], P[b]))
    seg("takeoff", "takeoff_cmd", "takeoff_done"); seg("loiter", "takeoff_done", "hold_end")
    seg("mission", "mission_start", "mission_end"); seg("rtl", "rtl_cmd", "disarmed"); seg("land", "land_cmd", "disarmed")
else:
    nv = vs.data["nav_state"]; tv = (vs.data["timestamp"]) / 1e6
    on = tv[nv == 14]; segs = [("offboard", on[0], on[-1])] if len(on) else []
for src, x, fld in (("pos_status.omega_ff", ps, "omega_ff"), ("rate_ff", rf, "omega_ff")):
    if x is None: continue
    t = x.data["timestamp"] / 1e6
    w = np.stack([x.data["%s[%d]" % (fld, i)] for i in range(3)], 1)
    ok = np.isfinite(w).all(1)
    if src == "rate_ff" and "valid" in x.data: ok &= x.data["valid"] > 0
    for n, a, b in segs:
        m = (t >= a) & (t < b) & ok
        if not m.any(): print(src, n, "no samples"); continue
        r = np.degrees(np.abs(w[m]))
        print("%-20s %-9s [%.1f,%.1f] peak|w| %.2f dps  axes max p %.2f q %.2f r %.2f  p99 norm %.2f  n=%d" % (
            src, n, a, b, np.degrees(np.linalg.norm(w[m], axis=1).max()), *r.max(0), np.percentile(np.degrees(np.linalg.norm(w[m], axis=1)), 99), m.sum()))
