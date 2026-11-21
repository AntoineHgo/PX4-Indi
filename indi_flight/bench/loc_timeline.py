#!/usr/bin/env python3
"""LOC timeline: python3 loc_timeline.py flight.ulg [t0 t1 [step]]  (ulog seconds)."""
import sys, numpy as np
from pyulog import ULog
u = ULog(sys.argv[1]); T0 = u.start_timestamp
t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 66
t1 = float(sys.argv[3]) if len(sys.argv) > 3 else 80
st = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
D = {}
def g(n, k):
    d = [x for x in u.data_list if x.name == n and x.multi_id == 0][0].data
    return (d['timestamp'] - T0) / 1e6, d[k]
def at(n, k, t):  # last sample at or before t (events / slow topics only; ZOH flagged by rate)
    tt, v = g(n, k); i = max(np.searchsorted(tt, t, 'right') - 1, 0); return v[i]
def tilt(q):
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[1]**2 + q[2]**2), -1, 1)))
tq, q0 = g('vehicle_attitude', 'q[0]')
qs = [g('vehicle_attitude', f'q[{i}]')[1] for i in range(4)]
tr = lambda t: tilt([c[np.searchsorted(tq, t)] for c in qs])
print('t  nav land(gc,ml,ld) z_agl_truth  thr_sp  mot_max/min  motors>=0.99  tilt  rate_err(p,q,r)  meas_torque_in_use fault tqvalid motor_valid frozen  pos:thr blend hold frz mean_u_valid stage')
for t in np.arange(t0, t1, st):
    nav = at('vehicle_status', 'nav_state', t)
    ld = [int(at('vehicle_land_detected', k, t)) for k in ('ground_contact', 'maybe_landed', 'landed')]
    z = -at('sim_ground_truth', 'z', t)
    tt, thr = g('vehicle_thrust_setpoint', 'xyz[2]') if False else g('vehicle_thrust_setpoint', 'xyz[2]')
    i = np.searchsorted(tt, t)
    tm, _ = g('actuator_motors', 'control[0]')
    j = np.searchsorted(tm, t)
    mc = np.array([g('actuator_motors', f'control[{k}]')[1][j:j + 40] for k in range(4)])
    rs = [at('vehicle_rates_setpoint', k, t) for k in ('roll', 'pitch', 'yaw')]
    om = [g('vehicle_angular_velocity', f'xyz[{k}]')[1][np.searchsorted(g('vehicle_angular_velocity','xyz[0]')[0], t)] for k in range(3)]
    sp = [at('indi_rate_status', f'rates_sp_applied[{k}]', t) for k in range(3)]
    er = [round(sp[k] - om[k], 2) for k in range(3)]
    print(f"{t:.2f} {int(nav)} {ld} z={z:.2f} thr={-thr[i]:.2f} mot={mc.max():.2f}/{mc.min():.2f} sat={(mc>=0.99).sum()} tilt={tr(t):.0f} err={er} "
          f"mt={int(at('indi_rate_status','measured_torque_in_use',t))} f={int(at('indi_rate_status','fault',t))} "
          f"v={int(at('actuator_torque_measured','valid',t))} mv={int(at('actuator_torque_measured','motor_valid_mask',t))} fz={int(at('actuator_torque_measured','motor_frozen_mask',t))} "
          f"pos:{at('indi_pos_status','thrust',t):.2f} {at('indi_pos_status','blend',t):.2f} {int(at('indi_pos_status','blend_hold',t))} {int(at('indi_pos_status','blend_frozen',t))} {int(at('indi_pos_status','mean_u_valid',t))} {int(at('indi_pos_status','stage_mode',t))}")
