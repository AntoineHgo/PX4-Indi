#!/usr/bin/env python3
"""Second key for G5.4 landing speed and contact->disarm (GATES.md section 5).
usage: g54_land_key2.py RUN_DIR...  Final descent = truth z_up from 2.0 m down to 0.3 m above the touchdown altitude
(window stated here; key1 window not consulted). Contact = first vehicle_land_detected.ground_contact rise after the
last time truth altitude was above 2 m; disarm = vehicle_status.arming_state leaving ARMED (2)."""
import sys, os
import numpy as np
from pyulog import ULog
for d in sys.argv[1:]:
    u = ULog(os.path.join(d, 'flight.ulg'))
    g = lambda n: u.get_dataset(n).data
    gt = g('vehicle_local_position_groundtruth'); t = gt['timestamp'] * 1e-6; zu = -gt['z']; vz = gt['vz']
    z0 = zu[-1]
    hi = np.nonzero(zu - z0 > 2.0)[0][-1]
    w = np.arange(hi, len(t)); w = w[(zu[w] - z0 <= 2.0) & (zu[w] - z0 >= 0.3)]
    vmean = float(np.mean(vz[w]))
    ld = g('vehicle_land_detected'); lt = ld['timestamp'] * 1e-6; gc = ld['ground_contact']
    k = np.nonzero((gc[1:] == 1) & (gc[:-1] == 0) & (lt[1:] > t[hi]))[0]
    tc = lt[k[0] + 1]
    vs = g('vehicle_status'); vt = vs['timestamp'] * 1e-6; a = vs['arming_state']
    j = np.nonzero((a[:-1] == 2) & (a[1:] != 2) & (vt[1:] > tc))[0]
    td = vt[j[0] + 1]
    p = dict(u.initial_parameters); ls = p['MPC_LAND_SPEED']; dl = p['COM_DISARM_LAND']
    ok1 = abs(vmean - ls) <= 0.2 * ls; ok2 = td - tc <= dl + 1.0
    print(f'{os.path.basename(d)}: mean vz {vmean:.3f} (window {t[w[0]]:.2f}-{t[w[-1]]:.2f} s) vs {ls:.2f} +-20% '
          f'{"PASS" if ok1 else "FAIL"}; contact {tc:.2f} disarm {td:.2f} -> {td-tc:.2f} s vs {dl+1:.1f} {"PASS" if ok2 else "FAIL"}')
