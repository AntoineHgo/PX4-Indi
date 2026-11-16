import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); g=lambda n:[d for d in u.data_list if d.name==n and d.multi_id==0][0].data
v=g('vehicle_angular_velocity'); t=v['timestamp']*1e-6
l=g('vehicle_land_detected'); tl=l['timestamp']*1e-6; air=np.flatnonzero(l['landed']==0)
a=tl[air[0]]+15; 
arm=g('vehicle_status'); ta=arm['timestamp']*1e-6; dis=ta[(arm['arming_state']!=2)&(ta>a)]
b=min(dis[0] if len(dis) else 1e9, a+30, tl[air[-1]]) if True else 0
s=(t>=a)&(t<b); print('window %.1f-%.1f'%(a,b))
for ax,nm in enumerate('rpy'):
    x=v[f'xyz[{ax}]'][s]; x=x-x.mean(); dt=np.median(np.diff(t[s]))
    F=np.abs(np.fft.rfft(x*np.hanning(len(x)))); f=np.fft.rfftfreq(len(x),dt); print(nm,'std %.4f dom %.1f Hz'%(x.std(),f[1:][np.argmax(F[1:])]))
m=g('actuator_motors'); tm=m['timestamp']*1e-6; sm=(tm>=a)&(tm<b)
mm=np.stack([m[f'control[{i}]'][sm] for i in range(4)],1); print('pin %.4f'%np.mean((mm<0.005).any(1)|(mm>0.995).any(1)))
