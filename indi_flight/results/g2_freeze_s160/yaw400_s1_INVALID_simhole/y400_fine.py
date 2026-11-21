import sys, numpy as np
from pyulog import ULog
u = ULog(sys.argv[1]); t0, t1 = float(sys.argv[2]), float(sys.argv[3])
def ds(n): return next(d for d in u.data_list if d.name == n)
def at(d, f, tt):
    tm = d.data['timestamp']/1e6; k = min(np.searchsorted(tm, tt), len(tm)-1); return d.data[f][k]
s = ds('indi_rate_status'); v = ds('vehicle_angular_velocity'); m = ds('actuator_motors'); r = ds('vehicle_rates_setpoint')
print('indi_rate_status fields:', ' '.join(k for k in s.data if '[' not in k or k.endswith('[0]'))[:600])
for tt in np.arange(t0, t1, 0.02):
    print(f"{tt:6.2f} w {at(v,'xyz[0]',tt):+6.2f} {at(v,'xyz[1]',tt):+6.2f} sp {at(r,'roll',tt):+6.2f} {at(r,'pitch',tt):+6.2f} tq {at(s,'torque_sp[0]',tt):+.3f} {at(s,'torque_sp[1]',tt):+.3f} mot "
          + ' '.join(f"{at(m,f'control[{c}]',tt):.2f}" for c in range(4)))
dt = np.diff(v.data['timestamp'])/1e3; tv = v.data['timestamp'][1:]/1e6; sel=(tv>t0-5)&(tv<t1)
print('gyro dt ms max', dt[sel].max(), 'at', tv[sel][np.argmax(dt[sel])])
ds2 = np.diff(s.data['timestamp'])/1e3; ts = s.data['timestamp'][1:]/1e6; sel=(ts>t0-5)&(ts<t1)
print('indi dt ms max', ds2[sel].max(), 'at', ts[sel][np.argmax(ds2[sel])])
for msg in u.logged_messages[-15:]: print('LOG', msg.timestamp/1e6, msg.message[:120])
