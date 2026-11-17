#!/usr/bin/env python3
"""Independent second-key check for T161 (stage 5, s72 thrust-gap flights).

Reads the two SITL ULog flights, finds the hold window that ends at the
landing start, and reports z-bias metrics against ground truth. Writes
indi_flight/results/stage5_s72/second_key.md.

Requires pyulog (run via indi_project/docker/run.sh if not on the host).
"""
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RES = os.path.join(ROOT, 'indi_flight', 'results', 'stage5_s72')
FLIGHTS = {
    'gap085_indi_htoff': os.path.join(RES, 'gap085_indi_htoff', 'run'),
    'loss08_indi': os.path.join(RES, 'loss08_indi', 'run'),
    'loss08_indi_htoff': os.path.join(RES, 'loss08_indi_htoff', 'run'),
}
WINDOW_US = 10_000_000          # last 10 s before landing start
GRID_DT_US = 10_000             # 100 Hz common evaluation grid
SETPOINT_TYPE_LAND = 4          # position_setpoint_triplet.current.type (PX4 enum)
NAV_STATE_AUTO_LAND = 18        # vehicle_status.nav_state (PX4 enum)

TRUTH_TOPIC = 'vehicle_local_position_groundtruth'
EST_TOPIC = 'vehicle_local_position'
SP_TOPIC = 'vehicle_local_position_setpoint'
STATUS_TOPIC = 'indi_pos_status'


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def valid(t, v):
    m = np.isfinite(v)
    return t[m], v[m]


def landing_start(ulog, hold_t0):
    """First LAND setpoint after hold start; cross-checked with AUTO_LAND nav state."""
    trip = topic(ulog, 'position_setpoint_triplet')
    t_sp = None
    if trip is not None and 'current.type' in trip:
        m = (trip['timestamp'] >= hold_t0) & (trip['current.type'] == SETPOINT_TYPE_LAND)
        if m.any():
            t_sp = int(trip['timestamp'][m][0])
    vs = topic(ulog, 'vehicle_status')
    t_nav = None
    if vs is not None and 'nav_state' in vs:
        m = (vs['timestamp'] >= hold_t0) & (vs['nav_state'] == NAV_STATE_AUTO_LAND)
        if m.any():
            t_nav = int(vs['timestamp'][m][0])
    return t_sp, t_nav


def first_armed(ulog):
    a = topic(ulog, 'actuator_armed')
    if a is None or 'armed' not in a:
        return None
    m = a['armed'] == 1
    return int(a['timestamp'][m][0]) if m.any() else None


def analyse(name, run_dir):
    meta = json.load(open(os.path.join(run_dir, 'run.json')))
    ulog = ULog(os.path.join(run_dir, 'flight.ulg'))
    hold_t0 = next(e['t_us'] for e in meta['events'] if e['name'] == 'hold')
    fault_us = meta['motor_fault']['event_us']

    t_sp_land, t_nav_land = landing_start(ulog, hold_t0)
    land_us = t_sp_land if t_sp_land is not None else t_nav_land
    if land_us is None:
        raise RuntimeError(f'{name}: no landing start found')
    t_hi = land_us
    t_lo = t_hi - WINDOW_US

    gt = topic(ulog, TRUTH_TOPIC)
    est = topic(ulog, EST_TOPIC)
    sp = topic(ulog, SP_TOPIC)
    st = topic(ulog, STATUS_TOPIC)
    for label, d in [('truth', gt), ('est', est), ('setpoint', sp), ('status', st)]:
        if d is None:
            raise RuntimeError(f'{name}: topic for {label} missing')

    grid = np.arange(t_lo, t_hi, GRID_DT_US, dtype=float)
    gt_t, gt_z = valid(gt['timestamp'].astype(float), gt['z'].astype(float))
    est_t, est_z = valid(est['timestamp'].astype(float), est['z'].astype(float))
    sp_t, sp_z = valid(sp['timestamp'].astype(float), sp['z'].astype(float))
    gt_i = np.interp(grid, gt_t, gt_z)
    est_i = np.interp(grid, est_t, est_z)
    sp_i = np.interp(grid, sp_t, sp_z)

    dz_truth = np.mean(gt_i - sp_i)
    dz_est = np.mean(est_i - sp_i)
    est_err = np.mean(est_i - gt_i)

    ts = st['timestamp'].astype(float)
    m = (ts >= t_lo) & (ts <= t_hi)
    a_f = np.mean(st['a_f[2]'][m])
    a_c = np.mean(st['a_c[2]'][m])
    idx = np.where(m)[0]
    blend_final = st['blend'][idx[-1]]

    def rate(d):
        tt = d['timestamp']
        return int(((tt >= t_lo) & (tt <= t_hi)).sum()) / (WINDOW_US / 1e6)

    info = {
        'fault_us': fault_us, 'hold_t0_us': hold_t0, 'land_sp_us': t_sp_land,
        'land_nav_us': t_nav_land, 't_lo_us': t_lo, 't_hi_us': t_hi,
        'armed_us': first_armed(ulog), 't_arm_meta_us': meta.get('t_arm_us'),
        'dz_truth': dz_truth, 'dz_est': dz_est, 'est_err': est_err,
        'a_f2': a_f, 'a_c2': a_c, 'blend': blend_final,
        'rates': {TRUTH_TOPIC: rate(gt), EST_TOPIC: rate(est), SP_TOPIC: rate(sp),
                  STATUS_TOPIC: rate(st)},
        'n_status': int(m.sum()),
    }
    return info


