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


SPLIT_OUT = os.path.join(RES, 'a33_split.md')


def _unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        return v / n


def _ang_deg(a, b):
    d = np.sum(a * b, axis=-1)
    with np.errstate(invalid='ignore', divide='ignore'):
        c = d / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def _body_z(q):
    """Body z axis in NED for PX4 quaternions q (N,4) = (w,x,y,z), body-to-NED."""
    w, x, y, z = q.T
    return np.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], axis=-1)


def _vec(d, prefix, n, m):
    return np.stack([d[f'{prefix}[{i}]'][m].astype(float) for i in range(n)], axis=-1)


def split_stats(name, r):
    ulog = ULog(os.path.join(FLIGHTS[name], 'flight.ulg'))
    t_lo, t_hi = r['t_lo_us'], r['t_hi_us']

    def win(d):
        t = d['timestamp']
        return (t >= t_lo) & (t <= t_hi)

    out = {}
    st = topic(ulog, STATUS_TOPIC)
    m = win(st)
    a_c = _vec(st, 'a_c', 3, m)
    a_f = _vec(st, 'a_f', 3, m)
    t_c = _vec(st, 't_c', 3, m)
    t_f = _vec(st, 't_f', 3, m)
    out['da'] = np.nanmean(a_c - a_f, axis=0)
    out['tc'] = np.nanmean(t_c, axis=0)
    out['tf'] = np.nanmean(t_f, axis=0)
    out['ang_tt'] = np.nanmean(_ang_deg(t_c, t_f))
    out['frozen'] = np.mean(st['blend_frozen'][m].astype(bool))
    out['blend'] = np.nanmean(st['blend'][m])
    out['thrust'] = np.nanmean(st['thrust'][m])
    out['n_status'] = int(m.sum())

    grid = np.arange(t_lo, t_hi, GRID_DT_US, dtype=float)

    def zgrid(d, key):
        t = d['timestamp'].astype(float)
        q = np.stack([d[f'{key}[{i}]'].astype(float) for i in range(4)], axis=-1)
        ok = np.isfinite(q).all(axis=-1)
        z = _body_z(q[ok])
        t = t[ok]
        zi = np.stack([np.interp(grid, t, z[:, i]) for i in range(3)], axis=-1)
        return _unit(zi)

    z_sp = zgrid(topic(ulog, 'vehicle_attitude_setpoint'), 'q_d')
    z_at = zgrid(topic(ulog, 'vehicle_attitude'), 'q')
    out['tilt_sp'] = np.degrees(np.arccos(np.clip(z_sp[:, 2], -1, 1))).mean()
    out['tilt_at'] = np.degrees(np.arccos(np.clip(z_at[:, 2], -1, 1))).mean()
    out['ang_zz'] = _ang_deg(z_sp, z_at).mean()

    am = topic(ulog, 'actuator_motors')
    mm = win(am)
    out['ctrl'] = [float(np.nanmean(am[f'control[{i}]'][mm])) for i in range(4)]

    es = topic(ulog, 'esc_status')
    rpm = None
    if es is not None:
        me = win(es)
        if me.sum() > 0:
            rpm = {}
            for i in range(12):
                k = f'esc[{i}].esc_rpm'
                if k in es:
                    rpm[i] = float(np.nanmean(es[k][me]))
    out['rpm'] = rpm
    return out


def split_report(res):
    names = list(FLIGHTS)
    stats = {n: split_stats(n, res[n]) for n in names}

    def f3(v):
        return ' / '.join(f'{x:+.3f}' for x in v)

    def row(label, fn):
        return f'| {label} | ' + ' | '.join(fn(stats[n]) for n in names) + ' |'

    def rpm_txt(s):
        if s['rpm'] is None:
            return 'absent'
        return ', '.join(f'm{i} {v:.0f}' for i, v in sorted(s['rpm'].items()))

    lines = ['# T162 a33 split: s72 thrust-gap flights (ULog, same window as second key)', '',
             '| Metric | ' + ' | '.join(names) + ' |',
             '|---|' + '---|' * len(names),
             row('window start / end (us)', lambda s: ''),  # placeholder replaced below
             ]
    lines[-1] = '| window (us) | ' + ' | '.join(
        f"[{res[n]['t_lo_us']}, {res[n]['t_hi_us']}]" for n in names) + ' |'
    lines += [
        row('mean a_c - a_f x / y / z (m/s^2)', lambda s: f3(s['da'])),
        row('mean t_c x / y / z', lambda s: f3(s['tc'])),
        row('mean t_f x / y / z', lambda s: f3(s['tf'])),
        row('mean angle t_c vs t_f (deg)', lambda s: f"{s['ang_tt']:.2f}"),
        row('fraction blend_frozen true', lambda s: f"{s['frozen']:.3f}"),
        row('mean blend', lambda s: f"{s['blend']:.4f}"),
        row('mean thrust', lambda s: f"{s['thrust']:+.4f}"),
        row('tilt setpoint q_d (deg)', lambda s: f"{s['tilt_sp']:.2f}"),
        row('tilt actual q (deg)', lambda s: f"{s['tilt_at']:.2f}"),
        row('mean angle body z: setpoint vs actual (deg)', lambda s: f"{s['ang_zz']:.2f}"),
        row('mean actuator_motors control[0..3]', lambda s: ' / '.join(f'{c:.3f}' for c in s['ctrl'])),
        row('mean esc_status rpm per motor', rpm_txt),
        '',
        '## Method', '',
        '- Window: same as second_key (last 10 s before landing start, from analyse()). '
        'All indi_pos_status, actuator_motors and esc_status samples inside it are used directly; '
        'no interpolation for those.',
        '- Vector angles (t_c vs t_f, body z setpoint vs actual) are per sample; the means are over the samples.',
        '- Attitude: body z (third column of the body-to-NED rotation of q_d or q) is interpolated '
        'linearly onto the 100 Hz window grid by timestamp, then normalised. Tilt = angle between body z and NED down.',
        '- blend_frozen fraction is over indi_pos_status samples in the window; blend and thrust are sample means.',
        '- esc rpm is the mean over esc_status samples in the window for each esc[i].esc_rpm present in the log.',
        '']
    with open(SPLIT_OUT, 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    print('wrote', SPLIT_OUT)


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
    split_report(res)


if __name__ == '__main__':
    main()
