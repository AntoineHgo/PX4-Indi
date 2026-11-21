#!/usr/bin/env python3
"""G5.10 pass logic (GATES.md row G5.10, S147). Scenario sat_sustained (scenarios.py), truth = sim_ground_truth (sim time).

  python3 indi_flight/bench/g510_check.py RUN_DIR [--json OUT.json]      (RUN_DIR holds flight.ulg, run.json)

Parts: SAT = segment "sat" (available thrust 0.274 of nominal, 3 m x step), REC = "rec" (full thrust, setpoint kept), AGG = "agg"
(20 m x, 4 m up step at full scale) + "aghold". Limits: no LOC (run ok, tilt < 60 deg, no disarm, nav_state offboard, z above 0.3 m),
altitude loss <= 2.0 m (max drop of truth z below the mean of the 1 s before "sat", over sat start .. end), tilt <= MPC_TILTMAX_AIR + 5 deg (S175; 20 deg if the param is absent),
no windup: back within 0.3 m (3-D) of the setpoint and staying in <= 5 s after saturation ends (SAT: start of "rec"; AGG: last
saturated sample, saturated = max motor command >= 0.98 x limit, limit 0.274 in SAT, 1.0 in AGG). Saturation fraction per part
proves the saturation. Exit 0 pass, 1 fail, 2 invalid (no saturation / no truth / events missing).
"""
import argparse, json, os, sys
import numpy as np

LIM = dict(alt_loss=2.0, tilt_deg=20.0, back_m=0.3, back_s=5.0, loc_tilt_deg=60.0)
SAT_SCALE, SAT_FRAC_MIN = 0.274, 0.05
TILT_MARGIN_DEG = 5.0   # S175 Q9 a: tilt limit = MPC_TILTMAX_AIR + 5 deg (read from the log); LIM['tilt_deg'] is the legacy 20 deg


def back_time(t, err, t_from, t_to):
    """Seconds from t_from until err <= back_m and stays so up to t_to (None: never / not at the end)."""
    m = (t >= t_from) & (t <= t_to)
    if not m.any():
        return None
    tt, ee = t[m], err[m]
    bad = np.where(ee > LIM["back_m"])[0]
    if len(bad) == 0:
        return 0.0
    if bad[-1] == len(tt) - 1:
        return None
    return float(tt[bad[-1] + 1] - t_from)


def sat_stats(tm, cmd, lim, t0, t1):
    m = (tm >= t0) & (tm < t1)
    if not m.any():
        return 0.0, None
    s = cmd[m].max(axis=1) >= 0.98 * lim
    last = float(tm[m][s][-1]) if s.any() else None
    return float(s.mean()), last


def analyse(t, pos, tilt_deg, tm, cmd, ev, sp, run_ok=True, nav_ok=True, armed_ok=True, tilt_lim_deg=None):
    """t [s], pos (N,3) NED truth, tilt_deg (N,), tm [s] / cmd (M,4) motor commands, ev {name: t_start_s} for sat, rec, agg,
    aghold, end; sp {name: setpoint NED}."""
    z_up = -pos[:, 2]
    pre = (t >= ev["sat"] - 1.0) & (t < ev["sat"])
    z0 = float(z_up[pre].mean())
    w = (t >= ev["sat"]) & (t <= ev["end"])
    tl = LIM["tilt_deg"] if tilt_lim_deg is None else float(tilt_lim_deg)
    out = {"tilt_limit_deg": tl, "tilt_ok_legacy_20deg": None, "z_pre_m": z0, "alt_loss_m": float(max(0.0, (z0 - z_up[w]).max())), "tilt_max_deg": float(tilt_deg[w].max())}
    f_sat, _ = sat_stats(tm, cmd, SAT_SCALE, ev["sat"], ev["rec"])
    f_rec, _ = sat_stats(tm, cmd, 1.0, ev["rec"], ev["agg"])
    f_agg, last_agg = sat_stats(tm, cmd, 1.0, ev["agg"], ev["end"])
    out.update(sat_frac_sat_part=f_sat, sat_frac_rec_part=f_rec, sat_frac_agg_part=f_agg, last_sat_agg_s=last_agg)
    e_sat = np.linalg.norm(pos - np.asarray(sp["rec"]), axis=1)
    e_agg = np.linalg.norm(pos - np.asarray(sp["agg"]), axis=1)
    out["back_s_sat"] = back_time(t, e_sat, ev["rec"], ev["agg"])
    out["back_s_agg"] = None if last_agg is None else back_time(t, e_agg, last_agg, ev["end"])
    ix = (t >= ev["rec"]) & (t < ev["agg"])
    out["overshoot_x_sat_m"] = float(max(0.0, (pos[ix, 0] - sp["rec"][0]).max()))
    ix = t >= ev["agg"]
    out["overshoot_x_agg_m"] = float(max(0.0, (pos[ix, 0] - sp["agg"][0]).max()))
    out["loc"] = bool((not run_ok) or (not nav_ok) or (not armed_ok) or out["tilt_max_deg"] >= LIM["loc_tilt_deg"] or float(z_up[w].min()) < 0.3)
    v = {"no_loc": not out["loc"], "alt_loss": out["alt_loss_m"] <= LIM["alt_loss"], "tilt": out["tilt_max_deg"] <= tl,
         "back_sat": out["back_s_sat"] is not None and out["back_s_sat"] <= LIM["back_s"],
         "back_agg": out["back_s_agg"] is not None and out["back_s_agg"] <= LIM["back_s"]}
    out["tilt_ok_legacy_20deg"] = bool(out["tilt_max_deg"] <= LIM["tilt_deg"])
    out["verdict"] = {k: bool(x) for k, x in v.items()}
    out["invalid"] = [s for s, bad in (("no saturation in SAT part", f_sat < SAT_FRAC_MIN),
                                       ("no saturation in AGG part", f_agg < SAT_FRAC_MIN)) if bad]
    out["pass"] = bool(all(v.values()) and not out["invalid"])
    return out


