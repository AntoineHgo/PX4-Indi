#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
from pyulog import ULog

ROOT = Path('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results')
OUT = ROOT / 'second_key_window_s15.md'
BASES = ['det_g16', 'det_g16_s4']
SCEN = ['hover', 'step_roll', 'traj_lemniscate']
RUNS = [f'r{i}' for i in range(1, 6)]
ARMED = 2
OFFBOARD_NAV = [14, 23]
OFFSET_US = 3_000_000
TOL_MS = 1.0


def first_offboard_t(ulog_path):
    ulog = ULog(str(ulog_path), message_name_filter_list=['vehicle_status'])
    ds = [d for d in ulog.data_list if d.name == 'vehicle_status']
    if not ds:
        raise RuntimeError('no vehicle_status topic')
    d = min(ds, key=lambda x: x.multi_id)
    ts = np.asarray(d.data['timestamp'], dtype=np.int64)
    arm = np.asarray(d.data['arming_state'])
    nav = np.asarray(d.data['nav_state'])
    order = np.argsort(ts, kind='stable')
    ts, arm, nav = ts[order], arm[order], nav[order]
    hits = np.flatnonzero((arm == ARMED) & np.isin(nav, OFFBOARD_NAV))
    if hits.size == 0:
        raise RuntimeError('no armed + offboard sample')
    return int(ts[hits[0]]), len(ds)


lines = []
rows = []
groups = {}
for base in BASES:
    for sc in SCEN:
        for r in RUNS:
            d = ROOT / base / sc / r
            run = json.loads((d / 'run.json').read_text())
            met = json.loads((d / 'metrics.json').read_text())['window']
            T, n_inst = first_offboard_t(d / 'flight.ulg')
            exp_start_us = T + OFFSET_US
            exp_end_us = exp_start_us + (run['t_window_end_us'] - run['t_window_start_us'])
            m_start_ms = float(met['start_s']) * 1e3
            m_end_ms = float(met['end_s']) * 1e3
            e_start_ms = exp_start_us / 1e3
            e_end_ms = exp_end_us / 1e3
            ds_ms = m_start_ms - e_start_ms
            de_ms = m_end_ms - e_end_ms
            label = f'{base}/{sc}/{r}'
            rows.append((label, T, n_inst, e_start_ms, m_start_ms, ds_ms, e_end_ms, m_end_ms, de_ms))
            groups.setdefault(f'{base}/{sc}', []).append(T)

hdr = ('| run | T (s) | n_vehicle_status | exp start (s) | metrics start (s) | diff start (ms) '
       '| exp end (s) | metrics end (s) | diff end (ms) |')
lines.append(hdr)
lines.append('|' + '---|' * 9)
for label, T, n_inst, es, ms_, ds, ee, me, de in rows:
    lines.append(f'| {label} | {T/1e6:.3f} | {n_inst} | {es/1e3:.3f} | {ms_/1e3:.3f} | {ds:+.4f} '
                 f'| {ee/1e3:.3f} | {me/1e3:.3f} | {de:+.4f} |')

bad = [row[0] for row in rows if abs(row[5]) >= TOL_MS or abs(row[8]) >= TOL_MS]
max_abs = max(max(abs(r[5]), abs(r[8])) for r in rows)
lines.append('')
lines.append(f'Max absolute diff over 30 runs: {max_abs:.6f} ms')
if bad:
    lines.append('Verdict: DISAGREE for ' + ', '.join(bad))
else:
    lines.append('Verdict: AGREE (every diff < 1 ms)')
lines.append('')
lines.append('T spread per scenario group (max - min over r1..r5):')
lines.append('')
lines.append('| group | min T (s) | max T (s) | spread (ms) |')
lines.append('|---|---|---|---|')
for g, Ts in groups.items():
    lines.append(f'| {g} | {min(Ts)/1e6:.3f} | {max(Ts)/1e6:.3f} | {(max(Ts)-min(Ts))/1e3:.3f} |')

text = '\n'.join(lines) + '\n'
print(text)
with OUT.open('a') as f:
    f.write(text)
