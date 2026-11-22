#!/usr/bin/env python3
"""G5.8 moving (3 m/s) failsafe check, second key (independent implementation).

Per failsafe event (RC loss, data-link loss, offboard loss) read from a flight.ulg:
 (a) configured failsafe nav state entered <= 1 s after the firmware's own loss flag
     (failsafe_flags rise; timeout referenced to the firmware flag, GATES add.3 (ii));
 (b) excursion = max horizontal |ground truth - commanded position setpoint| over the window
     [failsafe entry, next nav_state change or 15 s] <= 1 m.

Usage: g58_moving_check_key2.py RUN_DIR [--out FILE] [--hover-align]
RUN_DIR holds flight.ulg (or pass a .ulg path).

Handling of NaN position setpoints (velocity-only trajectory_setpoint): the reference is
propagated by integrating the velocity setpoint from the previous reference sample; if no
earlier reference exists in the window it is anchored on ground truth at the first sample
(excursion 0 there by construction). The NaN fraction (time weighted, window) is reported
together with exc_valid, the excursion over samples with a valid position setpoint only.
Ground truth: sim_ground_truth x,y (NED), shifted by the ref lat/lon difference between
vehicle_local_position_groundtruth and vehicle_local_position. Residual hover offset is
reported; applied only with --hover-align.
"""
import argparse
import math
import os
import sys

import numpy as np

LIM_DELAY = 1.0
LIM_EXC = 1.0
WIN_MAX = 15.0
MIN_SPEED = 2.0  # below this the event is not a moving event
EARTH_R = 6371000.0
ACT_NAV = {0: None, 1: 4, 2: 5, 3: 18}  # NAV_RCL_ACT / NAV_DLL_ACT: off, hold, RTL, land
OBL_NAV = {0: 2, 1: 1, 2: 15, 3: 5, 4: 18, 5: 4}  # COM_OBL_RC_ACT
NAV_NAME = {0: 'manual', 1: 'altctl', 2: 'posctl', 4: 'hold', 5: 'rtl', 12: 'descend', 13: 'termination',
            14: 'offboard', 15: 'stab', 17: 'takeoff', 18: 'land'}
CHANNELS = [('rc_loss', 'rc', 'COM_RC_LOSS_T'), ('link_loss', 'dl', 'COM_DL_LOSS_T'),
            ('offboard_loss', 'ob', 'COM_OF_LOSS_T')]


def expected_nav(kind, nav_pre, params):
    """Expected nav_state for the configured action (None = action disabled / unknown)."""
    if kind == 'offboard_loss' or (kind == 'rc_loss' and nav_pre == 14):
        return OBL_NAV.get(int(params.get('COM_OBL_RC_ACT', 0)))
    key = 'NAV_RCL_ACT' if kind == 'rc_loss' else 'NAV_DLL_ACT'
    return ACT_NAV.get(int(params.get(key, 0)))


def reference_track(sp, t0, t1, gt_xy_at):
    """Reference xy at sp samples in [t0,t1]. Returns t, ref(N,2), isnan(N), dt weights."""
    m = (sp['t'] >= t0) & (sp['t'] <= t1)
    t = sp['t'][m]
    px, py, vx, vy = sp['px'][m], sp['py'][m], sp['vx'][m], sp['vy'][m]
    n = len(t)
    ref = np.full((n, 2), np.nan)
    isnan = ~(np.isfinite(px) & np.isfinite(py))
    cur = None
    for k in range(n):
        if not isnan[k]:
            cur = np.array([px[k], py[k]])
        else:
            dt = t[k] - t[k - 1] if k > 0 else 0.0
            if cur is None:
                cur = gt_xy_at(t[k:k + 1])[0].copy()
            elif np.isfinite(vx[k]) and np.isfinite(vy[k]):
                cur = cur + dt * np.array([vx[k], vy[k]])
        ref[k] = cur
    w = np.diff(np.append(t, t1)) if n else np.zeros(0)
    w = np.clip(w, 0, None)
    return t, ref, isnan, w


