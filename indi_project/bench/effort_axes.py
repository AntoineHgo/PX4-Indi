#!/usr/bin/env python3
"""Per-axis torque-setpoint activity and motor-rate effort in a hover ULog.

Prints, over t0+15 s .. t0+45 s, the std and per-sample-change RMS of each
normalised vehicle_torque_setpoint axis, the mean motor-rate RMS (1/s) and
the angular-rate std per axis.

Usage: effort_axes.py LOG.ulg [LOG.ulg ...]
"""
import sys, numpy as np
from pyulog import ULog
for p in sys.argv[1:]:
    u = ULog(p, ["vehicle_torque_setpoint", "actuator_motors", "vehicle_angular_velocity"])
    out = []
    ts = u.get_dataset("vehicle_torque_setpoint").data
    t = ts["timestamp"]*1e-6; m = (t > t[0]+15) & (t < t[0]+45)
    for i in range(3):
        x = ts[f"xyz[{i}]"][m]; out.append(f"tq{i} std {x.std():.4f} drms {np.sqrt(np.mean(np.diff(x)**2)):.4f}")
    am = u.get_dataset("actuator_motors").data
    t = am["timestamp"]*1e-6; m = (t > t[0]+15) & (t < t[0]+45)
    dm = np.mean([np.sqrt(np.mean((np.diff(am[f"control[{i}]"][m])/np.diff(t[m]))**2)) for i in range(4)])
    av = u.get_dataset("vehicle_angular_velocity").data
    t = av["timestamp"]*1e-6; m = (t > t[0]+15) & (t < t[0]+45)
    w = " ".join(f"w{i} {av[f'xyz[{i}]'][m].std():.4f}" for i in range(3))
    print(p.split('results/')[1], "\n  ", "\n   ".join(out), f"\n   motor_rate_rms {dm:.3f}  {w}")
