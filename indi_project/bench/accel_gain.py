#!/usr/bin/env python3
# Effective gain from angular acceleration to torque setpoint per band (regression), and estimated vs ground-truth acceleration (gt logged at ~59 Hz: trust < 29 Hz only).
# Window = metrics.json window (absolute ULog time). Usage: accel_gain.py RUN_DIR [RUN_DIR ...] (dirs with flight.ulg + metrics.json)
# High-frequency torque vs angular acceleration: effective D gain, and true vs estimated acceleration content.
import sys,json,numpy as np
from pyulog import ULog
def bp(x,t,lo,hi,fs=None):
    x=x-x.mean(); dt=np.median(np.diff(t)); X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),dt); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
def onto(t_src,x,t_dst): return np.interp(t_dst,t_src,x)
for p in sys.argv[1:]:
    m=json.load(open(p+'/metrics.json')); t0,t1=m['window']['start_s'],m['window']['end_s']
    u=ULog(p+'/flight.ulg',['vehicle_angular_velocity','vehicle_torque_setpoint','vehicle_angular_velocity_groundtruth'])
    ds={d.name:d.data for d in u.data_list}
    ts=ds['vehicle_torque_setpoint']; t=ts['timestamp']*1e-6; k=(t>t0)&(t<t1); tt=t[k]
    av=ds['vehicle_angular_velocity']; ta=av['timestamp']*1e-6
    gt=ds['vehicle_angular_velocity_groundtruth']; tg=gt['timestamp']*1e-6; kg=(tg>t0-1)&(tg<t1+1)
    fsg=1/np.median(np.diff(tg[kg]))
    line=f"{p:20s} gt_fs {fsg:.0f}"
    for i,a in enumerate('RP'):
        tq=ts[f'xyz[{i}]'][k]; dw=onto(ta,av[f'xyz_derivative[{i}]'],tt)
        wg=gt[f'xyz[{i}]'][kg]; dwg=np.gradient(wg,tg[kg]); dwg=onto(tg[kg],dwg,tt)
        res=[]
        for lo,hi in ((10,30),(30,80)):
            T=bp(tq,tt,lo,hi); D=bp(dw,tt,lo,hi); G=bp(dwg,tt,lo,hi)
            gain=-(T@D)/(D@D)  # torque = -Dgain * accel (+ ...)
            res.append(f"{lo}-{hi}Hz: -dT/da {gain:.5f} corr {np.corrcoef(T,D)[0,1]:+.2f} a_est {D.std():.4f} a_true {G.std():.4f}")
        line+=f"\n   {a} "+' | '.join(res)
    print(line)
