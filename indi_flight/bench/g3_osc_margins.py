#!/usr/bin/env python3
"""G3 pre-test (S173) linear-margin check of the INDI rate and attitude loops at the drawn plants (S186).

    python3 bench/g3_osc_margins.py [out_dir]       self-test first, then README tables to stdout / out_dir/tables.md

Uses margins_models.L_indi (rate loop, break at torque setpoint) and margins_models.L_att_indi (attitude loop, break at rate
setpoint, closes MC_ROLL_P / MC_PITCH_P around the closed INDI rate loop).  Only the glue below is new (S186):
  plant gain g = 1/e (e = controller G1 / plant G1), rotor tau_r = 33 ms x tau_scale x (1 | asym), lat_s = loop_delay total_ms
  (act + imu delay lumped into command latency), n = 1 + tel_latency frames (1.25 ms physics frames, measured-path delay),
  firmware flight config: K 20, ACT_TC 0.033 -> lead c = min(K ACT_TC, 2) = 0.66, att_p 8, measured path, setpoint lead on.
Not modelled: eta x motor state on the measured path (eta = 1), yaw, weak motor, thrust sag, eRPM dropout, vibration, outer loops,
the 33 ms nominal is an assumption (ref_airframe_model.md), asymmetric tau enters as one linear tau (down or mean of up/down).
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_est as ME  # noqa: E402
import margins_models as MM  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "g3_pretest_s173")
TAU0 = 0.033
K_RATE, ACT_TC, ATT_P = 20.0, 0.033, 8.0
OSC = {3: "pitch", 7: "pitch", 13: "roll", 17: "pitch"}  # observed sustained limit cycle (LOC_CAUSE_S186, user brief)


def cfg(e, tau_r, delay_ms, tel_frames=0, K=K_RATE, act_tc=ACT_TC, att_p=ATT_P):
    return dict(MM.HEAD_FLIGHT, K=K, tau_m=act_tc, fb_lead=min(K * act_tc, 2.0), att_p=att_p, g=1.0 / e, tau_r=tau_r,
                lat_s=delay_ms * 1e-3, n=1 + int(tel_frames))


def margins(c, fs=800.0):
    """-> dict rate/att: pm, gm, fc (Hz, of the worst PM crossing), pm_all list"""
    out = {}
    for name, fun in (("rate", MM.L_indi), ("att", MM.L_att_indi)):
        kw = dict(c)
        if name == "rate":
            kw["att_p"] = 0.0
        f = np.geomspace(0.05, 0.45 * fs, 500)
        w = 2 * np.pi * f
        m = ME.margins(w, fun(w, fs, **kw), n_dense=3000)  # coarser than margins_of (speed); self-test compares
        cr = min(m["crossings"], key=lambda x: x["pm_deg"]) if m["crossings"] else None
        out[name] = dict(pm=m["pm_deg"], gm=m["gm_db"], fc=cr["f_c"] if cr else float("nan"),
                         fcs=[round(x["f_c"], 2) for x in m["crossings"]], Ms=m["Ms"])
    return out


def taus(scale, asym):
    return TAU0 * scale * asym, TAU0 * scale * (1 + asym) / 2  # slow (down), mean


def run_cfgs():
    rows = []
    for i in range(20):
        d = json.load(open(os.path.join(RES, "run_%03d" % i, "g3_draw.json")))["draw"]["factors"]
        rows.append((i, d))
    return rows


def selftest():
    """Known margin: L = wc/s e^{-s Td}, wc 100 rad/s, Td 5 ms -> crossover 100 rad/s, PM = 90 deg - wc Td = 61.35 deg, GM = inf."""
    w = np.geomspace(1.0, 2000.0, 3000)
    L = 100.0 / (1j * w) * np.exp(-1j * w * 0.005)
    m = ME.margins(w, L)
    assert abs(m["pm_deg"] - (90 - math.degrees(0.5))) < 0.2, m["pm_deg"]
    # the glue: nominal g = 1 (e = 1), delay 0 reproduces MM.margins_of(L_indi, HEAD-like) exactly
    c = cfg(1.0, TAU0, 0.0)
    a = margins(c)["rate"]["pm"]
    b = MM.margins_of(MM.L_indi, 800.0, npts=500, **dict(c, att_p=0.0))["pm_deg"]
    assert abs(a - b) < 0.5, (a, b)
    # higher e (controller gain too high) must cost phase margin
    assert margins(cfg(2.0, TAU0, 0.0))["rate"]["pm"] < a
    print("self-test ok (known PM 61.35 deg)")


def fmt(r):
    return "%5.1f/%5.1f@%4.1f" % (r["pm"], r["gm"], r["fc"])


def table():
    L = ["| run | axis | e | tau up/down ms | delay ms | n | rate PM/GM@Hz (down) | att PM/GM@Hz (down) | rate (mean) | att (mean) | obs |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    res = []
    L.append("| nom | - | 1 | 33/33 | 0 | 1 | " + " | ".join(
        [fmt(margins(cfg(1, TAU0, 0))[k]) for k in ("rate", "att")] * 1) + " | same | same | - |")
    for i, d in run_cfgs():
        for ax in ("roll", "pitch"):
            e = d["g1_err"][ax]
            up = TAU0 * d["tau_scale"]["value"]
            dn, mean = taus(d["tau_scale"]["value"], d["tau_asym"]["value"])
            dl, fr = d["loop_delay"]["total_ms"], d["tel_latency"].get("frames", 0)
            md, mm = margins(cfg(e, dn, dl, fr)), margins(cfg(e, mean, dl, fr))
            obs = OSC.get(i) == ax
            res.append(dict(run=i, axis=ax, e=e, down=md, mean=mm, obs=obs))
            L.append("| %d | %s | %.2f | %.0f/%.0f | %.2f | %d | %s | %s | %s | %s | %s |" % (
                i, ax, e, up * 1e3, dn * 1e3, dl, 1 + fr, fmt(md["rate"]), fmt(md["att"]), fmt(mm["rate"]), fmt(mm["att"]),
                "OSC" if obs else ""))
    return "\n".join(L), res


def grid(**over):
    """Worst-case (delay 10 ms, 2 frames tel) PM over e x tau grid; tau = 33 ms x mult (down value; up = mult 1 asym 3 -> use mult as tau_r)."""
    es = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    ms = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    out = {}
    for e in es:
        for mu in ms:
            out[(e, mu)] = margins(cfg(e, TAU0 * mu, 10.0, 2, **over))
    return es, ms, out


def grid_md(es, ms, out, key):
    L = ["| e \\ tau x | " + " | ".join("%.1f" % m for m in ms) + " |", "|---|" + "---|" * len(ms)]
    for e in es:
        L.append("| %.2f | " % e + " | ".join("%.0f" % out[(e, m)][key]["pm"] for m in ms) + " |")
    return "\n".join(L)


if __name__ == "__main__":
    selftest()
    t, res = table()
    print(t)
    es, ms, out = grid()
    print("\nrate PM grid, delay 10 ms, 2 frames\n" + grid_md(es, ms, out, "rate"))
    print("\natt PM grid\n" + grid_md(es, ms, out, "att"))
    if len(sys.argv) > 1:
        os.makedirs(sys.argv[1], exist_ok=True)
        open(os.path.join(sys.argv[1], "tables.md"), "w").write(t + "\n")
