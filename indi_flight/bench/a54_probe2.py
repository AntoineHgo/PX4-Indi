import sys, numpy as np
from pyulog import ULog
from scipy.signal import welch
log=sys.argv[1]; t0,t1=float(sys.argv[2]),float(sys.argv[3])
u=ULog(log); s=u.start_timestamp
def lines(t,x,lo,hi,n=2):
    fs=1/np.median(np.diff(t)); f,p=welch(x-x.mean(),fs=fs,nperseg=int(fs*2)); b=(f>=lo)&(f<=hi)
    idx=np.argsort(p[b])[::-1][:n]; med=np.median(p[b])
    return 'fs %.0f: '%fs+' '.join('%.1fHz(%.0fx)'%(f[b][i],p[b][i]/med) for i in idx)
want={'sensor_accel':['x','y','z'],'sensor_combined':['accelerometer_m_s2[0]','accelerometer_m_s2[2]'],'vehicle_acceleration':['xyz[0]','xyz[2]'],
 'vehicle_thrust_setpoint':['xyz[2]'],'vehicle_torque_setpoint':['xyz[0]'],'actuator_motors':['control[0]'],'vehicle_angular_velocity':['xyz[0]'],'trajectory_setpoint':['acceleration[2]']}
for d in u.data_list:
    if d.name in want and d.multi_id==0:
        t=(d.data['timestamp']-s)*1e-6; m=(t>=t0)&(t<t1)
        if m.sum()<200: continue
        for k in want[d.name]:
            if k in d.data: print(d.name,k,lines(t[m],d.data[k][m],20,130))
print([ (d.name,d.multi_id) for d in u.data_list if 'indi' in d.name])
