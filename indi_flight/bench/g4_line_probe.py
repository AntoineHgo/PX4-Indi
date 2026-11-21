#!/usr/bin/env python3
"""Probe (S169): largest 20-100 Hz line in actuator_motors control[0] over a window: freq, peak/median PSD,
band RMS within +-2 Hz of the line, total 20-100 Hz RMS. Usage: g4_line_probe.py LOG T0 T1 (ulog time base, s)."""
import sys
import numpy as np
from pyulog import ULog
from scipy.signal import welch
log, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
u = ULog(log, ['actuator_motors'])
s = u.start_timestamp
for name, key in (('actuator_motors', 'control[0]'),):
    d = u.get_dataset(name).data
    t = (d['timestamp'] - s) * 1e-6
    m = (t >= t0) & (t < t1)
    fs = 1.0 / np.median(np.diff(t[m]))
    x = d[key][m] - np.mean(d[key][m])
    f, p = welch(x, fs=fs, nperseg=int(fs * 2))
    b = (f >= 20) & (f <= 100)
    i = np.argmax(p[b]); fl = f[b][i]
    df = f[1] - f[0]
    line = (f >= fl - 2) & (f <= fl + 2)
    print('%s %s fs %.1f Hz line %.2f Hz peak/median %.1f line RMS %.2e band20-100 RMS %.2e' % (
        name, key, fs, fl, p[b][i] / np.median(p[b]), np.sqrt(np.sum(p[line]) * df), np.sqrt(np.sum(p[b]) * df)))
