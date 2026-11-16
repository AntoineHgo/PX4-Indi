#!/usr/bin/env python3
"""A-14 closing check (S28): baro consistency and EKF height error before and after arm.

Per ULog: first raw sensor_baro pressure, CAL_BARO0_OFF at logger start and its last change,
estimator_baro_bias at first sample, at arm and its median over [arm - 5 s, arm] (A-20 measure), whether cs_baro_fault ever set and cs_baro_hgt at arm,
max |z_ekf - z_true| over [t0, t1] (log time = sim time, s), and the median true z over [h0, h1].

Pass (design/a14_cause_s27.md, closing test as amended in DECISIONS D-A14): raw pressure ~95600 Pa
(baro agrees with GNSS without autocal step), no baro fault, max |z_ekf - z_true| < 0.1 m in 15-35 s,
true hold altitude within 0.05 m of the median over all runs.

Usage: a14_close_check.py --out table.md LOG1.ulg [LOG2.ulg ...]   (exit 1 if any run fails)
"""

import argparse
import sys

import numpy as np
from pyulog import ULog


def topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def check(path, t0, t1, h0, h1):
    u = ULog(path, ['sensor_baro', 'estimator_baro_bias', 'estimator_status_flags', 'vehicle_status',
                    'vehicle_local_position', 'vehicle_local_position_groundtruth'])
    baro = topic(u, 'sensor_baro')
    bias = topic(u, 'estimator_baro_bias')
    flags = topic(u, 'estimator_status_flags')
    st = topic(u, 'vehicle_status')
    lp = topic(u, 'vehicle_local_position')
    gt = topic(u, 'vehicle_local_position_groundtruth')
    armed = np.nonzero(st['arming_state'] == 2)[0]
    t_arm = st['timestamp'][armed[0]] if len(armed) else None
    off0 = u.initial_parameters.get('CAL_BARO0_OFF', float('nan'))
    offs = [v for (_, n, v) in u.changed_parameters if n == 'CAL_BARO0_OFF']
    r = {'p0': float(baro['pressure'][0]), 'off0': off0, 'off_last': offs[-1] if offs else off0,
         'bias0': float(bias['bias'][0]), 'baro_fault': bool(np.any(flags['cs_baro_fault']))}
    if t_arm is not None:
        i = min(np.searchsorted(bias['timestamp'], t_arm), len(bias['timestamp']) - 1)
        r['bias_arm'] = float(bias['bias'][i])
        # A-20 (S33 T69): bias0 is a first-sample transient; use the median over the settled pre-arm window
        mb = (bias['timestamp'] >= t_arm - 5e6) & (bias['timestamp'] <= t_arm)
        r['bias_med'] = float(np.median(bias['bias'][mb])) if np.any(mb) else float('nan')
        j = min(np.searchsorted(flags['timestamp'], t_arm), len(flags['timestamp']) - 1)
        r['baro_hgt_arm'] = int(flags['cs_baro_hgt'][j])
    else:
        r['bias_arm'], r['bias_med'], r['baro_hgt_arm'] = float('nan'), float('nan'), -1
    zt = np.interp(lp['timestamp'], gt['timestamp'], gt['z'])
    m = (lp['timestamp'] >= t0 * 1e6) & (lp['timestamp'] <= t1 * 1e6)
    r['max_err'] = float(np.max(np.abs(lp['z'][m] - zt[m]))) if np.any(m) else float('nan')
    mh = (gt['timestamp'] >= h0 * 1e6) & (gt['timestamp'] <= h1 * 1e6)
    r['z_hold'] = float(np.median(gt['z'][mh])) if np.any(mh) else float('nan')
    r['t_arm'] = t_arm / 1e6 if t_arm is not None else float('nan')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logs', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--err-window', default='15,35')
    ap.add_argument('--hold-window', default='45,60')
    a = ap.parse_args()
    t0, t1 = map(float, a.err_window.split(','))
    h0, h1 = map(float, a.hold_window.split(','))
    rows = [(p, check(p, t0, t1, h0, h1)) for p in a.logs]
    zmed = float(np.nanmedian([r['z_hold'] for _, r in rows]))
    lines = ['| log | p0 Pa | CAL_OFF start/last | bias0 | bias@arm | bias med arm-5..arm | baro_hgt@arm | baro_fault | '
             f'max err {t0:g}-{t1:g} s | z_hold (med {zmed:.3f}) | t_arm | pass |', '|' + '---|' * 12]
    ok_all = True
    for p, r in rows:
        ok = (abs(r['p0'] - 95600) < 200 and not r['baro_fault'] and r['max_err'] < 0.1
              and abs(r['z_hold'] - zmed) < 0.05)
        ok_all &= ok
        lines.append(f"| {p} | {r['p0']:.0f} | {r['off0']:.1f}/{r['off_last']:.1f} | {r['bias0']:.2f} | "
                     f"{r['bias_arm']:.2f} | {r['bias_med']:.2f} | {r['baro_hgt_arm']} | {int(r['baro_fault'])} | {r['max_err']:.3f} | "
                     f"{r['z_hold']:.3f} | {r['t_arm']:.2f} | {'PASS' if ok else 'FAIL'} |")
    lines.append(f"\n{sum(1 for _ in rows)} runs, overall {'PASS' if ok_all else 'FAIL'}")
    open(a.out, 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
