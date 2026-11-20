#!/usr/bin/env python3
"""Independent second key for G5.8 / G5.9 rows. usage: g5_rows_key2.py <flight_dir>"""
import json, sys, os
import numpy as np
from pyulog import ULog

d = sys.argv[1]
run = json.load(open(os.path.join(d, 'run.json')))
ev = {e['name']: e for e in run['g5_events']}
u = ULog(os.path.join(d, 'flight.ulg'))
D = {}
for x in u.data_list:
    D[(x.name, x.multi_id)] = x.data
S = 1e-6
out = []
def P(s):
    print(s); out.append(s)

def param(name, t_us):
    v = u.initial_parameters.get(name)
    for t, n, val in u.changed_parameters:
        if n == name and t <= t_us:
            v = val
    return v

def edges(ts, a, up=True):
    a = np.asarray(a).astype(int)
    i = np.nonzero(np.diff(a))[0] + 1
    return [(ts[k] * S, a[k]) for k in i]

# ---- rates / command period
ir = D[('indi_rate_status', 0)]
tsr = ir['timestamp']
rate = (len(tsr) - 1) / ((tsr[-1] - tsr[0]) * S)
Tcmd = 1.0 / rate
P(f'# key2 rows for {d}: indi_rate_status logged rate {rate:.1f} Hz -> command period {Tcmd*1e3:.3f} ms '
  f'(IMU_GYRO_RATEMAX={u.initial_parameters.get("IMU_GYRO_RATEMAX")})')

# ---- G5.8
vs = D[('vehicle_status', 0)]; ff = D[('failsafe_flags', 0)]
vts = vs['timestamp']
nav_ch = [(vts[i] * S, int(vs['nav_state'][i])) for i in range(1, len(vts)) if vs['nav_state'][i] != vs['nav_state'][i-1]]
fs_ch = edges(vts, vs['failsafe'])
navts = vs['nav_state_timestamp']
navts_ch = [(vts[i] * S, navts[i] * S) for i in range(1, len(vts)) if navts[i] != navts[i-1]]
def state_at(t):
    cur = int(vs['nav_state'][0]); f = int(vs['failsafe'][0])
    for tt, v in nav_ch:
        if tt <= t: cur = v
    for tt, v in fs_ch:
        if tt <= t: f = v
    return cur, f
def first_after(lst, t, pred=lambda v: True):
    for tt, v in lst:
        if tt >= t and pred(v): return tt
    return None
def flag_rise(name, t):
    return first_after(edges(ff['timestamp'], ff[name]), t, lambda v: v == 1)

# RC loss
t_ev = ev['rc_loss']['t_applied_us'] * S
T = param('COM_RC_LOSS_T', ev['rc_loss']['t_applied_us']); act = param('NAV_RCL_ACT', ev['rc_loss']['t_applied_us'])
rise = flag_rise('manual_control_signal_lost', t_ev)
ref = rise - T
ent = first_after(fs_ch, t_ev, lambda v: v == 1)
nv = first_after(nav_ch, t_ev)
ns0, f0 = state_at(t_ev)
dt = ent - ref
P(f'G5.8 rc_loss: COM_RC_LOSS_T={T} NAV_RCL_ACT={act}; ref=flag rise {rise:.4f} - T = {ref:.4f} s; vehicle_status.failsafe rise {ent:.4f} '
  f'(period 0.5 s log) -> entry-ref {dt:.3f} s; nav_state before={ns0}, nav_state change next={nv}; action hold=nav 4 (already loiter, no change observable) '
  f'-> {"PASS" if dt <= 1 and state_at(ent)[0]==4 else "FAIL"}')

# link loss
ts_all = []
for m in range(4):
    t = D.get(('telemetry_status', m))
    if t is None: continue
    ts_all += [x * S for x, h in zip(t['timestamp'], t['heartbeat_type_gcs']) if h]
