#!/usr/bin/env python3
"""G1 evidence integrity: how long after its intended sim time was each send applied in PX4 (as seen in the ULog)?

  applied_timing.py run_dir [run_dir ...] [--tol 1e-3] [--window-s 2] [--physics-step-us 4000]

Per run_dir reads sends.csv (+ run.json for optional step overrides) and flight.ulg, writes applied_timing.json.
delay = first matching logged sample at or after intended_sim_time_us, minus intended_sim_time_us (ULog time base =
sim time). Rows matching several samples use the first. Rows with no match in the window are reported as unmatched
(never dropped). The delay can not be finer than the logged topic period (reported as topic_period_us): when the
payload is constant (hover hold) every sample matches and the delay only measures log decimation; the
`changed` subset (payload differs from the previous send of the same kind) is the informative one.
pyulog is imported lazily so the matching functions and their self-test work without it.
"""
import argparse
import csv
import json
import math
import os
import sys

import numpy as np

PHYSICS_STEP_US = 4000  # gz physics step (port_1a_runner.md); override with run.json physics_step_us
ATTITUDE_STEP_US = 10000

# send kind -> (ulog topic, {payload key: ulog column}); NaN payload/column values never match
KIND_MAP = {
    "send_pos": ("trajectory_setpoint", {"x": "position[0]", "y": "position[1]", "z": "position[2]", "yaw": "yaw"}),
    "send_pva": ("trajectory_setpoint", {"x": "position[0]", "y": "position[1]", "z": "position[2]",
                                         "vx": "velocity[0]", "vy": "velocity[1]", "vz": "velocity[2]",
                                         "ax": "acceleration[0]", "ay": "acceleration[1]", "az": "acceleration[2]",
                                         "yaw": "yaw"}),
    # offboard attitude/rate: columns UNVERIFIED (no such run yet). attitude q_d is converted to euler by load_topics.
    "send_att": ("vehicle_attitude_setpoint", {"roll": "roll_d", "pitch": "pitch_d", "yaw": "yaw_d",
                                               "thrust": "thrust_neg_z"}),
    "send_rate": ("vehicle_rates_setpoint", {"p": "roll", "q": "pitch", "r": "yaw", "thrust": "thrust_neg_z"}),
}
PARAM_KINDS = ("param", "sag")
TOPICS = sorted({v[0] for v in KIND_MAP.values()})


def parse_payload(s):
    """'k=v;k=v' -> {k: float or str}. param payload is NAME=value (value may be non-numeric -> str)."""
    out = {}
    for part in s.split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        try:
            out[k.strip()] = float(v)
        except ValueError:
            out[k.strip()] = v
    return out


def match_first(intended_us, t, cols, targets, tol, window_us):
    """First sample with t >= intended_us (and t <= intended+window) where every |cols[k]-targets[k]| <= tol.
    t sorted ascending (np array). Returns (applied_us or None, n_matches_in_window). NaN never matches."""
    lo = int(np.searchsorted(t, intended_us, side="left"))
    hi = int(np.searchsorted(t, intended_us + window_us, side="right"))
    if hi <= lo or not targets:
        return None, 0
    ok = np.ones(hi - lo, bool)
    for k, v in targets.items():
        ok &= np.abs(np.asarray(cols[k][lo:hi], float) - v) <= tol  # NaN -> False
    idx = np.nonzero(ok)[0]
    return (int(t[lo + idx[0]]), int(idx.size)) if idx.size else (None, 0)


def match_param(intended_us, name, value, changes, initial, log_start_us, tol, window_us):
    """changes: [(t_us, name, value)] sorted by t. Returns (status, applied_us, n_matches).
    status: matched | pre_log (value already in initial params and the send precedes the log: unmeasurable) | unmatched."""
    hits = [c[0] for c in changes if c[1] == name and intended_us <= c[0] <= intended_us + window_us
            and abs(c[2] - value) <= tol * max(1.0, abs(value))]
    if hits:
        return "matched", hits[0], len(hits)
    if intended_us <= log_start_us and name in initial and abs(initial[name] - value) <= tol * max(1.0, abs(value)):
        return "pre_log", None, 0
    return "unmatched", None, 0


