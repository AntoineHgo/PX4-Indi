#!/usr/bin/env python3
"""Independent second key for gate rows G5.5 (offboard trajectories o1-o7, offb_vel_step) and G5.7 (mode_switch10).

Usage: g55_g57_key2.py <g55|g57> <flight_dir>...   (each dir holds flight.ulg and run.json)

Spec: indi_flight/GATES.md (shared definitions, G5.5 exact test, G5.7 exact test). Truth = *_groundtruth topics, ULog
timestamps (us -> s). Readings of ambiguous text are marked READING in the comments and listed in key2_g55_g57.md.
"""
import json
import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------- pure functions (unit-tested)

H_LIM, V_LIM = 0.5, 0.3                       # G5.5 trajectory RMS limits [m]
VS_RMS_LIM, VS_END_LIM, VS_DZ_LIM = 0.2, 0.1, 0.3
THR_LIM_FRAC, TILT_LIM_DEG = 0.20, 5.0        # G5.7
LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M, LOC_EXC_M = 60.0, 0.2, 2.0, 5.0


def phase(traj, t):
    """Phase phi(t): rate ramps 0->w as smoothstep-like poly u^3-u^4/2 over ramp_s, cruises, ramps down; total phase
    laps*2pi (scenario definition)."""
    w, tr, laps = traj['w'], traj['ramp_s'], traj['laps']
    tc = 2 * math.pi * laps / w - tr
    if t <= 0:
        return 0.0
    if t < tr:
        u = t / tr
        return w * tr * (u ** 3 - u ** 4 / 2)
    if t < tr + tc:
        return w * tr / 2 + w * (t - tr)
    if t < 2 * tr + tc:
        u = (2 * tr + tc - t) / tr
        return 2 * math.pi * laps - w * tr * (u ** 3 - u ** 4 / 2)
    return 2 * math.pi * laps


def ref_offset(traj, t):
    """NED offset [x, y, z] from the hold position at time t since trajectory start."""
    p = phase(traj, t)
    s = traj['shape']
    if s == 'lemniscate':
        return np.array([traj['ax'] * math.sin(p), traj['ay'] * math.sin(2 * p), 0.0])
    if s == 'circle':
        r = traj['r']
        return np.array([r * (math.cos(p) - 1.0), r * math.sin(p), -traj['z_amp'] * math.sin(p)])
    if s == 'zmulti':
        return np.array([0.0, 0.0, -sum(a * math.sin(k * p) for k, a in zip(traj['harm'], traj['amps']))])
    raise ValueError(s)


def track_rms(t, pos, hold, traj, t0, dur):
    """Horizontal (2-D distance) and vertical RMS of truth pos (N,3 NED) vs hold + analytic offset over [t0, t0+dur]."""
    m = (t >= t0) & (t <= t0 + dur)
    ref = np.array([hold + ref_offset(traj, tt - t0) for tt in t[m]])
    e = pos[m] - ref
    return math.sqrt(np.mean(e[:, 0] ** 2 + e[:, 1] ** 2)), math.sqrt(np.mean(e[:, 2] ** 2)), e


def vel_step(t, vx, z, t_step, t_hold, t_end):
    """offb_vel_step metrics. step = [t_step, t_hold], hold = [t_hold, t_end]. dz relative to mean z over the 1 s before
    t_step (READING: 'dz' = height change from the pre-step hold)."""
    m = (t >= t_hold - 3.0) & (t < t_hold)
    rms = math.sqrt(np.mean((vx[m] - 2.0) ** 2))
    end = abs(float(np.interp(t_end, t, vx)))
    z0 = z[(t >= t_step - 1.0) & (t < t_step)].mean()
    mm = (t >= t_step) & (t <= t_end)
    dz = float(np.max(np.abs(z[mm] - z0)))
    return rms, end, dz


def body_z(q):
    """World-frame body z axis of quaternions (N,4 w,x,y,z, body->world)."""
    w, x, y, zq = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return np.stack([2 * (x * zq + w * y), 2 * (y * zq - w * x), 1 - 2 * (x * x + y * y)], axis=1)


def tilt_deg(q):
    return np.degrees(np.arccos(np.clip(body_z(q)[:, 2], -1, 1)))