ts_all = np.array(sorted(ts_all))
e = ev['link_loss']; t_ev = e['t_applied_us'] * S
T = param('COM_DL_LOSS_T', e['t_applied_us']); act = param('NAV_DLL_ACT', e['t_applied_us'])
rise = flag_rise('gcs_connection_lost', t_ev)
last_hb = ts_all[ts_all < rise].max()
ref = last_hb + T
ent = first_after(fs_ch, t_ev, lambda v: v == 1)
ns0, f0 = state_at(t_ev)
nv = first_after(nav_ch, t_ev)
# failsafe flag was already 1 (from rc loss)? then entry not observable on vehicle_status
P(f'G5.8 link_loss: COM_DL_LOSS_T={T} NAV_DLL_ACT={act}; last heartbeat_type_gcs (telemetry_status, any instance) {last_hb:.4f}; ref {ref:.4f}; '
  f'gcs_connection_lost rise {rise:.4f} (flag log 2 Hz) -> rise-ref {rise-ref:.3f} s; at t_ev nav_state={ns0} failsafe={f0}; next nav_state change {nv}; '
  f'entry on vehicle_status NOT observable if failsafe already 1 (rise found after event: {ent}) -> '
  f'{"PASS(flag only, state already hold)" if rise-ref<=1 and state_at(rise+1)[0]==4 else "FAIL"}')

# offboard loss
e = ev['offboard_loss']; t_ev = e['t_applied_us'] * S
T = param('COM_OF_LOSS_T', e['t_applied_us']); act = param('COM_OBL_RC_ACT', e['t_applied_us'])
oc = D[('offboard_control_mode', 0)]['timestamp'] * S
last = oc[oc <= t_ev + 0.5].max()
ref = last + T
nv = first_after(nav_ch, t_ev, lambda v: v != 14)
rise = flag_rise('offboard_control_signal_lost', t_ev)
fs = first_after(fs_ch, t_ev, lambda v: v == 1)
P(f'G5.8 offboard_loss: COM_OF_LOSS_T={T} COM_OBL_RC_ACT={act}; last offboard_control_mode {last:.4f}; ref {ref:.4f}; flag rise {rise:.4f}; '
  f'nav_state leaves offboard {nv:.4f} -> {int(dict(nav_ch)[nv])} (expect 4 hold) failsafe rise {fs:.4f}; entry-ref {nv-ref:.3f} s -> '
  f'{"PASS" if nv-ref<=1 and dict(nav_ch)[nv]==4 else "FAIL"}')

# ---- G5.9 kill
sw = D[('manual_control_switches', 0)]
k = edges(sw['timestamp'], sw['kill_switch'])
t_k = ev['kill']['t_applied_us'] * S
t_sw = first_after(k, t_ev if False else t_k - 0.5, lambda v: v == 1)
ar = D[('actuator_armed', 0)]
t_arm_kill = first_after(edges(ar['timestamp'], ar['kill']), t_sw - 0.1, lambda v: v == 1)
t_dis = first_after(edges(ar['timestamp'], ar['armed']), t_sw, lambda v: v == 0)
ao = D[('actuator_outputs', 0)]; ta = ao['timestamp'] * S; o = np.stack([ao['output[%d]' % i] for i in range(4)], 1)
# all-zero from time x until disarm
z = np.all(o == 0, axis=1)
w = (ta >= t_sw - 0.1) & (ta <= t_dis)
idx = np.nonzero(w)[0]
t_zero = None
for j in range(len(idx)):
    if z[idx[j]:idx[-1]+1].all(): t_zero = ta[idx[j]]; break
pre = o[(ta > t_sw - 0.05) & (ta <= t_sw)].mean(0)
per_ao = np.median(np.diff(ta[(ta > t_sw - 1) & (ta < t_sw)]))
P(f'G5.9 kill: switch change {t_sw:.4f}; actuator_armed.kill rise {t_arm_kill:.4f} (+{(t_arm_kill-t_sw)*1e3:.1f} ms); outputs all 4 == 0 until disarm({t_dis:.3f}) from {t_zero:.5f} '
  f'(+{(t_zero-t_arm_kill)*1e3:.2f} ms after kill rise, +{(t_zero-t_sw)*1e3:.2f} ms after switch); pre-kill outputs {np.round(pre,1)}; '
  f'actuator_outputs period {per_ao*1e3:.2f} ms, command period {Tcmd*1e3:.2f} ms -> {"PASS" if t_zero-t_sw<=Tcmd else "FAIL"} (limit one command period from switch)')
