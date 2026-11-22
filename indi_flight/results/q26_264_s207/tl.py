import sys,numpy as np
from pyulog import ULog
R='/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_refly_s199/'
def load(p):
    u=ULog(R+p+'/run_264/flight.ulg'); D={}
    for d in u.data_list:
        if d.multi_id==0: D[d.name]=d.data
    return u,D
def tl(D,n): return D[n]['timestamp']/1e6
def at(D,n,k,t,off=0):
    x=D[n]; return np.interp(t+off,x['timestamp']/1e6,x[k])
def tilt(D,t):
    q=[at(D,'vehicle_attitude_groundtruth','q[%d]'%i,t) for i in range(4)]
    w,x,y,z=q; c=1-2*(x*x+y*y); return np.degrees(np.arccos(np.clip(c,-1,1)))
def rpm(D,i,t): return np.interp(t,D['esc_status']['timestamp']/1e6,D['esc_status']['esc[%d].esc_rpm'%i])
if __name__=='__main__':
    t0,t1,dt=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3])
    for p in ['indi_264','pid_264']:
        u,D=load(p); off=0
        ts=np.arange(t0,t1,dt)
        print('==',p, 'tilt>60 first:', end=' ')
        tt=np.arange(40,80,0.01); T=[tilt(D,t) for t in tt]; i=np.argmax(np.array(T)>60); print(tt[i] if max(T)>60 else None, 'maxtilt',max(T))
        print('t  tilt | motors0-3 | rpm0-3 | w(p q r)gt | sp(p q r) | tau_sp | unalloc(r p y) sat')
        for t in ts:
            m=[at(D,'actuator_motors','control[%d]'%i,t) for i in range(4)]
            r=[rpm(D,i,t) for i in range(4)]
            w=[at(D,'vehicle_angular_velocity_groundtruth','xyz[%d]'%i,t) for i in range(3)]
            s=[at(D,'vehicle_rates_setpoint',k,t) for k in ['roll','pitch','yaw']]
            ts_=[at(D,'vehicle_torque_setpoint','xyz[%d]'%i,t) for i in range(3)]
            ua=[at(D,'control_allocator_status','unallocated_torque[%d]'%i,t) for i in range(3)]
            print('%.2f %5.1f | %s | %s | %s | %s | %s | %s'%(t,tilt(D,t),' '.join('%.2f'%x for x in m),' '.join('%.0f'%x for x in r),' '.join('%4.0f'%np.degrees(x) for x in w),' '.join('%4.0f'%np.degrees(x) for x in s),' '.join('%.3f'%x for x in ts_),' '.join('%.3f'%x for x in ua)))
