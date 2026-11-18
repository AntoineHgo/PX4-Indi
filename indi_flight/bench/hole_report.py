#!/usr/bin/env python3
"""Per-run hole reporter (GATES.md G1 evidence limit 1): sim holes vs controller holes vs logger dropouts.

  python3 hole_report.py <run_dir | flight.ulg> [--out report.json]      exit 0 = PASS, 1 = FAIL, 2 = no usable data

Classes (a gap = interval between consecutive samples > 1.5 x the topic's own median period, after the first second):
  logger      gap overlapping a ULog dropout interval [t - duration, t] (+- 1 period). Counted from the dropout records;
              such gaps are not counted again as sim or controller.
  sim         gap in a simulator topic (sim_ground_truth, *_groundtruth, sensor_gyro) = physics steps not delivered.
  controller  gap in a controller-rate topic (vehicle_angular_velocity, vehicle_torque_setpoint, actuator_motors) or in an
              outer-loop topic (vehicle_local_position_setpoint) that no sim hole overlaps.
Nominal rate = the topic's median period (no hardcoded 800 Hz). Missing samples per gap = round(dt / median) - 1; fraction =
missing / (missing + logged samples) over the analysed span. Max single hole = largest gap dt in ms.
Limits (G1.1): missing fraction sim <= 0.05 %, controller and logger <= 0.1 %; single hole <= 10 ms.
Logger fraction = sum(dropout durations) / analysed span. The sim fraction uses the primary sim topic (first present of
sim_ground_truth, sensor_gyro); the class verdict is the worst over its topics.
Duplicate stamps (dt == 0 within 8 samples of a one-sample gap) are publisher jitter and cancel that gap. *_groundtruth
topics logged below the step rate are reported as class sim-info and excluded from the verdict when sim_ground_truth exists.
"""
import argparse
import json
import os
import sys

import numpy as np

SIM_TOPICS = ["sim_ground_truth", "vehicle_attitude_groundtruth", "vehicle_angular_velocity_groundtruth",
              "vehicle_local_position_groundtruth", "sensor_gyro"]
CTRL_TOPICS = ["vehicle_angular_velocity", "vehicle_torque_setpoint", "actuator_motors",
               "vehicle_local_position_setpoint"]
LIM_FRAC = {"sim": 5e-4, "controller": 1e-3, "logger": 1e-3}
LIM_HOLE_MS = 10.0
GAP_FACTOR = 1.5
SKIP_US = 1_000_000
DUP_WINDOW = 8   # samples: a duplicate stamp cancels a one-sample gap this close (logger/publisher jitter)


def find_gaps(ts, t_min):
    """-> (gaps [(t_start, dt)], median_period_us, n_samples) on samples >= t_min."""
    ts = np.sort(np.asarray(ts, dtype=np.int64))
    ts = ts[ts >= t_min]
    if ts.size < 3:
        return [], float("nan"), int(ts.size)
    dt = np.diff(ts)
    med = float(np.median(dt))
    gi = np.flatnonzero(dt > GAP_FACTOR * med)
    zi = set(np.flatnonzero(dt == 0).tolist())
    keep = []
    for i in gi.tolist():   # a gap next to a duplicate stamp (dt == 0) is publish-time jitter: no sample is missing
        j = next((k for k in sorted(zi, key=lambda k: abs(k - i)) if abs(k - i) <= DUP_WINDOW), None)
        if j is not None and dt[i] <= 2.0 * med + 1:
            zi.discard(j)
        else:
            keep.append(i)
    return [(int(ts[i]), int(dt[i])) for i in keep], med, int(ts.size)


def count_missing(ts, t_min):
    """Count-based missing samples: round(span / median) + 1 - n (all samples >= t_min, duplicate stamps counted as samples,
    because a publisher-jitter duplicate replaces a stamp without losing a sample). Independent of the gap/dup-cancel logic."""
    ts = np.sort(np.asarray(ts, dtype=np.int64))
    ts = ts[ts >= t_min]
    if ts.size < 3:
        return 0
    med = float(np.median(np.diff(ts)))
    return int(round((ts[-1] - ts[0]) / med) + 1 - ts.size)


