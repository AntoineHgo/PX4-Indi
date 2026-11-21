#!/usr/bin/env python3
"""G2 phase-plateau GM for every stage-6 freeze cell (S164).  One command, no args:
    python3 indi_flight/bench/g2_plateau_gm_s164.py          (--selftest runs only the self-test)
Writes indi_flight/results/g2_plateau_s164.md.

GATES G2 pass: GM is reported with the minimum of 1/|L| over frequencies where arg L is within 10 deg of -180 deg
(phase plateau GM); the pass uses the smaller of the two.

Method.  L comes from the primary estimator margins_est.frf_periodic, called exactly as each cell's CSV script did:
  rate  (results/g2_freeze_s160/*/s1.csv, m3a_margins_pretest.py): Tp 10, 1-60 Hz, discard 1, fs = 800/400 from cell name.
  outer (results/g2_outer_freeze_s163/*_pinj.csv, pinj_csv.estimate): z Tp 10, xy Tp 20, 0.2-8 Hz, discard 1.
  att   (results/g2_att_freeze_s162/*_att.csv): the window CSV was not kept (only the ulg); the FRF table written by
        ratesp_csv.py (f, |L| dB, unwrapped arg L, accepted; %.9g) is used and fed to margins_est.margins_from_frf's
        own call (margins(w[acc], L[acc], top_rejected=not acc[-1])).  Same numbers as the original call.
Phase: unwrap(angle(L)) over the accepted bins ascending in f (as margins_est.margins does), distance to -180 deg
taken modulo 360: dist = |wrap(arg + 180)|.  Plateau bins = accepted (coherent: 0.8 far / 0.9 near crossover) bins with
dist <= 10 deg.  Plateau GM = -20 log10(max |L|) over those bins (= min 1/|L|); NaN if there are none.  A dense
check (the same cubic-spline interpolation as margins_est, 20000 points) is also reported.
Pass: PM >= 45 deg and min(GM, plateau GM) >= 6 dB (NaN ignored; if both NaN: 'n/a', passes only when PM does, flagged).
"""
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import margins_est as me  # noqa: E402

RES = os.path.join(HERE, "..", "results")
OUT = os.path.join(RES, "g2_plateau_s164.md")
PM_MIN, GM_MIN, WIN = 45.0, 6.0, 10.0


def dist180(arg_deg):
    return np.abs((np.asarray(arg_deg) + 180.0 + 180.0) % 360.0 - 180.0)


def plateau(f, L, win=WIN):
    """f [Hz], L complex on accepted bins. Returns (plateau GM dB, f at min 1/|L|, n bins, dense GM dB, f dense)."""
    o = np.argsort(f)
    f, L = np.asarray(f, float)[o], np.asarray(L, complex)[o]
    ph = np.degrees(np.unwrap(np.angle(L)))
    m = dist180(ph) <= win
    nan = float("nan")
    if m.any():
        db = 20 * np.log10(np.abs(L[m]))
        i = int(np.argmax(db))
        g, fg = float(-db[i]), float(f[m][i])
    else:
        g, fg = nan, nan
    w = 2 * np.pi * f
    lw = np.log(w)
    sm = me._natural_spline(lw, np.log(np.abs(L)))
    sp = me._natural_spline(lw, np.unwrap(np.angle(L)))
    lq = np.linspace(lw[0], lw[-1], 20000)
    md, pd = sm(lq), np.degrees(sp(lq))
    k = dist180(pd) <= win
    if k.any():
        j = int(np.argmax(md[k]))
        gd, fd = float(-20 * md[k][j] / np.log(10)), float(np.exp(lq[k][j]) / 2 / np.pi)
    else:
        gd, fd = nan, nan
    m2 = m & (np.abs(L) < 1.0)
    gr = float(-20 * np.log10(np.abs(L[m2]).max())) if m2.any() else nan
    return g, fg, int(m.sum()), gd, fd, gr, float(ph[m][0]) if m.any() else nan, float(f[m][0]) if m.any() else nan


