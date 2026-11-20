#!/usr/bin/env python3
"""S131 AUTO smoke check: per-phase tracking, take-off handover, landing and INDI stage-mode transitions from one ULog.

  python3 indi_flight/bench/auto_smoke_check.py RUN_DIR [--json OUT.json]      (RUN_DIR holds flight.ulg and run.json)

Time base: ULog timestamps are absolute (hrt) seconds, the same base as run.json auto_phases / t_*_us. Do NOT subtract
ulog.start_timestamp (that made the NAV_LAND of S130 look 19.6 s early). Ground truth: vehicle_local_position_groundtruth
(NED, same local frame as the setpoint). Pure functions below take arrays and are covered by tests/test_auto_smoke_check.py.
"""
import argparse
import json
import os

import numpy as np

NAV = {2: "altctl", 3: "mission", 4: "loiter", 5: "rtl", 17: "takeoff", 18: "land", 14: "offboard", 0: "manual"}


def handover_metrics(t_thr, thr, t_z, z_ned, t_edge, w=0.05):
    """|mean thrust in [t, t+w) - mean thrust in [t-w, t)| at the edge, and altitude dip (m) in the 1 s after the edge
    (altitude at the edge minus the lowest altitude in [t, t+1 s]; 0 if it never goes below)."""
    a = thr[(t_thr >= t_edge - w) & (t_thr < t_edge)]
    b = thr[(t_thr >= t_edge) & (t_thr < t_edge + w)]
    step = float(abs(b.mean() - a.mean())) if a.size and b.size else float("nan")
    zu = -np.asarray(z_ned)
    z0 = float(np.interp(t_edge, t_z, zu))
    m = (t_z >= t_edge) & (t_z <= t_edge + 1.0)
    dip = float(max(0.0, z0 - zu[m].min())) if m.any() else float("nan")
    return step, dip


def mean_step(t, c, t0, w=0.1):
    """|mean(c in [t0, t0+w)) - mean(c in [t0-w, t0))|; nan if either window has no sample."""
    a = c[(t >= t0 - w) & (t < t0)]
    b = c[(t >= t0) & (t < t0 + w)]
    return float(abs(b.mean() - a.mean())) if a.size and b.size else float("nan")


def takeoff_g54(t_c, c, t_ramp, t_edge, hover, t_gt, z_up_gt, w=0.1, skip=0.5, tol=0.10, dip_tol=0.3):
    """G5.4 take-off check. c = collective = -vehicle_thrust_setpoint.xyz[2] at times t_c; hover = mean collective in
    the hold phase; t_ramp = first takeoff_status state 4, t_edge = transition 4 -> 5 (same absolute time base).
    Step(t) = |mean c[t, t+0.1) - mean c[t-0.1, t)|. Ramp points t_k = t_ramp + 0.5 + k*0.1 for all t_k < t_edge
    (the ramp climbs 0 -> hover in the first 0.5 s by design); the edge step is Step(t_edge). Each must be <= tol*hover.
    Dip = max(0, z_up_gt(t_edge) - min z_up_gt over [t_edge, t_edge+1 s]); z_up_gt = -z_ned of
    vehicle_local_position_groundtruth, interpolated at the edge. Must be <= dip_tol m."""
    t_c, c = np.asarray(t_c), np.asarray(c)
    n = int(np.floor((t_edge - t_ramp - skip) / w - 1e-9)) + 1 if t_edge > t_ramp + skip else 0
    tk = t_ramp + skip + w * np.arange(max(n, 0))
    st = np.array([mean_step(t_c, c, x, w) for x in tk])
    ok = np.isfinite(st)
    if ok.any():
        i = int(np.nanargmax(np.where(ok, st, -1.0)))
        mx, tmx = float(st[i]), float(tk[i])
    else:
        mx, tmx = float("nan"), float("nan")
    edge = mean_step(t_c, c, t_edge, w)
    t_gt, z = np.asarray(t_gt), np.asarray(z_up_gt)
    m = (t_gt >= t_edge) & (t_gt <= t_edge + 1.0)
    dip = float(max(0.0, np.interp(t_edge, t_gt, z) - z[m].min())) if m.any() else float("nan")
    lim = tol * hover
    return {"hover_collective": float(hover), "n_ramp_points": int(tk.size), "n_ramp_points_no_data": int((~ok).sum()),
            "ramp_max_step": mx, "ramp_max_step_pct_hover": 100 * mx / hover, "ramp_max_step_t_s": tmx,
            "edge_step": edge, "edge_step_pct_hover": 100 * edge / hover, "dip_m": dip,
            "ramp_ok": bool(ok.any() and not (st[ok] > lim).any() and not (~ok).any()),
            "edge_ok": bool(edge <= lim), "dip_ok": bool(dip <= dip_tol)}


