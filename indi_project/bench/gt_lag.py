#!/usr/bin/env python3
"""Timing of the gz_bridge ground truth against PX4's own estimates in one ULog.

The EKF attitude follows the gyro with negligible lag, so a ground-truth attitude that
lags it by tens of ms means the ground-truth timestamps are late (gz_bridge stamps
pose_info with hrt at reception). Prints the cross-correlation lag (positive = ground
truth late) for roll, pitch, the NED velocities and the NED positions.

Usage: gt_lag.py flight.ulg
"""
import sys

import numpy as np
from pyulog import ULog


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    raise KeyError(name)


def euler(d):
    w, x, y, z = (d['q[%d]' % i] for i in range(4))
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    return roll, pitch


def lag_ms(t_ref, x_ref, t_gt, x_gt, max_lag=0.3, step=0.002):
    t0 = max(t_ref[0], t_gt[0]) + max_lag
    t1 = min(t_ref[-1], t_gt[-1]) - max_lag
    tt = np.arange(t0, t1, step)
    a = np.interp(tt, t_ref, x_ref)
    a = a - a.mean()
    best, best_c = 0.0, -np.inf
    for lag in np.arange(-max_lag, max_lag + step / 2, step):
        b = np.interp(tt + lag, t_gt, x_gt)
        b = b - b.mean()
        c = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)
        if c > best_c:
            best, best_c = lag, c
    return 1e3 * best, best_c


def main():
    ulog = ULog(sys.argv[1])
    att = topic(ulog, 'vehicle_attitude')
    att_gt = topic(ulog, 'vehicle_attitude_groundtruth')
    lpos = topic(ulog, 'vehicle_local_position')
    lpos_gt = topic(ulog, 'vehicle_local_position_groundtruth')
    ta, tg = att['timestamp'] * 1e-6, att_gt['timestamp'] * 1e-6
    tl, tlg = lpos['timestamp'] * 1e-6, lpos_gt['timestamp'] * 1e-6
    r, p = euler(att)
    rg, pg = euler(att_gt)
    rows = [('roll', ta, r, tg, rg), ('pitch', ta, p, tg, pg)]

    for k in ('vx', 'vy', 'vz', 'x', 'y', 'z'):
        rows.append((k, tl, lpos[k], tlg, lpos_gt[k]))

    dt_gt = np.diff(tg)
    print('ground-truth attitude interval: median %.1f ms, max %.1f ms' % (1e3 * np.median(dt_gt), 1e3 * dt_gt.max()))

    for name, t1, x1, t2, x2 in rows:
        lag, c = lag_ms(t1, x1, t2, x2)
        print('%-5s lag %+6.1f ms (corr %.3f)' % (name, lag, c))


if __name__ == '__main__':
    main()
