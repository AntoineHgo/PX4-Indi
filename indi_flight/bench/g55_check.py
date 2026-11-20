#!/usr/bin/env python3
"""G5.5 pass logic (GATES.md 5b "G5.5 exact test", S139). Offboard trajectory / velocity step on the INDI stack.

  python3 indi_flight/bench/g55_check.py RUN_DIR [--json OUT.json]      (RUN_DIR holds flight.ulg, run.json)

o1..o7 (mode trajectory): truth vs the ANALYTIC reference (metrics.trajectory_error_analytic, hold_pos_ned + traj_pva),
over the "traj" segment (run.json events), horizontal RMS <= 0.5 m, vertical RMS <= 0.3 m.
offb_vel_step (mode velocity): RMS(truth vx - 2) over the last 3 s of the 5 s step <= 0.2 m/s; |truth vx| at the end of the
4 s hold <= 0.1 m/s (stricter of: mean of the last 0.2 s, last sample); max |dz| (vs mean z of the 0.5 s before the step,
from the start of the settle to the end of the hold) <= 0.3 m. Validity: INDI position status logged, no mc_pos_control
task (px4.log), run exit ok. Exit code 0 pass, 1 fail, 2 invalid.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TRAJ_H, TRAJ_V = 0.5, 0.3
VEL_RMS, VEL_END, VEL_DZ = 0.2, 0.1, 0.3


def traj_verdict(rms_h, rms_v):
    return {"rms_h_m": rms_h, "rms_v_m": rms_v, "h_ok": bool(rms_h <= TRAJ_H), "v_ok": bool(rms_v <= TRAJ_V),
            "pass": bool(rms_h <= TRAJ_H and rms_v <= TRAJ_V)}


def vel_step_metrics(t, vx, z_up, t_settle, t_step, t_hold, t_end):
    """t, vx, z_up (up positive) truth arrays [s]; returns the gated numbers and verdict."""
    m = (t >= t_step + 2.0) & (t < t_hold)
    rms = float(np.sqrt(np.mean((vx[m] - 2.0) ** 2)))
    e = (t >= t_end - 0.2) & (t <= t_end)
    end = max(abs(float(np.mean(vx[e]))), abs(float(vx[t <= t_end][-1])))
    zref = float(np.mean(z_up[(t >= t_step - 0.5) & (t < t_step)]))
    s = (t >= t_settle) & (t <= t_end)
    dz = float(np.max(np.abs(z_up[s] - zref)))
    r = {"vx_rms_last3s": rms, "vx_end_abs": end, "dz_max": dz, "rms_ok": rms <= VEL_RMS, "end_ok": end <= VEL_END,
         "dz_ok": dz <= VEL_DZ}
    r["pass"] = bool(r["rms_ok"] and r["end_ok"] and r["dz_ok"])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    import metrics
    from pyulog import ULog
    run = json.load(open(os.path.join(a.run_dir, "run.json")))
    u = ULog(os.path.join(a.run_dir, "flight.ulg"))
    ev = {e["name"]: e for e in run.get("events", [])}
    out = {"run": a.run_dir, "scenario": run.get("scenario"), "seed": run.get("seed"), "invalid": []}
    if run.get("exit_status") != "ok":
        out["invalid"].append("exit_status %s: %s" % (run.get("exit_status"), run.get("error")))
    if not [d for d in u.data_list if d.name == "indi_pos_status"]:
        out["invalid"].append("indi_pos_status not logged")
    try:
        pl = open(os.path.join(a.run_dir, "px4.log"), errors="ignore").read()
        out["mc_pos_control_mentioned_in_px4_log"] = "mc_pos_control" in pl
    except OSError:
        out["mc_pos_control_mentioned_in_px4_log"] = None
    gt, src = metrics.truth_local_position(u)
    out["truth_source"] = src
    if gt is None:
        out["invalid"].append("no truth")
    elif run.get("scenario") == "offb_vel_step":
        t = gt["timestamp"] * 1e-6
        ts, th = ev["vstep"]["t_us"] * 1e-6, ev["vhold"]["t_us"] * 1e-6
        out.update(vel_step_metrics(t, gt["vx"], -gt["z"], ev["settle"]["t_us"] * 1e-6, ts, th, th + 4.0))
    elif "traj" in ev and run.get("trajectory"):
        t0 = ev["traj"]["t_us"]
        t = gt["timestamp"]
        m = (t >= t0) & (t < t0 + ev["traj"]["dur_s"] * 1e6)
        pos = np.column_stack([gt[k][m] for k in ("x", "y", "z")])
        st = metrics.trajectory_error_analytic(t[m], pos, run["trajectory"], run["trajectory"]["t0_us"], run["hold_pos_ned"])
        out.update(traj_verdict(st["rms_horizontal_m"], st["rms_vertical_m"]))
        out["n"] = st["n"]
        out["traj_t0_minus_event_s"] = (run["trajectory"]["t0_us"] - t0) * 1e-6
    else:
        out["invalid"].append("no traj event / trajectory in run.json")
    out["valid"] = not out["invalid"]
    out["verdict"] = "INVALID" if out["invalid"] or "pass" not in out else ("PASS" if out["pass"] else "FAIL")
    print(json.dumps(out))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
    return {"PASS": 0, "FAIL": 1}.get(out["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
