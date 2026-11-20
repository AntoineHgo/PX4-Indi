#!/usr/bin/env python3
"""Extra S134 F-7 smoke metrics not covered by auto_smoke_check.py, for one auto_tour RUN_DIR.

  python3 extra_metrics.py RUN_DIR [RUN_DIR ...]

Uses the same ULog time base as auto_smoke_check.py (absolute hrt seconds). Collective = -vehicle_thrust_setpoint.xyz[2]
(the commanded thrust, published before and after the take-off edge). Hover = mean collective over the hold phase
(takeoff_done .. hold_end). Ramp = takeoff_status rampup start (first state 4) .. take-off edge (state 4 -> 5).
"""
import json
import os
import sys

import numpy as np
from pyulog import ULog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bench")
sys.path.insert(0, os.path.abspath(BENCH))
from auto_smoke_check import _d, handover_metrics, transitions  # noqa: E402


def bin_means(t, v, t0, t1, w=0.1):
    edges = np.arange(t0, t1 + 1e-9, w)
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (t >= a) & (t < b)
        if m.any():
            out.append((a, float(v[m].mean())))
    return out


def run(d):
    u = ULog(os.path.join(d, "flight.ulg"))
    meta = json.load(open(os.path.join(d, "run.json")))
    S = lambda x: x["timestamp"] * 1e-6  # noqa: E731
    pt = {p["name"]: p["t_us"] * 1e-6 for p in meta.get("auto_phases", [])}
    ts, ip, lp = _d(u, "takeoff_status"), _d(u, "indi_pos_status"), _d(u, "vehicle_local_position")
    vt = _d(u, "vehicle_thrust_setpoint")
    t_vt, c = S(vt), -vt["xyz[2]"]
    r = {}
    ts_t = S(ts)
    up = [t for t, a, b in transitions(ts_t, ts["takeoff_state"]) if b == 4]
    t_ramp = float(up[0]) if up else float("nan")
    tr = [e for e in transitions(ts_t, ts["takeoff_state"]) if e[1] == 4 and e[2] == 5]
    t_edge = float(tr[0][0])
    r["t_rampup_s"], r["t_edge_s"] = t_ramp, t_edge
    # hover: mean collective in hold phase
    hold = (t_vt >= pt["takeoff_done"]) & (t_vt < pt["hold_end"])
    hover = float(c[hold].mean())
    r["hover_collective"] = hover
    # take-off edge step (checker definition, 50 ms means) and 0.1 s means
    step50, dip = handover_metrics(S(ip), ip["thrust"], S(lp), lp["z"], t_edge)
    step100, _ = handover_metrics(S(ip), ip["thrust"], S(lp), lp["z"], t_edge, w=0.1)
    r["edge_step_frac_hover_50ms"] = step50 / hover
    r["edge_step_frac_hover_100ms"] = step100 / hover
    r["edge_step_50ms"], r["edge_step_100ms"], r["truth_dip_m"] = step50, step100, dip
    # max |collective change| between consecutive 0.1 s means, ramp from rampup+0.5 s to edge
    bm = bin_means(t_vt, c, t_ramp + 0.5, t_edge)
    diffs = [(abs(b[1] - a[1]), b[0]) for a, b in zip(bm[:-1], bm[1:])]
    mx, tmx = max(diffs)
    r["max_dcoll_0p1s"], r["max_dcoll_at_s"] = mx, tmx
    # pre-arm ground collective: 5 s before rampup start
    g = (t_vt >= t_ramp - 5.0) & (t_vt < t_ramp)
    r["preare_coll_mean"], r["preare_coll_min"], r["preare_coll_max"] = (
        float(c[g].mean()), float(c[g].min()), float(c[g].max()))
    r["preare_window_s"] = [t_ramp - 5.0, t_ramp]
    # stage_mode sequence
    r["stage_transitions"] = [(round(t, 2), a, b) for t, a, b in transitions(S(ip), ip["stage_mode"])]
    r["stage_mode_first"] = [int(ip["stage_mode"][0]), round(float(S(ip)[0]), 2)]
    return r


def main():
    out = {}
    for d in sys.argv[1:]:
        out[d] = run(d)
        print(d)
        for k, v in out[d].items():
            print(f"  {k}: {v}")
    if os.environ.get("JSON_OUT"):
        json.dump(out, open(os.environ["JSON_OUT"], "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
