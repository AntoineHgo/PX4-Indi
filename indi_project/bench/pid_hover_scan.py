#!/usr/bin/env python3
# Log scan for the pid_tuned hover mode (gz_x500 SITL). Per log: loop timing, 2-4 Hz roll-rate band RMS
# (whole window and consecutive 10 s segments, FFT mask, same window convention as gt_accel_bands.py),
# rate-loop terms, named parameters and sys/wall-time info.
# Usage: pid_hover_scan.py [--out MD] PATH=LABEL [PATH=LABEL ...]
#   Group = label prefix 'high' or 'low'. Rows are appended to MD (default indi_project/results/pid_hover_mode.md)
#   as each log is done.
# Window: run.json t_window_*_us if inside the log span, else metrics.json window, else
#   takeoff+10 s .. last landed==0 sample of vehicle_land_detected.
import datetime
import json
import os
import re
import sys

import numpy as np
from pyulog import ULog

LO, HI, SEG = 2.0, 4.0, 10.0
NEEDED = ['vehicle_angular_velocity', 'rate_ctrl_status', 'vehicle_rates_setpoint',
          'vehicle_torque_setpoint', 'vehicle_land_detected']
IGNORE = re.compile(r'^CAL_|_ID$')
NAMED = ['MC_ROLLRATE_P', 'MC_ROLLRATE_I', 'MC_ROLLRATE_D', 'MC_ROLLRATE_K', 'MC_ROLL_P',
         'IMU_GYRO_CUTOFF', 'IMU_DGYRO_CUTOFF', 'MC_INDI_EN']
COLS = [('vav_mean', 'VAV dt mean ms'), ('vav_std', 'VAV dt std ms'), ('vav_p99', 'VAV dt p99 ms'),
        ('vav_n2x', 'VAV n>2x median'), ('ts_minus_sample', 'VAV timestamp-timestamp_sample ms'),
        ('rcs_mean', 'RCS dt mean ms'), ('rcs_p99', 'RCS dt p99 ms'), ('rcs_n2x', 'RCS n>2x median'),
        ('rsp_mean', 'RSP dt mean ms'), ('rsp_p99', 'RSP dt p99 ms'), ('rsp_n2x', 'RSP n>2x median'),
        ('band_whole', 'band 2-4 Hz whole (rad/s RMS)'), ('band_s1', 'band seg1 0-10 s'),
        ('band_s2', 'band seg2 10-20 s'), ('band_s3', 'band seg3 20-30 s'),
        ('integ_mean', 'rollspeed_integ mean'), ('integ_std', 'rollspeed_integ std'),
        ('torque_std', 'torque x std')]


def fmt(x, nd=4):
    if x is None or isinstance(x, str):
        return 'n/a' if x is None else x
    return 'nan' if not np.isfinite(x) else f'{x:.{nd}g}'


def emit(out, text):
    with open(out, 'a') as f:
        f.write(text)
    print(text, end='')


def dtstats(t):
    dt = np.diff(t)
    if dt.size < 2:
        return dict(mean=np.nan, std=np.nan, p99=np.nan, n2x=0)
    med = np.median(dt)
    return dict(mean=dt.mean() * 1e3, std=dt.std() * 1e3, p99=np.percentile(dt, 99) * 1e3,
                n2x=int(np.sum(dt > 2 * med)))


def band_rms(t, x):
    # resample to a uniform grid at the median rate, keep only 2-4 Hz, return RMS
    if t.size < 16:
        return np.nan
    dt = np.median(np.diff(t))
    tg = np.arange(t[0], t[-1], dt)
    xg = np.interp(tg, t, x)
    xg = xg - xg.mean()
    f = np.fft.rfftfreq(len(xg), dt)
    X = np.fft.rfft(xg)
    X[(f < LO) | (f > HI)] = 0
    y = np.fft.irfft(X, n=len(xg))
    return float(np.sqrt(np.mean(y ** 2)))


