# Delay-line hooks A1/A2 implementation (S102)

Spec: `delay_line_hook_s94.md`. Hook B (GNSS) not implemented, no `SIM_GZ_GPS_DLY`. Only `src/modules/simulation/gz_bridge/` changed. Not flown, no tests run.

## Files and functions
- `module.yaml`: `SIM_GZ_DLY_ACT`, `SIM_GZ_DLY_IMU` (int32, ms, 0-10, default 0, reboot_required), before `SIM_GZ_ERPM_LOSS`.
- `GZMixingInterfaceESC.hpp/.cpp`: ctor reads `SIM_GZ_DLY_ACT` into `_act_delay_us`; new `publishDelayed()`; `updateOutputs()` calls it
  only if `_act_delay_us != 0`, else the original `Publish` line (default path unchanged); init log line.
- `GZBridge.hpp/.cpp`: `SIM_GZ_DLY_IMU` as `ParamInt`, latched to `_imu_delay_us` in `init()`; `imuCallback()` tail: `if (_imu_delay_us == 0)`
  original two `update(timestamp, ...)` calls and return, else ring path. `print_status()` prints delays and overflow/drop counters.

## Rates and ring sizes
- Physics step 1.25 ms, IMU 800 Hz: from `sim_step_impl_s16.md` (D-SIM-STEP; world `max_step_size` 0.00125, model IMU `update_rate` 800).
  I did NOT re-read the flown world/model files myself: UNVERIFIED by me.
- Mixer/`updateOutputs` rate: `MixingOutput` with `SchedulingPolicy::Auto` (`GZMixingInterfaceESC.hpp` `_mixing_output`), so it runs on each
  `actuator_motors` update, i.e. the control_allocator rate, which follows the rate loop (<= IMU 800 Hz, 400/267 Hz variants in s16). Not measured.
- Rings: `ACT_DELAY_LEN = 32` (16 doubles each), `IMU_DELAY_LEN = 32` per instance. 10 ms needs 8 entries at 800 Hz, 10 at 1 kHz; 32 covers
  10 ms up to 3.2 kHz (4x margin over 800 Hz). Static, no runtime allocation.

## Applied delay (quantised up to the next call/sample)
applied = ceil(d / T) * T. At T = 1.25 ms (800 Hz), both paths: 0:0 (bypass), 1:1.25, 2:2.5, 3:3.75, 4:5.0, 5:5.0, 6:6.25, 7:7.5, 8:8.75, 9:10.0, 10:10.0 ms.
At 400 Hz (2.5 ms): 1:2.5, 2:2.5, 3:5, 4:5, 5:5, 6:7.5, 7:7.5, 8:10, 9:10, 10:10. Whole-microsecond stamps, release test `now >= t + delay`;
if `hrt_absolute_time()` lags the gz stamp by a tick, a release can slip one period (the existing code already notes this clock skew). Exact
values are logged at the first release: `PX4_INFO ... applied X us for requested Y us`; init line logs the requested value.

## Semantics
- A1: entry keyed on `hrt_absolute_time()` at `updateOutputs`. Released only from `updateOutputs` (the mixer quantisation, nothing added).
  Newest due entry published, older due entries dropped and counted (`_act_dropped`, one INFO at first drop). Nothing due returns true.
  Ring full: oldest dropped, `_act_overflow`, one PX4_WARN. Note: `_esc_status`/`motorSpeedCallback` echo (SIM_GZ_ESC_FB 0) shows the
  delayed command since it is fed from the gz topic.
- A2: ring entry = `timestamp` exactly as today's code computes it (`min(header stamp, hrt)`), accel+gyro together, after noise/vibration.
  Released in `imuCallback` of the same instance; every due sample is released in order (none dropped, the vehicle_imu integrator needs all);
  `update(original_sample_time, ...)`, sample time never shifted. Groundtruth callbacks untouched. Ring full: oldest released early, counted,
  one PX4_WARN.

## Threads and locks
- A1: `updateOutputs` runs inside `Run()` under `_node_mutex` (non-recursive); the ring is touched only there, so no extra lock, and none taken.
- A2: `std::mutex _imu_delay_mutex` held through ring access and publication (keeps order). Taken after `addRotorVibration` released
  `_node_mutex`, never nested with it. Per-instance rings, one shared mutex. gz transport thread model UNVERIFIED (assumed concurrent).

## Build
PASS. `indi_project/docker/run.sh -n build -t 3600 'make px4_sitl_default'`: last lines `[709/710] Linking CXX static library ...libmodules__simulation__gz_bridge.a`,
`[710/710] Linking CXX executable bin/px4`; 0 warnings in the log. `make format` in the container: "Format checks passed" (the build ran before
the format step; format reported no change failure, but I did not rebuild after it). `git diff --stat`: only the 5 gz_bridge files.

## UNVERIFIED
- Actual mixer call rate and gz IMU callback rate in the flown run (no measurement; see print of first-release ages for a proxy).
- First-release log shows applied delay of the first sample only; jitter across the run is not measured.
- `vehicle_imu` / EKF / preflight behaviour with a 10 ms delay (stale-sensor checks at start: the first `delay` interval publishes nothing).
- Bit-identical default behaviour is by construction (bypass branches), not tested.
- Thread model of gz callbacks; behaviour of `updateOutputs` returning true when nothing was published.

## Suggested section-6 tests at 800 Hz
1. Default identity: all params 0, baseline scenario, compare `sensor_gyro`, `actuator_motors` with a pre-change ulog (same seed).
2. A2 lag: `timestamp - timestamp_sample` of `sensor_gyro` equals the table above (+- one 1.25 ms period) for d = 1, 4, 10; cross-correlate
   against `vehicle_angular_velocity_groundtruth`. Negative: d = 0 must give age ~0 and fail the assertion.
3. A1 lag: step the motor command, compare `actuator_motors` against the gz echo (`esc_status` with ESC_FB 0) on a 1.25 ms grid; lag = table. Negative: d = 0.
4. Overflow: temporarily set ring length 2 (build-time) and expect the WARN and a nonzero count in `gz_bridge status`.
5. Scheduling: d = 10 ms hover 60 s, check no `sensor_gyro` gaps beyond 10 ms + 1 period and no preflight stale-sensor failure.
