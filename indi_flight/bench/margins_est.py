#!/usr/bin/env python3
"""Frequency-response / stability-margin estimator for gate G2 (design/stage2_margins_s35.md sec 2-3).

Pure numpy (scipy is NOT required and not installed on the dev box).

Break-point convention (injection d added AT the break):
    x = signal AFTER the summation (what the plant sees),  x = y + d
    y = signal returned to the summation point BEFORE adding d (it carries the negative-feedback sign, y = -L x)
    => G_xd = 1/(1+L), G_yd = -L/(1+L), L = -G_yd / G_xd.
d is an exogenous instrument, so noise that is uncorrelated with d is removed from the ratio (the naive -S_yx/S_xx is
biased by the noise fed back into x).

CLI:  python3 margins_est.py log.csv --Tp 20 [--ref ref.csv] [--welch --nperseg N] [--fmin/--fmax/--per-decade]
      CSV columns: t,d,x,y  (uniform sample rate fs, taken from the median dt).  Exit 2 on lag / time-base error.
"""
import argparse
import json
import sys

import numpy as np


class TimeBaseError(ValueError):
    pass


# --------------------------------------------------------------------------------------------- excitation
def log_bins(fmin, fmax, Tp, per_decade=10, n_axes=1, axis=0):
    """Integer FFT-bin indices (f = k/Tp) log-spaced at ~per_decade per axis; axis a gets every n_axes-th unique bin,
    so the per-axis sets are disjoint (cross-axis terms separable)."""
    df = 1.0 / Tp
    n = int(np.ceil(np.log10(fmax / fmin) * per_decade * n_axes)) + 1
    f = fmin * 10.0 ** (np.arange(n) / (per_decade * n_axes))
    k = np.unique(np.round(f / df).astype(int))
    k = k[(k >= 1) & (k * df <= fmax * (1 + 0.5 * df / fmax))]
    return k[axis::n_axes]


def multisine(freqs, amps, fs, Tp, n_periods):
    """Schroeder-phase multisine, freqs must be on the 1/Tp grid. Returns t, d (n_periods*Tp seconds)."""
    freqs = np.asarray(freqs, float)
    amps = np.broadcast_to(np.asarray(amps, float), freqs.shape)
    o = np.argsort(freqs)
    freqs, amps = freqs[o], amps[o]
    if np.max(np.abs(freqs * Tp - np.round(freqs * Tp))) > 1e-6:
        raise ValueError("multisine freqs are not on the 1/Tp grid")
    p = amps ** 2 / np.sum(amps ** 2)
    # Schroeder: phi_k = -2 pi sum_{l<k} (k-l) p_l  (= -pi k(k-1)/K for equal power)
    phi = np.array([-2 * np.pi * np.sum((k - np.arange(k)) * p[:k]) for k in range(len(freqs))])
    n = int(round(fs * Tp * n_periods))
    t = np.arange(n) / fs
    d = np.zeros(n)
    for f, a, ph in zip(freqs, amps, phi):
        d += a * np.cos(2 * np.pi * f * t + ph)
    return t, d


def detect_bins(d, fs, Tp, rel=1e-3):
    """Excited bins of a logged d (bins whose period-FFT magnitude exceeds rel*max)."""
    N = int(round(fs * Tp))
    D = np.abs(np.fft.rfft(d[:N]))
    return np.where(D[1:] > rel * D.max())[0] + 1


# --------------------------------------------------------------------------------------------- helpers
def read_csv(path):
    a = np.genfromtxt(path, delimiter=",", names=True)
    return a["t"], a["d"], a["x"], a["y"]


def check_time_base(t, fs):
    """Max deviation (in samples) of the logged times from a uniform grid of rate fs."""
    t = np.asarray(t, float)
    dev = np.max(np.abs(t - (t[0] + np.arange(len(t)) / fs))) * fs
    return {"max_dev_samples": float(dev), "uniform": bool(dev <= 0.01)}


