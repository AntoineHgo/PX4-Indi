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
