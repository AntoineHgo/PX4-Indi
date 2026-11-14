#!/usr/bin/env python3
"""Old vs new binary regression table (O-11): mean +- std over seeds of key metrics, per scenario, markdown.
usage: regress_compare.py OLD_PATTERN NEW_PATTERN SCENARIO [SCENARIO ...]
Patterns contain {sc}; seed*/metrics.json is read under each, e.g.
  regress_compare.py 'results/s2_recheck_v1/runs/{sc}/indi_frz' 'results/s2_o11_regress/runs/v1new/{sc}' hover
'z' is (mean_new - mean_old) / sqrt(std_old^2/n_old + std_new^2/n_new): |z| < 2 reads as within run-to-run noise."""
import glob
import json
import math
import os
import statistics as st
import sys

METRICS = [("roll rate rms", "rate_tracking.roll_rms_rad_s"),
           ("att rot rms deg", "attitude_tracking.rotation_angle_rms_deg"),
           ("yaw rms deg", "attitude_tracking.yaw_rms_deg"),
           ("motor rate rms /s", "effort.motor_rate_rms_per_s"),
           ("sat frac", "effort.saturation_frac_motors")]


def get(d, path):
    for k in path.split("."):
        d = d.get(k) if isinstance(d, dict) else None
    return d


def load(pattern, sc):
    out = []
    for f in sorted(glob.glob(os.path.join(pattern.format(sc=sc), "seed*", "metrics.json"))):
        out.append(json.load(open(f)))
    return out


def fmt(xs):
    if not xs:
        return "-"
    return f"{st.mean(xs):.4g} +- {st.pstdev(xs):.2g}"


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    old_p, new_p, scenarios = sys.argv[1], sys.argv[2], sys.argv[3:]
    print("| scenario | metric | old (n) | new (n) | new/old | z |")
    print("|---|---|---|---|---|---|")
    for sc in scenarios:
        a, b = load(old_p, sc), load(new_p, sc)
        for label, path in METRICS:
            xa = [v for v in (get(m, path) for m in a) if v is not None]
            xb = [v for v in (get(m, path) for m in b) if v is not None]
            ratio = z = "-"
            if xa and xb:
                ma, mb = st.mean(xa), st.mean(xb)
                ratio = f"{mb / ma:.3f}" if ma else "-"
                se = math.sqrt(st.pstdev(xa) ** 2 / len(xa) + st.pstdev(xb) ** 2 / len(xb))
                z = f"{(mb - ma) / se:+.1f}" if se > 0 else "-"
            print(f"| {sc} | {label} | {fmt(xa)} ({len(xa)}) | {fmt(xb)} ({len(xb)}) | {ratio} | {z} |")


if __name__ == "__main__":
    main()
