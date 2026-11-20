#!/usr/bin/env python3
"""S138 G5.2 position-mode stick-step check: python3 g52_check.py RUN_DIR... -> g52_check.json per run, one PASS/FAIL line each.
Definition: indi_flight/GATES.md section 5b, "G5.2 exact test (S138 ...)". Inputs: flight.ulg, sticks.csv, run.json.
Edges come from the applied sticks (sticks.csv, sim-time base of the ULog): z step = first throttle raw != 500 and its return to 500;
x step (posctl only) = first pitch x != 0 and its return to 0. Truth = vehicle_local_position_groundtruth (NED).
Per step: start = truth at the stick edge; final = mean truth over the last 1.0 s of the centred window (window = release + 6 s,
cut at the next step edge); d = |final - start| (z: vertical, x: horizontal norm); valid needs d >= 1.0 m (z), >= 2.0 m (x).
Overshoot = max excursion beyond final along the step direction after release; settle = release to last exit of |s - d| <= 2 % d.
Off-axis (y and z during the x step; horizontal during the z step) = max |truth - start| in the off components over edge..window end, reported."""
import json
import os
import sys

import numpy as np

NAV = {"altctl": 1, "posctl": 2}                    # vehicle_status nav_state NAVIGATION_STATE_ALTCTL / POSCTL
LIM = {"z": dict(os=0.3, dmin=1.0), "x": dict(os=0.5, dmin=2.0)}   # m, GATES G5.2
SETTLE_MAX, SETTLE_BAND, REL_WIN_S, FINAL_S = 4.0, 0.02, 6.0, 1.0
LOC_TILT = 80.0


def edges(t, v, zero):
    """(t_on, t_release): first sample != zero, first return to zero after it. None if absent."""
    nz = np.flatnonzero(v != zero)
    if not len(nz):
        return None
    k = np.flatnonzero((v == zero) & (np.arange(len(v)) > nz[0]))
    return (t[nz[0]], t[k[0]]) if len(k) else None


def at(tp, p, t):
    return np.array([np.interp(t, tp, p[:, i]) for i in range(3)])


def step_metrics(kind, pos, t_on, t_rel, t_end):
    """pos: dict t, p (N x 3 NED). Returns dict of metrics for one step."""
    tp, p = pos["t"], pos["p"]
    start = at(tp, p, t_on)
    mf = (tp >= t_end - FINAL_S) & (tp <= t_end)
    final = p[mf].mean(axis=0)
    comp = [2] if kind == "z" else [0, 1]
    off = [i for i in range(3) if i not in comp]
    dv = (final - start)[comp]
    d = float(np.linalg.norm(dv))
    r = {"kind": kind, "t_on_s": float(t_on), "t_release_s": float(t_rel), "t_window_end_s": float(t_end),
         "hold_s": float(t_rel - t_on), "d_m": d, "start": start.tolist(), "final": final.tolist()}
    r["travel_at_release_m"] = float(np.linalg.norm((at(tp, p, t_rel) - start)[comp]))   # truth travel at the release edge
    lim = LIM[kind]
    r["valid"] = bool(d >= lim["dmin"])
    if d <= 0:
        r.update(overshoot_m=float("nan"), settle_s=float("nan"), off_axis_max_m=float("nan"), pass_=False)
        return r
    u = dv / d
    ma = (tp >= t_rel) & (tp <= t_end)
    s = (p[ma][:, comp] - start[comp]) @ u
    r["overshoot_m"] = float(max(0.0, s.max() - d))
    bad = np.flatnonzero(np.abs(s - d) > SETTLE_BAND * d)
    r["settle_s"] = float(tp[ma][bad[-1]] - t_rel) if len(bad) else 0.0
    me = (tp >= t_on) & (tp <= t_end)
    r["off_axis_max_m"] = float(np.abs(p[me][:, off] - start[off]).max())
    if kind == "z":   # sign: up positive (NED z negative)
        r["direction"] = "up" if dv[0] < 0 else "down"
    r["pass_overshoot"] = bool(r["overshoot_m"] <= lim["os"])
    r["pass_settle"] = bool(r["settle_s"] <= SETTLE_MAX)
    r["pass_"] = bool(r["valid"] and r["pass_overshoot"] and r["pass_settle"])
    return r