def lag_check(d_logged, d_reference):
    """Integer-sample lag of the logged injection vs the regenerated one (lag>0: logged is delayed).
    Non-zero lag is an error (ok False)."""
    a = np.asarray(d_logged, float)
    b = np.asarray(d_reference, float)
    n = min(len(a), len(b))
    a = a[:n] - a[:n].mean()
    b = b[:n] - b[:n].mean()
    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(a, nfft) * np.conj(np.fft.rfft(b, nfft)), nfft)  # c[k] = sum_m a[m+k] b[m]
    k = int(np.argmax(np.concatenate([c[nfft - n + 1:], c[:n]]))) - (n - 1)
    ok = k == 0  #BRK_lag
    return {"lag": k, "ok": ok, "error": None if ok else "injection lag of %d sample(s) between log and reference" % k}


def _crossovers_raw(f, L):
    m = np.log(np.abs(L))
    out = []
    for i in np.where(np.sign(m[:-1]) * np.sign(m[1:]) < 0)[0]:
        fr = m[i] / (m[i] - m[i + 1])
        out.append(float(np.exp(np.log(f[i]) + fr * (np.log(f[i + 1]) - np.log(f[i])))))
    return out


def _finish(f, Gxd, Gyd, g2x, g2y, Lstd, Lsem, n_avg, thr_far=0.8, thr_near=0.9, near_decade=1.0):
    L = -Gyd / Gxd  #BRK_sign
    g2 = np.minimum(g2x, g2y)
    thr = np.full(f.shape, thr_far)
    fc = _crossovers_raw(f, L) if len(f) > 1 else []
    for c in fc:  # tighter threshold within `near_decade` decades of a (raw) crossover
        thr[np.abs(np.log10(f / c)) <= near_decade] = thr_near
    acc = g2 >= thr
    rej = [{"f": float(fi), "g2": float(g)} for fi, g, a in zip(f, g2, acc) if not a]
    return {"f": f, "w": 2 * np.pi * f, "Gxd": Gxd, "Gyd": Gyd, "g2_xd": g2x, "g2_yd": g2y, "L": L,
            "L_std": Lstd, "L_sem": Lsem, "thr": thr, "accepted": acc, "rejected": rej, "fc_raw": fc,
            "n_avg": n_avg}


def _spec(D, X, Y):
    """Period-averaged spectra, rows = periods (or segments)."""
    Sdd = np.mean(np.abs(D) ** 2, 0)
    Sxd = np.mean(X * np.conj(D), 0)
    Syd = np.mean(Y * np.conj(D), 0)
    Sxx = np.mean(np.abs(X) ** 2, 0)
    Syy = np.mean(np.abs(Y) ** 2, 0)
    return Sdd, Sxd, Syd, Sxx, Syy


def _ls_phasors(t, sigs, freqs, Tp, discard):
    """Per-period least-squares phasors at the known excited freqs using the ACTUAL sample times (non-uniform ok)."""
    t0 = t[0]
    dt = np.median(np.diff(t))
    n_per = int(np.floor((t[-1] - t0 + dt) / Tp + 1e-9))
    K = len(freqs)
    out = []
    for p in range(discard, n_per):
        sel = (t >= t0 + p * Tp - 1e-9) & (t < t0 + (p + 1) * Tp - 1e-9)
        tt = t[sel] - t0
        ang = 2 * np.pi * tt[:, None] * freqs[None, :]
        # constant column: signals with a mean (e.g. z acceleration near -g) would otherwise bias every phasor
        A = np.hstack([np.cos(ang), np.sin(ang), np.ones((tt.size, 1))])
        coef = np.linalg.lstsq(A, sigs[:, sel].T, rcond=None)[0]  # (2K+1, 3)
        out.append((coef[:K] - 1j * coef[K:2 * K]).T)  # (3, K) phasors
    Z = np.array(out)  # (M, 3, K)
    return Z[:, 0], Z[:, 1], Z[:, 2]


