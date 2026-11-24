"""post_fault_err.py ULG...: params, fault time, 1 s post-fault mean rate error (roll,pitch) and torque_sp - torque_filtered, measured-torque-in-use fraction."""
import sys, numpy as np
from pyulog import ULog
for f in sys.argv[1:]:
    u = ULog(f); g = lambda n: u.get_dataset(n).data
    t0 = min(x[0] for x in u.changed_parameters if 'EC_MAX' in x[1]) * 1e-6
    p = u.initial_parameters
    print(f, 'ACT_BLD', p.get('MC_INDI_ACT_BLD'), 'W_MAX', p.get('MC_INDI_W_MAX'), 'ACT_TC', p.get('MC_INDI_ACT_TC'), 'fault_t %.2f' % t0)
    I, R, S = g('indi_rate_status'), g('vehicle_angular_velocity'), g('vehicle_rates_setpoint')
    ti = I['timestamp'] * 1e-6; m = (ti > t0) & (ti < t0 + 1)
    tr = R['timestamp'] * 1e-6
    for k, ax in ((0, 'roll'), (1, 'pitch')):
        sp = np.interp(ti[m], S['timestamp'] * 1e-6, S[ax]); w = np.interp(ti[m], tr, R[f'xyz[{k}]'])
        e = sp - w; te = I[f'torque_sp[{k}]'][m] - I[f'torque_filtered[{k}]'][m]
        print(f'  {ax}: rate_err mean {e.mean():+.4f} mean|.| {np.abs(e).mean():.4f} rad/s; (torque_sp - torque_filtered) mean {te.mean():+.4f} mean|.| {np.abs(te).mean():.4f}')
    print('  measured_torque_in_use fraction %.2f' % I['measured_torque_in_use'][m].mean())
