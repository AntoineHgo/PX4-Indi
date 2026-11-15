# IMU rate plan for G2 (session 15)

Goal: controller rates 250/400/800 Hz selectable, IMU at 1 kHz, physics step independent of the IMU rate.
Read-only investigation; nothing built or run. "UNVERIFIED" marks what only a run can confirm.

## 1. Physics step
- Runner world: `indi_flight/bench/run_scenario.py:183` uses `$PX4_GZ_WORLDS/default.sdf` = `Tools/simulation/gz/worlds/default.sdf:5-7`:
  `max_step_size` 0.004 s, `real_time_update_rate` 250. The step is 4 ms: a 1 kHz IMU is impossible with it (a gz sensor
  updates at most once per physics step).
- `px4-rc.gzsim:161-188` re-applies `real_time_factor=PX4_SIM_SPEED_FACTOR` and the world file's `max_step_size` at start.
- TRAP: `run_scenario.py:182-186` + `model_variant.py:103-112` (`build_world`) set the physics step to 1/imu_rate whenever
  `--imu-rate != 250`. This violates the mission rule (step must not follow the IMU rate). Remove that coupling; use one
  fixed world for all runs (new world under indi_flight/sim/worlds/, selected via PX4_GZ_WORLDS).
- `model_variant.py:64-70` edits `imu_sensor` `<update_rate>` of the model copy (x500_base only; quad5in variants raise
  SystemExit at `run_scenario.py:154-155`).

## 2. gz_bridge
- `GZBridge.cpp:632-666` `imuCallback`: one gz message -> one `_px4_accel/_px4_gyro.update()` (PX4Gyroscope::update publishes
  one sensor_gyro per call, non-FIFO path). Sample time = gz header stamp (sim time, :641), clamped to <= hrt_absolute_time (:644).
  So sensor_gyro rate == gz IMU rate (if the world step allows it).
- Tied to the IMU callback: only `addRotorVibration` (:602-629, called :660, instance 0): phase advance uses dt between
  stamps (clamped 20 ms), so it is rate-correct at 1 kHz. Rotor rpm is read from `GZMixingInterfaceESC` under a mutex.
- eRPM telemetry (`GZMixingInterfaceESC.cpp:128-183`) runs in `motorSpeedCallback` (gz motor-speed topic), latency counted in
  those callbacks (`_erpm_latency`, :163): tied to the physics/actuator publish rate, NOT the IMU. If the physics step
  changes from 4 ms, the ERPM latency in seconds changes: re-check SIM_GZ ERPM latency params (UNVERIFIED which unit).

## 3. Controller rate parameters
- 4040_gz_quad5in (ROMFS/px4fmu_common/init.d-posix/airframes) sets none of IMU_GYRO_RATEMAX, IMU_INTEG_RATE, IMU_GYRO_CUTOFF,
  IMU_DGYRO_CUTOFF (grep empty); rc.mc_defaults not checked. Defaults (imu_gyro_parameters.yaml): IMU_GYRO_RATEMAX 400
  (100..2000), IMU_GYRO_CUTOFF 40 Hz, IMU_DGYRO_CUTOFF 20 Hz. IMU_INTEG_RATE (VehicleIMU.cpp:150) clamped 50..1000, default
  200 per IntegratorConingTest comment; it feeds vehicle_imu/EKF only, not the rate loop.
- `VehicleAngularVelocity.cpp:134-149`: publishes every N = round((1e6/RATEMAX)/(1e6/sensor_rate)) gyro samples, N in 1..8
  (queue length). With a 1 kHz IMU: RATEMAX 250 -> N=4 exact; 400 -> N=round(2.5)=3 = 333 Hz (NOT 400); 800 -> N=1 = 1000 Hz
  (NOT 800); 500 -> 500. Exact 400/800 need the sensor rate to be a multiple of them (IMU 800 Hz: 800 N=1, 400 N=2;
  1.25 ms is not a multiple of a 1 ms step so it jitters; 4 kHz physics 0.25 ms would make 250/400/800/1000 all exact).
- Gyro LP/D filters use the measured sample rate (`:120-131`, `:172`) so cutoffs stay in Hz: keep IMU_GYRO_CUTOFF/DGYRO fixed
  across rates, or the comparison confounds rate and filtering.
- `McIndiRateControl.cpp:69` registers a callback on vehicle_angular_velocity: runs once per published sample; dt from
  `timestamp_sample` deltas (:238-239, clamped 0.125 ms..20 ms: 1 kHz and 800 Hz are within limits).
- Cycle-count params depend on rate: MC_INDI_DELAY (default 0) and MC_INDI_ERPM_DLY (default 1) are in controller cycles
  (mc_indi_rate_control_params.yaml); scale them with the rate (1 cycle = 4 ms at 250 Hz, 1.25 ms at 800 Hz) or the
  delay in seconds changes. MC_INDI_DT_MAX is per cycle, also rate dependent.

## 4. Minimal change list
1. New fixed world: `max_step_size` 0.001 (and `real_time_update_rate` 1000), used by ALL runs including 250 Hz; remove the
   `build_world(imu_rate)` coupling in run_scenario.py:184-186 (keep `--imu-rate` for the sensor only).
2. quad5in_base/model.sdf:174 `<update_rate>` 250 -> 1000 (or a per-run model copy, since variants cannot be applied to quad5in
   yet, run_scenario.py:154).
3. Params per controller rate (IMU 1 kHz, step 1 ms): 250: IMU_GYRO_RATEMAX=250; 400: 400 (=> measured 333 Hz) or move to the
   0.25 ms/800 Hz-sensor option; 800: 800 (=> measured 1000 Hz, N=1) - an exact 800 needs the sensor at 800 Hz.
   Fix IMU_GYRO_CUTOFF/IMU_DGYRO_CUTOFF; scale MC_INDI_DELAY/ERPM_DLY.
4. Add `vehicle_imu_status` (gyro_raw_rate_hz, gyro_rate_hz) to LOG_TOPICS (run_scenario.py:53-59): low-rate evidence of the rate.
Pre-test checks: (a) physics step in px4/gz log == 1 ms for the 250, 400, 800 runs; (b) sensor_gyro rate (or vehicle_imu_status
gyro_raw_rate_hz) ~1000 Hz in sim time; (c) vehicle_angular_velocity rate in the ULog == the intended rate within 1 %, jitter
of timestamp_sample; (d) PID hover/step_roll still flies with the 1 ms world (plant discretisation and ERPM latency change: re-run the
PID baseline at 1 ms, the 4 ms results are not comparable); (e) wall/sim ratio at --speed 4.
Risks: CPU at speed 4 (4x more physics steps and 4x rate-loop callbacks; real-time at 1 ms step UNVERIFIED, 16 cores
available); logger: topics logged at full rate are vehicle_angular_velocity, actuator_motors, esc_status,
vehicle_torque_setpoint, vehicle_thrust_setpoint, control_allocator_status (all per rate-loop cycle, up to 1 kHz) so
expect ~4x log volume vs 250 Hz and possible logger drops (check `logger` buffer messages, UNVERIFIED);
sensor_gyro itself is not in LOG_TOPICS.
