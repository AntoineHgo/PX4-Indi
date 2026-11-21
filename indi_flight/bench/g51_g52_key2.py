#!/usr/bin/env python3
"""Independent second key for gate rows G5.1 and G5.2 (GATES.md S136 / S138 exact tests).

usage: g51_g52_key2.py <g51|g52> <flight_dir>...

Written from the GATES text only. Reading choices where the text is ambiguous:
 R1 acro RMS pools the samples of the three plateaus into one RMS; the 0 plateau is
    [edge+0.1, min(edge+1.0, next stick change)].
 R2 stick edges = times (sticks.csv t_sim_us, the applied stick log) where the channel
    leaves/returns to its resting value (|v - rest| > 50 counts); sim time = ulog time.
 R3 commanded acro rate = stick/1000 * 100 deg/s; MAVLink x (pitch) forward -> nose
    down -> q negative (PX4 mc_rate_control uses -pitch); roll y -> +p; yaw r -> +r.
 R4 truth body rate = vehicle_angular_velocity_groundtruth xyz; tilt from
    vehicle_attitude_groundtruth, tilt = acos(1 - 2(qx^2+qy^2)); stab tilt gate is the max.
 R5 LOC (G5.1 and G5.2 text: ground contact, tilt<80, NaN; the other shared LOC items are printed as info) over [t_window_start_us, t_window_end_us] of run.json: tilt > 60 deg > 0.2 s,
    height < start-2.0 m, ground contact = height < 0.3 m, NaN in truth, horizontal
    excursion > 5 m from the window-start position; G5.1 also tilt < 80 deg.
    (controller fault flag is not checked here.)
 R6 G5.2: z axis = up height; x axis = horizontal projection on the start->final
    direction; release = stick return to rest; centred window = [release, release+6];
    final = mean over [release+5, release+6]; settle = (last sample with
    |s-final|>2% d) - release (0 if none).
"""
import sys, os, json, csv, math
import numpy as np

ACRO_MAX = 100.0  # deg/s at stick 1.0
LIM = dict(acro_rms=10.0, stab_tilt=3.0, stab_yawrate=10.0, tilt_loc=80.0,
           z_os=0.3, x_os=0.5, settle=4.0, z_dmin=1.0, x_dmin=2.0)


# ---------------------------------------------------------------- core functions
def plateau_rms(t, err, windows):
    """RMS of err over the union of [a,b] windows (pooled samples)."""
    t = np.asarray(t); err = np.asarray(err)
    m = np.zeros(len(t), bool)
    for a, b in windows:
        m |= (t >= a) & (t < b)  # half-open: the sample at the next edge already carries the new command
    if not m.any():
        return float('nan')
    return float(np.sqrt(np.mean(err[m] ** 2)))


def step_metrics(t, s, t_rel, d, win=6.0, band=0.02):
    """s = truth coordinate along the step direction, in units where final = d.
    Returns (overshoot, settle) after the release edge t_rel."""
    t = np.asarray(t); s = np.asarray(s)
    m = (t >= t_rel) & (t <= t_rel + win)
    tt, ss = t[m], s[m]
    os_ = max(0.0, float(np.max(ss - d)))
    out = np.abs(ss - d) > band * d
    if out.any():
        settle = float(tt[np.nonzero(out)[0][-1]] - t_rel)
    else:
        settle = 0.0
    return os_, settle


