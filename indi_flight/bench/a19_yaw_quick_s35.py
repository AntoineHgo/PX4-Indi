import sys, numpy as np
from pyulog import ULog
def yaw(d):
    w,x,y,z=[d[f'q[{i}]'] for i in range(4)]
    return np.degrees(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))
for p in sys.argv[1:]:
    u=ULog(p,['sim_ground_truth','vehicle_attitude','vehicle_status'])
    g={d.name:d.data for d in u.data_list}
    gt,va,st=g['sim_ground_truth'],g['vehicle_attitude'],g['vehicle_status']
    ta=st['timestamp'][np.nonzero(st['arming_state']==2)[0][0]]
    yt=np.interp(va['timestamp'],gt['timestamp'],np.unwrap(np.radians(yaw(gt))))
    e=(np.degrees(yt)-yaw(va)+180)%360-180
    def at(t0,t1):
        m=(va['timestamp']>=t0*1e6)&(va['timestamp']<=t1*1e6); return e[m].mean(), e[m].std()
    print(p, 'arm %.2f s'%(ta/1e6), 'pre-arm 25-30: %+.2f' % at(25,30)[0], 'window 45-60: %+.2f sd %.2f' % at(45,60))