def frf_periodic(d, x, y, fs, Tp, excited_bins, discard=1, t=None, **thr):
    """Per-period FFT (no window) at the excited bins, first `discard` periods dropped.
    If t (logged sample times) is given and is not on a uniform grid of rate fs (> 0.01 sample), the per-period
    least-squares phasor fit at the known excited frequencies using the ACTUAL times is used instead of the FFT.
    Returns dict (see _finish). L = -G_yd/G_xd; L_std = std of the per-period L across periods, L_sem = std/sqrt(M)."""
    d, x, y = (np.asarray(v, float) for v in (d, x, y))
    bins = np.asarray(excited_bins, int)
    nonuni = t is not None and not check_time_base(t, fs)["uniform"]
    if nonuni:
        f = bins / Tp
        D, X, Y = _ls_phasors(np.asarray(t, float), np.vstack([d, x, y]), f, Tp, discard)
    else:
        Nf = fs * Tp
        N = int(round(Nf))
        if abs(Nf - N) > 1e-3:
            raise TimeBaseError("fs*Tp = %.4f is not an integer: period-exact FFT impossible (use actual times t)" % Nf)
        npd = len(d) // N
        sl = lambda v: np.fft.fft(v[:npd * N].reshape(npd, N)[discard:], axis=1)[:, bins]
        D, X, Y = sl(d), sl(x), sl(y)
        f = bins / Tp
    M = D.shape[0]
    if M < 2:
        raise ValueError("need >= 2 usable periods after discard")
    Sdd, Sxd, Syd, Sxx, Syy = _spec(D, X, Y)
    g2x = np.abs(Sxd) ** 2 / (Sdd * Sxx)
    g2y = np.abs(Syd) ** 2 / (Sdd * Syy)
    Lp = -(Y * np.conj(D)) / (X * np.conj(D))
    Lstd = np.sqrt(np.sum(np.abs(Lp - Lp.mean(0)) ** 2, 0) / (M - 1))
    r = _finish(f, Sxd / Sdd, Syd / Sdd, g2x, g2y, Lstd, Lstd / np.sqrt(M), M, **thr)
    r["naive_L"] = -np.mean(Y * np.conj(X), 0) / np.mean(np.abs(X) ** 2, 0)  # -S_yx/S_xx, no instrument (diagnostic)
    r["nonuniform_path"] = bool(nonuni)
    return r


def frf_welch(d, x, y, fs, nperseg, **thr):
    """Welch fallback for non-periodic data: Hann, 50 % overlap, constant detrend. Same dict as frf_periodic."""
    d, x, y = (np.asarray(v, float) for v in (d, x, y))
    w = np.hanning(nperseg)
    step = nperseg // 2
    starts = range(0, len(d) - nperseg + 1, step)
    F = lambda v: np.array([np.fft.rfft(w * (v[s:s + nperseg] - v[s:s + nperseg].mean())) for s in starts])
    D, X, Y = F(d), F(x), F(y)
    Sdd, Sxd, Syd, Sxx, Syy = _spec(D, X, Y)
    f = np.fft.rfftfreq(nperseg, 1.0 / fs)
    k = slice(1, None)
    g2x = np.abs(Sxd) ** 2 / (Sdd * Sxx)
    g2y = np.abs(Syd) ** 2 / (Sdd * Syy)
    nan = np.full(f[k].shape, np.nan)
    return _finish(f[k], (Sxd / Sdd)[k], (Syd / Sdd)[k], g2x[k], g2y[k], nan, nan, D.shape[0], **thr)


