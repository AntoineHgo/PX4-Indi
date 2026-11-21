import sys, json, numpy as np
from pyulog import ULog
# usage: omega_ff.py RUNDIR TOUCHDOWN_S   (touchdown on ulog time base, s since start_timestamp)
run = sys.argv[1]
u = ULog(run + '/flight.ulg')
s0 = u.start_timestamp
def get(name):
    d = [x for x in u.data_list if x.name == name]
    return d[0].data if d else None
vs = get('vehicle_status')
t_vs = (vs['timestamp'].astype(np.float64) - s0) * 1e-6
nav = vs['nav_state']
idx = np.where(nav == 18)[0]
if len(idx) == 0:
    print(json.dumps({'run': run.split('/')[-1], 'AUTO_LAND': 'never entered'})); sys.exit()
entry = t_vs[idx[0]]
ll = get('vehicle_land_detected'); t_ll = (ll['timestamp'].astype(np.float64) - s0) * 1e-6
land = np.where((t_ll >= entry) & (ll['landed'] == 1))[0]
td = t_ll[land[0]] if len(land) else float('nan')
ff = get('indi_rate_feedforward')
t_ff = (ff['timestamp'].astype(np.float64) - s0) * 1e-6
m = (t_ff >= entry) & (t_ff <= td)
r = np.degrees(ff['omega_ff[0]'][m]); p = np.degrees(ff['omega_ff[1]'][m])
av = get('vehicle_angular_velocity')
t_av = (av['timestamp'].astype(np.float64) - s0) * 1e-6
ma = (t_av >= entry) & (t_av <= td)
q = np.degrees(av['xyz[1]'][ma])
out = {'run': run.split('/')[-1], 'entry_s': round(entry, 2), 'touchdown_s': round(td, 2),
       'n_ff': int(m.sum()), 'omega_ff_roll_peak': round(float(np.max(np.abs(r))), 2) if r.size else None,
       'omega_ff_pitch_peak': round(float(np.max(np.abs(p))), 2) if p.size else None,
       'q_std_deg_s': round(float(np.std(q)), 2) if q.size else None,
       't_peak_rel_entry_s': round(float(t_ff[m][np.argmax(np.maximum(np.abs(r), np.abs(p)))] - entry), 2) if r.size else None}
print(json.dumps(out))