def analyze(d, params_at=None):
    """d: dict with status{t,nav,armed}, flags{t,rc,dl,ob}, sp{t,px,py,vx,vy}, gt{t,x,y,vx,vy}, params."""
    st, fl, sp, gt = d['status'], d['flags'], d['sp'], d['gt']
    params_of = d['params'] if callable(d['params']) else (lambda t: d['params'])
    gt_xy_at = lambda tt: np.column_stack([np.interp(tt, gt['t'], gt['x']), np.interp(tt, gt['t'], gt['y'])])
    out = []
    for kind, key, pname in CHANNELS:
        f = fl[key].astype(int)
        for j in range(1, len(f)):
            if not (f[j] == 1 and f[j - 1] == 0):
                continue
            t_lo, t_hi = fl['t'][j - 1], fl['t'][j]  # firmware flag rose in (t_lo, t_hi]
            params = params_of(t_hi)
            r = {'kind': kind, 'ref_t': t_hi, 'ref_lo': t_lo, 'T_loss': params.get(pname), 'params': params}
            i_arm = np.searchsorted(st['t'], t_hi, side='right') - 1
            if i_arm < 0 or not st['armed'][i_arm]:
                continue
            i_pre = max(np.searchsorted(st['t'], t_lo, side='right') - 1, 0)
            nav_pre = int(st['nav'][i_pre])
            v = gt_xy_at  # noqa
            vxy = math.hypot(np.interp(t_hi, gt['t'], gt['vx']), np.interp(t_hi, gt['t'], gt['vy']))
            r['speed'] = vxy
            r['nav_pre'] = nav_pre
            r['exp_nav'] = expected_nav(kind, nav_pre, params)
            # entry: first nav change away from nav_pre at or after the last low flag sample
            ent = None
            for i in range(i_pre + 1, len(st['t'])):
                if st['t'][i] >= t_lo and st['nav'][i] != nav_pre:
                    ent = i
                    break
            if ent is None or st['t'][ent] > t_hi + WIN_MAX:
                r.update(entry_t=None, entry_nav=None, delay=None, delay_max=None, nan_frac=None, exc=None,
                         exc_valid=None, verdict='FAIL', why='no nav change after loss flag')
                out.append(r)
                continue
            te = st['t'][ent]
            nav_e = int(st['nav'][ent])
            nxt = [st['t'][i] for i in range(ent + 1, len(st['t'])) if st['nav'][i] != nav_e]
            tend = min(te + WIN_MAX, nxt[0] if nxt else te + WIN_MAX, sp['t'][-1])
            r.update(entry_t=te, entry_nav=nav_e, delay=te - t_hi, delay_max=te - t_lo, win_end=tend)
            tt, ref, isn, w = reference_track(sp, te, tend, gt_xy_at)
            if len(tt) == 0:
                r.update(nan_frac=None, exc=None, exc_valid=None, verdict='FAIL', why='no setpoint in window')
                out.append(r)
                continue
            dev = np.hypot(*(gt_xy_at(tt) - ref).T)
            tot = w.sum()
            r['nan_frac'] = float(w[isn].sum() / tot) if tot > 0 else float(isn.mean())
            r['exc'] = float(dev.max())
            r['exc_valid'] = float(dev[~isn].max()) if (~isn).any() else None
            ok_a = nav_e == r['exp_nav'] and r['delay'] <= LIM_DELAY
            ok_b = r['exc'] <= LIM_EXC
            why = []
            if nav_e != r['exp_nav']:
                why.append('entered %s expected %s' % (NAV_NAME.get(nav_e, nav_e), NAV_NAME.get(r['exp_nav'], r['exp_nav'])))
            if r['delay'] > LIM_DELAY:
                why.append('delay %.2f > %.1f' % (r['delay'], LIM_DELAY))
            if not ok_b:
                why.append('excursion %.2f > %.1f' % (r['exc'], LIM_EXC))
            if vxy < MIN_SPEED:
                r['verdict'] = 'SKIP'
                why.insert(0, 'onset speed %.2f < %.1f m/s, not a moving event' % (vxy, MIN_SPEED))
            else:
                r['verdict'] = 'PASS' if ok_a and ok_b else 'FAIL'
            r['why'] = '; '.join(why)
            out.append(r)
    out.sort(key=lambda r: r['ref_t'])
    return out


def _params_at(u, t_us):
    p = dict(u.initial_parameters)
    for tp, n, val in u.changed_parameters:
        if tp <= t_us:
            p[n] = val
    return p


def _ll_offset(lat, lon, lat0, lon0):
    return (math.radians(lat - lat0) * EARTH_R, math.radians(lon - lon0) * EARTH_R * math.cos(math.radians(lat0)))


