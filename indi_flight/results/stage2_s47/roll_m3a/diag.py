import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); g=lambda n:[d for d in u.data_list if d.name==n and d.multi_id==0][0].data
v=g('vehicle_angular_velocity'); t=v['timestamp']*1e-6
for a,b in ((36,44),(44,51),(60,70)):
  s=(t>=a)&(t<b)
  for ax in (0,2):
    x=v[f'xyz[{ax}]'][s]; x=x-x.mean(); dt=np.median(np.diff(t[s])); F=np.abs(np.fft.rfft(x*np.hanning(len(x)))); f=np.fft.rfftfreq(len(x),dt)
    k=np.argsort(F)[-3:][::-1]; print(a,b,'axis',ax,'peaks Hz',np.round(f[k],1),'rms %.3f'%x.std())
