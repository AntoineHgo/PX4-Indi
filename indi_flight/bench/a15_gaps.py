#!/usr/bin/env python3
"""Sample-gap analysis for a PX4 ULog.

Lists inter-sample gaps (> 1.9 ms, i.e. at least one missing 1.25 ms sample at
800 Hz) per topic, merges gap times across topics (within 1 ms), and reports
logger dropouts and whether they coincide with gap times.

Usage: python3 a15_gaps.py <flight.ulg> --out <report.md>
"""
import argparse
import os

import numpy as np
from pyulog import ULog

TOPICS = [
    "sensor_gyro",
    "vehicle_angular_velocity",
    "actuator_motors",
    "vehicle_torque_setpoint",
    "esc_status",
    "vehicle_attitude_groundtruth",
    "vehicle_angular_velocity_groundtruth",
    "vehicle_local_position_groundtruth",
    "sim_ground_truth",  # S21: sim-only truth, queue 16
]
GAP_THRESHOLD_US = 1900.0  # > 1.9 ms: at least one missing 1.25 ms sample
PERIOD_US = 1250.0  # nominal 800 Hz period
SKIP_FIRST_US = 1_000_000  # ignore the first second of the log
MERGE_US = 1000.0  # gap times within 1 ms are the same row


def gaps_in(ts_us, t_min):
    """Return ([(start_us, dt_us)], dts) for gaps > threshold starting at or after t_min.

    dts holds every consecutive interval (after t_min) for median-period estimation.
    """
    ts = np.asarray(ts_us, dtype=np.int64)
    if ts.size < 2:
        return [], np.array([], dtype=np.int64)
    if np.any(np.diff(ts) < 0):
        ts = np.sort(ts)
    dt = np.diff(ts)
    active = ts[:-1] >= t_min
    sel = active & (dt > GAP_THRESHOLD_US)
    gaps = list(zip(ts[:-1][sel].tolist(), dt[sel].tolist()))
    return gaps, dt[active]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulog", help="path to flight.ulg")
    ap.add_argument("--out", required=True, help="markdown report path")
    args = ap.parse_args()

    ulog = ULog(args.ulog)
    t0 = int(ulog.start_timestamp)
    t_min = t0 + SKIP_FIRST_US

    def rel(t_us):
        return (t_us - t0) / 1e6

    labels = []
    summaries = []
    events = []  # (t_us, label, dt_us)
    missing_topics = []

    for topic in TOPICS:
        insts = [d for d in ulog.data_list if d.name == topic]
        if not insts:
            missing_topics.append(topic)
            continue
        for inst in insts:
            label = topic if len(insts) == 1 else f"{topic}[{inst.multi_id}]"
            labels.append(label)
            ts = np.asarray(inst.data["timestamp"], dtype=np.int64)
            gaps, dts = gaps_in(ts, t_min)
            median_ms = float(np.median(dts)) / 1000.0 if dts.size else float("nan")
            skipped = bool(dts.size) and median_ms * 1000.0 > GAP_THRESHOLD_US
            row = {
                "label": label,
                "n": int(np.count_nonzero(ts >= t_min)),
                "median_ms": median_ms,
                "gaps": 0,
                "missing": 0,
                "skipped": skipped,
                "has_ts_sample": "timestamp_sample" in inst.data,
                "ts_gaps": None,
                "ts_matched": None,
            }
            if not skipped:
                for t, dt in gaps:
                    events.append((t, label, dt))
                row["gaps"] = len(gaps)
                row["missing"] = sum(max(round(dt / PERIOD_US) - 1, 0) for _, dt in gaps)
            if row["has_ts_sample"]:
                tss = np.asarray(inst.data["timestamp_sample"], dtype=np.int64)
                tg, _ = gaps_in(tss, t_min)
                row["ts_gaps"] = len(tg)
                gs = np.sort(np.array([t for t, _ in gaps], dtype=np.int64))
                matched = 0
                if gs.size:
                    for t, _ in tg:
                        if np.min(np.abs(gs - t)) <= MERGE_US:
                            matched += 1
                row["ts_matched"] = matched
            summaries.append(row)

    # Merge gap events across topics into rows (chain within MERGE_US).
    events.sort()
    rows = []
    for t, label, dt in events:
        if rows and t - rows[-1]["last"] <= MERGE_US:
            r = rows[-1]
        else:
            r = {"start": t, "last": t, "cells": {}}
            rows.append(r)
        r["last"] = t
        r["cells"][label] = max(r["cells"].get(label, 0), dt)

    # Logger dropouts.
    dropouts = []
    for d in getattr(ulog, "dropouts", []):
        t = int(d.timestamp)
        dur_ms = float(d.duration)
        lo = t - dur_ms * 1000.0 - MERGE_US
        hi = t + MERGE_US
        in_window = [r for r in rows if lo <= r["start"] <= hi]
        nearest = min(rows, key=lambda r: abs(r["start"] - t)) if rows else None
        dropouts.append({
            "t": t,
            "dur_ms": dur_ms,
            "matched": bool(in_window),
            "nearest_s": rel(nearest["start"]) if nearest else None,
            "nearest_delta_ms": (nearest["start"] - t) / 1000.0 if nearest else None,
            "before_skip": t < t_min,
        })

    n_single = sum(1 for r in rows if len(r["cells"]) == 1)
    n_multi = sum(1 for r in rows if len(r["cells"]) >= 2)

    L = []
    L.append("# A-15 sample-gap analysis")
    L.append("")
    L.append(f"- Log: `{args.ulog}`")
    L.append(f"- Log start timestamp: {t0} us. First {SKIP_FIRST_US/1e6:.0f} s ignored.")
    L.append(f"- Gap threshold: dt > {GAP_THRESHOLD_US/1000:.1f} ms (nominal period {PERIOD_US/1000:.2f} ms).")
    L.append(f"- Merge window for coincident gap times: {MERGE_US/1000:.1f} ms.")
    L.append(f"- Topics not in log: {', '.join(missing_topics) if missing_topics else 'none'}")
    L.append("")
    L.append("## Per-topic summary")
    L.append("")
    L.append("| topic | samples (after 1 s) | median period (ms) | gap intervals | missing samples (est.) | timestamp_sample field | timestamp_sample gap intervals | of those, within 1 ms of a timestamp gap | note |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for s in summaries:
        note = ""
        if s["skipped"]:
            note = "skipped: median period above gap threshold, every interval would be a gap"
        L.append("| {} | {} | {:.3f} | {} | {} | {} | {} | {} | {} |".format(
            s["label"], s["n"], s["median_ms"],
            "-" if s["skipped"] else s["gaps"],
            "-" if s["skipped"] else s["missing"],
            "yes" if s["has_ts_sample"] else "no",
            "-" if s["ts_gaps"] is None else s["ts_gaps"],
            "-" if s["ts_matched"] is None else s["ts_matched"],
            note,
        ))
    L.append("")
    L.append(f"Gap times merged across topics: {len(rows)} rows. "
             f"Rows where one topic has a gap: {n_single}. Rows where two or more topics have a gap at the same time: {n_multi}.")
    L.append("")
    L.append("## Gap table (rows = distinct gap times; cell = gap length in ms for that topic, blank = no gap)")
    L.append("")
    head = "| # | start (s, log time) | topics with gap | " + " | ".join(labels) + " |"
    L.append(head)
    L.append("|" + "---|" * (len(labels) + 3))
    for i, r in enumerate(rows, 1):
        cells = [f"{r['cells'][lb] / 1000:.2f}" if lb in r["cells"] else "" for lb in labels]
        L.append(f"| {i} | {rel(r['start']):.4f} | {len(r['cells'])} | " + " | ".join(cells) + " |")
    L.append("")
    # Pairwise coincidence: share of row-topic gap times that have a gap in the column topic within 1 ms.
    by_label = {}
    for t, label, _ in events:
        by_label.setdefault(label, []).append(t)
    by_label = {k: np.sort(np.array(v, dtype=np.int64)) for k, v in by_label.items()}
    pair_labels = [lb for lb in labels if lb in by_label]

    def n_coincident(a, b):
        A, B = by_label[a], by_label[b]
        if B.size == 1:
            d = np.abs(A - B[0])
        else:
            i = np.clip(np.searchsorted(B, A), 1, B.size - 1)
            d = np.minimum(np.abs(A - B[i - 1]), np.abs(A - B[i]))
        return int(np.count_nonzero(d <= MERGE_US))

    L.append("## Pairwise coincidence")
    L.append("")
    L.append("Cell = share of the row topic's gap times that have a gap in the column topic within 1 ms.")
    L.append("")
    L.append("| row topic (gaps) | " + " | ".join(pair_labels) + " |")
    L.append("|" + "---|" * (len(pair_labels) + 1))
    for a in pair_labels:
        na = by_label[a].size
        cells = [f"{100.0 * n_coincident(a, b) / na:.0f}%" for b in pair_labels]
        L.append(f"| {a} ({na}) | " + " | ".join(cells) + " |")
    L.append("")

    L.append("## Logger dropouts (pyulog `ULog.dropouts`)")
    L.append("")
    if not dropouts:
        L.append("No logging_dropout messages in this log.")
    else:
        L.append("| dropout time (s) | duration (ms, as logged) | before 1 s skip | matches a gap time | nearest gap row (s) | delta to dropout (ms) |")
        L.append("|---|---|---|---|---|---|")
        for d in dropouts:
            L.append("| {:.4f} | {:.1f} | {} | {} | {} | {} |".format(
                rel(d["t"]), d["dur_ms"], "yes" if d["before_skip"] else "no",
                "yes" if d["matched"] else "no",
                "-" if d["nearest_s"] is None else f"{d['nearest_s']:.4f}",
                "-" if d["nearest_delta_ms"] is None else f"{d['nearest_delta_ms']:.2f}",
            ))
    L.append("")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(L) + "\n")

    print(f"wrote {args.out}")
    print(f"topics missing: {missing_topics}")
    for s in summaries:
        print(f"{s['label']}: samples={s['n']} median={s['median_ms']:.3f} ms gaps={s['gaps']} "
              f"missing={s['missing']} skipped={s['skipped']} ts_sample_gaps={s['ts_gaps']} matched={s['ts_matched']}")
    print(f"merged gap rows={len(rows)} single-topic={n_single} multi-topic={n_multi}")
    print(f"dropouts={len(dropouts)} matched={sum(1 for d in dropouts if d['matched'])}")


if __name__ == "__main__":
    main()
