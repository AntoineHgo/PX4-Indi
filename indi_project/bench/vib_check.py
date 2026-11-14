#!/usr/bin/env python3
"""IMU vibration check: PX4 vibration metrics, gyro/accel spread and spectrum peaks, rotor speed and motor effort
over the metric window of each run. Usage: vib_check.py <run_dir> [<run_dir> ...]"""
import json
import sys

import numpy as np
from pyulog import ULog


def window(u, run_dir, name, field, multi=0):
    w = json.load(open(f"{run_dir}/metrics.json"))["window"]
    d = u.get_dataset(name, multi)
    t = (d.data["timestamp"] - u.start_timestamp) * 1e-6
    sel = (t >= w["start_s"]) & (t <= w["end_s"])
    return t[sel], d.data[field][sel]


def peak_hz(t, x):
    x = x - x.mean()
    dt = np.median(np.diff(t))
    f = np.fft.rfftfreq(len(x), dt)
    a = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    a[f < 5] = 0
    return f[np.argmax(a)], 0.5 / dt


for run_dir in sys.argv[1:]:
    u = ULog(f"{run_dir}/flight.ulg")
    out = {"run": run_dir.rstrip("/").split("results/")[-1]}
    for f in ("accel_vibration_metric", "gyro_vibration_metric"):
        out[f] = float(np.mean(window(u, run_dir, "vehicle_imu_status", f)[1]))
    for i, ax in enumerate("xyz"):
        t, g = window(u, run_dir, "sensor_combined", f"gyro_rad[{i}]")
        out[f"gyro_{ax}_std"] = float(np.std(g))
        t, a = window(u, run_dir, "sensor_combined", f"accelerometer_m_s2[{i}]")
        out[f"acc_{ax}_p2p"] = float(np.percentile(a, 99) - np.percentile(a, 1))
    out["gyro_x_peak_hz"], out["sensor_combined_nyquist_hz"] = peak_hz(*window(u, run_dir, "sensor_combined", "gyro_rad[0]"))
    out["rotor_rpm_mean"] = float(np.mean([window(u, run_dir, "esc_status", f"esc[{i}].esc_rpm")[1].mean() for i in range(4)]))
    out["motor_cmd_std"] = float(np.mean([np.std(window(u, run_dir, "actuator_motors", f"control[{i}]")[1]) for i in range(4)]))
    m = json.load(open(f"{run_dir}/metrics.json"))
    out["pos_rms_3d_m"] = m["position"]["rms_3d_m"]
    out["att_rms_deg"] = m["attitude_tracking"]["rotation_angle_rms_deg"]
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}))
