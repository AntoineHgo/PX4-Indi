import sys,numpy as np
from pyulog import ULog
from common import R,eul
kind=sys.argv[1]; t1,t2,dt=float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
u=ULog(f'{R}{kind}_264/run_264/flight.ulg')
g=lambda n:[d for d in u.data_list if d.name==n and d.multi_id==0][0].data
ts=lambda d:d['timestamp'].astype(float)*1e-6
tg=np.arange(t1,t2,0.02)
rs=lambda n,k:np.interp(tg,ts(g(n)),g(n)[k])
m=np.array([rs('actuator_motors',f'control[{j}]') for j in range(4)])
rpm=np.array([rs('esc_status',f'esc[{j}].esc_rpm') for j in range(4)])
w=np.array([rs('vehicle_angular_velocity',f'xyz[{j}]') for j in range(3)])
q=[rs('vehicle_attitude',f'q[{j}]') for j in range(4)]; ro,pi_=eul(q)
tilt=np.degrees(np.arccos(np.clip(1-2*(q[1]**2+q[2]**2),-1,1)))
ts_=np.array([rs('vehicle_torque_setpoint',f'xyz[{j}]') for j in range(3)])
th=rs('vehicle_thrust_setpoint','xyz[2]')
un=np.array([rs('control_allocator_status',f'unallocated_torque[{j}]') for j in range(3)])
wsp=np.array([rs('vehicle_rates_setpoint',k) for k in ['roll','pitch','yaw']])
print(kind,'t | motors cmd 0..3 | rpm 0..3 | roll pitch tilt deg | w p q r dps | rate sp p q r | tau_sp r p y | thrust_sp | unalloc r p y')
for t in np.arange(t1,t2,dt):
    i=int((t-t1)/0.02)
    print(f"{t:5.2f} | "+' '.join(f'{x:.2f}' for x in m[:,i])+" | "+' '.join(f'{x:5.0f}' for x in rpm[:,i])+f" | {np.degrees(ro[i]):5.1f} {np.degrees(pi_[i]):5.1f} {tilt[i]:4.1f} | "+' '.join(f'{np.degrees(x):6.0f}' for x in w[:,i])+" | "+' '.join(f'{np.degrees(x):5.0f}' for x in wsp[:,i])+" | "+' '.join(f'{x:6.3f}' for x in ts_[:,i])+f" | {th[i]:.2f} | "+' '.join(f'{x:.3f}' for x in un[:,i]))
