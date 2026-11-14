"""Session 42 tilt diagnosis helper. Run: python3 -I tilt_diag.py <cmd> ...
pyulog lives in the user site dir, which -I hides, so it is appended to sys.path explicitly."""
import sys, glob, json, os
sys.path.append('/home/ahugo/.local/lib/python3.12/site-packages')
import numpy as np
from pyulog import ULog

def load(p):
    return ULog(p)

def get(u, name, multi=0):
    for d in u.data_list:
        if d.name == name and d.multi_id == multi:
            return d.data
    return None

def quat_to_rp(q):
    w, x, y, z = q
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    pitch = np.arcsin(np.clip(2*(w*y-z*x), -1, 1))
    return np.degrees(roll), np.degrees(pitch)

def tsec(u, d):
    return (d['timestamp'] - u.start_timestamp) / 1e6

def binmean(t, v, t0, t1, step=1.0):
    out = []
    for a in np.arange(t0, t1, step):
        m = (t >= a) & (t < a+step)
        out.append(np.mean(v[m], axis=0) if m.any() else np.nan*np.ones(v.shape[1:]))
    return np.array(out)

def topics(path):
    u = load(path)
    for d in sorted(u.data_list, key=lambda d: d.name):
        print(d.name, d.multi_id, len(d.data['timestamp']))

if __name__ == '__main__':
    if sys.argv[1] == 'topics':
        topics(sys.argv[2])

def T(d):  # absolute px4 time in s (same base as run.json t_us)
    return d['timestamp'] / 1e6

def att(u, name='vehicle_attitude'):
    d = get(u, name)
    q = np.vstack([d['q[%d]' % i] for i in range(4)])
    r, p = quat_to_rp(q)
    return T(d), r, p

def table(path, t0=20, t1=46, step=1.0):
    u = load(path)
    rows = {}
    t, r, p = att(u); rows['roll'] = (t, r[:, None]); rows['pitch'] = (t, p[:, None])
    t, r, p = att(u, 'vehicle_attitude_setpoint') if False else (None, None, None)
    d = get(u, 'vehicle_attitude_setpoint')
    q = np.vstack([d['q_d[%d]' % i] for i in range(4)]); rs, ps = quat_to_rp(q)
    rows['roll_sp'] = (T(d), rs[:, None]); rows['pitch_sp'] = (T(d), ps[:, None])
    d = get(u, 'vehicle_rates_setpoint')
    rows['rsp'] = (T(d), np.degrees(np.vstack([d['roll'], d['pitch'], d['yaw']]).T))
    d = get(u, 'vehicle_angular_velocity')
    rows['rate'] = (T(d), np.degrees(np.vstack([d['xyz[0]'], d['xyz[1]'], d['xyz[2]']]).T))
    d = get(u, 'vehicle_torque_setpoint')
    rows['tau'] = (T(d), np.vstack([d['xyz[0]'], d['xyz[1]'], d['xyz[2]']]).T)
    d = get(u, 'vehicle_thrust_setpoint')
    rows['thr'] = (T(d), -d['xyz[2]'][:, None])
    d = get(u, 'indi_rate_status')
    for k in () if d is None else ('nu', 'angular_accel_filtered', 'torque_filtered', 'torque_increment'):
        rows[k] = (T(d), np.vstack([d[k + '[%d]' % i] for i in range(3)]).T)
    if d is not None: rows['fault'] = (T(d), np.vstack([d['fault'], d['measured_torque_in_use']]).T.astype(float))
    d = get(u, 'actuator_motors')
    rows['mot'] = (T(d), np.vstack([d['control[%d]' % i] for i in range(4)]).T)
    d = get(u, 'esc_status')
    if d is not None and 'esc[0].esc_rpm' in d:
        rows['erpm'] = (T(d), np.vstack([d['esc[%d].esc_rpm' % i] for i in range(4)]).T)
    d = get(u, 'control_allocator_status')
    sat = [k for k in d if 'saturation' in k or 'unallocated' in k]
    rows['alloc_unalloc'] = (T(d), np.vstack([d['unallocated_torque[%d]' % i] for i in range(3)]).T)
    rows['alloc_sat'] = (T(d), np.vstack([d[k] for k in sat if 'saturation' in k]).T.astype(float)) if sat else None
    d = get(u, 'vehicle_local_position')
    rows['pos'] = (T(d), np.vstack([d['x'], d['y'], d['z']]).T)
    return rows

