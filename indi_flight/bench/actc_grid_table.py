#!/usr/bin/env python3
"""ACT_TC identification grid: error table and ratio statistics.

Usage: python3 indi_flight/bench/actc_grid_table.py [GRID.tsv]
Ratios: r_slow = tau_sym_hat / tau_slow, r_mean = tau_sym_hat / tau_mean.
Percentile: numpy.percentile(..., 95), method "linear" (interpolation between
order statistics at rank 0.95*(n-1)); n is small, so it is close to the max.
Frames column is reported as is; in S209 it was inert (A-59).
"""
import csv
import sys

import numpy as np

DEFAULT = "indi_flight/results/actc_grid_s209/GRID.tsv"


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = []
    for r in rows:
        d = dict(cell=r["cell"], asym=r["asym"], dir=r["dir"], dly=float(r["dly_ms"]),
                 pas=r["pass"].strip(), flags=r["flags"].strip(), status=r["status"].strip())
        for k in ("true_up", "true_down", "true_mean", "true_slow",
                  "est_up", "est_down", "est_sym", "est_delay_ms"):
            d[k] = float(r[k]) if r[k].strip() not in ("", "nan") else float("nan")
        d["cls"] = "1" if r["asym"] == "1" else "3" + r["dir"]
        d["up"] = d["est_up"] / d["true_up"]
        d["down"] = d["est_down"] / d["true_down"]
        d["r_slow"] = d["est_sym"] / d["true_slow"]
        d["r_mean"] = d["est_sym"] / d["true_mean"]
        d["ddly"] = d["est_delay_ms"] - d["dly"]
        d["ok"] = d["pas"] in ("1", "PASS", "True") and d["flags"] == "" and d["status"] == "done"
        out.append(d)
    return out


def stats(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None
    return v.min(), v.max(), float(np.percentile(v, 95)), v.size


def main(path):
    rows = load(path)
    print("cell                 up/true down/true r_slow r_mean ddly_ms ok")
    for d in rows:
        print(f"{d['cell']:20s} {d['up']:8.3f} {d['down']:9.3f} {d['r_slow']:6.3f} "
              f"{d['r_mean']:6.3f} {d['ddly']:7.2f} {'PASS' if d['ok'] else 'FAIL'}")
    print("\nratio stats (min / max / p95, n)")
    for name in ("overall", "1", "3d", "3u"):
        sel = [d for d in rows if d["ok"] and (name == "overall" or d["cls"] == name)]
        for k in ("r_slow", "r_mean"):
            s = stats([d[k] for d in sel])
            if s:
                print(f"{name:8s} {k:7s} {s[0]:.4f} {s[1]:.4f} {s[2]:.4f} n={s[3]}")
    ok = [d for d in rows if d["ok"]]
    for k in ("up", "down"):
        e = max(abs(d[k] - 1) for d in ok)
        print(f"max |est/true-1| tau_{k}: {e:.4f}")
    dd = [d["ddly"] for d in ok]
    print(f"delay_hat - true: min {min(dd):.2f} max {max(dd):.2f} ms")
    for dl in sorted({d["dly"] for d in ok}):
        x = [d["ddly"] for d in ok if d["dly"] == dl]
        print(f"  true delay {dl:g} ms: bias {min(x):.2f}..{max(x):.2f} ms (n={len(x)})")
    bad = [d for d in rows if not d["ok"]]
    print(f"\nfailed identifications: {len(bad)}")
    for d in bad:
        print(f"  {d['cell']}: pass={d['pas']} status={d['status']} flags={d['flags'] or '-'}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
