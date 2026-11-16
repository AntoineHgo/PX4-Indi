#!/usr/bin/env python3
"""Synthetic self-test for indi_flight/bench/margins_est.py (gate G2 estimator). No sim, no firmware.

  python3 indi_flight/bench/tests/test_margins_selftest.py      (exit 0 = pass, 1 = any failure)

Tests: 1 open-loop known answer (+1b multi-crossing), 2 closed-loop with noise (instrument vs naive, rejected bins),
3 time base (lag check, non-integer decimation by sample-and-hold).

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


def main():
    tests = [test1_open_loop, test1b_multi_crossing, test2_closed_loop, test3_timebase]
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
