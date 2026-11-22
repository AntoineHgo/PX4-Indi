import numpy as np
from tl import *
d=lambda x: np.degrees(x)
for p,on in [('indi_264',59.722),('pid_264',59.618)]:
    u,D=load(p); print('== %s onset %.3f (t rel)'%(p,on))
    for r in np.arange(-0.02,0.60,0.04):
        t=on+r
        w=[d(at(D,'vehicle_angular_velocity','xyz[%d]'%i,t)) for i in range(3)]
        s=[d(at(D,'vehicle_rates_setpoint',k,t)) for k in ['roll','pitch','yaw']]
        ts_=[at(D,'vehicle_torque_setpoint','xyz[%d]'%i,t) for i in range(3)]
        m=[at(D,'actuator_motors','control[%d]'%i,t) for i in range(4)]
        l=f'{r:+.2f} tilt {tilt(D,t):4.0f} w {w[0]:4.0f} {w[1]:4.0f} {w[2]:4.0f} sp {s[0]:5.0f} {s[1]:5.0f} {s[2]:5.0f} tsp {ts_[0]:.3f} {ts_[1]:.3f} {ts_[2]:.3f} m {" ".join("%.2f"%x for x in m)}'
        if p=='indi_264':
            a=[d(at(D,'indi_rate_status','angular_accel_filtered[%d]'%i,t)) for i in range(3)]
            nu=[at(D,'indi_rate_status','nu[%d]'%i,t) for i in range(3)]
            inj=[d(at(D,'indi_rate_status','rates_sp_applied[%d]'%i,t)) for i in range(3)]
            l+=f' | accf {a[0]:5.0f} {a[1]:5.0f} {a[2]:5.0f} nu {nu[0]:6.1f} {nu[1]:6.1f} {nu[2]:6.1f} sp_app {inj[0]:5.0f} {inj[1]:5.0f} {inj[2]:5.0f}'
        print(l)