# --------------------------------------------------------------------------------------------- margins
def _natural_spline(x, y):
    n = len(x)
    if n < 4:
        return lambda q: np.interp(q, x, y)
    h = np.diff(x)
    A = np.zeros((n, n))
    r = np.zeros(n)
    A[0, 0] = A[-1, -1] = 1.0
    for i in range(1, n - 1):
        A[i, i - 1], A[i, i], A[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        r[i] = 3 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    c = np.linalg.solve(A, r)
    b = np.diff(y) / h - h * (2 * c[:-1] + c[1:]) / 3
    dd = np.diff(c) / (3 * h)

    def ev(q):
        i = np.clip(np.searchsorted(x, q) - 1, 0, n - 2)
        s = q - x[i]
        return y[i] + b[i] * s + c[i] * s ** 2 + dd[i] * s ** 3
    return ev


def _wrap180(deg):
    r = (deg + 180.0) % 360.0 - 180.0
    return 180.0 if r <= -180.0 else r


def margins(w, L, n_dense=20000, band_limit_db=-10.0, top_rejected=False):
    """Margins from L(jw) on (accepted) bins. Cubic-spline interpolation of log|L| and unwrapped phase vs log w.
    Every |L|=1 crossing -> PM_i = angle+180 (wrapped to (-180,180]), DM_i = PM_i(rad)/w_ci;
    every -180 deg phase crossing -> GM_i = -20log10|L|. Worst (min) values returned, all crossings listed.
    band_limited if |L| at the top bin is not below band_limit_db (or the top excited bin was rejected)."""
    w = np.asarray(w, float)
    L = np.asarray(L, complex)
    o = np.argsort(w)
    w, L = w[o], L[o]
    lw = np.log(w)
    sm = _natural_spline(lw, np.log(np.abs(L)))
    sp = _natural_spline(lw, np.unwrap(np.angle(L)))
    lq = np.linspace(lw[0], lw[-1], n_dense)
    m, p = sm(lq), sp(lq)
    cross, pcross = [], []
    for i in np.where(np.sign(m[:-1]) * np.sign(m[1:]) < 0)[0]:
        fr = m[i] / (m[i] - m[i + 1])
        wc = float(np.exp(lq[i] + fr * (lq[i + 1] - lq[i])))
        ph = p[i] + fr * (p[i + 1] - p[i])
        pm = _wrap180(np.degrees(ph) + 180.0)
        cross.append({"w_c": wc, "f_c": wc / 2 / np.pi, "pm_deg": pm, "dm_s": float(np.radians(pm) / wc),
                      "slope_down": bool(m[i] > m[i + 1])})
    q = (p + np.pi) / (2 * np.pi)
    fl = np.floor(q)
    for i in np.where(fl[:-1] != fl[1:])[0]:
        fr = (max(fl[i], fl[i + 1]) - q[i]) / (q[i + 1] - q[i])
        mm = m[i] + fr * (m[i + 1] - m[i])
        wp = float(np.exp(lq[i] + fr * (lq[i + 1] - lq[i])))
        pcross.append({"w": wp, "f": wp / 2 / np.pi, "gm_db": float(-20 * mm / np.log(10))})
    S = 1.0 / np.abs(1.0 + np.exp(m + 1j * p))
    last_bin_db = float(20 * np.log10(np.abs(L[-1])))  # |L| at the highest analysed bin (not a maximum)
    bl = bool(last_bin_db >= band_limit_db or top_rejected)
    nan = float("nan")
    return {
        "pm_deg": min([c["pm_deg"] for c in cross], default=nan),  #BRK_first
        "dm_s": min([c["dm_s"] for c in cross], default=nan),
        "gm_db": min([c["gm_db"] for c in pcross], default=nan),
        "crossings": cross, "phase_crossings": pcross,
        "band_limited": bl, "last_bin_db": last_bin_db, "top_db": last_bin_db,
        "Ms": float(S.max()), "Ms_db": float(20 * np.log10(S.max())), "w_Ms": float(np.exp(lq[np.argmax(S)])),
    }


def margins_from_frf(res, **kw):
    a = res["accepted"]
    return margins(res["w"][a], res["L"][a], top_rejected=not bool(a[-1]), **kw)


# --------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--Tp", type=float, required=True, help="multisine period [s]")
    ap.add_argument("--discard", type=int, default=1)
    ap.add_argument("--ref", help="reference CSV (t,d) regenerated from the multisine params, for the lag check")
    ap.add_argument("--welch", action="store_true")
    ap.add_argument("--nperseg", type=int, help="Welch segment length in samples (default 4 periods)")
    a = ap.parse_args(argv)
    t, d, x, y = read_csv(a.csv)
    fs = 1.0 / np.median(np.diff(t))
    out = {"fs": fs}
    rc = 0
    tb = check_time_base(t, fs)
    out["time_base"] = tb
    if a.ref:
        lc = lag_check(d, np.genfromtxt(a.ref, delimiter=",", names=True)["d"])
        out["lag_check"] = lc
        rc = 2 if not lc["ok"] else rc
    try:
        if a.welch:
            res = frf_welch(d, x, y, fs, a.nperseg or int(round(4 * a.Tp * fs)))
        else:
            res = frf_periodic(d, x, y, fs, a.Tp, detect_bins(d, fs, a.Tp), a.discard, t=t)
        mg = margins_from_frf(res)
        out.update(margins=mg, n_bins=int(len(res["f"])), n_accepted=int(res["accepted"].sum()), rejected=res["rejected"])
    except (TimeBaseError, ValueError) as e:
        out["error"] = str(e)
        rc = 2
    print(json.dumps(out, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
