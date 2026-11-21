#!/usr/bin/env python3
"""G5.10 sustained-saturation metrics, independent second key (key2).

Time bases: actuator_motors, vehicle_attitude_groundtruth, vehicle_local_position_groundtruth,
manual_control_setpoint use timestamp_sample; vehicle_attitude_setpoint has no timestamp_sample, so
its timestamp is used. No zero-order hold of a decimated topic: the 46 Hz stick topic and the
89 Hz setpoint are only evaluated at their own samples; the 690 Hz truth is interpolated to them.
"""
import json
import os
import sys

import numpy as np

SAT_THR = 0.99


def sat_time(t, m, t0, t1, thr=SAT_THR, mode="all"):
    """Saturated time in [t0,t1] [s]. Sample i holds for [t_i, t_{i+1}) (native 800 Hz motor stream).
    m: (n,k). mode 'all': every motor >= thr; 'any': at least one.
    Returns (total_s, longest_continuous_s, covered_s)."""
    t = np.asarray(t, float)
    m = np.asarray(m, float)
    f = (m >= thr).all(axis=1) if mode == "all" else (m >= thr).any(axis=1)
    a = np.clip(t[:-1], t0, t1)
    b = np.clip(t[1:], t0, t1)
    dt = b - a
    fs = f[:-1]
    total = float(dt[fs].sum())
    covered = float(dt.sum())
    best = cur = 0.0
    for d, s in zip(dt, fs):
        if s:
            cur += d
            best = max(best, cur)
        else:
            cur = 0.0
    return total, best, covered


def att_recovery(t, err_deg, t_c, lim=5.0):
    """First time (rel. to t_c) at/after t_c where err<=lim and stays <=lim to the end of data.
    Also returns first-reach time. (stays_s, first_s); None if never."""
    t = np.asarray(t, float)
    e = np.asarray(err_deg, float)
    idx = np.where(t >= t_c)[0]
    if len(idx) == 0:
        return None, None
    t = t[idx]
    e = e[idx]
    ok = e <= lim
    first = float(t[np.argmax(ok)] - t_c) if ok.any() else None
    bad = np.where(~ok)[0]
    if len(bad) == 0:
        stay = 0.0 if first is not None else None
    elif bad[-1] == len(t) - 1:
        stay = None
    else:
        stay = float(t[bad[-1] + 1] - t_c)
    return stay, first


def quat_angle_deg(q1, q2):
    d = np.abs(np.sum(q1 * q2, axis=1)).clip(0, 1)
    return np.degrees(2 * np.arccos(d))


def tilt_deg(q):
    # body z axis down component of R(q): R33 = 1 - 2(x^2+y^2)
    r33 = 1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)
    return np.degrees(np.arccos(np.clip(r33, -1, 1)))


def interp_q(tq, q, tt):
    out = np.empty((len(tt), 4))
    for k in range(4):
        out[:, k] = np.interp(tt, tq, q[:, k])
    # sign continuity assumed (truth is smooth, 1.4 ms spacing); renormalise
    return out / np.linalg.norm(out, axis=1, keepdims=True)


def load(flight):
    from pyulog import ULog
    names = ["actuator_motors", "vehicle_attitude_groundtruth", "vehicle_local_position_groundtruth",
             "vehicle_local_position", "vehicle_attitude_setpoint", "manual_control_setpoint"]
    u = ULog(os.path.join(flight, "flight.ulg"), message_name_filter_list=names)
    P = dict(u.initial_parameters)
    for ts, name, val in (u.changed_parameters or []):
        P[name] = val  # last value; no change expected in these flights
    D = {d.name: d.data for d in u.data_list}
    return D, P


