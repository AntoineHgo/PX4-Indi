#!/usr/bin/env python3
"""Second-key computation (s29) of three flight metrics from raw ULog files.

Independent of the primary metrics script. For each run it computes, on the
window [start_s, end_s] taken from the primary output (ULog time base, us/1e6):
  1. rate tracking RMS per axis (truth - setpoint), truth = sim_ground_truth
     angular_velocity (body FRD), setpoint = vehicle_rates_setpoint linearly
     interpolated onto the truth sample times;
  2. attitude rotation-angle RMS (deg), setpoint = vehicle_attitude_setpoint.q_d
     zero-order hold (latest setpoint at or before each truth sample), truth =
     sim_ground_truth q[0..3]; angle = 2*acos(|<q_sp, q_truth>|);
  3. effort: actuator_motors control[0..3] linearly resampled on a uniform
     400 Hz grid, 2nd-order Butterworth low-pass at 50 Hz (bilinear transform
     with prewarping, hand-written biquad) applied forward then backward,
     first difference * 400, RMS per motor, mean over the 4 motors.

Usage: python3 indi_flight/bench/second_key_s29.py
Writes indi_flight/results/second_key_s29/second_key_values.json and
indi_flight/results/second_key_s29.md (comparison table).
"""
import json
import math
import os

import numpy as np
from pyulog import ULog

ROOT = '/home/ahugo/Documents/Drotek/Codes/PX4-Indi'
G = os.path.join(ROOT, 'indi_flight/results/g16_sched_set_s26/speed4')
S = os.path.join(ROOT, 'indi_flight/results/second_key_s29')
MD = os.path.join(ROOT, 'indi_flight/results/second_key_s29.md')

RUNS = [('hover', 'r1'), ('hover', 'r2'), ('step_roll', 'r1'),
        ('step_roll', 'r3'), ('traj_lemniscate', 'r1')]
FS_GRID = 400.0
FC_LP = 50.0
REL_TOL = 0.01          # 1 % relative
ATT_ABS_TOL = 0.1       # 0.1 deg absolute
EFFORT_FS = 1.0         # normalized motor control range assumed as full scale
EFFORT_ABS_TOL = 0.001  # 0.1 % of FS


def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    raise KeyError(name)


def butter2_coeffs(fc, fs):
    """2nd-order Butterworth LP, bilinear transform with prewarping."""
    wc = 2.0 * fs * math.tan(math.pi * fc / fs)
    k = 2.0 * fs
    a0 = k * k + math.sqrt(2.0) * wc * k + wc * wc
    b = np.array([wc * wc, 2.0 * wc * wc, wc * wc]) / a0
    a = np.array([1.0, 2.0 * (wc * wc - k * k) / a0,
                  (k * k - math.sqrt(2.0) * wc * k + wc * wc) / a0])
    return b, a


def biquad_df1(b, a, x):
    """Direct-form-I biquad, initialised at steady state for the first sample
    (DC gain of the filter is 1, so a constant input passes unchanged)."""
    y = np.empty_like(x)
    x1 = x2 = y1 = y2 = x[0]
    b0, b1, b2 = b
    a1, a2 = a[1], a[2]
    for n in range(len(x)):
        xn = x[n]
        yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        y[n] = yn
        x2, x1 = x1, xn
        y2, y1 = y1, yn
    return y


def effort_rms(ulog, t0, t1):
    am = topic(ulog, 'actuator_motors')
    ta = np.asarray(am['timestamp_sample'], dtype=float) * 1e-6
    o = np.argsort(ta, kind='stable')
    ta = ta[o]
    ctrl = np.stack([np.asarray(am['control[%d]' % i], dtype=float)[o]
                     for i in range(4)], axis=1)
    grid = np.arange(t0, t1, 1.0 / FS_GRID)
    u = np.stack([np.interp(grid, ta, ctrl[:, i]) for i in range(4)], axis=1)
    b, a = butter2_coeffs(FC_LP, FS_GRID)
    out = np.empty_like(u)
    for i in range(4):
        fwd = biquad_df1(b, a, u[:, i])
        out[:, i] = biquad_df1(b, a, fwd[::-1])[::-1]
    d = np.diff(out, axis=0) * FS_GRID
    per_motor = np.sqrt(np.mean(d ** 2, axis=0))
    return float(np.mean(per_motor)), per_motor, int(len(grid))


def rate_and_attitude(ulog, t0, t1):
    gt = topic(ulog, 'sim_ground_truth')
    tt = np.asarray(gt['timestamp_sample'], dtype=float) * 1e-6
    m = (tt >= t0) & (tt <= t1)
    tt = tt[m]
    w = {ax: np.asarray(gt['angular_velocity[%d]' % i], dtype=float)[m]
         for i, ax in enumerate(('roll', 'pitch', 'yaw'))}
    q_t = np.stack([np.asarray(gt['q[%d]' % i], dtype=float)[m] for i in range(4)], axis=1)
    q_t /= np.linalg.norm(q_t, axis=1, keepdims=True)

    # rate setpoint: linear interpolation, unique sorted timestamps
    rs = topic(ulog, 'vehicle_rates_setpoint')
    ts_r, idx = np.unique(np.asarray(rs['timestamp'], dtype=float) * 1e-6, return_index=True)
    rates = {}
    for ax in ('roll', 'pitch', 'yaw'):
        sp = np.interp(tt, ts_r, np.asarray(rs[ax], dtype=float)[idx])
        err = w[ax] - sp
        rates[ax] = float(np.sqrt(np.mean(err ** 2)))

    # attitude setpoint: zero-order hold
    avs = topic(ulog, 'vehicle_attitude_setpoint')
    ts_a, idx = np.unique(np.asarray(avs['timestamp'], dtype=float) * 1e-6, return_index=True)
    q_d = np.stack([np.asarray(avs['q_d[%d]' % i], dtype=float)[idx] for i in range(4)], axis=1)
    q_d /= np.linalg.norm(q_d, axis=1, keepdims=True)
    k = np.searchsorted(ts_a, tt, side='right') - 1
    k = np.clip(k, 0, len(ts_a) - 1)
    dot = np.abs(np.sum(q_d[k] * q_t, axis=1)).clip(0.0, 1.0)
    ang = np.degrees(2.0 * np.arccos(dot))
    att_rms = float(np.sqrt(np.mean(ang ** 2)))
    return rates, att_rms, int(len(tt))


