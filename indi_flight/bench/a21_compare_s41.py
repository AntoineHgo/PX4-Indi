#!/usr/bin/env python3
"""A-21 closing test 2 (S41): model-only INDI roll loop, margins_models.L_indi evaluated with the as-coded values at the
measured bins, against the measured per-bin L, plus the smallest extra plant element that closes the gap.
Read-only on margins_models.py (imported).  Run:  a21_compare_s41.py [--out tables.md]
Hypotheses:  A0 as coded | (a) extra pure delay | (b) extra first-order lag | (c) plant tau_r | (d) gain g = G1_true/G1_set
             ATT = rate setpoint from the attitude P loop (MC_ROLL_P = 8, airframe 4040_gz_quad5in) closes around the break
             point: nu = K (rate_sp - F w), rate_sp = -Patt theta, theta = integral of w  ->  K (F + Patt Ia) Pn.
"""
import argparse, json, math, os, re, sys
import numpy as np
from scipy.optimize import least_squares, minimize_scalar

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import margins_models as MM  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
FILES = {"s41_seed2": "indi_flight/results/stage2_s41/margins_model_long_s2.txt",
         "s40_seed1": "indi_flight/results/stage2_s40/pretest_inj/margins_model_long.txt"}
FIT_BAND = (2.0, 12.7)  # Hz: below, the position/velocity loops also close around the break; above, |L| < -10 dB and noisy
FS = 800.0
AS_CODED = dict(MM.INDI_DEF)  # eta 1, g 1, Tb 0, tau_r 0.033, tau_m 0.02, d_m 0 (MC_INDI_DELAY), n 1, K 20, G1 320, 40/20 Hz, lat 0
PATT_AIRFRAME = 8.0  # MC_ROLL_P set-default in 4040_gz_quad5in (module default 4.0)


def load(path):
    t = open(os.path.join(REPO, path)).read()
    f = json.loads(re.search(r"^f (\[.*\])", t, re.M).group(1))
    db = json.loads(re.search(r"^\|L\| dB (\[.*\])", t, re.M).group(1))
    ph = json.loads(re.search(r"^arg deg (\[.*\])", t, re.M).group(1))
    js = json.loads([l for l in t.splitlines() if l.startswith("{")][-1])
    return np.array(f), np.array(db), np.array(ph), js


def L_ext(w, fs=FS, Td=0.0, tx=0.0, Patt=0.0, Tatt=0.0, **kw):
    """L_indi (model-only path, same recursions) with: extra plant delay Td [s] and lag tx [s] on the plant (Pn, Va; the
    actuator model does not know them), and the attitude loop term Patt (integral of w, extra delay Tatt [s])."""
    p = dict(AS_CODED); p.update(kw)
    w = np.asarray(w, float); T = 1.0 / fs; zi = np.exp(-1j * w * T)
    a = math.exp(-T / p["tau_r"]); c1 = p["tau_r"] * (1 - a); c2 = T - c1
    zl = zi ** p["lat"]; Ar0 = (1 - a) * zi / (1 - a * zi)
    X = np.exp(-1j * w * Td) / (1 + 1j * w * tx)
    ge = p["g"] * p["eta"] * X
    Pn = ge * zl * (c1 * Ar0 + c2) * zi / (1 - zi)
    Va = ge * zl * zi * (c1 * Ar0 + c2) / T
    F = MM.tf_lpf2p(zi, fs, p["gyro_fc"]); aF = F * MM.tf_alpha(zi, fs, p["dgyro_fc"])
    am = math.exp(-T / p["tau_m"])
    Tmod = aF * p["eta_m"] * (1 - am) * zi / (1 - am * zi) * zi ** p["d_m"]
    Ia = T * zi / (1 - zi) * np.exp(-1j * w * Tatt)
    return p["K"] * (F + Patt * Ia) * Pn + aF * Va - Tmod


def err(Lm, f, db, ph):
    """per-bin log-complex residual: (dB error, deg error) of model - measured, wrapped."""
    L = Lm(2 * np.pi * f)
    edb = 20 * np.log10(np.abs(L)) - db
    edg = (np.degrees(np.angle(L)) - ph + 180) % 360 - 180
    return edb, edg


def cost_vec(edb, edg):  # 1 rad = 8.686 dB = 57.3 deg
    return np.concatenate([edb / 8.686, np.radians(edg)])


def rms_eq(edb, edg):
    return 8.686 * math.sqrt(np.mean((edb / 8.686) ** 2 + np.radians(edg) ** 2))