def _overlaps(t, dt, intervals, pad):
    return any(t - pad <= hi and t + dt + pad >= lo for lo, hi in intervals)


def _stats(gaps, med, n, span_us, cls, hold_gaps=None):
    """hold_gaps: gaps whose max dt is held to the 10 ms limit (default = gaps). Controller passes every non-logger gap here
    so a controller hole attributed to a sim hole still has to meet the limit."""
    missing = sum(max(round(dt / med) - 1, 0) for _, dt in gaps)
    frac = missing / (missing + n) if n else float("nan")
    mx = max((dt for _, dt in (gaps if hold_gaps is None else hold_gaps)), default=0.0) / 1000.0
    ok = cls == "sim-info" or (frac <= LIM_FRAC[cls] and mx <= LIM_HOLE_MS)
    return {"class": cls, "count": len(gaps), "missing": missing, "samples": n, "median_ms": med / 1000.0,
            "rate_hz": 1e6 / med, "missing_frac": frac, "max_hole_ms": mx, "pass": bool(ok)}


def analyse(topics, t_start, t_end, dropouts=()):
    """topics {name: timestamps_us}; dropouts [(t_us, duration_ms)]. Returns the report dict (no I/O)."""
    t_min = t_start + SKIP_US
    span = max(t_end - t_min, 1)
    drop_iv = [(t - d * 1000.0, float(t)) for t, d in dropouts if t >= t_min]
    rows, classes = [], {"sim": [], "controller": [], "logger": []}
    sim_iv, sim_primary = [], None
    for name in SIM_TOPICS:
        # *_groundtruth topics are logged below the step rate in some runs (rate-limited logging, not sim holes):
        # with sim_ground_truth present they are shown as class "sim-info" and excluded from the verdict.
        info = name.endswith("_groundtruth") and "sim_ground_truth" in topics
        if name in topics:
            gaps, med, n = find_gaps(topics[name], t_min)
            if not np.isfinite(med):
                continue
            pad = med
            s = [g for g in gaps if not _overlaps(g[0], g[1], drop_iv, pad)]
            r = _stats(s, med, n, span, "sim")
            if info:
                r["class"] = "sim-info"
            else:
                sim_iv += [(t, t + dt) for t, dt in s]
            r["topic"] = name
            rows.append(r)
            if sim_primary is None and name in ("sim_ground_truth", "sensor_gyro"):
                sim_primary = med
    for name in CTRL_TOPICS:
        if name in topics:
            gaps, med, n = find_gaps(topics[name], t_min)
            if not np.isfinite(med):
                continue
            pad = max(med, 1250.0)
            nl = [g for g in gaps if not _overlaps(g[0], g[1], drop_iv, pad)]   # not logger-explained
            c = [g for g in nl if not _overlaps(g[0], g[1], sim_iv, pad)]
            r = _stats(c, med, n, span, "controller", hold_gaps=nl)   # 10 ms limit holds even if a sim hole explains the gap
            # count cross-check: gap-based missing (all non-logger gaps) vs round(span/median)+1-n; > 1 apart = not PASS
            gm = sum(max(round(dt / med) - 1, 0) for _, dt in nl)
            lg = [g for g in gaps if g not in nl]   # logger-explained gaps are not in gm, so remove them from the count basis
            cm = count_missing(topics[name], t_min) - sum(max(round(dt / med) - 1, 0) for _, dt in lg)
            r["missing_count_based"] = cm
            r["count_disagree"] = abs(cm - gm) > 1
            if r["count_disagree"]:
                r["pass"] = False
            r["topic"] = name
            rows.append(r)
    out = {"span_s": span / 1e6, "topics": rows, "classes": {}}
    for cls in ("sim", "controller"):
        rs = [r for r in rows if r["class"] == cls]
        if cls == "sim" and sim_primary is not None:   # one count basis for sim: the primary topic's row
            prim = [r for r in rs if r["topic"] in ("sim_ground_truth", "sensor_gyro")][:1]
            rs_frac = prim
        else:
            rs_frac = rs
        out["classes"][cls] = {
            "count": max((r["count"] for r in rs), default=0),   # a hole seen in several topics counts once
            "missing_frac": max((r["missing_frac"] for r in rs_frac), default=float("nan")),
            "max_hole_ms": max((r["max_hole_ms"] for r in rs), default=0.0),
            "pass": all(r["pass"] for r in rs) if rs else None,
            "limit_frac": LIM_FRAC[cls], "present": bool(rs)}
    if sim_primary is None:   # decimated *_groundtruth topics cannot detect sim holes: refuse to pass silently
        out["classes"]["sim"].update({"pass": False, "present": True, "assessable": False,
                                      "verdict": "sim: not assessable (no sim_ground_truth or sensor_gyro in the log)"})
    dur = sum(d for t, d in dropouts if t >= t_min)
    mxd = max((d for t, d in dropouts if t >= t_min), default=0.0)
    lf = dur * 1000.0 / span
    out["classes"]["logger"] = {
        "count": sum(1 for t, _ in dropouts if t >= t_min), "missing_frac": lf, "max_hole_ms": mxd,
        "pass": bool(lf <= LIM_FRAC["logger"] and mxd <= LIM_HOLE_MS), "limit_frac": LIM_FRAC["logger"], "present": True}
    out["pass"] = all(c["pass"] for c in out["classes"].values() if c["pass"] is not None)
    out["limits"] = {"frac": LIM_FRAC, "single_hole_ms": LIM_HOLE_MS}
    return out


