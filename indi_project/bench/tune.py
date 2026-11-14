#!/usr/bin/env python3
"""Tuning driver: one procedure, one cost J, two parameter spaces (PID, INDI).

Usage (from the repo root):
  python3 indi_project/bench/tune.py --family {pid,indi} --n-candidates 24 --seeds 1 2 --jobs 6 \
      --sampler-seed 0 [--base-params indi_project/bench/params/indi_v1.params] \
      [--round-name r1] [--center CANDIDATE_JSON] [--span-factor 2.0] [--vary NAME ...] \
      [--scenarios hover step_roll ...] [--dry-run]

Candidates: Latin hypercube in log-space, each parameter in [center/span, center*span] (clamped to the parameter
min/max from the PX4 YAML); candidate 0 is the center. Each flight goes through bench/run_batch.sh (so through
run_scenario.py and metrics.py exactly as for the plain batches) with a PARAMS_FILE overlay.
The reference is `pid_default` (no overlay) under results/runs/<scenario>/pid_default/, run first if missing.

Cost per (scenario, seed): ratio = primary / primary_ref, plus 0.2 * (effort_ratio - 1) if effort_ratio > 1.25,
or 10 for a failed run (no ULog, runner rc != 0, missing metric). J = mean over (scenario, seed).
Output: results/tuning/<family>/<round>/c<NN>/params, c<NN>/<scenario>/seed<S>[_x4]/, summary.csv, candidates.json.
Runs whose metrics.json already exists are skipped (resumable). --center accepts a JSON file holding either
{"NAME": value, ...} or a summary-style record {"params": {...}}.
"""
import argparse
import csv
import json
import math
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(BENCH_DIR)
REPO_DIR = os.path.dirname(PROJ_DIR)
RUN_BATCH = os.path.join(BENCH_DIR, "run_batch.sh")
REF_ROOT = os.path.join(PROJ_DIR, "results", "runs")
TUNE_ROOT = os.path.join(PROJ_DIR, "results", "tuning")
YAMLS = [os.path.join(REPO_DIR, "src/modules/mc_rate_control/mc_rate_control_params.yaml"),
         os.path.join(REPO_DIR, "src/modules/mc_att_control/mc_att_control_params.yaml")]

SPACES = {
    "pid": ["MC_ROLLRATE_P", "MC_ROLLRATE_I", "MC_ROLLRATE_D", "MC_PITCHRATE_P", "MC_PITCHRATE_I", "MC_PITCHRATE_D",
            "MC_YAWRATE_P", "MC_YAWRATE_I", "MC_YAW_TQ_CUTOFF", "MC_ROLL_P", "MC_PITCH_P",
            "MC_YAW_P"],
    "indi": ["MC_INDI_K_R", "MC_INDI_K_P", "MC_INDI_K_Y", "MC_INDI_ACT_TC", "MC_INDI_YAW_CUT", "MC_ROLL_P", "MC_PITCH_P", "MC_YAW_P"],
}
# scenario -> (speed, primary metric (section, key))
SCENARIOS = {
    "hover": (1, ("position", "rms_3d_m")),
    "step_roll": (4, ("attitude_tracking", "roll_rms_deg")),
    "step_pitch": (4, ("attitude_tracking", "pitch_rms_deg")),
    "step_yaw": (4, ("attitude_tracking", "yaw_rms_deg")),
    "rate_step_roll": (4, ("rate_tracking", "roll_rms_rad_s")),
}
EFFORT = ("effort", "motor_rate_rms_per_s")
EFFORT_LIMIT, EFFORT_WEIGHT, FAIL_COST = 1.25, 0.2, 10.0
RUN_TIMEOUT_S = 700  # wall guard around run_batch.sh; each container itself is limited to 600 s (-t)


def read_yaml_params(paths):
    """Minimal parser: name -> {default, min, max} for the PX4 parameter YAML files (no PyYAML needed)."""
    out, cur = {}, None
    for p in paths:
        for line in open(p):
            m = re.match(r"^    ([A-Z0-9_]+):\s*$", line)
            if m:
                cur = out.setdefault(m.group(1), {})
                continue
            m = re.match(r"^\s+(default|min|max):\s*(\S+)", line)
            if m and cur is not None:
                try:
                    cur[m.group(1)] = float(m.group(2))
                except ValueError:
                    pass
    return out


def read_params_file(path):
    out = {}
    if path:
        for line in open(path):
            line = line.split("#")[0].strip()
            if line:
                k, v = line.split(None, 1)
                out[k] = v.strip()
    return out


def load_center(names, base_lines, center_json, meta):
    center, src = {}, {}
    for n in names:
        if n in base_lines:
            center[n], src[n] = float(base_lines[n]), "base-params"
        elif n in meta and "default" in meta[n]:
            center[n], src[n] = meta[n]["default"], "yaml default"
        else:
            sys.exit(f"no center value for {n}")
    if center_json:
        d = json.load(open(center_json))
        d = d.get("params", d)
        for n in names:
            if n in d:
                center[n], src[n] = float(d[n]), "--center"
    return center, src


