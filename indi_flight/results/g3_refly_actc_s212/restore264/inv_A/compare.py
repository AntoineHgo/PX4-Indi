import sys, numpy as np
from pyulog import ULog
f, tf, t0, t1, dt = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
u = ULog(f)
def ds(n):
    try: return u.get_dataset(n).data
    except Exception: return None
def at(d, k, t):
    if d is None or k not in d: return np.nan
    i = np.searchsorted(d['timestamp']/1e6, t) - 1
    return d[k][max(i,0)]
att=ds('vehicle_attitude'); av=ds('vehicle_angular_velocity'); rs=ds('vehicle_rates_setpoint')
am=ds('actuator_motors'); esc=ds('esc_status'); cas=ds('control_allocator_status')
ts=ds('vehicle_thrust_setpoint'); tq=ds('vehicle_torque_setpoint'); irs=ds('indi_rate_status'); ips=ds('indi_pos_status')
atm=ds('actuator_torque_measured'); lp=ds('vehicle_local_position')
print('dt  tilt  p q r(dps) | psp qsp rsp | u0 u1 u2 u3 | rpm0..3 | Tz_sp | tq_sp xyz | unal_tq xyz unal_Tz sat0..3 | vz')
for t in np.arange(tf+t0, tf+t1, dt):
    q=[at(att,'q[%d]'%i,t) for i in range(4)]
    tilt=np.degrees(np.arccos(np.clip(1-2*(q[1]**2+q[2]**2),-1,1)))
    r=[np.degrees(at(av,'xyz[%d]'%i,t)) for i in range(3)]
    rsp=[np.degrees(at(rs,k,t)) for k in ('roll','pitch','yaw')]
    um=[at(am,'control[%d]'%i,t) for i in range(4)]
    rpm=[at(esc,'esc[%d].esc_rpm'%i,t) for i in range(4)]
    s='%5.2f %5.1f %6.0f %6.0f %6.0f | %6.0f %6.0f %5.0f | %s | %s | %5.2f | %s | %s %5.2f %s | %5.2f' % (t-tf, tilt, *r, *rsp,
      ' '.join('%4.2f'%x for x in um), ' '.join('%5.0f'%x for x in rpm), at(ts,'xyz[2]',t),
      ' '.join('%5.2f'%at(tq,'xyz[%d]'%i,t) for i in range(3)),
      ' '.join('%5.2f'%at(cas,'unallocated_torque[%d]'%i,t) for i in range(3)), at(cas,'unallocated_thrust[2]',t),
      ''.join('%d'%at(cas,'actuator_saturation[%d]'%i,t) for i in range(4)), at(lp,'vz',t))
    print(s)
    if irs is not None and '-i' in sys.argv:
        print('      INDI: tinc %s tfilt %s tsp %s meas %s valid %d fault %d | a_c %s thr %.2f t_c %s blend %.2f fail %d' % (
          ' '.join('%5.2f'%at(irs,'torque_increment[%d]'%i,t) for i in range(3)),
          ' '.join('%5.2f'%at(irs,'torque_filtered[%d]'%i,t) for i in range(3)),
          ' '.join('%5.2f'%at(irs,'torque_sp[%d]'%i,t) for i in range(3)),
          ' '.join('%5.2f'%at(atm,'torque[%d]'%i,t) for i in range(3)), at(atm,'valid',t), at(irs,'fault',t),
          ' '.join('%5.1f'%at(ips,'a_c[%d]'%i,t) for i in range(3)), at(ips,'thrust',t),
          ' '.join('%5.2f'%at(ips,'t_c[%d]'%i,t) for i in range(3)), at(ips,'blend',t), at(ips,'failure',t)))
