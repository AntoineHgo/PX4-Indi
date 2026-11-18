#!/usr/bin/env python3
"""Synthetic self-test for indi_flight/bench/margins_est.py (gate G2 estimator). No sim, no firmware.

  python3 indi_flight/bench/tests/test_margins_selftest.py      (exit 0 = pass, 1 = any failure)

Tests: 1 open-loop known answer (+1b multi-crossing), 2 closed-loop with noise (instrument vs naive, rejected bins),
3 time base (lag check, non-integer decimation by sample-and-hold),
4 models (margins_models.py): analytic L vs time-domain, reduction 7.4, w_n/zeta vs numeric poles. Break check G for test 4: see test4_models notes in models_T78.md.

BREAK CHECKS (run once by temporarily patching margins_est.py, then restored; each patch made the file exit 1):
  A  drop the minus in L = -G_yd/G_xd           -> FAIL test2 "(a) instrument L biased" and test3 "decimated L wrong"
  B  first |L|=1 crossing PM instead of worst   -> FAIL test1b "worst PM wrong"  (B2, same for DM: "worst DM wrong")
  C  lag_check always ok                         -> FAIL test3 "lag_check shift 1" (lag found but ok=True)
  D  ignore actual sample times (force FFT path) -> FAIL test3 "non-uniform times must route to actual-time path"
  E  PM = angle+170 instead of +180              -> FAIL test1 "margins off" and test1b "per-crossing PM/DM off"
  F  GM sign flipped                             -> FAIL test1 "margins off" and test1b "worst GM wrong"

CONVENTIONS / FINDINGS
  - scipy is not installed: the independent root solve is a local bisection (`brentq` here) on the continuous expression.
  - Test 1 discretisation: exact ZOH of 1/(s(1+sT)) (K=20, T=20 ms) x one-sample computation delay x explicit 8 ms
    delay. A ZOH is Ts/2 extra delay, so the continuous reference uses tau_eff = 8 ms + 1.5 Ts. Band 0.5-60 Hz,
    10 bins/decade, cubic-spline interpolation (linear interpolation of the phase between 26 % spaced bins is NOT
    accurate enough for DM +-0.3 ms; DM is ~50 ms so that is 0.6 %). Measured errors: see printed lines (<0.02 dB, <0.01 deg, <0.02 ms).
  - Test 1b: sampled continuous L with a 20 Hz resonance bump (3 |L|=1 crossings, first PM 80 deg, worst -89 deg).
  - Test 3b: at the held-sample jitter used here (<= 0.4 sample, common to d, x, y) the nominal-time FFT is already within
    tolerance when fs*Tp is an integer (330 Hz), so that comparison has no power; the actual-time path matches it. When fs*Tp is
    not an integer (266.67 Hz) the nominal path REFUSES (TimeBaseError). Both ways satisfy "right, or reports the error".
"""
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import margins_est as ME  # noqa: E402
import margins_models as MM  # noqa: E402

TOL_GM_DB, TOL_PM_DEG, TOL_DM_S = 1.0, 3.0, 0.3e-3
TOL_L_DB, TOL_L_DEG = 1.0, 3.0
K_GAIN, T_LAG = 20.0, 0.02
FAILS = []


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def brentq(f, a, b, n=200):
    """Independent root finder (bisection; scipy is not installed). Requires a sign change on [a, b]."""
    fa, fb = f(a), f(b)
    check(fa * fb <= 0, "no sign change in bracket")
    for _ in range(n):
        c = 0.5 * (a + b)
        fc = f(c)
        if fa * fc <= 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return 0.5 * (a + b)


def roots_scan(f, lo, hi, n=100000):
    """All roots of f on (lo, hi) (log grid scan for sign changes + bisection)."""
    g = np.exp(np.linspace(np.log(lo), np.log(hi), n))
    v = np.array([f(x) for x in g]) if n < 5000 else f(g)
    return [brentq(f, g[i], g[i + 1]) for i in np.where(np.sign(v[:-1]) * np.sign(v[1:]) < 0)[0]]