def takeoff_overshoot(t, z_up, t_edge, t_end, t_hold_end, target, tol=0.5, near=0.2, bounce_tol=0.3):
    """Truth z_up (m above start). Overshoot = max z_up in [t_edge, t_end] - target (t_end = takeoff_done + 3 s), <= tol.
    Bounce: from the first time z_up >= target - near, the largest shortfall target - z_up until t_hold_end, <= bounce_tol."""
    t, z = np.asarray(t), np.asarray(z_up)
    m = (t >= t_edge) & (t <= t_end)
    over = float(z[m].max() - target) if m.any() else float("nan")
    near_i = np.where((t >= t_edge) & (z >= target - near))[0]
    if near_i.size:
        w = (t >= t[near_i[0]]) & (t <= t_hold_end)
        bounce = float(max(0.0, target - z[w].min()))
    else:
        bounce = float("nan")
    return {"target_m": float(target), "overshoot_m": over, "bounce_m": bounce,
            "overshoot_ok": bool(over <= tol), "bounce_ok": bool(bounce <= bounce_tol)}


def touchdown_check(t, z_up, vz_down, t_q, tilt_deg, t_ld, landed, t_start, t_disarm, ground, vz_max=0.8, tilt_max=10.0,
                    relift=0.15, td_h=0.05):
    """Touchdown anchored on truth, not on ground_contact. ground = truth z_up at takeoff_cmd. t_td = first time at or
    after the altitude maximum within [t_start, t_disarm] (t_start = rtl/land command) with z_up <= ground + 0.05 m.
    vz = max truth vz (down +) over [t_td-0.2, t_td]; tilt = max tilt in [t_td-1, t_disarm]; re-lift = max z_up in
    [t_td, t_disarm] minus ground, <= 0.15; relanded = landed goes false again after true in [t_td, t_disarm)."""
    t, z, v = np.asarray(t), np.asarray(z_up), np.asarray(vz_down)
    w = np.where((t >= t_start) & (t <= t_disarm))[0]
    k = w[np.argmax(z[w])] if w.size else None
    hit = np.where(z[k:] <= ground + td_h)[0] if k is not None else []
    if len(hit) == 0:
        nan = float("nan")
        return {"t_td_s": nan, "vz_contact": nan, "tilt_max_deg": nan, "relift_m": nan, "landed_dropped": False,
                "vz_ok": False, "tilt_ok": False, "relift_ok": False, "landed_ok": False}
    t_td = float(t[k + hit[0]])
    mv = (t >= t_td - 0.2) & (t <= t_td)
    vz = float(v[mv].max())
    tq = np.asarray(t_q)
    mt = (tq >= t_td - 1.0) & (tq <= t_disarm)
    tilt = float(np.asarray(tilt_deg)[mt].max()) if mt.any() else float("nan")
    mz = (t >= t_td) & (t <= t_disarm)
    lift = float(z[mz].max() - ground)
    ml = (np.asarray(t_ld) >= t_td) & (np.asarray(t_ld) < t_disarm)
    la = np.asarray(landed)[ml].astype(int)
    relanded = bool(la.size and la.max() == 1 and (la[np.argmax(la == 1):] == 0).any())
    return {"t_td_s": t_td, "vz_contact": vz, "tilt_max_deg": tilt, "relift_m": lift, "landed_dropped": relanded,
            "vz_ok": bool(vz <= vz_max), "tilt_ok": bool(tilt <= tilt_max), "relift_ok": bool(lift <= relift),
            "landed_ok": not relanded}