def loc_check(t, tilt_deg, height, xy, t0, t1, tilt_hard=None):
    """Returns list of LOC reasons (empty = none)."""
    m = (t >= t0) & (t <= t1)
    tt, ti, h, p = t[m], tilt_deg[m], height[m], xy[m]
    why = []
    if not (np.isfinite(ti).all() and np.isfinite(h).all() and np.isfinite(p).all()):
        why.append('nan')
    ti = np.nan_to_num(ti, nan=0.0)
    # tilt > 60 deg for > 0.2 s (longest continuous run)
    run = 0.0; best = 0.0; last = None
    for k in range(len(tt)):
        if ti[k] > 60.0:
            run = (tt[k] - tt[k - 1]) + run if k > 0 and ti[k - 1] > 60.0 else 0.0
            best = max(best, run)
        else:
            run = 0.0
    if best > 0.2:
        why.append('tilt>60 for %.2fs' % best)
    if tilt_hard is not None and ti.max() >= tilt_hard:
        why.append('tilt>=%g (%.1f)' % (tilt_hard, ti.max()))
    if h.min() < h[0] - 2.0:
        why.append('height drop %.2f m' % (h[0] - h.min()))
    if h.min() < 0.3:
        why.append('ground contact (h %.2f m)' % h.min())
    exc = np.hypot(p[:, 0] - p[0, 0], p[:, 1] - p[0, 1]).max()
    if exc > 5.0:
        why.append('excursion %.2f m' % exc)
    return why


# ---------------------------------------------------------------- data loading
def load_flight(d):
    from pyulog import ULog
    run = json.load(open(os.path.join(d, 'run.json')))
    top = ['vehicle_local_position_groundtruth', 'vehicle_attitude_groundtruth',
           'vehicle_angular_velocity_groundtruth']
    u = ULog(os.path.join(d, 'flight.ulg'), message_name_filter_list=top)
    g = {}
    for n in top:
        ds = u.get_dataset(n).data
        g[n] = ds
    lp = g[top[0]]; at = g[top[1]]; av = g[top[2]]
    T = lp['timestamp'] * 1e-6
    ta = at['timestamp'] * 1e-6
    tv = av['timestamp'] * 1e-6
    qw, qx, qy, qz = (at['q[%d]' % i] for i in range(4))
    tilt_a = np.degrees(np.arccos(np.clip(1 - 2 * (qx ** 2 + qy ** 2), -1, 1)))
    tilt = np.interp(T, ta, tilt_a)
    rates = np.degrees(np.stack([np.interp(T, tv, av['xyz[%d]' % i]) for i in range(3)], 1))
    pos = np.stack([lp['x'], lp['y'], lp['z']], 1)
    sticks = list(csv.DictReader(open(os.path.join(d, run['sticks_csv']))))
    ts = np.array([int(r['t_sim_us']) for r in sticks]) * 1e-6
    ch = {k: np.array([float(r[k]) for r in sticks]) for k in 'xyzr'}
    return dict(run=run, t=T, tilt=tilt, rates=rates, pos=pos, ts=ts, ch=ch,
                w0=run['t_window_start_us'] * 1e-6, w1=run['t_window_end_us'] * 1e-6)


def active_segments(ts, v, rest, thr=50.0):
    """[(t_on, t_off, value_at_on)] of the channel being away from rest; a change of
    value by > thr while active starts a new segment (edge = first applied row with the
    changed value)."""
    act = np.abs(v - rest) > thr
    segs = []; i = 0; n = len(ts)
    while i < n:
        if act[i]:
            j = i
            while j + 1 < n and act[j + 1] and abs(v[j + 1] - v[i]) <= thr:
                j += 1
            t_off = ts[j + 1] if j + 1 < n else ts[j]
            segs.append((ts[i], t_off, v[i] - rest))
            i = j + 1
        else:
            i += 1
    return segs


def stick_at(ts, v, tq):
    idx = np.clip(np.searchsorted(ts, tq, side='right') - 1, 0, len(ts) - 1)
    return v[idx]


def doublets(F, key, rest=0.0):
    """Group active segments of channel into doublets (+A, -A): returns list of
    (e1, e2, e3, A) where e3 = release."""
    segs = active_segments(F['ts'], F['ch'][key], rest)
    out = []
    k = 0
    while k + 1 < len(segs):
        a, b = segs[k], segs[k + 1]
        if abs(b[0] - a[1]) < 1e-3:
            out.append((a[0], b[0], b[1], a[2]))
            k += 2
        else:
            k += 1
    return out


