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

# S87: count cross-check tolerance. Disagreement = duplicate stamps not absorbed by a gap; > 1 FAILs, <= 1 is tolerated.
def motors_row(j):
    return [x for x in hr.analyse(j, T0, END)["topics"] if x["topic"] == "actuator_motors"][0]


def lose_and_dup(n):
    """n isolated lost samples balanced by n far-away duplicate stamps -> gap-based n, count-based 0."""
    j = topics(1250)
    idx = np.arange(5000, 5000 + 8000 * n, 8000)
    m = np.delete(j["actuator_motors"], idx)
    m = np.insert(m, idx + 4000, m[idx + 4000])
    j["actuator_motors"] = m
    return j


# healthy 800 Hz, stamps jittered by +-1 us (rounded to int us), publisher dup stamps + 1-2 period gaps like the s86 flights
rng = np.random.default_rng(1)
j = topics(1250)
for k in ("vehicle_angular_velocity", "vehicle_torque_setpoint", "actuator_motors"):
    j[k] = j[k] + rng.integers(-1, 2, j[k].size)
m = j["actuator_motors"].copy()
for p in range(2000, 50000, 5000):   # dup stamp followed by a 2-period gap (publish jitter), no lost sample
    m[p + 1] = m[p]
    m[p + 2] = m[p] + 2 * 1250
    m[p + 3:] = m[p + 3:]
j["actuator_motors"] = np.sort(m)
r = hr.analyse(j, T0, END)
check("S87 healthy 800 Hz with 1 us jitter and publish jitter: PASS", r["pass"] and not motors_row(j)["count_disagree"])

# the s86 defect: a 3-period gap (2 missing by dt) with ONE duplicate stamp = 1 real lost sample; both methods must say 1
j = topics(1250); m = j["actuator_motors"]
m = np.delete(m, [30001, 30002])      # gap of 3 periods
m = np.insert(m, 30000, m[30000])     # + one duplicate stamp next to it
j["actuator_motors"] = m
row = motors_row(j)
check("S87 3-period gap + 1 dup: gap-based == count-based == 1, no disagree",
      row["missing"] == 1 and row["missing_count_based"] == 1 and not row["count_disagree"])

# a single real dropped sample is still reported as missing by both methods (and PASS, 1/72000 << 0.1 %)
j = topics(1250); j["actuator_motors"] = np.delete(j["actuator_motors"], 20000)
row = motors_row(j)
check("S87 single dropped sample reported", row["missing"] == 1 and row["missing_count_based"] == 1
      and row["count"] == 1 and not row["count_disagree"])

# disagreement of 1 passes, 2 fails (> 1)
check("S87 count disagreement of 1 tolerated", motors_row(lose_and_dup(1))["pass"] and not motors_row(lose_and_dup(1))["count_disagree"])
row = motors_row(lose_and_dup(2))
check("S87 count disagreement of 2 FAILs", row["missing"] - row["missing_count_based"] == 2 and row["count_disagree"]
      and not row["pass"] and not hr.analyse(lose_and_dup(2), T0, END)["pass"])

# tolerance scales with the duplicate-stamp count: 1200 dup+gap publish-jitter pairs -> tolerance 1 + int(0.001 * ~1200) = 2
def jittery(extra_far_dups):
    j = topics(1250)
    base = j["actuator_motors"]
    for q in range(40, base.size - 40, 40):   # dup stamp + 2-period gap: 1 stamp replaced, nothing lost
        base[q + 1] = base[q]
        base[q + 2] = base[q] + 2 * 1250
    base = np.sort(base)
    fars = np.arange(1000, 1000 + 20 * extra_far_dups, 20) * 1 + 20   # >= 8 samples away from every pair
    fars = fars - (fars % 40) + 20
    j["actuator_motors"] = np.insert(base, fars, base[fars]) if extra_far_dups else base
    return j


row = motors_row(jittery(0))
check("S87 many publish-jitter dups: PASS, tolerance scales", row["pass"] and row["count_tol"] >= 2 and not row["count_disagree"])
row = motors_row(jittery(2))
check("S87 2 unpaired dups among ~1200: within tolerance", row["pass"] and not row["count_disagree"]
      and abs(row["missing"] - row["missing_count_based"]) == 2)
row = motors_row(jittery(6))
check("S87 6 unpaired dups among ~1200: FAIL", row["count_disagree"] and not row["pass"])

# ---- S88 (T186): max hole from RAW gaps, per-topic excess over the nominal period
def with_gap(period, gap_us, t_gap=T0 + 30_000_000):
    """Regular grid, then one gap of exactly gap_us and the grid continues from there (median unchanged)."""
    a = np.arange(T0, t_gap, period, dtype=np.int64)
    return np.concatenate([a, np.arange(a[-1] + gap_us, END, period, dtype=np.int64)])


def row_of(j, name):
    return [x for x in hr.analyse(j, T0, END)["topics"] if x["topic"] == name][0]


# (a) k=2 gap with a duplicate stamp next to it: count absorbed, but the raw gap must still be reported
j = topics(1250)
m = j["actuator_motors"]
q = 20000
m[q + 1] = m[q]            # dup stamp ...
m[q + 2] = m[q] + 2 * 1250   # ... followed by a 2-period gap
j["actuator_motors"] = np.sort(m)
row = row_of(j, "actuator_motors")
check("S88a k=2 gap next to a dup is reported in max_hole_ms (raw dt 2.5 ms)", abs(row["max_hole_ms"] - 2.5) < 1e-6
      and row["missing"] == 0)
# a 10 ms-excess-class k=2 case at a slow topic: 100 Hz topic (nominal 10 ms), dup + 21 ms gap must fail (excess 11 ms)
j = topics(1250)
o = with_gap(10000, 21000)
k = int(np.flatnonzero(np.diff(o) == 21000)[0])
o[k + 1:] = o[k + 1:]
o = np.sort(np.insert(o, k, o[k]))   # dup stamp right before the gap
j["vehicle_local_position_setpoint"] = o
row = row_of(j, "vehicle_local_position_setpoint")
check("S88a 100 Hz topic, dup + 21 ms gap: FAIL on excess 11 ms", not row["pass"] and row["max_excess_ms"] > 10.0)

# (b) 89 Hz outer topic (nominal 11.236 ms): 18.75 ms gap passes, 25 ms gap fails
j = topics(1250); j["vehicle_local_position_setpoint"] = with_gap(11236, 18750)
row = row_of(j, "vehicle_local_position_setpoint")
check("S88b 89 Hz topic, one 18.75 ms gap: PASS (excess 7.5 ms)", row["pass"] and abs(row["max_excess_ms"] - 7.514) < 0.01
      and not row["count_disagree"])
j = topics(1250); j["vehicle_local_position_setpoint"] = with_gap(11236, 25000)
row = row_of(j, "vehicle_local_position_setpoint")
check("S88b 89 Hz topic, one 25 ms gap: FAIL (excess 13.8 ms)", not row["pass"] and row["max_excess_ms"] > 10.0)

# (c) 250 Hz controller topic (nominal 4 ms), one 15 ms gap: excess 11 ms -> FAIL
j = topics(1250); j["actuator_motors"] = with_gap(4000, 15000)
row = row_of(j, "actuator_motors")
check("S88c 250 Hz topic, one 15 ms gap: FAIL (excess 11 ms)", not row["pass"] and abs(row["max_excess_ms"] - 11.0) < 1e-6)

print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)