def land_speed_check(vz_mean, land_speed, c2d, disarm_land, rel=0.2, slack=1.0):
    """Mean descent vz within +-rel of MPC_LAND_SPEED; contact->disarm <= COM_DISARM_LAND + slack s."""
    return {"vz_ok": bool(abs(vz_mean - land_speed) <= rel * land_speed), "disarm_ok": bool(c2d <= disarm_land + slack)}


def descent_start(t_sp, z_sp_ned, t0, drop=0.3):
    """Final-descent start: first time after t0 where the setpoint z_up falls more than `drop` m below its running max
    since t0 (end of the climb/cruise at RTL altitude). nan if it never does."""
    t, z = np.asarray(t_sp), -np.asarray(z_sp_ned)
    m = (t >= t0) & np.isfinite(z)
    t, z = t[m], z[m]
    k = np.where(z < np.maximum.accumulate(z) - drop)[0] if z.size else []
    return float(t[k[0]]) if len(k) else float("nan")


def rtl_height_error(t_gt, z_gt_ned, t_sp, z_sp_ned, t0, t1, tol=1.0):
    """max |truth z - trajectory_setpoint z| (NED, finite setpoint rows) over [t0, t1], <= tol m."""
    t_sp, zs = np.asarray(t_sp), np.asarray(z_sp_ned)
    m = (t_sp >= t0) & (t_sp <= t1) & np.isfinite(zs)
    if not m.any():
        return {"max_err_m": float("nan"), "ok": False}
    e = float(np.abs(np.interp(t_sp[m], t_gt, z_gt_ned) - zs[m]).max())
    return {"max_err_m": e, "ok": bool(e <= tol)}


def mean_descent_vz(t, z_ned, vz, lo=1.0, hi=4.0):
    """Mean vz (m/s, NED: positive = down) over the samples with lo < height < hi m while descending (vz > 0)."""
    h = -np.asarray(z_ned)
    m = (h > lo) & (h < hi) & (vz > 0)
    return (float(vz[m].mean()), int(m.sum())) if m.any() else (float("nan"), 0)


def transitions(t, v):
    """[(t, from, to)] of a piecewise constant signal."""
    i = np.where(np.diff(v) != 0)[0]
    return [(float(t[k + 1]), int(v[k]), int(v[k + 1])) for k in i]


def track_err(t, gt, t_sp, sp, t0, t1):
    """xy / z error of the ground truth against the finite position setpoint rows in [t0, t1]: dict or None."""
    m = (t_sp >= t0) & (t_sp <= t1) & np.isfinite(sp).all(axis=1)
    if not m.any():
        return None
    g = np.stack([np.interp(t_sp[m], t, gt[:, k]) for k in range(3)], axis=1)
    e = g - sp[m]
    exy = np.hypot(e[:, 0], e[:, 1])
    return {"n": int(m.sum()), "xy_rms": float(np.sqrt((exy ** 2).mean())), "xy_max": float(exy.max()),
            "z_rms": float(np.sqrt((e[:, 2] ** 2).mean())), "z_max": float(np.abs(e[:, 2]).max())}


