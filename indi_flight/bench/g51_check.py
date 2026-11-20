#!/usr/bin/env python3
"""S136 G5.1 flight-mode stick-step check: python3 g51_check.py RUN_DIR... -> g51_check.json per run, one PASS/FAIL line each.
Definition: indi_flight/GATES.md section 5b, "G5.1 exact test (S136 ...)". Inputs: flight.ulg, sticks.csv, run.json.
Edges come from the applied sticks (sticks.csv, same sim-time base as the ULog), not from the scenario.
Sign conventions (PX4 mavlink_receiver / mc_indi_rate_control): MANUAL_CONTROL y = roll stick, x = pitch stick, r = yaw stick;
acro rate setpoint (FRD body) = (roll, -pitch, yaw) stick/1000 x (MC_ACRO_R_MAX, P_MAX, Y_MAX), so pitch stick forward (+x) commands
a negative pitch rate. Truth rates: vehicle_angular_velocity_groundtruth xyz (FRD, rad/s)."""
import json
import os
import sys

import numpy as np

AXES = (("roll", "y", 0, +1.0, "MC_ACRO_R_MAX"), ("pitch", "x", 1, -1.0, "MC_ACRO_P_MAX"), ("yaw", "r", 2, +1.0, "MC_ACRO_Y_MAX"))
NAV = {"acro": 10, "stabilized": 15}
RMS_MAX, TILT_MAX, YAWR_MAX, LOC_TILT = 10.0, 3.0, 10.0, 80.0   # deg/s, deg, deg/s, deg (GATES G5.1)
SKIP_S, ZERO_PLATEAU_S = 0.1, 1.0
REL_LO, REL_HI = 1.0, 2.5


def stick_edges(t, v):
    """(t_plus, t_minus, t_release) in the units of t: first nonzero, first sign flip after it, first return to zero after that."""
    nz = np.flatnonzero(v != 0)
    if not len(nz):
        return None
    i1 = nz[0]
    s = np.sign(v[i1])
    j = np.flatnonzero((np.sign(v) == -s) & (np.arange(len(v)) > i1))
    if not len(j):
        return None
    k = np.flatnonzero((v == 0) & (np.arange(len(v)) > j[0]))
    if not len(k):
        return None
    return t[i1], t[j[0]], t[k[0]]


def held(ts, vs, t):
    """Zero-order hold of the applied stick samples at times t."""
    return vs[np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 1)]


def tilt_deg(q):
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))


def rise_overshoot(t, w, cmd, t_edge, t_end):
    """Rise time to 90 % of the plateau command (nan if never) and peak overshoot [deg/s] beyond it, edge to t_end."""
    m = (t >= t_edge) & (t < t_end)
    c = cmd[m][-1] if m.any() else 0.0
    if c == 0 or not m.any():
        return float("nan"), float("nan")
    y = w[m] * np.sign(c)
    ca = abs(c)
    hit = np.flatnonzero(y >= 0.9 * ca)
    return (float(t[m][hit[0]] - t_edge) if len(hit) else float("nan")), float(max(0.0, y.max() - ca))


def evaluate(mode, st, tr, att, zup, nav, maxr):
    """st: dict t,x,y,r (applied sticks, seconds); tr: dict t, w (N x 3 truth rates rad/s); att: dict t, tilt_deg;
    zup: dict t, z (truth height); nav: dict t, v (nav_state); maxr: {param: deg/s}. Returns the result dict (pass / valid / metrics)."""
    res = {"mode": mode, "axes": {}, "valid": True, "invalid_reason": []}
    wd = np.degrees(tr["w"])
    ed = {a[0]: stick_edges(st["t"], st[a[1]]) for a in AXES}
    if any(e is None for e in ed.values()):
        res["valid"] = False
        res["invalid_reason"].append("stick edges not found in sticks.csv")
        res["pass"] = False
        return res
    t0, t1 = ed["roll"][0], ed["yaw"][2] + REL_HI
    nm = (nav["t"] >= t0) & (nav["t"] <= t1)
    states = sorted({int(x) for x in nav["v"][nm]})
    res["nav_states_in_steps"] = states
    if states != [NAV[mode]]:
        res["valid"] = False
        res["invalid_reason"].append(f"nav_state {states} != [{NAV[mode]}] ({mode})")
    ok = True
    for name, field, ix, sgn, par in AXES:
        e1, e2, e3 = ed[name]
        mx = maxr[par]
        r = {"edges_s": [e1, e2, e3], "stick_amp": float(np.max(np.abs(st[field])))}
        if mode == "acro":
            wins = [(e1 + SKIP_S, e2), (e2 + SKIP_S, e3), (e3 + SKIP_S, e3 + ZERO_PLATEAU_S)]
            err, off = [], []
            for a, b in wins:
                m = (tr["t"] >= a) & (tr["t"] < b)   # right end exclusive: the edge sample already holds the next command
                cmd = sgn * held(st["t"], st[field], tr["t"][m]) / 1000.0 * mx
                err.append(wd[m, ix] - cmd)
                for _, _, jx, _, _ in AXES:
                    if jx != ix:
                        off.append(wd[m, jx])
            e = np.concatenate(err)
            r["rms_deg_s"] = float(np.sqrt(np.mean(e ** 2)))
            r["off_axis_rms_deg_s"] = float(np.sqrt(np.mean(np.concatenate(off) ** 2)))
            cmd_all = sgn * held(st["t"], st[field], tr["t"]) / 1000.0 * mx
            rt, ov = [], []
            for a, b in ((e1, e2), (e2, e3)):
                x, y = rise_overshoot(tr["t"], wd[:, ix], cmd_all, a, b)
                rt.append(x)
                ov.append(y)
            r["rise_s"], r["overshoot_deg_s"] = rt, ov
            r["pass"] = bool(r["rms_deg_s"] <= RMS_MAX)
        else:
            m = (att["t"] >= e3 + REL_LO) & (att["t"] <= e3 + REL_HI)
            r["tilt_max_deg"] = float(att["tilt_deg"][m].max()) if m.any() else float("nan")
            r["pass"] = bool(r["tilt_max_deg"] <= TILT_MAX)
            if name == "yaw":
                mw = (tr["t"] >= e3 + REL_LO) & (tr["t"] <= e3 + REL_HI)
                r["yaw_rate_max_deg_s"] = float(np.abs(wd[mw, 2]).max()) if mw.any() else float("nan")
                r["pass"] = bool(r["pass"] and r["yaw_rate_max_deg_s"] <= YAWR_MAX)
        ok &= r["pass"]
        res["axes"][name] = r
    mt = (att["t"] >= t0) & (att["t"] <= t1)
    mz = (zup["t"] >= t0) & (zup["t"] <= t1)
    res["tilt_max_all_deg"] = float(att["tilt_deg"][mt].max())
    res["z_up_min_m"] = float(zup["z"][mz].min())
    res["loc"] = bool(res["tilt_max_all_deg"] >= LOC_TILT or res["z_up_min_m"] < 0.2)
    res["pass"] = bool(ok and not res["loc"] and res["valid"])
    return res


