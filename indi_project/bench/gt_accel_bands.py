#!/usr/bin/env python3
# Ground-truth roll angular-acceleration spectrum per band (0-29.5 Hz) from vehicle_angular_velocity_groundtruth.
# Window = metrics.json window (absolute ULog time). Usage: gt_accel_bands.py RUN_DIR [RUN_DIR ...] (dirs with flight.ulg + metrics.json)
import sys,json,numpy as np
from pyulog import ULog
def psd(x,t,seg=256):
    dt=np.median(np.diff(t)); x=x-x.mean(); n=len(x)//seg; w=np.hanning(seg)
    return np.fft.rfftfreq(seg,dt), np.mean([np.abs(np.fft.rfft(x[i*seg:(i+1)*seg]*w))**2 for i in range(n)],0)
edges=[0,2,4,6,8,10,12,14,17,20,24,29.5]
for p in sys.argv[1:]:
    m=json.load(open(p+'/metrics.json')); t0,t1=m['window']['start_s'],m['window']['end_s']
    u=ULog(p+'/flight.ulg',['vehicle_angular_velocity_groundtruth','vehicle_angular_velocity'])
    ds={d.name:d.data for d in u.data_list}
    out=[]
    for name in ('vehicle_angular_velocity_groundtruth','vehicle_angular_velocity'):
        d=ds[name]; t=d['timestamp']*1e-6; k=(t>t0)&(t<t1)
        f,P=psd(d['xyz[0]'][k]+0j*0 if False else d['xyz[0]'][k],t[k], 256 if 'ground' in name else 1024)
        P=P*(2*np.pi*f)**2  # rate -> acceleration PSD
        out.append([np.sqrt(P[(f>=a)&(f<b)].sum()) for a,b in zip(edges[:-1],edges[1:])])
    print(f"{p:20s} true  roll accel per band: "+' '.join(f'{x:6.3f}' for x in out[0]))
print("bands Hz:", ' '.join(f'{a}-{b}' for a,b in zip(edges[:-1],edges[1:])))