def tilt_limit_from_params(initial, changed, t_sat_s):
    """(MPC_TILTMAX_AIR, tilt limit or None, warning or None) from the log parameters; value at SAT start (initial, then changes
    up to t_sat). Limit = MPC_TILTMAX_AIR + TILT_MARGIN_DEG; None -> analyse() uses its default, which is reported as a warning."""
    tmax = dict(initial).get("MPC_TILTMAX_AIR")
    for ts_, n_, v_ in changed:
        if n_ == "MPC_TILTMAX_AIR" and ts_ <= t_sat_s * 1e6:
            tmax = v_
    if tmax is None:
        return None, None, "MPC_TILTMAX_AIR not in the log parameters: tilt limit falls back to the analyse() default (20 deg)"
    return tmax, float(tmax) + TILT_MARGIN_DEG, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import metrics
    from scenarios import SCENARIOS
    from pyulog import ULog
    run = json.load(open(os.path.join(a.run_dir, "run.json")))
    u = ULog(os.path.join(a.run_dir, "flight.ulg"))
    ev_raw = {e["name"]: e["t_us"] * 1e-6 for e in run.get("events", [])}
    gt, src = metrics.truth_local_position(u)
    am = metrics.ctrl_topic(u, "actuator_motors")
    ga = metrics.ctrl_topic(u, "vehicle_attitude_groundtruth")
    bad = [n for n, x in (("truth", gt), ("actuator_motors", am), ("attitude truth", ga)) if x is None]
    bad += [k for k in ("sat", "rec", "agg", "aghold") if k not in ev_raw]
    if bad:
        print("INVALID, missing:", bad)
        return 2
    sc = SCENARIOS[run["scenario"]]
    hold = np.asarray(run["hold_pos_ned"], float)
    sp = {k: hold + np.asarray(v) for k, v in sc["seg_pos"].items()}
    ev = dict(ev_raw)
    ev["end"] = ev_raw["aghold"] + dict((n, d) for n, d, _ in sc["segments"])["aghold"]
    t = gt["timestamp"] * 1e-6
    pos = np.column_stack([gt[k] for k in ("x", "y", "z")])
    q = metrics.qcols(ga, "q")
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))
    tg = ga["timestamp"] * 1e-6
    tilt_t = np.interp(t, tg, tilt)
    cmd = np.column_stack([am[f"control[{i}]"] for i in range(4)])
    vs = metrics.topic(u, "vehicle_status")
    tv = vs["timestamp"] * 1e-6
    w = (tv >= ev["sat"]) & (tv <= ev["end"])
    nav_ok = bool(np.all(vs["nav_state"][w] == 14)) if w.any() else True
    armed_ok = bool(np.all(vs["arming_state"][w] == 2)) if w.any() else True
    out = {"run": a.run_dir, "scenario": run["scenario"], "seed": run.get("seed"), "truth_source": src, "events_s": ev}
    tmax, tl, tilt_warn = tilt_limit_from_params(u.initial_parameters, u.changed_parameters, ev["sat"])
    out["MPC_TILTMAX_AIR"] = tmax
    out["tilt_limit_warning"] = tilt_warn
    if tilt_warn:
        print("WARNING:", tilt_warn)
    out.update(analyse(t, pos, tilt_t, am["timestamp"] * 1e-6, cmd, ev, sp, run.get("exit_status") == "ok", nav_ok, armed_ok, tl))
    for k, x in out.items():
        print(f"{k}: {x}")
    for k, x in out["verdict"].items():
        print(f"{'PASS' if x else 'FAIL'} {k}")
    print("RESULT", "INVALID" if out["invalid"] else ("PASS" if out["pass"] else "FAIL"))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=float)
    return 2 if out["invalid"] else (0 if out["pass"] else 1)


if __name__ == "__main__":
    sys.exit(main())
