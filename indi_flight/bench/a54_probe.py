import sys, numpy as np
from pyulog import ULog
from scipy.signal import welch
log=sys.argv[1]; t0,t1=float(sys.argv[2]),float(sys.argv[3])
u=ULog(log,['sensor_accel','esc_status','vehicle_acceleration','actuator_motors','sensor_combined'])
s=u.start_timestamp
def sl(name,inst=0):
    for d in u.data_list:
        if d.name==name and d.multi_id==inst: 
            t=(d.data['timestamp']-s)*1e-6; m=(t>=t0)&(t<t1); return t[m],{k:v[m] for k,v in d.data.items()}
    return None,None
def lines(t,x,lo,hi,n=3):
    fs=1/np.median(np.diff(t)); f,p=welch(x-x.mean(),fs=fs,nperseg=int(fs*2)); b=(f>=lo)&(f<=hi)
    idx=np.argsort(p[b])[::-1][:n]; med=np.median(p[b])
    return 'fs %.0f: '%fs+' '.join('%.1fHz(%.0fx)'%(f[b][i],p[b][i]/med) for i in idx)
for nm in ['sensor_accel','sensor_combined','vehicle_acceleration']:
    t,d=sl(nm)
    if t is None: print(nm,'absent'); continue
    k=[k for k in d if k.endswith('x') or k=='accelerometer_m_s2[0]' or k=='xyz[0]']
    k='accelerometer_m_s2[2]' if nm=='sensor_combined' else ('z' if 'z' in d else 'xyz[2]')
    print(nm,k,lines(t,d[k],5,420))
for inst in (0,1):
    t,d=sl('esc_status',inst)
    if t is not None and 'esc[0].esc_rpm' in d: print('esc',inst,'rpm0 mean %.0f'%np.mean(d['esc[0].esc_rpm']), 'mean all %.0f'%np.mean([np.mean(d['esc[%d].esc_rpm'%j]) for j in range(4)]))
t,d=sl('actuator_motors'); print('act',lines(t,d['control[0]'],5,420))
