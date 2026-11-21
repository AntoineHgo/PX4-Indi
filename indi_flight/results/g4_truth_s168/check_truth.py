#!/usr/bin/env python3
"""S168 probe: esc_status instance 0 (eRPM model) vs instance 1 (true rotor speed) in one ulog."""
import sys
import numpy as np
from pyulog import ULog

u = ULog(sys.argv[1], ['esc_status', 'actuator_motors'])
inst = {d.multi_id: d for d in u.data_list if d.name == 'esc_status'}
print('esc_status instances:', sorted(inst))
for k, d in sorted(inst.items()):
    t = d.data['timestamp'] * 1e-6
    dt = np.diff(t)
    w = np.stack([d.data['esc[%d].esc_rpm' % i] for i in range(4)], 1).astype(float)
    m = (t > t[0] + 40) & (t < t[0] + 70)
    print('inst %d: n %d rate %.1f Hz (median dt %.5f s, max dt %.4f) rpm mean %s std %s uniq %d'
          % (k, len(t), 1 / np.median(dt), np.median(dt), dt.max(),
             np.round(w[m].mean(0)), np.round(w[m].std(0), 2), len(np.unique(w[m, 0]))))
if 0 in inst and 1 in inst:
    a, b = inst[0], inst[1]
    tb = b.data['timestamp'] * 1e-6
    ta = a.data['timestamp'] * 1e-6
    w0 = np.interp(tb, ta, a.data['esc[0].esc_rpm'].astype(float))
    w1 = b.data['esc[0].esc_rpm'].astype(float)
    m = (tb > tb[0] + 40) & (tb < tb[0] + 70)
    d = w0[m] - w1[m]
    print('motor0 inst0-inst1 in hover window: mean %.2f rpm, rms %.2f rpm, max |d| %.1f, identical frac %.3f'
          % (d.mean(), np.sqrt((d ** 2).mean()), np.abs(d).max(), np.mean(d == 0)))
    # lag estimate by cross-correlation of detrended signals (instance 0 should lag by ~1 telemetry frame)
    x = w1[m] - w1[m].mean()
    y = w0[m] - w0[m].mean()
    lags = range(-5, 11)
    c = [np.dot(x[max(0, -l):len(x) - max(0, l)], y[max(0, l):len(y) - max(0, -l)]) for l in lags]
    print('xcorr best lag (samples, inst0 after inst1 > 0):', list(lags)[int(np.argmax(c))])
