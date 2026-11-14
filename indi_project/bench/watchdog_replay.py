#!/usr/bin/env python3
"""Offline replay of the O-12 watchdog trips over recorded flight.ulg files.

Applies the trips of plan/o12_watchdog_spec.md (tilt, altitude, non-finite) to
vehicle_attitude / vehicle_local_position inside the airborne window
(vehicle_land_detected.landed == false, trimmed at both ends) and writes a
markdown report. Read-only on results/, except for the report file.
"""
import argparse
import glob
import json
import math
import multiprocessing as mp
import os
import re

import numpy as np

# Thresholds: keep identical to the constants of the future run_scenario.py watchdog.
TILT_DEG = 60.0          # loss of control: max(|roll|,|pitch|) above this ...
TILT_HOLD_S = 0.5        # ... for at least this long
MIN_HEIGHT_M = 0.3       # height (-z) below this while airborne trips
ALT_BELOW_SP_M = 3.0     # more than this below the z setpoint ...
ALT_HOLD_S = 1.0         # ... for at least this long
CLIMB_FRAC = 0.9        # takeoff counts as complete at this fraction of the median airborne height
TRIM_S = 3.0             # airborne window trimmed at both ends (takeoff/landing)

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
FAIL_KEY = re.compile(r"^(error|errors|err|exception|traceback|status|ok|valid)$|fail|crash|abort|watchdog", re.I)


def longest_run(mask, t):
    """Return (start_time, duration) of the longest contiguous True run."""
    best = (0.0, 0.0)
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            dur = t[j] - t[i]
            if dur >= best[1]:
                best = (float(t[i]), float(dur))
            i = j + 1
        else:
            i += 1
    return best


def sustained_level(x, t, hold):
    """Largest value v such that x >= v over a contiguous span of >= hold seconds."""
    if len(x) < 2:
        return float("nan")
    # sort-free: for each start, extend while t - t0 < hold; use sliding min with a deque
    from collections import deque
    dq, best, i = deque(), -math.inf, 0
    for j in range(len(x)):
        while dq and x[dq[-1]] >= x[j]:
            dq.pop()
        dq.append(j)
        while t[j] - t[i] > hold:
            i += 1
            while dq and dq[0] < i:
                dq.popleft()
        if t[j] - t[i] >= hold * 0.98 and x[dq[0]] > best:
            best = x[dq[0]]
    return best if best > -math.inf else float("nan")


