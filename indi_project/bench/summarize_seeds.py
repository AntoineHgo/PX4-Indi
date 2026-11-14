#!/usr/bin/env python3
"""Per-scenario mean/std over seeds of key metrics, two controllers side by side, as a markdown table.
usage: summarize_seeds.py RUNS_DIR SCENARIO [SCENARIO ...] [--a pid_default] [--b indi_tuned]
Reads RUNS_DIR/<scenario>/<controller>/seed*/metrics.json. Ratio is mean(b)/mean(a); 'b<a' counts the seeds
(paired by seed number) where b is lower."""
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
        print(f"| metric | {a.a} | {a.b} | ratio b/a | b<a |\n|---|---|---|---|---|")
        for name, path in METRICS:
            va = [get(ra[s], path) for s in ra]
            vb = [get(rb[s], path) for s in rb]
            va, vb = [x for x in va if x is not None], [x for x in vb if x is not None]
            if not va or not vb:
                continue
            ma = statistics.mean(va)
            ratio = statistics.mean(vb) / ma if ma else float('nan')
            pairs = [(get(ra[s], path), get(rb[s], path)) for s in seeds]
            wins = sum(1 for x, y in pairs if x is not None and y is not None and y < x)
            print(f"| {name} | {fmt(va)} | {fmt(vb)} | {ratio:.2f} | {wins}/{len(pairs)} |")


if __name__ == '__main__':
    main()