def verdict(pm, gm, pg):
    gs = [v for v in (gm, pg) if np.isfinite(v)]
    mn = min(gs) if gs else float("nan")
    if not np.isfinite(pm):
        return mn, "FAIL(no PM)"
    if gs:
        return mn, "PASS" if (pm >= PM_MIN and mn >= GM_MIN) else "FAIL"
    return mn, "PASS(n/a GM)" if pm >= PM_MIN else "FAIL"


def selftest():
    lines = []
    # 1) plateau at -175 deg, |L| = -8 dB, no exact -180 crossing
    f = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0])
    db = np.array([20.0, 8.0, -2.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0])
    ph = np.array([-120.0, -140.0, -160.0, -175.0, -175.0, -175.0, -175.0, -175.0, -175.0])
    # bins with phase in (-170,-190) all have |L| = -8 dB; the -160 bin is 20 deg away (excluded)
    L = 10 ** (db / 20) * np.exp(1j * np.radians(ph))
    mg = me.margins(2 * np.pi * f, L)
    pg = plateau(f, L)[0]
    ok1 = np.isnan(mg["gm_db"]) and abs(pg - 8.0) < 0.05
    lines.append("- plateau -175 deg, |L| = -8 dB, no crossing: classic GM = %s, plateau GM = %.2f dB (expect NaN / 8.00): %s"
                 % (mg["gm_db"], pg, "OK" if ok1 else "FAIL"))
    # 2) clean crossing: L = a/(jw) exp(-jw tau), a = 6 rad/s, tau = 0.05 s -> wpc = pi/2/tau, GM = 20log10(wpc/a)
    f = me.log_bins(0.2, 20.0, 10.0)
    w = 2 * np.pi * f
    L = 6.0 / (1j * w) * np.exp(-1j * w * 0.05)
    mg = me.margins(w, L)
    g, fg, n, gd, fd = plateau(f, L)[:5]
    exact = 20 * np.log10(np.pi / 2 / 0.05 / 6.0)
    ok2 = abs(mg["gm_db"] - exact) < 0.05 and g >= mg["gm_db"] - 1.0 and g <= mg["gm_db"] + 0.0 + 1e-9 + 3.0 and n >= 1
    lines.append("- clean crossing (exact GM %.2f dB): classic GM %.2f, plateau GM %.2f dB over %d bins at %.2f Hz, dense %.2f dB"
                 " (need plateau >= GM - 1 dB): %s" % (exact, mg["gm_db"], g, n, fg, gd, "OK" if ok2 else "FAIL"))
    return ok1 and ok2, lines


def num(s):
    return float(s)


def rate_cells():
    out = []
    for d in sorted(glob.glob(os.path.join(RES, "g2_freeze_s160", "*_s[0-9]"))):
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "s1.csv")) or not os.path.exists(os.path.join(d, "margins.txt")):
            continue
        hz = 400.0 if "400" in name else 800.0
        t, dd, x, y = me.read_csv(os.path.join(d, "s1.csv"))
        res = me.frf_periodic(dd, x, y, hz, 10.0, me.log_bins(1.0, 60.0, 10.0, per_decade=10), 1, t=t)
        mg = me.margins_from_frf(res)
        txt = open(os.path.join(d, "margins.txt")).read()
        ref_pm = num(re.search(r'"pm_deg": ([-0-9.eNa]+)', txt).group(1))
        ref_gm = num(re.search(r'"gm_db": ([-0-9.eNa]+)', txt).group(1))
        a = res["accepted"]
        out.append(("rate", name, mg, ref_pm, ref_gm, res["f"][a], res["L"][a], int(a.sum()), len(a)))
    return out


def att_cells():
    out = []
    for p in sorted(glob.glob(os.path.join(RES, "g2_att_freeze_s162", "*_att.csv"))):
        name = os.path.basename(p)[:-8]
        j = json.load(open(p.replace("_att.csv", "_margins.json")))
        a = np.genfromtxt(p, delimiter=",", names=True)
        acc = a["accepted"] > 0.5
        L = 10 ** (a["L_db"] / 20) * np.exp(1j * np.radians(a["arg_L_deg"]))
        mg = me.margins(2 * np.pi * a["f_hz"][acc], L[acc], top_rejected=not bool(acc[-1]))
        out.append(("att", name, mg, j["pm_deg"], j["gm_db"], a["f_hz"][acc], L[acc], int(acc.sum()), len(acc)))
    return out