# ---------------------------------------------------------------- plants / loops
def Pz_zoh(z, Ts, T=T_LAG):
    """Exact ZOH discretisation of 1/(s(1+sT)): states [theta, v]; theta[k]=Pz(z) u[k]."""
    a = np.exp(-Ts / T)
    a12, b1, b2 = T * (1 - a), Ts - T * (1 - a), 1 - a
    return (b1 + a12 * b2 / (z - a)) / (z - 1)


def L_discrete(w, Ts, tau, K=K_GAIN):
    """Discretised loop: ZOH plant, one-sample computation delay, explicit extra continuous delay tau.
    (A ZOH is an extra Ts/2 delay, so the continuous reference below uses tau_eff = tau + 1.5 Ts.)"""
    z = np.exp(1j * w * Ts)
    return K * Pz_zoh(z, Ts) * z ** -1 * np.exp(-1j * w * tau)


def L_cont(w, tau_eff, K=K_GAIN, T=T_LAG):
    return K * np.exp(-1j * w * tau_eff) / (1j * w * (1 + 1j * w * T))


def analytic_simple(tau_eff, K=K_GAIN, T=T_LAG):
    """GM, PM, DM of K e^{-s tau}/(s(1+sT)) by an independent root solve on the continuous expression."""
    wc = brentq(lambda w: abs(L_cont(w, tau_eff, K, T)) - 1.0, 0.5, 1e3)
    pm = 90.0 - math.degrees(math.atan(wc * T)) - math.degrees(wc * tau_eff)
    w180 = brentq(lambda w: math.atan(w * T) + w * tau_eff - math.pi / 2, 1.0, 1e4)
    gm = -20 * math.log10(abs(L_cont(w180, tau_eff, K, T)))
    return gm, pm, math.radians(pm) / wc, wc, w180


# ---------------------------------------------------------------- test 1
def test1_open_loop():
    tau = 0.008
    Tp = 20.0
    for fs in (800.0, 400.0, 266.67):
        Ts = 1.0 / fs
        f = ME.log_bins(0.5, 60.0, Tp, 10) / Tp
        w = 2 * np.pi * f
        m = ME.margins(w, L_discrete(w, Ts, tau))
        gm, pm, dm, wc, w180 = analytic_simple(tau + 1.5 * Ts)
        e = (m["gm_db"] - gm, m["pm_deg"] - pm, m["dm_s"] - dm)
        print("  T1 fs=%7.2f ref GM %.2f dB PM %.2f deg DM %.2f ms (fc %.2f Hz) | err GM %+.3f dB PM %+.3f deg DM %+.4f ms"
              % (fs, gm, pm, dm * 1e3, wc / 2 / math.pi, e[0], e[1], e[2] * 1e3))
        check(45 <= pm <= 70, "test design: PM %.1f outside 45-70" % pm)
        check(abs(e[0]) <= TOL_GM_DB and abs(e[1]) <= TOL_PM_DEG and abs(e[2]) <= TOL_DM_S, "margins off at fs=%g" % fs)
        check(len(m["crossings"]) == 1 and not m["band_limited"], "crossing count / band-limited flag")