def next_change(F, t_after):
    """First time after t_after at which roll/pitch/yaw sticks change from rest."""
    best = None
    for key in 'xyr':
        for s in active_segments(F['ts'], F['ch'][key], 0.0):
            if s[0] > t_after + 1e-3:
                best = s[0] if best is None else min(best, s[0])
    return best


# ---------------------------------------------------------------- rows
def run_loc(F, hard):
    """G5.1/G5.2 LOC as stated in the row text: no ground contact, truth tilt < 80 deg
    (plus NaN). The shared-definition extras (tilt>60 for 0.2 s, height drop, 5 m
    excursion) are returned separately as info: acro/stab have no position loop."""
    t = F['t']; h = -F['pos'][:, 2]
    allw = loc_check(t, F['tilt'], h, F['pos'][:, :2], F['w0'], F['w1'], tilt_hard=hard)
    gate = [w for w in allw if w.startswith(('nan', 'tilt>=', 'ground'))]
    extra = [w for w in allw if w not in gate]
    return gate, extra


def row_g51(d):
    F = load_flight(d)
    mode = F['run']['stick']['mode']
    res = []  # (name, value, limit_str, ok)
    t, rates, tilt = F['t'], F['rates'], F['tilt']
    axes = [('roll', 'y', 0, +1.0), ('pitch', 'x', 1, -1.0), ('yaw', 'r', 2, +1.0)]
    info = []
    for name, key, ri, sign in axes:
        dbl = doublets(F, key)
        if not dbl:
            res.append((name + ' doublet found', 0, '1', False)); continue
        e1, e2, e3, A = dbl[0]
        if mode == 'acro':
            nxt = next_change(F, e3)
            end0 = e3 + 1.0 if nxt is None else min(e3 + 1.0, nxt)
            wins = [(e1 + 0.1, e2), (e2 + 0.1, e3), (e3 + 0.1, end0)]
            cmd = sign * stick_at(F['ts'], F['ch'][key], t) / 1000.0 * ACRO_MAX
            r = plateau_rms(t, cmd - rates[:, ri], wins)
            res.append(('%s RMS err [deg/s]' % name, r, '<= %g' % LIM['acro_rms'], r <= LIM['acro_rms']))
            # reported, not gated: rise time to 90 % and overshoot of the first edge
            m = (t >= e1) & (t <= e2)
            tgt = sign * A / 1000.0 * ACRO_MAX
            y = rates[m, ri] / tgt
            t90 = float(t[m][np.argmax(y >= 0.9)] - e1) if (y >= 0.9).any() else float('nan')
            info.append('%s t90 %.3f s ovs %.1f %%' % (name, t90, max(0.0, (y.max() - 1) * 100)))
        else:
            ws, we = e3 + 1.0, e3 + 2.5
            m = (t >= ws) & (t <= we)
            mx = float(tilt[m].max())
            res.append(('%s tilt max [deg] (release+1..2.5)' % name, mx, '<= %g' % LIM['stab_tilt'], mx <= LIM['stab_tilt']))
            if name == 'yaw':
                yr = float(np.abs(rates[m, 2]).max())
                res.append(('yaw |r| max [deg/s]', yr, '<= %g' % LIM['stab_yawrate'], yr <= LIM['stab_yawrate']))
    why, extra = run_loc(F, LIM['tilt_loc'])
    info.append('shared-LOC extras (not gated here): %s' % (extra or 'none'))
    res.append(('LOC (tilt<80, none)', len(why), '== 0' + (' [' + '; '.join(why) + ']' if why else ''), not why))
    tm = (t >= F['w0']) & (t <= F['w1'])
    res.append(('window tilt max [deg] (info)', float(tilt[tm].max()), 'info', True))
    return F, res, info