def show(path, keys, t0=20, t1=46, step=1.0):
    rows = table(path, t0, t1, step)
    edges = np.arange(t0, t1, step)
    cols = []
    names = []
    for k in keys:
        if rows.get(k) is None: continue
        t, v = rows[k]
        b = binmean(t, v, t0, t1, step)
        cols.append(b); names += ['%s%d' % (k, i) for i in range(b.shape[1])]
    M = np.hstack(cols)
    print('t     ' + ' '.join('%9s' % n[:9] for n in names))
    for e, row in zip(edges, M):
        print('%5.1f ' % e + ' '.join('%9.3f' % x for x in row))

if __name__ == '__main__' and sys.argv[1] == 'show':
    show(sys.argv[2], sys.argv[3].split(','), float(sys.argv[4]), float(sys.argv[5]))

def tilt_summary(path):
    u = load(path)
    t, r, p = att(u)
    d = get(u, 'vehicle_attitude_setpoint')
    q = np.vstack([d['q_d[%d]' % i] for i in range(4)]); rs, ps = quat_to_rp(q)
    rs_i = np.interp(t, T(d), rs); ps_i = np.interp(t, T(d), ps)
    err = np.hypot(r - rs_i, p - ps_i)
    def m(a, b):
        k = (t >= a) & (t < b); return err[k].mean() if k.any() else float('nan')
    big = np.where((err > 2.0) & (t > 25))[0]
    onset = t[big[0]] if len(big) else float('nan')
    return m(30, 40), m(44, 50), onset, err[(t > 25)].max()

if __name__ == '__main__' and sys.argv[1] == 'sweep':
    for p in sorted(glob.glob(sys.argv[2])):
        try:
            a, b, o, mx = tilt_summary(p)
            print('%-95s err30-40=%6.2f err44-50=%6.2f onset(>2deg,t>25)=%6.1f max=%6.1f' % (p.split('runs/')[-1], a, b, o, mx))
        except Exception as e:
            print(p, 'ERR', e)

def fixed_point(path, t0=44, t1=50):
    """Check tau_cmd = torque_filtered + nu/G1 (alpha~0) and rate_sp = P*att_err in the held tilt."""
    u = load(path)
    G1 = {0: 174., 1: 174.}
    d = get(u, 'indi_rate_status'); t = T(d); k = (t >= t0) & (t < t1)
    nu = np.vstack([d['nu[%d]' % i] for i in range(3)]).T[k].mean(0)
    af = np.vstack([d['angular_accel_filtered[%d]' % i] for i in range(3)]).T[k].mean(0)
    tf = np.vstack([d['torque_filtered[%d]' % i] for i in range(3)]).T[k].mean(0)
    inc = np.vstack([d['torque_increment[%d]' % i] for i in range(3)]).T[k].mean(0)
    d2 = get(u, 'vehicle_torque_setpoint'); k2 = (T(d2) >= t0) & (T(d2) < t1)
    tau = np.vstack([d2['xyz[%d]' % i] for i in range(3)]).T[k2].mean(0)
    print('nu', nu, 'alpha_f', af, 'torque_filtered', tf, 'increment', inc, 'tau_cmd', tau)
    print('tf+inc', tf + inc, ' nu/G1', nu[:2] / 174.)
    print('implied disturbance d = tau_cmd - tf (command not realised):', tau - tf)

if __name__ == '__main__' and sys.argv[1] == 'fixed':
    fixed_point(sys.argv[2])
