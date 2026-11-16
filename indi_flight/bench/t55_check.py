"""T55 check of a --sched --sched-anchor run of an attitude or trajectory scenario (run in Docker: pyulog).
usage: t55_check.py <run dir> [step_roll|traj_lemniscate]   (reads flight.ulg, run.json, sched.txt; no copy of the trajectory math:
traj_phase / traj_pos are imported from run_scenario.py)"""
import importlib.util
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

d = sys.argv[1]
scen = sys.argv[2] if len(sys.argv) > 2 else json.load(open(os.path.join(d, "run.json")))["scenario"]
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rs", os.path.join(here, "run_scenario.py"))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)
sc = rs.SCENARIOS[scen]
run = json.load(open(os.path.join(d, "run.json")))
print("run exit_status", run.get("exit_status"), "error", run.get("error"), "wall_s", run.get("wall_time_s"), "metrics", run.get("metrics_status"))
u = ULog(os.path.join(d, "flight.ulg"))
D = {}
for x in u.data_list:
    D.setdefault(x.name, x.data)
a = D["sim_schedule_applied"]
n_file = sum(1 for l in open(os.path.join(d, "sched.txt")) if l.strip() and not l.startswith("#"))
print("rows in file", n_file, "applied", len(a["timestamp"]))
err = a["timestamp"].astype(np.int64) - a["t_sched_us"].astype(np.int64)
print("applied-row error us: min", err.min(), "max", err.max(), "mean %.1f" % err.mean(), "rows with err != 0:", int((err != 0).sum()))
for k in sorted(set(a["kind"])):
    m = a["kind"] == k
    print("  kind", k, "rows", int(m.sum()), "err max", int(err[m].max()))
print("row_index contiguous:", bool((np.diff(a["row_index"].astype(np.int64)) == 1).all()))
anc = int(a["anchor_us"][-1])
t_scen = anc + 3_000_000
s = D["vehicle_status"]
off = [(int(t), int(nv)) for t, nv in zip(s["timestamp"], s["nav_state"])]
t14 = next(t for t, nv in off if nv == 14)
print("anchor_us", anc, "first nav_state 14 in vehicle_status", t14, "diff", anc - t14)
hold = [a["sp[%d]" % i][a["kind"] == 5][0] for i in range(4)]
print("hold (first sp_hold)", [round(float(h), 4) for h in hold])
lp = D["vehicle_local_position"]
print("armed at", [int(t) for t, ar in zip(s["timestamp"], s["arming_state"]) if ar == 2][:1], "final z", float(lp["z"][-1]))

if sc["mode"] == "attitude":
    q = D["vehicle_attitude_setpoint"]
    t = q["timestamp"].astype(np.int64)
    qd = np.column_stack([q["q_d[%d]" % i] for i in range(4)])
    w, x, y, z = qd.T
    roll = np.degrees(np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)))
    thr = -q["thrust_body[2]"]
    print("vehicle_attitude_setpoint samples", len(t), "period median us", int(np.median(np.diff(t))))
    tt = 0.0
    prev = 0.0
    for name, dur, val in sc["segments"]:
        te = t_scen + int(tt * 1e6)
        m = (t >= te) & (t < te + int(dur * 1e6))
        first = np.argmax(t >= te)
        # first sample at or after the scheduled event time and its value; the last sample before
        print("segment %-6s sched +%.3f s: expected roll %+.1f deg; first sp sample at +%d us value %+.3f deg; "
              "roll over segment min %+.3f max %+.3f; thrust min %.3f max %.3f" %
              (name, tt, val, int(t[first] - te), roll[first], roll[m].min(), roll[m].max(), thr[m].min(), thr[m].max()))
        tt += dur
    for i in range(len(t) - 1):  # exact step instants: first sample whose roll differs by > 1 deg from the sample before
        pass
    jumps = [(int(t[i]) - t_scen, round(float(roll[i - 1]), 2), round(float(roll[i]), 2)) for i in range(1, len(t)) if abs(roll[i] - roll[i - 1]) > 1.0]
    print("roll jumps > 1 deg (us after anchor+3 s, before, after):", jumps)
    zz = lp["z"][(lp["timestamp"] >= t_scen) & (lp["timestamp"] < t_scen + 14_000_000)]
    print("altitude over the window: z min %.3f max %.3f (hold %.3f)" % (zz.min(), zz.max(), hold[2]))
else:
    ts = D["trajectory_setpoint"]
    t = ts["timestamp"].astype(np.int64)
    t0 = t_scen + 3_000_000
    dur = sc["segments"][1][1]
    print("trajectory_setpoint samples", len(t), "logged period median us", int(np.median(np.diff(t))))
    m = (t >= t0) & (t < t0 + int(dur * 1e6))
    idx = np.where(m)[0]
    errs = []
    for i in idx:
        ph = rs.traj_phase(sc["traj"], (t[i] - t0) * 1e-6)
        ref = rs.traj_pos(sc["traj"], ph)
        e = [ts["position[%d]" % k][i] - (hold[k] + ref[k]) for k in range(3)]
        errs.append(math.sqrt(sum(v * v for v in e)))
    errs = np.array(errs)
    print("samples in window", len(idx), "position error to analytic reference: max %.4f m mean %.4f m" % (errs.max(), errs.mean()))
    for f in (0.1, 0.3, 0.5, 0.7, 0.9):
        i = idx[int(f * (len(idx) - 1))]
        tl = (t[i] - t0) * 1e-6
        ph = rs.traj_phase(sc["traj"], tl)
        ref = rs.traj_pos(sc["traj"], ph)
        got = [float(ts["position[%d]" % k][i]) for k in range(3)]
        exp = [hold[k] + ref[k] for k in range(3)]
        print("  t_traj %.3f s: sp %s ref %s |err| %.4f m  v_sp %s" % (tl, [round(g, 3) for g in got], [round(float(e), 3) for e in exp],
              math.dist(got, exp), [round(float(ts["velocity[%d]" % k][i]), 3) for k in range(3)]))
    pm = (lp["timestamp"] >= t0) & (lp["timestamp"] < t0 + int(dur * 1e6))
    print("vehicle x range %.2f..%.2f y %.2f..%.2f" % (lp["x"][pm].min(), lp["x"][pm].max(), lp["y"][pm].min(), lp["y"][pm].max()))
mj = os.path.join(d, "metrics.json")
if os.path.exists(mj):
    mm = json.load(open(mj))
    print("metrics.json keys:", list(mm.keys())[:25])
    for k in ("trajectory", "step_metrics", "tracking", "summary"):
        if k in mm:
            print(k, json.dumps(mm[k])[:600])
