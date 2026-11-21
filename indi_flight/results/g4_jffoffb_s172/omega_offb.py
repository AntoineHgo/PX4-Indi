import sys, json, numpy as np
from pyulog import ULog
run = sys.argv[1]
u = ULog(run + '/flight.ulg'); s0 = u.start_timestamp
def get(name):
    d = [x for x in u.data_list if x.name == name]
    return d[0].data if d else None
def t_of(d): return (d['timestamp'].astype(np.float64) - s0) * 1e-6
vs = get('vehicle_status'); t_vs = t_of(vs); nav = vs['nav_state']
land_i = np.where(nav == 18)[0]
offb_i = np.where(nav == 14)[0]
entry = t_vs[land_i[0]] if len(land_i) else float('nan')
offb = t_vs[offb_i[0]] if len(offb_i) else float('nan')
ll = get('vehicle_land_detected'); t_ll = t_of(ll)
lr = np.where((t_ll >= entry) & (ll['landed'] == 1))[0]
td = t_ll[lr[0]] if len(lr) else float('nan')
ff = get('indi_rate_feedforward'); t_ff = t_of(ff)
av = get('vehicle_angular_velocity'); t_av = t_of(av)
def peak(t0, t1):
    m = (t_ff >= t0) & (t_ff <= t1)
    if not m.any(): return None, 0
    r = np.degrees(ff['omega_ff[0]'][m]); p = np.degrees(ff['omega_ff[1]'][m])
    return round(float(np.max(np.abs(np.r_[r, p]))), 3), int(np.count_nonzero(np.r_[r, p]))
land_pk, _ = peak(entry, td)
offb_pk, offb_nz = peak(offb, entry)
ma = (t_av >= entry) & (t_av <= td)
q = np.degrees(av['xyz[1]'][ma])
print(json.dumps({'run': run.split('/')[-1], 'offboard_entry_s': round(float(offb), 2), 'land_entry_s': round(float(entry), 2),
  'touchdown_s': round(float(td), 2), 'omega_ff_land_peak': land_pk, 'omega_ff_offb_peak': offb_pk,
  'omega_ff_offb_nonzero_samples': offb_nz, 'q_descent_std': round(float(np.std(q)), 2) if q.size else None}))
