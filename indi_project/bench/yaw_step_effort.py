#!/usr/bin/env python3
"""Break down control activity around each yaw setpoint step of a step_yaw ULog (PID or INDI).

For every yaw attitude-setpoint jump (> 0.1 rad) it takes the window [t_step - 0.2 s, t_step + 2 s] and prints:
motor-rate RMS (as metrics.py, all motors) and the part of it along the yaw allocation direction (motor signs from
CA_ROTORi_KM), peak |yaw rate setpoint|, peak |yaw torque setpoint|, and for INDI the peaks of nu_z/G1_Y, of the
setpoint part K_Y*r_sp/G1_Y and of the torque increment. A 2 s hold window before the first step is the reference.

Usage: yaw_step_effort.py LOG.ulg [LOG.ulg ...]
"""
import sys
import numpy as np
from pyulog import ULog

TOPICS = ["vehicle_attitude_setpoint", "vehicle_rates_setpoint", "vehicle_torque_setpoint", "actuator_motors",
          "indi_rate_status"]


def get(u, name):
    try:
        d = u.get_dataset(name).data
    except (KeyError, IndexError, ValueError):
        return None
    return d


def yaw_of(d):
    w, x, y, z = (d[f"q_d[{i}]"] for i in range(4))
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def motor_rates(am, n, km):
    t = am["timestamp"] * 1e-6
    u = np.column_stack([am[f"control[{i}]"] for i in range(n)])
    dt = np.diff(t)
    ok = dt > 0
    du = np.diff(u, axis=0)[ok] / dt[ok, None]
    yaw_dir = np.sign(km) / np.sqrt(n)
    return t[1:][ok], du, du @ yaw_dir


def peak(t, x, a, b):
    m = (t >= a) & (t <= b)
    return float(np.max(np.abs(x[m]))) if m.any() else float("nan")


def rms_in(t, x, a, b):
    m = (t >= a) & (t <= b)
    return float(np.sqrt(np.mean(x[m] ** 2))) if m.any() else float("nan")


def main():
    for p in sys.argv[1:]:
        u = ULog(p, TOPICS)
        prm = u.initial_parameters
        n = 4
        km = np.array([prm.get(f"CA_ROTOR{i}_KM", 0.0) for i in range(n)])
        asp = get(u, "vehicle_attitude_setpoint")
        ta = asp["timestamp"] * 1e-6
        ysp = np.unwrap(yaw_of(asp))
        jumps = ta[1:][np.abs(np.diff(ysp)) > 0.1]
        steps = [s for i, s in enumerate(jumps) if i == 0 or s - jumps[i - 1] > 1.0]
        rsp, tq, am, ind = (get(u, k) for k in TOPICS[1:])
        tm, du, du_y = motor_rates(am, n, km)
        ctl = f"INDI K_Y {prm.get('MC_INDI_K_Y'):.3g} G1_Y {prm.get('MC_INDI_G1_Y'):.3g}" if ind is not None \
            else f"PID YAWRATE_P {prm.get('MC_YAWRATE_P'):.3g} TQ_CUT {prm.get('MC_YAW_TQ_CUTOFF'):.3g}"
        print(f"{p.split('results/')[-1]}  [{ctl}, YAW_P {prm.get('MC_YAW_P'):.3g}]  steps at "
              + ", ".join(f"{s - ta[0]:.1f}" for s in steps))
        wins = [("hold", steps[0] - 2.2, steps[0] - 0.2)] + [(f"step{i}", s - 0.2, s + 2.0) for i, s in enumerate(steps)]
        for name, a, b in wins:
            line = (f"  {name:6s} mrate_rms {rms_in(tm, du, a, b):.3f} (yaw dir {rms_in(tm, du_y, a, b):.3f})"
                    f"  |r_sp| {peak(rsp['timestamp'] * 1e-6, rsp['yaw'], a, b):.2f}"
                    f"  |tq_z| {peak(tq['timestamp'] * 1e-6, tq['xyz[2]'], a, b):.3f}")
            if ind is not None:
                ti = ind["timestamp"] * 1e-6
                g1 = prm["MC_INDI_G1_Y"]
                r_sp = np.interp(ti, rsp["timestamp"] * 1e-6, rsp["yaw"])
                line += (f"  |nu/G1| {peak(ti, ind['nu[2]'] / g1, a, b):.3f}"
                         f"  |K_Y r_sp/G1| {peak(ti, prm['MC_INDI_K_Y'] * r_sp / g1, a, b):.3f}"
                         f"  |inc| {peak(ti, ind['torque_increment[2]'], a, b):.3f}"
                         f"  inc_rms {rms_in(ti, ind['torque_increment[2]'], a, b):.4f}")
            print(line)


if __name__ == "__main__":
    main()