def check(d):
    from pyulog import ULog
    meta = json.load(open(os.path.join(d, "run.json")))
    mode = meta["stick"]["mode"]
    u = ULog(os.path.join(d, "flight.ulg"))
    ds = {x.name: x.data for x in u.data_list}
    sk = np.genfromtxt(os.path.join(d, "sticks.csv"), delimiter=",", names=True)
    st = {"t": sk["t_sim_us"] * 1e-6, "x": sk["x"], "y": sk["y"], "r": sk["r"]}
    g = ds["vehicle_angular_velocity_groundtruth"]
    tr = {"t": g["timestamp"] * 1e-6, "w": np.stack([g[f"xyz[{i}]"] for i in range(3)], axis=1)}
    a = ds["vehicle_attitude_groundtruth"]
    att = {"t": a["timestamp"] * 1e-6, "tilt_deg": tilt_deg(np.stack([a[f"q[{k}]"] for k in range(4)], axis=1))}
    p = ds["vehicle_local_position_groundtruth"]
    zup = {"t": p["timestamp"] * 1e-6, "z": -p["z"]}
    v = ds["vehicle_status"]
    nav = {"t": v["timestamp"] * 1e-6, "v": v["nav_state"]}
    maxr = {k: u.initial_parameters.get(k) for k in ("MC_ACRO_R_MAX", "MC_ACRO_P_MAX", "MC_ACRO_Y_MAX")}
    res = evaluate(mode, st, tr, att, zup, nav, maxr)
    res["run"] = os.path.basename(d.rstrip("/"))
    res["params"] = {k: u.initial_parameters.get(k) for k in ("MC_ACRO_R_MAX", "MC_ACRO_P_MAX", "MC_ACRO_Y_MAX", "MC_ACRO_EXPO", "MC_ACRO_SUPEXPO",
                                                             "MPC_MAN_TILT_MAX", "MPC_MAN_Y_MAX")}
    gt_dt = float(np.median(np.diff(tr["t"])))
    res["truth_rate_hz"] = round(1 / gt_dt, 1)
    res["truth_att_hz"] = round(1 / float(np.median(np.diff(att["t"]))), 1)
    mc = ds["manual_control_setpoint"]
    res["manual_control_setpoint_samples"] = int(len(mc["timestamp"]))
    res["manual_control_max_abs"] = {k: float(np.abs(mc[k]).max()) for k in ("roll", "pitch", "yaw") if k in mc}
    json.dump(res, open(os.path.join(d, "g51_check.json"), "w"), indent=1)
    return res


def line(res):
    tag = "INVALID" if not res["valid"] else ("PASS" if res["pass"] else "FAIL")
    parts = []
    for n, r in res["axes"].items():
        if "rms_deg_s" in r:
            parts.append(f"{n} rms {r['rms_deg_s']:.2f} (off {r['off_axis_rms_deg_s']:.1f})")
        else:
            parts.append(f"{n} tilt {r['tilt_max_deg']:.2f}" + (f" yawrate {r['yaw_rate_max_deg_s']:.2f}" if "yaw_rate_max_deg_s" in r else ""))
    return f"{res.get('run', '?')} {res['mode']} G5.1 {tag}: " + "; ".join(parts) + f"; tilt max {res.get('tilt_max_all_deg', float('nan')):.1f} loc {res.get('loc')}" \
        + (f" reason {res['invalid_reason']}" if res["invalid_reason"] else "")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(line(check(d)))
