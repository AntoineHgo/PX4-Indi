#!/usr/bin/env python3
"""Independent second key for the G5.1 stick-step test (S136).

usage: g51_key2.py <run_dir> <acro|stab>

Reads <run_dir>/flight.ulg and <run_dir>/sticks.csv. Prints markdown.
"""
import csv
import math
import sys

import numpy as np
from pyulog import ULog

R2D = 180.0 / math.pi
AXES = ['roll', 'pitch', 'yaw']
STICK_COL = {'roll': 'y', 'pitch': 'x', 'yaw': 'r'}
# acro command gain: roll=+y, pitch=-x, yaw=+r; 1000 raw = 100 deg/s
CMD_SIGN = {'roll': 1.0, 'pitch': -1.0, 'yaw': 1.0}
ACRO_FULL_DEG_S = 100.0


def load_sticks(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['t_sim_us']) for r in rows]) * 1e-6
    v = {ax: np.array([float(r[c]) for r in rows]) for ax, c in STICK_COL.items()}
    return t, v


def find_doublet(t, v, thresh=100.0):
    """Return (+A start, -A start, return to 0) of the first +,-,0 sequence."""
    s = np.where(v > thresh, 1, np.where(v < -thresh, -1, 0))
    events = []
    prev = 0
    for i in range(len(s)):
        if s[i] != prev:
            events.append((t[i], int(s[i])))
            prev = s[i]
    for i in range(len(events) - 2):
        if events[i][1] == 1 and events[i + 1][1] == -1 and events[i + 2][1] == 0:
            return events[i][0], events[i + 1][0], events[i + 2][0]
    raise SystemExit('no +A/-A/0 doublet found')


def stick_at(ts, vs, tq):
    """Stick value applied at times tq (zero-order hold on the stick timeline)."""
    idx = np.searchsorted(ts, tq, side='right') - 1
    idx = np.clip(idx, 0, len(vs) - 1)
    return vs[idx]


def get_topic(log, name, fields):
    try:
        d = log.get_dataset(name).data
    except (KeyError, IndexError):
        raise SystemExit('topic missing: ' + name)
    t = d['timestamp'] * 1e-6
    return t, [d[f] for f in fields]


def acro_edges(ts, vs, ax, edge_pos, edge_neg, edge_ret, t_end):
    """RMS of (commanded - truth) per edge plateau for axis ax."""
    v = vs[ax]
    g = CMD_SIGN[ax]
    out = {}
    windows = [
        ('+A', edge_pos, edge_neg),
        ('-A', edge_neg, edge_ret),
        ('0', edge_ret, min(edge_ret + 2.5, t_end)),  # capped to 1.0 s below
    ]
    return v, g, windows


def run_acro(run_dir):
    ts, vs = load_sticks(run_dir + '/sticks.csv')
    log = ULog(run_dir + '/flight.ulg', message_name_filter_list=[
        'vehicle_angular_velocity_groundtruth'])
    tt, (wx, wy, wz) = get_topic(log, 'vehicle_angular_velocity_groundtruth',
                                 ['xyz[0]', 'xyz[1]', 'xyz[2]'])
    truth = {'roll': wx * R2D, 'pitch': wy * R2D, 'yaw': wz * R2D}
    # stick-driven commanded rate, sampled on the ULog timeline
    lines = []
    lines.append('| axis | edge | window [s] | RMS (deg/s) | rise t90 (ms) | overshoot (%) |')
    lines.append('|---|---|---|---|---|---|')
    for ax in AXES:
        ep, en, er = find_doublet(ts, vs[ax])
        edges = [('+A', ep, en), ('-A', en, er), ('0', er, None)]
        for label, t0, t1 in edges:
            if label == '0':
                t1_eff = min(t0 + 1.0, t0 + 1e9)
                # next axis edge bounds the plateau; cap at 1.0 s
                t1_eff = t0 + 1.0
            else:
                t1_eff = t1
            w0 = t0 + 0.1
            m = (tt >= w0) & (tt < t1_eff)
            cmd = CMD_SIGN[ax] * stick_at(ts, vs[ax], tt[m]) / 1000.0 * ACRO_FULL_DEG_S
            err = cmd - truth[ax][m]
            rms = math.sqrt(float(np.mean(err ** 2))) if m.any() else float('nan')
            # rise / overshoot on the commanded (non-zero) plateau
            rise = overs = float('nan')
            if label != '0':
                plat = CMD_SIGN[ax] * stick_at(ts, vs[ax], np.array([t0 + 0.3]))[0] / 1000.0 * ACRO_FULL_DEG_S
                mr = (tt >= t0) & (tt < t1_eff)
                tr = truth[ax][mr]
                tm = tt[mr]
                if plat != 0 and tr.size:
                    sgn = np.sign(plat)
                    hit = np.nonzero(sgn * tr >= 0.9 * abs(plat))[0]
                    if hit.size:
                        rise = (tm[hit[0]] - t0) * 1e3
                    overs = (np.max(sgn * tr) / abs(plat) - 1.0) * 100.0
            lines.append('| %s | %s | [%.3f, %.3f] | %.2f | %s | %s |' % (
                ax, label, w0, t1_eff, rms,
                '%.0f' % rise if not math.isnan(rise) else '-',
                '%.1f' % overs if not math.isnan(overs) else '-'))
    return '\n'.join(lines)


def run_stab(run_dir):
    ts, vs = load_sticks(run_dir + '/sticks.csv')
    log = ULog(run_dir + '/flight.ulg', message_name_filter_list=[
        'vehicle_attitude_groundtruth', 'vehicle_angular_velocity_groundtruth'])
    ta, (q0, q1, q2, q3) = get_topic(log, 'vehicle_attitude_groundtruth',
                                     ['q[0]', 'q[1]', 'q[2]', 'q[3]'])
    # PX4 quaternion is [w, x, y, z]; body z in world z = 1 - 2(x^2 + y^2)
    cz = 1.0 - 2.0 * (q1 ** 2 + q2 ** 2)
    tilt = np.degrees(np.arccos(np.clip(cz, -1.0, 1.0)))
    tw, (wx, wy, wz) = get_topic(log, 'vehicle_angular_velocity_groundtruth',
                                 ['xyz[0]', 'xyz[1]', 'xyz[2]'])
    yaw_rate = np.abs(wz * R2D)
    lines = []
    lines.append('| axis | release [s] | window [s] | max truth tilt (deg) | max abs truth yaw rate (deg/s) |')
    lines.append('|---|---|---|---|---|')
    for ax in AXES:
        _, _, er = find_doublet(ts, vs[ax])
        w0, w1 = er + 1.0, er + 2.5
        m = (ta >= w0) & (ta <= w1)
        mx = float(np.max(tilt[m])) if m.any() else float('nan')
        yr = '-'
        if ax == 'yaw':
            my = (tw >= w0) & (tw <= w1)
            yr = '%.2f' % float(np.max(yaw_rate[my])) if my.any() else 'nan'
        lines.append('| %s | %.3f | [%.3f, %.3f] | %.2f | %s |' % (ax, er, w0, w1, mx, yr))
    lines.append('')
    lines.append('Whole-run max truth tilt (LOC check, < 80 deg): %.2f deg' % float(np.max(tilt)))
    return '\n'.join(lines)


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ('acro', 'stab'):
        raise SystemExit(__doc__)
    run_dir, mode = sys.argv[1].rstrip('/'), sys.argv[2]
    print('## %s (%s)' % (run_dir.split('/')[-1], mode))
    print()
    print(run_acro(run_dir) if mode == 'acro' else run_stab(run_dir))
    print()


if __name__ == '__main__':
    main()
