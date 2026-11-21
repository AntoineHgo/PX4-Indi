#!/usr/bin/env python3
"""G5.10 redefinition helper (S178): motor >= 0.99 duration + stabilized-part metrics. Does NOT replace bench/g510_check.py.
  score_motors.py sat  RUN_DIR [--json OUT]   window = segment "sat" .. "rec" of sat_sustained (5 s)
  score_motors.py stab RUN_DIR [--json OUT]   window = segment "full" .. "rec" of g510_stab_full (1 s), plus recovery metrics
actuator_motors control[0..3] = commanded thrust fraction 0..1. Reported: s with max over motors >= 0.99, s with all 4 >= 0.99.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../bench"))
import metrics
from pyulog import ULog

kind, d = sys.argv[1], sys.argv[2]
run = json.load(open(os.path.join(d, "run.json")))
u = ULog(os.path.join(d, "flight.ulg"))
ev = {e["name"]: e["t_us"] * 1e-6 for e in run["events"]}
am = metrics.ctrl_topic(u, "actuator_motors")
tm = am["timestamp"] * 1e-6
cmd = np.column_stack([am[f"control[{i}]"] for i in range(4)])
t0, t1 = (ev["sat"], ev["rec"]) if kind == "sat" else (ev["full"], ev["rec"])
m = (tm >= t0) & (tm < t1)
dt = np.diff(tm, append=tm[-1] + np.median(np.diff(tm)))
out = {"run": d, "window_s": [t0, t1], "window_len_s": t1 - t0,
       "motor_max_in_window": float(cmd[m].max()), "motor_mean_max4_in_window": float(cmd[m].max(axis=1).mean()),
       "s_any_ge_0.99": float(dt[m][cmd[m].max(axis=1) >= 0.99].sum()), "s_all4_ge_0.99": float(dt[m][cmd[m].min(axis=1) >= 0.99].sum())}
out["frac_any_ge_0.99"] = out["s_any_ge_0.99"] / out["window_len_s"]
out["frac_all4_ge_0.99"] = out["s_all4_ge_0.99"] / out["window_len_s"]
if kind == "stab":
    gt, _ = metrics.truth_local_position(u)
    ga = metrics.ctrl_topic(u, "vehicle_attitude_groundtruth")
    t = gt["timestamp"] * 1e-6
    z = -gt["z"]
    q = metrics.qcols(ga, "q")
    tilt = np.interp(t, ga["timestamp"] * 1e-6, np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1))))
    end = ev["rec"] + 9.0
    pre = (t >= ev["full"] - 1) & (t < ev["full"]); w = (t >= ev["full"]) & (t <= end)
    tl = dict(u.initial_parameters).get("MPC_TILTMAX_AIR")
    out.update(z_pre_m=float(z[pre].mean()), alt_loss_m=float(max(0.0, (z[pre].mean() - z[w]).max())), alt_gain_max_m=float((z[w] - z[pre].mean()).max()),
               tilt_max_deg=float(tilt[w].max()), MPC_TILTMAX_AIR=tl, tilt_limit_deg=None if tl is None else tl + 5.0,
               loc=bool(tilt[w].max() >= 60 or z[w].min() < 0.3 or run.get("exit_status") != "ok"))
    sat = cmd[(tm >= ev["full"]) & (tm <= end)].max(axis=1) >= 0.99
    last = float(tm[(tm >= ev["full"]) & (tm <= end)][sat][-1]) if sat.any() else None
    out["last_motor_ge_0.99_s"] = last
    if last is not None:  # recovery reference (no position setpoint in stabilized): level (tilt <= 5 deg) from the last saturated sample
        r = (t >= last) & (t <= end); bad = np.where(tilt[r] > 5.0)[0]
        out["level_5deg_after_sat_s"] = 0.0 if len(bad) == 0 else (None if bad[-1] == r.sum() - 1 else float(t[r][bad[-1] + 1] - last))
    out["pass_limits"] = bool(not out["loc"] and out["alt_loss_m"] <= 2.0 and (tl is None or out["tilt_max_deg"] <= tl + 5.0))
for k, v in out.items():
    print(f"{k}: {v}")
if "--json" in sys.argv:
    json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
