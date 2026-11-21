#!/usr/bin/env python3
"""S165 G2: linear-model cross-check of the measured rate-loop cells (S160/S163, M3a break) and the attitude yaw cells (S162).

Usage: python3 indi_flight/bench/g2_rate_model_s165.py [--selftest]   (no args: regenerates results/g2_freeze_s160/xcheck_rate.md)
Model = margins_models.L_indi (roll/pitch) / L_indi_yaw (yaw), parameters ONLY from the freeze params file and the airframe
model; nothing is tuned to the data.  Margins use margins_est.margins on the same frequency bins as the measurement.
Attitude yaw: L_att = A_att(att_p) * T_cl, T_cl = closed yaw INDI rate loop (setpoint -> rate), built from L_indi_yaw.
"""
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import margins_est as ME  # noqa: E402
import margins_models as MM  # noqa: E402

RES = os.path.join(HERE, "..", "results")
R160 = os.path.join(RES, "g2_freeze_s160")
R162 = os.path.join(RES, "g2_att_freeze_s162")
OUT = os.path.join(R160, "xcheck_rate.md")

# Freeze params (bench/params/quad5in_indi_defaults.params + ID_OK 1, results/g2_freeze_s160/params_*.params):
K, ACT_TC, LEAD, ACT_BLD = 20.0, 0.033, 1.0, 1.0           # MC_INDI_K_*, ACT_TC, LEAD, ACT_BLD (blend tc, s)
G2Y, G1Y = 27.0, 205.0                                     # MC_INDI_G2_Y / G1_Y -> ts = G2/G1
ATT_P = {"roll": 8.0, "pitch": 8.0, "yaw": 3.0}            # MC_ROLL_P/PITCH_P/YAW_P from 4040_gz_quad5in
GYRO_FC, DGYRO_FC = 40.0, 20.0                             # as in margins_models flown configs (UNVERIFIED vs IMU_*_CUTOFF defaults)
TAU_PLANT = 0.033                                          # sim rotor timeConstant 33 ms (ref_airframe_model.md)


def cfg(axis, variant):
    """Model kwargs for one cell variant: '' (measured torque path), 'mo' (W_MAX 0, model path), 'fwdef' (ID_OK 0: K x 0.5, ACT_TC 0.05, W_MAX 0)."""
    k, tc, meas = K, ACT_TC, variant == ""
    if variant == "fwdef":
        k, tc, meas = 0.5 * K, 0.05, False
    lead = min(LEAD * k * tc, 2.0)
    p = dict(K=k, tau_r=TAU_PLANT, tau_m=tc, gyro_fc=GYRO_FC, dgyro_fc=DGYRO_FC, fb_lead=lead, att_p=ATT_P[axis],
             att_lat=1, sp_lead=True, n=1, d_m=0, lat=0, eta=1.0, g=1.0, eta_m=1.0, Tb=ACT_BLD if meas else 0.0, meas=meas)
    if axis == "yaw":
        p.update(ts_fw=G2Y / G1Y, ts_true=G2Y / G1Y)
        p["path"] = "meas" if meas else "model"
    return p


def Lrate(w, fs, axis, variant):
    p = cfg(axis, variant)
    return (MM.L_indi_yaw if axis == "yaw" else MM.L_indi)(w, fs, **p)


def Latt_yaw(w, fs, variant=""):
    """Attitude yaw open loop, break at the rate setpoint: A_att * closed rate loop (setpoint -> rate)."""
    p = cfg("yaw", variant)
    zi = np.exp(-1j * np.asarray(w) * (1.0 / fs))
    L0 = MM.L_indi_yaw(w, fs, **dict(p, att_p=0.0))
    X = MM.L_indi_yaw(w, fs, **dict(p, att_p=1.0)) - L0       # (K + lead) A1 Pn / Dz
    A1 = MM._att_path(zi, fs, 1.0, p["att_lat"])
    Tcl = X / A1 / (1.0 + L0)
    return MM._att_path(zi, fs, p["att_p"], p["att_lat"]) * Tcl


