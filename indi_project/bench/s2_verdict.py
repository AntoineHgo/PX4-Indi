#!/usr/bin/env python3
"""v2 verdict on the held-out set V under the unchanged section-6 rules (bench/scenarios.md sec. 8).
usage: s2_verdict.py [RUNS_DIR] [--b indi_v2] [--a pid_tuned] [--hover-runs DIR] [--final]
Per V entry: primary metric (sec. 8 table), paired by seed, median improvement 1 - b/a and the exact two-sided
Wilcoxon p (summarize_seeds.wilcoxon_exact). A run fails when it has no metrics.json, run.json exit_status is not
'ok', or the primary metric is missing (sec. 4: failed runs are reported, never dropped). Criterion 4 (hover effort,
T1 on v2) reads hover from --hover-runs when given (the seen set), else it is reported as pending."""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summarize_seeds import get, load, wilcoxon_exact  # noqa: E402

ATT, RATE = "attitude_tracking.roll_rms_deg", "rate_tracking.roll_rms_rad_s"
ROT = "attitude_tracking.rotation_angle_rms_deg"
HOVER = "position.rms_3d_m"
EFFORT = "effort.motor_rate_rms_per_s"
# entry -> primary metric. V9 (T8 profile): sec. 3 says "attitude RMS after the event"; the window rotation-angle
# RMS is the sec. 4 attitude metric, chosen here before reading any V9 result.
PRIMARY = {"v2_tau2_att": ATT, "v2_tau2_rate": RATE, "v2_asym_att": ATT, "v2_asym_rate": RATE,
           "v2_lat_att": ATT, "v2_lat_rate": RATE, "v2_drop_att": ATT, "v2_drop_rate": RATE,
           "v2_vib3_hover": HOVER, "v2_vib3_att": ATT, "v2_sag_att": ATT,
           "gust_diag": ROT, "com_shift": ROT, "motor_loss_0": ROT}
SEEDS = [f"seed{i}" for i in range(1, 11)]
FINAL = False


def failed(runs, entry, ctrl, seed, metric):
    d = os.path.join(runs, entry, ctrl, seed)
    try:
        status = json.load(open(os.path.join(d, "run.json"))).get("exit_status")
    except (OSError, ValueError):
        status = None
    if status in ("running", None) and not FINAL:
        return False  # run.json is written at the end: no status means still flying unless the batch is over
    if status != "ok" or not os.path.isfile(os.path.join(d, "metrics.json")):
        return True
    return get(load(runs, entry, ctrl).get(seed, {}), metric) is None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            "..", "results", "s2_heldout_v2", "runs"))
    ap.add_argument("--a", default="pid_tuned")
    ap.add_argument("--b", default="indi_v2")
    ap.add_argument("--hover-runs")
    ap.add_argument("--final", action="store_true", help="batch ended: a run without run.json failed")
    a = ap.parse_args()
    global FINAL
    FINAL = a.final

    print(f"| entry | primary metric | {a.a} mean | {a.b} mean | ratio | b<a | med impr | p | effort ratio | "
          f"fails {a.a}/{a.b} | verdict |\n|---|---|---|---|---|---|---|---|---|---|---|")
    better = worse = n_complete = 0
    b_fails = []
    for entry, metric in PRIMARY.items():
        ra, rb = load(a.runs, entry, a.a), load(a.runs, entry, a.b)
        fa = sum(failed(a.runs, entry, a.a, s, metric) for s in SEEDS if os.path.isdir(os.path.join(a.runs, entry, a.a, s)))
        fb = [s for s in SEEDS if os.path.isdir(os.path.join(a.runs, entry, a.b, s)) and failed(a.runs, entry, a.b, s, metric)]
        b_fails += [f"{entry}/{s}" for s in fb]
        pairs = [(get(ra[s], metric), get(rb[s], metric)) for s in sorted(set(ra) & set(rb))]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        eff = [(get(ra[s], EFFORT), get(rb[s], EFFORT)) for s in sorted(set(ra) & set(rb))]
        eff = [y / x for x, y in eff if x and y is not None]
        if not pairs:
            print(f"| {entry} | {metric} | - | - | - | - | - | - | - | {fa}/{len(fb)} | no data |")
            continue
        n_complete += len(pairs) == 10
        ma, mb = statistics.mean(x for x, _ in pairs), statistics.mean(y for _, y in pairs)
        med = statistics.median(1.0 - y / x for x, y in pairs if x)
        p = wilcoxon_exact([y - x for x, y in pairs])
        verdict = "n.s."
        if p < 0.05 and med >= 0.10:
            verdict, better = "better", better + 1
        elif p < 0.05 and med <= -0.10:
            verdict, worse = "**worse**", worse + 1
        elif p < 0.05:
            verdict = "better < 10 %" if med > 0 else "worse < 10 %"
        wins = sum(y < x for x, y in pairs)
        print(f"| {entry} | {metric} | {ma:.4g} | {mb:.4g} | {mb / ma:.2f} | {wins}/{len(pairs)} | {med * 100:.0f} % | "
              f"{p:.3g} | {statistics.median(eff):.2f} | {fa}/{len(fb)} | {verdict} |")

    print(f"\nComplete entries (10 paired seeds): {n_complete}/{len(PRIMARY)}")
    print(f"1. INDI failures in V: {len(b_fails)} {b_fails if b_fails else ''} (seen/T entries: see the seen set)")
    print(f"2. significantly better (>= 10 %, p < 0.05): {better}/{len(PRIMARY)} (needs >= 10)")
    print(f"3. significantly worse by > 10 %: {worse} (needs 0)")
    if a.hover_runs:
        ra, rb = load(a.hover_runs, "hover", a.a), load(a.hover_runs, "hover", a.b)
        ea = [get(ra[s], EFFORT) for s in ra]
        eb = [get(rb[s], EFFORT) for s in rb]
        ea, eb = [x for x in ea if x is not None], [x for x in eb if x is not None]
        if ea and eb:
            r = statistics.mean(eb) / statistics.mean(ea)
            print(f"4. hover effort ratio (T1, v2): {r:.2f} (needs <= 1.5; n = {len(ea)}/{len(eb)})")
    else:
        print("4. hover effort (T1, v2): pending, pass --hover-runs results/s2_seen_v2/runs")
    c1, c3 = not b_fails, worse == 0
    outcome = ("INDI outperforms PID" if c1 and c3 and better >= 10 else
               "INDI matches PID" if c1 and c3 else "INDI does not outperform PID")
    print(f"\nOutcome on criteria 1-3 (V only; criterion 1 also needs the seen/T entries, criterion 4 hover): {outcome}")


if __name__ == "__main__":
    main()