def outer_cells():
    out = []
    for p in sorted(glob.glob(os.path.join(RES, "g2_outer_freeze_s163", "*_pinj.csv"))):
        name = os.path.basename(p)[:-9]
        j = json.load(open(p.replace("_pinj.csv", "_margins.json")))
        Tp = 10.0 if "_ax3_" in name else 20.0
        t, dd, x, y = np.loadtxt(p, delimiter=",", skiprows=1).T
        fs = 1.0 / np.median(np.diff(t))
        res = me.frf_periodic(dd, x, y, fs, Tp, me.log_bins(0.2, 8.0, Tp), 1, t=t)  # = pinj_csv.estimate
        a = res["accepted"]
        mg = me.margins_from_frf(res) if a.sum() >= 2 else {"pm_deg": float("nan"), "gm_db": float("nan")}
        out.append(("outer", name, mg, j["margins"]["pm_deg"], j["margins"]["gm_db"], res["f"][a], res["L"][a],
                    int(a.sum()), len(a)))
    return out


def same(a, b, tol):
    return (np.isnan(a) and np.isnan(b)) or abs(a - b) <= tol


def fmt(v, p=1):
    return "NaN" if not np.isfinite(v) else "%.*f" % (p, v)


def main():
    ok, st = selftest()
    if "--selftest" in sys.argv:
        print("\n".join(st))
        sys.exit(0 if ok else 1)
    md = ["# G2 phase-plateau GM at the stage-6 freeze cells (S164)", "",
          "Script: `indi_flight/bench/g2_plateau_gm_s164.py` (no args). Rule (GATES G2 Pass): pass = PM >= 45 deg and "
          "min(GM, plateau GM) >= 6 dB; plateau GM = -20 log10(max |L|) over coherent kept bins with arg L within 10 deg of "
          "-180 deg.", "",
          "## Method", "",
          "- Estimator: `margins_est.frf_periodic` + `margins_from_frf` (primary), called as each cell's CSV script did "
          "(rate: m3a_margins_pretest.py, Tp 10, 1-60 Hz, fs 800/400 from the cell name; outer: pinj_csv.estimate, z Tp 10 s, "
          "xy Tp 20 s, 0.2-8 Hz; both discard 1).",
          "- Attitude: window CSVs were not kept (ulg only); the stored FRF table `*_att.csv` (f, |L| dB, unwrapped arg, "
          "accepted, %.9g) is rebuilt into L and passed to `margins_est.margins` as `margins_from_frf` does (Tp 10, 0.2-20 Hz).",
          "- Bins used: the estimator's `accepted` bins (coherence >= 0.8, >= 0.9 within a decade of each crossover).",
          "- Phase wrapping: `unwrap(angle(L))` ascending over accepted bins (same as margins_est), distance to -180 deg "
          "mod 360 = |((arg + 360) mod 360) - 180| <= 10 deg (equivalently any -180 + 360 k).",
          "- Plateau GM on measured bins (gate value); a dense check on the margins_est cubic-spline curve (20000 pts) is "
          "listed as 'dense'. 'f_plat' = frequency of the plateau minimum (largest |L| inside the plateau).",
          "- Pass: PM >= 45 and min(GM, plateau) >= 6 dB; NaN ignored; both NaN -> 'PASS(n/a GM)' (no -180 +-10 deg "
          "anywhere in the coherent band).", "",
          "## Self-test", ""] + st + ["", "Self-test: %s" % ("PASS" if ok else "FAIL"), ""]
    cells = rate_cells() + att_cells() + outer_cells()
    md += ["## Reproduction of existing margins", ""]
    bad = 0
    for loop in ("rate", "att", "outer"):
        c = [x for x in cells if x[0] == loop]
        dpm = max(abs(x[2]["pm_deg"] - x[3]) for x in c if np.isfinite(x[3]) and np.isfinite(x[2]["pm_deg"]))
        dgm = max(abs(x[2]["gm_db"] - x[4]) for x in c if np.isfinite(x[4]) and np.isfinite(x[2]["gm_db"]))
        nanmis = [x[1] for x in c if np.isnan(x[2]["gm_db"]) != np.isnan(x[4]) or np.isnan(x[2]["pm_deg"]) != np.isnan(x[3])]
        fails = [x[1] for x in c if not (same(x[2]["pm_deg"], x[3], 0.01) and same(x[2]["gm_db"], x[4], 0.01))]
        bad += len(fails)
        md.append("- %s: %d cells, max |dPM| %.2e deg, max |dGM| %.2e dB, NaN mismatches %s, outside 0.01: %s"
                  % (loop, len(c), dpm, dgm, nanmis or "none", fails or "none"))
    md += ["", "Reproduction: %s" % ("ALL cells within 0.01 deg / 0.01 dB" if bad == 0 else "%d cell(s) differ" % bad), "",
           "## Table", "",
           "| loop | cell | bins | PM deg | GM dB | plateau GM dB | f_plat Hz | n_plat | dense plateau dB | plateau, |L|<1 only dB | min dB | pass |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for loop, name, mg, _, _, f, L, na, nt in cells:
        pm, gm = mg["pm_deg"], mg["gm_db"]
        pg, fg, n, gd, fd, gr, _, flo = plateau(f, L) if len(f) >= 2 else (float("nan"),) * 2 + (0,) + (float("nan"),) * 5
        mn, v = verdict(pm, gm, pg)
        classic_v = verdict(pm, gm, float("nan"))[1]
        rows.append((loop, name, pm, gm, pg, mn, v, classic_v, gd, verdict(pm, gm, gr)[1], fg, flo, gr))
        md.append("| %s | %s | %d/%d | %s | %s | %s | %s | %d | %s | %s | %s | %s |" % (
            loop, name, na, nt, fmt(pm), fmt(gm), fmt(pg), fmt(fg, 2), n, fmt(gd), fmt(gr), fmt(mn), v))
    md += ["", "## Worst cell per loop (by min(GM, plateau); PM worst listed separately)", ""]
    for loop in ("rate", "att", "outer"):
        r = [x for x in rows if x[0] == loop]
        fin = [x for x in r if np.isfinite(x[5])]
        w = min(fin, key=lambda x: x[5]) if fin else None
        wp = min(r, key=lambda x: x[2])
        md.append("- %s: worst min(GM, plateau) = %s dB (%s; GM %s, plateau %s); worst PM = %s deg (%s); fails: %s" % (
            loop, fmt(w[5]) if w else "n/a", w[1] if w else "-", fmt(w[3]) if w else "-", fmt(w[4]) if w else "-",
            fmt(wp[2]), wp[1], [x[1] for x in r if x[6].startswith("FAIL")] or "none"))
    chg = [x for x in rows if x[6] != x[7]]
    md += ["", "Verdict changes versus classic-GM-only pass (literal gate rule): %s" % (", ".join(x[1] for x in chg) or "none"), ""]
    lo = [x for x in rows if np.isfinite(x[4]) and x[4] < 0]
    md += ["Low-frequency artefact check: plateau minima with |L| > 1 (plateau GM < 0 dB, i.e. a bin ABOVE unity gain whose "
           "phase is within 10 deg of -180): %s." % (", ".join("%s (plateau %.1f dB at %.2f Hz)" % (x[1], x[4], x[10]) for x in lo) or "none"),
           "These are not a gain-increase stability margin (|L| > 1 there is the normal low-frequency region of an integrating "
           "loop; the Nyquist encirclement count is unchanged unless the phase crosses -180 deg while |L| > 1). The literal gate "
           "rule counts them; the column 'plateau, |L|<1 only' restricts the plateau to bins below unity gain. Verdicts with "
           "that restriction: %s." % (", ".join("%s %s" % (x[1], x[9]) for x in rows if x[9] != x[6]) or "identical to the literal rule"), ""]
    with open(OUT, "w") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
    sys.exit(0 if ok and bad == 0 else 1)


if __name__ == "__main__":
    main()