def test1b_multi_crossing():
    """Loop with a resonance bump that lifts |L| above 1 again: 3 crossings; the WORST must be reported, not the first."""
    tau, w0, zn, zd = 0.008, 2 * np.pi * 20.0, 1.2, 0.04
    Lc = lambda w: L_cont(w, tau) * (w0 ** 2 - w ** 2 + 2j * zn * w0 * w) / (w0 ** 2 - w ** 2 + 2j * zd * w0 * w)
    Tp = 20.0
    f = ME.log_bins(0.5, 60.0, Tp, 120) / Tp
    w = 2 * np.pi * f
    m = ME.margins(w, Lc(w))
    wcs = roots_scan(lambda x: np.abs(Lc(x)) - 1.0, w[0], w[-1])
    pms = [ME._wrap180(math.degrees(np.angle(Lc(x))) + 180.0) for x in wcs]
    dms = [math.radians(p) / x for p, x in zip(pms, wcs)]
    w180 = roots_scan(lambda x: np.imag(Lc(x)), w[0], w[-1])
    gms = [-20 * math.log10(abs(Lc(x))) for x in w180 if Lc(x).real < 0]
    print("  T1b analytic: crossings f=%s PM=%s deg DM=%s ms GM=%s dB" % (
        np.round(np.array(wcs) / 2 / np.pi, 2), np.round(pms, 1), np.round(np.array(dms) * 1e3, 2), np.round(gms, 1)))
    print("  T1b estimator: n_cross=%d PM %.2f DM %.2f ms GM %.2f dB" % (
        len(m["crossings"]), m["pm_deg"], m["dm_s"] * 1e3, m["gm_db"]))
    check(len(wcs) >= 3, "test design: need >= 3 |L|=1 crossings, got %d" % len(wcs))
    check(abs(pms[0] - min(pms)) > 2 * TOL_PM_DEG, "test design: first crossing must differ from the worst by > 6 deg")
    check(len(m["crossings"]) == len(wcs), "estimator crossing count %d != %d" % (len(m["crossings"]), len(wcs)))
    for c, p, dmi in zip(m["crossings"], pms, dms):
        check(abs(c["pm_deg"] - p) <= TOL_PM_DEG and abs(c["dm_s"] - dmi) <= TOL_DM_S, "per-crossing PM/DM off")
    check(abs(m["pm_deg"] - min(pms)) <= TOL_PM_DEG, "worst PM wrong")
    check(abs(m["dm_s"] - min(dms)) <= TOL_DM_S, "worst DM wrong")
    if gms:
        check(abs(m["gm_db"] - min(gms)) <= TOL_GM_DB, "worst GM wrong")
    else:
        check(math.isnan(m["gm_db"]), "GM should be nan")


# ---------------------------------------------------------------- closed-loop simulation (tests 2, 3)
def simulate_loop(d, fs, K=K_GAIN, T=T_LAG, sig_m=0.01, sig_w=0.02, seed=1):
    """x = u = d + c, y = c = -K m[k-1] (one-sample computation delay), m = theta + white noise, process noise on v.
    True loop: L(z) = K z^-1 Pz(z)."""
    Ts = 1.0 / fs
    a = math.exp(-Ts / T)
    a12, b1, b2 = T * (1 - a), Ts - T * (1 - a), 1 - a
    rng = np.random.default_rng(seed)
    nm = rng.normal(0, sig_m, len(d))
    nw = rng.normal(0, sig_w, len(d))
    n = len(d)
    x, y = np.zeros(n), np.zeros(n)
    th = v = mprev = 0.0
    for k in range(n):
        c = -K * mprev
        u = d[k] + c
        y[k], x[k] = c, u
        mprev = th + nm[k]
        th, v = th + a12 * v + b1 * u, a * v + b2 * u + nw[k]
    return x, y


_SIM = {}


def sim_data():
    if "d" in _SIM:
        return _SIM
    fs, Tp, nper = 800.0, 10.0, 31
    bins = ME.log_bins(0.5, 30.0, Tp, 10)
    f = bins / Tp
    amp = 0.15 * np.maximum(1.0, (f / 3.0) ** 2.5)  # boosted at HF where |L| (and the y SNR) is small
    grp = np.arange(len(f)) % 4  # 0,2 strong; 1 weak (x0.001); 3 medium (x0.05)
    amp = amp * np.where(grp == 1, 1e-3, np.where(grp == 3, 0.05, 1.0))
    t, d = ME.multisine(f, amp, fs, Tp, nper)
    x, y = simulate_loop(d, fs)
    _SIM.update(fs=fs, Tp=Tp, nper=nper, bins=bins, f=f, grp=grp, t=t, d=d, x=x, y=y)
    return _SIM


def L_true_closed(f, fs):
    Ts = 1.0 / fs
    z = np.exp(2j * np.pi * f * Ts)
    return K_GAIN * Pz_zoh(z, Ts) / z


def errs(Lest, Ltrue):
    r = Lest / Ltrue
    return 20 * np.log10(np.abs(r)), np.degrees(np.angle(r))


