#!/usr/bin/env python3
"""A-14: compare EKF2 height vs truth around the first |err|>0.5 m on the ground.
usage: a14_compare.py OUT.txt a.ulg [b.ulg ...]   (time = log timestamp s, log starts at boot)"""
import sys
import numpy as np
from pyulog import ULog

def get(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None

def at(t, d, f):  # sample-and-hold
    i = np.clip(np.searchsorted(d['timestamp'] / 1e6, t, 'right') - 1, 0, len(d['timestamp']) - 1)
    return d[f][i]

def main():
    out = open(sys.argv[1], 'w')
    def P(*a):
        s = ' '.join(str(x) for x in a); print(s); out.write(s + '\n')
    for path in sys.argv[2:]:
        u = ULog(path)
        P('=' * 70); P(path)
        P('topics:', sorted({d.name for d in u.data_list}))
        lp = get(u, 'vehicle_local_position'); gt = get(u, 'sim_ground_truth')
        st = get(u, 'vehicle_status')
        if st is not None and 'arming_state' in st:
            a = np.where(st['arming_state'] == 2)[0]
            P('first armed (vehicle_status) t=%.2f' % (st['timestamp'][a[0]] / 1e6 if len(a) else -1))
        tl = lp['timestamp'] / 1e6
        err = lp['z'] - at(tl, gt, 'z')
        m = (tl > 15) & (tl < 35) & (np.abs(err) > 0.5)
        P('err at t=10,20,25,29,31: ' + ' '.join('%.0f:%.2f' % (t, at(t, dict(timestamp=lp['timestamp'], e=err), 'e')) for t in (10, 20, 25, 29, 31)))
        if not m.any():
            P('no |err|>0.5 m in 15-35 s; max |err| = %.3f' % np.abs(err[(tl > 15) & (tl < 35)]).max()); t0 = 27.0
        else:
            t0 = tl[m][0]; P('FIRST |err|>0.5 at t=%.3f s err=%.3f' % (t0, err[m][0]))
        w = (t0 - 2, t0 + 2)
        def sel(d, tcol='timestamp'):
            t = d[tcol] / 1e6; return t, (t >= w[0]) & (t <= w[1])
        P('-- vehicle_local_position (every 0.25 s)')
        t, k = sel(lp); idx = np.where(k)[0]
        last = -9
        for i in idx:
            if t[i] - last >= 0.25:
                last = t[i]
                P('t=%.2f z=%.3f err=%.3f z_reset=%d dz=%.3f ref_alt=%.2f z_global=%s xy_global=%s' % (t[i], lp['z'][i], err[i], lp['z_reset_counter'][i], lp['delta_z'][i], lp['ref_alt'][i], lp['z_global'][i], lp['xy_global'][i]))
        P('-- flags / reset changes in window')
        sf = get(u, 'estimator_status_flags')
        fl = [f for f in sf if f.startswith(('cs_', 'fs_'))]
        base = {f: sf[f][np.searchsorted(sf['timestamp'] / 1e6, 15)] for f in fl}
        P('flags at t~15:', {f: int(v) for f, v in base.items() if f in ('cs_baro_hgt', 'cs_gps_hgt', 'cs_rng_hgt', 'cs_ev_hgt', 'cs_gnss_pos', 'cs_baro_fault', 'cs_gnss_hgt_fault', 'cs_in_air', 'cs_vehicle_at_rest')})
        ts = sf['timestamp'] / 1e6
        prev = None
        for i in range(len(ts)):
            if ts[i] < 15 or ts[i] > 35: prev = None; continue
            cur = {f: int(sf[f][i]) for f in fl}
            if prev is not None:
                ch = {f: (prev[f], cur[f]) for f in fl if prev[f] != cur[f]}
                if ch or sf['control_status_changes'][i] != sf['control_status_changes'][i - 1]:
                    P('t=%.3f flag change %s  ctrl_chg=%d fault_chg=%d' % (ts[i], ch, sf['control_status_changes'][i], sf['fault_status_changes'][i]))
            prev = cur
        for name in ('estimator_aid_src_baro_hgt', 'estimator_aid_src_gnss_hgt'):
            d = get(u, name)
            P('--', name)
            if d is None: P('absent'); continue
            t, k = sel(d); last = -9
            for i in np.where(k)[0]:
                if t[i] - last >= 0.25:
                    last = t[i]
                    P('t=%.2f obs=%.3f innov=%.3f ratio=%.2f fused=%d rej=%d' % (t[i], d['observation'][i], d['innovation'][i], d['test_ratio'][i], d['fused'][i], d['innovation_rejected'][i]))
        for name, fs in (('vehicle_air_data', ('baro_alt_meter', 'baro_pressure_pa')), ('sensor_baro', ('pressure',)), ('sensor_gps', ('alt', 'fix_type')), ('vehicle_gps_position', ('alt', 'fix_type')), ('estimator_baro_bias', ('bias',)), ('vehicle_global_position', ('alt', 'delta_alt', 'alt_reset_counter'))):
            d = get(u, name)
            P('--', name)
            if d is None: P('absent'); continue
            fs = [f for f in fs if f in d]
            t, k = sel(d); last = -9
            for i in np.where(k)[0]:
                if t[i] - last >= 0.5:
                    last = t[i]; P('t=%.2f ' % t[i] + ' '.join('%s=%.3f' % (f, d[f][i]) for f in fs))
        es = get(u, 'estimator_states')
        P('-- estimator_states pos_z[9], vel_z[6], accel bias z[15], baro-bias-ish, baro_bias[?] (states 0-3 quat,4-6 vel,7-9 pos,10-12 dang bias,13-15 dvel bias)')
        t, k = sel(es); last = -9
        for i in np.where(k)[0]:
            if t[i] - last >= 0.5:
                last = t[i]; P('t=%.2f velz=%.3f posz=%.3f dvb=%s' % (t[i], es['states[6]'][i], es['states[9]'][i], np.round([es['states[13]'][i], es['states[14]'][i], es['states[15]'][i]], 4)))
        ee = get(u, 'estimator_event_flags')
        if ee is not None:
            t, k = sel(ee)
            for i in np.where(k)[0]: P('event t=%.3f' % t[i], {f: int(ee[f][i]) for f in ee if f.startswith(('reset', 'starting', 'warning', 'gps_', 'height', 'stopping')) and ee[f][i]})
    out.close()
main()
