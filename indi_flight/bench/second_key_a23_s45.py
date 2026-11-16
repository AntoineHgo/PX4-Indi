#!/usr/bin/env python3
"""Second-key check for the S45 A-23 yaw flight: rate RMS, motor floor, torque achieved.

Usage: second_key_a23_s45.py LOG OUT_MD
"""
import sys

import numpy as np
from pyulog import ULog

T0, T1 = 52.0, 82.0
MOTOR_FLOOR = 0.005


def rms_demeaned(x):
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean((x - np.mean(x)) ** 2)))


def selftest():
    n = 200001
    t = np.linspace(0.0, 100 * 2 * np.pi, n)
    val = rms_demeaned(np.sin(t))
    assert abs(val - 0.7071) < 1e-3, val
    print(f"self-test: RMS of unit sine = {val:.6f} (expected 0.707107, tol 1e-3) PASS")
    return val


def get_topic(ulog, name):
    matches = [d for d in ulog.data_list if d.name == name]
    if not matches:
        raise SystemExit(f"topic {name} not found in log")
    if len(matches) > 1:
        print(f"note: {name} has {len(matches)} instances, using multi_id 0")
    return next((d for d in matches if d.multi_id == 0), matches[0])


def window_mask(t):
    return (t >= T0) & (t <= T1)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: second_key_a23_s45.py LOG OUT_MD")
    log_path, out_md = sys.argv[1], sys.argv[2]

    selftest_val = selftest()
    ulog = ULog(log_path)
    lines = []
    lines.append("# Second-key check: S45 A-23 yaw flight (indi_g1y)")
    lines.append("")
    lines.append(f"Log: `{log_path}`")
    lines.append(f"Window: {T0:.1f} s to {T1:.1f} s since boot (topic timestamp / 1e6)")
    lines.append("")
    lines.append(f"Self-test: RMS of unit sine = {selftest_val:.6f} (PASS, tol 1e-3)")
    lines.append("")

    # 1. Angular velocity RMS
    av = get_topic(ulog, "vehicle_angular_velocity")
    t_av = av.data["timestamp"].astype(float) / 1e6
    m = window_mask(t_av)
    t_w = t_av[m]
    dt = np.diff(t_w)
    med_dt = float(np.median(dt)) if dt.size else float("nan")
    rms = {}
    for i, axis in enumerate(["x", "y", "z"]):
        rms[axis] = rms_demeaned(av.data[f"xyz[{i}]"][m])
    pitch_ok = rms["y"] < 0.02
    lines.append("## 1. vehicle_angular_velocity.xyz (demeaned RMS, rad/s)")
    lines.append("")
    lines.append(f"- samples in window: {t_w.size}")
    lines.append(f"- median sample interval: {med_dt * 1e3:.3f} ms ({1.0 / med_dt:.1f} Hz)")
    lines.append(f"- RMS roll  xyz[0]: {rms['x']:.6f} rad/s")
    lines.append(f"- RMS pitch xyz[1]: {rms['y']:.6f} rad/s")
    lines.append(f"- RMS yaw   xyz[2]: {rms['z']:.6f} rad/s")
    lines.append(f"- pass criterion pitch RMS < 0.02 rad/s: {'PASS' if pitch_ok else 'FAIL'}")
    lines.append("")
    print(f"angvel samples={t_w.size} median_dt={med_dt*1e3:.3f} ms "
          f"RMS x={rms['x']:.6f} y={rms['y']:.6f} z={rms['z']:.6f} "
          f"pitch<0.02 {'PASS' if pitch_ok else 'FAIL'}")

    # 2. Motor floor
    am = get_topic(ulog, "actuator_motors")
    t_am = am.data["timestamp"].astype(float) / 1e6
    mm = window_mask(t_am)
    lines.append("## 2. actuator_motors.control[0..3]")
    lines.append("")
    lines.append(f"- samples in window: {int(mm.sum())}")
    lines.append("")
    lines.append("| motor | frac < 0.005 | mean | std | pass (<1%) |")
    lines.append("|---|---|---|---|---|")
    motor_pass_all = True
    for i in range(4):
        c = am.data[f"control[{i}]"][mm].astype(float)
        frac = float(np.mean(c < MOTOR_FLOOR)) if c.size else float("nan")
        ok = frac < 0.01
        motor_pass_all &= ok
        lines.append(f"| {i} | {frac:.4%} | {np.mean(c):.4f} | {np.std(c):.4f} | "
                     f"{'PASS' if ok else 'FAIL'} |")
        print(f"motor{i} frac<0.005={frac:.4%} mean={np.mean(c):.4f} std={np.std(c):.4f} "
              f"{'PASS' if ok else 'FAIL'}")
    lines.append("")
    lines.append(f"- pass criterion every motor < 0.005 on < 1% of samples: "
                 f"{'PASS' if motor_pass_all else 'FAIL'}")
    lines.append("")

    # 3. Torque setpoint achieved
    ca = get_topic(ulog, "control_allocator_status")
    t_ca = ca.data["timestamp"].astype(float) / 1e6
    mc = window_mask(t_ca)
    tsa = ca.data["torque_setpoint_achieved"][mc].astype(bool)
    frac_true = float(np.mean(tsa)) if tsa.size else float("nan")
    lines.append("## 3. control_allocator_status.torque_setpoint_achieved")
    lines.append("")
    lines.append(f"- samples in window: {tsa.size}")
    lines.append(f"- fraction true: {frac_true:.4%}")
    lines.append("")
    print(f"torque_setpoint_achieved samples={tsa.size} frac_true={frac_true:.4%}")

    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