# ---- G5.9 rearm
t_rearm = first_after(edges(ar['timestamp'], ar['armed']), t_sw, lambda v: v == 1)
ip = D[('indi_pos_status', 0)]; tp = ip['timestamp'] * S
tb = ir['timestamp'] * S
def A3(dd, n): return np.stack([dd['%s[%d]' % (n, i)] for i in range(3)], 1)
def nz(x): return float(np.max(np.abs(x))) if np.size(x) else float('nan')
pre = (tp > t_dis) & (tp < t_rearm)
P(f'G5.9 rearm at {t_rearm:.4f} (actuator_armed); indi_pos_status samples between disarm and arm: {int(pre.sum())} (last at {tp[tp<t_rearm].max():.3f})')
for name, tt, src in (('blend', tp, ip['blend']), ('hold_cycles', tp, ip['hold_cycles']),
                      ('torque_filtered', tb, A3(ir,'torque_filtered')), ('rate_sp_dot', tb, A3(ir,'rate_sp_dot'))):
    m = (tt >= t_rearm)
    first = np.nonzero(m)[0][0]
    n = 5
    v = np.abs(src[first:first+n]).reshape(n, -1).max(1) if src.ndim == 2 else np.abs(src[first:first+n])
    m1 = (tt >= t_rearm) & (tt < t_rearm + 0.2)
    mx = nz(src[m1])
    last_before = np.nonzero(tt < t_sw)[0][-1]
    P(f'  {name}: pre-kill last sample (t={tt[last_before]:.3f}) maxabs {nz(src[last_before]):.4g}; first sample after arm (t={tt[first]:.4f}) maxabs {v[0]:.4g}; max over first 0.2 s {mx:.4g}')
# first second motor change
w = (ta >= t_rearm) & (ta <= t_rearm + 1.0)
oo = o[w]
W = float(param('MC_INDI_W_MAX', int(t_rearm / S)))
rng = oo.max(0) - oo.min(0)
P(f'G5.9 rearm first-second motor command change (actuator_outputs, same units): units max {o.max():.1f}; ctrl-at-arm {np.round(oo[0],1)}; end {np.round(oo[-1],1)}; '
  f'range per motor {np.round(rng,1)} -> max {rng.max():.1f} units = {rng.max()/W*100:.2f} % of full scale W={W:.0f} (MC_INDI_W_MAX; output is rotor speed, hover ~ W*sqrt(MPC_THR_HOVER))')
# takeoff handover
tk = D[('takeoff_status', 0)]; ttk = tk['timestamp']
st = edges(ttk, tk['takeoff_state'])
t_edge = first_after([(a, b) for a, b in st], t_rearm, lambda v: v == 5)
P(f'  takeoff_state edges after rearm: {[(round(a,3),int(b)) for a,b in st if a>t_rearm][:4]} (4 rampup -> 5 flight at {t_edge:.4f})')
hov = param('MPC_THR_HOVER', int(t_edge / S))
th = ip['thrust']
b = th[(tp >= t_edge - 0.1) & (tp < t_edge)].mean(); a_ = th[(tp >= t_edge) & (tp < t_edge + 0.1)].mean()
step = a_ - b
gt = D[('vehicle_local_position_groundtruth', 0)]; tg = gt['timestamp'] * S
alt = -gt['z']
z0 = alt[(tg >= t_edge - 0.05) & (tg <= t_edge)].mean()
w = (tg >= t_edge) & (tg <= t_edge + 1.0)
dip = max(0.0, z0 - alt[w].min())
P(f'G5.9 take-off handover: thrust before {b:.4f} after {a_:.4f} step {step:+.4f} vs MPC_THR_HOVER {hov:.4f} -> {abs(step)/hov*100:.1f} % of hover '
  f'({"PASS" if abs(step)<=0.1*hov else "FAIL"}, limit 10 %); truth altitude dip within 1 s {dip:.3f} m (alt at edge {z0:.3f}) '
  f'-> {"PASS" if dip<=0.3 else "FAIL"} (limit 0.3 m)')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'g5_events_s145', 'key2_rows.md'), 'w').write('\n'.join(out) + '\n')