def compute_rows(sends, topics, changes, initial, log_start_us, tol=1e-3, window_us=2_000_000):
    """sends: [{kind, intended_us, payload}]; topics: {name: (t, cols)}; returns one result dict per send (same order).
    Adds 'changed' (payload differs from previous send of that kind), 'status', 'applied_us', 'delay_us', 'n_matches'."""
    res, prev = [], {}
    for s in sends:
        kind, ius, pl = s["kind"], s["intended_us"], s["payload"]
        r = dict(kind=kind, intended_us=ius, payload=pl, changed=prev.get(kind) != pl, status="unmatched",
                 applied_us=None, delay_us=None, n_matches=0)
        prev[kind] = pl
        p = parse_payload(pl)
        if kind in PARAM_KINDS:
            name = next(iter(p), None)
            v = p.get(name) if name else None
            if isinstance(v, float):
                r["status"], r["applied_us"], r["n_matches"] = match_param(ius, name, v, changes, initial,
                                                                           log_start_us, 1e-4, window_us)
        elif kind in KIND_MAP and KIND_MAP[kind][0] in topics:
            t, cols = topics[KIND_MAP[kind][0]]
            tg = {KIND_MAP[kind][1][k]: v for k, v in p.items() if k in KIND_MAP[kind][1] and isinstance(v, float)}
            if tg:
                a, n = match_first(ius, t, cols, tg, tol, window_us)
                if a is not None:
                    r["status"], r["applied_us"], r["n_matches"] = "matched", a, n
        if r["applied_us"] is not None:
            r["delay_us"] = r["applied_us"] - ius
        res.append(r)
    return res


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else None


def summarize(rows, topic_period_us, step_us=PHYSICS_STEP_US):
    """Per kind: counts + delay p50/p95/max (us and steps), for all matched rows and for the `changed` subset."""
    out = {}
    for kind in sorted({r["kind"] for r in rows}):
        rk = [r for r in rows if r["kind"] == kind]
        d = {"n": len(rk), "n_matched": sum(r["status"] == "matched" for r in rk),
             "n_pre_log": sum(r["status"] == "pre_log" for r in rk),
             "n_unmatched": sum(r["status"] == "unmatched" for r in rk),
             "n_multi_match": sum(r["n_matches"] > 1 for r in rk), "n_changed": sum(r["changed"] for r in rk),
             "topic_period_us": topic_period_us.get(kind), "step_us": step_us}
        for tag, sub in (("all", rk), ("changed", [r for r in rk if r["changed"]])):
            dl = [r["delay_us"] for r in sub if r["delay_us"] is not None]
            d[tag] = {"n": len(dl), **{k: (v, None if v is None else v / step_us) for k, v in
                                       (("p50_us", pct(dl, 50)), ("p95_us", pct(dl, 95)),
                                        ("max_us", float(max(dl)) if dl else None))}}
        per = d["topic_period_us"]
        d["caveat"] = ("constant payload / few changes: delay is bounded by log decimation, not command latency"
                       if d["n_changed"] < max(3, 0.05 * d["n"]) and kind in KIND_MAP else
                       "delay floor = logged topic period" if per and per > step_us else "")
        out[kind] = d
    return out


def load_topics(ulog):
    topics, period = {}, {}
    for name in TOPICS:
        ds = [d for d in ulog.data_list if d.name == name and d.multi_id == 0]
        if not ds:
            continue
        data = dict(ds[0].data)
        t = np.asarray(data["timestamp"], np.int64)
        if "thrust_body[2]" in data:
            data["thrust_neg_z"] = -np.asarray(data["thrust_body[2]"], float)
        if "q_d[0]" in data:  # unverified conversion, ZYX euler from q_d (w,x,y,z)
            w, x, y, z = (np.asarray(data[f"q_d[{i}]"], float) for i in range(4))
            data["roll_d"] = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
            data["pitch_d"] = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
            data["yaw_d"] = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        topics[name] = (t, data)
        period[name] = float(np.median(np.diff(t))) if t.size > 1 else None
    return topics, period


