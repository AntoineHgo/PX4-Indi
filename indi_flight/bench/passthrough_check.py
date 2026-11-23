"""S133: ulog check of a pass-through-mode flight. usage: passthrough_check.py flight.ulg
S215 (G7): verdict + exit code (0 PASS, 1 FAIL, 2 INVALID). PASS = window with pos/vel/alt all off exists, 0 att_sp and 0
indi_pos_status samples inside it (design/impl_s133). Absent or empty topic, or no window = not a pass (no IndexError)."""
import sys
import numpy as np
from pyulog import ULog
def invalid(why):
    print("INVALID:", why); print("RESULT INVALID"); sys.exit(2)
u = ULog(sys.argv[1], message_name_filter_list=None)
D = {}
for d in u.data_list:
    D.setdefault(d.name, []).append(d)
def info(n):
    for d in D.get(n, []):
        if not len(d.data["timestamp"]): print(f"{n}[{d.multi_id}] EMPTY"); continue
        print(f"{n}[{d.multi_id}] n={len(d.data['timestamp'])} t={d.data['timestamp'][0]/1e6:.2f}..{d.data['timestamp'][-1]/1e6:.2f}")
    if not D.get(n): print(n, "ABSENT")
for n in ("vehicle_attitude_setpoint", "vehicle_thrust_setpoint", "vehicle_torque_setpoint", "vehicle_rates_setpoint", "indi_pos_status", "takeoff_status", "trajectory_setpoint", "vehicle_local_position_setpoint"):
    info(n)
for n in ("vehicle_control_mode", "vehicle_status", "vehicle_attitude_setpoint", "indi_pos_status"):
    if not any(len(d.data["timestamp"]) for d in D.get(n, [])): invalid(n + " absent or empty")
D = {n: [d for d in l if len(d.data["timestamp"])] for n, l in D.items()}
vc = D["vehicle_control_mode"][0].data; t = vc["timestamp"]
for f in ("flag_control_position_enabled", "flag_control_velocity_enabled", "flag_control_altitude_enabled", "flag_control_climb_rate_enabled", "flag_control_attitude_enabled", "flag_control_rates_enabled", "flag_control_manual_enabled"):
    if f in vc: print(f, "values", sorted(set(vc[f].tolist())))
ns = D["vehicle_status"][0].data
print("nav_state values", sorted(set(ns["nav_state"].tolist())))
# armed window with pos/vel/alt all off
pv = (vc["flag_control_position_enabled"] | vc["flag_control_velocity_enabled"] | vc["flag_control_altitude_enabled"]).astype(bool)
off = ~pv
print("control_mode samples all-three-off:", int(off.sum()), "of", len(off))
n_att = n_pos = 0
if "vehicle_attitude_setpoint" in D:
    ts = np.concatenate([d.data["timestamp"] for d in D["vehicle_attitude_setpoint"]])
    # attitude sp samples falling in intervals where all off
    idx = np.searchsorted(t, ts, side="right") - 1
    idx = np.clip(idx, 0, len(t) - 1)
    n_att = int(off[idx].sum()); print("att_sp samples while pos/vel/alt all off:", n_att, "of", len(ts))
if "indi_pos_status" in D:
    ts = D["indi_pos_status"][0].data["timestamp"]
    idx = np.clip(np.searchsorted(t, ts, side="right") - 1, 0, len(t) - 1)
    n_pos = int(off[idx].sum()); print("indi_pos_status samples while all off:", n_pos, "of", len(ts))
ok = {"window_exists": bool(off.any()), "no_att_sp": n_att == 0, "no_indi_pos_status": n_pos == 0}
if not off.any(): print("pass-through never engaged: no sample with pos/vel/alt all off")
for k, x in ok.items(): print("%s %s" % ("PASS" if x else "FAIL", k))
res = all(ok.values()); print("RESULT", "PASS" if res else "FAIL"); sys.exit(0 if res else 1)
