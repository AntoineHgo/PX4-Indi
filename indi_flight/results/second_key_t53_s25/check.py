#!/usr/bin/env python3
"""Second-key check of t53 pretest s25 hover_r1: schedule vs ULog.

Usage: check.py <path/to/flight.ulg>   (sched.txt is read from the same folder)
Writes README.md next to this file.
"""
import math
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
ULG = os.path.abspath(sys.argv[1])
RUN_DIR = os.path.dirname(ULG)
SCHED = os.path.join(RUN_DIR, 'sched.txt')
POS_TOL_M = 0.05
HDG_TOL_RAD = 0.02
NAV_STATE_ANCHOR = 14
ARMING_STATE_ARMED = 2

ulog = ULog(ULG, message_name_filter_list=[
    'vehicle_status', 'sim_schedule_applied', 'trajectory_setpoint', 'vehicle_local_position'])


def topic(name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    raise SystemExit(f'topic {name} not in log')


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


out = []


def emit(line=''):
    print(line)
    out.append(line)


# ---- schedule file
sched = []
anchor_seen = False
with open(SCHED) as f:
    for line in f:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split()
        sched.append({'t': int(parts[0]), 'kind': parts[1], 'label': ' '.join(parts[1:]),
                      'rel': anchor_seen})
        if parts[1] == 'anchor':
            anchor_seen = True
anchor_sched_idx = next(i for i, r in enumerate(sched) if r['kind'] == 'anchor')

# ---- item 1: anchor instant from vehicle_status
vs = topic('vehicle_status')
vs_t = vs['timestamp'].astype(np.int64)
hit = np.flatnonzero((vs['nav_state'] == NAV_STATE_ANCHOR) & (vs['arming_state'] == ARMING_STATE_ARMED))
if hit.size == 0:
    raise SystemExit('no vehicle_status sample with nav_state 14 and armed')
anchor_meas = int(vs_t[hit[0]])

# ---- sim_schedule_applied rows
ap = topic('sim_schedule_applied')
applied = []
for i in range(len(ap['timestamp'])):
    applied.append({
        'row': int(ap['row_index'][i]),
        'applied': int(ap['timestamp'][i]),
        'anchor_us': int(ap['anchor_us'][i]),
        'sp': [float(ap[f'sp[{k}]'][i]) for k in range(4)],
    })
applied.sort(key=lambda a: a['row'])

emit('# Second-key check: t53 pretest s25, hover_r1')
emit()
emit(f'log: {ULG}')
emit(f'sched rows: {len(sched)}, sim_schedule_applied rows: {len(applied)}')
emit(f'tolerances (chosen here): position {POS_TOL_M} m, heading {HDG_TOL_RAD} rad (wrapped)')
emit()

# item 1
anchor_row = applied[anchor_sched_idx]
anchor_field = anchor_row['anchor_us']
after = [a for a in applied if a['row'] >= anchor_sched_idx]
bad_after = [a['row'] for a in after if a['anchor_us'] != anchor_meas]
item1_ok = (anchor_field == anchor_meas) and not bad_after
emit('## Item 1: anchor instant')
emit(f'vehicle_status first nav_state==14 & armed: {anchor_meas} us')
emit(f'sim_schedule_applied anchor_us (anchor row {anchor_sched_idx}): {anchor_field} us')
emit(f'rows at/after anchor with anchor_us != measured: {bad_after if bad_after else "none"}')
emit(f'ITEM 1: {"AGREE" if item1_ok else "DISAGREE"} (diff {anchor_field - anchor_meas:+d} us)')
emit()

# item 2
emit('## Item 2: applied vs scheduled time')
emit('row  kind                    sched_t_us  expected_us  applied_us   err_us  verdict')
err_rows = []
for a in applied:
    s = sched[a['row']]
    expected = anchor_meas + s['t'] if s['rel'] else s['t']
    err = a['applied'] - expected
    err_rows.append(err)
    v = 'AGREE' if err == 0 else 'DISAGREE'
    emit(f"{a['row']:<4} {s['label']:<23} {s['t']:>11d} {expected:>12d} {a['applied']:>12d} {err:>+8d}  {v}")
item2_ok = all(e == 0 for e in err_rows) and len(applied) == len(sched)
nonzero = [(a['row'], e) for a, e in zip(applied, err_rows) if e != 0]
emit(f'nonzero errors: {nonzero if nonzero else "none"}')
emit(f'ITEM 2: {"AGREE" if item2_ok else "DISAGREE"}')
emit()

# item 3
tp = topic('trajectory_setpoint')
tp_t = tp['timestamp'].astype(np.int64)
lp = topic('vehicle_local_position')
lp_t = lp['timestamp'].astype(np.int64)
emit('## Item 3: hold setpoints (sp_hold) vs local position at apply time')
emit('TS = first trajectory_setpoint at/after apply; LP = last vehicle_local_position at/before apply')
emit('row  apply_us    TS_dt_us  TS x/y/z/yaw                       LP x/y/z/heading                   '
     'd_x     d_y     d_z    d_psi   sp-TS max  verdict')
item3_ok = True
for a in applied:
    s = sched[a['row']]
    if s['kind'] != 'sp_hold':
        continue
    T = a['applied']
    j = int(np.searchsorted(tp_t, T, side='left'))
    i = int(np.searchsorted(lp_t, T, side='right')) - 1
    if j >= len(tp_t) or i < 0:
        emit(f"{a['row']:<4} no trajectory_setpoint after or local_position before apply")
        item3_ok = False
        continue
    tx, ty, tz = (float(tp['position[0]'][j]), float(tp['position[1]'][j]), float(tp['position[2]'][j]))
    tyaw = float(tp['yaw'][j])
    lx, ly, lz = float(lp['x'][i]), float(lp['y'][i]), float(lp['z'][i])
    lhdg = float(lp['heading'][i])
    dx, dy, dz = tx - lx, ty - ly, tz - lz
    dpsi = wrap(tyaw - lhdg)
    spd = max(abs(a['sp'][0] - tx), abs(a['sp'][1] - ty), abs(a['sp'][2] - tz), abs(wrap(a['sp'][3] - tyaw)))
    vals = [dx, dy, dz, dpsi]
    ok = all(np.isfinite(vals)) and max(abs(dx), abs(dy), abs(dz)) <= POS_TOL_M and abs(dpsi) <= HDG_TOL_RAD
    item3_ok &= bool(ok)
    emit(f"{a['row']:<4} {T:>10d} {int(tp_t[j]) - T:>9d}  "
         f"{tx:+.3f}/{ty:+.3f}/{tz:+.3f}/{tyaw:+.3f}  "
         f"{lx:+.3f}/{ly:+.3f}/{lz:+.3f}/{lhdg:+.3f}  "
         f"{dx:+.4f} {dy:+.4f} {dz:+.4f} {dpsi:+.4f}  {spd:.4f}  {'AGREE' if ok else 'DISAGREE'}")
emit(f'ITEM 3: {"AGREE" if item3_ok else "DISAGREE"}')

with open(os.path.join(HERE, 'README.md'), 'w') as f:
    f.write('```text\n' + '\n'.join(out) + '\n```\n')
