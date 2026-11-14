#!/usr/bin/env python3
"""Per-scenario mean/std over seeds of key metrics, two controllers side by side, as a markdown table.
usage: summarize_seeds.py RUNS_DIR SCENARIO [SCENARIO ...] [--a pid_default] [--b indi_tuned]
Reads RUNS_DIR/<scenario>/<controller>/seed*/metrics.json. Ratio is mean(b)/mean(a); 'b<a' counts the seeds
(paired by seed number) where b is lower; 'med impr' is the median of 1 - b/a over paired seeds and 'p' the exact
two-sided Wilcoxon signed-rank p-value on the paired differences (acceptance test of scenarios.md section 6)."""
import argparse
import glob
import json
import os
import statistics

METRICS = [("att rot rms deg", "attitude_tracking.rotation_angle_rms_deg"),
           ("roll rms deg", "attitude_tracking.roll_rms_deg"),
           ("pitch rms deg", "attitude_tracking.pitch_rms_deg"),
           ("yaw rms deg", "attitude_tracking.yaw_rms_deg"),
           ("pos rms horiz m", "position.rms_horizontal_m"),
           ("pos max dev 3d m", "position.max_dev_3d_m"),
           ("motor rate rms /s", "effort.motor_rate_rms_per_s"),
           ("sat frac", "effort.saturation_frac_motors")]


def get(d, path):
    for k in path.split('.'):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d if isinstance(d, (int, float)) else None


def load(runs, scen, ctrl):
    out = {}
    for f in sorted(glob.glob(os.path.join(runs, scen, ctrl, 'seed*', 'metrics.json'))):
        out[os.path.basename(os.path.dirname(f))] = json.load(open(f))
    return out


def wilcoxon_exact(diffs):
    """Exact two-sided Wilcoxon signed-rank p-value, zeros dropped, average ranks for ties, n <= 20."""
    d = [x for x in diffs if x != 0.0]
    n = len(d)
    if n == 0:
        return 1.0
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    w_plus = sum(r for r, x in zip(ranks, d) if x > 0)
    centre = n * (n + 1) / 4.0
    extreme = 0
    for mask in range(1 << n):
        w = sum(ranks[k] for k in range(n) if mask >> k & 1)
        if abs(w - centre) >= abs(w_plus - centre) - 1e-9:
            extreme += 1
    return extreme / float(1 << n)


def fmt(v):
    return f"{statistics.mean(v):.3g} ± {statistics.stdev(v):.2g}" if len(v) > 1 else (f"{v[0]:.3g}" if v else "-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs')
    ap.add_argument('scenarios', nargs='+')
    ap.add_argument('--a', default='pid_default')
    ap.add_argument('--b', default='indi_tuned')
    a = ap.parse_args()
    for scen in a.scenarios:
        ra, rb = load(a.runs, scen, a.a), load(a.runs, scen, a.b)
        seeds = sorted(set(ra) & set(rb))
        print(f"\n### {scen} ({a.a} n={len(ra)}, {a.b} n={len(rb)}, paired {len(seeds)})\n")
        print(f"| metric | {a.a} | {a.b} | ratio b/a | b<a | med impr | p |\n|---|---|---|---|---|---|---|")
        for name, path in METRICS:
            va = [get(ra[s], path) for s in ra]
            vb = [get(rb[s], path) for s in rb]
            va, vb = [x for x in va if x is not None], [x for x in vb if x is not None]
            if not va or not vb:
                continue
            ma = statistics.mean(va)
            ratio = statistics.mean(vb) / ma if ma else float('nan')
            pairs = [(get(ra[s], path), get(rb[s], path)) for s in seeds]
            pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
            wins = sum(1 for x, y in pairs if y < x)
            impr = [1.0 - y / x for x, y in pairs if x]
            med = f"{statistics.median(impr) * 100:.0f} %" if impr else "-"
            pval = wilcoxon_exact([y - x for x, y in pairs])
            print(f"| {name} | {fmt(va)} | {fmt(vb)} | {ratio:.2f} | {wins}/{len(pairs)} | {med} | {pval:.3g} |")


if __name__ == '__main__':
    main()
