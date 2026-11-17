#!/usr/bin/env python3
"""Fit a first-order-plus-delay model of the closed rate loop (rate setpoint -> body rate) on one axis.

  python3 rate_fit.py LOG.ulg AXIS(0|1|2) T0 T1   -> prints tau [ms], delay [ms], fit RMS, and the
  attitude-loop damping implied by MC_*_P (read from the log) for an inner loop 1/(tau s + 1) e^{-ds}.
Model: y' = (r(t-d) - y)/tau, Euler on the setpoint time base; grid search tau 5-200 ms, d 0-40 ms.
"""
import sys
import numpy as np
from pyulog import ULog
from scipy.signal import lfilter

f, ax, t0, t1 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
u = ULog(f, ["vehicle_rates_setpoint", "vehicle_angular_velocity"])
d = {x.name: x.data for x in u.data_list}
key = ["roll", "pitch", "yaw"][ax]
rs = d["vehicle_rates_setpoint"]; av = d["vehicle_angular_velocity"]
ts = rs["timestamp"] * 1e-6; r = rs[key]
ta = av["timestamp"] * 1e-6; y = av[f"xyz[{ax}]"]
T0 = 0.0
t = np.arange(t0, t1, 1 / 800.0) + T0
R = np.interp(t, ts, r); Y = np.interp(t, ta, y)
best = None
for d_ms in range(0, 41, 1):
    Rd = np.interp(t - d_ms * 1e-3, ts, r)
    for tau_ms in range(5, 201, 1):
        a = (1 / 800.0) / (tau_ms * 1e-3)
        m, _ = lfilter([0, a], [1, -(1 - a)], Rd, zi=[(1 - a) * Y[0]])
        e = np.sqrt(np.mean((m - Y) ** 2))
        if best is None or e < best[0]:
            best = (e, tau_ms, d_ms)
P = {p.key if hasattr(p, 'key') else p: v for p, v in u.initial_parameters.items()}
Pa = P.get(["MC_ROLL_P", "MC_PITCH_P", "MC_YAW_P"][ax], float('nan'))
e, tau, dl = best
# attitude loop P/s * 1/(tau s+1): s^2 tau + s + P = 0 -> zeta = 1/(2 sqrt(P tau))
print(f"axis {key}: tau {tau} ms, delay {dl} ms, fit RMS {e:.4f} rad/s (|y| rms {np.sqrt(np.mean(Y**2)):.3f}), "
      f"att P {Pa}, zeta(no delay) {1/(2*np.sqrt(Pa*tau*1e-3)):.2f}")