def _d(u, name):
    L = [d for d in u.data_list if d.name == name]
    return L[0].data if L else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    from pyulog import ULog
    u = ULog(os.path.join(a.run_dir, "flight.ulg"))
    meta = json.load(open(os.path.join(a.run_dir, "run.json")))
    S = lambda d: d["timestamp"] * 1e-6  # noqa: E731
    out = {"scenario": meta.get("scenario"), "exit_status": meta.get("exit_status"), "error": meta.get("error")}
    ph = meta.get("auto_phases", [])
    pt = {p["name"]: p["t_us"] * 1e-6 for p in ph}
    out["phases_s"] = pt
    gt, sp = _d(u, "vehicle_local_position_groundtruth"), _d(u, "trajectory_setpoint")
    lp, vs, ld = _d(u, "vehicle_local_position"), _d(u, "vehicle_status"), _d(u, "vehicle_land_detected")
    ts, ip, ctl = _d(u, "takeoff_status"), _d(u, "indi_pos_status"), None
    L = []
    P = lambda s="": L.append(s)  # noqa: E731
    P(f"scenario {out['scenario']} exit {out['exit_status']} error {out['error']}")
    P("phases (sim s): " + ", ".join(f"{k}={v:.1f}" for k, v in pt.items()))
    names = [p["name"] for p in ph]
    win = {}
    for lab, s0, s1 in (("takeoff", "takeoff_cmd", "takeoff_done"), ("hold", "takeoff_done", "hold_end"),
                        ("mission", "mission_start", "mission_end"),
                        ("rtl", "rtl_cmd", "disarmed"), ("land", "land_cmd", "disarmed")):
        if s0 in pt and s1 in pt:
            win[lab] = (pt[s0], pt[s1])
    out["tracking"] = {}
    P("\n== tracking vs trajectory_setpoint (ground truth; rows with finite position setpoint only)")
    if gt is not None and sp is not None:
        g = np.stack([gt["x"], gt["y"], gt["z"]], axis=1)
        s = np.stack([sp[f"position[{k}]"] for k in range(3)], axis=1)
        for lab, (t0, t1) in win.items():
            r = track_err(S(gt), g, S(sp), s, t0, t1)
            out["tracking"][lab] = r
            P(f"{lab:8s} [{t0:.1f},{t1:.1f}] " + ("no finite position setpoint rows" if r is None else
              f"n={r['n']} xy rms {r['xy_rms']:.3f} max {r['xy_max']:.3f} m | z rms {r['z_rms']:.3f} max {r['z_max']:.3f} m"))
    else:
        P("missing vehicle_local_position_groundtruth or trajectory_setpoint")
    P("\n== take-off handover (takeoff_status rampup(4) -> flight(5))")
    out["handover"] = None
    if ts is not None and ip is not None and lp is not None:
        edges = [e for e in transitions(S(ts), ts["takeoff_state"]) if e[1] == 4 and e[2] == 5]
        if edges:
            te = edges[0][0]
            step, dip = handover_metrics(S(ip), ip["thrust"], S(lp), lp["z"], te)
            out["handover"] = {"t_edge_s": te, "thrust_step": step, "alt_dip_m": dip, "first_indi_pos_status_s": float(S(ip)[0])}
            P(f"edge at {te:.3f} s: indi_pos_status.thrust step {step:.4f} (nan = no sample before the edge; first sample "
              f"{S(ip)[0]:.3f} s), altitude dip within 1 s {dip:.3f} m")
            vt = _d(u, "vehicle_thrust_setpoint")  # published by whoever commands thrust, before and after the edge
            if vt is not None:
                st2, _ = handover_metrics(S(vt), -vt["xyz[2]"], S(lp), lp["z"], te)
                out["handover"]["vehicle_thrust_setpoint_step"] = st2
                P(f"vehicle_thrust_setpoint (-xyz[2]) step at the edge: {st2:.4f}")
            hold = win.get("hold")
            ups = [float(x) for x in S(ts)[ts["takeoff_state"] == 4]]
            if vt is not None and gt is not None and hold and ups:
                tv_, cv_ = S(vt), -vt["xyz[2]"]
                hv = float(cv_[(tv_ >= hold[0]) & (tv_ < hold[1])].mean())
                g = takeoff_g54(tv_, cv_, ups[0], te, hv, S(gt), -gt["z"])
                out["g54_takeoff"] = g
                P(f"G5.4 take-off (vehicle_thrust_setpoint collective, hover {hv:.4f} from hold phase; 0.1 s means; ramp {ups[0]:.2f}..{te:.2f} s, "
                  f"{g['n_ramp_points']} points from ramp+0.5 s):")
                P(f"  ramp max step {g['ramp_max_step']:.4f} = {g['ramp_max_step_pct_hover']:.1f} % hover at {g['ramp_max_step_t_s']:.2f} s "
                  f"-> {'PASS' if g['ramp_ok'] else 'FAIL'} (<= 10 %)")
                P(f"  edge step {g['edge_step']:.4f} = {g['edge_step_pct_hover']:.1f} % hover -> {'PASS' if g['edge_ok'] else 'FAIL'} (<= 10 %)")
                P(f"  truth dip within 1 s {g['dip_m']:.3f} m -> {'PASS' if g['dip_ok'] else 'FAIL'} (<= 0.3 m)")
            else:
                P("G5.4 take-off: not evaluated (need vehicle_thrust_setpoint, groundtruth, hold phase, rampup state)")
        else:
            P("no rampup->flight edge; takeoff_state transitions: " + str(transitions(S(ts), ts["takeoff_state"])[:8]))
    else:
        P("missing takeoff_status / indi_pos_status / vehicle_local_position")
    P("\n== landing")
    out["land"] = None
    if lp is not None and ld is not None and vs is not None:
        tend = pt.get("land_cmd", pt.get("rtl_cmd", 0.0))
        tl, la = S(ld), ld["landed"].astype(int)
        cl = [tt for tt in tl[la == 1] if tt > tend]
        tc = float(cl[0]) if cl else float("nan")
        tg = S(ld)[ld["ground_contact"].astype(int) == 1]
        tg = float(tg[tg > tend][0]) if (tg > tend).any() else float("nan")
        tv, arm = S(vs), vs["arming_state"]
        dis = [tt for tt, v in zip(tv, arm) if v == 1 and tt > tend]
        td = float(dis[0]) if dis else float("nan")
        m = (S(lp) > tend) & (S(lp) < (tc if np.isfinite(tc) else 1e18))
        vzm, n = mean_descent_vz(S(lp)[m], lp["z"][m], lp["vz"][m])
        lsp = u.initial_parameters.get("MPC_LAND_SPEED", float("nan"))
        out["land"] = {"t_ground_contact_s": tg, "t_landed_s": tc, "t_disarm_s": td, "contact_to_disarm_s": td - tg,
                       "landed_to_disarm_s": td - tc, "mean_vz_1_4m": vzm, "n": n, "MPC_LAND_SPEED": lsp}
        P(f"ground_contact {tg:.2f} s, landed {tc:.2f} s, disarm {td:.2f} s -> contact->disarm {td - tg:.2f} s "
          f"(landed->disarm {td - tc:.2f} s)")
        P(f"mean vz (down+) between 1 and 4 m height: {vzm:.3f} m/s over {n} samples; MPC_LAND_SPEED {lsp}")
    P("\n== G5.4 other limits (truth = vehicle_local_position_groundtruth)")
    g5 = {}
    out["g54_other"] = g5
    ok_s = lambda b: "PASS" if b else "FAIL"  # noqa: E731
    if gt is not None and "takeoff_done" in pt and "hold_end" in pt and out.get("handover"):
        zup, tg_ = -gt["z"], S(gt)
        # target = MIS_TAKEOFF_ALT applied to this run (run.json params_applied, else the ULog parameter), m above home
        tgt = (meta.get("params_applied") or {}).get("MIS_TAKEOFF_ALT", u.initial_parameters.get("MIS_TAKEOFF_ALT"))
        z0 = float(np.interp(pt.get("takeoff_cmd", pt["armed"]), tg_, zup))  # ground level at the take-off command
        if tgt is not None:
            r = takeoff_overshoot(tg_, zup - z0, out["handover"]["t_edge_s"], pt["takeoff_done"] + 3.0, pt["hold_end"], float(tgt))
            g5["takeoff"] = r
            P(f"take-off (target {r['target_m']} m = MIS_TAKEOFF_ALT): overshoot {r['overshoot_m']:.3f} m -> {ok_s(r['overshoot_ok'])} (<= 0.5), "
              f"bounce {r['bounce_m']:.3f} m -> {ok_s(r['bounce_ok'])} (<= 0.3)")
    lnd = out.get("land")
    if gt is not None and lnd and np.isfinite(lnd["t_ground_contact_s"]) and np.isfinite(lnd["t_disarm_s"]):
        ga = _d(u, "vehicle_attitude_groundtruth")
        src = "vehicle_attitude_groundtruth"
        if ga is None:
            ga, src = _d(u, "vehicle_attitude"), "vehicle_attitude"
        q = np.stack([ga[f"q[{k}]"] for k in range(4)], axis=1)
        tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))
        tstart = pt.get("land_cmd", pt.get("rtl_cmd", 0.0))
        gnd = float(np.interp(pt.get("takeoff_cmd", pt["armed"]), S(gt), -gt["z"]))
        r = touchdown_check(S(gt), -gt["z"], gt["vz"], S(ga), tilt, S(ld), ld["landed"], tstart, lnd["t_disarm_s"], gnd)
        g5["touchdown"] = {**r, "tilt_source": src}
        P(f"touchdown (truth z_up <= ground+0.05 m) at {r['t_td_s']:.2f} s (ground_contact {lnd['t_ground_contact_s']:.2f} s): max vz {r['vz_contact']:.3f} m/s -> {ok_s(r['vz_ok'])} (<= 0.8); tilt max {r['tilt_max_deg']:.2f} deg "
          f"({src}) -> {ok_s(r['tilt_ok'])} (<= 10); re-lift {r['relift_m']:.3f} m -> {ok_s(r['relift_ok'])} (<= 0.15); "
          f"landed stays true -> {ok_s(r['landed_ok'])}")
        dl = u.initial_parameters.get("COM_DISARM_LAND", float("nan"))
        r = land_speed_check(lnd["mean_vz_1_4m"], lnd["MPC_LAND_SPEED"], lnd["contact_to_disarm_s"], dl)
        g5["land"] = {**r, "COM_DISARM_LAND": dl}
        P(f"land: mean vz {lnd['mean_vz_1_4m']:.3f} vs MPC_LAND_SPEED {lnd['MPC_LAND_SPEED']:.3f} (+-20 %) -> {ok_s(r['vz_ok'])}; "
          f"contact->disarm {lnd['contact_to_disarm_s']:.2f} s vs COM_DISARM_LAND {dl} + 1 s -> {ok_s(r['disarm_ok'])}")
    if "rtl_cmd" in pt and gt is not None and sp is not None:
        t1 = descent_start(S(sp), sp["position[2]"], pt["rtl_cmd"])
        if np.isfinite(t1):
            r = rtl_height_error(S(gt), gt["z"], S(sp), sp["position[2]"], pt["rtl_cmd"], t1)
            g5["rtl"] = {**r, "t_rtl_cmd_s": pt["rtl_cmd"], "t_descent_start_s": t1}
            P(f"rtl height error over [{pt['rtl_cmd']:.1f}, {t1:.1f}] s (descent start = setpoint z_up 0.3 m below its max since rtl_cmd): "
              f"{r['max_err_m']:.3f} m -> {ok_s(r['ok'])} (<= 1)")
        else:
            P("rtl: no descent start found in trajectory_setpoint")
    else:
        g5["rtl"] = "n/a"
        P("rtl height error: n/a (no rtl phase)")
    P("\n== stage_mode / nav_state transitions")
    if ip is not None:
        tr = transitions(S(ip), ip["stage_mode"])
        out["stage_transitions"] = tr
        P(f"indi_pos_status stage_mode: first {int(ip['stage_mode'][0])} at {S(ip)[0]:.2f} s, n={len(ip['stage_mode'])}, "
          f"values {sorted(set(int(x) for x in ip['stage_mode']))}, transitions {tr[:10]}")
    if vs is not None:
        nt = [(round(t, 2), NAV.get(f, f), NAV.get(g_, g_)) for t, f, g_ in transitions(S(vs), vs["nav_state"])]
        out["nav_transitions"] = nt
        P("vehicle_status nav_state: " + str(nt[:14]))
    P("heartbeat mode_log [t, main, sub, armed]: " + str(meta.get("mode_log", [])[:14]))
    print("\n".join(L))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
