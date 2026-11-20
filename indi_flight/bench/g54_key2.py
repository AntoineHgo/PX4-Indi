#!/usr/bin/env python3
"""Independent second key for G5.4 touchdown, tilt, relift and edge metrics.

Usage: python3 g54_key2.py RUN_DIR [RUN_DIR ...]   (each holds flight.ulg)

All times are ULog timestamps converted to seconds (timestamp * 1e-6).
Truth altitude = -z of vehicle_local_position_groundtruth (up positive).
"""
import os
import sys

import numpy as np
from pyulog import ULog

ARMED = 2  # vehicle_status.arming_state value for ARMING_STATE_ARMED

TOPICS = {
    'vehicle_local_position_groundtruth': ['z', 'vz'],
    'vehicle_attitude_groundtruth': ['q[0]', 'q[1]', 'q[2]', 'q[3]'],
    'vehicle_status': ['arming_state'],
    'takeoff_status': ['takeoff_state'],
    'vehicle_thrust_setpoint': ['xyz[2]'],
}


def load(ulog, topic):
    d = ulog.get_dataset(topic).data
    out = {'t': d['timestamp'].astype(np.float64) * 1e-6}
    for f in TOPICS[topic]:
        out[f] = d[f].astype(np.float64)
    return out


def analyse(run_dir):
    path = os.path.join(run_dir, 'flight.ulg')
    ulog = ULog(path, message_name_filter_list=list(TOPICS))
    lp = load(ulog, 'vehicle_local_position_groundtruth')
    at = load(ulog, 'vehicle_attitude_groundtruth')
    vs = load(ulog, 'vehicle_status')
    tk = load(ulog, 'takeoff_status')
    th = load(ulog, 'vehicle_thrust_setpoint')

    alt = -lp['z']
    t = lp['t']

    # first arming
    armed_idx = np.where(vs['arming_state'] == ARMED)[0]
    t_arm = vs['t'][armed_idx[0]]

    # ground = mean truth altitude over 2 s before first arming
    m = (t >= t_arm - 2.0) & (t < t_arm)
    ground = alt[m].mean()

    # t_max = time of max truth altitude (after first arming)
    idx = np.where(t >= t_arm)[0]
    t_max = t[idx[np.argmax(alt[idx])]]

    # t_td = first time after t_max with altitude <= ground + 0.05 m
    after = np.where((t > t_max) & (alt <= ground + 0.05))[0]
    t_td = t[after[0]]

    # disarm = first non-armed state after first arming (else end of log)
    dis = np.where((vs['t'] > t_arm) & (vs['arming_state'] != ARMED))[0]
    t_dis = vs['t'][dis[0]] if len(dis) else t[-1]

    # touchdown speed = max downward vz over [t_td-0.2, t_td]
    m = (t >= t_td - 0.2) & (t <= t_td)
    v_td = lp['vz'][m].max()

    # tilt = max angle between body z and world vertical over [t_td-1, disarm]
    ta = at['t']
    m = (ta >= t_td - 1.0) & (ta <= t_dis)
    q = np.stack([at['q[0]'][m], at['q[1]'][m], at['q[2]'][m], at['q[3]'][m]], axis=1)
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    r22 = 1.0 - 2.0 * (x * x + y * y)  # body z . world z
    tilt = np.degrees(np.arccos(np.clip(r22, -1.0, 1.0))).max()

    # relift = max(altitude - ground) over [t_td, disarm]
    m = (t >= t_td) & (t <= t_dis)
    relift = (alt[m] - ground).max()

    # edge = first takeoff_state change 4 -> 5
    ts = tk['takeoff_state']
    chg = np.where((ts[:-1] == 4) & (ts[1:] == 5))[0]
    edge = tk['t'][chg[0] + 1] if len(chg) else float('nan')

    # collective = -thrust z
    tt = th['t']
    coll = -th['xyz[2]']
    if np.isfinite(edge):
        pre = coll[(tt >= edge - 0.1) & (tt < edge)].mean()
        post = coll[(tt >= edge) & (tt < edge + 0.1)].mean()
        hover = np.median(coll[(tt >= edge + 5.0) & (tt <= edge + 15.0)])
        step_pct = 100.0 * (post - pre) / hover
    else:
        hover = float('nan')
        step_pct = float('nan')

    return {
        'run': os.path.basename(os.path.normpath(run_dir)),
        't_td': t_td, 'v_td': v_td, 'tilt': tilt, 'relift': relift,
        'edge': edge, 'step_pct': step_pct, 'hover': hover,
        'ground': ground, 't_arm': t_arm, 't_dis': t_dis,
    }


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    for run_dir in argv:
        r = analyse(run_dir)
        print(f"{r['run']}: t_td={r['t_td']:.3f} s  v_td={r['v_td']:.3f} m/s  "
              f"tilt={r['tilt']:.2f} deg  relift={r['relift']:.3f} m  "
              f"edge={r['edge']:.3f} s  edge_step={r['step_pct']:.2f} %  "
              f"hover={r['hover']:.4f}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