def pick_window(dirp, t, land):
    tmin, tmax = t[0], t[-1]
    cands = []
    rj = os.path.join(dirp, 'run.json')
    if os.path.exists(rj):
        r = json.load(open(rj))
        if r.get('t_window_start_us') is not None:
            cands.append(('run.json', r['t_window_start_us'] * 1e-6, r['t_window_end_us'] * 1e-6))
    mj = os.path.join(dirp, 'metrics.json')
    if os.path.exists(mj):
        w = json.load(open(mj)).get('window')
        if w:
            cands.append(('metrics.json', w['start_s'], w['end_s']))
    note = ', '.join(f'{s}={a:.2f}-{b:.2f}' for s, a, b in cands)
    for src, a, b in cands:
        if tmin <= a < b <= tmax:
            return src, a, b, note
    tl = land['timestamp'] * 1e-6
    air = tl[land['landed'] == 0]
    if air.size == 0:
        raise RuntimeError('no airborne samples in vehicle_land_detected')
    return 'takeoff+10..landing', air[0] + 10.0, air[-1], note


def scan(path, label):
    dirp = os.path.dirname(os.path.abspath(path))
    u = ULog(path, NEEDED)
    ds = {d.name: d.data for d in u.data_list if d.multi_id == 0 and d.name in NEEDED}
    v = ds['vehicle_angular_velocity']
    t = v['timestamp'].astype(np.float64) * 1e-6
    x = v['xyz[0]'].astype(np.float64)
    src, w0, w1, note = pick_window(dirp, t, ds['vehicle_land_detected'])
    k = (t >= w0) & (t < w1)
    m = {}
    s = dtstats(t[k])
    m.update(vav_mean=s['mean'], vav_std=s['std'], vav_p99=s['p99'], vav_n2x=s['n2x'])
    if 'timestamp_sample' in v:
        d = v['timestamp'][k].astype(np.int64) - v['timestamp_sample'][k].astype(np.int64)
        m['ts_minus_sample'] = d.mean() * 1e-3
    for nm, key in (('rate_ctrl_status', 'rcs'), ('vehicle_rates_setpoint', 'rsp')):
        if nm in ds:
            tt = ds[nm]['timestamp'].astype(np.float64) * 1e-6
            tt = tt[(tt >= w0) & (tt < w1)]
            s = dtstats(tt)
            m[key + '_mean'], m[key + '_p99'], m[key + '_n2x'] = s['mean'], s['p99'], s['n2x']
    m['band_whole'] = band_rms(t[k], x[k])
    for i in range(3):
        a = w0 + i * SEG
        b = a + SEG
        q = (t >= a) & (t < b)
        m[f'band_s{i + 1}'] = band_rms(t[q], x[q]) if b <= w1 + 1e-3 else np.nan
    rc = ds.get('rate_ctrl_status')
    if rc is not None and 'rollspeed_integ' in rc:
        tr = rc['timestamp'].astype(np.float64) * 1e-6
        g = rc['rollspeed_integ'][(tr >= w0) & (tr < w1)].astype(np.float64)
        m['integ_mean'], m['integ_std'] = g.mean(), g.std()
    tq = ds.get('vehicle_torque_setpoint')
    if tq is not None:
        tt = tq['timestamp'].astype(np.float64) * 1e-6
        m['torque_std'] = float(np.std(tq['xyz[0]'][(tt >= w0) & (tt < w1)]))
    mi = u.msg_info_dict
    boot = int(mi.get('boot_time_utc_us', 0) or 0)
    meta = dict(src=f'{src} ({note}); used {w0:.2f}-{w1:.2f} s', window=(w0, w1))
    meta['utc'] = (datetime.datetime.fromtimestamp(boot * 1e-6, datetime.timezone.utc)
                   .strftime('%Y-%m-%d %H:%M:%S UTC') if boot else 'n/a')
    rj = os.path.join(dirp, 'run.json')
    meta['wall'] = json.load(open(rj)).get('wall_time_s') if os.path.exists(rj) else None
    meta['sys'] = (f"{mi.get('sys_name', '?')} {str(mi.get('ver_sw', '?'))[:10]} "
                   f"{mi.get('ver_sw_branch', '')} hw={mi.get('ver_hw', '?')}")
    return m, meta, dict(u.initial_parameters)