def edge_metrics(te, thr_t, thr, hover, q_t, q, qd_t, qd):
    """One mode edge at time te: thrust step as fraction of hover, max attitude error [deg] over [te+0.3, te+1.0]."""
    a = thr[(thr_t >= te) & (thr_t < te + 0.1)].mean()
    b = thr[(thr_t >= te - 0.1) & (thr_t < te)].mean()
    step = abs(a - b) / hover
    m = (q_t >= te + 0.3) & (q_t <= te + 1.0)
    idx = np.clip(np.searchsorted(qd_t, q_t[m], side='right') - 1, 0, len(qd_t) - 1)  # zero-order hold setpoint
    c = np.sum(body_z(q[m]) * body_z(qd[idx]), axis=1)
    return step, float(np.degrees(np.arccos(np.clip(c, -1, 1))).max())


def loc_tilt(t, q):
    """True if tilt > 60 deg for more than 0.2 s continuously."""
    bad = tilt_deg(q) > LOC_TILT_DEG
    run0 = None
    for i, b in enumerate(bad):
        if b and run0 is None:
            run0 = t[i]
        if not b:
            run0 = None
        if b and t[i] - run0 > LOC_TILT_S:
            return True
    return False


def line(name, val, lim, ok, unit=''):
    return f"  {name:28s} {val:10.4f} {unit:4s} limit {lim}  {'PASS' if ok else 'FAIL'}"


# ---------------------------------------------------------------- log access

def load(d):
    from pyulog import ULog
    names = ['vehicle_local_position_groundtruth', 'vehicle_attitude_groundtruth', 'vehicle_status',
             'vehicle_thrust_setpoint', 'vehicle_attitude_setpoint']
    u = ULog(os.path.join(d, 'flight.ulg'), message_name_filter_list=names)
    out = {}
    for n in names:
        try:
            out[n] = u.get_dataset(n).data
        except (IndexError, KeyError, ValueError):
            pass
    return out


def tsec(dd):
    return dd['timestamp'].astype(np.float64) * 1e-6


def truth(L):
    lp = L['vehicle_local_position_groundtruth']
    at = L['vehicle_attitude_groundtruth']
    t = tsec(lp)
    pos = np.stack([lp['x'], lp['y'], lp['z']], axis=1).astype(np.float64)
    vel = np.stack([lp['vx'], lp['vy'], lp['vz']], axis=1).astype(np.float64)
    q = np.stack([at['q[%d]' % i] for i in range(4)], axis=1).astype(np.float64)
    return t, pos, vel, tsec(at), q


def loc_checks(t, pos, qt, q, w0, w1):
    """LOC list over [w0, w1] (airborne window, truth)."""
    m = (t >= w0) & (t <= w1)
    why = []
    if not np.all(np.isfinite(pos[m])):
        why.append('nan')
    z0 = pos[(t >= w0 - 1) & (t < w0), 2].mean()
    if np.max(pos[m, 2] - z0) > LOC_DROP_M:   # NED z grows when going down
        why.append('height_drop')
    mq = (qt >= w0) & (qt <= w1)
    if loc_tilt(qt[mq], q[mq]):
        why.append('tilt')
    return why


# ---------------------------------------------------------------- rows

def g55(d):
    run = json.load(open(os.path.join(d, 'run.json')))
    L = load(d)
    t, pos, vel, qt, q = truth(L)
    ev = {e['name']: e for e in run['events']}
    out = []
    ok_all = True
    if run['scenario'] == 'offb_vel_step':
        ts = ev['vstep']['t_us'] * 1e-6
        th = ev['vhold']['t_us'] * 1e-6
        te = th + ev['vhold']['dur_s']
        rms, end, dz = vel_step(t, vel[:, 0], pos[:, 2], ts, th, te)
        loc = loc_checks(t, pos, qt, q, ev['settle']['t_us'] * 1e-6, te)
        for n, v, lim, u in (('rms(vx-2) last 3 s', rms, VS_RMS_LIM, 'm/s'), ('|vx| end of hold', end, VS_END_LIM, 'm/s'),
                             ('max|dz|', dz, VS_DZ_LIM, 'm')):
            ok = v <= lim
            ok_all &= ok
            out.append(line(n, v, f'<= {lim}', ok, u))
    else:
        tr = run['trajectory']
        t0 = tr['t0_us'] * 1e-6
        hold = np.array(run['hold_pos_ned'], dtype=float)
        h, v, e = track_rms(t, pos, hold, tr, t0, tr['dur_s'])
        w0 = ev['settle']['t_us'] * 1e-6
        w1 = t0 + tr['dur_s'] + ev['hold']['dur_s']
        loc = loc_checks(t, pos, qt, q, w0, w1)
        if np.max(np.hypot(e[:, 0], e[:, 1])) > LOC_EXC_M:  # truth horizontal distance to the analytic reference
            loc.append('excursion')
        for n, val, lim in (('horizontal RMS', h, H_LIM), ('vertical RMS', v, V_LIM)):
            ok = val <= lim
            ok_all &= ok
            out.append(line(n, val, f'<= {lim}', ok, 'm'))
        out.append(f"  (max horizontal error {np.max(np.hypot(e[:, 0], e[:, 1])):.3f} m, max vertical {np.max(np.abs(e[:, 2])):.3f} m)")
    out.append(f"  LOC {'none' if not loc else loc}  {'PASS' if not loc else 'FAIL'}")
    ok_all &= not loc
    return ok_all, out


