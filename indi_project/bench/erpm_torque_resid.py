#!/usr/bin/env python3
# eRPM-measured torque vs a first-order (12.5 ms) model of the commanded torque, per band; residual = content not explained by the command.
# Window = metrics.json window (absolute ULog time). Usage: erpm_torque_resid.py RUN_DIR [RUN_DIR ...] (dirs with flight.ulg + metrics.json)
# measured (eRPM) torque vs first-order model of the commanded torque, per band
import sys,json,numpy as np
from pyulog import ULog
BANDS=[(0.5,2),(2,4),(4,10),(10,30),(30,80)]
def band(x,t,lo,hi):
    x=x-x.mean(); dt=np.median(np.diff(t)); X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),dt); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
for p in sys.argv[1:]:
    m=json.load(open(p+'/metrics.json')); t0,t1=m['window']['start_s'],m['window']['end_s']
    u=ULog(p+'/flight.ulg',['vehicle_torque_setpoint','actuator_torque_measured'])
    ds={d.name:d.data for d in u.data_list}
    me=ds['actuator_torque_measured']; tm=me['timestamp']*1e-6; k=(tm>t0)&(tm<t1); tt=tm[k]
    ts=ds['vehicle_torque_setpoint']; tsp=ts['timestamp']*1e-6
    print(f"{p}  valid {np.mean(me['valid'][k]):.3f}  fs {1/np.median(np.diff(tt)):.0f}")
    for i,a in enumerate('RP'):
        cmd=np.interp(tt,tsp,ts[f'xyz[{i}]'])
        best=None
        for lag in range(0,8):   # samples of transport delay, fit
            dt=np.median(np.diff(tt)); al=dt/(0.0125+dt); y=np.zeros_like(cmd); acc=cmd[0]
            c=np.roll(cmd,lag); c[:lag]=cmd[0]
            for j in range(len(c)): acc+=al*(c[j]-acc); y[j]=acc
            meas=me[f'torque[{i}]'][k]; r=meas-y
            e=np.sqrt(np.mean(band(r,tt,2,30)**2))
            if best is None or e<best[0]: best=(e,lag,y,meas,r)
        e,lag,y,meas,r=best
        print(f"  {a} lag {lag}  "+'  '.join(f"{lo}-{hi}Hz cmd {np.std(band(cmd,tt,lo,hi)):.5f} meas {np.std(band(meas,tt,lo,hi)):.5f} resid {np.std(band(r,tt,lo,hi)):.5f}" for lo,hi in BANDS))
