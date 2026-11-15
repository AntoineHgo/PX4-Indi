#!/usr/bin/env python3
"""Roll-rate RMS in the 2-4 Hz band and roll torque std inside the hover metric window, per flight.ulg.

Usage: pid_hover_mode.py RUN_DIR [RUN_DIR ...]  (each RUN_DIR holds flight.ulg and run.json)
Same discriminator as results/pid_hover_mode.md (high state 0.005-0.0075 rad/s, low 0.0006-0.0028 rad/s).
"""
import json
import sys

import numpy as np
from pyulog import ULog


def band_rms(x, t, lo, hi):
    x = x - x.mean()
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), np.mean(np.diff(t)))
    X[(f < lo) | (f > hi)] = 0
    return float(np.sqrt(np.mean(np.fft.irfft(X, len(x)) ** 2)))


def main():
    print('| run | band 2-4 Hz roll rate RMS rad/s | roll torque std | state |')
    print('|---|---|---|---|')
    for d in sys.argv[1:]:
        j = json.load(open(f'{d}/run.json'))
        u = ULog(f'{d}/flight.ulg')
        w0, w1 = j['t_window_start_us'], j['t_window_end_us']
        v = u.get_dataset('vehicle_angular_velocity').data
        m = (v['timestamp_sample'] > w0) & (v['timestamp_sample'] < w1)
        b = band_rms(v['xyz[0]'][m], v['timestamp_sample'][m] * 1e-6, 2.0, 4.0)
        q = u.get_dataset('vehicle_torque_setpoint').data
        mq = (q['timestamp'] > w0) & (q['timestamp'] < w1)
        tq = float(np.std(q['xyz[0]'][mq]))
        state = 'high' if b > 0.004 else 'low' if b < 0.0035 else '?'
        print(f'| {d} | {b:.4f} | {tq:.5f} | {state} |')


if __name__ == '__main__':
    main()