NAV_NAMES = {2: 'posctl', 1: 'altctl', 15: 'stab', 4: 'hold'}


def g57(d, validity='leaveP'):
    run = json.load(open(os.path.join(d, 'run.json')))
    L = load(d)
    t, pos, vel, qt, q = truth(L)
    vs = L['vehicle_status']
    vst, nav = tsec(vs), vs['nav_state']
    w0 = run['t_window_start_us'] * 1e-6
    w1 = run['t_window_end_us'] * 1e-6
    hover = run['hover_thr_used']
    # edges = logged nav_state changes inside the window
    ch = np.where(np.diff(nav) != 0)[0] + 1
    ch = [i for i in ch if w0 <= vst[i] <= w1 + 1.0]
    edges = [(vst[i], int(nav[i - 1]), int(nav[i])) for i in ch]
    th = L['vehicle_thrust_setpoint']
    thr_t, thr = tsec(th), -th['xyz[2]'].astype(np.float64)
    sp = L['vehicle_attitude_setpoint']
    qd = np.stack([sp['q_d[%d]' % i] for i in range(4)], axis=1).astype(np.float64)
    qd_t = tsec(sp)
    out, ok_all = [], True
    expect = [(2, 1), (1, 2), (2, 15), (15, 2), (2, 4), (4, 2), (2, 1), (1, 15), (15, 4), (4, 2)]
    got = [(a, b) for _, a, b in edges]
    ok_e = got == expect
    out.append(f"  edges {len(edges)} {'PASS' if ok_e else 'FAIL'} (expected order {'ok' if ok_e else 'MISMATCH ' + str(got)})")
    ok_all &= ok_e
    speeds = []
    worst_thr, worst_tilt = 0.0, 0.0
    for te, a, b in edges:
        sp_h = float(np.hypot(np.interp(te, t, vel[:, 0]), np.interp(te, t, vel[:, 1])))
        step, tilt = edge_metrics(te, thr_t, thr, hover, qt, q, qd_t, qd)
        speeds.append(sp_h)
        worst_thr, worst_tilt = max(worst_thr, step), max(worst_tilt, tilt)
        out.append(f"    {NAV_NAMES.get(a, a)}>{NAV_NAMES.get(b, b)} t={te - w0:6.2f}s v={sp_h:4.2f} thr={100 * step:5.2f}% tilt={tilt:5.2f}deg")
    if validity == 'leaveP':
        lv = [s for s, (_, a, b) in zip(speeds, edges) if a == 2]
        okv = len(lv) == 4 and all(s >= 1.5 for s in lv)
        out.append(f"  validity (AMENDED leaveP: speed >= 1.5 at 4 edges leaving posctl) min {min(lv) if lv else float('nan'):.2f} {'VALID' if okv else 'INVALID'}")
    ok_all &= okv
    ok1 = worst_thr <= THR_LIM_FRAC
    ok2 = worst_tilt <= TILT_LIM_DEG
    out.append(line('max thrust step / hover', 100 * worst_thr, '<= 20 %', ok1, '%'))
    out.append(line('max attitude jump', worst_tilt, '<= 5 deg', ok2, 'deg'))
    loc = loc_checks(t, pos, qt, q, w0, w1)
    armed = vs['arming_state'][(vst >= w0) & (vst <= w1)]
    if np.any(armed != 2):
        loc.append('disarmed')
    out.append(f"  LOC {'none' if not loc else loc}  {'PASS' if not loc else 'FAIL'}")
    ok_all &= ok1 and ok2 and not loc
    return ok_all, out


def main(argv):
    if len(argv) < 3 or argv[1] not in ('g55', 'g57'):
        print(__doc__)
        return 2
    allok = True
    for d in argv[2:]:
        d = d.rstrip('/')
        ok, out = (g55 if argv[1] == 'g55' else g57)(d)
        print(f"{os.path.basename(d)} {argv[1].upper()} {'PASS' if ok else 'FAIL'}")
        print('\n'.join(out))
        allok &= ok
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