def make_candidates(names, center, n, span, sampler_seed, meta, vary=None):
    """Candidate 0 = center; candidates 1..n-1 = Latin hypercube in log space over [c/span, c*span].
    Parameters not in vary (when given) stay at the center."""
    rng = np.random.default_rng(sampler_seed)
    d, m = len(names), max(n - 1, 0)
    # LHS: one point per stratum of each dimension, strata shuffled independently per dimension
    u = (np.array([rng.permutation(m) for _ in range(d)]).T + rng.random((m, d))) / max(m, 1) if m else np.zeros((0, d))
    logc = np.log(np.array([center[k] for k in names]))
    cands = [dict(center)]
    for i in range(m):
        row = {}
        for j, k in enumerate(names):
            if vary is not None and k not in vary:
                row[k] = center[k]
                continue
            v = math.exp(logc[j] + (2 * u[i, j] - 1) * math.log(span))
            lo, hi = meta.get(k, {}).get("min", -math.inf), meta.get(k, {}).get("max", math.inf)
            row[k] = float(f"{min(max(v, lo), hi):.4g}")
        cands.append(row)
    return cands


def metric(d, sec_key):
    try:
        v = d[sec_key[0]][sec_key[1]]
        return float(v) if v is not None and math.isfinite(float(v)) else None
    except (KeyError, TypeError, ValueError):
        return None


def run_dir(root, scn, seed, speed, flat=True, ctl="pid_default"):
    sfx = "" if speed == 1 else f"_x{speed}"
    return os.path.join(root, scn, f"seed{seed}{sfx}") if flat else os.path.join(root, scn, ctl, f"seed{seed}{sfx}")


