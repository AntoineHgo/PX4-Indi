import sys,numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); dt=float(sys.argv[2]) if len(sys.argv)>2 else 0.1
def g(n,i=0):
    L=[d for d in u.data_list if d.name==n and d.multi_id==i]; return L[0].data if L else None
T=lambda d:d['timestamp'].astype(float)*1e-6
at=g('vehicle_attitude'); ta=T(at); q=[at[f'q[{j}]'] for j in range(4)]
tilt=np.degrees(np.arccos(np.clip(1-2*(q[1]**2+q[2]**2),-1,1)))
t0a=float(sys.argv[3]); k=np.argmax((tilt>60)&(ta>t0a)) if ((tilt>60)&(ta>t0a)).any() else -1; tl=ta[k] if k>=0 else t0a+3.0
m=g('actuator_motors'); tm=T(m); mot=np.array([m[f'control[{j}]'] for j in range(4)])
# fault: first time max motor jumps? use motor mean step: find first time after tl-6 where mean motor rises >0.1 within 0.3s
mm=mot.mean(0)
print("tilt>60 at %.2f"%tl)
ne=max(d.multi_id for d in u.data_list if d.name=='esc_status'); e=g('esc_status',int(sys.argv[4]) if len(sys.argv)>4 else 0); te=T(e); print('esc instances 0..',ne); rpm=np.array([e[f'esc[{j}].esc_rpm'] for j in range(4)])
cs=g('control_allocator_status'); tc=T(cs)
sat=np.array([cs[f'actuator_saturation[{j}]'] for j in range(4)]); un=np.array([cs[f'unallocated_torque[{j}]'] for j in range(3)])
ts=g('vehicle_torque_setpoint'); tt=T(ts); tsp=np.array([ts[f'xyz[{j}]'] for j in range(3)])
av=g('vehicle_angular_velocity'); tw=T(av); w=np.degrees(np.array([av[f'xyz[{j}]'] for j in range(3)]))
rs=g('vehicle_rates_setpoint'); tr=T(rs); wsp=np.degrees(np.array([rs[k] for k in ('roll','pitch','yaw')]))
ir=g('indi_rate_status')
I=lambda t,tt,x: np.interp(t,tt,x)
t0=t0a
print(" t     | mot0..3              | rpm0..3                 | sat0..3   | tsp r p y            | unall r p y        | w p q r       | wsp p q r     | tilt")
for t in np.arange(t0,tl+0.15,dt):
    s=f"{t:6.2f}| "+" ".join(f"{I(t,tm,x):.2f}" for x in mot)+" | "+" ".join(f"{I(t,te,x):5.0f}" for x in rpm)
    s+=" | "+" ".join(f"{int(round(I(t,tc,x))):+d}" for x in sat)+" | "+" ".join(f"{I(t,tt,x):+.3f}" for x in tsp)
    s+=" | "+" ".join(f"{I(t,tc,x):+.3f}" for x in un)+" | "+" ".join(f"{I(t,tw,x):+4.0f}" for x in w)+" | "+" ".join(f"{I(t,tr,x):+4.0f}" for x in wsp)+f" | {I(t,ta,tilt):4.1f}"
    print(s)
if ir is not None:
    ti=T(ir)
    print("INDI: t | nu p q r | acc_f p q r | tq_meas_f r p y | tq_inc r p y | tq_sp r p y")
    for t in np.arange(t0,tl+0.15,dt):
        f=lambda k:" ".join(f"{I(t,ti,ir[f'{k}[{j}]']):+7.3f}" for j in range(3))
        print(f"{t:6.2f}| {f('nu')} | {f('angular_accel_filtered')} | {f('torque_filtered')} | {f('torque_increment')} | {f('torque_sp')}")
