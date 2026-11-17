#!/usr/bin/env python3
"""S70 thrust-gap check on one position-mode run (scenario s5_gap085 / s5_loss08).

Usage: s5_gap_check.py RUN_DIR [--out FILE.json]     (RUN_DIR holds flight.ulg and run.json)

z error = simulator truth z (NED, truth_local_position) minus run.json hold_pos_ned[2]; positive = below the hold point.
Event time = start of segment "up" as applied by the runner: run.json events[name=="up"].t_us (logged after the
SIM_GZ_EC_* writes returned; sim time = ULog time base). run.json motor_fault.event_us / event_done_us are echoed.
Reports mean/std of the z error in [event+10, event+20] s and in the last 10 s of the log's hold, max |z dev| after
the event, mean |vehicle_thrust_setpoint| before ([event-10, event]) and after (same last-10 s window), the params
MPC_Z_P / MPC_Z_VEL_P_ACC / MPC_USE_HTE from the log, the prediction (1-s) g / (Z_P Z_VEL_P_ACC) (valid for stock
mc_pos_control with the hover-thrust estimator off), and for the INDI run the "INDI stage cond" log messages and
the indi_pos_status mean_u_valid fraction after the event.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as M  # noqa: E402

G = 9.80665


def stats(t_s, v, lo, hi):
    m = (t_s >= lo) & (t_s <= hi) & np.isfinite(v)
    if not m.any():
        return {"mean": None, "std": None, "n": 0}
    return {"mean": float(np.mean(v[m])), "std": float(np.std(v[m])), "n": int(m.sum())}


def analyze(t_truth_us, z_truth, hold_z, event_us, t_thr_us, thr_norm, params, end_us=None, scale=None):
    """Pure computation. Times in us (ULog base), z NED [m]. end_us = end of the hold (default last truth sample)."""
    tt = np.asarray(t_truth_us, float) * 1e-6
    ev = event_us * 1e-6
    end = (end_us if end_us is not None else t_truth_us[-1]) * 1e-6
    err = np.asarray(z_truth, float) - hold_z
    after = tt >= ev
    out = {"event_s": ev, "end_s": end, "hold_z": hold_z,
           "z_err_ev10_20": stats(tt, err, ev + 10, ev + 20),
           "z_err_last10": stats(tt, err, end - 10, end),
           "max_abs_z_dev_after": float(np.max(np.abs(err[after & (tt <= end)]))) if after.any() else None,
           "z_err_before": stats(tt, err, ev - 5, ev - 1e-6)}
    tp = np.asarray(t_thr_us, float) * 1e-6
    th = np.asarray(thr_norm, float)
    out["thrust_before"] = stats(tp, th, ev - 10, ev - 1e-6)["mean"]
    out["thrust_after_last10"] = stats(tp, th, end - 10, end)["mean"]
    zp, za, hte = params.get("MPC_Z_P"), params.get("MPC_Z_VEL_P_ACC"), params.get("MPC_USE_HTE")
    out["params"] = {"MPC_Z_P": zp, "MPC_Z_VEL_P_ACC": za, "MPC_USE_HTE": hte,
                     "HTE_HT_ERR_INIT": params.get("HTE_HT_ERR_INIT"), "HTE_HT_NOISE": params.get("HTE_HT_NOISE")}
    out["thrust_scale"] = scale
    out["prediction_m"] = (1.0 - scale) * G / (zp * za) if scale is not None and zp and za else None
    return out


def _collective_scale(mf, n_rotors=4):
    """Collective thrust scale of a motor_fault: the mean over all rotors (one motor at s gives 1 - (1 - s) / 4)."""
    s = mf.get("thrust_scale")
    if s is None:
        return None
    motors = mf.get("motors", [mf["motor"]] if "motor" in mf else list(range(n_rotors)))
    return 1.0 - len(motors) * (1.0 - float(s)) / n_rotors


def main(argv):
    from pyulog import ULog
    run = argv[1]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(run, "gap_check.json")
    meta = json.load(open(os.path.join(run, "run.json")))
    ul = ULog(os.path.join(run, "flight.ulg"))
    ev = [e for e in meta["events"] if e["name"] == "up"][0]
    mf = meta.get("motor_fault", {})
    tr, src = M.truth_local_position(ul)
    thr = M.topic(ul, "vehicle_thrust_setpoint")
    thr_n = np.linalg.norm(np.stack([thr["xyz[0]"], thr["xyz[1]"], thr["xyz[2]"]], 1), axis=1)
    params = {k: ul.initial_parameters.get(k) for k in ("MPC_Z_P", "MPC_Z_VEL_P_ACC", "MPC_USE_HTE", "HTE_HT_ERR_INIT", "HTE_HT_NOISE", "MC_INDI_W_MAX",
                                                        "MC_INDI_POS_EN", "MC_INDI_EN")}
    for _, n, v in ul.changed_parameters:  # last value wins
        if n in params:
            params[n] = v
    seg_end = ev["t_us"] + int((ev["dur_s"] + [e for e in meta["events"] if e["name"] == "hold"][0]["dur_s"]) * 1e6)
    end_us = min(int(tr["timestamp"][-1]), seg_end)
    res = analyze(tr["timestamp"], tr["z"], meta["hold_pos_ned"][2], ev["t_us"], thr["timestamp"], thr_n, params,
                  end_us=end_us, scale=_collective_scale(mf))
    h = M.topic(ul, "hover_thrust_estimate")  # MPC_USE_HTE does not exist in this build: HTE is always on, estimate logged instead
    if h is not None:
        th = h["timestamp"] * 1e-6
        res["hte_estimate"] = {"at_event": float(h["hover_thrust"][max(np.searchsorted(th, ev["t_us"] * 1e-6) - 1, 0)]),
                               "at_end": float(h["hover_thrust"][max(np.searchsorted(th, end_us * 1e-6) - 1, 0)])}
    res.update({"run": run, "truth_source": src, "event_t_us": ev["t_us"],
                "motor_fault_event_us": mf.get("event_us"), "motor_fault_event_done_us": mf.get("event_done_us"),
                "motors": mf.get("motors", [mf.get("motor")])})
    conds = [(m.timestamp * 1e-6, m.message) for m in ul.logged_messages if "INDI stage cond" in m.message]
    res["indi_stage_msgs"] = [f"{t:.1f}s {m}" for t, m in conds][-6:]
    st = M.topic(ul, "indi_pos_status")
    if st is not None and len(st["timestamp"]):
        a = st["timestamp"] >= ev["t_us"]
        res["indi_pos_status"] = {"n": int(len(st["timestamp"])),
                                  "mean_u_valid_frac_after": float(np.mean(st["mean_u_valid"][a])) if a.any() else None,
                                  "mean_u_after": float(np.nanmean(st["mean_u"][a])) if a.any() else None,
                                  "thrust_after": float(np.mean(st["thrust"][a])) if a.any() else None}
    else:
        res["indi_pos_status"] = None
    json.dump(res, open(out_path, "w"), indent=1)
    z1, z2 = res["z_err_ev10_20"], res["z_err_last10"]
    print(f"{run}: event {res['event_s']:.2f}s HTE={params['MPC_USE_HTE']} Z_P={params['MPC_Z_P']} ACC={params['MPC_Z_VEL_P_ACC']}")
    print(f"  z err [ev+10,ev+20] mean {z1['mean']:.3f} std {z1['std']:.3f} m; last10 mean {z2['mean']:.3f} std {z2['std']:.3f} m;"
          f" max|dev| {res['max_abs_z_dev_after']:.3f} m; predicted {res['prediction_m']}")
    print(f"  HTE estimate {res.get('hte_estimate')}")
    print(f"  thrust before {res['thrust_before']:.4f} after {res['thrust_after_last10']:.4f}; indi_pos_status {res['indi_pos_status']}")
    print("  stage:", res["indi_stage_msgs"][-3:])


if __name__ == "__main__":
    main(sys.argv)
