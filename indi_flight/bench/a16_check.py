#!/usr/bin/env python3
"""A-16 timestamp check for actuator_motors, esc_status and sensor_gyro.

After the first second of log, counts samples, inter-sample gaps (> 1.9 ms),
zero-dt pairs (dt == 0) and missing slots, using `timestamp` and, where the
field exists, `timestamp_sample`. Each zero-dt pair is classed as a duplicate
(all value fields equal) or different. Expected slots = window / 1.25 ms + 1.

Usage: python3 a16_check.py <flight.ulg> <out_dir>
Writes <out_dir>/a16_check.json and <out_dir>/a16_table.md, prints the table.
"""
import argparse
import json
import os

import numpy as np
from pyulog import ULog

PERIOD_US = 1250.0
GAP_US = 1900.0
SKIP_US = 1_000_000
TOPICS = ["actuator_motors", "esc_status", "sensor_gyro"]


def value_matrix(data, n):
    """Stack every value field (no timestamps, no padding) into an (n, m) float matrix."""
    cols = []
    for key in sorted(data.keys()):
        if key in ("timestamp", "timestamp_sample") or key.endswith(".timestamp") or "_padding" in key:
            continue
        try:
            col = np.asarray(data[key], dtype=float)
        except (TypeError, ValueError):
            continue
        if col.ndim >= 1 and col.shape[0] == n:
            cols.append(col.reshape(n, -1))
    return np.hstack(cols) if cols else np.zeros((n, 0))


def analyse(ts, M, t_cut, t_end):
    keep = (ts >= t_cut) & (ts <= t_end)
    ts = ts[keep]
    M = M[keep]
    n = int(ts.size)
    d = np.diff(ts)
    expected = (t_end - t_cut) / PERIOD_US + 1.0
    gap = d > GAP_US
    zero = d == 0
    k_zero = np.nonzero(zero)[0]
    ident = np.array(
        [np.array_equal(M[k], M[k + 1], equal_nan=True) for k in k_zero], dtype=bool
    )
    # gap within the 2 diffs before the pair (d[k-2], d[k-1])
    gap_before = np.array(
        [any(gap[j] for j in (k - 2, k - 1) if 0 <= j < gap.size) for k in k_zero], dtype=bool
    )
    gap_idx = np.nonzero(gap)[0]
    gap_then_zero = [bool(np.any(zero[j + 1:j + 3])) for j in gap_idx]
    missing = int(np.sum(np.maximum(np.round(d[gap] / PERIOD_US).astype(int) - 1, 0)))
    pos = d[d > 0]
    unique = 1 + int(pos.size)
    frac = lambda a, b: (a / b) if b else float("nan")
    return {
        "n": n,
        "expected": round(expected, 1),
        "n_vs_exp_pct": 100.0 * (n / expected - 1.0),
        "unique": unique,
        "unique_plus_missing_vs_exp_pct": 100.0 * ((unique + missing) / expected - 1.0),
        "gaps": int(gap.sum()),
        "missing_slots": missing,
        "zero_pairs": int(zero.sum()),
        "zero_identical": int(ident.sum()),
        "zero_different": int((~ident).sum()),
        "zero_gap_before_frac": frac(int(gap_before.sum()), k_zero.size),
        "gap_then_zero_frac": frac(sum(gap_then_zero), gap_idx.size),
        "neg_dt": int(np.sum(d < 0)),
        "median_dt_us": float(np.median(d)) if d.size else float("nan"),
        "frac_dt_nominal": frac(int(np.sum(np.abs(pos - PERIOD_US) <= 50.0)), pos.size),
        "value_cols": int(M.shape[1]),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulog", help="path to flight.ulg")
    ap.add_argument("out_dir", help="directory for a16_check.json and a16_table.md")
    args = ap.parse_args()

    ulog = ULog(args.ulog)
    t0 = int(ulog.start_timestamp)
    t_cut = t0 + SKIP_US
    topics = {d.name: d for d in ulog.data_list if d.name in TOPICS and d.multi_id == 0}
    missing = [t for t in TOPICS if t not in topics]
    if missing:
        raise SystemExit(f"missing topics: {missing}")
    t_end = min(int(np.max(np.asarray(topics[t].data["timestamp"]))) for t in TOPICS)

    results = {"log": os.path.abspath(args.ulog), "t0_us": t0, "window_us": [t_cut, t_end]}
    rows = []
    for name in TOPICS:
        data = topics[name].data
        ts = np.asarray(data["timestamp"], dtype=np.int64)
        M = value_matrix(data, ts.size)
        res = {"timestamp": analyse(ts, M, t_cut, t_end)}
        if "timestamp_sample" in data:
            tss = np.asarray(data["timestamp_sample"], dtype=np.int64)
            res["timestamp_sample"] = analyse(tss, M, t_cut, t_end)
        results[name] = res
        for field in ("timestamp", "timestamp_sample"):
            if field not in res:
                rows.append((name, field, None))
                continue
            rows.append((name, field, res[field]))

    hdr = ("| topic | field | n | expected | n vs exp | unique+missing vs exp | gaps | missing slots "
           "| zero pairs | identical | different | gap before pair | gap->zero | neg dt | median dt us "
           "| dt==1250 frac | value cols |")
    lines = [hdr, "|" + "---|" * 17]
    for name, field, r in rows:
        if r is None:
            lines.append(f"| {name} | {field} | n/a | | | | | | | | | | | | | | |")
            continue
        lines.append(
            f"| {name} | {field} | {r['n']} | {r['expected']:.1f} | {r['n_vs_exp_pct']:+.2f}% "
            f"| {r['unique_plus_missing_vs_exp_pct']:+.2f}% | {r['gaps']} | {r['missing_slots']} "
            f"| {r['zero_pairs']} | {r['zero_identical']} | {r['zero_different']} "
            f"| {r['zero_gap_before_frac']:.3f} | {r['gap_then_zero_frac']:.3f} | {r['neg_dt']} "
            f"| {r['median_dt_us']:.1f} | {r['frac_dt_nominal']:.4f} | {r['value_cols']} |"
        )
    table = "\n".join(lines) + "\n"

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "a16_check.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.out_dir, "a16_table.md"), "w") as f:
        f.write(table)
    print(f"window_us={t_cut}..{t_end} ({(t_end - t_cut) / 1e6:.3f} s)")
    print(table)


if __name__ == "__main__":
    main()
