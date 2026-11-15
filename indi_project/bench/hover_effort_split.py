#!/usr/bin/env python3
# Hover effort split: motor-rate RMS per mode (roll/pitch/yaw/collective), torque-setpoint band RMS, INDI terms (nu/G1, a_f/G1, t_f, increment) per band.
# Window = metrics.json window (absolute ULog time). Usage: hover_effort_split.py RUN_DIR [RUN_DIR ...] (dirs with flight.ulg + metrics.json)
import sys, json, numpy as np
from pyulog import ULog
BANDS=[(0,2),(2,10),(10,30),(30,80),(80,250)]
def win(d,t0,t1):
    t=d['timestamp']*1e-6; return t,(t>=t0)&(t<=t1)
def bands(x,t):
    x=x-x.mean(); dt=np.median(np.diff(t)); fs=1/dt
    X=np.fft.rfft(x*np.hanning(len(x))); f=np.fft.rfftfreq(len(x),dt); P=np.abs(X)**2
    tot=P[1:].sum()
    return fs,[np.sqrt(P[(f>=a)&(f<b)].sum()/tot)*x.std() if tot>0 else 0 for a,b in BANDS]
def run(path):
    m=json.load(open(path+'/metrics.json')); u=ULog(path+'/flight.ulg',['vehicle_torque_setpoint','actuator_motors','vehicle_angular_velocity','indi_rate_status','actuator_torque_measured'])
    ds={d.name:d.data for d in u.data_list}; tb=u.start_timestamp*1e-6
    t0=m['window']['start_s']; t1=m['window']['end_s']
    out={}
    am=ds['actuator_motors']; t,k=win(am,t0,t1); M=np.stack([am[f'control[{i}]'][k] for i in range(4)],1); tt=t[k]
    # x-quad modes from CA geometry: px,py,km signs
    px=np.array([.174,-.174,.174,-.174]); py=np.array([.174,-.174,-.174,.174]); km=np.array([1,1,-1,-1])
    modes={'roll':-py/np.abs(py),'pitch':px/np.abs(px),'yaw':km,'coll':np.ones(4)}
    dt=np.diff(tt); g=dt>0
    dM=np.diff(M,axis=0)[g]/dt[g,None]
    out['motor_rate_rms']=np.mean(np.sqrt(np.mean(dM**2,0)))
    out['mode_rate_rms']={n:np.sqrt(np.mean((dM@v/4)**2)) for n,v in modes.items()}
    ts=ds['vehicle_torque_setpoint']; t,k=win(ts,t0,t1)
    out['tq']={a:(ts[f'xyz[{i}]'][k].std(),np.sqrt(np.mean(np.diff(ts[f'xyz[{i}]'][k])**2)),bands(ts[f'xyz[{i}]'][k],t[k])[1]) for i,a in enumerate('RPY')}
    out['tq_fs']=bands(ts['xyz[0]'][k],t[k])[0]
    av=ds['vehicle_angular_velocity']; t,k=win(av,t0,t1)
    out['w_std']=[av[f'xyz[{i}]'][k].std() for i in range(3)]
    out['dw_std']=[av[f'xyz_derivative[{i}]'][k].std() for i in range(3)]
    if 'indi_rate_status' in ds:
        s=ds['indi_rate_status']; t,k=win(s,t0,t1); g1=[u.initial_parameters[f'MC_INDI_G1_{a}'] for a in 'RPY']
        out['indi']={}
        for i,a in enumerate('RPY'):
            nu=s[f'nu[{i}]'][k]/g1[i]; af=s[f'angular_accel_filtered[{i}]'][k]/g1[i]; tf=s[f'torque_filtered[{i}]'][k]; inc=s[f'torque_increment[{i}]'][k]
            out['indi'][a]={n:(x.std(),bands(x,t[k])[1]) for n,x in (('nu/G1',nu),('a_f/G1',af),('t_f',tf),('inc',inc),('t_f+inc',tf+inc))}
        out['meas_in_use']=float(np.mean(s['measured_torque_in_use'][k]))
    return out
for p in sys.argv[1:]:
    o=run(p); c=p.split('/')[-2]
    print(f"== {c} {p.split('/')[-1]}  motor_rate {o['motor_rate_rms']:.4f}  modes "+' '.join(f"{n} {v:.4f}" for n,v in o['mode_rate_rms'].items())+f"  tq_fs {o['tq_fs']:.0f}")
    print("   w_std "+' '.join(f'{x:.4f}' for x in o['w_std'])+"  dw_std "+' '.join(f'{x:.3f}' for x in o['dw_std']))
    for a,(sd,dr,b) in o['tq'].items(): print(f"   tq{a} std {sd:.5f} drms {dr:.5f} bands "+' '.join(f'{x:.5f}' for x in b))
    if 'indi' in o:
        print(f"   meas_in_use {o['meas_in_use']:.2f}")
        for a,d in o['indi'].items(): print(f"   {a} "+' | '.join(f"{n} {sd:.5f} ["+' '.join(f'{x:.5f}' for x in b)+"]" for n,(sd,b) in d.items()))
