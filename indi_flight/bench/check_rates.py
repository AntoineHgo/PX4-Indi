#!/usr/bin/env python3
"""Logged-rate check of a run (D-SIM-STEP pre-test, G1.1): rate params, per-topic logged rate from timestamp_sample
(sim time), PX4's own gyro rate (vehicle_imu_status) and logger dropouts. Usage: check_rates.py <run_dir> [...]"""
import json
import os
import sys

import numpy as np
from pyulog import ULog

TOPICS = ["sensor_gyro", "vehicle_angular_velocity", "actuator_motors", "esc_status", "vehicle_torque_setpoint"]

for run in sys.argv[1:]:
    meta = json.load(open(os.path.join(run, "run.json")))
    u = ULog(os.path.join(run, "flight.ulg"))
    print(f"== {run}: exit={meta.get('exit_status')} step={meta.get('physics_step_s')} rate_hz={meta.get('rate_hz')}")
    print("  params", {k: u.initial_parameters.get(k) for k in ("IMU_GYRO_RATEMAX", "IMU_GYRO_CUTOFF", "IMU_DGYRO_CUTOFF")})
    for t in TOPICS:
        ds = [d for d in u.data_list if d.name == t and d.multi_id == 0]
        if not ds:
            print(f"  {t}: MISSING")
            continue
        d = ds[0].data
        ts = d.get("timestamp_sample", d["timestamp"]) * 1e-6
        dt = np.diff(ts)
        print(f"  {t}: n={len(ts)} median={1 / np.median(dt):.1f} Hz mean={len(ts) / (ts[-1] - ts[0]):.1f} Hz "
              f"dt p1/p99={np.percentile(dt, 1) * 1e3:.3f}/{np.percentile(dt, 99) * 1e3:.3f} ms")
    st = [d for d in u.data_list if d.name == "vehicle_imu_status" and d.multi_id == 0]
    if st:
        print(f"  vehicle_imu_status gyro_rate_hz={np.median(st[0].data['gyro_rate_hz']):.1f} "
              f"raw={np.median(st[0].data['gyro_raw_rate_hz']):.1f}")
    print(f"  logger dropouts: {len(u.dropouts)}, {sum(x.duration for x in u.dropouts)} ms")