def fly(scn, seed, speed, label, params_file, results_dir, flat, tag, log_lock):
    """Run one flight via run_batch.sh unless metrics.json exists. Returns True when metrics.json exists after."""
    out = run_dir(results_dir, scn, seed, speed, flat, label)
    if os.path.exists(os.path.join(out, "metrics.json")):
        return True
    env = dict(os.environ, SCENARIOS=scn, CONTROLLERS=label, SEEDS=str(seed), SPEEDS=str(speed), JOBS="1",
               TIMEOUT="600", RESULTS_DIR=results_dir, FLAT_LAYOUT="1" if flat else "0", NAME_TAG=tag)
    if params_file:
        env["PARAMS_FILE"] = params_file
    else:
        env.pop("PARAMS_FILE", None)
    try:
        r = subprocess.run(["bash", RUN_BATCH], env=env, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
        rc, tail = r.returncode, r.stdout.strip().splitlines()[-1:]
    except subprocess.TimeoutExpired:
        rc, tail = -1, ["timeout"]
        subprocess.run(["docker", "rm", "-f", f"px4-indi-{scn}-{seed}{'-x%d' % speed if speed != 1 else ''}-{tag}"],
                       capture_output=True)
    with log_lock:
        print(f"[tune] {tag} {scn} seed{seed} x{speed} rc={rc} {' '.join(tail)}", flush=True)
    return os.path.exists(os.path.join(out, "metrics.json"))


def load_metrics(path):
    try:
        return json.load(open(os.path.join(path, "metrics.json")))
    except (OSError, ValueError):
        return None


def score(cand_dir, scenarios, seeds, refs):
    """Return (J, ratios per scenario (mean over seeds), n_failures)."""
    terms, ratios, fails = [], {}, 0
    for scn in scenarios:
        speed, key = SCENARIOS[scn]
        rs = []
        for s in seeds:
            m = load_metrics(run_dir(cand_dir, scn, s, speed))
            ref = refs[(scn, s)]
            p = metric(m, key) if m else None
            e = metric(m, EFFORT) if m else None
            if p is None or e is None:
                fails += 1
                terms.append(FAIL_COST)
                continue
            ratio = p / ref[0]
            er = e / ref[1]
            term = ratio + (EFFORT_WEIGHT * (er - 1) if er > EFFORT_LIMIT else 0.0)
            rs.append(ratio)
            terms.append(term)
        ratios[scn] = float(np.mean(rs)) if rs else float("nan")
    return float(np.mean(terms)), ratios, fails


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=sorted(SPACES))
    ap.add_argument("--n-candidates", type=int, default=24)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--scenarios", nargs="+", default=list(SCENARIOS), choices=sorted(SCENARIOS))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--sampler-seed", type=int, default=0)
    ap.add_argument("--base-params", default=None, help="params file whose lines come first in every candidate file")
    ap.add_argument("--round-name", default="r1")
    ap.add_argument("--center", default=None, help="JSON with the center values (overrides defaults / base params)")
    ap.add_argument("--span-factor", type=float, default=2.0)
    ap.add_argument("--vary", nargs="+", default=None, help="only these parameters vary, the others stay at the center")
    ap.add_argument("--dry-run", action="store_true", help="print candidates and the run plan, do not fly")
    a = ap.parse_args()

    names = SPACES[a.family]
    meta = read_yaml_params(YAMLS)
    base_path = os.path.abspath(a.base_params) if a.base_params else None
    base_lines = read_params_file(base_path)
    center, src = load_center(names, base_lines, a.center, meta)
    if a.vary is not None and not set(a.vary) <= set(names):
        ap.error(f"--vary names must be in {names}")
    cands = make_candidates(names, center, a.n_candidates, a.span_factor, a.sampler_seed, meta, a.vary)
    root = os.path.join(TUNE_ROOT, a.family, a.round_name)

    print(f"[tune] family={a.family} round={a.round_name} n={len(cands)} span={a.span_factor} "
          f"sampler_seed={a.sampler_seed} scenarios={a.scenarios} seeds={a.seeds}")
    print("[tune] center: " + ", ".join(f"{k}={center[k]:g} ({src[k]})" for k in names))
    for i, c in enumerate(cands):
        print(f"  c{i:02d} " + " ".join(f"{k}={c[k]:.4g}" for k in names))
    n_ref = len(a.scenarios) * len(a.seeds)
    print(f"[tune] plan: {n_ref} reference flights (pid_default, skipped if present) + "
          f"{len(cands) * n_ref} candidate flights, jobs={a.jobs}")
    if a.dry_run:
        return 0

    os.makedirs(root, exist_ok=True)
    json.dump({"family": a.family, "names": names, "center": center, "center_source": src, "span": a.span_factor,
               "sampler_seed": a.sampler_seed, "base_params": base_path, "candidates": cands},
              open(os.path.join(root, "candidates.json"), "w"), indent=1)
    base_text = open(base_path).read().rstrip("\n") + "\n" if base_path else ""
    for i, c in enumerate(cands):
        d = os.path.join(root, f"c{i:02d}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "params"), "w") as f:
            f.write(base_text + "".join(f"{k} {c[k]:.6g}\n" for k in names))

    lock = threading.Lock()
    # 1. reference flights (pid_default) first
    refs, bad = {}, False
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(fly, scn, s, SCENARIOS[scn][0], "pid_default", None, REF_ROOT, False,
                          f"ref-{a.family}-{a.round_name}", lock): (scn, s)
                for scn in a.scenarios for s in a.seeds}
        for f in as_completed(futs):
            f.result()
    for scn in a.scenarios:
        speed, key = SCENARIOS[scn]
        for s in a.seeds:
            m = load_metrics(run_dir(REF_ROOT, scn, s, speed, False))
            p, e = (metric(m, key), metric(m, EFFORT)) if m else (None, None)
            if not p or not e:
                print(f"[tune] ERROR: reference pid_default {scn} seed{s} missing/invalid", file=sys.stderr)
                bad = True
            refs[(scn, s)] = (p, e)
    if bad:
        return 2

    # 2. candidate flights, candidate-major; summary rewritten whenever a candidate completes
    rows, remaining = {}, {i: len(a.scenarios) * len(a.seeds) for i in range(len(cands))}
    cols = (["cand", "J", "failures"] + [f"ratio_{s}" for s in a.scenarios] + names)

    def write_summary():
        with open(os.path.join(root, "summary.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for i in sorted(rows):
                r = rows[i]
                w.writerow([f"c{i:02d}", f"{r['J']:.5f}", r["fails"]] +
                           [f"{r['ratios'][s]:.5f}" for s in a.scenarios] + [f"{cands[i][k]:.6g}" for k in names])

    def finish(i):
        J, ratios, fails = score(os.path.join(root, f"c{i:02d}"), a.scenarios, a.seeds, refs)
        rows[i] = {"J": J, "ratios": ratios, "fails": fails}
        write_summary()
        print(f"[tune] c{i:02d} done: J={J:.4f} failures={fails}", flush=True)

    with ThreadPoolExecutor(a.jobs) as ex:
        futs = {}
        for i in range(len(cands)):
            pf = os.path.join(root, f"c{i:02d}", "params")
            for scn in a.scenarios:
                for s in a.seeds:
                    fut = ex.submit(fly, scn, s, SCENARIOS[scn][0], f"{a.family}_{a.round_name}_c{i:02d}", pf,
                                    os.path.join(root, f"c{i:02d}"), True, f"c{i:02d}-{a.family}-{a.round_name}", lock)
                    futs[fut] = i
        for f in as_completed(futs):
            i = futs[f]
            f.result()
            with lock:
                remaining[i] -= 1
                if remaining[i] == 0:
                    finish(i)

    best = sorted(rows, key=lambda i: rows[i]["J"] if math.isfinite(rows[i]["J"]) else math.inf)[:5]
    print("[tune] best 5:")
    for i in best:
        print(f"  c{i:02d} J={rows[i]['J']:.4f} failures={rows[i]['fails']} " +
              " ".join(f"{k}={cands[i][k]:.4g}" for k in names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
