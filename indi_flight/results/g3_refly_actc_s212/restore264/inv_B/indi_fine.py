import sys, numpy as np
from pyulog import ULog
u=ULog(sys.argv[1]); t0,t1,st=map(float,sys.argv[2:5])
D={n:u.get_dataset(n).data for n in ('indi_rate_status','actuator_torque_measured','vehicle_attitude','actuator_motors','vehicle_angular_velocity','indi_pos_status')}
def at(n,k,t):
    d=D[n]; i=min(max(np.searchsorted(d['timestamp'],t*1e6)-1,0),len(d['timestamp'])-1); return d[k][i]
print('t | rate p q | sp p q | nu p q | a_f p q | t_f p q | t_meas p q | blend=tf-tm p q | dT p q | tsp p q | tilt | m0..3 | pos: a_c z, thrust, mean_u')
for t in np.arange(t0,t1,st):
    I='indi_rate_status'; q=[at('vehicle_attitude',f'q[{i}]',t) for i in range(4)]
    tilt=np.degrees(np.arccos(np.clip(1-2*(q[1]**2+q[2]**2),-1,1)))
    f=lambda n,k: ' '.join(f"{at(n,k.format(i),t):+6.2f}" for i in range(2))
    tf=[at(I,f'torque_filtered[{i}]',t) for i in range(2)]; tm=[at('actuator_torque_measured',f'torque[{i}]',t) for i in range(2)]
    print(f"{t:6.2f} |{f('vehicle_angular_velocity','xyz[{}]')} |{f(I,'rates_sp_applied[{}]')} |"+' '.join(f"{at(I,f'nu[{i}]',t):+6.0f}" for i in range(2))+' |'+' '.join(f"{at(I,f'angular_accel_filtered[{i}]',t):+6.0f}" for i in range(2))
          +f" |{f(I,'torque_filtered[{}]')} |{f('actuator_torque_measured','torque[{}]')} | {tf[0]-tm[0]:+.3f} {tf[1]-tm[1]:+.3f} |{f(I,'torque_increment[{}]')} |{f(I,'torque_sp[{}]')} |{tilt:5.1f} |"
          +' '.join(f"{at('actuator_motors',f'control[{i}]',t):.2f}" for i in range(4))+f" | {at('indi_pos_status','a_c[2]',t):+5.1f} {at('indi_pos_status','thrust',t):+.2f} {at('indi_pos_status','mean_u',t):.2f}")