def summ(m):
    c = [x for x in m["crossings"] if x["slope_down"]] or m["crossings"]
    pm = min(x["pm_deg"] for x in c) if c else None
    fc = c[0]["f_c"] if c else None
    gm = min(x["gm_db"] for x in m["phase_crossings"]) if m["phase_crossings"] else None
    return pm, gm, fc


def meas_from(m):
    return summ(m)


def load_rate():
    out = {}
    for d in sorted(glob.glob(os.path.join(R160, "*_s[0-9]"))):
        n = os.path.basename(d)
        mm = re.match(r"^(roll|pitch|yaw)(400|800)(_mo|_fwdef)?_s(\d)$", n)
        f = os.path.join(d, "margins.txt")
        if not mm or not os.path.exists(f):
            continue
        txt = open(f).read().splitlines()
        fl = next(l for l in txt if l.startswith("f ["))
        js = next(l for l in reversed(txt) if l.startswith("{"))
        freq = json.loads(fl[2:])
        m = json.loads(js)
        key = (mm.group(1), int(mm.group(2)), (mm.group(3) or "")[1:])
        out.setdefault(key, []).append((np.array(freq), m))
    return out


def load_att():
    out = {}
    for f in sorted(glob.glob(os.path.join(R162, "ax3_r*_s*_margins.json"))):
        mm = re.search(r"ax3_r(\d+)_s(\d)", f)
        d = json.load(open(f))
        out.setdefault(("yaw-att", int(mm.group(1)), ""), []).append((None, d["margins"]))
    return out


def fmt(x, p=1):
    return "n/a" if x is None else f"{x:.{p}f}"


