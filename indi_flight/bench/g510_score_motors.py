#!/usr/bin/env python3
"""G5.10 key 1: motor saturation + limits, SAT part (sat_sustained) and STABILIZED full-scale part (g510_stab_full).

  g510_score_motors.py RUN_DIR [RUN_DIR ...] [--json OUT]   (scenario read from run.json; needs flight.ulg + run.json)

Spec: GATES.md row G5.10, Q9 (S175) and Owner amendments S180 Q17 A.
Definitions
  LOC (loss of control) = truth height above ground < 0.3 m at any sample from the window start while NOT in a landing
        phase (a landing phase starts at a run.json event whose name starts with "land"; none in these scenarios),
        or truth tilt > 90 deg. run.json exit_status is NOT used (a landing timeout long after the window is not a LOC).
        A log that ends before the check span is covered is not rewarded: a crash/abort shows up as LOC through truth.
  Windows: SAT  = [sat, sat + dur] (events "sat"); checks span to sat end + 5 s (log end if shorter).
           STAB = [full, full + dur] (event "full"); checks span to rec + 9 s (log end if no "rec" event).
  Saturated = actuator_motors command >= 0.99; reported s with all 4 and with any motor, sample i held to sample i+1.
  SAT checks: no LOC; tilt max <= MPC_TILTMAX_AIR + 5 deg; altitude loss <= 2.0 m (truth, vs median of the 1 s before);
        recovery = 3D truth within 0.3 m of hold_pos_ned and staying so, <= 5 s after the window end (log must cover
        it); motors: all-4 saturated fraction of the window >= SAT_MIN_FRAC (assumed 0.5, spec gives no figure).
  STAB checks (Q17 A): no LOC; tilt max <= MPC_MAN_TILT_MAX + 5 deg; no altitude-loss limit; recovery = attitude error
        (truth vs q_d of vehicle_attitude_setpoint, quaternion angle) <= 5 deg and staying so from <= 1 s after stick
        centre (first manual_control_setpoint sample after the last non-zero roll/pitch/throttle stick).
Time base: timestamp_sample where logged (metrics.tstamp), else timestamp; decimated topics are evaluated only at their own
samples, truth is interpolated to them (no zero-order hold). Parameters are read from the log.
"""
import json, os, sys
import numpy as np

SAT_THR = 0.99
SAT_MIN_FRAC = 0.5
LOC_H, LOC_TILT = 0.3, 90.0


def tilt_deg(q):
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))


def quat_angle_deg(a, b):
    return np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(a * b, axis=1)), 0, 1)))


def interp_q(tq, q, tt):
    q = q.copy()
    for i in range(1, len(q)):
        if np.dot(q[i], q[i - 1]) < 0:
            q[i] = -q[i]
    o = np.column_stack([np.interp(tt, tq, q[:, k]) for k in range(4)])
    return o / np.linalg.norm(o, axis=1, keepdims=True)


def sat_time(t, m, t0, t1, mode):
    f = (m >= SAT_THR).all(axis=1) if mode == "all" else (m >= SAT_THR).any(axis=1)
    dt = np.clip(t[1:], t0, t1) - np.clip(t[:-1], t0, t1)
    return float(dt[f[:-1]].sum()), float(dt.sum())


def stays_from(t, ok, t_ref):
    """Seconds after t_ref from which ok holds to the end of the data; None if never / ok False at the last sample."""
    i = np.where(t >= t_ref)[0]
    if len(i) == 0:
        return None
    t, ok = t[i], ok[i]
    bad = np.where(~ok)[0]
    if len(bad) == 0:
        return 0.0
    return None if bad[-1] == len(t) - 1 else float(t[bad[-1] + 1] - t_ref)


