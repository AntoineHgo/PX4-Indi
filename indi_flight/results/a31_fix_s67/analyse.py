import sys,json,numpy as np
from pyulog import ULog
d=sys.argv[1]; prof=sys.argv[2]
u=ULog(d+'/flight.ulg'); D={x.name:x.data for x in u.data_list}
on=json.load(open(d+'/disturbance_trigger.json'))['onset_px4_s']
def t(n): return D[n]['timestamp']*1e-6
e=D['esc_status']; te=t('esc_status')
r2=np.mean([e[f'esc[{i}].esc_rpm']**2.0 for i in range(4)],axis=0)
rp=np.array([e[f'esc[{i}].esc_rpm']**2.0 for i in range(4)])
pre=(te>on-8)&(te<on-1); dur=(te>on+10)&(te<on+28)
print('onset',on,'rpm2 ratio',r2[dur].mean()/r2[pre].mean())
if prof=='payload_add':
    print('extra thrust / (m g)',r2[dur].mean()/r2[pre].mean()-1,'(applied 0.25)')
else:
    # roll torque ~ (left-right) rpm^2 diff; scale from hover: sum k w^2 = m g
    k=0.610*9.8/ (rp[:,pre].mean(axis=1).sum()*(2*np.pi/60)**2)
    m=rp[:,dur].mean(axis=1)-rp[:,pre].mean(axis=1)
    print('d(rpm2) per motor',m)
    # quad5in geometry unknown here: use ratio vs g15 (0.0898 for 0.0448): need arm; print raw
    np.save(d+'/../com_dm.npy',m)
for n in ('vehicle_attitude_groundtruth','vehicle_attitude'):
    if n in D:
        q=np.array([D[n][f'q[{i}]'] for i in range(4)]); ta=t(n)
        roll=np.degrees(np.arctan2(2*(q[0]*q[1]+q[2]*q[3]),1-2*(q[1]**2+q[2]**2)))
        for lo,hi in ((0,5),(5,25),(25,28),(28,31)):
            m=(ta>on+lo)&(ta<on+hi); print(n,lo,hi,'roll min/max %.1f %.1f'%(roll[m].min(),roll[m].max()))
        break
