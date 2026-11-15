import sys, json, os, glob
import numpy as np
from pyulog import ULog
R = '/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s8n_oset/runs'
def topic(u, n):
    for d in u.data_list:
        if d.name == n and d.multi_id == 0: return d.data
    return None
def rms(x): return float(np.sqrt(np.nanmean(np.asarray(x)**2)))
def zoh(ts, vs, td):
    idx = np.clip(np.searchsorted(ts, td, side='right')-1, 0, None); return np.asarray(vs)[idx].astype(float)
def hermite(ts, p, v, td):
    # cubic Hermite between logged setpoint samples using logged position and velocity
    i = np.clip(np.searchsorted(ts, td, side='right')-1, 0, len(ts)-2)
    h = (ts[i+1]-ts[i])*1e-6; s = np.clip((td-ts[i])*1e-6/h, 0, 1)
    h00=2*s**3-3*s**2+1; h10=s**3-2*s**2+s; h01=-2*s**3+3*s**2; h11=s**3-s**2
    return h00*p[i]+h10*h*v[i]+h01*p[i+1]+h11*h*v[i+1]
def one(path):
    run = json.load(open(os.path.join(path,'run.json')))
    u = ULog(os.path.join(path,'flight.ulg'))
    lp = topic(u,'vehicle_local_position'); sp = topic(u,'trajectory_setpoint'); gt = topic(u,'vehicle_local_position_groundtruth')
    w0, w1 = run['t_window_start_us'], run['t_window_end_us']
    t = lp['timestamp']; m = (t>=w0)&(t<=w1)
    ts = sp['timestamp']
    P = [sp[f'position[{i}]'] for i in range(3)]; V = [sp[f'velocity[{i}]'] for i in range(3)]
    ok = np.isfinite(P[0])&np.isfinite(V[0]); 
    tm = t[m]
    tm = tm[(tm>=ts[ok][0])&(tm<=ts[ok][-1])]
    est = np.column_stack([np.interp(tm, t, lp[k]) for k in ('x','y','z')])
    ref_z = np.column_stack([zoh(ts[ok], P[i][ok], tm) for i in range(3)])
    ref_h = np.column_stack([hermite(ts[ok], P[i][ok], V[i][ok], tm) for i in range(3)])
    e_z = np.linalg.norm(est-ref_z,axis=1); e_h = np.linalg.norm(est-ref_h,axis=1)
    out = dict(zoh=rms(e_z), herm=rms(e_h), dt_sp=float(np.median(np.diff(ts))*1e-6))
    # speed
    out['vref_rms'] = rms(np.linalg.norm(np.column_stack([zoh(ts[ok], V[i][ok], tm) for i in range(3)]),axis=1))
    if gt is not None:
        tg = gt['timestamp']
        g = np.column_stack([np.interp(tm, tg, gt[k]) for k in ('x','y','z')])
        # constant frame offset between EKF and ground truth: remove the mean difference over the window
        off = np.mean(est-g, axis=0)
        out['gt_herm'] = rms(np.linalg.norm(g+off-ref_h,axis=1))
        out['ekf_minus_gt'] = rms(np.linalg.norm(est-g-off,axis=1))
    return out
ents = sys.argv[1:] or sorted(os.listdir(R))
print("%-24s %-12s  %6s %6s %6s %6s | reported(zoh) recomputed: ZOH  Hermite  GT-Hermite  EKF-GT  vref"%('entry','ctrl','','','',''))
res = {}
for e in ents:
    for c in ('pid_tuned','indi_pos_v3'):
        rows=[]
        for s in range(1,11):
            p = os.path.join(R,e,c,f'seed{s}')
            try:
                o = one(p); rep = json.load(open(os.path.join(p,'metrics.json')))['trajectory']['rms_3d_m']; o['rep']=rep; rows.append(o)
            except Exception as ex:
                print('  fail',p,ex)
        k = lambda n: np.mean([r[n] for r in rows if n in r])
        res[(e,c)] = {n:k(n) for n in ('rep','zoh','herm','gt_herm','ekf_minus_gt','vref_rms','dt_sp')}
        print("%-24s %-12s n=%2d  reported %.3f | zoh %.3f  herm %.3f  gt %.3f  ekf-gt %.3f  vref %.2f  sp_dt %.3f"%(e,c,len(rows),k('rep'),k('zoh'),k('herm'),k('gt_herm'),k('ekf_minus_gt'),k('vref_rms'),k('dt_sp')))
    a=res[(e,'pid_tuned')]; b=res[(e,'indi_pos_v3')]
    print("   ratio INDI/PID: reported %.2f | zoh %.2f | hermite %.2f | ground truth %.2f"%(b['rep']/a['rep'], b['zoh']/a['zoh'], b['herm']/a['herm'], b['gt_herm']/a['gt_herm']))
