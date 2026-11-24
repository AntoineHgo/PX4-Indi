#!/usr/bin/env python3
"""Item-2 (sustained oscillation) of both G3 keys on a cropped time range, scorers unchanged (S223).

The scorers (g3_checks.py key 1, g3_checks_key2.py key 2) always run item 2 over the whole airborne span and have no window
option (--t0/--t1 only move item 3). This wrapper crops the log arrays to a range and calls their unchanged functions:
key 1 g3_checks.load + evaluate (item2_oscillation), key 2 g3_checks_key2.load_run + osc_rates.
Crop: time range [a, b) in seconds since the ulog start_timestamp (key-1 time base; key 2 uses start_timestamp + that).
A cropped range that does not start at the log start gets ground-level lead-in samples (copies of the first samples, placed
before the range) so the scorers' own airborne test (height above the first samples) still works; the lead-in is not airborne
and is never inside a detector window. Rates, nav-change skip, thresholds are the scorers'.
Usage: g3_item2_split.py RUN_DIR --cut T [--json OUT]   -> scores whole run (check), [0,T) and [T,end]
       g3_item2_split.py --self-test
Needs scipy (key 1): run inside docker (indi_project/docker/run.sh)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g3_checks as k1  # noqa: E402
import g3_checks_key2 as k2  # noqa: E402


def _lead(t_first, n, dt):
    return t_first - dt * n + dt * np.arange(n)


def key1_crop(tt, pos, q, w, tm, cmd, nav, a, b):
    """key-1 arrays cropped to [a,b) (time base: ulog start); lead-in of 800 ground samples if a > 0."""
    m = (tt >= a) & (tt < b)
    t, p, qq, ww = tt[m], pos[m], q[m], w[m]
    if a > 0:
        n = 800
        t = np.concatenate([_lead(t[0], n, 1e-3), t]); p = np.concatenate([np.repeat(pos[:1], n, 0), p])
        qq = np.concatenate([np.repeat(q[:1], n, 0), qq]); ww = np.concatenate([np.repeat(w[:1], n, 0), ww])
    mm = (tm >= a) & (tm < b)
    return t, p, qq, ww, tm[mm], cmd[mm]


def key1_item2(log, a, b):
    tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(log, 0.0, 1.0)
    t, p, qq, ww, tm2, cmd2 = key1_crop(tt, pos, q, w, tm, cmd, navc, a, b)
    r = k1.evaluate(t, p, qq, ww, tm2, cmd2, None, 0.0, 1.0, mode="attitude", t_land=None, nav_changes=navc)
    o = r["item2_oscillation"]
    if "reason" in o:
        return {"pass": False, "reason": o["reason"]}
    ta = r["airborne"][0]
    out = {"pass": bool(o["pass"]), "airborne": r["airborne"], "axes": {}}
    for ax in "pqr":
        d = o[ax]
        out["axes"][ax] = {"sustained": d["sustained"], "max_ratio": d["max_ratio"], "rms_at_max": d["rms_at_max_ratio"],
                           "max_rms_flagged": d["max_rms_ratio_flagged"],
                           "lines": [(hz, ta + off, n) for hz, off, n in d["lines"]]}  # (Hz, first window start [s], windows)
    out["position_sustained"] = o["position"]["sustained"]
    return out


def key2_item2(d, a, b):
    import shutil
    import tempfile
    rj = json.load(open(os.path.join(d, "run.json")))
    tmp = None
    if not any(e["name"] == "hold" for e in rj["events"]):
        # aborted run (LOC) has no hold event; load_run only uses it for the height sign, so give a temporary copy one
        # inside the flight (first event + 1 s, 3 s); the scored arrays are not affected
        tmp = tempfile.mkdtemp()
        os.symlink(os.path.abspath(os.path.join(d, "flight.ulg")), os.path.join(tmp, "flight.ulg"))
        rj["events"].append({"name": "hold", "t_us": rj["events"][-1]["t_us"] + 1_000_000, "dur_s": 3.0})
        json.dump(rj, open(os.path.join(tmp, "run.json"), "w"))
    try:
        kw, _ = k2.load_run(tmp or d)
    finally:
        if tmp:
            shutil.rmtree(tmp)
    from pyulog import ULog
    st = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["vehicle_status"]).start_timestamp * 1e-6
    A, B = st + a, st + b
    t = kw["t"]; m = (t >= A) & (t < B)
    tc, w, h = t[m], kw["w"][m], kw["h"][m]
    if a > 0:
        n = 800
        tc = np.concatenate([_lead(tc[0], n, 1.25e-3), tc]); w = np.concatenate([np.repeat(kw["w"][:1], n, 0), w])
        h = np.concatenate([kw["h"][:n], h])
    air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]
    if not ia.size:
        return {"pass": False, "reason": "never airborne"}
    a0, a1 = tc[ia[0]], tc[ia[-1]]
    mm = (tc >= a0) & (tc <= a1)
    try:
        res = k2.osc_rates(tc[mm], w[mm], [x for x in kw["nav_t"]])
    except ValueError:  # osc_rates takes max() over the windows: none fits
        return {"pass": None, "reason": "airborne span shorter than one 4 s window", "airborne": [a0 - st, a1 - st]}
    out = {"pass": not any(v["sustained"] for v in res.values()), "airborne": [a0 - st, a1 - st], "axes": {}}
    for ax, v in res.items():
        out["axes"][ax] = {"sustained": v["sustained"], "max_ratio": v["max_ratio"], "rms_at_max": None,
                           "max_rms_flagged": v["max_rms_dps"],
                           "lines": []}
        if v["at"]:  # v["at"] = (streak start relative to the grid start, Hz); grid starts at the airborne start a0
            out["axes"][ax]["lines"] = [(v["at"][1], a0 - st + v["at"][0], 3)]
    return out


def score(run_dir, cut):
    log = os.path.join(run_dir, "flight.ulg")
    end = 1e9
    return {"cut_s": cut, "whole": {"key1": key1_item2(log, 0.0, end), "key2": key2_item2(run_dir, 0.0, end)}, "pre": {"key1": key1_item2(log, 0.0, cut), "key2": key2_item2(run_dir, 0.0, cut)},
            "post": {"key1": key1_item2(log, cut, end), "key2": key2_item2(run_dir, cut, end)}}


def self_test():
    """2 Hz 15 deg/s sine on p only before the cut: flagged pre-cut, not post-cut, in both keys' item 2."""
    fs, T, cut = 800.0, 100.0, 60.0
    t = np.arange(0, T, 1 / fs); n = len(t)
    rng = np.random.default_rng(1)
    w = rng.normal(0, 0.003, (n, 3)); w[t < cut, 0] += np.radians(15.0) * np.sin(2 * np.pi * 2.0 * t[t < cut])
    pos = np.stack([np.zeros(n), np.zeros(n), -np.minimum(t, 5.0) * 2.0], 1)  # NED climb to 10 m
    q = np.tile([1.0, 0, 0, 0], (n, 1)); cmd = np.full((n, 4), 0.14)
    ok = True
    def chk(name, got, want):
        nonlocal ok; g = got == want; ok &= g; print(("PASS " if g else "FAIL ") + name, "got", got, "want", want)
    t1, p1, q1, w1, tm1, c1 = key1_crop(t, pos, q, w, t, cmd, [], 0.0, cut)
    t2, p2, q2, w2, tm2, c2 = key1_crop(t, pos, q, w, t, cmd, [], cut, 1e9)
    for nm, (tt, pp, qq, ww, tm, cc), want in (("pre", (t1, p1, q1, w1, tm1, c1), False), ("post", (t2, p2, q2, w2, tm2, c2), True)):
        r = k1.evaluate(tt, pp, qq, ww, tm, cc, None, 0.0, 1.0, mode="attitude")
        chk("key1 %s-cut item2 pass" % nm, r["item2_oscillation"]["pass"], want)
    h = -pos[:, 2]
    for nm, a, b, want in (("pre", 0.0, cut, False), ("post", cut, 1e9, True)):
        m = (t >= a) & (t < b); tc, ww, hh = t[m], w[m], h[m]
        if a > 0:
            tc = np.concatenate([_lead(tc[0], 800, 1e-3), tc]); ww = np.concatenate([np.repeat(w[:1], 800, 0), ww])
            hh = np.concatenate([h[:800], hh])
        air = hh > hh[:800].mean() + 0.3; ia = np.where(air)[0]
        r = k2.osc_rates(tc[ia[0]:ia[-1] + 1], ww[ia[0]:ia[-1] + 1])
        chk("key2 %s-cut item2 pass" % nm, not any(v["sustained"] for v in r.values()), want)
    # whole-run sanity: the unsplit signal is flagged by both
    chk("key1 whole item2 pass", k1.evaluate(t, pos, q, w, t, cmd, None, 0.0, 1.0, mode="attitude")["item2_oscillation"]["pass"], False)
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--self-test" in a:
        sys.exit(0 if self_test() else 1)
    out = None
    if "--json" in a:
        i = a.index("--json"); out = a[i + 1]; a = a[:i] + a[i + 2:]
    i = a.index("--cut"); cut = float(a[i + 1]); a = a[:i] + a[i + 2:]
    s = score(a[0], cut)
    txt = json.dumps(s, indent=1, default=float)
    if out:
        open(out, "w").write(txt + "\n")
    print(txt)