def margins(**kw):
    m = MM.margins_of(lambda w, fs, **k: L_ext(w, fs, **k), FS, **kw)
    return m["pm_deg"], m["f_c"] if "f_c" in m else m["crossings"][0]["f_c"], m["gm_db"], m["phase_crossings"][0]["f"] if m.get("phase_crossings") else float("nan")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None); a = ap.parse_args()
    data = {k: load(v) for k, v in FILES.items()}
    out = []
    P = out.append
    P("As-coded parameters (MM.INDI_DEF): " + json.dumps({k: AS_CODED[k] for k in ("tau_r", "tau_m", "d_m", "n", "K", "G1", "gyro_fc", "dgyro_fc", "lat", "g", "eta")}))
    fA = np.concatenate([d[0] for d in data.values()]); dA = np.concatenate([d[1] for d in data.values()]); pA = np.concatenate([d[2] for d in data.values()])
    sel = (fA >= FIT_BAND[0]) & (fA <= FIT_BAND[1])

    def resid(x, names, base):
        kw = dict(base); kw.update(dict(zip(names, x)))
        edb, edg = err(lambda w: L_ext(w, **kw), fA[sel], dA[sel], pA[sel])
        return cost_vec(edb, edg)

    def fit(names, x0s, lo, hi, base=None):
        base = base or {}; best = None
        for x0 in x0s:
            r = least_squares(resid, x0, args=(names, base), bounds=(lo, hi))
            if best is None or r.cost < best.cost: best = r
        kw = dict(base); kw.update(dict(zip(names, best.x)))
        edb, edg = err(lambda w: L_ext(w, **kw), fA[sel], dA[sel], pA[sel])
        return kw, dict(zip(names, best.x)), rms_eq(edb, edg)

    hyps = []
    hyps.append(("A0 as coded (no outer loop)", {}, {}, 0))
    hyps.append(("ATT only: Patt = 8 (airframe), no fit", dict(Patt=PATT_AIRFRAME), {}, 0))
    for name, names, x0s, lo, hi, base in [
        ("(a) extra pure delay Td", ["Td"], [[0.002], [0.01]], [0], [0.1], {}),
        ("(b) extra first-order lag tx", ["tx"], [[0.002], [0.01]], [0], [0.1], {}),
        ("(c) plant tau_r", ["tau_r"], [[0.04], [0.06]], [0.01], [0.3], {}),
        ("(d) gain g = G1_true/G1_set", ["g"], [[1.0], [1.5]], [0.2], [5], {}),
        ("ATT + (a) delay Td, Patt=8", ["Td"], [[0.002], [0.01]], [0], [0.1], dict(Patt=PATT_AIRFRAME)),
        ("ATT + (b) lag tx, Patt=8", ["tx"], [[0.002], [0.01]], [0], [0.1], dict(Patt=PATT_AIRFRAME)),
        ("ATT + (c) tau_r, Patt=8", ["tau_r"], [[0.04], [0.033]], [0.01], [0.3], dict(Patt=PATT_AIRFRAME)),
        ("ATT + (d) g, Patt=8", ["g"], [[1.0], [1.5]], [0.2], [5], dict(Patt=PATT_AIRFRAME)),
        ("ATT with Patt free", ["Patt"], [[4.0], [10.0]], [0], [60], {}),
        ("ATT Patt=8 + g + Td", ["g", "Td"], [[1.0, 0.001], [1.5, 0.005]], [0.2, 0], [5, 0.1], dict(Patt=PATT_AIRFRAME)),
    ]:
        kw, fitted, rms = fit(names, x0s, lo, hi, base)
        hyps.append((name, kw, fitted, rms))
    # evaluate every hypothesis
    P("\n## Fit summary (fit band %.1f-%.1f Hz, both flights, %d bins)\n" % (FIT_BAND[0], FIT_BAND[1], sel.sum()))
    P("| hypothesis | fitted | rms resid (dB-equiv) | PM deg @Hz | GM dB @Hz |")
    P("|---|---|---|---|---|")
    for name, kw, fitted, rms in hyps:
        edb, edg = err(lambda w: L_ext(w, **kw), fA[sel], dA[sel], pA[sel])
        r = rms_eq(edb, edg)
        try:
            pm, fc, gm, fg = margins(**kw)
            mtxt = "%.1f @%.2f | %.1f @%.2f" % (pm, fc, gm, fg)
        except Exception as e:
            mtxt = "margins failed: %s | -" % e
        fit_s = ", ".join("%s=%.4g" % (k, v) for k, v in fitted.items()) or "-"
        P("| %s | %s | %.2f | %s |" % (name, fit_s, r, mtxt))
    P("\nMeasured: " + "; ".join("%s PM %.1f @%.2f Hz, GM %.1f dB @%.2f Hz" % (k, d[3]["pm_deg"], d[3]["crossings"][0]["f_c"], d[3]["gm_db"], d[3]["phase_crossings"][0]["f"]) for k, d in data.items()))
    # per-bin tables
    show = [h for h in hyps if h[0].split(" ")[0] in ("A0", "ATT") and ("free" in h[0] or "only" in h[0] or h[0].startswith("A0"))]
    show += [h for h in hyps if h[0].startswith("(a)") or h[0].startswith("(b)") or h[0].startswith("(c)") or h[0].startswith("ATT + (a)") or h[0].startswith("ATT Patt=8 + g")]
    for k, (f, db, ph, js) in data.items():
        P("\n## Per-bin %s: measured vs model (|L| dB / arg deg; err = model - measured)\n" % k)
        hdr = "| f Hz | meas dB | meas deg |" + "".join(" %s dB | deg |" % h[0][:14] for h in show)
        P(hdr); P("|" + "---|" * (3 + 2 * len(show)))
        for i, fi in enumerate(f):
            row = "| %.1f | %.1f | %.1f |" % (fi, db[i], ph[i])
            for name, kw, fitted, rms in show:
                L = L_ext(2 * np.pi * np.array([fi]), **kw)[0]
                row += " %.1f | %.0f |" % (20 * np.log10(abs(L)), (np.degrees(np.angle(L))))
            P(row + ("  (outside fit band)" if not (FIT_BAND[0] <= fi <= FIT_BAND[1]) else ""))
        P("")
        for name, kw, fitted, rms in show:
            edb, edg = err(lambda w: L_ext(w, **kw), f, db, ph)
            m = (f >= FIT_BAND[0]) & (f <= FIT_BAND[1])
            P("residual %-34s in-band rms %.2f dB-eq (max |dB| %.1f, max |deg| %.0f)" % (name, rms_eq(edb[m], edg[m]), np.abs(edb[m]).max(), np.abs(edg[m]).max()))
    txt = "\n".join(out)
    print(txt)
    if a.out: open(a.out, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
