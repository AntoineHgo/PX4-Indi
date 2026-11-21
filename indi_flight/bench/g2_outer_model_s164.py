#!/usr/bin/env python3
"""S164 minimal analytic linear model of the G2 outer-loop cells (PT0 = a_ref break, PT1 = t_c break) and its
cross-check against the S163 measured margins.  One command, no args:  python3 bench/g2_outer_model_s164.py
Writes results/g2_outer_freeze_s163/xcheck.md.  Parameters come from the freeze param file / stock PX4 defaults /
firmware source / the S162 attitude README only; nothing is tuned to the outer data (see the UNSOURCED list in xcheck.md).

Convention (as margins_est): break signal u = c + d enters the plant, y = c is returned, L = -c/u.
Hover small-signal, one axis, T = 1/88.89 Hz outer period, h = exp(-sT/2) (ZOH of the stage output):
  C(s)   = (Kvp + Kvi Ti(z)) (1 + Kp/s) + Kvd s_d(z) Fd(z)   stock PositionControl on the velocity (P-PID, I on the
           velocity error incl. v_sp = Kp (p_sp - p), D on the low-passed velocity derivative, MPC_VEL_LP = 0: no vel filter)
  lateral  plant  v/u = h Gatt(s)/s  (a = g tan(theta), theta_cmd = t_c/g), INDI increment (t_f - a_f)_lat = z_b,lat dT = 0 at hover
  vertical plant  v/u = h M(s)/s,  M = 1/(tau s+1) rotor lag, INDI increment E = F[e^{-snTs} M h (1-Bl) + Bl e^{-s(1+n)Ts} - M h]
  PT1: L1 = C v/u - E          PT0: L0 = C (v/u) / (1 - E)   (E = 0 laterally)
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import margins_est as ME  # noqa: E402
import margins_models as MM  # noqa: E402

ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results", "g2_outer_freeze_s163")
FS_OUT = 1.0 / 0.01125  # 88.89 Hz outer module rate (README of S163; vehicle_local_position update rate)
T = 1.0 / FS_OUT

# ---- parameters: (value, source)
P = dict(
    xy=dict(Kp=MM.XY_GAINS_INDI['Kp'], Kvp=MM.XY_GAINS_INDI['Kv'], Kvi=0.4, Kvd=0.2),   # MC_INDI_XY_P/VP (firmware defaults); Kvi/Kvd stock MPC_XY_VEL_I/D_ACC
    z=dict(Kp=1.0, Kvp=4.0, Kvi=2.0, Kvd=0.0),
    veld_lp=5.0,        # MPC_VELD_LP yaml default
    lpf=10.0,           # MC_INDI_POS_LPF (freeze params)
    dly=1,              # MC_INDI_POS_DLY (freeze params), module samples
    tb=0.3,             # MC_INDI_POS_TB (freeze params)
    tau_rotor=0.033,    # ASSUMPTION: MC_INDI_ACT_TC 0.033 used as the physical rotor lag (sim value not read)
)
# S162 attitude cells (README table, roll+pitch, both seeds): crossover f_c and PM of the rate-setpoint break
ATT = {800: dict(fc=1.385, pm=54.55), 400: dict(fc=1.40, pm=53.9)}  # f_c from the two-seed table (1.38-1.40 Hz), PM mean


def zi(w):
    return np.exp(-1j * w * T)


def lpf2p(w, fs, fc):
    b, a = MM.lpf2p_ba(fs, fc)
    z1 = np.exp(-1j * w / fs)
    return (b[0] + b[1] * z1 + b[2] * z1 ** 2) / (1 + a[1] * z1 + a[2] * z1 ** 2)


def alpha_f(w, fs, fc):
    al = MM.alpha_coef(fs, fc)
    return al / (1 - (1 - al) * np.exp(-1j * w / fs))


def Gatt(w, rate):
    """closed attitude loop with L_att = wa e^{-s ta}/s; wa from the measured crossover, ta from the measured PM (ASSUMPTION)."""
    wa = 2 * math.pi * ATT[rate]["fc"]
    ta = math.radians(90.0 - ATT[rate]["pm"]) / wa
    L = wa * np.exp(-1j * w * ta) / (1j * w)
    return L / (1 + L)


def Cvel(w, g, continuous=False):
    s = 1j * w
    if continuous:
        Ti = 1 / s
        Dd = s / (1 + s / (2 * math.pi * P["veld_lp"]))
    else:
        Ti = T * zi(w) / (1 - zi(w))                       # I updated after use (forward Euler, one sample)
        Dd = (1 - zi(w)) / T * alpha_f(w, FS_OUT, P["veld_lp"])
    return (g["Kvp"] + g["Kvi"] * Ti) * (1 + g["Kp"] / s) + g["Kvd"] * Dd


def Eind(w):
    """vertical INDI increment, u_f - T_act_f per unit c (g_t k_cmd = 1 at hover)."""
    s = 1j * w
    h = np.exp(-s * T / 2)
    M = 1 / (1 + P["tau_rotor"] * s)
    F = lpf2p(w, FS_OUT, P["lpf"])
    z = np.exp(-s * T)
    zn = z ** P["dly"]
    a = T / (P["tb"] + T)
    Bl = a / (1 - (1 - a) * np.exp(-s * T))
    return F * (zn * M * h * (1 - Bl) + Bl * z * zn - M * h)


def L_cell(w, pt, axis, rate, extra_delay=0.0, continuous=False):
    s = 1j * w
    h = np.exp(-s * T / 2) * np.exp(-s * extra_delay)
    if axis == "z":
        C = Cvel(w, P["z"], continuous)
        E = Eind(w)
        v = h / (1 + P["tau_rotor"] * s) / s
    else:
        C = Cvel(w, P["xy"], continuous)
        E = 0.0
        v = h * Gatt(w, rate) / s
    return C * v / (1 - E) if pt == 0 else C * v - E


def margins_at(f, **kw):
    w = 2 * np.pi * np.asarray(f, float)
    return ME.margins(w, L_cell(w, **kw))


def fmt(x, p=1):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{p}f}"


def summ(m):
    c = m["crossings"]
    c = [x for x in c if x["slope_down"]] or c
    pm = min(x["pm_deg"] for x in c) if c else None
    fc = c[0]["f_c"] if c else None
    gm = min(x["gm_db"] for x in m["phase_crossings"]) if m["phase_crossings"] else None
    return pm, gm, fc, m["top_db"]


def load():
    import json
    out = {}
    for name in sorted(os.listdir(RES)):
        if not name.endswith("_margins.json"):
            continue
        p = name.split("_")  # pt0_ax1_r800_s1
        d = json.load(open(os.path.join(RES, name)))
        out.setdefault((int(p[0][2:]), p[1], int(p[2][1:])), []).append(d)
    return out


def selftest():
    lines = []
    ok = True
    # 1) known loop L = k e^{-s tau}/s: PM = 90 - wc tau [deg], GM = 20 log10(pi/(2 tau k))
    k, tau = 5.0, 0.1
    w = np.geomspace(0.05, 200, 3000)
    m = ME.margins(w, k * np.exp(-1j * w * tau) / (1j * w))
    pm_a, gm_a = 90 - math.degrees(k * tau), 20 * math.log10(math.pi / (2 * tau * k))
    r = abs(m["margins"]["pm_deg"] - pm_a) if "margins" in m else abs(m["pm_deg"] - pm_a)
    pm_m, gm_m = m["pm_deg"], m["gm_db"]
    ok &= abs(pm_m - pm_a) < 0.1 and abs(gm_m - gm_a) < 0.1
    lines.append(f"- known loop 5 e^(-0.1 s)/s: margins PM {pm_m:.2f} (analytic {pm_a:.2f}), GM {gm_m:.2f} (analytic {gm_a:.2f})")
    # 2) identity with the existing keyed horizontal outer factor (margins_models.outer_factor, A-36/T195):
    #    1 + C(s) /s (continuous, no delay, Gatt = 1) must equal outer_factor
    w = np.geomspace(0.1, 20, 40)
    s = 1j * w
    g = P["xy"]
    Cc = Cvel(w, g, continuous=True)
    # outer_factor has P-PID with Kd F(s) added to 1, C/s form: compare 1 + Cc/s with it (Kd term: Kd s Fd / s = Kd Fd)
    ref = MM.outer_factor(w, Kp=g["Kp"], Kv=g["Kvp"], Ki=g["Kvi"], Kd=g["Kvd"], fd=P["veld_lp"])
    err = np.max(np.abs((1 + Cc / s) - ref))
    ok &= err < 1e-9
    lines.append(f"- continuous C(s)/s vs margins_models.outer_factor (T195 key): max |1 + C/s - O| = {err:.2e}")
    # 3) vertical increment vanishes at DC, small everywhere
    Ew = Eind(np.geomspace(0.01, 50, 400))
    lines.append(f"- INDI increment E: |E(0.01 rad/s)| = {abs(Ew[0]):.1e}, max |E| over 0.01-50 rad/s = {np.max(np.abs(Ew)):.3f} "
                 f"({20*math.log10(np.max(np.abs(Ew))):.1f} dB)")
    ok &= abs(Ew[0]) < 1e-3 and np.max(np.abs(Ew)) < 0.5
    # 4) attitude model reproduces the S162 numbers it was built from
    wq = np.geomspace(0.2, 20, 600) * 2 * math.pi
    for rate in (800, 400):
        wa = 2 * math.pi * ATT[rate]["fc"]
        ta = math.radians(90 - ATT[rate]["pm"]) / wa
        L = wa * np.exp(-1j * wq * ta) / (1j * wq)
        mm = ME.margins(wq, L)
        lines.append(f"- attitude L at {rate}: model f_c {mm['crossings'][0]['f_c']:.2f} Hz PM {mm['pm_deg']:.1f} (input {ATT[rate]['fc']}, {ATT[rate]['pm']})")
        ok &= abs(mm["pm_deg"] - ATT[rate]["pm"]) < 0.5
    return ok, lines

FINDINGS = """- PT0 x/y and PT1 x/y GM (model 11.5-11.7 dB vs measured about 16.3-17.3 dB, dGM -4.8 to -5.1 dB, outside 3 dB): the phase is right (model -180 crossing at 2.36 Hz at 800 Hz, measured 2.31-2.36 Hz; f_c 0.30 Hz vs 0.23-0.31 Hz) but |L| above 1 Hz falls about 10 dB faster in the measurement than in the model (at 2 Hz -15.3 vs -10.7 dB, 5 Hz -31.8 vs -24.3 dB, 8 Hz -45.1 vs -33.7 dB for PT0 ax1 r800 s1). Likely unmodelled element: the attitude/thrust response. The model lumps the S162 phase deficit into a pure delay (unity gain), whereas the real inner chain (attitude P, rate loop K = 20, rotor lag, INDI filters) is lag-like and attenuates, the gap grows with frequency as a first-order lag with a time constant of order 0.07 s would. Other candidates: the EKF velocity output (smoothing), rotor drag acting as extra velocity damping. This is a hypothesis, not tested here (the model was not refitted). Direction of the error is the safe one (model GM is lower than measured), as in A-36 for the attitude cells.
- PT1 x/y PM 800 (model 53.5 vs measured worst 59.7, d = -6.2 deg, mean larger): within 10 deg; the measured PT0 and PT1 xy differ by up to 8 deg in PM and by 0.07 Hz in f_c while the model predicts them identical (E = 0 laterally): the difference between cells is the lateral INDI increment (rotor drag, small tilt coupling), which is not modelled and is within seed spread (up to 9 deg, S163).
- z cells: PM within 10 deg (dPM -5.0 to -8.5, model lower, i.e. conservative); both model and measurement have no -180 crossing in 0.2-8 Hz, so GM is not comparable; model |L| at 8 Hz is -28.9 dB (PT0) and -12.0 dB (PT1) vs measured <= -28.2 and <= -17.8 dB. The model PT1 z is 6 dB above the measured top bin: the E term (blend/delay mismatch, vertical INDI increment) is likely overstated by the assumed rotor lag 0.033 s and unity thrust model, or the real z rotor/IMU chain has extra attenuation. The z PT1 measured phase is not stored in margins.json, so the phase-plateau check remains open (model wide-band phase crossings are listed in the information table).
- GATE reading: PM within 10 deg in all 8 rows; GM within 3 dB in 0 of 4 xy rows (dGM about -5 dB, explained above as an unmodelled attenuation of the thrust/attitude chain, model conservative), n/a (no crossing, agreement) in 4 z rows. Per the gate wording this is a difference to be explained, not yet explained by a test: it needs either the model with the real inner lag (rate loop + rotor model) or a measured attitude-to-acceleration FRF."""


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-mpc", action="store_true", help="evaluate the old MPC_XY_P / MPC_XY_VEL_P_ACC xy gains (s164 values)")
    ap.add_argument("--params", default=None, help="params file with MC_INDI_XY_P / MC_INDI_XY_VP (firmware defaults 1.2 / 3.6 when absent)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    g = MM.xy_gains(a.params, legacy_mpc=a.legacy_mpc)
    P["xy"]["Kp"], P["xy"]["Kvp"] = g["Kp"], g["Kv"]
    out = a.out or os.path.join(RES, "xcheck.md" if a.legacy_mpc else "xcheck_indi_xy.md")
    ok, st = selftest()
    meas = load()
    rows, notes = [], []
    cells = [("PT0 x/y", 0, "xy", ("ax1", "ax2")), ("PT0 z", 0, "z", ("ax3",)), ("PT1 x/y", 1, "xy", ("ax1", "ax2")), ("PT1 z", 1, "z", ("ax3",))]
    summary = []
    for name, pt, ax, axes in cells:
        for rate in (800, 400):
            ds = [d for a in axes for d in meas[(pt, a, rate)]]
            f = ds[0]["f"]
            mp = [summ(d["margins"]) for d in ds]
            pms = [x[0] for x in mp if x[0] is not None]
            gms = [x[1] for x in mp if x[1] is not None]
            fcs = [x[2] for x in mp if x[2] is not None]
            tops = [x[3] for x in mp]
            mdl = summ(margins_at(f, pt=pt, axis=("z" if ax == "z" else "xy"), rate=rate))
            wide = summ(margins_at(np.geomspace(0.05, 40, 600), pt=pt, axis=("z" if ax == "z" else "xy"), rate=rate))
            sens = summ(margins_at(f, pt=pt, axis=("z" if ax == "z" else "xy"), rate=rate, extra_delay=T))
            d_pm_w = mdl[0] - min(pms) if mdl[0] is not None else None
            d_pm_m = mdl[0] - np.mean(pms) if mdl[0] is not None else None
            if gms and mdl[1] is not None:
                d_gm = mdl[1] - min(gms)
                gv = "within 3 dB" if abs(d_gm) <= 3 else "OUT"
            elif not gms and mdl[1] is None:
                d_gm, gv = None, f"agree: no -180 crossing (model top {fmt(mdl[3])} dB vs measured {fmt(max(tops))} dB)"
            else:
                d_gm, gv = None, "OUT: crossing exists in only one of model/measurement"
            pv = "within 10 deg" if (d_pm_w is not None and abs(d_pm_w) <= 10 and abs(d_pm_m) <= 10) else "OUT"
            rows.append((name, rate, mdl, min(pms), float(np.mean(pms)), min(gms) if gms else None, float(np.mean(fcs)), d_pm_w, d_pm_m, d_gm, pv, gv, wide, sens))
    L = []
    L.append("# S164 G2 outer cells: linear-model cross-check (xcheck)\n")
    L.append("Script: `python3 indi_flight/bench/g2_outer_model_s164.py` (no args; regenerates this file). Measured: S163 `*_margins.json` "
             "(freeze plant). Model margins use the same estimator (`margins_est.margins`, spline over the measured frequency bins "
             "0.2-8 Hz), so the band is the same. Model is not tuned to these data.\n")
    L.append("## Model (one paragraph)\n")
    L.append(
        "Small-signal hover, one axis, outer period T = 11.25 ms (88.89 Hz, S163 README). Block list, value, source: "
        "(1) velocity/position controller C = (Kvp + Kvi/s)(1 + Kp/s) + Kvd s Fd, xy: " + (f"MPC_XY_P {g['Kp']}, MPC_XY_VEL_P_ACC {g['Kv']} (legacy)" if a.legacy_mpc else f"MC_INDI_XY_P {g['Kp']}, MC_INDI_XY_VP {g['Kv']}") + ", MPC_XY_VEL_I/D_ACC 0.4/0.2; z: MPC_Z_P 1.0, "
        "MPC_Z_VEL_P/I/D_ACC 4.0/2.0/0 (the freeze params file does not set MPC_*: stock yaml defaults, "
        "`multicopter_position_control_gain_params.yaml`), structure from `PositionControl.cpp` lines 130-204 (the integrator acts on v_sp - v, so "
        "the factor (1 + Kp/s) multiplies both P and I; I forward-Euler with one-sample delay, D = backward difference then first-order alpha "
        "filter at MPC_VELD_LP 5 Hz, MPC_VEL_LP 0 and notch 0 = no velocity filter, `McIndiPosControl.cpp` 715-770); (2) ZOH of the stage output "
        "e^(-sT/2) (module rate; the stage runs in the same callback as PositionControl, so no further sample of delay); "
        "(3) INDI stage in accel_only mode (`McIndiPosControl.cpp:297`): t_c = t_f + a_c - a_f, t_f = z_b (-g_t u_f), a_f = R f_b,f + g, "
        "u_f = u_meas,f + b, b = LP_tb(u_model,f - u_meas,f), all measurement filters LowPassFilter2p at MC_INDI_POS_LPF 10 Hz sampled at 88.89 Hz, "
        "measurement delay MC_INDI_POS_DLY = 1 module sample, MC_INDI_POS_TB 0.3 s (freeze params, `indi_accel_control.cpp` 238-340); "
        "lateral axes: t_f and a_f use the same attitude R, so the increment (t_f - a_f)_lat = z_b,lat (u_f g_t - T_act,f) is second order at hover and the "
        "stage is an identity a_c -> t_c (E = 0, drag not modelled); vertical: E = F[z^-n M h (1-Bl) + Bl z^-(1+n) - M h] with n = 1 and rotor lag "
        "M = 1/(0.033 s + 1) (ASSUMED equal to MC_INDI_ACT_TC), so a_up/a_c = M h/(1-E); "
        "(4) attitude/thrust response for lateral axes Gatt = L/(1+L), L = wa e^(-s ta)/s, wa = 2 pi f_c and ta from the measured S162 attitude cell "
        "(f_c 1.385/1.40 Hz, PM 54.55/53.9 deg at 800/400, mean of roll+pitch, ASSUMPTION, this is the only place data enter the model); "
        "(5) plant integrator v = a/s; the EKF velocity is taken as transparent (see unsourced list). "
        "Loops: PT0 (break at a_ref) L0 = C (v/u)/(1-E); PT1 (break at t_c) L1 = C (v/u) - E; for xy E = 0 so the model predicts PT0 = PT1.\n")
    L.append("## Self-test\n")
    L += st
    L.append(f"\nSelf-test verdict: {'PASS' if ok else 'FAIL'}\n")
    L.append("## Results (measured = both seeds, x and y pooled for xy; worst = min over runs)\n")
    L.append("| loop | rate | model PM | meas PM worst / mean | dPM worst / mean | model GM | meas GM worst | dGM | model f_c | meas f_c mean | PM verdict | GM verdict |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (name, rate, mdl, pw, pmn, gw, fcm, dpw, dpm, dgm, pv, gv, wide, sens) in rows:
        L.append(f"| {name} | {rate} | {fmt(mdl[0])} | {fmt(pw)} / {fmt(pmn)} | {fmt(dpw)} / {fmt(dpm)} | {fmt(mdl[1])} | {fmt(gw)} | {fmt(dgm)} | "
                 f"{fmt(mdl[2],2)} | {fmt(fcm,2)} | {pv} | {gv} |")
    L.append("\nInformation (not used for verdict): model margins over a wide band 0.05-40 Hz, and with one extra sample of delay (T) in the loop.\n")
    L.append("| loop | rate | wide PM / GM / f_c | +1 sample PM / GM |")
    L.append("|---|---|---|---|")
    for (name, rate, mdl, pw, pmn, gw, fcm, dpw, dpm, dgm, pv, gv, wide, sens) in rows:
        L.append(f"| {name} | {rate} | {fmt(wide[0])} / {fmt(wide[1])} / {fmt(wide[2],2)} | {fmt(sens[0])} / {fmt(sens[1])} |")
    L.append("\n## Out-of-tolerance loops: likely unmodelled element\n")
    L.append(FINDINGS)
    L.append("\n## Assumptions NOT sourced from the freeze params / firmware / a measurement\n")
    L += [
        "1. MPC_* gains are the stock yaml defaults: the freeze file does not set them (not confirmed against the flown `.params`; the per-run `.params` also carry no MPC_*).",
        "2. Rotor lag 0.033 s taken from MC_INDI_ACT_TC (the controller's belief); the sim rotor time constant was not read. Affects z only.",
        "3. Attitude closed loop = L/(1+L) with L = wa e^(-s ta)/s fitted to two numbers (f_c, PM) of the S162 attitude cell; ta is derived from that PM.",
        "4. EKF velocity treated as transparent (no lag, no GNSS 110 ms delay, no GNSS/IMU complementary-filter dynamics). Near the 0.2-0.5 Hz crossover this is the least safe assumption.",
        "5. Delay of the stage output = ZOH T/2 only; the att_control pick-up (<= 1.25 ms) and local_position publication latency are ignored. A +1 sample variant is listed as information.",
        "6. Lateral INDI increment set to zero (no rotor/body drag, no blade flapping, thrust vector error second order at hover); a_f taken to be the true specific force with no IMU lag.",
        "7. Vertical thrust model: g_t k_cmd = 1 (units of c), T_act = M c without nonlinearity (thrust ~ omega^2 vs u linear ignored); u_meas available fresh every module cycle (ESC telemetry rate not modelled).",
        "8. MC_INDI_POS_DLY counted in module (88.89 Hz) samples; filter sample rate = module rate (`McIndiPosControl.cpp` 156-169 passes the measured rate); not verified for the delay unit.",
        "9. Velocity-derivative filter is AlphaFilter with alpha = Ts/(Ts + 1/(2 pi fc)) (as in margins_models.alpha_coef, itself marked unverified).",
    ]
    txt = "\n".join(L) + "\n"
    open(out, "w").write(txt)
    for r in rows:
        print(r[0], r[1], "model PM/GM/fc", [fmt(x, 2) for x in r[2][:3]], "meas worst PM", fmt(r[3]), "dPM", fmt(r[7]), "dGM", fmt(r[9]), r[10], "|", r[11][:40])
    print("selftest", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
