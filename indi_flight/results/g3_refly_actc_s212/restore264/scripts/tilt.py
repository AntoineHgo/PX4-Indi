import sys, numpy as np
from pyulog import ULog
for f in sys.argv[1:]:
    u = ULog(f)
    at = [d for d in u.data_list if d.name == 'vehicle_attitude'][0].data
    t = at['timestamp'] * 1e-6
    tilt = np.degrees(np.arccos(np.clip(1 - 2 * (at['q[1]'] ** 2 + at['q[2]'] ** 2), -1, 1)))
    pt = [x[0] * 1e-6 for x in u.changed_parameters if 'EC_MAX' in x[1]]
    t0 = min(pt) if pt else 0
    w = t > t0 - 1
    k = np.argmax(w & (tilt > 60)) if (w & (tilt > 60)).any() else -1
    print(f"fault_t {t0:.2f} end_t {t[-1]:.2f} max_tilt_after_fault {tilt[t > t0].max():.1f} at {t[t > t0][tilt[t > t0].argmax()]:.2f}; first>60 {t[k] if k >= 0 else None}")
