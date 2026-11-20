#!/usr/bin/env python3
"""Independent second key for the G5.2 exact test (S138), GATES 5b.

usage: key2.py            (runs the six runs next to this script's parent dir)

Anchors every edge on the log: stick steps from manual_control_setpoint
(throttle = z stick, pitch = x stick), truth from vehicle_local_position_groundtruth
(NED). Prints a markdown table, one line per run and step.
"""
import math
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.dirname(HERE)
RUNS = ['altctl_s1', 'altctl_s2', 'altctl_s3', 'posctl_s1', 'posctl_s2', 'posctl_s3']
STICK_THR = 0.05       # stick deflection that counts as applied
CENTRE_S = 6.0         # centred window after each release
FINAL_S = 1.0          # final = mean truth over last 1.0 s of centred window
BAND = 0.02            # settle band, fraction of d
OS_Z_MAX, OS_X_MAX = 0.3, 0.5
SETTLE_MAX = 4.0
D_Z_MIN, D_X_MIN = 1.0, 2.0


def segments(t, v):
    """(t_on, t_off) for each contiguous |v| > STICK_THR stretch."""
    on = np.abs(v) > STICK_THR
    out = []
    i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            out.append((float(t[i]), float(t[j - 1]) if j < len(t) else float(t[-1])))
            i = j
        else:
            i += 1
    return out


def load(run_dir):
    log = ULog(os.path.join(run_dir, 'flight.ulg'), message_name_filter_list=[
        'manual_control_setpoint', 'vehicle_local_position_groundtruth'])
    ms = log.get_dataset('manual_control_setpoint').data
    tm = ms['timestamp'] * 1e-6
    gt = log.get_dataset('vehicle_local_position_groundtruth').data
    tg = gt['timestamp'] * 1e-6
    pos = np.stack([gt['x'], gt['y'], gt['z']], axis=1)  # NED
    return tm, ms['throttle'], ms['pitch'], tg, pos


def truth_at(tg, pos, t):
    return np.array([np.interp(t, tg, pos[:, k]) for k in range(3)])


def evaluate(tg, pos, t_on, t_off, kind):
    """kind 'z' (vertical, up positive) or 'x' (horizontal along start->final)."""
    r = t_off                     # release edge
    start = truth_at(tg, pos, np.array([t_on]))[:, 0]
    m_fin = (tg >= r + CENTRE_S - FINAL_S) & (tg < r + CENTRE_S)
    final = pos[m_fin].mean(axis=0)
    m = (tg >= r) & (tg < r + CENTRE_S)
    tw = tg[m]
    pw = pos[m]
    if kind == 'z':
        disp = -(final[2] - start[2])            # up positive
        u = np.array([0.0, 0.0, -1.0])
        proj = -(pw[:, 2] - start[2])
        perp_h = np.hypot(pw[:, 0] - final[0], pw[:, 1] - final[1])
        off = float(np.max(perp_h))
        off_lab = 'max horiz drift (m)'
        d_min = D_Z_MIN
    else:
        dv = final[:2] - start[:2]
        disp = float(np.hypot(dv[0], dv[1]))
        u = np.array([dv[0], dv[1], 0.0]) / disp if disp > 0 else np.array([1.0, 0.0, 0.0])
        rel = pw - start
        proj = rel[:, 0] * u[0] + rel[:, 1] * u[1]
        perp = np.abs(-rel[:, 0] * u[1] + rel[:, 1] * u[0])
        off = float(np.max(np.maximum(perp, np.abs(pw[:, 2] - final[2]))))
        off_lab = 'max perp/z excursion (m)'
        d_min = D_X_MIN
    d = abs(disp)
    # overshoot beyond final, in step direction, after release
    over = max(0.0, float(np.max(proj - d)))
    # settle: last re-entry into the 2 % band (|proj - d| <= 0.02 d)
    err = np.abs(proj - d)
    outside = err > BAND * d
    if not outside.any():
        settle = 0.0
    elif outside[-1]:
        settle = float('inf')
    else:
        last = int(np.nonzero(outside)[0][-1])
        settle = float(tw[last + 1] - r)
    valid = d >= d_min
    ok = valid and over <= (OS_Z_MAX if kind == 'z' else OS_X_MAX) and settle <= SETTLE_MAX
    return dict(d=d, over=over, settle=settle, off=off, off_lab=off_lab, valid=valid,
                direction_ok=(disp > 0), ok=ok, t_on=t_on, t_off=t_off)


def main():
    rows = []
    for name in RUNS:
        run_dir = os.path.join(RESULTS, name)
        tm, thr, pit, tg, pos = load(run_dir)
        zs = segments(tm, thr)
        xs = segments(tm, pit)
        steps = []
        if zs:
            steps.append(('z', zs[0]))
        if 'posctl' in name and xs:
            steps.append(('x', xs[0]))
        if len(zs) != 1 or ('posctl' in name and len(xs) != 1) or ('altctl' in name and xs):
            print('# WARNING %s: z segments %d, x segments %d' % (name, len(zs), len(xs)), file=sys.stderr)
        for kind, (t_on, t_off) in steps:
            res = evaluate(tg, pos, t_on, t_off, kind)
            rows.append((name, kind, res))
    print('| run | step | edge on/off (s) | d (m) | overshoot (m) | settle (s) | off-axis (m) | valid | verdict |')
    print('|---|---|---|---|---|---|---|---|---|')
    for name, kind, r in rows:
        verdict = 'PASS' if r['ok'] else 'FAIL'
        if not r['valid']:
            verdict += ' (invalid d)'
        if not r['direction_ok']:
            verdict += ' (wrong direction)'
        settle = '%.2f' % r['settle'] if math.isfinite(r['settle']) else 'never'
        print('| %s | %s | %.3f / %.3f | %.3f | %.3f | %s | %.3f (%s) | %s | %s |' % (
            name, kind, r['t_on'], r['t_off'], r['d'], r['over'], settle, r['off'], r['off_lab'],
            'yes' if r['valid'] else 'no', verdict))


if __name__ == '__main__':
    main()
