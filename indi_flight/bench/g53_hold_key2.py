#!/usr/bin/env python3
"""G5.3 Hold test, independent second-key re-implementation (spec from GATES.md S139 paragraph).

Usage: python3 g53_hold_key2.py <run_dir> [<run_dir> ...]
Each run_dir holds flight.ulg and run.json. Prints diagnostics to stdout and
writes one result line per run to key2_g53_hold.txt in the results directory
(the parent of the run directories, which must be shared).
"""
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

WINDOW_S = 28.0
REF_S = 1.0
RMS_LIMIT_M = 0.3
NAV_HOLD = 4


def load(ulg_path):
    u = ULog(ulg_path, message_name_filter_list=["vehicle_status", "vehicle_local_position_groundtruth"])
    out = {}
    for d in u.data_list:
        if d.name in ("vehicle_status", "vehicle_local_position_groundtruth") and d.multi_id == 0:
            out[d.name] = d.data
    return out


def truth_time(gt):
    # timestamp_sample if present (and set), else timestamp
    if "timestamp_sample" in gt:
        ts = np.asarray(gt["timestamp_sample"], dtype=np.int64)
        base = np.asarray(gt["timestamp"], dtype=np.int64)
        return np.where(ts > 0, ts, base)
    return np.asarray(gt["timestamp"], dtype=np.int64)


def run(run_dir):
    run_json = json.load(open(os.path.join(run_dir, "run.json")))
    t0 = int(run_json["disturbance"]["onset_us"])
    data = load(os.path.join(run_dir, "flight.ulg"))
    gt = data["vehicle_local_position_groundtruth"]
    vs = data["vehicle_status"]

    t = truth_time(gt)
    pos = np.stack([np.asarray(gt["x"]), np.asarray(gt["y"]), np.asarray(gt["z"])], axis=1)

    ref_mask = (t >= t0 - int(REF_S * 1e6)) & (t <= t0)
    if not ref_mask.any():
        raise SystemExit(f"{run_dir}: no truth samples in reference window")
    ref = pos[ref_mask].mean(axis=0)

    end = t0 + int(WINDOW_S * 1e6)
    win = (t >= t0) & (t <= end)
    dist = np.linalg.norm(pos[win] - ref, axis=1)
    rms = math.sqrt(float(np.mean(dist ** 2)))
    dmax = float(dist.max())

    # nav_state: last value published before each instant
    vt = np.asarray(vs["timestamp"], dtype=np.int64)
    nav = np.asarray(vs["nav_state"], dtype=np.int64)
    order = np.argsort(vt, kind="stable")
    vt, nav = vt[order], nav[order]
    before = np.searchsorted(vt, t0, side="right") - 1
    state_at_start = int(nav[before]) if before >= 0 else None
    in_win = (vt >= t0) & (vt <= end)
    states = ([state_at_start] if state_at_start is not None else []) + list(nav[in_win])
    valid = bool(states) and all(s == NAV_HOLD for s in states)
    # diagnostic: when nav_state first became 4 relative to onset
    is4 = np.where(nav == NAV_HOLD)[0]
    first4 = (vt[is4[0]] - t0) / 1e6 if len(is4) else float("nan")
    last_change = None
    for i in range(1, len(nav)):
        if nav[i] != nav[i - 1] and vt[i] <= end + 60_000_000:
            last_change = (round((vt[i] - t0) / 1e6, 3), int(nav[i - 1]), int(nav[i]))

    if not valid:
        verdict = "INVALID"
    else:
        verdict = "PASS" if rms <= RMS_LIMIT_M else "FAIL"

    print(f"{os.path.basename(run_dir)}: onset_us={t0} ulog=[{t[0]},{t[-1]}] "
          f"truth_samples_win={int(win.sum())} ref_samples={int(ref_mask.sum())} "
          f"ref={ref.round(3).tolist()} first_nav4_rel_s={first4:.3f} "
          f"nav_state_at_onset={state_at_start} states_in_win={sorted(set(states))} "
          f"last_nav_change(rel_s,from,to)={last_change}")
    return f"{os.path.basename(run_dir)} rms={rms:.4f} m max={dmax:.4f} m valid={'yes' if valid else 'no'} verdict={verdict}"


def main():
    dirs = sys.argv[1:]
    if not dirs:
        raise SystemExit(__doc__)
    lines = [run(d) for d in dirs]
    out = os.path.join(os.path.dirname(os.path.abspath(dirs[0])), "key2_g53_hold.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("wrote", out)


if __name__ == "__main__":
    main()
