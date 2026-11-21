#!/usr/bin/env python3
"""A-49 closing test: amplitude of the simulated vibration lines in sensor_accel (S156, D-VIB-HOOK).

Reads full-rate sensor_accel (instance 0) and esc_status from a ULog, takes a hover window, and estimates per axis the
sinusoid amplitude of the 1P line (mean rotor speed) and of the blade-pass line (NB x 1P, aliased to the sample rate)
from the band power above the local noise floor: A = sqrt(2 * (P_band - P_floor)).

Usage: vib_line_check.py LOG.ulg --t0 S --t1 S [--nb 3]   |   vib_line_check.py --selftest
"""
import argparse
import sys

import numpy as np


def alias(f, fs):
    f = f % fs
    return fs - f if f > fs / 2 else f


def band_amp(x, fs, f0, half_bw=6.0, floor_bw=(15.0, 40.0)):
    """Sinusoid amplitude at f0 from the Hann-windowed periodogram: band power minus the median floor nearby."""
    x = np.asarray(x, float) - np.mean(x)
    n = len(x)
    w = np.hanning(n)
    X = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(n, 1.0 / fs)
    psd = (np.abs(X) ** 2) / (fs * np.sum(w ** 2))  # one-sided density x 0.5 (two-sided), integrate x 2 below
    psd[1:-1] *= 2.0
    df = f[1] - f[0]
    band = np.abs(f - f0) <= half_bw
    ring = (np.abs(f - f0) >= floor_bw[0]) & (np.abs(f - f0) <= floor_bw[1])
    floor = np.median(psd[ring]) if ring.any() else 0.0
    p = max(np.sum(psd[band] - floor) * df, 0.0)
    return float(np.sqrt(2.0 * p))


def selftest():
    rng = np.random.default_rng(0)
    fs, t = 800.0, np.arange(0, 20, 1 / 800.0)
    ok = True
    for A, f0, sig in ((10.0, 159.0, 0.35), (1.0, 159.0, 0.35), (5.0, alias(477.0, fs), 0.35)):
        ph = 2 * np.pi * f0 * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)  # slow speed wander, line width ~0.1 Hz
        x = A * np.sin(ph) + rng.normal(0, sig, len(t)) + 9.81
        a = band_amp(x, fs, f0)
        good = abs(a / A - 1) < 0.03
        ok &= good
        print(f"selftest A={A} f0={f0:.1f}: est {a:.3f} {'OK' if good else 'FAIL'}")
    a0 = band_amp(rng.normal(0, 0.35, len(t)), fs, 159.0)
    good = a0 < 0.1
    ok &= good
    print(f"selftest noise only: est {a0:.3f} {'OK' if good else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?")
    ap.add_argument("--t0", type=float, help="window start, s from log start")
    ap.add_argument("--t1", type=float, help="window end, s from log start")
    ap.add_argument("--nb", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    from pyulog import ULog
    u = ULog(a.log, ["sensor_accel", "esc_status"])
    t_start = u.start_timestamp
    acc = [d for d in u.data_list if d.name == "sensor_accel" and d.multi_id == 0][0].data
    esc = [d for d in u.data_list if d.name == "esc_status"][0].data
    ts = (acc["timestamp_sample"] - t_start) * 1e-6
    m = (ts >= a.t0) & (ts <= a.t1)
    dts = np.diff(ts[m])
    fs = 1.0 / np.median(dts)
    print(f"sensor_accel samples {m.sum()}, fs {fs:.1f} Hz, dt min/max {dts.min()*1e3:.3f}/{dts.max()*1e3:.3f} ms")
    te = (esc["timestamp"] - t_start) * 1e-6
    me = (te >= a.t0) & (te <= a.t1)
    rpm = np.mean([np.abs(esc[f"esc[{i}].esc_rpm"][me]) for i in range(4)], axis=0)
    rpm = rpm[np.all([esc[f"esc[{i}].esc_rpm"][me] != 0 for i in range(4)], axis=0)]  # drop telemetry-loss zeros
    f1 = np.median(rpm) / 60.0
    fbp = alias(a.nb * f1, fs)
    print(f"mean rotor speed {np.mean(rpm):.0f} rpm (std {np.std(rpm):.0f}), 1P {f1:.1f} Hz, "
          f"blade-pass {a.nb * f1:.1f} Hz -> {fbp:.1f} Hz at fs")
    for ax in "xyz":
        x = acc[ax][m]
        X = np.abs(np.fft.rfft((x - x.mean()) * np.hanning(len(x))))
        fpk = np.fft.rfftfreq(len(x), 1.0 / fs)[np.argmax(X)]
        print(f"{ax}: spectral peak {fpk:.1f} Hz")
        print(f"{ax}: 1P {band_amp(x, fs, f1):.3f} m/s^2  BP {band_amp(x, fs, fbp):.3f} m/s^2  "
              f"std {np.std(x):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
