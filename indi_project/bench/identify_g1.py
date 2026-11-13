#!/usr/bin/env python3
"""Identify INDI control effectiveness G1 and actuator time constant from a ULog.

Model (plan/architecture.md sec. 4-6): the measured angular acceleration
vehicle_angular_velocity.xyz_derivative equals G1 * H(A(torque_sp)) up to an
offset, where A is a first-order lag (time constant tc), H the PX4 gyro
derivative filter chain LPF2p(gyro_cutoff) -> AlphaFilter(dgyro_cutoff), and
an integer delay d in gyro samples. G1 is fitted per axis by least squares on
sample-to-sample increments (removes offsets), for a grid of tc and d; the
pair with the best R^2 is reported.

Usage: identify_g1.py LOG.ulg [LOG.ulg ...] [--fs 250] [--gyro-cutoff 40]
       [--dgyro-cutoff 20]
"""
import argparse
import json
import math

import numpy as np
from pyulog import ULog


def lpf2p(x, fs, fc):
    """PX4 math::LowPassFilter2p (src/lib/mathlib/math/filter/LowPassFilter2p.hpp)."""
    if fc <= 0:
        return x.copy()
    ohm = math.tan(math.pi * fc / fs)
    c = 1 + 2 * math.cos(math.pi / 4) * ohm + ohm * ohm
    b0 = ohm * ohm / c
    b1, b2 = 2 * b0, b0
    a1 = 2 * (ohm * ohm - 1) / c
    a2 = (1 - 2 * math.cos(math.pi / 4) * ohm + ohm * ohm) / c
    y = np.zeros_like(x)
    d1 = d2 = 0.0
    for i, xi in enumerate(x):  # direct form II, as in PX4
        d0 = xi - d1 * a1 - d2 * a2
        y[i] = d0 * b0 + d1 * b1 + d2 * b2
        d2, d1 = d1, d0
    return y


def first_order(x, dt, tau):
    """Discrete first-order lag; also PX4 AlphaFilter when tau = 1/(2 pi fc)."""
    alpha = dt / (tau + dt)
    y = np.zeros_like(x)
    acc = 0.0
    for i, xi in enumerate(x):
        acc += alpha * (xi - acc)
        y[i] = acc
    return y


def load(path):
    ulog = ULog(path, ['vehicle_angular_velocity', 'vehicle_torque_setpoint',
                       'vehicle_thrust_setpoint'])
    d = {m.name: m.data for m in ulog.data_list if m.multi_id == 0}
    av = d['vehicle_angular_velocity']
    ts = av['timestamp_sample'] if 'timestamp_sample' in av else av['timestamp']
    acc = np.column_stack([av[f'xyz_derivative[{i}]'] for i in range(3)])
    tq = d['vehicle_torque_setpoint']
    idx = np.searchsorted(tq['timestamp'], ts, side='right') - 1
    ok = idx >= 0
    torque = np.column_stack([tq[f'xyz[{i}]'] for i in range(3)])[np.clip(idx, 0, None)]
    th = d['vehicle_thrust_setpoint']
    tidx = np.clip(np.searchsorted(th['timestamp'], ts, side='right') - 1, 0, None)
    flying = ok & (-th['xyz[2]'][tidx] > 0.2)
    return ts, acc, torque, flying


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logs', nargs='+')
    ap.add_argument('--fs', type=float, default=250.0)
    ap.add_argument('--gyro-cutoff', type=float, default=40.0)
    ap.add_argument('--dgyro-cutoff', type=float, default=20.0)
    args = ap.parse_args()
    dt = 1.0 / args.fs
    data = [load(p) for p in args.logs]
    result = {}
    for axis, name in enumerate(['roll', 'pitch', 'yaw']):
        best = None
        for tc in [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.06]:
            for delay in range(0, 5):
                xs, ys = [], []
                for ts, acc, torque, flying in data:
                    u = first_order(torque[:, axis], dt, tc)
                    u = lpf2p(u, args.fs, args.gyro_cutoff)
                    u = first_order(u, dt, 1 / (2 * math.pi * args.dgyro_cutoff))
                    if delay:
                        u = np.concatenate([np.zeros(delay), u[:-delay]])
                    m = flying[1:] & flying[:-1]
                    xs.append(np.diff(u)[m])
                    ys.append(np.diff(acc[:, axis])[m])
                x, y = np.concatenate(xs), np.concatenate(ys)
                g = float(x @ y / (x @ x))
                r2 = 1 - float(np.sum((y - g * x) ** 2) / np.sum((y - y.mean()) ** 2))
                if best is None or r2 > best['r2']:
                    best = {'g1': g, 'tc': tc, 'delay_samples': delay, 'r2': r2, 'n': int(x.size)}
        result[name] = best
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