def find_primary_motor(obj, path=()):
    """Return (path, value) for every numeric leaf whose key contains 'motor_rate'."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits += find_primary_motor(v, path + (k,))
    elif 'motor_rate' in (path[-1] if path else ''):
        hits.append((path, obj))
    return hits


def compare(p, k, abs_tol):
    tol = max(REL_TOL * abs(p), abs_tol)
    rel = (k - p) / p * 100.0 if p != 0 else float('nan')
    return rel, ('AGREE' if abs(k - p) <= tol else 'DISAGREE')


def main():
    rows, values, windows = [], {}, []
    for scen, rep in RUNS:
        run = '%s/%s' % (scen, rep)
        tag = '%s_%s' % (scen, rep)
        prim = json.load(open(os.path.join(S, 'primary_%s.json' % tag)))
        t0 = float(prim['window']['start_s'])
        t1 = float(prim['window']['end_s'])
        windows.append((run, int(round(t0 * 1e6)), int(round(t1 * 1e6))))
        ulog = ULog(os.path.join(G, run, 'flight.ulg'))

        rates, att_rms, n_truth = rate_and_attitude(ulog, t0, t1)
        eff_mean, eff_axes, n_grid = effort_rms(ulog, t0, t1)
        values[tag] = {'window_s': [t0, t1], 'n_truth': n_truth, 'n_grid': n_grid,
                       'rate_rms_rad_s': rates, 'attitude_rot_rms_deg': att_rms,
                       'motor_rate_rms_per_s': eff_mean,
                       'motor_rate_rms_per_motor': [float(x) for x in eff_axes]}

        pr = prim['rate_tracking']
        pairs = [('rate roll (rad/s)', pr['roll_rms_rad_s'], rates['roll'], 0.0),
                 ('rate pitch (rad/s)', pr['pitch_rms_rad_s'], rates['pitch'], 0.0),
                 ('rate yaw (rad/s)', pr['yaw_rms_rad_s'], rates['yaw'], 0.0),
                 ('attitude rot-angle RMS (deg)',
                  prim['attitude_tracking']['rotation_angle_rms_deg'], att_rms, ATT_ABS_TOL)]
        hits = find_primary_motor(prim)
        if hits:
            pairs.append(('motor_rate_rms_per_s (mean of 4)', hits[0][1], eff_mean, EFFORT_ABS_TOL))
        else:
            pairs.append(('motor_rate_rms_per_s (mean of 4)', float('nan'), eff_mean, EFFORT_ABS_TOL))
            print('WARNING: motor_rate_rms_per_s not found in primary JSON for', tag)
        for metric, p, kv, at in pairs:
            rel, verdict = compare(p, kv, at)
            rows.append((run, metric, p, kv, rel, verdict))

    lines = []
    lines.append('# Second-key check, s29 (independent ULog computation)\n')
    lines.append('Primary values: `python3 indi_flight/bench/metrics.py --run-json '
                 '<run>/run.json --out indi_flight/results/second_key_s29/primary_<scen>_<rep>.json '
                 '<run>/flight.ulg` for each run (scratch output, existing metrics.json untouched).')
    lines.append('Second key: `python3 indi_flight/bench/second_key_s29.py` '
                 '(reads the primary scratch JSON for window only, then computes independently).\n')
    lines.append('Tolerance (G1.3): max(1 % of primary, absolute). Absolute parts: attitude 0.1 deg; '
                 'effort 0.1 % of FS with FS = 1.0 (normalized motor control, assumed); '
                 'rates have no absolute unit in G1.3 so 1 % relative only.\n')
    lines.append('Setpoint/attitude conventions: rate setpoint linearly interpolated onto truth times; '
                 'attitude setpoint zero-order hold; quaternions w-first (PX4 convention).\n')
    lines.append('## Windows (ULog time, us)\n')
    lines.append('| run | window start us | window end us |')
    lines.append('|---|---|---|')
    for run, a, b in windows:
        lines.append('| %s | %d | %d |' % (run, a, b))
    lines.append('')
    lines.append('## Comparison\n')
    lines.append('| run | metric | primary | key | rel diff | verdict |')
    lines.append('|---|---|---|---|---|---|')
    for run, metric, p, kv, rel, verdict in rows:
        lines.append('| %s | %s | %.6g | %.6g | %+.3f %% | %s |' % (run, metric, p, kv, rel, verdict))
    lines.append('')
    os.makedirs(S, exist_ok=True)
    with open(os.path.join(S, 'second_key_values.json'), 'w') as f:
        json.dump(values, f, indent=1)
    with open(MD, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    for run, metric, p, kv, rel, verdict in rows:
        print('%-18s %-32s %12.6g %12.6g %+9.3f %% %s' % (run, metric, p, kv, rel, verdict))


if __name__ == '__main__':
    main()