def load_ulog(path):
    from pyulog import ULog
    u = ULog(path)
    topics = {}
    for d in u.data_list:
        if d.multi_id == 0 and d.name in SIM_TOPICS + CTRL_TOPICS:
            topics[d.name] = np.asarray(d.data["timestamp"], dtype=np.int64)
    t_end = max((int(v[-1]) for v in topics.values() if len(v)), default=int(u.last_timestamp))
    drops = [(int(d.timestamp), float(d.duration)) for d in getattr(u, "dropouts", [])]
    return topics, int(u.start_timestamp), t_end, drops


def fmt(rep, label):
    L = [f"hole report: {label}  (span {rep['span_s']:.1f} s after the first second)"]
    L.append(f"{"topic":38s}{'class':11s}{'rate Hz':>8s}{'holes':>6s}{'miss':>6s}{'miss %':>9s}{'max ms':>8s}  verdict")
    for r in rep["topics"]:
        L.append(f"{r['topic']:38s}{r['class']:11s}{r['rate_hz']:8.1f}{r['count']:6d}{r['missing']:6d}"
                 f"{100 * r['missing_frac']:9.4f}{r['max_hole_ms']:8.2f}  {'info' if r['class'] == 'sim-info' else ('PASS' if r['pass'] else 'FAIL')}"
                 + (f" (count-disagree: count-based missing {r['missing_count_based']})" if r.get("count_disagree") else ""))
    for k, c in rep["classes"].items():
        v = "n/a (topics absent)" if c["pass"] is None else ("PASS" if c["pass"] else "FAIL")
        if c.get("assessable") is False:
            v = "FAIL " + c["verdict"]
        L.append(f"CLASS {k:10s} holes {c['count']:4d}  missing {100 * c['missing_frac']:.4f} % (limit "
                 f"{100 * c['limit_frac']:.2f} %)  max {c['max_hole_ms']:.2f} ms (limit 10)  {v}")
    L.append("OVERALL " + ("PASS" if rep["pass"] else "FAIL"))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="run directory (with flight.ulg) or a .ulg file")
    ap.add_argument("--out", help="JSON report path")
    a = ap.parse_args()
    p = os.path.join(a.path, "flight.ulg") if os.path.isdir(a.path) else a.path
    topics, t0, t1, drops = load_ulog(p)
    if not topics:
        print("no known topics in", p)
        return 2
    rep = analyse(topics, t0, t1, drops)
    rep["source"] = p
    if os.path.isdir(a.path) and os.path.exists(os.path.join(a.path, "run.json")):
        try:
            rj = json.load(open(os.path.join(a.path, "run.json")))
            rep["run_json_keys"] = sorted(rj)[:20]
        except Exception:
            pass
    print(fmt(rep, p))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
