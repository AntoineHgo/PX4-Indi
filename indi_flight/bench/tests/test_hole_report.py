#!/usr/bin/env python3
"""Synthetic self-test for bench/hole_report.py analyse() (arrays only, no ulog).

  python3 -I indi_flight/bench/tests/test_hole_report.py      (numpy only; exit 0 = pass, 1 = failure)

BREAK CHECK (run once, then restored): making the controller class ignore sim-hole overlap (drop the
`not _overlaps(..., sim_iv, pad)` clause in hole_report.analyse) fails the 'sim hole propagated' case.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import hole_report as hr  # noqa: E402

T0 = 10_000_000
END = T0 + 60_000_000


def reg(period, cut=()):
    ts = np.arange(T0, END, period, dtype=np.int64)
    for a, b in cut:   # remove samples in [a, b)
        ts = ts[(ts < a) | (ts >= b)]
    return ts


def topics(period, sim_cut=(), ctrl_cut=(), outer_cut=()):
    sim = reg(period, sim_cut)
    ctl = reg(period, tuple(sim_cut) + tuple(ctrl_cut))   # controller topics follow the sim steps
    return {"sim_ground_truth": sim, "sensor_gyro": sim, "vehicle_angular_velocity": ctl,
            "vehicle_torque_setpoint": ctl, "actuator_motors": ctl,
            "vehicle_local_position_setpoint": reg(11236, outer_cut)}


fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


for per, tag in ((1250, "800Hz"), (2500, "400Hz")):
    r = hr.analyse(topics(per), T0, END)
    check(f"{tag} no holes: pass, zero counts", r["pass"] and all(c["count"] == 0 for c in r["classes"].values()))
    row = [x for x in r["topics"] if x["topic"] == "actuator_motors"][0]
    check(f"{tag} rate measured from median", abs(row["rate_hz"] - 1e6 / per) < 1e-6)
check("outer 89 Hz topic has its own median", abs([x for x in hr.analyse(topics(1250), T0, END)["topics"]
      if x["topic"] == "vehicle_local_position_setpoint"][0]["rate_hz"] - 89.0) < 0.1)

# one sim hole (3 steps) propagated to controller topics: sim, not controller
cut = [(T0 + 20_000_000, T0 + 20_000_000 + 3 * 1250)]
r = hr.analyse(topics(1250, sim_cut=cut), T0, END)
check("sim hole counted as sim", r["classes"]["sim"]["count"] == 1)
check("sim hole not counted as controller", r["classes"]["controller"]["count"] == 0)
check("sim hole missing 3 steps", [x for x in r["topics"] if x["topic"] == "sim_ground_truth"][0]["missing"] == 3)

# controller-only hole
r = hr.analyse(topics(1250, ctrl_cut=[(T0 + 30_000_000, T0 + 30_000_000 + 2 * 1250)]), T0, END)
check("controller-only hole counted as controller", r["classes"]["controller"]["count"] >= 1
      and r["classes"]["sim"]["count"] == 0)
check("same hole in 3 controller topics counts once", r["classes"]["controller"]["count"] == 1)

# 12 ms hole -> FAIL; 8 ms single hole in a short run is a fraction fail only if above limit
r = hr.analyse(topics(1250, ctrl_cut=[(T0 + 30_000_000, T0 + 30_000_000 + 12_000)]), T0, END)
check("12 ms controller hole FAIL", (not r["pass"]) and r["classes"]["controller"]["max_hole_ms"] >= 12.0
      and not r["classes"]["controller"]["pass"])
r = hr.analyse(topics(1250, sim_cut=[(T0 + 30_000_000, T0 + 30_000_000 + 12_000)]), T0, END)
check("12 ms sim hole FAIL", not r["classes"]["sim"]["pass"] and r["classes"]["controller"]["count"] == 0)
r = hr.analyse(topics(1250, ctrl_cut=[(T0 + 30_000_000, T0 + 30_000_000 + 4 * 1250)]), T0, END)
check("5 ms hole alone: pass (fraction 12/72000 < 0.1 %)", r["pass"])

# publisher jitter: a duplicate stamp next to a one-sample gap is not a hole; a rate-limited groundtruth topic is info only
j = topics(1250); m = j["actuator_motors"].copy(); m[30000:30003] = [m[30000], m[30000], m[30002]]
j["actuator_motors"] = m
r = hr.analyse(j, T0, END)
check("duplicate stamp + gap cancels", r["pass"] and r["classes"]["controller"]["count"] == 0)
j = topics(1250); j["vehicle_attitude_groundtruth"] = np.delete(reg(1250), np.arange(5000, 40000, 8))
r = hr.analyse(j, T0, END)
check("decimated groundtruth is info only", r["pass"] and r["classes"]["sim"]["count"] == 0)

# first second skipped
r = hr.analyse(topics(1250, ctrl_cut=[(T0 + 200_000, T0 + 300_000)]), T0, END)
check("hole in first second ignored", r["pass"] and r["classes"]["controller"]["count"] == 0)

# logger dropout: gap in all topics explained by the dropout, class logger only
cut = [(T0 + 40_000_000, T0 + 40_000_000 + 5000)]
r = hr.analyse(topics(1250, ctrl_cut=cut), T0, END, dropouts=[(T0 + 40_000_000 + 5000, 5.0)])
check("dropout counted as logger", r["classes"]["logger"]["count"] == 1 and r["classes"]["controller"]["count"] == 0)
r = hr.analyse(topics(1250), T0, END, dropouts=[(T0 + 40_000_000, 15.0)])
check("15 ms dropout FAIL", not r["classes"]["logger"]["pass"] and not r["pass"])

# S86 fix 2: the 10 ms limit holds for controller gaps attributed to a sim hole (12 ms controller hole next to a 2.5 ms sim hole)
t = T0 + 30_000_000
r = hr.analyse(topics(1250, sim_cut=[(t, t + 2 * 1250)], ctrl_cut=[(t + 2 * 1250, t + 2 * 1250 + 12_000)]), T0, END)
check("S86 12 ms controller hole next to 2.5 ms sim hole FAIL",
      (not r["pass"]) and r["classes"]["controller"]["max_hole_ms"] >= 12.0 and not r["classes"]["controller"]["pass"])

# S86 fix 3: no primary sim topic (only decimated *_groundtruth) -> "sim: not assessable", not a silent pass
j = topics(1250); del j["sim_ground_truth"]; del j["sensor_gyro"]
j["vehicle_attitude_groundtruth"] = np.delete(reg(1250), np.arange(5000, 40000, 8))
r = hr.analyse(j, T0, END)
check("S86 no primary sim topic: not assessable FAIL", (not r["pass"]) and not r["classes"]["sim"]["pass"]
      and "not assessable" in r["classes"]["sim"].get("verdict", "") and "not assessable" in hr.fmt(r, "x"))
check("S86 primary sim topic present: assessable", "verdict" not in hr.analyse(topics(1250), T0, END)["classes"]["sim"])

# S86 fix 1: count cross-check. 5 isolated lost samples (gap-based missing 5) balanced by 5 far-away duplicate stamps
# (count-based missing 0): the two methods disagree by 5 > 1 -> not PASS even though each alone is under the limits.
j = topics(1250); m = j["actuator_motors"]
lost = np.arange(5000, 45000, 8000)
m = np.delete(m, lost)
m = np.insert(m, np.arange(5000, 45000, 8000) + 4000, m[np.arange(5000, 45000, 8000) + 4000])
j["actuator_motors"] = m
r = hr.analyse(j, T0, END)
row = [x for x in r["topics"] if x["topic"] == "actuator_motors"][0]
check("S86 count cross-check disagreement is not PASS", row["missing"] == 5 and row["missing_count_based"] == 0
      and row["count_disagree"] and not row["pass"] and not r["pass"])
check("S86 count cross-check agrees on a real hole", [x for x in hr.analyse(
      topics(1250, ctrl_cut=[(T0 + 30_000_000, T0 + 30_000_000 + 4 * 1250)]), T0, END)["topics"]
      if x["topic"] == "actuator_motors"][0]["missing_count_based"] == 4)

print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
