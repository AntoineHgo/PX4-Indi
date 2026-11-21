#!/usr/bin/env python3
"""List estimator reset-counter increments while airborne in each flight (post-freeze validity check, S162).
usage: reset_edge_sweep.py <flight.ulg> [...]   One line per flight: increments of vehicle_attitude.quat_reset_counter and
vehicle_local_position xy/z/vxy/vz/heading reset counters at samples where vehicle_land_detected.landed == 0."""
import sys
import numpy as np
from pyulog import ULog

CNT = {'vehicle_attitude': ['quat_reset_counter'],
       'vehicle_local_position': ['xy_reset_counter', 'z_reset_counter', 'vxy_reset_counter', 'vz_reset_counter',
                                  'heading_reset_counter']}


def edges(t, c):
    i = np.nonzero(np.diff(c.astype(np.int64)) != 0)[0] + 1
    return t[i]


def airborne_at(ld, tq):
    t, l = ld.data['timestamp'], ld.data['landed']
    k = np.searchsorted(t, tq, side='right') - 1
    return np.array([k_ >= 0 and l[k_] == 0 for k_ in k])


def selftest():
    t = np.arange(10.0)
    c = np.array([0, 0, 1, 1, 1, 2, 2, 2, 2, 2])
    assert list(edges(t, c)) == [2.0, 5.0]


selftest()
for f in sys.argv[1:]:
    try:
        u = ULog(f, message_name_filter_list=list(CNT) + ['vehicle_land_detected'])
    except Exception as e:  # noqa
        print(f'{f}: ERROR {e}')
        continue
    d = {x.name: x for x in u.data_list if x.multi_id == 0}
    out = []
    for topic, fields in CNT.items():
        if topic not in d:
            out.append(f'{topic} MISSING')
            continue
        for fl in fields:
            if fl not in d[topic].data:
                continue
            e = edges(d[topic].data['timestamp'], d[topic].data[fl])
            if 'vehicle_land_detected' in d and len(e):
                e = e[airborne_at(d['vehicle_land_detected'], e)]
            if len(e):
                out.append(f'{fl}@' + ','.join(f'{x/1e6:.2f}' for x in e))
    print(f'{f}: ' + ('; '.join(out) if out else 'none airborne'))