def score(D):
    """D: dict with kind ('sat'|'stab'), events {name: (t_s, dur_s)}, params, tm, M, tg, qg, tp, z_up (height, up positive),
    pos_ned (n,3) or None, hold (3,) or None, stick (tc, busy) or None, sp (ts, qd) or None, exit_status."""
    kind, ev, P = D["kind"], D["events"], D["params"]
    tm, M, tg, qg, tp = D["tm"], D["M"], D["tg"], D["qg"], D["tp"]
    log_end = float(max(tm[-1], tg[-1], tp[-1]))
    key = "sat" if kind == "sat" else "full"
    out = {"kind": kind, "exit_status": D.get("exit_status"), "log_end_s": log_end}
    if key not in ev:
        out.update(loc=True, error=f"no '{key}' event", passed=False)
        return out
    t0 = ev[key][0]
    t1 = t0 + ev[key][1]
    if kind == "sat":
        tend = t1 + 5.0
        pname, lim = "MPC_TILTMAX_AIR", None
    else:
        tend = ev["rec"][0] + 9.0 if "rec" in ev else log_end
        pname, lim = "MPC_MAN_TILT_MAX", None
    if P.get(pname) is not None:
        lim = P[pname] + 5.0
    land = [v[0] for k, v in ev.items() if k.startswith("land")]
    out.update(window_s=[t0, t1], span_end_s=min(tend, log_end), tilt_param=pname, tilt_limit_deg=lim)
    out["covered_span"] = bool(log_end >= tend - 1e-3)
    out["s_all4_ge_0.99"], cov = sat_time(tm, M, t0, t1, "all")
    out["s_any_ge_0.99"], _ = sat_time(tm, M, t0, t1, "any")
    out["window_len_s"], out["window_covered_s"] = t1 - t0, cov
    out["frac_all4_ge_0.99"] = out["s_all4_ge_0.99"] / (t1 - t0)
    w = (tg >= t0) & (tg <= tend)
    tilt = tilt_deg(qg[w]) if w.any() else np.array([])
    out["tilt_max_deg"] = float(tilt.max()) if len(tilt) else None
    wp = (tp >= t0) & (tp <= tend)
    h = D["z_up"][wp]
    tpw = tp[wp]
    notland = np.ones(len(tpw), bool)
    if land:
        notland = tpw < min(land)
    crash = bool(((h < LOC_H) & notland).any())
    out["height_min_m"] = float(h.min()) if len(h) else None
    out["crash_t_s"] = float(tpw[(h < LOC_H) & notland][0]) if crash else None
    out["loc"] = bool(crash or (len(tilt) and tilt.max() > LOC_TILT) or not len(tilt) or not len(h))
    pre = (tp >= t0 - 1.0) & (tp < t0)
    z0 = float(np.median(D["z_up"][pre])) if pre.any() else None
    if z0 is not None and len(h):
        out["alt_loss_m"] = float(max(0.0, z0 - h.min()))
        out["alt_gain_max_m"] = float(max(0.0, h.max() - z0))
    else:
        out["alt_loss_m"] = out["alt_gain_max_m"] = None
    tilt_ok = lim is not None and out["tilt_max_deg"] is not None and out["tilt_max_deg"] <= lim
    out["tilt_ok"] = bool(tilt_ok)
    if kind == "sat":
        pos, hold = D["pos_ned"], D["hold"]
        rec = None
        wr = tp >= t1
        if hold is not None and wr.any() and out["covered_span"]:
            dev = np.linalg.norm(pos[wr] - np.asarray(hold), axis=1)
            rec = stays_from(tp[wr], dev <= 0.3, t1)
        out["recovery_s"] = rec
        out["recovery_ok"] = bool(rec is not None and rec <= 5.0)
        out["alt_ok"] = bool(out["alt_loss_m"] is not None and out["alt_loss_m"] <= 2.0)
        out["motors_ok"] = bool(out["frac_all4_ge_0.99"] >= SAT_MIN_FRAC)
        out["passed"] = bool(not out["loc"] and out["tilt_ok"] and out["alt_ok"] and out["recovery_ok"] and out["motors_ok"])
    else:
        rec = None
        st, sp = D["stick"], D["sp"]
        if st is not None and sp is not None and len(sp[0]):
            tc, busy = st
            b = np.where(busy & (tc >= t0 - 0.5) & (tc <= tend))[0]
            if len(b) and b[-1] + 1 < len(tc):
                t_c = float(tc[b[-1] + 1])
                out["t_centre_s"] = t_c
                ts, qd = sp
                ws = (ts >= t0) & (ts <= min(tend, tg[-1])) & (ts >= tg[0])
                if ws.any():
                    err = quat_angle_deg(interp_q(tg, qg, ts[ws]), qd[ws])
                    rec = stays_from(ts[ws], err <= 5.0, t_c)
                    out["att_err_max_deg"] = float(err.max())
        out["recovery_s"] = rec
        out["recovery_ok"] = bool(rec is not None and rec <= 1.0)
        out["passed"] = bool(not out["loc"] and out["tilt_ok"] and out["recovery_ok"])
    return out


def load(d):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import metrics
    from pyulog import ULog
    run = json.load(open(os.path.join(d, "run.json")))
    u = ULog(os.path.join(d, "flight.ulg"))
    P = dict(u.initial_parameters)
    ctrl = metrics.ctrl_topic
    am = ctrl(u, "actuator_motors")
    ga = ctrl(u, "vehicle_attitude_groundtruth")
    gt, _ = metrics.truth_local_position(u)
    sp = ctrl(u, "vehicle_attitude_setpoint")
    mc = ctrl(u, "manual_control_setpoint")
    kind = "stab" if run["scenario"].startswith("g510_stab") else "sat"
    pos = np.column_stack([gt["x"], gt["y"], gt["z"]])
    D = dict(kind=kind, events={e["name"]: (e["t_us"] * 1e-6, float(e.get("dur_s", 0.0))) for e in run["events"]},
             params=P, tm=am["timestamp"] * 1e-6, M=np.column_stack([am[f"control[{i}]"] for i in range(4)]),
             tg=ga["timestamp"] * 1e-6, qg=metrics.qcols(ga, "q"), tp=gt["timestamp"] * 1e-6, z_up=-gt["z"], pos_ned=pos,
             hold=run.get("hold_pos_ned"), exit_status=run.get("exit_status"), stick=None, sp=None)
    if mc is not None:
        busy = (np.abs(mc["roll"]) > 0.02) | (np.abs(mc["pitch"]) > 0.02) | (np.abs(mc["throttle"]) > 0.02)
        D["stick"] = (mc["timestamp"] * 1e-6, busy)
    if sp is not None:
        D["sp"] = (sp["timestamp"] * 1e-6, metrics.qcols(sp, "q_d"))
    return D


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--json"]
    jo = None
    if "--json" in sys.argv:
        jo = sys.argv[sys.argv.index("--json") + 1]
        args.remove(jo)
    res = {}
    for d in args:
        res[d] = score(load(d))
        print(d)
        for k, v in res[d].items():
            print(f"  {k}: {v}")
    if jo:
        json.dump(res, open(jo, "w"), indent=1)
