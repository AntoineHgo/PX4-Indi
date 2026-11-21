import sys, numpy as np
from pyulog import ULog
u = ULog(sys.argv[1])
def ds(n):
    return next(d for d in u.data_list if d.name == n)
s = ds('indi_rate_status'); t = s.data['timestamp']/1e6
inj = s.data.get('inject[2]')
nz = np.nonzero(inj)[0]
print('inject yaw first/last nonzero t', t[nz[0]] if len(nz) else None, t[nz[-1]] if len(nz) else None, 'max', np.max(np.abs(inj)))
for k in ['torque_sp[2]','torque_sp_pre_inject[2]','fault','landed']:
    if k in s.data: print(k, 'range', np.min(s.data[k]), np.max(s.data[k]))
a = ds('vehicle_attitude'); ta = a.data['timestamp']/1e6
q = np.vstack([a.data[f'q[{i}]'] for i in range(4)]).T
tilt = np.degrees(np.arccos(np.clip(1-2*(q[:,1]**2+q[:,2]**2),-1,1)))
for tt in np.arange(ta[0], ta[-1], 1.0):
    i = np.searchsorted(ta, tt); j = np.searchsorted(t, tt)
    ao = ds('actuator_motors'); tm = ao.data['timestamp']/1e6; k = min(np.searchsorted(tm, tt), len(tm)-1)
    m = [ao.data[f'control[{c}]'][k] for c in range(4)]
    print(f"{tt:6.1f} tilt {tilt[i]:5.1f} yawsp {s.data['torque_sp[2]'][min(j,len(t)-1)]:+.3f} inj {inj[min(j,len(t)-1)]:+.4f} mot {' '.join(f'{x:.2f}' for x in m)}")
v = ds('vehicle_angular_velocity'); tv = v.data['timestamp']/1e6
for c in range(3):
    w = v.data[f'xyz[{c}]']; sel = (tv > tv[-1]-6)
    print('rate', c, 'max abs last 6 s', np.max(np.abs(w[sel])))