def analyse(run_dir, tol=1e-3, window_us=2_000_000, step_us=None):
    from pyulog import ULog  # lazy
    meta = {}
    if os.path.exists(os.path.join(run_dir, "run.json")):
        meta = json.load(open(os.path.join(run_dir, "run.json")))
    step_us = step_us or meta.get("physics_step_us") or PHYSICS_STEP_US
    sends = [dict(kind=r["kind"], intended_us=int(r["intended_sim_time_us"]), payload=r["payload"])
             for r in csv.DictReader(open(os.path.join(run_dir, "sends.csv")))]
    u = ULog(os.path.join(run_dir, "flight.ulg"))
    topics, period = load_topics(u)
    changes = sorted(u.changed_parameters, key=lambda c: c[0])
    rows = compute_rows(sends, topics, changes, u.initial_parameters, u.start_timestamp, tol, window_us)
    tp = {k: period.get(v[0]) for k, v in KIND_MAP.items()}
    tp.update({k: None for k in PARAM_KINDS})
    out = {"run_dir": run_dir, "tol": tol, "window_us": window_us, "step_us": step_us, "attitude_step_us": ATTITUDE_STEP_US,
           "log_start_us": int(u.start_timestamp), "n_changed_parameters_in_log": len(changes),
           "kinds": summarize(rows, tp, step_us)}
    json.dump(out, open(os.path.join(run_dir, "applied_timing.json"), "w"), indent=1)
    return out


def fmt(v):
    return "-" if v is None else f"{v:.0f}"


def report(out):
    print(f"== {out['run_dir']}  (step {out['step_us']} us, tol {out['tol']}, window {out['window_us'] / 1e6:g} s, "
          f"log start {out['log_start_us'] / 1e6:.3f} s)")
    for kind, d in out["kinds"].items():
        print(f" {kind}: n={d['n']} matched={d['n_matched']} unmatched={d['n_unmatched']} pre_log={d['n_pre_log']} "
              f"multi={d['n_multi_match']} changed={d['n_changed']} topic_period_us={fmt(d['topic_period_us'])}")
        for tag in ("all", "changed"):
            a = d[tag]
            print(f"   {tag:8s} n={a['n']:4d} p50 {fmt(a['p50_us'][0])} us ({fmt(a['p50_us'][1])} st)  "
                  f"p95 {fmt(a['p95_us'][0])} us ({fmt(a['p95_us'][1])} st)  max {fmt(a['max_us'][0])} us "
                  f"({fmt(a['max_us'][1])} st)")
        if d["caveat"]:
            print(f"   CAVEAT: {d['caveat']}")


def compare(outs):
    print("== cross-run (delay p50/p95/max us, all matched rows | unmatched)")
    for kind in sorted({k for o in outs for k in o["kinds"]}):
        for o in outs:
            d = o["kinds"].get(kind)
            if d:
                a = d["all"]
                print(f" {kind:9s} {os.path.basename(o['run_dir'].rstrip('/')):28s} {fmt(a['p50_us'][0]):>8s} "
                      f"{fmt(a['p95_us'][0]):>8s} {fmt(a['max_us'][0]):>8s} | {d['n_unmatched']}/{d['n']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("--window-s", type=float, default=2.0)
    ap.add_argument("--physics-step-us", type=int, default=None)
    a = ap.parse_args()
    outs = []
    for rd in a.run_dirs:
        outs.append(analyse(rd, a.tol, int(a.window_s * 1e6), a.physics_step_us))
        report(outs[-1])
    if len(outs) > 1:
        compare(outs)


if __name__ == "__main__":
    sys.exit(main())
