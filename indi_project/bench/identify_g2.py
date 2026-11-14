#!/usr/bin/env python3
"""Identify the yaw rotor-acceleration effectiveness G2 of the gz x500 plant (O-4).

Yaw model per rotor i with spin sign s_i (ccw +1, cw -1):
    Izz r_dot = sum_i s_i (k_f k_m) w_i^2 + sum_i s_i J_r' w_i_dot + d
Integrated over a window [t0, t1] this needs no differentiation of the gyro:
    dr = a * int(u1 dt) + b * du2 + c * T,   u1 = sum s_i w_i^2, u2 = sum s_i w_i
a = k_f k_m / Izz (G1 yaw per w^2), b = J_r' / Izz (G2 yaw per rad/s^2), c = constant disturbance.
The ratio b/a = J_r' / (k_f k_m) does not depend on Izz. In gz the rotor joint turns at
w / rotorVelocitySlowdownSim, so a transmitted reaction torque gives J_r' = J_rotor / 10
(x500: 2.65e-5 / 10 -> b/a = 19.4 s); b = 0 means the simulator has no G2 term.

w_i is esc_status.esc_rpm (true speed x slowdown already applied, v2 eRPM model), r is
vehicle_angular_velocity.xyz[2]. Only airborne samples are used. The logged rate is behind PX4's gyro
low-pass (IMU_GYRO_CUTOFF), which would otherwise be confounded with the G2 term: u1 and u2 go through
the same 2nd-order Butterworth (filter matching, as in INDI). The rpm notches are not replicated.

Usage: identify_g2.py [--shift-ms D] LOG.ulg [LOG.ulg ...]
--shift-ms D advances esc_rpm by D ms (compensates telemetry latency).
"""
import sys

import numpy as np
from pyulog import ULog

SPIN = np.array([1.0, 1.0, -1.0, -1.0])  # x500 model.sdf turningDirection ccw, ccw, cw, cw
RPM = 2 * np.pi / 60
H = 1e-3       # resampling grid [s]
WIN = 0.05     # window length [s]
STRIDE = 0.01  # window stride [s]


def get(ul, name):
    return [d for d in ul.data_list if d.name == name and d.multi_id == 0][0].data


def lpf2p(x, fc, fs):
    """2nd-order Butterworth low-pass, same discretisation as math::LowPassFilter2p."""
    fr = fs / fc
    ohm = np.tan(np.pi / fr)
    c = 1 + 2 * np.cos(np.pi / 4) * ohm + ohm * ohm
    b0 = ohm * ohm / c
    a1, a2 = 2 * (ohm * ohm - 1) / c, (1 - 2 * np.cos(np.pi / 4) * ohm + ohm * ohm) / c
    y = np.empty_like(x)
    d1 = d2 = x[0] / (1 + a1 + a2)
    for k, xk in enumerate(x):
        d0 = xk - d1 * a1 - d2 * a2
        y[k] = b0 * (d0 + 2 * d1 + d2)
        d2, d1 = d1, d0
    return y


def windows(path, shift):
    ul = ULog(path)
    es, av, ld = get(ul, 'esc_status'), get(ul, 'vehicle_angular_velocity'), get(ul, 'vehicle_land_detected')
    te = es['timestamp'] * 1e-6 - shift
    tg = np.arange(te[0], te[-1], H)
    w = np.stack([np.interp(tg, te, es['esc[%d].esc_rpm' % m] * RPM) for m in range(4)])
    fc = ul.initial_parameters.get('IMU_GYRO_CUTOFF', 0)
    u1 = SPIN @ (w * w)
    u2 = SPIN @ w
    if fc > 0:
        u1, u2 = lpf2p(u1, fc, 1 / H), lpf2p(u2, fc, 1 / H)
    r = np.interp(tg, av['timestamp'] * 1e-6, av['xyz[2]'])
    air = np.interp(tg, ld['timestamp'] * 1e-6, 1.0 - ld['landed'].astype(float), left=0, right=0) > 0.999
    iu1 = np.r_[0.0, np.cumsum(0.5 * (u1[1:] + u1[:-1]) * H)]
    n, s = int(round(WIN / H)), int(round(STRIDE / H))
    rows, y = [], []
    for k in range(0, len(tg) - n, s):
        if air[k:k + n + 1].all():
            rows.append([iu1[k + n] - iu1[k], u2[k + n] - u2[k], WIN])
            y.append(r[k + n] - r[k])
    return np.array(rows), np.array(y)


def fit(X, y):
    scale = np.abs(X).max(axis=0)
    beta, *_ = np.linalg.lstsq(X / scale, y, rcond=None)
    res = y - (X / scale) @ beta
    dof = max(len(y) - X.shape[1], 1)
    cov = np.linalg.inv((X / scale).T @ (X / scale)) * (res @ res) / dof
    r2 = 1 - (res @ res) / ((y - y.mean()) @ (y - y.mean()))
    return beta / scale, np.sqrt(np.diag(cov)) / scale, r2


def main():
    args = sys.argv[1:]
    shift = 0.0
    if args[0] == '--shift-ms':
        shift, args = float(args[1]) * 1e-3, args[2:]
    Xs, ys = [], []
    for p in args:
        X, y = windows(p, shift)
        Xs.append(X); ys.append(y)
    X, y = np.vstack(Xs), np.concatenate(ys)
    beta, se, r2 = fit(X, y)
    print('logs %d, shift %.1f ms, windows %d, R^2 %.4f' % (len(args), shift * 1e3, len(y), r2))
    for name, b, e in zip(['a (G1y per w^2)', 'b (G2y per rad/s^2)', 'c (rad/s^2)'], beta, se):
        print('%-20s %+.4e  se %.1e' % (name, b, e))
    print('b/a = %.2f s (expected 19.4 s if the reaction torque is transmitted at 1/10 speed, 0 if not)'
          % (beta[1] / beta[0]))
    beta0, _, r20 = fit(X[:, [0, 2]], y)
    print('without G2 term: a %+.4e, R^2 %.3f' % (beta0[0], r20))


if __name__ == '__main__':
    main()