def row_g52(d):
    F = load_flight(d)
    t = F['t']; pos = F['pos']; res = []; info = []; invalid = []
    up = -pos[:, 2]

    def at(tq, arr):
        return np.array([np.interp(tq, t, arr[:, i]) for i in range(arr.shape[1])]) if arr.ndim > 1 else float(np.interp(tq, t, arr))

    # z step (throttle stick away from its rest value, first sample)
    zrest = F['ch']['z'][0]
    zs = active_segments(F['ts'], F['ch']['z'], zrest)
    if not zs:
        res.append(('z step found', 0, '1', False))
    else:
        e, r_, _ = zs[0]
        start = at(e, up)
        fm = (t >= r_ + 5.0) & (t <= r_ + 6.0)
        final = float(up[fm].mean())
        dd = abs(final - start); sg = 1.0 if final >= start else -1.0
        s = (up - start) * sg
        os_, st = step_metrics(t, s, r_, dd)
        res.append(('z step size d [m] (valid >= %g)' % LIM['z_dmin'], dd, '>= %g' % LIM['z_dmin'], dd >= LIM['z_dmin']))
        if dd < LIM['z_dmin']:
            invalid.append('z d')
        res.append(('z overshoot [m]', os_, '<= %g' % LIM['z_os'], os_ <= LIM['z_os']))
        res.append(('z settle [s]', st, '<= %g' % LIM['settle'], st <= LIM['settle']))
        m = (t >= e) & (t <= r_ + 6.0)
        info.append('z-step off-axis xy max %.2f m' % np.hypot(pos[m, 0] - pos[m, 0][0], pos[m, 1] - pos[m, 1][0]).max())
    # x step (only if present)
    xs = active_segments(F['ts'], F['ch']['x'], 0.0)
    mode = F['run']['stick']['mode']
    if xs:
        e, r_, _ = xs[0]
        start = at(e, pos[:, :2])
        fm = (t >= r_ + 5.0) & (t <= r_ + 6.0)
        final = pos[fm, :2].mean(0)
        v = final - start; dd = float(np.hypot(*v)); u = v / dd
        s = (pos[:, :2] - start) @ u
        os_, st = step_metrics(t, s, r_, dd)
        res.append(('x step size d [m] (valid >= %g)' % LIM['x_dmin'], dd, '>= %g' % LIM['x_dmin'], dd >= LIM['x_dmin']))
        if dd < LIM['x_dmin']:
            invalid.append('x d')
        res.append(('x overshoot [m]', os_, '<= %g' % LIM['x_os'], os_ <= LIM['x_os']))
        res.append(('x settle [s]', st, '<= %g' % LIM['settle'], st <= LIM['settle']))
        m = (t >= e) & (t <= r_ + 6.0)
        lat = (pos[m, :2] - start) @ np.array([-u[1], u[0]])
        info.append('x-step y off-axis max %.2f m, z excursion max %.2f m' % (np.abs(lat).max(), np.abs(up[m] - up[m][0]).max()))
    elif mode == 'posctl':
        res.append(('x step found', 0, '1', False))
    why, extra = run_loc(F, LIM['tilt_loc'])
    info.append('shared-LOC extras (not gated here): %s' % (extra or 'none'))
    res.append(('LOC (none)', len(why), '== 0' + (' [' + '; '.join(why) + ']' if why else ''), not why))
    return F, res, info, invalid


def report(row, d):
    if row == 'g51':
        F, res, info = row_g51(d); invalid = []
    else:
        F, res, info, invalid = row_g52(d)
    name = os.path.basename(os.path.normpath(d))
    print('== %s (%s, mode %s)' % (name, row.upper(), F['run']['stick']['mode']))
    for n, v, lim, ok in res:
        print('  %-42s %10.3f  limit %-14s %s' % (n, v, lim, 'PASS' if ok else 'FAIL'))
    for i in info:
        print('  info: ' + i)
    if invalid:
        verdict = 'INVALID(%s)' % ','.join(invalid)
    else:
        verdict = 'PASS' if all(r[3] for r in res) else 'FAIL'
    print('  VERDICT %s %s' % (row.upper(), verdict))
    return verdict


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('g51', 'g52'):
        sys.exit(__doc__)
    for d in sys.argv[2:]:
        report(sys.argv[1], d)