# ---------------------------------------------------------------- test 2
def test2_closed_loop():
    S = sim_data()
    with tempfile.TemporaryDirectory() as td:  # same CSV format / reader as the bench logs
        p = os.path.join(td, "log.csv")
        np.savetxt(p, np.column_stack([S["t"], S["d"], S["x"], S["y"]]), delimiter=",", header="t,d,x,y",
                   comments="", fmt="%.10g")
        t, d, x, y = ME.read_csv(p)
    fs = 1.0 / np.median(np.diff(t))
    res = ME.frf_periodic(d, x, y, fs, S["Tp"], S["bins"], discard=1, t=t)
    Lt = L_true_closed(res["f"], fs)
    edb, edg = errs(res["L"], Lt)
    ndb, ndg = errs(res["naive_L"], Lt)
    acc, g2 = res["accepted"], np.minimum(res["g2_xd"], res["g2_yd"])
    grp = S["grp"]
    print("  T2 bins %d accepted %d (groups strong/weak/medium accepted: %s)" % (
        len(acc), acc.sum(), [int(acc[grp == g].sum()) for g in (0, 1, 3)]))
    print("  T2 per-bin min(g2) by freq: " + " ".join("%.1f:%.2f%s" % (a, b, "" if c else "x") for a, b, c in zip(res["f"], g2, acc)))
    print("  T2 instrument on accepted: max |err| %.3f dB %.3f deg" % (np.abs(edb[acc]).max(), np.abs(edg[acc]).max()))
    bad = (np.abs(ndb) > TOL_L_DB) | (np.abs(ndg) > TOL_L_DEG)
    print("  T2 naive -Syx/Sxx: %d/%d bins outside tolerance, max %.1f dB %.1f deg (%d of them rejected, %d accepted)" % (
        bad.sum(), len(bad), np.abs(ndb).max(), np.abs(ndg).max(), (bad & ~acc).sum(), (bad & acc).sum()))
    check(acc.sum() >= len(acc) // 3, "too few accepted bins")
    check(np.all(np.abs(edb[acc]) <= TOL_L_DB) and np.all(np.abs(edg[acc]) <= TOL_L_DEG), "(a) instrument L biased")
    check((bad & ~acc).sum() >= 3, "(b) naive estimator not biased at low-SNR bins: test has no power")
    check(np.abs(ndb[~acc]).max() > 3 * TOL_L_DB, "(b) naive bias too small at rejected bins")
    check(not acc[grp == 1].any(), "(c) tiny-amplitude bins were not rejected")
    check(np.all(g2[~acc] < res["thr"][~acc]) and np.all(g2[acc] >= res["thr"][acc]), "(c) acceptance != coherence rule")
    check(np.all(g2[grp == 1] < 0.8), "(c) tiny-amplitude bins should have low coherence")
    check(len(res["rejected"]) == (~acc).sum(), "(c) rejected list mismatch")
    # the rejected bins whose instrument estimate is outside tolerance are all in the rejected set
    outside = (np.abs(edb) > TOL_L_DB) | (np.abs(edg) > TOL_L_DEG)
    check(not (outside & acc).any(), "(c) a bad bin slipped through the coherence gate")
    # Welch fallback on the same (periodic) data: within tolerance on its own accepted bins near the true L
    wr = ME.frf_welch(d, x, y, fs, int(4 * S["Tp"] * fs))
    sel = wr["accepted"] & (wr["f"] > 0.4) & (wr["f"] < 10)
    wdb, wdg = errs(wr["L"], L_true_closed(wr["f"], fs))
    print("  T2 Welch fallback: %d accepted bins in 0.4-10 Hz, max err %.2f dB %.2f deg" % (
        sel.sum(), np.abs(wdb[sel]).max(), np.abs(wdg[sel]).max()))
    check(sel.sum() >= 5 and np.all(np.abs(wdb[sel]) <= 2 * TOL_L_DB) and np.all(np.abs(wdg[sel]) <= 2 * TOL_L_DEG),
          "Welch fallback off")


# ---------------------------------------------------------------- test 3
def test3_timebase():
    S = sim_data()
    d_ref = S["d"]
    for sh, exp in ((0, 0), (1, 1), (-1, -1), (5, 5)):
        r = ME.lag_check(np.roll(d_ref, sh), d_ref)
        check(r["lag"] == exp and r["ok"] == (exp == 0), "lag_check shift %d -> %r" % (sh, r))
    print("  T3a lag_check: shift 0 ok; shifts +1,-1,+5 flagged with the right lag")

    fs0, Tp = S["fs"], S["Tp"]
    t_end = len(d_ref) / fs0
    for fs2 in (330.0, 266.67):
        k = np.arange(int((t_end - 1.0) * fs2))
        idx = np.floor(k / fs2 * fs0 + 1e-9).astype(int)  # latest 800 Hz sample at each tick (sample-and-hold)
        t_act = idx / fs0
        dd, xx, yy = d_ref[idx], S["x"][idx], S["y"][idx]
        tb = ME.check_time_base(t_act, fs2)
        check(not tb["uniform"], "actual-time grid should be non-uniform at fs2=%g" % fs2)
        # (i) nominal-uniform-time assumption
        try:
            rn = ME.frf_periodic(dd, xx, yy, fs2, Tp, S["bins"], 1)
            en = errs(rn["L"], L_true_closed(rn["f"], fs0))
            msg = "naive uniform FFT: max |err| %.2f dB %.2f deg on accepted" % (
                np.abs(en[0][rn["accepted"]]).max(), np.abs(en[1][rn["accepted"]]).max())
        except ME.TimeBaseError as e:
            msg = "naive uniform FFT refused (TimeBaseError: fs*Tp non-integer)"
            check(fs2 == 266.67, "unexpected TimeBaseError at %g" % fs2)
        # (ii) with the actual sample times
        ra = ME.frf_periodic(dd, xx, yy, fs2, Tp, S["bins"], 1, t=t_act)
        edb, edg = errs(ra["L"], L_true_closed(ra["f"], fs0))
        acc = ra["accepted"]
        print("  T3b fs2=%.2f (max time dev %.2f samples): %s | actual-time LS fit: %d accepted, max err %.3f dB %.3f deg"
              % (fs2, tb["max_dev_samples"], msg, acc.sum(), np.abs(edb[acc]).max(), np.abs(edg[acc]).max()))
        check(ra["nonuniform_path"], "non-uniform times must route to the actual-time path")
        check(acc.sum() >= len(acc) // 3, "too few accepted bins after decimation")
        check(np.all(np.abs(edb[acc]) <= TOL_L_DB) and np.all(np.abs(edg[acc]) <= TOL_L_DEG),
              "decimated L wrong with actual times at fs2=%g" % fs2)


# ---------------------------------------------------------------- test 4 (model vs time-domain simulation, margins_models.py)
def _F_cont(s, fc=40.0):
    wc = 2 * math.pi * fc
    return 1.0 / (1.0 + math.sqrt(2.0) * s / wc + (s / wc) ** 2)


def _expected_reduction_cont(w, fs, eta, K=20.0, tau=0.033):
    """eta (K/s) F_w A_r with A_r = e^{-sT/2}/(1 + s tau) (ZOH half-sample delay), built independently of margins_models."""
    s = 1j * w
    return eta * K / s * _F_cont(s) * np.exp(-s / fs / 2) / (1 + s * tau)


def _expected_reduction_z(w, fs, eta, K=20.0, tau=0.033):
    """Sampled-data version: K F(z) * eta * [tau(1-a) A0 + T - tau(1-a)]/(z-1) with A0 = (1-a)/(z-a) (the plant w[k]/u)."""
    T = 1.0 / fs
    z = np.exp(1j * w * T)
    a = math.exp(-T / tau)
    c1 = tau * (1 - a)
    b, aa = MM.lpf2p_ba(fs, 40.0)
    F = (b[0] + b[1] / z + b[2] / z ** 2) / (aa[0] + aa[1] / z + aa[2] / z ** 2)
    return K * F * eta * (c1 * (1 - a) / (z - a) + T - c1) / (z - 1)


def test4_models():
    # (a) analytic L vs time-domain-estimated L, excited bins up to 0.4 fs
    cfgs = [("INDI model-only n=0 (g 1.2, eta 0.8, d_m 2)", "indi", dict(meas=False, n=0, g=1.2, eta=0.8, d_m=2)),
            ("INDI meas+blend Tb .1 n=1 eta .5 (lat 1)", "indi", dict(meas=True, n=1, Tb=0.1, eta=0.5, lat=1)),
            ("PID roll gains (eta 0.9)", "pid", dict(eta=0.9))]
    for fs in (800.0, 400.0):
        for name, ctrl, kw in cfgs:
            td = MM.L_timedomain(fs, ctrl, **kw)
            w = 2 * np.pi * td["f"]
            La = (MM.L_indi if ctrl == "indi" else MM.L_pid)(w, fs, **kw)
            edb, edg = errs(td["L"], La)
            print("  T4a fs=%3.0f %-45s bins %d (to %.0f Hz) accepted %d  max err %.4f dB %.4f deg" % (
                fs, name, len(w), td["f"][-1], td["accepted"].sum(), np.abs(edb).max(), np.abs(edg).max()))
            check(td["f"][-1] >= 0.38 * fs and td["accepted"].all(), "T4a bins/coherence %s fs=%g" % (name, fs))
            check(np.abs(edb).max() <= 0.5 and np.abs(edg).max() <= 3.0, "T4a model != time domain: %s fs=%g" % (name, fs))
    # (b) reduction 7.4: n=0, model chain == plant chain (tau_m = tau_r, d_m = lat = 0), model chain knows eta (eta_m = eta)
    f = np.geomspace(0.1, 150.0, 400)
    w = 2 * np.pi * f
    worst = 0.0
    for fs in (800.0, 400.0):
        for eta in (1.0, 0.7, 0.4):
            ref = _expected_reduction_cont(w, fs, eta)
            for Tb in (0.0, 0.03, 0.1, 1.0):
                for meas in (True, False):
                    if not meas and Tb != 0.0:
                        continue
                    L = MM.L_indi_cont(w, fs, eta=eta, Tb=Tb, n=0, tau_m=0.033, tau_r=0.033, d_m=0, meas=meas, eta_m=eta)
                    worst = max(worst, np.max(np.abs(L - ref) / np.abs(ref)))
    print("  T4b continuous reduction eta(K/s)F_w A_r (n=0, A_m=A_r, eta_m=eta): max rel err %.2e" % worst)
    check(worst <= 1e-9, "T4b continuous reduction off: %.2e" % worst)
    lit = np.max(np.abs(MM.L_indi_cont(w, 800.0, eta=0.5, Tb=0.1, n=0, tau_m=0.033, meas=True) - _expected_reduction_cont(w, 800.0, 0.5))
                 / np.abs(_expected_reduction_cont(w, 800.0, 0.5)))
    print("  T4b literal 7.4 (A_m = A_r, eta_m = 1, eta = 0.5) leaves a rel residual up to %.2f: the model chain must know eta" % lit)
    check(lit > 0.1, "T4b: with eta_m=1 and eta=0.5 the reduction should NOT hold")
    # sampled-data: the reduction is NOT exact (a_f is the backward-difference average of the torque over [k-1,k], the
    # sampled model/measured torque is taken at k): the residual must vanish first order in T
    res = []
    for fs in (400.0, 800.0, 1600.0):
        fl = np.geomspace(0.5, 10.0, 60)
        wl = 2 * np.pi * fl
        refz = _expected_reduction_z(wl, fs, 0.6)
        Lm = MM.L_indi(wl, fs, eta=0.6, Tb=0.1, n=0, tau_m=0.033, meas=True, eta_m=0.6)
        res.append(np.max(np.abs(Lm - refz) / np.abs(refz)))
    print("  T4b sampled-data residual (model path, 0.5-10 Hz) at 400/800/1600 Hz: %s (first order in T)" % np.array2string(np.array(res), precision=4))
    check(res[0] / res[1] > 1.6 and res[1] / res[2] > 1.6, "T4b sampled residual not O(T)")
    # (c) w_n / zeta of the polynomial vs numeric dominant closed-loop pole of the low-frequency L
    for eta in (0.25, 0.5, 0.75):
        for Tb in (0.03, 0.1, 0.3, 1.0):
            pl = MM.a1_poly(eta, Tb)
            _, pn = MM.lowfreq_pole(eta, Tb)
            err = abs(pn - pl["slow"]) / abs(pl["slow"])
            msg = "eta %.2f Tb %.2f: poly w_n %.2f zeta %.2f slow %s | numeric %s | rel diff %.2e" % (
                eta, Tb, pl["wn"], pl["zeta"], np.round(pl["slow"], 3), np.round(pn, 3), err)
            if pl["zeta"] < 1.0:
                wn_n, z_n = abs(pn), -pn.real / abs(pn)
                msg += " | numeric w_n %.2f zeta %.2f" % (wn_n, z_n)
                check(abs(wn_n - pl["wn"]) / pl["wn"] < 0.05 and abs(z_n - pl["zeta"]) / pl["zeta"] < 0.05, "T4c w_n/zeta " + msg)
            check(err < 0.05, "T4c pole " + msg)
            print("  T4c " + msg)


def test5_sp_lead():
    """A-34 / S78: setpoint-path lead option of MM.L_indi. (a) legacy defaults unchanged, (b) the lead term equals
    att_p cl D(z) T z^-1/(1-z^-1) Pn with D from the firmware recursion (filtered backward difference, kSetpointLeadTc)
    run sample by sample on a sine, (c) sp_lead False removes exactly that term, (d) lead raises |L| at 1-5 Hz."""
    fs, T = 800.0, 1.0 / 800.0
    f = np.array([1.0, 2.5, 5.0, 10.0])
    w = 2 * np.pi * f
    base = dict(MM.HEAD_FLIGHT)
    L0 = MM.L_indi(w, fs)
    check(np.allclose(L0, MM.L_indi(w, fs, fb_lead=0.0, att_p=0.0, sp_lead=False)), "T5a legacy defaults changed")
    Lh = MM.L_indi(w, fs, **base)
    Ln = MM.L_indi(w, fs, **dict(base, sp_lead=False))
    # (b) D(z) by the firmware recursion on sin(w k T)
    FW_SP_LEAD_TC = 0.01  # indi_rate_control.hpp kSetpointLeadTc, literal on purpose (second key S78)
    check(MM.SP_LEAD_TC == FW_SP_LEAD_TC, "T5b model Tc %s != firmware %s" % (MM.SP_LEAD_TC, FW_SP_LEAD_TC))
    als = T / (FW_SP_LEAD_TC + T)
    for i, wi in enumerate(w):
        n = int(round(fs / f[i] * 40))
        k = np.arange(n)
        sp = np.sin(wi * k * T)
        dot, prev, out = 0.0, 0.0, np.zeros(n)
        for j in range(n):
            raw = (sp[j] - prev) / T
            dot += als * (raw - dot)
            prev = sp[j]
            out[j] = dot
        sl = slice(n // 2, n)  # steady state, whole periods (n/2 = 20 periods)
        Dnum = 2j * np.mean(out[sl] * np.exp(-1j * wi * k[sl] * T))  # out = Im(D e^{jwkT}) -> D
        zi = np.exp(-1j * wi * T)
        Dan = als / (1.0 - (1.0 - als) * zi) * (1.0 - zi) / T
        check(abs(Dnum - Dan) / abs(Dan) < 0.01, "T5b D(z) %.1f Hz: sim %s analytic %s" % (f[i], Dnum, Dan))
    # (c) difference = cl D att_p z^-lat T z^-1/(1-z^-1) Pn ; Pn recovered from the att_p = 0 loop is not separable, so rebuild
    zi = np.exp(-1j * w * T)
    L_a0 = MM.L_indi(w, fs, **dict(base, att_p=0.0))
    Ln_minus = Ln - L_a0  # attitude term without sp lead = K att_p z^-lat T z^-1/(1-z^-1) Pn
    Lh_minus = Lh - L_a0
    D = als / (1.0 - (1.0 - als) * zi) * (1.0 - zi) / T
    ratio = Lh_minus / Ln_minus
    K_eff = base.get("K", MM.INDI_DEF["K"])
    check(np.allclose(ratio, 1.0 + base["fb_lead"] * D / K_eff),
          "T5c lead ratio wrong")
    # (d)
    sel = f <= 5.0
    check(np.all(abs(Lh[sel]) > abs(Ln[sel])), "T5d lead must raise |L| at 1-5 Hz")
    print("  T5 D(z) sim vs analytic ok, ratio (K + c D)/K ok, |L| gain %s dB" % np.round(20 * np.log10(abs(Lh) / abs(Ln)), 2))


def test6_yaw_model():
    """S107: MM.L_indi_yaw against its analytic limits (no att path, c = 0, model path, near-ideal lags and filters):
    (a) matched spin-up (ts_fw = ts_true): the (1 + ts s) of the plant cancels the Dz of the law, L -> K / s e^{-s 1.5 T}
    (pure integrator plus ZOH and one-sample delay); (b) fw G2 = 0 with a true spin-up ts: L -> K (1 + ts s) / s e^{-s 1.5 T} + ts s;
    (c) Dz recursion: matched case is independent of ts."""
    fs, T = 800.0, 1.0 / 800.0
    f = np.array([0.1, 0.2, 0.4])
    w = 2 * np.pi * f
    base = dict(path="model", tau_r=1e-6, tau_m=1e-6, gyro_fc=350.0, dgyro_fc=350.0, fb_lead=0.0, att_p=0.0, K=10.0)
    for ts in (0.0, 0.1317):
        L = MM.L_indi_yaw(w, fs, **dict(base, ts_fw=ts, ts_true=ts))
        ref = 10.0 / (1j * w) * np.exp(-1j * w * 1.5 * T)
        check(np.allclose(abs(L), abs(ref), rtol=0.01), "T6a |L| ts %g: %s vs %s" % (ts, abs(L), abs(ref)))
        check(np.allclose(np.angle(L / ref, deg=True), 0.0, atol=1.0), "T6a phase ts %g: %s" % (ts, np.angle(L / ref, deg=True)))
    ts = 0.1317
    w2 = 2 * np.pi * np.array([0.5, 1.0])
    L = MM.L_indi_yaw(w2, fs, **dict(base, ts_fw=0.0, ts_true=ts))
    # L = K (1 + ts s)/s e^{-1.5 s T} + [(1 + ts s) a_f term - t_f term] = + ts s (acceleration feedback sees the spin-up, t_f does not)
    ref = 10.0 * (1 + 1j * w2 * ts) / (1j * w2) * np.exp(-1j * w2 * 1.5 * T) + 1j * w2 * ts
    check(np.allclose(abs(L), abs(ref), rtol=0.02), "T6b |L| %s vs %s" % (abs(L), abs(ref)))
    check(np.allclose(np.angle(L / ref, deg=True), 0.0, atol=2.0), "T6b phase %s" % np.angle(L / ref, deg=True))
    print("  T6 yaw L: integrator + 1.5 T delay (matched and unmatched spin-up) within 1 %% and 1 deg, |L| %s" % np.round(abs(L), 3))
    # roll/pitch untouched by the yaw addition
    m = MM.margins_of(MM.L_indi, 800.0, **MM.HEAD_FLIGHT)
    check(abs(m["pm_deg"] - 66.7) < 0.05 and abs(m["gm_db"] - 14.93) < 0.01, "T6c roll HEAD_FLIGHT changed: %s %s" % (m["pm_deg"], m["gm_db"]))


def main():
    tests = [test1_open_loop, test1b_multi_crossing, test2_closed_loop, test3_timebase, test4_models, test5_sp_lead, test6_yaw_model]
    for tfn in tests:
        print(tfn.__name__)
        try:
            tfn()
            print("  PASS")
        except Exception as e:  # noqa: BLE001 (a crash is a failure too)
            FAILS.append(tfn.__name__)
            print("  FAIL: %s" % e)
    print("ALL PASS" if not FAILS else "FAILED: %s" % ", ".join(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
