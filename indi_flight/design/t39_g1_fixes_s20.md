# T39 G1 fixes (S20)

Run: `results/a12_fix_s18/pretest_truth_topics/hover` (PID hover, quad5in, 1.25 ms world, rate_hz 800).

## Task 1 g1_checks.py rows (edited)

- Added `vehicle_attitude_groundtruth` and `vehicle_angular_velocity_groundtruth`; all three truth topics are now `"controller"` (= run.json `rate_hz`, same convention as the gyro rows) instead of fixed 50 Hz.
- Why controller rate: truth is published every physics step (800 Hz) and used to score rate/attitude tracking at controller rate; for 400 / 267 Hz runs the 800 Hz truth still passes (`med >= declared`). Comment added in the file.
- `selftest` passes ("g1_checks selftest ok").
- NEW finding, not changed: the three truth rows now FAIL on the gap rule (see Task 4), not on rate. Max gap 3.75 ms = exactly the limit 3/800 (strict `<`), same pattern as esc_status. Gap histogram (timestamp_sample): truth topics have 6 gaps of 3 steps (3.75 ms) and ~7.7k of 2 steps (2.5 ms) in ~52k samples; esc_status 123 gaps of 3.75 ms. The rate itself (800.0 Hz median) is met. Whether a 3-step truth gap matters: metrics interpolate/score truth, so 6 isolated 3.75 ms gaps are probably harmless, but loosening the truth gap rule is a decision for the owner, I left the rule unchanged.

## Task 2 check_truth_s18.py (edited)

Default output is now `truth_check.md` in the directory of the input ULog (`os.path.dirname(abspath(ulg))`); `DEFAULT_OUT` (the committed `second_key.md` path) removed; default input unchanged; docstring updated. Explicit 2nd argument still overrides. Syntax checked only (script not re-run, to avoid touching result files).

## Task 3 vehicle_local_position = 88.9 Hz: cause CONFIRMED (source + log)

Chain, 800 Hz IMU (1.25 ms):
1. `ROMFS/px4fmu_common/init.d-posix/px4-rc.simulator` sets `IMU_INTEG_RATE` default 250 (ULog initial params: IMU_INTEG_RATE 250; EKF2_PREDICT_US 10000). `run_scenario.py` does not override either.
2. `src/modules/sensors/vehicle_imu/VehicleIMU.cpp` ~L688: `gyro_integral_samples = round(_imu_integration_interval_us / gyro_interval_us) = round(4000 / 1250) = round(3.2) = 3` -> vehicle_imu messages integrate 3 samples = 3.75 ms. Log: `vehicle_imu.delta_angle_dt = delta_velocity_dt = 3750 us` (unique), sensor_combined 266.7 Hz.
3. `src/modules/ekf2/EKF/imu_down_sampler/imu_down_sampler.cpp` L61-68: `_required_samples = round(EKF2_PREDICT_US / delta_ang_dt_avg) = round(10000 / 3750) = round(2.667) = 3` -> EKF update every 3 vehicle_imu messages = 11.25 ms = 9 physics steps = 800/9 = 88.9 Hz. EKF2.cpp publishes local position at each EKF update.
4. Log: vehicle_local_position and estimator_status both 88.89 Hz (n = 6641), dt in {10000, 11250, 12500} us, mean 11250 us. Matches.
- Independent of `rate_hz` (IMU_GYRO_RATEMAX): the chain uses the raw 800 Hz sensor interval, not the decimated controller rate. Not verified on a 400 / 267 Hz flight in this task.
- Old config for reference: 250 Hz IMU, 4 ms: round(4000/4000) = 1 sample, EKF round(10000/4000) = round(2.5) = 3 -> 12 ms = 83 Hz, so by the same arithmetic the old config would have given ~83 Hz, not the 125 Hz (8 ms) in the table (derived by calculation only, no old flight checked).
- Edited g1_checks.py: `vehicle_local_position` 125.0 -> 88.0 (floor under 800/9 = 88.889 so a float or jitter on the median cannot fail it; gap limit now 34.1 ms vs observed max 11.3 ms), with a cause comment.
- Do trajectory metrics need more than 88.9 Hz? No evidence of it. `metrics.py` (~L446-456) scores `trajectory.estimate` (vehicle_local_position) and `.truth` (groundtruth) each against the ANALYTIC reference (`hold_pos_ned + traj_pva(traj, t - t0)`) at their own sample times, so no interpolation of one onto the other and the estimate rate only sets the sampling density of the error. Lemniscate time scale is seconds (EKF output is itself delayed/smoothed), so 11.25 ms sampling is far finer than the signal. The estimate error is also dominated by EKF dynamics, not sampling. Caveat: the `truth_minus_estimate_pre_t0` diagnostic and any EKF-vs-truth comparison (check_truth_s18.py) interpolate truth to EKF times, unaffected. Not tested numerically (no re-scoring with decimated data).

## Task 4 g1.1 output

`bash indi_flight/bench/gate_g1.sh g1.1 indi_flight/results/a12_fix_s18/pretest_truth_topics/hover` (exit 1):

| run | topic | declared Hz | median Hz | max gap ms | gap limit ms | verdict |
|---|---|---|---|---|---|---|
| a12_fix_s18/pretest_truth_topics/hover | sensor_gyro | 800 | 800.0 | 2.5 | 3.8 | pass |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_angular_velocity | 800 | 800.0 | 2.5 | 3.8 | pass |
| a12_fix_s18/pretest_truth_topics/hover | actuator_motors | 800 | 800.0 | 2.5 | 3.8 | pass |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_torque_setpoint | 800 | 800.0 | 2.5 | 3.8 | pass |
| a12_fix_s18/pretest_truth_topics/hover | esc_status | 800 | 800.0 | 3.8 | 3.8 | FAIL |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_local_position | 88 | 88.9 | 11.3 | 34.1 | pass |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_local_position_groundtruth | 800 | 800.0 | 3.8 | 3.8 | FAIL |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_attitude_groundtruth | 800 | 800.0 | 3.8 | 3.8 | FAIL |
| a12_fix_s18/pretest_truth_topics/hover | vehicle_angular_velocity_groundtruth | 800 | 800.0 | 3.8 | 3.8 | FAIL |
G1.1 verdict: FAIL

esc_status FAIL is the known A-10, unchanged.
