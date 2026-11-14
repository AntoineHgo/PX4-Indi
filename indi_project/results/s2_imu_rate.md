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
- Logged rates (session 28): the logger polls every 3500 us (`src/modules/logger/logger.cpp:265`), so topics without
  an interval are logged at <= 285.7 Hz, and `esc_status` has a 5 ms interval in the high-rate profile (SDLOG_PROFILE 17).
  The loop itself runs at 1 kHz: VehicleAngularVelocity publishes every round(1250 us / 1000 us) = 1 gyro sample
  (IMU_GYRO_RATEMAX 800), and the logged sample spacing is 3/4 ms (odd multiples of 1 ms occur, impossible at 500 Hz).
  At 250 Hz the logged spacing is 4 ms. Consequence: logged INDI signals at 1000 Hz are a 3.5 ms subsample.

## Lockstep cost and speed invariance at 1000 Hz (session 28, `s2_imu_cost/`)

step_roll, PID defaults, `--sim v2 --erpm-drop 0.01 --imu-rate 1000`. Wall time includes ~20 s of startup.

| run | wall | roll rate rms | roll att rms [deg] | rise 10-90 [s] | overshoot [%] | settle 5 % [s] |
|---|---|---|---|---|---|---|
| speed 1, seeds 1-6, 6 in parallel | 71 s (whole batch) | 0.0790-0.0825 | 3.20-3.40 | 0.419-0.420 | 0.116-0.139 | 0.659-0.676 |
| speed 2, seed 1 | 43 s | 0.0810 | 3.23 | 0.420 | 0.115 | 0.662 |
| speed 4, seed 1 | 31 s | 0.0791 | 3.32 | 0.420 | 0.131 | 0.671 |

- Six parallel 1000 Hz runs at speed 1 take the same wall time as one: the host keeps up.
- Speed 2 and 4 stay inside the 6-seed spread of speed 1 on every step metric (attitude/rate scenarios only; position
  scenarios keep the D-speed rule of speed 1).
- The first 500 and 1000 Hz runs of this session were invalid (physics step reset to 0.004 s by px4-rc.gzsim, gyro at
  250 Hz); the 1000 Hz run was re-flown after the fix, the 500 Hz run was not and is discarded.
