#!/usr/bin/env python3
"""S139 G5.3 hold check: python3 g53_hold_check.py RUN_DIR... -> g53_hold_check.json per run, one line each.
Definition: indi_flight/GATES.md 5b "G5.3 exact test (S139 ...)", Hold part. Scenario hold_wind with wind override (steady 5, peak 8, dir 0).
Wind start t0 = run.json disturbance.onset_us. Reference = mean truth position (vehicle_local_position_groundtruth) over [t0-1, t0].
Hold RMS = RMS of the 3-D distance to the reference over [t0, t0+28 s]; pass <= 0.3 m. nav_state must be 4 (AUTO_LOITER) over the whole window,
else invalid. Also reported: max distance, mean offset x/y/z, position drift between the hold edge (nav change to 4) and t0.
Sample time = timestamp_sample when the truth topic has it, else timestamp."""
import json
import os
import sys

import numpy as np

RMS_LIM, WIN_S, REF_S = 0.3, 28.0, 1.0


def evaluate(t0, nav, pos):
    """nav: t, v; pos: t, p (N x 3). Returns result dict."""
    t, p = pos["t"], pos["p"]
    mr = (t >= t0 - REF_S) & (t < t0)
    mw = (t >= t0) & (t <= t0 + WIN_S)
    res = {"t_wind_s": float(t0), "n_ref": int(mr.sum()), "n_win": int(mw.sum())}
    if mr.sum() < 5 or mw.sum() < 5:
        return dict(res, valid=False, passed=False, invalid_reason="no truth samples in the reference or window")
    ref = p[mr].mean(axis=0)
    d = np.linalg.norm(p[mw] - ref, axis=1)
    res["ref_ned"] = ref.tolist()
    res["hold_rms_m"] = float(np.sqrt(np.mean(d ** 2)))
    res["hold_max_m"] = float(d.max())
    res["mean_offset_ned_m"] = (p[mw] - ref).mean(axis=0).tolist()
    # nav_state at every instant of the window: the state in force at t0 plus every sample inside
    k0 = max(int(np.searchsorted(nav["t"], t0, side="right")) - 1, 0)
    inw = (nav["t"] > t0) & (nav["t"] <= t0 + WIN_S)
    states = sorted(set([int(nav["v"][k0])] + [int(x) for x in nav["v"][inw]]))
    res["nav_states_in_window"] = states
    res["nav_ok"] = states == [4]
    res["valid"] = bool(res["nav_ok"])
    res["invalid_reason"] = None if res["valid"] else f"nav_state in window {states}, need only 4"
    res["passed"] = bool(res["valid"] and res["hold_rms_m"] <= RMS_LIM)
    return res


def _t(dd):
    return (dd["timestamp_sample"] * 1e-6) if ("timestamp_sample" in dd and np.all(dd["timestamp_sample"] > 0)) else dd["timestamp"] * 1e-6


def check(d):
    from pyulog import ULog
    meta = json.load(open(os.path.join(d, "run.json")))
    u = ULog(os.path.join(d, "flight.ulg"))
    ds = {x.name: x.data for x in u.data_list}
    g, v = ds["vehicle_local_position_groundtruth"], ds["vehicle_status"]
    pos = {"t": _t(g), "p": np.stack([g["x"], g["y"], g["z"]], axis=1)}
    nav = {"t": v["timestamp"] * 1e-6, "v": v["nav_state"]}
    t0 = meta["disturbance"]["onset_us"] * 1e-6
    res = evaluate(t0, nav, pos)
    ch = [nav["t"][i] for i in range(1, len(nav["v"])) if nav["v"][i] == 4 and nav["v"][i - 1] != 4 and nav["t"][i] < t0 + 1]
    res["hold_edge_s"] = float(ch[-1]) if ch else None
    res["wind_start_after_edge_s"] = float(t0 - ch[-1]) if ch else None
    res["run"] = os.path.basename(d.rstrip("/"))
    res["wind_meta"] = meta["disturbance"].get("wind")
    res["mode_switches"] = meta.get("mode_switches")
    res["params"] = {k: u.initial_parameters.get(k) for k in ("COM_RC_OVERRIDE", "COM_RC_IN_MODE", "MPC_XY_CRUISE", "NAV_ACC_RAD")}
    json.dump(res, open(os.path.join(d, "g53_hold_check.json"), "w"), indent=1)
    return res


def line(r):
    tag = "INVALID" if not r["valid"] else ("PASS" if r["passed"] else "FAIL")
    return f"{r.get('run', '?')} G5.3-hold {tag}: rms {r.get('hold_rms_m', float('nan')):.3f} m (<= {RMS_LIM}) max {r.get('hold_max_m', float('nan')):.3f} " \
           f"mean_off {np.round(r.get('mean_offset_ned_m', [np.nan] * 3), 3).tolist()} nav {r.get('nav_states_in_window')} " \
           f"edge->wind {r.get('wind_start_after_edge_s')}" + (f" reason {r['invalid_reason']}" if r.get("invalid_reason") else "")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(line(check(d)))
