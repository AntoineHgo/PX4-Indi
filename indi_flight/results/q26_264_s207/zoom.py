import numpy as np,sys
from tl import *
for p,a,b in [('indi_264',59.64,59.92),('pid_264',59.54,59.82)]:
    u,D=load(p); print('==',p)
    for t in np.arange(a,b,0.02):
        m=[at(D,'actuator_motors','control[%d]'%i,t) for i in range(4)]
        r=[rpm(D,i,t) for i in range(4)]
        ts_=[at(D,'vehicle_torque_setpoint','xyz[%d]'%i,t) for i in range(3)]
        th=at(D,'vehicle_thrust_setpoint','xyz[2]',t)
        w=[np.degrees(at(D,'vehicle_angular_velocity','xyz[%d]'%i,t)) for i in range(3)]
        s=f'{t:.2f} m {" ".join("%.2f"%x for x in m)} rpm {" ".join("%5.0f"%x for x in r)} tsp {" ".join("%.3f"%x for x in ts_)} T {th:.2f} w {" ".join("%4.0f"%x for x in w)}'
        if p=='indi_264':
            s+=' meas '+" ".join("%.3f"%at(D,'actuator_torque_measured','torque[%d]'%i,t) for i in range(3))+' valid %d'%at(D,'actuator_torque_measured','valid',t)+' fz %d'%at(D,'actuator_torque_measured','motor_frozen_mask',t)+' fault %d'%at(D,'indi_rate_status','fault',t)
        print(s)
