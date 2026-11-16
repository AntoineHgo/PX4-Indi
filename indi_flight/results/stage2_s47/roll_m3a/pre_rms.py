# RMS of roll rate (detrended 1 s mean) in 1 s segments, plus motor pin, before/during injection
import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); g=lambda n:[d for d in u.data_list if d.name==n and d.multi_id==0][0].data
v=g('vehicle_angular_velocity'); t=v['timestamp']*1e-6; m=g('actuator_motors'); tm=m['timestamp']*1e-6
r=g('vehicle_land_detected'); 
for a in (35,40,45,50,55,60,70,80):
    s=(t>=a)&(t<a+5); x=v['xyz[0]'][s]; 
    sm=(tm>=a)&(tm<a+5); mm=np.stack([m[f'control[{i}]'][sm] for i in range(4)],1)
    print(a,'rollrate std %.3f pitch %.3f yaw %.3f'%(x.std(),v['xyz[1]'][s].std(),v['xyz[2]'][s].std()),'pin %.3f'%np.mean((mm<0.005).any(1)|(mm>0.995).any(1)))
