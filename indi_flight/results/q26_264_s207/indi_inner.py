import numpy as np
from tl import *
u,D=load('indi_264'); on=59.722
print('rel | pitch axis: nu  a_filt(rad/s2) tq_filt  tq_incr  tsp  tq_meas(eRPM)  tsp_pre_inject | roll same')
for r in np.arange(0.0,0.5,0.04):
    t=on+r; g=lambda k: at(D,'indi_rate_status',k,t)
    row=f'{r:+.2f}'
    for i in (1,0):
        row+=f' | nu {g("nu[%d]"%i):6.1f} a {g("angular_accel_filtered[%d]"%i):6.1f} tqf {g("torque_filtered[%d]"%i):.4f} inc {g("torque_increment[%d]"%i):.4f} tsp {g("torque_sp[%d]"%i):.4f} meas {at(D,"actuator_torque_measured","torque[%d]"%i,t):.4f} inUse {g("measured_torque_in_use"):.0f}'
    print(row)
