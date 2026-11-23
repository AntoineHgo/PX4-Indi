import sys,numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); t0=float(sys.argv[2])
def g(n,i=0):
    L=[d for d in u.data_list if d.name==n and d.multi_id==i]; return L[0].data if L else None
T=lambda d:d['timestamp']*1e-6
def eul(qw,qx,qy,qz):
    r=np.degrees(np.arctan2(2*(qw*qx+qy*qz),1-2*(qx*qx+qy*qy))); p=np.degrees(np.arcsin(np.clip(2*(qw*qy-qz*qx),-1,1))); return r,p
at=g('vehicle_attitude'); sp=g('vehicle_attitude_setpoint'); th=g('vehicle_thrust_setpoint'); lp=g('vehicle_local_position'); ls=g('vehicle_local_position_setpoint') or g('trajectory_setpoint')
ra,pa=eul(*[at[f'q[{j}]'] for j in range(4)]); rs,ps=eul(*[sp[f'q_d[{j}]'] for j in range(4)])
I=lambda t,d,x: np.interp(t,T(d),x)
print("t | roll pitch | roll_sp pitch_sp | thrust_sp_body_z(att_sp) | thrust_sp(z) | vz alt-z")
for t in np.arange(t0,t0+1.2,0.05):
    print(f"{t:6.2f} | {I(t,at,ra):6.1f} {I(t,at,pa):6.1f} | {I(t,sp,rs):6.1f} {I(t,sp,ps):6.1f} | {I(t,sp,sp['thrust_body[2]']):+.3f} | {I(t,th,th['xyz[2]']):+.3f} | {I(t,lp,lp['vz']):+.2f} {I(t,lp,lp['z']):+.2f}")