def analyse(flight):
    run = json.load(open(os.path.join(flight, "run.json")))
    D, P = load(flight)
    ev = {e["name"]: e for e in run["events"]}
    stab = run["scenario"].startswith("g510_stab")
    r = {"flight": os.path.basename(flight.rstrip("/")), "scenario": run["scenario"],
         "log_end_s": D["actuator_motors"]["timestamp_sample"][-1] / 1e6}
    tm = D["actuator_motors"]["timestamp_sample"] / 1e6
    M = np.stack([D["actuator_motors"]["control[%d]" % i] for i in range(4)], 1)
    gt = D["vehicle_attitude_groundtruth"]
    tg = gt["timestamp_sample"] / 1e6
    qg = np.stack([gt["q[%d]" % i] for i in range(4)], 1)
    lp = D["vehicle_local_position_groundtruth"]
    tl = lp["timestamp_sample"] / 1e6
    pos = np.stack([lp["x"], lp["y"], lp["z"]], 1)
    if stab:
        t0 = ev["full"]["t_us"] / 1e6
        t1 = t0 + ev["full"]["dur_s"]
        tend = (ev["rec"]["t_us"] + 9e6) / 1e6
        lim = P["MPC_MAN_TILT_MAX"] + 5
        r["tilt_limit_deg"] = lim
    else:
        t0 = ev["sat"]["t_us"] / 1e6
        t1 = t0 + ev["sat"]["dur_s"]
        tend = t1 + 5.0
        lim = P["MPC_TILTMAX_AIR"] + 5
        r["tilt_limit_deg"] = lim
    r.update(t_start=t0, t_end=t1)
    r["sat_all_s"], r["sat_all_longest_s"], cov = sat_time(tm, M, t0, t1, mode="all")
    r["sat_any_s"], r["sat_any_longest_s"], _ = sat_time(tm, M, t0, t1, mode="any")
    r["sat_covered_s"] = cov
    r["sat_phase_s"] = t1 - t0
    r["motor_mean_in_phase"] = float(M[(tm >= t0) & (tm <= min(t1, tm[-1]))].mean())
    # tilt (truth) from phase start to tend or log end
    w = (tg >= t0) & (tg <= tend)
    tl_ = tilt_deg(qg[w])
    r["tilt_max_deg"] = float(tl_.max())
    r["tilt_ok"] = bool(tl_.max() <= lim)
    # altitude (truth, NED z): loss = max(z - z0), z0 median over 1 s before phase start
    z0 = np.median(pos[(tl >= t0 - 1) & (tl < t0), 2])
    wl = (tl >= t0) & (tl <= tend)
    r["alt_hold_m"] = float(-z0)
    r["alt_loss_max_m"] = float(max(0.0, (pos[wl, 2] - z0).max()))
    r["alt_gain_max_m"] = float(max(0.0, (z0 - pos[wl, 2]).max()))
    r["height_min_m"] = float(-pos[wl, 2].max())
    # loss of control: truth height < 0.3 m after phase start, or tilt > 90 deg
    crash = bool((-pos[wl, 2] < 0.3).any())
    r["loc"] = bool(crash or (tl_ > 90).any())
    r["crash_t_s"] = float(tl[wl][np.argmax(-pos[wl, 2] < 0.3)]) if crash else None
    if stab:
        mc = D["manual_control_setpoint"]
        tc = mc["timestamp_sample"] / 1e6
        busy = (np.abs(mc["roll"]) > 0.02) | (np.abs(mc["pitch"]) > 0.02) | (np.abs(mc["throttle"]) > 0.02)
        i_last = np.where(busy & (tc >= t0 - 0.5) & (tc <= tend))[0][-1]
        t_c = float(tc[i_last + 1])
        r["t_centre_s"] = t_c
        r["stick_full_s"] = float(tc[i_last + 1] - tc[np.where(busy & (tc >= t0 - 0.5))[0][0]])
        sp = D["vehicle_attitude_setpoint"]
        ts = sp["timestamp"] / 1e6
        qd = np.stack([sp["q_d[%d]" % i] for i in range(4)], 1)
        ws = (ts >= t0) & (ts <= tend)
        err = quat_angle_deg(interp_q(tg, qg, ts[ws]), qd[ws])
        stay, first = att_recovery(ts[ws], err, t_c)
        r["att_err_first_le5_s"] = first
        r["att_err_stays_le5_from_s"] = stay
        r["att_err_at_1s_deg"] = float(np.interp(t_c + 1.0, ts[ws], err))
        r["att_err_max_after_1s_deg"] = float(err[ts[ws] >= t_c + 1.0].max()) if (ts[ws] >= t_c + 1).any() else None
        r["att_err_max_deg"] = float(err.max())
        # the setpoint jumps to level at stick centre, so 'first' can be 0 on a pre-jump sample:
        # the criterion uses the time from which the error stays <= 5 deg
        r["att_ok"] = bool(stay is not None and stay <= 1.0)
        r["pass_q17"] = bool((not r["loc"]) and r["tilt_ok"] and r["att_ok"])
    else:
        hold = np.array(run["hold_pos_ned"])
        # recovery: after phase end, first time the 3D truth deviation to hold is <=0.3 m and stays so
        wr = (tl >= t1)
        if wr.any() and tl[-1] >= t1:
            dev = np.linalg.norm(pos[wr] - hold, axis=1)
            tt = tl[wr]
            ok = dev <= 0.3
            bad = np.where(~ok)[0]
            if len(bad) == 0:
                rec = 0.0
            elif bad[-1] == len(tt) - 1:
                rec = None
            else:
                rec = float(tt[bad[-1] + 1] - t1)
            r["recovery_s"] = rec
        else:
            r["recovery_s"] = None
        r["recovery_ok"] = bool(r["recovery_s"] is not None and r["recovery_s"] <= 5.0 and tl[-1] >= t1 + 5.0)
        r["pass_g510_sat"] = bool((not r["loc"]) and r["tilt_ok"] and r["alt_loss_max_m"] <= 2.0 and r["recovery_ok"])
    return r


if __name__ == "__main__":
    out = [analyse(p) for p in sys.argv[1:]]
    print(json.dumps(out, indent=1))
