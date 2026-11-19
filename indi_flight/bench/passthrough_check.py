"""S133: ulog check of a pass-through-mode flight. usage: passthrough_check.py flight.ulg"""
import sys
import numpy as np
from pyulog import ULog
u = ULog(sys.argv[1], message_name_filter_list=None)
D = {}
for d in u.data_list:
    D.setdefault(d.name, []).append(d)
def info(n):
    for d in D.get(n, []):
        print(f"{n}[{d.multi_id}] n={len(d.data['timestamp'])} t={d.data['timestamp'][0]/1e6:.2f}..{d.data['timestamp'][-1]/1e6:.2f}")
    if n not in D: print(n, "ABSENT")
for n in ("vehicle_attitude_setpoint", "vehicle_thrust_setpoint", "vehicle_torque_setpoint", "vehicle_rates_setpoint", "indi_pos_status", "takeoff_status", "trajectory_setpoint", "vehicle_local_position_setpoint"):
    info(n)
vc = D["vehicle_control_mode"][0].data; t = vc["timestamp"]
for f in ("flag_control_position_enabled", "flag_control_velocity_enabled", "flag_control_altitude_enabled", "flag_control_climb_rate_enabled", "flag_control_attitude_enabled", "flag_control_rates_enabled", "flag_control_manual_enabled"):
    if f in vc: print(f, "values", sorted(set(vc[f].tolist())))
ns = D["vehicle_status"][0].data
print("nav_state values", sorted(set(ns["nav_state"].tolist())))
# armed window with pos/vel/alt all off
pv = (vc["flag_control_position_enabled"] | vc["flag_control_velocity_enabled"] | vc["flag_control_altitude_enabled"]).astype(bool)
off = ~pv
print("control_mode samples all-three-off:", int(off.sum()), "of", len(off))
if "vehicle_attitude_setpoint" in D:
    ts = np.concatenate([d.data["timestamp"] for d in D["vehicle_attitude_setpoint"]])
    # attitude sp samples falling in intervals where all off
    idx = np.searchsorted(t, ts, side="right") - 1
    idx = np.clip(idx, 0, len(t) - 1)
    print("att_sp samples while pos/vel/alt all off:", int(off[idx].sum()), "of", len(ts))
if "indi_pos_status" in D:
    ts = D["indi_pos_status"][0].data["timestamp"]
    idx = np.clip(np.searchsorted(t, ts, side="right") - 1, 0, len(t) - 1)
    print("indi_pos_status samples while all off:", int(off[idx].sum()), "of", len(ts))
