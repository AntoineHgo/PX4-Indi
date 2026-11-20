#!/usr/bin/env python3
"""S139 G5.7 mode-switch check: python3 g57_check.py RUN_DIR... -> g57_check.json per run, one line each.
Definition: indi_flight/GATES.md 5b "G5.7 exact test (S139 ...)". Scenario mode_switch10 (run.json events p0 / e1..e10 / end).
Edges = vehicle_status nav_state changes between the start of p0 and the start of "end"; expected new states
[ALTCTL 1, POSCTL 2, STAB 15, POSCTL 2, LOITER 4, POSCTL 2, ALTCTL 1, STAB 15, LOITER 4, POSCTL 2]. Valid: 10 edges with these states and
truth horizontal speed >= 1.5 m/s at >= 8 of them. Per edge: thrust step = |mean collective (-vehicle_thrust_setpoint.xyz[2]) over
[e, e+0.1] - mean over [e-0.1, e]| <= 20 % of hover (hover = mean collective over settle+1 .. settle+3 s); tilt error = max angle between
truth body z (vehicle_attitude_groundtruth) and the vehicle_attitude_setpoint body z over [e+0.3, e+1.0] <= 5 deg. First 0.3 s reported
(setpoint step, peak error), not gated. LOC = truth tilt >= 80 deg or altitude < 0.2 m over p0..end. Sample times: timestamp_sample when
the topic has it, else timestamp (per topic; never mixed within one topic)."""
import json
import os
import sys

import numpy as np

EXPECT = [1, 2, 15, 2, 4, 2, 1, 15, 4, 2]   # vehicle_status nav_state: ALTCTL 1, POSCTL 2, LOITER 4, STAB 15
THR_LIM, TILT_LIM, V_MIN, N_V_MIN, LOC_TILT = 0.20, 5.0, 1.5, 8, 80.0


def zaxis(q):
    """Body z axis (world frame) of quaternions q (N x 4, w x y z)."""
    w, x, y, z = q.T
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], axis=1)


def ang(a, b):
    return np.degrees(np.arccos(np.clip(np.sum(a * b, axis=1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1), -1, 1)))


def mean_in(t, c, a, b):
    m = (t >= a) & (t < b)
    return float(c[m].mean()) if m.any() else float("nan")


def tilt_metrics(att, asp, te):
    """(max tilt err over [te+0.3, te+1.0], peak over [te, te+0.3), max setpoint tilt rate deg/s over [te, te+1.0])."""
    zt, zs = zaxis(att["q"]), zaxis(asp["q"])
    zi = np.stack([np.interp(att["t"], asp["t"], zs[:, k]) for k in range(3)], axis=1)
    e = ang(zt, zi)
    m1 = (att["t"] >= te + 0.3) & (att["t"] <= te + 1.0)
    m0 = (att["t"] >= te) & (att["t"] < te + 0.3)
    ms = (asp["t"] >= te) & (asp["t"] <= te + 1.0)
    rate = np.degrees(np.arccos(np.clip(np.sum(zs[ms][1:] * zs[ms][:-1], axis=1) / np.linalg.norm(zs[ms][1:], axis=1) / np.linalg.norm(zs[ms][:-1], axis=1), -1, 1))) / np.diff(asp["t"][ms]) if ms.sum() > 2 else np.array([float("nan")])
    rate = rate[np.isfinite(rate)]
    return (float(e[m1].max()) if m1.any() else float("nan"), float(e[m0].max()) if m0.any() else float("nan"),
            float(rate.max()) if rate.size else float("nan"))


