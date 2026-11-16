#!/usr/bin/env python3
"""S48: INDI roll loop broken at the torque setpoint (M3a) WITH the attitude P loop closed.

Extends margins_models.L_indi: the rate-error term K F Pn becomes K F Pn (1 + P_att T z^-1/(1-z^-1)) because the
attitude loop feeds rate_sp = P_att (att_sp - att), att = sum(w) T (no attitude-estimate filtering modelled).
Compares with the measured S47 bins (results/stage2_s47/roll_m3a/model_g2_a001_margins.txt) and sweeps K_R, P_att.
Usage: att_loop_model_s48.py <out.md>
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_models as MM  # noqa: E402
import margins_est as ME  # noqa: E402


def L_att(w, fs=800.0, P_att=8.0, **kw):
    p = dict(MM.INDI_DEF); p.update(kw)
    L0 = MM.L_indi(w, fs=fs, **p)
    p2 = dict(p); p2["K"] = 0.0
    Lk0 = MM.L_indi(w, fs=fs, **p2)          # L without the rate-error term
    rate_term = L0 - Lk0                      # = K F Pn
    zi = np.exp(-1j * np.asarray(w, float) / fs)
    return Lk0 + rate_term * (1.0 + P_att * (1.0 / fs) * zi / (1 - zi))


def marg(fun, **kw):
    w = np.logspace(math.log10(2 * math.pi * 0.2), math.log10(2 * math.pi * 150), 300)
    m = ME.margins(w, fun(w, **kw), n_dense=5000)
    return m


def main(out):
    meas = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results/stage2_s47/roll_m3a/model_g2_a001_margins.txt")).read().splitlines()
    f = json.loads(meas[1].split(" ", 1)[1]); mag = json.loads(meas[2].split(" ", 2)[2]); ph = json.loads(meas[3].split(" ", 2)[2])
    base = dict(tau_r=0.033, tau_m=0.02, K=20.0, meas=False)
    lines = ["# S48 attitude-loop model of the INDI roll M3a break", "",
             "Model: margins_models.L_indi (model-only path, tau plant 33 ms, ACT_TC 20 ms, K_R 20, 800 Hz) x attitude P term.", "",
             "| f Hz | meas dB | meas deg | rate-only dB | deg | +att P8 dB | deg |", "|---|---|---|---|---|---|---|"]
    for fi, mi, pi in zip(f, mag, ph):
        w = np.array([2 * math.pi * fi])
        a = MM.L_indi(w, **base)[0]; b = L_att(w, P_att=8.0, **base)[0]
        lines.append("| %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |" % (fi, mi, pi, 20 * math.log10(abs(a)), math.degrees(np.angle(a)),
                     20 * math.log10(abs(b)), math.degrees(np.angle(b))))
    lines += ["", "## Margins (model)", "", "| case | PM deg | f_c Hz | GM dB | DM ms |", "|---|---|---|---|---|"]
    def row(name, fun, **kw):
        m = marg(fun, **kw)
        fc = m["crossings"][0]["f_c"] if m.get("crossings") else float("nan")
        lines.append("| %s | %.1f | %.2f | %.1f | %.1f |" % (name, m["pm_deg"] or float("nan"), fc, m["gm_db"] or float("nan"), 1e3 * (m["dm_s"] or float("nan"))))
    row("rate only K20", MM.L_indi, **base)
    row("measured S47: PM 22.3 f_c 3.48 GM 4.1 DM 17.9 -> model K20 P8", L_att, P_att=8.0, **base)
    row("K20 P8, ACT_TC matched 33 ms", L_att, P_att=8.0, **dict(base, tau_m=0.033))
    for K in (20, 30, 40, 60):
        for P in (3, 4, 5, 6, 8):
            row("K%d P%d" % (K, P), L_att, P_att=float(P), **dict(base, K=float(K)))
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
