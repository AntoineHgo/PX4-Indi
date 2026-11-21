#!/usr/bin/env python3
"""Independent second key for G5.11 (estimator-reset) metrics, from raw ULog only."""
import json, os, sys
import numpy as np
from pyulog import ULog

D = os.path.dirname(os.path.abspath(__file__))

def rotz(q):
    """World-frame direction of body z axis for quaternions q=[w,x,y,z] (rows)."""
    q = np.atleast_2d(q); w, x, y, z = q.T
    return np.stack([2*(x*z + w*y), 2*(y*z - w*x), 1 - 2*(x*x + y*y)], 1)

def ang(a, b):
    a = a/np.linalg.norm(a); b = b/np.linalg.norm(b)
    return np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a@b))

def tilt_jump(t, zb, ta):
    """max angle over [ta, ta+1s] of zb vs normalised mean over [ta-1s, ta). t in s."""
    pre = (t >= ta-1) & (t < ta); post = (t >= ta) & (t <= ta+1)
    if pre.sum() == 0 or post.sum() == 0: return float('nan')
    m = zb[pre].mean(0)
    return max(ang(v, m) for v in zb[post])

def selftest():
    h = np.radians(3)/2
    zb = rotz([np.cos(h), np.sin(h), 0, 0])[0]
    a = ang(zb, np.array([0, 0, 1.]))
    assert abs(a - 3.0) < 1e-9, a
    t = np.linspace(-2, 2, 401); Z = np.tile([0, 0, 1.], (401, 1)); Z[t >= 0] = zb
    assert abs(tilt_jump(t, Z, 0.0) - 3.0) < 1e-9
    return a

def get(u, name):
    d = [x for x in u.data_list if x.name == name]
    return d[0].data if d else None

def incs(ts, c):
    i = np.where(np.diff(c.astype(np.int64)) != 0)[0] + 1
    return [int(ts[k]) for k in i]

def run(seed, out):
    d = f'{D}/g5_events_s{seed}'
    rj = json.load(open(d+'/run.json'))
    u = ULog(d+'/flight.ulg')
    ev = {e['name']: e for e in rj['g5_events']}
    att = get(u, 'vehicle_attitude'); lp = get(u, 'vehicle_local_position')
    sp = get(u, 'vehicle_attitude_setpoint'); gt = get(u, 'vehicle_local_position_groundtruth')
    vs = get(u, 'vehicle_status')
    tsp = sp['timestamp']/1e6
    zb = rotz(np.stack([sp[f'q_d[{i}]'] for i in range(4)], 1))
    tg = gt['timestamp']/1e6; P = np.stack([gt['x'], gt['y'], gt['z']], 1)
    res = {}
    for name, (ts, c) in {'ekf_yaw': (att['timestamp'], att['quat_reset_counter']),
                          'ekf_xy': (lp['timestamp'], lp['xy_reset_counter'])}.items():
        L = incs(ts, c); tr = ev[name]['t_applied_us']
        out.append(f'seed {seed} {name}: all increments (us) {L}; run.json t_applied_us {tr}')
        ta_us = min(L, key=lambda x: abs(x-tr))  # nearest increment to run.json time
        ta = ta_us/1e6
        n = sum(1 for x in L if ta-1 <= x/1e6 <= ta+8)
        w = (vs['timestamp']/1e6 >= ta-1) & (vs['timestamp']/1e6 <= ta+8)
        # include state in force at window start
        k0 = np.searchsorted(vs['timestamp']/1e6, ta-1, 'right')-1
        navs = set(vs['nav_state'][w].tolist()) | {int(vs['nav_state'][max(k0, 0)])}
        valid = (n == 1) and len(navs) == 1
        tj = tilt_jump(tsp, zb, ta)
        pre = (tg >= ta-1) & (tg < ta); post = (tg >= ta) & (tg <= ta+5)
        te = np.linalg.norm(P[post]-P[pre].mean(0), axis=1).max()
        ok = valid and tj <= 1.0 and te <= 0.5
        res[name] = dict(ta=ta, nav=sorted(navs), valid=valid, n=n, tj=tj, te=te, ok=ok, dt=(ta_us-tr)/1e3)
        out.append(f'{seed}  {name:8s} t_a={ta:.3f}s (run.json dt {res[name]["dt"]:+.0f} ms) nav_state={sorted(navs)} '
                   f'valid={valid}(n_inc={n}) tilt_jump={tj:.3f}deg(<=1) truth_exc={te:.3f}m(<=0.5) {"PASS" if ok else "FAIL"}')
        if name == 'ekf_yaw':
            r = [tilt_jump(tsp, zb, ta-k) for k in range(2, 10)]
            out.append(f'{seed}  ekf_yaw no-event ref tilt jump (t_a-2..-9 s): min={min(r):.3f} max={max(r):.3f} deg  all={[round(x,3) for x in r]}')

if __name__ == '__main__':
    out = [f'self-test ok: 3 deg tilt -> {selftest():.6f} deg']
    for s in (1, 2, 3): run(s, out)
    open(D+'/key2_g511.txt', 'w').write('\n'.join(out)+'\n')
    print('\n'.join(out))