def main():
    res = {n: analyse(n, d) for n, d in FLIGHTS.items()}
    names = list(FLIGHTS)

    for n in names:
        r = res[n]
        print(f"{n}: fault_us={r['fault_us']} hold_t0_us={r['hold_t0_us']} "
              f"land_sp_us={r['land_sp_us']} land_nav_us={r['land_nav_us']} "
              f"armed_us={r['armed_us']} t_arm_meta_us={r['t_arm_meta_us']} "
              f"window=[{r['t_lo_us']},{r['t_hi_us']}] n_status={r['n_status']}")

    rows = [
        ('dz_truth (m, GT - SP, NED)', 'dz_truth', '{:+.4f}'),
        ('dz_est (m, est - SP, NED)', 'dz_est', '{:+.4f}'),
        ('est_err (m, est - GT)', 'est_err', '{:+.4f}'),
        ('mean a_f[2] (m/s^2)', 'a_f2', '{:+.4f}'),
        ('mean a_c[2] (m/s^2)', 'a_c2', '{:+.4f}'),
        ('final blend', 'blend', '{:.4f}'),
    ]
    lines = ['# T161 second key: s72 thrust-gap flights (ULog, independent)', '',
             '| Metric | ' + ' | '.join(names) + ' |',
             '|---|' + '---|' * len(names)]
    for label, key, fmt in rows:
        lines.append(f'| {label} | ' + ' | '.join(fmt.format(res[n][key]) for n in names) + ' |')
    lines += ['', 'Logged rate in window (Hz):', '',
              '| Topic | ' + ' | '.join(names) + ' |', '|---|' + '---|' * len(names)]
    for t in [TRUTH_TOPIC, EST_TOPIC, SP_TOPIC, STATUS_TOPIC]:
        lines.append(f'| {t} | ' + ' | '.join(f"{res[n]['rates'][t]:.1f}" for n in names) + ' |')
    lines += ['', '## Method', '',
              '- Hold window: last 10 s before landing start. Landing start = first '
              'position_setpoint_triplet.current.type == LAND after hold start '
              '(cross-checked against vehicle_status nav_state == AUTO_LAND, see the stdout diagnostics).',
              '- Hold start (run.json "hold") is used only to search for the landing start. The window does not use '
              'run.json times. Clock check: first actuator_armed differs from run.json t_arm_us by ~0.72 s, so run.json '
              'times may be offset from ULog time (the fault time at motor_fault.event_us is affected too).',
              '- Setpoint, truth and estimate z are linearly interpolated onto a common 100 Hz grid '
              'over the window; means are over that grid.',
              '- dz_truth = GT z - setpoint z; dz_est = estimate z - setpoint z; est_err = estimate z - GT z '
              '(NED, positive = below).',
              '- indi_pos_status a_f[2], a_c[2] are sample means over the window; blend is the last sample in it.',
              f"- Truth topic: {TRUTH_TOPIC} (present in both logs). Setpoint topic: {SP_TOPIC}.", '']
    out = os.path.join(RES, 'second_key.md')
    with open(out, 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    print('wrote', out)


if __name__ == '__main__':
    main()