def load(path, hover_align=False):
    from pyulog import ULog
    u = ULog(path)
    g = lambda n: u.get_dataset(n).data
    vs, ff, ts, sg = g('vehicle_status'), g('failsafe_flags'), g('trajectory_setpoint'), g('sim_ground_truth')
    lp = g('vehicle_local_position')
    d = {}
    d['status'] = dict(t=vs['timestamp'] / 1e6, nav=vs['nav_state'], armed=vs['arming_state'] == 2)
    d['flags'] = dict(t=ff['timestamp'] / 1e6, rc=ff['manual_control_signal_lost'], dl=ff['gcs_connection_lost'],
                      ob=ff['offboard_control_signal_lost'])
    d['sp'] = dict(t=ts['timestamp'] / 1e6, px=ts['position[0]'], py=ts['position[1]'], vx=ts['velocity[0]'],
                   vy=ts['velocity[1]'])
    ox = oy = 0.0
    try:
        lg = g('vehicle_local_position_groundtruth')
        ox, oy = _ll_offset(lg['ref_lat'][0], lg['ref_lon'][0], lp['ref_lat'][0], lp['ref_lon'][0])
    except KeyError:
        pass
    gx, gy = sg['x'] + ox, sg['y'] + oy
    tg = sg['timestamp'] / 1e6
    # residual offset to the estimator in the slowest in-air second before the first event (diagnostic)
    tl = lp['timestamp'] / 1e6
    ex = np.interp(tg, tl, lp['x'])
    ey = np.interp(tg, tl, lp['y'])
    sp_est = np.hypot(sg['vx'], sg['vy'])
    off = np.where(d['status']['nav'] == 14)[0]
    ref_t = d['status']['t'][off[0]] if len(off) else tg[-1]
    m = (tg < ref_t) & (sp_est < 0.3) & (sg['z'] < -1.0)
    resid = (float(np.median(gx[m] - ex[m])), float(np.median(gy[m] - ey[m]))) if m.sum() > 100 else None
    if hover_align and resid:
        gx, gy = gx - resid[0], gy - resid[1]
    d['gt'] = dict(t=tg, x=gx, y=gy, vx=sg['vx'], vy=sg['vy'])
    d['params'] = lambda t: _params_at(u, int(t * 1e6))
    d['info'] = dict(ref_offset_m=(ox, oy), hover_resid_m=resid)
    return d


def fmt(res, d=None):
    lines = []
    for r in res:
        if r.get('entry_t') is None:
            lines.append('%s %s ref_t=%.3f: %s' % (r['verdict'], r['kind'], r['ref_t'], r.get('why')))
            continue
        ex = '%.3f' % r['exc_valid'] if r['exc_valid'] is not None else 'n/a'
        lines.append('%s %s ref_t=%.3f entry=%s@%.3f delay=%.3f s (<=%.3f s bound) NaN=%.1f%% v_onset=%.2f m/s '
                     'exc=%.3f m (valid-only %s m)%s' % (
                         r['verdict'], r['kind'], r['ref_t'], NAV_NAME.get(r['entry_nav'], r['entry_nav']),
                         r['entry_t'], r['delay'], r['delay_max'], 100 * r['nan_frac'], r['speed'], r['exc'], ex,
                         ('  [' + r['why'] + ']') if r.get('why') else ''))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir')
    ap.add_argument('--out')
    ap.add_argument('--hover-align', action='store_true')
    a = ap.parse_args(argv)
    path = a.run_dir if a.run_dir.endswith('.ulg') else os.path.join(a.run_dir, 'flight.ulg')
    d = load(path, a.hover_align)
    res = analyze(d)
    lines = fmt(res)
    p = res[-1]['params'] if res else {}
    lines.append('params (last event): ' + ' '.join('%s=%s' % (k, p.get(k)) for k in (
        'COM_RC_LOSS_T', 'COM_DL_LOSS_T', 'COM_OF_LOSS_T', 'NAV_RCL_ACT', 'NAV_DLL_ACT', 'COM_OBL_RC_ACT')))
    lines.append('gt frame: ref offset %s m, residual hover offset %s m (applied: %s)' % (
        d['info']['ref_offset_m'], d['info']['hover_resid_m'], a.hover_align))
    txt = '\n'.join(lines)
    print(txt)
    if a.out:
        with open(a.out, 'w') as f:
            f.write(txt + '\n')
    return 0 if all(r['verdict'] in ('PASS', 'SKIP') for r in res) and res else 1


if __name__ == '__main__':
    sys.exit(main())
