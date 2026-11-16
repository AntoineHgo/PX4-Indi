#!/usr/bin/env python3
"""A17: test whether Commander publishes on a fixed phase of a 10 ms loop.

For each Commander-published topic present in the log, take every message's
timestamp mod 10000 us, histogram it in 1250 us bins (8 bins), and report the
dominant bin. Also report the phase of the first armed instant
(vehicle_status.arming_state == 2) and the first nav_state == 14 instant.

Usage: a17_commander_phase.py <ulog> <out.json>
"""
import json
import os
import sys

import numpy as np
from pyulog import ULog

PERIOD_US = 10000
BIN_US = 1250
NBINS = PERIOD_US // BIN_US
TOPICS = ["vehicle_status", "commander_state", "failsafe_flags",
          "actuator_armed", "vehicle_control_mode"]
ARMING_STATE_ARMED = 2
NAV_STATE_OFFBOARD = 14


def first_instant(datasets, field, value):
    """Earliest timestamp (us) where field == value, over all instances."""
    best = None
    for d in datasets:
        if field not in d.data:
            continue
        ts = np.asarray(d.data["timestamp"], dtype=np.int64)
        mask = np.asarray(d.data[field]) == value
        if mask.any():
            t = int(ts[mask].min())
            best = t if best is None else min(best, t)
    return best


def main():
    ulog_path, out_path = sys.argv[1], sys.argv[2]
    ulog = ULog(ulog_path)

    by_name = {}
    for d in ulog.data_list:
        by_name.setdefault(d.name, []).append(d)

    result = {
        "log": ulog_path,
        "period_us": PERIOD_US,
        "bin_us": BIN_US,
        "topics": {},
        "missing_topics": [],
    }

    for topic in TOPICS:
        if topic not in by_name:
            result["missing_topics"].append(topic)
            continue
        ts = np.concatenate([np.asarray(d.data["timestamp"], dtype=np.int64)
                             for d in by_name[topic]])
        mod = ts % PERIOD_US
        hist = np.bincount(mod // BIN_US, minlength=NBINS)[:NBINS]
        n = int(ts.size)
        k = int(np.argmax(hist))
        result["topics"][topic] = {
            "instances": len(by_name[topic]),
            "message_count": n,
            "histogram_bins_us": [[i * BIN_US, (i + 1) * BIN_US - 1] for i in range(NBINS)],
            "histogram_counts": [int(c) for c in hist],
            "most_common_bin": k,
            "most_common_bin_us": [k * BIN_US, (k + 1) * BIN_US - 1],
            "most_common_bin_fraction": float(hist[k]) / n if n else None,
            "exact_mod_min_us": int(mod.min()),
            "exact_mod_max_us": int(mod.max()),
        }

    status = by_name.get("vehicle_status", [])
    armed_t = first_instant(status, "arming_state", ARMING_STATE_ARMED)
    offb_t = first_instant(status, "nav_state", NAV_STATE_OFFBOARD)
    result["first_armed_us"] = armed_t
    result["first_armed_mod_us"] = None if armed_t is None else armed_t % PERIOD_US
    result["first_offboard_us"] = offb_t
    result["first_offboard_mod_us"] = None if offb_t is None else offb_t % PERIOD_US

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    for topic, r in result["topics"].items():
        print(f"{topic}: n={r['message_count']} bin={r['most_common_bin']} "
              f"frac={r['most_common_bin_fraction']:.3f} counts={r['histogram_counts']}")
    print(f"armed mod={result['first_armed_mod_us']} offboard mod={result['first_offboard_mod_us']}")
    if result["missing_topics"]:
        print("missing:", ", ".join(result["missing_topics"]))


if __name__ == "__main__":
    main()