def analyse(path):
    from pyulog import ULog
    rel = os.path.relpath(path, RESULTS)
    try:
        u = ULog(path, ["vehicle_attitude", "vehicle_local_position",
                        "vehicle_local_position_setpoint", "vehicle_land_detected"])
        d = {x.name: x.data for x in u.data_list}
        att, pos, ld = d["vehicle_attitude"], d["vehicle_local_position"], d["vehicle_land_detected"]
    except Exception as e:  # noqa: BLE001
        return {"rel": rel, "error": repr(e)[:120]}
    sp = d.get("vehicle_local_position_setpoint")

    ld_t = ld["timestamp"] * 1e-6
    air = ld_t[ld["landed"] == 0]
    if len(air) == 0:
        return {"rel": rel, "error": "never airborne (landed always true)"}
    # window: first/last landed==false trimmed; the start additionally waits for takeoff to
    # complete (height reaches CLIMB_FRAC of the median airborne height)
    t0, t1 = air[0] + TRIM_S, air[-1] - TRIM_S
    tp_all = pos["timestamp"] * 1e-6
    ok_p = (tp_all >= air[0]) & (tp_all <= air[-1]) & np.isfinite(pos["z"])
    if ok_p.sum() > 10:
        hh = -pos["z"][ok_p].astype(float)
        cruise = float(np.median(hh))
        up = np.nonzero(hh >= CLIMB_FRAC * cruise)[0]
        if cruise > 1.0 and len(up):
            t0 = max(t0, float(tp_all[ok_p][up[0]]))
    # the online watchdog (run_scenario.py) is active from takeoff completion (5 s hover before offboard) to the land
    # command (4 s recover after the metrics window): use that window whenever run.json records it
    try:
        run = json.load(open(os.path.join(os.path.dirname(path), "run.json")))
        t0, t1 = run["t_offboard_us"] * 1e-6 - 5.0, run["t_window_end_us"] * 1e-6 + 4.0
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if t1 - t0 < 1.0:
        return {"rel": rel, "error": "airborne window too short (%.1fs)" % (t1 - t0)}

    res = {"rel": rel, "trips": [], "win": (float(t0), float(t1))}
    # attitude
    ta = att["timestamp"] * 1e-6
    q = np.stack([att["q[%d]" % i] for i in range(4)], 1).astype(float)
    m = (ta >= t0) & (ta <= t1)
    if not np.all(np.isfinite(q[m])):
        k = int(np.argmax(~np.all(np.isfinite(q), 1) & m))
        res["trips"].append(("non-finite attitude", float(ta[k]), float("nan")))
    qm = q[m]
    ok = np.all(np.isfinite(qm), 1)
    qm, tm = qm[ok], ta[m][ok]
    if len(tm) > 2:
        q0, q1, q2, q3 = qm.T
        roll = np.degrees(np.arctan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 ** 2 + q2 ** 2)))
        pitch = np.degrees(np.arcsin(np.clip(2 * (q0 * q2 - q3 * q1), -1, 1)))
        tilt = np.maximum(np.abs(roll), np.abs(pitch))
        res["max_tilt"] = float(tilt.max())
        res["tilt_sust"] = float(sustained_level(tilt, tm, TILT_HOLD_S))
        s, dur = longest_run(tilt > TILT_DEG, tm)
        if dur >= TILT_HOLD_S:
            res["trips"].append(("tilt > %.0f deg for >= %.1f s" % (TILT_DEG, TILT_HOLD_S),
                                 s + TILT_HOLD_S, float(tilt[(tm >= s) & (tm <= s + TILT_HOLD_S)].max())))
    # position
    tp = pos["timestamp"] * 1e-6
    mp_ = (tp >= t0) & (tp <= t1) & np.isfinite(pos["z"])
    tpm, h = tp[mp_], -pos["z"][mp_].astype(float)
    if len(tpm):
        res["min_h"] = float(h.min())
        lo = h < MIN_HEIGHT_M
        if lo.any():
            k = int(np.argmax(lo))
            res["trips"].append(("height < %.1f m" % MIN_HEIGHT_M, float(tpm[k]), float(h[k])))
        if sp is not None and len(sp["timestamp"]):
            ts, zs = sp["timestamp"] * 1e-6, sp["z"].astype(float)
            g = np.isfinite(zs)
            if g.sum() > 1:
                idx = np.clip(np.searchsorted(ts[g], tpm, side="right") - 1, 0, g.sum() - 1)
                zsp = zs[g][idx]
                # only where a setpoint sample is recent (<1 s old)
                fresh = (tpm - ts[g][idx]) < 1.0
                deficit = np.where(fresh, (-zsp) - h, -np.inf)  # >0 means below setpoint (height deficit)
                if np.isfinite(deficit).any():
                    res["max_below_sp"] = float(deficit[np.isfinite(deficit)].max())
                    fin = np.where(np.isfinite(deficit), deficit, -1e9)
                    res["below_sp_sust"] = float(sustained_level(fin, tpm, ALT_HOLD_S))
                    s, dur = longest_run(deficit > ALT_BELOW_SP_M, tpm)
                    if dur >= ALT_HOLD_S:
                        k = int(np.argmax(tpm >= s + ALT_HOLD_S))
                        res["trips"].append(("> %.1f m below z setpoint for >= %.1f s" % (ALT_BELOW_SP_M, ALT_HOLD_S),
                                             float(s + ALT_HOLD_S), float(deficit[k])))
    return res


def marks(rundir):
    """Failure-like keys found in run.json / metrics.json of a run directory."""
    out = []

    def walk(o, p, f):
        if isinstance(o, dict):
            for k, v in o.items():
                if FAIL_KEY.search(str(k)):
                    out.append("%s:%s=%s" % (f, p + str(k), json.dumps(v)[:80]))
                walk(v, p + str(k) + ".", f)
        elif isinstance(o, list):
            for i, v in enumerate(o[:50]):
                walk(v, p + "%d." % i, f)
    seen = False
    for f in ("run.json", "metrics.json"):
        fp = os.path.join(rundir, f)
        if os.path.exists(fp):
            seen = True
            try:
                walk(json.load(open(fp)), "", f)
            except Exception as e:  # noqa: BLE001
                out.append("%s:unreadable(%s)" % (f, type(e).__name__))
    return out, seen


def pct(v):
    v = np.array([x for x in v if x is not None and np.isfinite(x)])
    if not len(v):
        return "n/a"
    return "%.2f / %.2f / %.2f" % (np.percentile(v, 50), np.percentile(v, 99), v.max())


def pct_lo(v):
    v = np.array([x for x in v if x is not None and np.isfinite(x)])
    if not len(v):
        return "n/a"
    return "%.2f / %.2f / %.2f" % (np.percentile(v, 50), np.percentile(v, 1), v.min())


