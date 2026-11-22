#!/usr/bin/env python3
"""S207 Q26 model check, no flight: K scaled 1/tau_c (K tau_c held at 20 x 0.033 = 0.66) against fixed K 20.

    python3 q26_kscale.py [OUTDIR]

Reuses cause_s199/margins_s200 (cfg, loops, draw, read; method of MARGINS_S200.md).  Only the controller K / ACT_TC are overridden here
(cfg() takes tau_m and lead; K is set on the returned dict), so no change to the existing scripts.
Controller ACT_TC rules: ref 0.033 | a = tau_slow of the plant | b = 1.5 x tau_slow.  Gain rules: fixed K 20 | scaled K = 0.66 / tau_c.
Lead as in firmware: c = min(K tau_c, kMaxLeadGain 2).  Corners: plant tau x0.5/x3 of 33 ms (symmetric), delay 0/10 ms, tel frames 0/3, e 0.8/1.2.
"""
import itertools
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "g3_refly_s199", "cause_s199"))
import margins_s200 as M  # noqa: E402

K0, TC0, KTC, CAP = 20.0, 0.033, 20.0 * 0.033, 2.0
LOOPS = ("rate", "rate+att")
ATT = ("att",)
TCRULES = ("ref", "a", "b")
GAINS = ("fixed", "scaled")


def case(axis, e, tau, delay, frames, tcrule, gain):
    tc = {"ref": TC0, "a": tau, "b": 1.5 * tau}[tcrule]
    tc = min(tc, 0.2)                                  # firmware clamp of MC_INDI_ACT_TC
    k = K0 if gain == "fixed" else KTC / tc
    k = min(max(k, 1.0), 100.0)                        # MC_INDI_K_R/P limits
    p = M.cfg(axis, e, tau, delay, frames, tau_m=tc, lead=min(k * tc, CAP))
    p["K"] = k
    r = M.loops(p, LOOPS + ATT)
    return dict(tc=tc, K=k, lead=min(k * tc, CAP), ktc=k * tc, cap=k * tc > CAP, **{n: r[n] for n in r})


def row(name, axis, e, tau, delay, frames, tcrule, gain):
    c = case(axis, e, tau, delay, frames, tcrule, gain)
    out = [name, tcrule, gain, "%.4f" % c["tc"], "%.2f" % c["K"], "%.2f" % c["ktc"], "yes" if c["cap"] else "no"]
    for n in LOOPS + ATT:
        r = c[n]
        out += ["%.1f" % r["pm"], "%.1f" % r["gm"], "%.2f" % r["fc"], "%.1f" % (r["dm"] * 1e3)]
    return out, c


HDR = ["plant", "tc_rule", "gain_rule", "ACT_TC", "K", "K_tau_c", "cap_binds"]
for n in LOOPS + ATT:
    HDR += [n + "_PM_deg", n + "_GM_dB", n + "_fc_Hz", n + "_DM_ms"]


def selftest():
    # reproduces MARGINS_S200 section 1 (drawn 245, slow tau, ACT_TC 0.033, K 20): rate 44/24.9/68 ms, rate+att 6/24.9/7.5 ms, att 24/3.1
    f = M.draw(245)
    ax, e = "pitch", f["g1_err"]["pitch"]
    tau = 0.033 * max(f["tau_up"]["value"], f["tau_down"]["value"])
    c = case(ax, e, tau, f["loop_delay"]["total_ms"], f["tel_latency"]["frames"], "ref", "fixed")
    assert abs(c["rate"]["pm"] - 44) < 1 and abs(c["rate+att"]["pm"] - 6) < 1.5 and abs(c["att"]["gm"] - 3.1) < 0.3, c
    # MARGINS_S200 sec 2b: realised box worst rate+att at tau_m 0.033 is 5.7 deg (the 'ref'/'fixed' corner set)
    w = min(case("pitch", e_, 0.033 * s, d, fr, "ref", "fixed")["rate+att"]["pm"] for s, d, e_, fr in corners(0.8, 1.2))
    assert abs(w - 5.7) < 0.5, w
    # scaled rule at ACT_TC 0.033 is identical to fixed (K tau_c = 0.66 by construction)
    a = case("pitch", 1.0, 0.033, 5.0, 1, "ref", "scaled")
    b = case("pitch", 1.0, 0.033, 5.0, 1, "ref", "fixed")
    assert abs(a["K"] - 20) < 1e-9 and abs(a["rate"]["pm"] - b["rate"]["pm"]) < 1e-6
    print("SELFTEST ok: reproduces MARGINS_S200 (245 drawn, realised-box worst 5.7 deg)")


def corners(e1, e2):
    return [(s, d, e, fr) for s, d, e, fr in itertools.product((0.5, 3.0), (0.0, 10.0), (e1, e2), (0, 3))]


def main(out):
    os.makedirs(out, exist_ok=True)
    selftest()
    rows = []
    for run, ax in ((245, "pitch"), (239, "roll"), (283, "pitch")):
        f = M.draw(run)
        e = f["g1_err"][ax]
        tau = 0.033 * max(f["tau_up"]["value"], f["tau_down"]["value"])
        for t, g in itertools.product(TCRULES, GAINS):
            r, _ = row("run%d_%s" % (run, ax), ax, e, tau, f["loop_delay"]["total_ms"], f["tel_latency"]["frames"], t, g)
            rows.append(r)
    with open(os.path.join(out, "drawn.tsv"), "w") as fh:
        fh.write("\t".join(HDR) + "\n" + "\n".join("\t".join(r) for r in rows) + "\n")
    worst = {}
    for tag, es in (("e0.8-1.2", (0.8, 1.2)), ("e0.5-2.0", (0.5, 2.0))):
        crow, wr = [], []
        for t, g in itertools.product(TCRULES, GAINS):
            wst = {n: dict(pm=1e9, gm=1e9, pmc=None, gmc=None) for n in LOOPS + ATT}
            ncap = 0
            for c in corners(*es):
                s, d, e, fr = c
                name = "c_tau%g_d%g_e%g_fr%d" % (s, d, e, fr)
                r, cc = row(name, "pitch", e, 0.033 * s, d, fr, t, g)
                crow.append(r)
                ncap += cc["cap"]
                for n in LOOPS + ATT:
                    if cc[n]["pm"] < wst[n]["pm"]:
                        wst[n].update(pm=cc[n]["pm"], pmc=name)
                    if cc[n]["gm"] < wst[n]["gm"]:
                        wst[n].update(gm=cc[n]["gm"], gmc=name)
            worst[(tag, t, g)] = (wst, ncap)
        with open(os.path.join(out, "corners_%s.tsv" % tag), "w") as fh:
            fh.write("\t".join(HDR) + "\n" + "\n".join("\t".join(r) for r in crow) + "\n")
    with open(os.path.join(out, "worst.tsv"), "w") as fh:
        fh.write("box\ttc_rule\tgain_rule\tloop\tworst_PM_deg\tPM_corner\tworst_GM_dB\tGM_corner\tcorners_with_cap_binding_of_16\n")
        for (tag, t, g), (w, ncap) in worst.items():
            for n in LOOPS + ATT:
                fh.write("%s\t%s\t%s\t%s\t%.1f\t%s\t%.1f\t%s\t%d\n" % (tag, t, g, n, w[n]["pm"], w[n]["pmc"], w[n]["gm"], w[n]["gmc"], ncap))
    print(open(os.path.join(out, "worst.tsv")).read())
    print(open(os.path.join(out, "drawn.tsv")).read())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
