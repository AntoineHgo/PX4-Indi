#!/usr/bin/env python3
"""S153 ground-arm check: python3 groundarm_check.py RUN_DIR [--json OUT] (RUN_DIR: flight.ulg, run.json from --ground-arm).
Per phase (low / centre): max truth altitude above ground, max thrust command (indi_pos_status.thrust, else -vehicle_thrust_setpoint z);
land-detector edges; thrust step at landed->not-landed edge (mean 0.1 s after - mean 0.1 s before) in % of hover; truth overshoot over 3 m; tilt > 10 deg."""
import argparse
import json
import os

import numpy as np
from pyulog import ULog


def d(u, n):
    L = [x for x in u.data_list if x.name == n]
    return L[0].data if L else None


def mean_step(t, c, t0, w=0.1):
    a, b = c[(t >= t0 - w) & (t < t0)], c[(t >= t0) & (t < t0 + w)]
    return float(b.mean() - a.mean()) if a.size and b.size else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--json")
    a = ap.parse_args()
    u = ULog(os.path.join(a.run_dir, "flight.ulg"))
    m = json.load(open(os.path.join(a.run_dir, "run.json")))
    ph = {k: v * 1e-6 for k, v in m["ground_arm"]["phases_us"].items()}
    S = lambda x: x["timestamp"] * 1e-6  # noqa: E731
    gt, ld, ip, vt, att = (d(u, n) for n in ("vehicle_local_position_groundtruth", "vehicle_land_detected",
                                              "indi_pos_status", "vehicle_thrust_setpoint", "vehicle_attitude_groundtruth"))
    out = {"exit": m.get("exit_status"), "error": m.get("error"), "controller": m.get("controller"), "phases_s": ph}
    tg, zu = S(gt), -gt["z"]
    ground = float(np.interp(ph["low"], tg, zu))
    out["ground_z_up_m"] = ground
    if ip is not None:
        tt, thr, src = S(ip), ip["thrust"].astype(float), "indi_pos_status.thrust"
    else:
        tt, thr, src = S(vt), -vt["xyz[2]"].astype(float), "-vehicle_thrust_setpoint.z"
    out["thrust_source"] = src
    tv, cv = S(vt), -vt["xyz[2]"].astype(float)
    ends = {"low": ph["centre"], "centre": ph["climb"]}
    for n, t1 in ends.items():
        w = (tg >= ph[n]) & (tg < t1)
        wt = (tt >= ph[n]) & (tt < t1)
        wv = (tv >= ph[n]) & (tv < t1)
        out[n] = {"max_alt_above_ground_m": float((zu[w] - ground).max()),
                  "max_thrust": float(thr[wt].max()) if wt.any() else None, "n_thrust": int(wt.sum()),
                  "max_vehicle_thrust_sp": float(cv[wv].max()) if wv.any() else None}
    # hover thrust: median collective in the hold phase
    wh = (tv >= ph["hold"]) & (tv < ph["land_cmd"])
    hover = float(np.median(cv[wh])) if wh.any() else float("nan")
    out["hover_collective"] = hover
    t, ev = S(ld), []
    keys = ("landed", "maybe_landed", "ground_contact", "freefall")
    for k in keys:
        x = ld[k].astype(int)
        ch = np.where(np.diff(x) != 0)[0] + 1
        ev += [(float(t[0]), k, int(x[0]), "initial")] + [(float(t[i]), k, int(x[i]), "edge") for i in ch]
    out["land_detector"] = sorted(ev, key=lambda e: e[0])
    lx = ld["landed"].astype(int)
    up = [t[i] for i in np.where(np.diff(lx) == -1)[0] + 1 if t[i] >= ph["low"]]
    if up:
        te = float(up[0])
        out["t_unlanded_s"] = te
        out["t_unlanded_since_arm_s"] = te - ph["low"]
        for nm, (tx, cx) in (("indi_pos_status.thrust", (tt, thr)), ("vehicle_thrust_setpoint", (tv, cv))):
            st = mean_step(tx, cx, te)
            out["edge_step_" + ("indi" if nm.startswith("indi") else "vts")] = st
            out["edge_step_pct_hover_" + ("indi" if nm.startswith("indi") else "vts")] = 100 * st / hover
        out["edge_phase"] = [k for k in ("low", "centre", "climb", "hold") if ph[k] <= te][-1]
    wc = (tg >= ph["climb"]) & (tg < ph["land_cmd"])
    out["max_alt_above_ground_m"] = float((zu[wc] - ground).max())
    out["overshoot_over_3m"] = out["max_alt_above_ground_m"] - 3.0
    q = np.stack([att["q[%d]" % i] for i in range(4)], 1)
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))
    ta = S(att)
    wa = (ta >= ph["low"]) & (ta < ph["land_cmd"])
    out["max_tilt_deg_before_land"] = float(tilt[wa].max())
    out["tilt_gt10_s"] = float((np.diff(ta[wa], prepend=ta[wa][0])[tilt[wa] > 10]).sum())
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
