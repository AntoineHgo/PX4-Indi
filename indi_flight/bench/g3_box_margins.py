#!/usr/bin/env python3
"""S187 Q22 model check: rate/attitude PM and GM at the fast-motor corner and on the 20 box pre-test draws.

    python3 bench/g3_box_margins.py [OUT_MD]

Reuses g3_osc_margins.cfg/margins (margins_models.L_indi, L_att_indi; K 20, ACT_TC 0.033, MC_ROLL/PITCH_P 8, measured path,
800 Hz = freeze params results/g5_freeze_s157/params.params). Asymmetric tau enters as one linear tau: slow = max(up, down), mean.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g3_osc_margins as O  # noqa: E402

DRAWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "g3_box_s187", "pretest_draws")
F = lambda m: "%.0f/%.1f @%.2f" % (m["pm"], m["gm"], m["fc"])


def corner():
    L = ["| e | tau x | delay ms | n=1+tel frames | rate PM deg / GM dB @Hz | att PM / GM @Hz |", "|---|---|---|---|---|---|"]
    res = []
    for e in (0.8, 1.0, 1.2):
        for tau in (0.5, 1.0):
            for fr in (0, 3):
                m = O.margins(O.cfg(e, O.TAU0 * tau, 10.0, fr))
                res.append((e, tau, fr, m))
                L.append("| %.1f | %.1f | 10 | %d | %s | %s |" % (e, tau, 1 + fr, F(m["rate"]), F(m["att"])))
    return "\n".join(L), res


def draws():
    L = ["| run | axis | e | tau up/down ms | delay ms | n=1+frames | rate PM slow/mean | att PM slow/mean | <30 |", "|---|---|---|---|---|---|---|---|---|"]
    res = []
    for i in range(20):
        f = json.load(open(os.path.join(DRAWS, "run_%03d.json" % i)))["factors"]
        up, dn = O.TAU0 * f["tau_up"]["value"], O.TAU0 * f["tau_down"]["value"]
        slow, mean = max(up, dn), 0.5 * (up + dn)
        dl, fr = f["loop_delay"]["total_ms"], f["tel_latency"].get("frames", 0)
        for ax in ("roll", "pitch"):
            e = f["g1_err"][ax]
            ms, mm = O.margins(O.cfg(e, slow, dl, fr)), O.margins(O.cfg(e, mean, dl, fr))
            low = min(ms["rate"]["pm"], ms["att"]["pm"], mm["rate"]["pm"], mm["att"]["pm"])
            res.append(dict(run=i, axis=ax, e=e, slow=ms, mean=mm, low=low))
            L.append("| %d | %s | %.2f | %.0f/%.0f | %.2f | %d | %.0f/%.0f | %.0f/%.0f | %s |" % (
                i, ax, e, up * 1e3, dn * 1e3, dl, 1 + fr, ms["rate"]["pm"], mm["rate"]["pm"], ms["att"]["pm"], mm["att"]["pm"],
                "**LOW**" if low < 30 else ""))
    return "\n".join(L), res


if __name__ == "__main__":
    O.selftest()
    t1, r1 = corner()
    t2, r2 = draws()
    out = "## Fast-motor corner (tau both directions x tau, loop delay 10 ms)\n" + t1 + "\n\n## 20 box pre-test draws (roll, pitch)\n" + t2 + "\n"
    w = min(r2, key=lambda r: r["low"])
    out += "\nWorst PM over draws (slow or mean tau, rate or att): %.1f deg, run %d %s\n" % (w["low"], w["run"], w["axis"])
    print(out)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write(out)