def evaluate(win, nav, pos, att, thr, asp, hover, validity="all"):
    """win: dict t_p0, t_end, t_end_end (s). nav: t, v. pos: t, p (NED). att: t, q (truth). thr: t, c (collective).
    asp: t, q (attitude setpoint). Returns result dict."""
    ch = [(nav["t"][i], int(nav["v"][i - 1]), int(nav["v"][i])) for i in range(1, len(nav["v"])) if nav["v"][i] != nav["v"][i - 1]]
    ch = [e for e in ch if win["t_p0"] <= e[0] < win["t_end"]]
    res = {"hover_collective": hover, "n_edges": len(ch), "edges": [], "expected": EXPECT}
    vel = np.gradient(pos["p"][:, :2], pos["t"], axis=0)
    spd = np.hypot(vel[:, 0], vel[:, 1])
    zt, zs = zaxis(att["q"]), zaxis(asp["q"])
    for (te, a, b) in ch:
        r = {"t_s": float(te), "from": a, "to": b, "speed": float(np.interp(te, pos["t"], spd))}
        r["thrust_step"] = abs(mean_in(thr["t"], thr["c"], te, te + 0.1) - mean_in(thr["t"], thr["c"], te - 0.1, te))
        r["thrust_step_pct_hover"] = 100 * r["thrust_step"] / hover
        sp_i = lambda tt: np.array([np.interp(tt, asp["t"], zs[:, k]) for k in range(3)])[None, :]  # noqa: E731
        tm = (att["t"] >= te + 0.3) & (att["t"] <= te + 1.0)
        r["tilt_err_deg"] = float(max(ang(zt[i][None, :], sp_i(att["t"][i]))[0] for i in np.flatnonzero(tm))) if tm.any() else float("nan")
        rm = (att["t"] >= te) & (att["t"] < te + 0.3)
        r["rise_peak_err_deg"] = float(max(ang(zt[i][None, :], sp_i(att["t"][i]))[0] for i in np.flatnonzero(rm))) if rm.any() else float("nan")
        r["sp_step_deg"] = float(ang(sp_i(te - 0.05), sp_i(te + 0.05))[0])
        r["ok_thrust"] = bool(r["thrust_step_pct_hover"] <= 100 * THR_LIM)
        r["ok_tilt"] = bool(r["tilt_err_deg"] <= TILT_LIM)
        res["edges"].append(r)
    res["states_ok"] = [e["to"] for e in res["edges"]] == EXPECT
    res["n_fast"] = int(sum(e["speed"] >= V_MIN for e in res["edges"]))
    m = (att["t"] >= win["t_p0"]) & (att["t"] < win["t_end_end"])
    mp = (pos["t"] >= win["t_p0"]) & (pos["t"] < win["t_end_end"])
    res["tilt_max_deg"] = float(np.degrees(np.arccos(np.clip(zt[m][:, 2], -1, 1))).max()) if m.any() else float("nan")
    res["z_up_min_m"] = float((-pos["p"][mp, 2]).min()) if mp.any() else float("nan")
    res["loc"] = bool(res["tilt_max_deg"] >= LOC_TILT or res["z_up_min_m"] < 0.2)
    res["validity_rule"] = validity
    if validity == "leaveP":    # truth speed >= V_MIN at each edge that leaves posctl (from == 2)
        lv = [e for e in res["edges"] if e["from"] == 2]
        res["n_leaveP"], res["n_leaveP_fast"] = len(lv), int(sum(e["speed"] >= V_MIN for e in lv))
        speed_ok = len(lv) == 4 and res["n_leaveP_fast"] == 4
    else:
        speed_ok = res["n_fast"] >= N_V_MIN
    res["valid"] = bool(res["states_ok"] and speed_ok)
    res["invalid_reason"] = None if res["valid"] else f"states_ok {res['states_ok']} (to {[e['to'] for e in res['edges']]}), n_fast {res['n_fast']}, rule {validity}"
    res["thrust_ok"] = all(e["ok_thrust"] for e in res["edges"]) and bool(res["edges"])
    res["tilt_ok"] = all(e["ok_tilt"] for e in res["edges"]) and bool(res["edges"])
    res["passed"] = bool(res["valid"] and res["thrust_ok"] and res["tilt_ok"] and not res["loc"])
    return res


def load(d):
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"))
    ds = {x.name: x.data for x in u.data_list}
    return u, ds


def _t(dd):
    return (dd["timestamp_sample"] * 1e-6) if ("timestamp_sample" in dd and np.all(dd["timestamp_sample"] > 0)) else dd["timestamp"] * 1e-6


def check(d, validity="all"):
    meta = json.load(open(os.path.join(d, "run.json")))
    u, ds = load(d)
    ev = {e["name"]: e for e in meta["events"]}
    win = {"t_p0": ev["p0"]["t_us"] * 1e-6, "t_end": ev["end"]["t_us"] * 1e-6, "t_end_end": ev["end"]["t_us"] * 1e-6 + ev["end"]["dur_s"]}
    g, a, v = ds["vehicle_local_position_groundtruth"], ds["vehicle_attitude_groundtruth"], ds["vehicle_status"]
    pos = {"t": _t(g), "p": np.stack([g["x"], g["y"], g["z"]], axis=1)}
    att = {"t": _t(a), "q": np.stack([a[f"q[{k}]"] for k in range(4)], axis=1)}
    vt, sp = ds["vehicle_thrust_setpoint"], ds["vehicle_attitude_setpoint"]
    thr = {"t": _t(vt), "c": -vt["xyz[2]"]}
    asp = {"t": _t(sp), "q": np.stack([sp[f"q_d[{k}]"] for k in range(4)], axis=1)}
    t0 = ev["settle"]["t_us"] * 1e-6
    hover = mean_in(thr["t"], thr["c"], t0 + 1, t0 + 3)
    res = evaluate(win, {"t": v["timestamp"] * 1e-6, "v": v["nav_state"]}, pos, att, thr, asp, hover, validity)
    res["run"] = os.path.basename(d.rstrip("/"))
    res["mode_switches"] = meta.get("mode_switches")
    res["params"] = {k: u.initial_parameters.get(k) for k in ("COM_RC_OVERRIDE", "COM_RC_IN_MODE", "MPC_VEL_MANUAL", "MPC_POS_MODE")}
    json.dump(res, open(os.path.join(d, "g57_check.json" if validity == "all" else f"g57_check_{validity}.json"), "w"), indent=1)
    return res


def line(r):
    tag = "INVALID" if not r["valid"] else ("PASS" if r["passed"] else "FAIL")
    e = "; ".join(f"{x['from']}>{x['to']} v {x['speed']:.1f} thr {x['thrust_step_pct_hover']:.1f}% tilt {x['tilt_err_deg']:.2f} (rise {x['rise_peak_err_deg']:.1f}, spstep {x['sp_step_deg']:.1f})"
                  for x in r["edges"])
    return f"{r.get('run', '?')} G5.7 {tag}: edges {r['n_edges']} fast {r['n_fast']} loc {r['loc']} hover {r['hover_collective']:.3f} | {e}" + \
        (f" reason {r['invalid_reason']}" if r["invalid_reason"] else "")


if __name__ == "__main__":
    args = sys.argv[1:]
    val = "all"
    if "--validity" in args:
        i = args.index("--validity")
        val = args[i + 1]
        del args[i:i + 2]
    for d in args:
        print(line(check(d, val)))
