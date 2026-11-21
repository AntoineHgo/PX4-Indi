import json
import os
import numpy as np
from pyulog import ULog

# Read-only analysis of the a_ff -> omega_ff chain around AUTO_LAND entry.
REPO = os.environ.get('PX4_INDI_REPO', '/home/ahugo/Documents/Drotek/Codes/PX4-Indi')
RES = REPO + '/indi_flight/results/g4_jff_s172'
RUNS = ['hover_harsh_s3', 'hover_quiet_s3']


def get(u, name):
    for x in u.data_list:
        if x.name == name and x.multi_id == 0:
            return x.data
    return None


def rel(d, s0):
    return (d['timestamp'].astype(np.float64) - s0) * 1e-6


def seg_stats(a):
    fin = a[np.isfinite(a)]
    if fin.size == 0:
        return {'n': int(a.size), 'nan': int(a.size), 'min': None, 'max': None, 'std': None, 'std_d1': None}
    d1 = np.diff(a)
    d1 = d1[np.isfinite(d1)]
    return {'n': int(a.size), 'nan': int(a.size - fin.size),
            'min': round(float(fin.min()), 3), 'max': round(float(fin.max()), 3),
            'std': round(float(fin.std()), 3),
            'std_d1': round(float(d1.std()), 3) if d1.size else None}


def run_one(name):
    u = ULog(RES + '/' + name + '/flight.ulg')
    s0 = u.start_timestamp
    out = {'run': name}

    vs = get(u, 'vehicle_status')
    t_vs = rel(vs, s0)
    idx = np.where(vs['nav_state'] == 18)[0]
    if idx.size == 0:
        out['error'] = 'AUTO_LAND never entered'
        return out
    entry = float(t_vs[idx[0]])
    W0, W1 = entry - 2.0, entry + 6.0
    out['entry_s'] = round(entry, 3)

    # 1. trajectory_setpoint
    ts = get(u, 'trajectory_setpoint')
    t = rel(ts, s0)
    win = (t >= W0) & (t <= W1)
    tw = t[win]
    out['tsp_rate_hz'] = round(1.0 / float(np.median(np.diff(tw))), 2) if tw.size > 2 else None
    pre = (t >= W0) & (t < entry)
    post = (t >= entry) & (t <= W1)
    acc = {}
    for i, ax in enumerate('xyz'):
        a = ts['acceleration[%d]' % i].astype(np.float64)
        acc[ax] = a
        out['acc_' + ax] = {'pre': seg_stats(a[pre]), 'post': seg_stats(a[post])}
    # largest single-sample change of acc x,y inside the window
    for ax in 'xy':
        a = acc[ax][win]
        tt = tw
        dd = np.abs(np.diff(a))
        if np.any(np.isfinite(dd)):
            k = int(np.nanargmax(dd))
            out['acc_' + ax + '_max_step'] = {
                'step_mps2': round(float(dd[k]), 3),
                't_rel_entry_s': round(float(tt[k + 1] - entry), 3),
                'from_to': [round(float(a[k]), 3), round(float(a[k + 1]), 3)]}
    for nm, f in [('vel_x', 'velocity[0]'), ('vel_y', 'velocity[1]'),
                  ('pos_x', 'position[0]'), ('pos_y', 'position[1]')]:
        v = ts[f].astype(np.float64)[post]
        out[nm + '_post'] = {'n': int(v.size), 'nan': int(np.sum(~np.isfinite(v)))}

    # 2. indi_rate_feedforward
    ff = get(u, 'indi_rate_feedforward')
    t_ff = rel(ff, s0)
    mw = (t_ff >= W0) & (t_ff <= W1)
    tf = t_ff[mw]
    for i, ax in enumerate('xy'):
        w = np.degrees(ff['omega_ff[%d]' % i].astype(np.float64)[mw])
        aw = np.abs(w)
        if np.any(np.isfinite(aw)):
            k = int(np.nanargmax(aw))
            out['omega_' + ax] = {'peak_abs_degs': round(float(aw[k]), 2),
                                  'peak_signed_degs': round(float(w[k]), 2),
                                  't_peak_rel_entry_s': round(float(tf[k] - entry), 3)}
        bins = []
        for b in range(8):
            lo = W0 + b
            m = (tf >= lo) & (tf < lo + 1.0)
            bins.append(round(float(np.nanmean(aw[m])), 2) if np.any(m) else None)
        out['omega_' + ax + '_mean_abs_bins_-2_to_6s'] = bins

    # 2b. omega_ff vs backward difference of a_ff (sample-based, no filter/hold model)
    fin = np.isfinite(acc['x']) & np.isfinite(acc['y']) & (t >= entry - 0.5) & (t <= W1)
    tq, ax_, ay_ = t[fin], acc['x'][fin], acc['y'][fin]
    dt = np.diff(tq)
    jx = np.diff(ax_) / dt
    jy = np.diff(ay_) / dt
    tj = tq[1:]
    jx_i = np.interp(tf, tj, jx)
    jy_i = np.interp(tf, tj, jy)
    wx = np.degrees(ff['omega_ff[0]'].astype(np.float64)[mw])
    wy = np.degrees(ff['omega_ff[1]'].astype(np.float64)[mw])
    sel = (tf >= entry) & np.isfinite(wx) & np.isfinite(wy)
    out['corr_omega_x_vs_jy'] = round(float(np.corrcoef(wx[sel], jy_i[sel])[0, 1]), 3)
    out['corr_omega_y_vs_minus_jx'] = round(float(np.corrcoef(wy[sel], -jx_i[sel])[0, 1]), 3)
    # implied 1/collective (rad/s per m/s^3) from least squares, expected ~1/g if collective ~ g
    k = np.dot(np.radians(wx[sel]), jy_i[sel]) / np.dot(jy_i[sel], jy_i[sel])
    out['implied_collective_mps2_x'] = round(float(1.0 / k), 2) if k != 0 else None

    # 3. indi_pos_status
    ps = get(u, 'indi_pos_status')
    if ps is not None:
        names = list(ps.keys())
        out['indi_pos_status_fields'] = names
        out['indi_pos_status_jerk_like_fields'] = [n for n in names if 'jerk' in n.lower() or 'diff' in n.lower()]
        t_ps = rel(ps, s0)
        mp = (t_ps >= W0) & (t_ps <= W1)
        js = ps['jerk_source'][mp]
        vals, cnt = np.unique(js, return_counts=True)
        out['jerk_source_in_window'] = {int(v): int(c) for v, c in zip(vals, cnt)}
        chg = np.where(np.diff(ps['jerk_source'].astype(int)) != 0)[0]
        out['jerk_source_changes_rel_entry_s'] = [round(float(t_ps[c + 1] - entry), 3) for c in chg[:10]]

    # 4. vehicle_local_position ax, ay std
    lp = get(u, 'vehicle_local_position')
    t_lp = rel(lp, s0)
    lpre = (t_lp >= W0) & (t_lp < entry)
    lpost = (t_lp >= entry) & (t_lp <= W1)
    for f in ['ax', 'ay']:
        v = lp[f].astype(np.float64)
        out['lpos_' + f] = {'pre_std': round(float(np.nanstd(v[lpre])), 3),
                            'post_std': round(float(np.nanstd(v[lpost])), 3),
                            'post_nan': int(np.sum(~np.isfinite(v[lpost])))}
    return out


for r in RUNS:
    print(json.dumps(run_one(r), default=str))