def selftest():
    ok = True
    # 1: 5 exp(-0.1 s)/s : PM = 180 - 180/pi*(0.1*5) ... wc = 5 -> PM = 90 - deg(0.5) ; GM = 20log10(pi/2/(0.1*5))
    w = np.geomspace(0.2, 60, 400)
    s = 1j * w
    m = ME.margins(w, 5 * np.exp(-0.1 * s) / s)
    pm, gm, fc = summ(m)
    pm_a, gm_a = 90 - np.degrees(0.5), 20 * np.log10(np.pi / 2 / 0.5)
    print(f"selftest 5e^-0.1s/s: PM {pm:.2f} (analytic {pm_a:.2f}), GM {gm:.2f} ({gm_a:.2f}), fc {fc:.3f} ({5 / 2 / np.pi:.3f})")
    ok &= abs(pm - pm_a) < 0.2 and abs(gm - gm_a) < 0.2
    # 2: k/(s(tau s+1)) : PM = 90 - atan(wc tau), analytic wc
    k, tau = 10.0, 0.1
    wc = np.sqrt((-1 + np.sqrt(1 + 4 * k * k * tau * tau)) / (2 * tau * tau))
    m = ME.margins(w, k / (s * (tau * s + 1)))
    pm, gm, fc = summ(m)
    pm_a = 90 - np.degrees(np.arctan(wc * tau))
    print(f"selftest k/(s(tau s+1)): PM {pm:.2f} (analytic {pm_a:.2f}), fc {fc * 2 * np.pi:.3f} ({wc:.3f}), GM {gm}")
    ok &= abs(pm - pm_a) < 0.2 and gm is None
    # 3: discrete model sanity: attitude-yaw L at low frequency ~ att_p*T_cl/s with T_cl -> 1 : |L| ~ 3/w
    ww = np.array([0.05])
    L = Latt_yaw(ww, 800.0)
    print(f"selftest Latt_yaw at 0.05 rad/s: |L| {abs(L[0]):.1f} (att_p/w = {3 / 0.05:.1f})")
    ok &= abs(abs(L[0]) / (3 / 0.05) - 1) < 0.1
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    rate, att = load_rate(), load_att()
    rows, notes = [], []
    n_agree = n_tot = 0
    order = [(a, r, v) for v in ("", "mo", "fwdef") for a in ("roll", "pitch", "yaw") for r in (800, 400)]
    cells = [(k, rate[k]) for k in order if k in rate] + [(k, att[k]) for k in sorted(att, key=lambda x: -x[1])]
    for key, runs in cells:
        ax, r, var = key
        fs = float(r)
        ms = [meas_from(m) for _, m in runs]
        pms = [x[0] for x in ms]
        gms = [x[1] for x in ms if x[1] is not None]
        fcs = [x[2] for x in ms]
        if ax == "yaw-att":
            f = np.geomspace(0.2, 20.0, 40)  # S107 recipe 0.2-20 Hz bins
            Lf = lambda w: Latt_yaw(w, fs, var)  # noqa: E731
        else:
            f = runs[0][0]
            Lf = lambda w: Lrate(w, fs, ax, var)  # noqa: E731
        w = 2 * np.pi * f
        mp, mg, mf = summ(ME.margins(w, Lf(w)))
        dpm = mp - np.mean(pms)
        dpm_w = max(abs(mp - p) for p in pms)
        if gms and mg is not None:
            dgm = mg - np.mean(gms)
            dgm_w = max(abs(mg - g) for g in gms)
            ok_gm = dgm_w <= 3.0
            gtxt = f"{fmt(mg)} / {fmt(dgm, 1)}"
        else:
            dgm = dgm_w = None
            ok_gm = (mg is None) == (not gms)
            gtxt = "n/a"
        ok = dpm_w <= 10.0 and ok_gm
        n_tot += 1
        n_agree += ok
        name = {"": "", "mo": " model-only", "fwdef": " fwdef"}[var]
        name = f"{ax}{r}{name}" if ax != "yaw-att" else f"att yaw {r}"
        rows.append(f"| {name} (n={len(runs)}) | {fmt(np.mean(gms)) if gms else 'n/a'} / {fmt(np.mean(pms))} / {fmt(np.mean(fcs), 2)} "
                    f"| {fmt(mg)} / {fmt(mp)} / {fmt(mf, 2)} | dGM {gtxt.split(' / ')[-1]} dB, dPM {dpm:+.1f} (worst {dpm_w:.1f}) "
                    f"| {'yes' if ok else 'NO'} |")
    hdr = ("# S165 G2: rate-loop and attitude-yaw cells at the stage-6 freeze, linear-model cross-check\n\n"
           "Script: `python3 indi_flight/bench/g2_rate_model_s165.py` (`--selftest` for the synthetic check). Model: "
           "`margins_models.L_indi` / `L_indi_yaw` (sampled-data, att path closed for the M3a rate break), attitude yaw = "
           "MC_YAW_P 3 x closed yaw rate loop / s. Parameters only from the freeze params (K 20, ACT_TC 0.033, LEAD 1 -> c = 0.66, "
           "ACT_BLD 1 s, G2_Y/G1_Y 27/205, MC_ROLL/PITCH_P 8, MC_YAW_P 3, 1 sample measurement delay, gyro/dgyro LPF 40/20 Hz) and "
           "the airframe (rotor tc 33 ms). Not tuned. Margins with `margins_est.margins` on the measured bins (rate 1-50 Hz, "
           "attitude: log grid 0.2-20 Hz, 40 bins). Measured = mean over seeds (n), delta = model - measured mean. "
           "Agree = |PM| within 10 deg and |GM| within 3 dB for every seed (xcheck.md criterion).\n\n"
           "| cell | measured GM dB / PM deg / f_c Hz | model GM / PM / f_c | delta | agree? |\n|---|---|---|---|---|\n")
    txt = hdr + "\n".join(rows) + f"\n\nAgreement: {n_agree}/{n_tot} cell groups.\n"
    open(OUT, "w").write(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
