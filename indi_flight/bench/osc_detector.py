"""Sustained-oscillation detector (GATES.md section 2 shared definitions, PROPOSED thresholds).

Truth body rates p, q, r (deg/s) on a uniform grid; Hann PSD, 4 s windows, 1 s step, band 2-40 Hz.
A window is flagged on an axis when one peak has power > 20 x band median AND the rate RMS at that peak
(PSD integrated over peak +-2 bins, Hann main lobe) > 5 deg/s. Sustained = >= 3 consecutive flagged windows
whose peak frequencies are within +-10 % of the first window of the run.
"""
import numpy as np

PEAK_RATIO = 20.0
RMS_MIN_DPS = 5.0
WIN_S, STEP_S = 4.0, 1.0
BAND = (2.0, 40.0)
MIN_CONSEC = 3
FREQ_TOL = 0.10


def _uniform(t_s, x, fs):
    t_s = np.asarray(t_s, float)
    tg = np.arange(t_s[0], t_s[-1], 1.0 / fs)
    return tg, np.interp(tg, t_s, x)


def window_flag(x, fs, band=BAND):
    """x: one axis (deg/s), one window. Returns (flagged, f_peak, ratio, rms_at_peak)."""
    n = len(x)
    w = np.hanning(n)
    xd = (x - np.mean(x)) * w
    X = np.fft.rfft(xd)
    psd = 2.0 * np.abs(X) ** 2 / (fs * np.sum(w ** 2))  # one-sided, sum(psd)*df = variance
    f = np.fft.rfftfreq(n, 1.0 / fs)
    df = f[1] - f[0]
    m = (f >= band[0]) & (f <= band[1])
    pb, fb = psd[m], f[m]
    k = int(np.argmax(pb))
    ratio = pb[k] / max(np.median(pb), 1e-300)
    lo, hi = max(k - 2, 0), min(k + 3, len(pb))
    rms = float(np.sqrt(np.sum(pb[lo:hi]) * df))
    return bool(ratio > PEAK_RATIO and rms > RMS_MIN_DPS), float(fb[k]), float(ratio), rms


def detect(t_s, p, q, r, fs=800.0, win_s=WIN_S, step_s=STEP_S, band=BAND):
    """t_s seconds; p,q,r in deg/s. Returns (windows, sustained). windows: list of dicts, one per window
    (t0, flagged, axis, f_hz, ratio, rms_dps); a window is flagged if any axis is flagged (strongest axis reported)."""
    t_s = np.asarray(t_s, float)
    axes = {}
    for nm, x in (("p", p), ("q", q), ("r", r)):
        tg, axes[nm] = _uniform(t_s, np.asarray(x, float), fs)
    n, ns = int(round(win_s * fs)), int(round(step_s * fs))
    wins = []
    for i0 in range(0, len(tg) - n + 1, ns):
        best = None
        for nm, x in axes.items():
            fl, fp, ra, rm = window_flag(x[i0:i0 + n], fs, band)
            c = dict(t0=float(tg[i0]), flagged=fl, axis=nm, f_hz=fp, ratio=ra, rms_dps=rm)
            if best is None or (fl, ra) > (best["flagged"], best["ratio"]):
                best = c
        wins.append(best)
    return wins, sustained(wins)


def sustained(wins):
    run = []
    for w in wins:
        if w["flagged"] and (not run or abs(w["f_hz"] - run[0]["f_hz"]) <= FREQ_TOL * run[0]["f_hz"]):
            run.append(w)
        else:
            run = [w] if w["flagged"] else []
        if len(run) >= MIN_CONSEC:
            return True
    return False