def init():
    os.nice(19)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=RESULTS)
    ap.add_argument("--out", default=os.path.join(RESULTS, "o12_watchdog_replay.md"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.results, "**", "flight.ulg"), recursive=True))
    with mp.Pool(min(a.workers, 4), initializer=init) as p:
        rs = p.map(analyse, files, chunksize=4)
    bad = [r for r in rs if "error" in r]
    good = [r for r in rs if "error" not in r]
    L = ["# O-12 watchdog replay over recorded flights", "",
         "Script: `bench/watchdog_replay.py`. Thresholds: tilt > %.0f deg for >= %.1f s; height < %.1f m; "
         "> %.1f m below z setpoint for >= %.1f s; non-finite attitude. Window: as the online watchdog, takeoff "
         "completion (t_offboard - 5 s) to the land command (t_window_end + 4 s) from run.json; without those keys, "
         "landed==false trimmed by %.0f s at both ends." % (TILT_DEG, TILT_HOLD_S, MIN_HEIGHT_M, ALT_BELOW_SP_M, ALT_HOLD_S, TRIM_S), "",
         "- flight.ulg scanned: %d" % len(files),
         "- parse failures / unusable (skipped): %d" % len(bad),
         "- analysed: %d" % len(good), ""]
    if bad:
        kinds = {}
        for r in bad:
            kinds[r["error"][:60]] = kinds.get(r["error"][:60], 0) + 1
        L.append("Skipped reasons: " + "; ".join("%s x%d" % kv for kv in sorted(kinds.items())))
        L.append("")
    trips = [(r, t) for r in good for t in r["trips"]]
    tripped = sorted({r["rel"] for r, _ in trips})
    L += ["## Trips (%d trips in %d runs)" % (len(trips), len(tripped)), ""]
    if trips:
        L += ["| run | reason | t (s, log) | value | failure marks in run.json/metrics.json |", "|---|---|---|---|---|"]
        for r, (why, t, v) in trips:
            mk, seen = marks(os.path.dirname(os.path.join(a.results, r["rel"])))
            mk_s = "; ".join(mk) if mk else ("none found" if seen else "no run.json/metrics.json")
            L.append("| %s | %s | %.1f | %.2f | %s |" % (os.path.dirname(r["rel"]), why, t, v, mk_s))
    else:
        L.append("No trips.")
    L += ["", "## Margins over all analysed runs", "",
          "Percentiles over runs (p50 / p99 / max; for min-type values p50 / p1 / min), inside the airborne window.", "",
          "| quantity | threshold | p50 / p99 / max |", "|---|---|---|",
          "| max tilt, any instant (deg) | - | %s |" % pct([r.get("max_tilt") for r in good]),
          "| tilt level held >= 0.5 s (deg) | > %.0f trips | %s |" % (TILT_DEG, pct([r.get("tilt_sust") for r in good])),
          "| min height -z (m) | < %.1f trips | %s |" % (MIN_HEIGHT_M, pct_lo([r.get("min_h") for r in good])),
          "| max depth below z setpoint, instant (m) | - | %s |" % pct([r.get("max_below_sp") for r in good]),
          "| depth below z setpoint held >= 1.0 s (m) | > %.1f trips | %s |" % (ALT_BELOW_SP_M, pct([r.get("below_sp_sust") for r in good])),
          "", "Runs without a usable z setpoint are excluded from the setpoint rows; "
          "runs counted there: %d of %d." % (sum(1 for r in good if "max_below_sp" in r), len(good)), ""]
    # top runs by tilt for judging margin
    top = sorted(good, key=lambda r: -r.get("tilt_sust", -1))[:8]
    L += ["### Highest sustained tilt (held 0.5 s)", "", "| run | tilt held 0.5 s (deg) | max tilt (deg) | min height (m) |", "|---|---|---|---|"]
    for r in top:
        L.append("| %s | %.1f | %.1f | %.2f |" % (os.path.dirname(r["rel"]), r.get("tilt_sust", float("nan")),
                                                  r.get("max_tilt", float("nan")), r.get("min_h", float("nan"))))
    low = sorted([r for r in good if "min_h" in r], key=lambda r: r["min_h"])[:8]
    L += ["", "### Lowest height", "", "| run | min height (m) |", "|---|---|"]
    for r in low:
        L.append("| %s | %.2f |" % (os.path.dirname(r["rel"]), r["min_h"]))
    open(a.out, "w").write("\n".join(L) + "\n")
    print("scanned %d, failures %d, trips %d in %d runs" % (len(files), len(bad), len(trips), len(tripped)))


if __name__ == "__main__":
    main()
