import numpy as np
from pyulog import ULog
u = ULog('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_campaign_f10/run_264/flight.ulg')
D = {d.name: d.data for d in u.data_list if d.multi_id == 0}
e = D['esc_status']; t = e['timestamp'] / 1e6
r = np.array([e['esc[%d].esc_rpm' % i] for i in range(4)])
for k in range(len(t) - 1):
    if t[k] > 58.8 and (r[2, k] - r[2, k + 1] > 1500):
        print('rpm2 dip onset %.3f' % t[k], r[2, k], '->', r[2, k + 1]); break
g = D['vehicle_attitude_groundtruth']; tt = g['timestamp'] / 1e6
q1, q2 = g['q[1]'], g['q[2]']
tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q1 ** 2 + q2 ** 2), -1, 1)))
i = np.argmax((tilt > 60) & (tt > 50)); print('tilt>60 at %.3f' % tt[i])
w = D['vehicle_angular_velocity']; tw = w['timestamp'] / 1e6
print('max |q| dps 59..abort', np.degrees(np.abs(w['xyz[1]'][(tw > 59) & (tw < tt[i])]).max()))
