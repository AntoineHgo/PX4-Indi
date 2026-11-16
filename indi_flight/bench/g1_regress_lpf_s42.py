#!/usr/bin/env python3
"""G1 (roll) from an M3a log, with the D-term filter applied to u as well as alpha.

angular_accel_filtered is the gyro derivative after LPF2p(dgyro_fc), so the regressor u = torque_sp must pass the
same filter (and the motor lag tau) before regressing; T86 omitted it and found a spurious 20 ms delay.
Usage: g1_regress_lpf_s42.py LOG.ulg OUT.md [dgyro_fc=20] [t0=52] [t1=82]
"""
import sys
import numpy as np
from pyulog import ULog


def lpf2p(x, fs, fc):
    # PX4 math::LowPassFilter2p (Butterworth biquad, bilinear)
    fr = fs / fc
    om = np.tan(np.pi / fr)
    c = 1 + 2 * np.cos(np.pi / 4) * om + om * om
    b0 = om * om / c
    b1, b2 = 2 * b0, b0
    a1 = 2 * (om * om - 1) / c
    a2 = (1 - 2 * np.cos(np.pi / 4) * om + om * om) / c
    y = np.zeros_like(x)
    d1 = d2 = 0.0
    for i, xi in enumerate(x):
        d0 = xi - d1 * a1 - d2 * a2
        y[i] = d0 * b0 + d1 * b1 + d2 * b2
        d2, d1 = d1, d0
    return y


def lag(x, tau, dt):
    if tau <= 0:
        return x.copy()
    a = np.exp(-dt / tau)
    y = np.zeros_like(x)
    for i in range(1, len(x)):
        y[i] = a * y[i - 1] + (1 - a) * x[i - 1]
    return y


def bandpass(x, dt, lo, hi):
    X = np.fft.rfft(x - x.mean())
    f = np.fft.rfftfreq(len(x), dt)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def main(path, out, fc=20.0, t0=52.0, t1=82.0):
    d = ULog(path).get_dataset('indi_rate_status').data
    t = d['timestamp_sample'] * 1e-6
    u_all = d['torque_sp[0]']
    a_all = d['angular_accel_filtered[0]']
    dt = float(np.median(np.diff(t)))
    rows = []
    for tau in (0.0, 0.02, 0.033, 0.04):
        for k in (0, 2, 4, 6, 8, 12):
            uf = lpf2p(lag(u_all, tau, dt), 1 / dt, fc)
            uf = np.roll(uf, k)
            w = (t >= t0) & (t <= t1)
            a = bandpass(a_all[w], dt, 2, 10)
            x = bandpass(uf[w], dt, 2, 10)
            g = float(x @ a / (x @ x))
            r2 = 1 - np.sum((a - g * x) ** 2) / np.sum(a ** 2)
            rows.append((tau, k, g, r2))
    best = max(rows, key=lambda r: r[3])
    with open(out, 'w') as fo:
        fo.write(f"# G1 roll regression with LPF2p({fc} Hz) on u (S42)\n\nLog `{path}`, window {t0}-{t1} s since boot (timestamp_sample),"
                 f" dt {dt*1e3:.3f} ms, alpha = indi_rate_status.angular_accel_filtered[0], u = torque_sp[0],"
                 " regressor = LPF2p(lag_tau(u)) delayed k samples, both band-passed 2-10 Hz.\n\n| tau [s] | k | G1 | R^2 |\n|---|---|---|---|\n")
        for r in rows:
            fo.write(f"| {r[0]} | {r[1]} | {r[2]:.1f} | {r[3]:.3f} |\n")
        fo.write(f"\nBest: tau {best[0]}, k {best[1]}, G1 {best[2]:.1f}, R^2 {best[3]:.3f}\n")
    print(best)


if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], *[float(v) for v in a[3:]])
