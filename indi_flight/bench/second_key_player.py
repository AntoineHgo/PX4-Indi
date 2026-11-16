#!/usr/bin/env python3
"""Independent check of a sim-time scenario player run, read from a ULog.

Usage: second_key_player.py <flight.ulg> <out.json>

Reports, for one log:
  1. sim_schedule_applied rows: timestamp, t_sched_us, kind, timestamp - t_sched_us
  2. vehicle_status: first timestamp with arming_state == 2 (armed) and
     first timestamp with nav_state == 14 (offboard)
  3. those two instants minus the matching applied row timestamp
     (kind 'arm' and kind 'mode_offboard')
  4. sensor_gyro median sample period from timestamp_sample diffs

Any section that cannot be computed is recorded under "errors" with the
value left as null; the script does not abort on a missing topic/field.
"""

import json
import os
import sys

import numpy as np
from pyulog import ULog

WANTED = ["sim_schedule_applied", "vehicle_status", "sensor_gyro"]
ARMED = 2
NAV_OFFBOARD = 14


def decode_str(v):
    if isinstance(v, bytes):
        return v.split(b"\x00", 1)[0].decode(errors="replace")
    if isinstance(v, str):
        return v.split("\x00", 1)[0]
    return str(v)


def char_column(d, base, n):
    """Return a list of n decoded strings for a char[] field.

    pyulog may expose the field either as one column holding strings or as
    flattened byte columns named base[0], base[1], ...
    """
    if base in d:
        return [decode_str(x) for x in d[base]]
    keys = [k for k in d if k.startswith(base + "[")]
    if not keys:
        return None
    keys.sort(key=lambda k: int(k[len(base) + 1:-1]))
    out = []
    for i in range(n):
        raw = bytes(int(d[k][i]) & 0xFF for k in keys)
        out.append(raw.split(b"\x00", 1)[0].decode(errors="replace"))
    return out


def load_ulog(path):
    try:
        return ULog(path, message_name_filter_list=WANTED)
    except TypeError:
        return ULog(path)


def get_ds(ul, name, multi_id=0):
    for d in ul.data_list:
        if d.name == name and d.multi_id == multi_id:
            return d
    return None


def section_schedule(ul, res):
    ds = get_ds(ul, "sim_schedule_applied")
    if ds is None:
        res["errors"].append("topic sim_schedule_applied not found")
        return []
    d = ds.data
    ts = np.asarray(d["timestamp"], dtype=np.int64)
    n = len(ts)
    if "t_sched_us" not in d:
        res["errors"].append("sim_schedule_applied has no t_sched_us field")
        return []
    t_sched = np.asarray(d["t_sched_us"], dtype=np.int64)
    kinds_raw = d.get("kind")
    if kinds_raw is not None and np.asarray(kinds_raw).dtype.kind in "iu":
        # kind is a uint8 enum (KIND_* in msg/SimScheduleApplied.msg)
        names = {1: "arm", 2: "disarm", 3: "mode_offboard", 4: "sp"}
        kinds = [names.get(int(x), f"code{int(x)}") for x in kinds_raw]
    else:
        kinds = char_column(d, "kind", n)
    if kinds is None:
        res["errors"].append("sim_schedule_applied has no kind field")
        kinds = [None] * n
    rows = []
    for i in range(n):
        rows.append({
            "timestamp": int(ts[i]),
            "t_sched_us": int(t_sched[i]),
            "kind": kinds[i],
            "timestamp_minus_t_sched_us": int(ts[i]) - int(t_sched[i]),
        })
    return rows


def first_applied(rows, kind):
    for r in rows:
        if r["kind"] == kind:
            return r["timestamp"]
    return None


def section_vehicle_status(ul, res):
    ds = get_ds(ul, "vehicle_status")
    if ds is None:
        res["errors"].append("topic vehicle_status not found")
        return None, None
    d = ds.data
    ts = np.asarray(d["timestamp"], dtype=np.int64)
    arm_hits = np.flatnonzero(np.asarray(d["arming_state"]) == ARMED) if "arming_state" in d else None
    nav_hits = np.flatnonzero(np.asarray(d["nav_state"]) == NAV_OFFBOARD) if "nav_state" in d else None
    if arm_hits is None:
        res["errors"].append("vehicle_status has no arming_state field")
    if nav_hits is None:
        res["errors"].append("vehicle_status has no nav_state field")
    armed_ts = int(ts[arm_hits[0]]) if arm_hits is not None and arm_hits.size else None
    offboard_ts = int(ts[nav_hits[0]]) if nav_hits is not None and nav_hits.size else None
    if arm_hits is not None and arm_hits.size == 0:
        res["errors"].append("arming_state never reached 2 in vehicle_status")
    if nav_hits is not None and nav_hits.size == 0:
        res["errors"].append("nav_state never reached 14 in vehicle_status")
    return armed_ts, offboard_ts


def section_gyro_period(ul, res):
    ds = get_ds(ul, "sensor_gyro")
    if ds is None:
        res["errors"].append("topic sensor_gyro not found")
        return None, None
    d = ds.data
    if "timestamp_sample" not in d:
        res["errors"].append("sensor_gyro has no timestamp_sample field")
        return None, None
    tss = np.asarray(d["timestamp_sample"], dtype=np.int64)
    diffs = np.diff(tss)
    if diffs.size == 0:
        res["errors"].append("sensor_gyro has fewer than 2 samples")
        return None, None
    return float(np.median(diffs)), int(diffs.size)


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    ulog_path, out_path = sys.argv[1], sys.argv[2]

    res = {"log": ulog_path, "errors": []}
    ul = load_ulog(ulog_path)

    rows = section_schedule(ul, res)
    armed_ts, offboard_ts = section_vehicle_status(ul, res)

    arm_applied = first_applied(rows, "arm")
    off_applied = first_applied(rows, "mode_offboard")
    if arm_applied is None:
        res["errors"].append("no applied row with kind 'arm'")
    if off_applied is None:
        res["errors"].append("no applied row with kind 'mode_offboard'")

    gyro_median, gyro_n = section_gyro_period(ul, res)

    res["sim_schedule_applied"] = rows
    res["first_armed_timestamp"] = armed_ts
    res["first_offboard_timestamp"] = offboard_ts
    res["applied_arm_timestamp"] = arm_applied
    res["applied_mode_offboard_timestamp"] = off_applied
    res["armed_minus_applied_arm_us"] = (
        armed_ts - arm_applied if armed_ts is not None and arm_applied is not None else None)
    res["offboard_minus_applied_mode_offboard_us"] = (
        offboard_ts - off_applied if offboard_ts is not None and off_applied is not None else None)
    res["sensor_gyro_median_period_us"] = gyro_median
    res["sensor_gyro_num_periods"] = gyro_n

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {out_path}: {len(rows)} applied rows, errors={len(res['errors'])}")
    for e in res["errors"]:
        print("ERROR:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
