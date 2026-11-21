#!/usr/bin/env python3
"""Amplitude spectrum of indi_pos_status a_f[0..2] in a time window (ulog -> peak freq / amplitude).

Uses true per-sample timestamps: resamples to a uniform grid (linear interp) at fs, Hann window,
single-sided amplitude (peak amplitude of a sinusoid, coherent-gain corrected).
Usage: af_line.py flight.ulg --t0 40 --t1 50 [--at 6.84] [--fmin 2 --fmax 10]  (times: s on the px4/ulog timestamp clock, like metrics.json window)
"""
import argparse
import numpy as np


def amp_spectrum(t, x, t0, t1, fs=200.0):
    m = (t >= t0) & (t <= t1)
    t, x = t[m], x[m]
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    xg = np.interp(tg, t, x)
    xg = xg - xg.mean()
    w = np.hanning(len(xg))
    nfft = 1 << (int(np.ceil(np.log2(len(xg)))) + 2)
    X = np.fft.rfft(xg * w, nfft)
    f = np.fft.rfftfreq(nfft, 1.0 / fs)
    return f, 2.0 * np.abs(X) / w.sum()


def peak(f, a, fmin, fmax):
    k = (f >= fmin) & (f <= fmax)
    i = np.argmax(a[k])
    return f[k][i], a[k][i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ulg"); ap.add_argument("--t0", type=float, default=40.0); ap.add_argument("--t1", type=float, default=50.0)
    ap.add_argument("--at", type=float, default=6.84); ap.add_argument("--fmin", type=float, default=2.0)
    ap.add_argument("--fmax", type=float, default=10.0)
    a = ap.parse_args()
    from pyulog import ULog
    u = ULog(a.ulg, message_name_filter_list=["indi_pos_status"])
    d = u.data_list[0].data
    t = (d["timestamp"] ) / 1e6
    print(f"samples {len(t)}, mean rate {len(t) / (t[-1] - t[0]):.1f} Hz, window {a.t0}-{a.t1} s")
    for ax in (0, 1):
        x = d[f"a_f[{ax}]"]
        f, s = amp_spectrum(t, x, a.t0, a.t1)
        pf, pa = peak(f, s, a.fmin, a.fmax)
        k = (f >= a.at - 0.3) & (f <= a.at + 0.3)
        print(f"a_f[{ax}]: peak {a.fmin}-{a.fmax} Hz at {pf:.2f} Hz amp {pa:.4f} m/s2; max within +-0.3 Hz of {a.at}: {s[k].max():.4f}")


if __name__ == "__main__":
    main()
