import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); g={d.name:d.data for d in u.data_list}
for n in ('indi_rate_status','actuator_torque_measured','esc_status','sensor_gyro','indi_pos_status'):
    if n in g: t=g[n]['timestamp']; print(n,len(t),'median dt ms %.2f'%(np.median(np.diff(t))/1e3))
    else: print(n,'ABSENT')
r=g['indi_rate_status']; print('fields',[k for k in r if 'meas' in k or 'inj' in k.lower()])
for k in r:
    if 'measured_torque_in_use' in k: print(k,'nonzero frac',np.mean(r[k]!=0))
    if 'inj' in k.lower() and r[k].dtype.kind=='f':
        a=np.abs(r[k]); idx=np.where(a>0)[0]; print(k,'active n',len(idx),'t0..t1 s', (r['timestamp'][idx[0]]-r['timestamp'][0])/1e6 if len(idx) else None,(r['timestamp'][idx[-1]]-r['timestamp'][0])/1e6 if len(idx) else None)
a=g['vehicle_attitude']; q=np.stack([a['q[%d]'%i] for i in range(4)],1)
roll=np.degrees(np.arctan2(2*(q[:,0]*q[:,1]+q[:,2]*q[:,3]),1-2*(q[:,1]**2+q[:,2]**2)))
print('max |roll| deg',np.abs(roll).max(),'t_end s',(a['timestamp'][-1]-a['timestamp'][0])/1e6)
l=g.get('vehicle_land_detected')
