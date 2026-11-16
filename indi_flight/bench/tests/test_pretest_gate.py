#!/usr/bin/env python3
"""Self-test of pretest_gate.py on synthetic signals with known answers."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pretest_gate as pg  # noqa: E402

rng = np.random.default_rng(1)
fs = 800.0
t = np.arange(0, 30, 1 / fs)
ok = True


def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok &= bool(cond)


# 17 Hz limit cycle of amplitude 0.2 rad/s on pitch over a slow 0.5 rad/s drift: RMS 0.2/sqrt(2), drift removed
xyz = np.zeros((t.size, 3))
xyz[:, 0] = 0.005 * rng.standard_normal(t.size)
xyz[:, 1] = 0.2 * np.sin(2 * np.pi * 17 * t) + 0.5 * np.sin(2 * np.pi * 0.05 * t)
rms = pg.rate_rms(t, xyz)
check('limit cycle RMS 0.1414', abs(rms[1] - 0.2 / np.sqrt(2)) < 0.005)
check('white noise RMS 0.005', abs(rms[0] - 0.005) < 0.0005)
check('zero axis RMS 0', rms[2] < 1e-12)
check('limit cycle fails rate', any('axis 1' in f for f in pg.verdict(rms, 0.0, 1.0)))

# irregular sampling: drop 30 % of samples, answer unchanged
keep = rng.random(t.size) > 0.3
rms_i = pg.rate_rms(t[keep], xyz[keep])
check('irregular sampling', abs(rms_i[1] - rms[1]) < 0.005)

# motor pin: 3 % of rows have one motor at 0
ctrl = np.full((10000, 4), 0.137)
ctrl[:300, 2] = 0.0
check('pin fraction 0.03', abs(pg.pin_fraction(ctrl) - 0.03) < 1e-12)
check('pin fails', any('pin' in f for f in pg.verdict(np.zeros(3), 0.03, 1.0)))
check('achieved fails', any('achieved' in f for f in pg.verdict(np.zeros(3), 0.0, 0.85)))
check('clean hover passes', pg.verdict(np.array([0.0068, 0.0056, 0.0017]), 0.0, 1.0) == [])
check('nan fails', len(pg.verdict(np.array([np.nan, 0, 0]), np.nan, np.nan)) == 3)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