def evaluate(mode, st, pos, nav, att=None):
    """st: t, x, z (applied raw sticks, s); pos: t, p; nav: t, v; att: t, tilt_deg (optional LOC check)."""
    res = {"mode": mode, "steps": {}, "valid": True, "invalid_reason": []}
    ez = edges(st["t"], st["z"], 500)
    if ez is None:
        res.update(valid=False, passed=False)
        res["invalid_reason"].append("z stick edges not found")
        return res
    ex = edges(st["t"], st["x"], 0) if mode == "posctl" else None
    if mode == "posctl" and ex is None:
        res.update(valid=False, passed=False)
        res["invalid_reason"].append("x stick edges not found")
        return res
    z_end = ez[1] + REL_WIN_S if ex is None else min(ez[1] + REL_WIN_S, ex[0])
    res["steps"]["z"] = step_metrics("z", pos, ez[0], ez[1], z_end)
    t_last = z_end
    if ex is not None:
        res["steps"]["x"] = step_metrics("x", pos, ex[0], ex[1], ex[1] + REL_WIN_S)
        t_last = ex[1] + REL_WIN_S
    nm = (nav["t"] >= ez[0]) & (nav["t"] <= t_last)
    states = sorted({int(v) for v in nav["v"][nm]})
    res["nav_states_in_steps"] = states
    if states != [NAV[mode]]:
        res["valid"] = False
        res["invalid_reason"].append(f"nav_state {states} != [{NAV[mode]}] ({mode})")
    for k, r in res["steps"].items():
        if not r["valid"]:
            res["valid"] = False
            res["invalid_reason"].append(f"{k} step d={r['d_m']:.2f} m below {LIM[k]['dmin']} m")
        if k == "z" and r.get("direction") == "down":
            res["valid"] = False
            res["invalid_reason"].append("z step went down")
    mz = (pos["t"] >= ez[0]) & (pos["t"] <= t_last)
    res["z_up_min_m"] = float(-pos["p"][mz][:, 2].max())
    res["tilt_max_all_deg"] = float("nan")
    if att is not None:
        mt = (att["t"] >= ez[0]) & (att["t"] <= t_last)
        res["tilt_max_all_deg"] = float(att["tilt_deg"][mt].max())
    res["loc"] = bool(res["tilt_max_all_deg"] >= LOC_TILT or res["z_up_min_m"] < 0.2)
    res["passed"] = bool(res["valid"] and not res["loc"] and all(r["pass_"] for r in res["steps"].values()))
    return res


def check(d):
    from pyulog import ULog
    meta = json.load(open(os.path.join(d, "run.json")))
    mode = meta["stick"]["mode"]
    u = ULog(os.path.join(d, "flight.ulg"))
    ds = {x.name: x.data for x in u.data_list}
    sk = np.genfromtxt(os.path.join(d, "sticks.csv"), delimiter=",", names=True)
    st = {"t": sk["t_sim_us"] * 1e-6, "x": sk["x"], "z": sk["z"]}
    g = ds["vehicle_local_position_groundtruth"]
    pos = {"t": g["timestamp"] * 1e-6, "p": np.stack([g["x"], g["y"], g["z"]], axis=1)}
    v = ds["vehicle_status"]
    nav = {"t": v["timestamp"] * 1e-6, "v": v["nav_state"]}
    a = ds["vehicle_attitude_groundtruth"]
    q = np.stack([a[f"q[{k}]"] for k in range(4)], axis=1)
    att = {"t": a["timestamp"] * 1e-6, "tilt_deg": np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))}
    res = evaluate(mode, st, pos, nav, att)
    res["run"] = os.path.basename(d.rstrip("/"))
    res["truth_pos_hz"] = round(1 / float(np.median(np.diff(pos["t"]))), 1)
    res["pos_steps_meta"] = meta.get("pos_steps")
    res["params"] = {k: u.initial_parameters.get(k) for k in ("MPC_VEL_MANUAL", "MPC_POS_MODE", "MPC_Z_VEL_MAX_UP", "MPC_ACC_HOR", "MPC_JERK_MAX")}
    json.dump(res, open(os.path.join(d, "g52_check.json"), "w"), indent=1)
    return res


def line(res):
    tag = "INVALID" if not res["valid"] else ("PASS" if res["passed"] else "FAIL")
    parts = [f"{k} d {r['d_m']:.2f} os {r.get('overshoot_m', float('nan')):.3f} settle {r.get('settle_s', float('nan')):.2f} (hold {r['hold_s']:.2f} s, travel at release {r['travel_at_release_m']:.2f}) off {r.get('off_axis_max_m', float('nan')):.2f}"
             for k, r in res["steps"].items()]
    return f"{res.get('run', '?')} {res['mode']} G5.2 {tag}: " + "; ".join(parts) + f"; loc {res.get('loc')}" \
        + (f" reason {res['invalid_reason']}" if res["invalid_reason"] else "")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(line(check(d)))
