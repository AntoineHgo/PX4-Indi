import json, os, numpy as np
from pyulog import ULog

def welch(x,fs,nperseg):
    w=np.hanning(nperseg); step=nperseg//2; acc=[]; 
    for i in range(0,x.shape[0]-nperseg+1,step):
        seg=x[i:i+nperseg]; seg=(seg-seg.mean(axis=0))*w[:,None]
        acc.append(np.abs(np.fft.rfft(seg,axis=0))**2)
    P=np.mean(acc,axis=0)/(fs*(w**2).sum()); P[1:-1]*=2
    return np.fft.rfftfreq(nperseg,1/fs),P
R='/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project/results/s8m_smoke_gnss0/hover'
def topic(u,n):
    for d in u.data_list:
        if d.name==n and d.multi_id==0: return d.data
def rms(x): return float(np.sqrt(np.mean(np.asarray(x)**2)))
print(os.listdir(R))
for c in sorted(os.listdir(R)):
    rows=[]
    for s in range(1,11):
        p=os.path.join(R,c,f'seed{s}')
        if not os.path.exists(os.path.join(p,'flight.ulg')): continue
        run=json.load(open(os.path.join(p,'run.json'))); u=ULog(os.path.join(p,'flight.ulg'))
        am=topic(u,'actuator_motors'); t=am['timestamp']; m=(t>=run['t_window_start_us'])&(t<=run['t_window_end_us'])
        U=np.column_stack([am[f'control[{i}]'][m] for i in range(4)]); tt=t[m]*1e-6
        rep=json.load(open(os.path.join(p,'metrics.json')))['effort']['motor_rate_rms_per_s']
        fs=250.; tu=np.arange(tt[0],tt[-1],1/fs); Uu=np.column_stack([np.interp(tu,tt,U[:,i]) for i in range(4)])
        Uu=Uu-Uu.mean(axis=0)
        f,P=welch(Uu,fs,1024); P=P.mean(axis=1); df=f[1]-f[0]
        band=lambda a,b: float(np.sqrt(P[(f>=a)&(f<b)].sum()*df))
        dband=lambda a,b: float(np.sqrt((P*(2*np.pi*f)**2)[(f>=a)&(f<b)].sum()*df))
        # collective vs differential
        coll=Uu.mean(axis=1); diff=Uu-coll[:,None]
        es=topic(u,'esc_status'); te=es['timestamp']; me=(te>=run['t_window_start_us'])&(te<=run['t_window_end_us'])
        rpm=np.column_stack([es[f'esc[{i}].esc_rpm'][me] for i in range(4)]).astype(float)
        av=topic(u,'vehicle_angular_velocity'); ta=av['timestamp_sample']; dts=np.diff(ta); 
        rows.append(dict(rep=rep, std=rms(Uu), b0_5=band(0,5), b5_30=band(5,30), b30=band(30,126), d0_5=dband(0,5), d5_30=dband(5,30), d30=dband(30,126),
                         coll=rms(coll), diff=rms(diff), rpm_std=float(np.mean(rpm.std(axis=0))), ctrl_dt_ms=float(np.min(dts[dts>0])*1e-3)))
    if rows:
        k=lambda n:(np.mean([r[n] for r in rows]), np.median([r[n] for r in rows]))
        print(c,'n=%d'%len(rows))
        for n in rows[0]: print('   %-10s mean %.4g  median %.4g   min %.4g max %.4g'%(n,*k(n),min(r[n] for r in rows),max(r[n] for r in rows)))
