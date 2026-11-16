#!/usr/bin/env python3
"""Pre-test gate on one flight log: refuses a configuration that oscillates or pins motors.

Usage: pretest_gate.py LOG OUT.md [--delay 15] [--length 30]

Window: starts `delay` s after the first vehicle_land_detected sample with landed false (log event, not the
runner's view), lasts `length` s, and is cut at the first disarm after it. Checks in that window:
  rate      per-axis RMS of vehicle_angular_velocity.xyz after removing a 1 s centred moving mean < 0.02 rad/s
  pin       fraction of actuator_motors samples with any motor < 0.005 or > 0.995                 < 0.01
  achieved  fraction of control_allocator_status samples with torque_setpoint_achieved true      > 0.90
Exit status: 0 pass, 1 fail, 2 not computable. Thresholds from S44-S45 (limit cycle 0.2 rad/s, pin 38-46 %;
clean derived-G1 hover 0.007 rad/s, pin 0 %).
"""
import sys

import numpy as np

RATE_MAX = 0.02
PIN_MAX = 0.01
ACH_MIN = 0.90


def rate_rms(t, xyz):
    """Per-axis RMS of xyz minus its 1 s centred moving mean (t in s, irregular sampling allowed)."""
    out = np.zeros(3)
    for a in range(3):
        c = np.concatenate([[0.0], np.cumsum(xyz[:, a])])
        lo = np.searchsorted(t, t - 0.5)
        hi = np.searchsorted(t, t + 0.5)
        mean = (c[hi] - c[lo]) / np.maximum(hi - lo, 1)
        out[a] = np.sqrt(np.mean((xyz[:, a] - mean) ** 2))
    return out


def pin_fraction(ctrl):
    return float(np.mean(np.any((ctrl < 0.005) | (ctrl > 0.995), axis=1)))


def verdict(rms, pin, ach):
    fails = [f'rate RMS axis {a} {rms[a]:.4g} >= {RATE_MAX}' for a in range(3) if not rms[a] < RATE_MAX]
    if not pin < PIN_MAX:
        fails.append(f'motor pin {pin:.4g} >= {PIN_MAX}')
    if not ach > ACH_MIN:
        fails.append(f'torque achieved {ach:.4g} <= {ACH_MIN}')
    return fails


def main(argv):
    from pyulog import ULog
    log, out = argv[1], argv[2]
    opt = dict(zip(argv[3::2], argv[4::2]))
    delay = float(opt.get('--delay', 15))
    length = float(opt.get('--length', 30))
    ul = ULog(log)

    def get(name):
        return ul.get_dataset(name).data

    lines = [f'# Pre-test gate: `{log}`', '']
    try:
        ld, vs, av, am, ca = (get(n) for n in ('vehicle_land_detected', 'vehicle_status', 'vehicle_angular_velocity',
                                               'actuator_motors', 'control_allocator_status'))
    except Exception as e:  # missing topic
        lines.append(f'NOT COMPUTABLE: {e}')
        open(out, 'w').write('\n'.join(lines) + '\n')
        return 2
    t_ld = ld['timestamp'] * 1e-6
    air = np.flatnonzero(ld['landed'] == 0)
    if air.size == 0:
        lines.append('NOT COMPUTABLE: never airborne')
        open(out, 'w').write('\n'.join(lines) + '\n')
        return 2
    t0 = t_ld[air[0]] + delay
    t1 = t0 + length
    t_vs = vs['timestamp'] * 1e-6
    disarm = t_vs[(t_vs > t0) & (vs['arming_state'] != 2)]
    if disarm.size:
        t1 = min(t1, float(disarm[0]))
    t_av = av['timestamp'] * 1e-6
    m = (t_av >= t0) & (t_av < t1)
    xyz = np.column_stack([av[f'xyz[{i}]'] for i in range(3)])[m]
    t_am = am['timestamp'] * 1e-6
    ma = (t_am >= t0) & (t_am < t1)
    ctrl = np.column_stack([am[f'control[{i}]'] for i in range(4)])[ma]
    t_ca = ca['timestamp'] * 1e-6
    mc = (t_ca >= t0) & (t_ca < t1)
    if t1 - t0 < 5 or m.sum() < 100 or ma.sum() < 100 or mc.sum() < 10:
        lines.append(f'NOT COMPUTABLE: window [{t0:.3f}, {t1:.3f}) s too short or empty')
        open(out, 'w').write('\n'.join(lines) + '\n')
        return 2
    rms = rate_rms(t_av[m], xyz)
    pin = pin_fraction(ctrl)
    ach = float(np.mean(ca['torque_setpoint_achieved'][mc].astype(bool)))
    fails = verdict(rms, pin, ach)
    lines += [f'- window: [{t0:.3f}, {t1:.3f}) s since boot, first airborne + {delay} s',
              f'- samples: angular velocity {int(m.sum())}, motors {int(ma.sum())}, allocator {int(mc.sum())}',
              f'- rate RMS x/y/z [rad/s]: {rms[0]:.4g} / {rms[1]:.4g} / {rms[2]:.4g} (limit {RATE_MAX})',
              f'- motor pin fraction: {pin:.4g} (limit {PIN_MAX})',
              f'- torque setpoint achieved fraction: {ach:.4g} (limit {ACH_MIN})',
              '', 'PASS' if not fails else 'FAIL: ' + '; '.join(fails)]
    open(out, 'w').write('\n'.join(lines) + '\n')
    print(lines[-1])
    return 0 if not fails else 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv))
