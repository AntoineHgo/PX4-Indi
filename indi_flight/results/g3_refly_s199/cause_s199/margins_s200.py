#!/usr/bin/env python3
"""S200: rate-loop margins on the drawn plants of G3 failed runs 245/239/283 and a controller tau_m sweep over the G3 box corners.

    python3 margins_s200.py [--selftest] [OUT_JSON]

Reuses bench/g2_rate_model_s165.cfg (freeze params: K 20, ACT_TC 0.033, LEAD 1, ACT_BLD 1 s, MC_ROLL/PITCH_P 8, measured path, 800 Hz,
plant tau 33 ms) and its summ() margin reading, with the g3_osc_margins glue for the plant (g = 1/e, lat_s = loop delay act+imu,
n = 1 + telemetry frames).  Loops: 'rate' = rate loop alone (att_p 0, M3a break), 'rate+att' = M3a break with the attitude path closed
(what the G2 rate cells measure), 'att' = attitude loop (break at rate setpoint, L_att_indi).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "..", "..", "..", "bench")
sys.path.insert(0, BENCH)
import g2_rate_model_s165 as G  # noqa: E402
import margins_est as ME  # noqa: E402
import margins_models as MM  # noqa: E402

FS = 800.0
TAU0 = 0.033
K = 20.0
CAMP = os.path.join(HERE, "..", "..", "g3_campaign_f10")
F = np.geomspace(0.05, 0.45 * FS, 600)
W = 2 * np.pi * F


def cfg(axis, e=1.0, tau_r=TAU0, delay_ms=0.0, frames=0, tau_m=TAU0, att_p=None, lead=None):
    p = G.cfg(axis, "")                      # flown freeze config, measured path, Tb = ACT_BLD = 1 s
    p.update(g=1.0 / e, tau_r=tau_r, lat_s=delay_ms * 1e-3, n=1 + int(frames), tau_m=tau_m, fb_lead=min(K * tau_m, 2.0) if lead is None else lead)
    if att_p is not None:
        p["att_p"] = att_p
    return p


def read(m):
    c = [x for x in m["crossings"] if x["slope_down"]] or m["crossings"]
    cr = min(c, key=lambda x: x["pm_deg"]) if c else None
    pc = m["phase_crossings"]
    return dict(pm=cr["pm_deg"] if cr else float("nan"), fc=cr["f_c"] if cr else float("nan"),
                dm=cr["dm_s"] if cr else float("nan"), gm=min(x["gm_db"] for x in pc) if pc else float("inf"),
                f180=[round(x["f"], 2) for x in pc], Ms=m["Ms"])


def loops(p, which=("rate", "rate+att", "att")):
    out = {}
    for name in which:
        if name == "att":
            L = MM.L_att_indi(W, FS, **dict(MM.HEAD_FLIGHT, **p))
        else:
            L = MM.L_indi(W, FS, **dict(p, att_p=0.0 if name == "rate" else p["att_p"]))
        out[name] = read(ME.margins(W, L, n_dense=3000))
    return out


def Lat(p, name, f):
    w = 2 * np.pi * np.atleast_1d(f)
    if name == "att":
        return MM.L_att_indi(w, FS, **dict(MM.HEAD_FLIGHT, **p))
    return MM.L_indi(w, FS, **dict(p, att_p=0.0 if name == "rate" else p["att_p"]))


def draw(run):
    return json.load(open(os.path.join(CAMP, "run_%d" % run, "g3_draw.json")))["draw"]["factors"]


def selftest():
    # 1. known-margin L = wc/s e^{-s Td}
    w = np.geomspace(1.0, 2000.0, 3000)
    m = ME.margins(w, 100.0 / (1j * w) * np.exp(-1j * w * 0.005))
    assert abs(m["pm_deg"] - (90 - math.degrees(0.5))) < 0.2
    res = []
    # 2. nominal flown config vs S160 measured mean roll800 (g2_freeze_s160/xcheck_rate.md): 18.9 dB / 56.4 deg / 3.27 Hz; tol PM 10 deg, GM 3 dB
    r = read(ME.margins(W, MM.L_indi(W, FS, **G.cfg("roll", "")), n_dense=3000))
    ok1 = abs(r["pm"] - 56.4) <= 10 and abs(r["gm"] - 18.9) <= 3
    res.append(("nominal flown roll800 vs S160 measured 56.4 deg / 18.9 dB", r, ok1))
    # 3. my cfg() at nominal equals the S165 cfg
    r2 = read(ME.margins(W, MM.L_indi(W, FS, **cfg("roll")), n_dense=3000))
    ok2 = abs(r2["pm"] - r["pm"]) < 0.1 and abs(r2["gm"] - r["gm"]) < 0.1
    res.append(("cfg() nominal == g2_rate_model_s165.cfg", r2, ok2))
    # 4. G2_SCORES.md (freeze-10) spot cell roll800_fwdef_s2: GM 15.7 / PM 46.9 / DM 75.5 ms; the model is the S165 'fwdef' variant (K x0.5, tc 0.05, model path)
    r3 = read(ME.margins(W, MM.L_indi(W, FS, **G.cfg("roll", "fwdef")), n_dense=3000))
    ok3 = abs(r3["pm"] - 46.9) <= 20 and abs(r3["gm"] - 15.7) <= 3
    res.append(("roll800_fwdef vs G2_SCORES 46.9 deg / 15.7 dB / 75.5 ms (tol PM 20, GM 3)", r3, ok3))
    # 5. direction checks
    assert read(ME.margins(W, MM.L_indi(W, FS, **cfg("roll", e=2.0, att_p=0.0)), n_dense=3000))["pm"] < read(
        ME.margins(W, MM.L_indi(W, FS, **cfg("roll", att_p=0.0)), n_dense=3000))["pm"]
    return res


def fmt(r):
    gm = "n/a" if not np.isfinite(r["gm"]) else "%.1f" % r["gm"]
    return "%.0f / %s / %.1f ms @%.2f Hz" % (r["pm"], gm, r["dm"] * 1e3, r["fc"])


def runs():
    spec = {245: "pitch", 239: "roll", 283: "pitch"}
    obs = {245: [2.0], 239: [2.0, 2.5], 283: [10.75]}
    out = {}
    for run, ax in spec.items():
        f = draw(run)
        e = f["g1_err"][ax]
        up, dn = TAU0 * f["tau_up"]["value"], TAU0 * f["tau_down"]["value"]
        dl, fr = f["loop_delay"]["total_ms"], f["tel_latency"]["frames"]
        row = dict(axis=ax, e=e, tau_up=up, tau_down=dn, delay=dl, frames=fr, obs=obs[run], v={})
        for tag, tau in (("slow", max(up, dn)), ("mean", 0.5 * (up + dn))):
            p = cfg(ax, e, tau, dl, fr)
            L = loops(p)
            row["v"][tag] = dict(L=L, at={n: [(fo, abs(Lat(p, n, fo)[0]), math.degrees(np.angle(Lat(p, n, fo)[0]))) for fo in obs[run]]
                                           for n in ("rate", "rate+att", "att")})
        row["nominal"] = loops(cfg(ax))
        out[run] = row
    return out


def sweep(lead=None, which=("rate", "rate+att", "att"), es=(0.5, 2.0)):
    """worst PM / GM over the 16 box corners per tau_m (and the worst over the e = 0.5 and e = 2 halves); lead None = firmware c = min(K tau_m, 2)."""
    taums = (0.017, 0.025, 0.033, 0.05, 0.07, 0.1)
    out = {}
    for tm in taums:
        worst = {n: dict(pm=1e9, gm=1e9, pmc=None, gmc=None, pm_e={x: 1e9 for x in es}, nneg=0) for n in which}
        for sc in (0.5, 3.0):
            for dl in (0.0, 10.0):
                for e in es:
                    for fr in (0, 3):
                        L = loops(cfg("pitch", e, TAU0 * sc, dl, fr, tau_m=tm, lead=lead), which)
                        for n, r in L.items():
                            c = (sc, dl, e, fr)
                            w = worst[n]
                            w["pm_e"][e] = min(w["pm_e"][e], r["pm"])
                            w["nneg"] += int(r["pm"] <= 0 or r["gm"] < 0)
                            if r["pm"] < w["pm"]:
                                w.update(pm=r["pm"], pmc=c)
                            if r["gm"] < w["gm"]:
                                w.update(gm=r["gm"], gmc=c)
        out[tm] = worst
    return out


if __name__ == "__main__":
    st = selftest()
    for name, r, ok in st:
        print("SELFTEST", "ok  " if ok else "FAIL", name, "->", fmt(r))
    R = runs()
    S = sweep()
    S2 = sweep(lead=0.66)
    S3 = sweep(es=(0.8, 1.2))
    json.dump(dict(selftest=[(n, r, bool(o)) for n, r, o in st], runs=R, sweep={str(k): v for k, v in S.items()}, sweep_e08_12={str(k): v for k, v in S3.items()}, sweep_lead066={str(k): v for k, v in S2.items()}),
              open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "margins_s200.json"), "w"), indent=1, default=str)
    for run, row in R.items():
        print(run, row["axis"], "e=%.2f tau up/down %.0f/%.0f ms delay %.1f frames %d" % (row["e"], row["tau_up"] * 1e3, row["tau_down"] * 1e3, row["delay"], row["frames"]))
        print("  nominal", {k: fmt(v) for k, v in row["nominal"].items()})
        for tag, v in row["v"].items():
            print(" ", tag, {k: fmt(x) for k, x in v["L"].items()})
            print("   at obs", {k: [(f, round(a, 2), round(p)) for f, a, p in x] for k, x in v["at"].items()})
    for tm, w in S.items():
        print(tm, {n: (round(x["pm"], 1), round(x["gm"], 1), x["pmc"], x["pm_e"], x["nneg"]) for n, x in w.items()})
    print("e 0.8/1.2")
    for tm, w in S3.items():
        print(tm, {n: (round(x["pm"], 1), round(x["gm"], 1), x["pmc"], x["gmc"], x["nneg"]) for n, x in w.items()})
    print("lead fixed 0.66")
    for tm, w in S2.items():
        print(tm, {n: (round(x["pm"], 1), round(x["gm"], 1), x["pmc"], x["pm_e"], x["nneg"]) for n, x in w.items()})
