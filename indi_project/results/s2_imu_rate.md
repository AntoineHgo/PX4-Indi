# Stage-2 sim: IMU / physics rate option, lockstep cost (session 27, 2026-11-14)

`run_scenario.py --imu-rate N` sets the x500_base imu_sensor update_rate and writes a world copy with
max_step_size 1/N (and points PX4_GZ_WORLDS at it, because px4-rc.gzsim re-applies the world's max_step_size).
Flights: step_roll, PID defaults, seed 1, speed 1, `--sim v2 --erpm-drop 0.01`.

| imu rate | physics step | wall time | gyro raw rate in PX4 | exit |
|---|---|---|---|---|
| 250 | 0.004 s | 69 s | 250 Hz | ok |
| 1000 | 0.001 s | 69 s | 1000 Hz | ok |

- At speed 1 the 1000 Hz configuration still runs in real time (single run, 3 runs in parallel on the host).
  Cost at speed > 1 and in large parallel batches is NOT measured yet.
- Open: `esc_status` (and `vehicle_angular_velocity`) are logged at 250 Hz in the 1000 Hz run. Find whether this is the
  logger interval or the control/output loop rate (IMU_GYRO_RATEMAX 800, IMU_INTEG_RATE 250) before using 1000 Hz.
- The first 500 and 1000 Hz runs of this session were invalid (physics step reset to 0.004 s by px4-rc.gzsim, gyro at
  250 Hz); the 1000 Hz run was re-flown after the fix, the 500 Hz run was not and is discarded.