def summ(a):
    if not np.isfinite(a).any():
        return 'n/a'
    return f'{np.nanmean(a):.4g} [{np.nanmin(a):.4g}..{np.nanmax(a):.4g}]'


def main():
    args = sys.argv[1:]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'pid_hover_mode.md')
    if args[:1] == ['--out']:
        out, args = args[1], args[2:]
    hdr = '| label | group | window source | ' + ' | '.join(c[1] for c in COLS) + ' | boot UTC | wall_time_s | sys / ver / branch / hw |'
    emit(out, '\n## Per-log rows\n\nVAV = vehicle_angular_velocity, RCS = rate_ctrl_status, RSP = vehicle_rates_setpoint, dt = sample interval over the window.\n\n'
         + hdr + '\n' + '|' + '---|' * (3 + len(COLS) + 3) + '\n')
    runs = []
    for a in args:
        path, label = a.split('=', 1)
        m, meta, params = scan(path, label)
        group = 'high' if label.startswith('high') else 'low'
        cells = [label, group, meta['src']] + [fmt(m.get(k, np.nan)) for k, _ in COLS] + [meta['utc'], fmt(meta['wall']), meta['sys']]
        emit(out, '| ' + ' | '.join(cells) + ' |\n')
        runs.append((label, group, m, params))

    emit(out, '\n## High vs low (mean over runs [min..max])\n\n| metric | high | low | high/low (means) |\n|---|---|---|---|\n')
    for k, title in COLS:
        h = np.array([mm.get(k, np.nan) for _, g, mm, _ in runs if g == 'high'], dtype=float)
        lo = np.array([mm.get(k, np.nan) for _, g, mm, _ in runs if g == 'low'], dtype=float)
        ratio = fmt(np.nanmean(h) / np.nanmean(lo)) if np.isfinite(h).any() and np.isfinite(lo).any() else 'n/a'
        emit(out, f'| {title} | {summ(h)} | {summ(lo)} | {ratio} |\n')

    names = NAMED
    emit(out, '\n## Named parameters per run (the rest of the ULog parameters are covered by the difference section)\n\n| label | ' + ' | '.join(names) + ' |\n'
         + '|---|' + '---|' * len(names) + '\n')
    for lab, _, _, p in runs:
        emit(out, f'| {lab} | ' + ' | '.join(fmt(p[k], 6) if k in p else 'absent' for k in names) + ' |\n')

    allp = set()
    for _, _, _, p in runs:
        allp |= set(p)
    keys = sorted(k for k in allp if not IGNORE.search(k))
    diff, within = [], []
    for k in keys:
        hv = sorted({repr(p.get(k, 'absent')) for _, g, _, p in runs if g == 'high'})
        lv = sorted({repr(p.get(k, 'absent')) for _, g, _, p in runs if g == 'low'})
        if hv != lv:
            diff.append(f'| {k} | {", ".join(hv)} | {", ".join(lv)} |')
        for gname in ('high', 'low'):
            vals = {repr(p.get(k, 'absent')) for _, g, _, p in runs if g == gname}
            if len(vals) > 1:
                within.append(f'{k} ({gname})')
    emit(out, f'\n## Parameter differences, high vs low (CAL_* and *_ID ignored; {len(diff)} keys)\n\n'
         '| param | high values | low values |\n|---|---|---|\n' + '\n'.join(diff) + '\n')
    emit(out, f'\nParameters varying within a group (not high-vs-low): {", ".join(within) if within else "none"}\n')


if __name__ == '__main__':
    main()
