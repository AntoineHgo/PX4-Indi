# D-SIM-STEP implementation notes (session 16)

Implements `DECISIONS.md` D-SIM-STEP (1.25 ms physics step, IMU 800 Hz, all runs). Nothing built, run or committed.
Line numbers are the files after the edit.

## Changes
1. `indi_flight/sim/worlds/default.sdf` (new): byte copy of `Tools/simulation/gz/worlds/default.sdf` with
   `max_step_size` 0.00125 (:5) and `real_time_update_rate` 800 (:7); diff against the stock file is those two lines.
   How it is picked: `px4-rc.gzsim:164-188` reads `max_step_size` from `${PX4_GZ_WORLDS}/${PX4_GZ_WORLD}.sdf` and re-applies it with
   `set_physics` (plus `real_time_factor = PX4_SIM_SPEED_FACTOR`). PX4_GZ_WORLD is the running world's name ("default").
   The runner starts gz itself with the world path, so both must be the same file.
2. `bench/run_scenario.py:34` `WORLDS_DIR`; `:163` `load_env` sets `PX4_GZ_WORLDS=WORLDS_DIR` for EVERY run (all models, all imu
   rates). The repo is mounted at its own path in the container (`indi_project/docker/run.sh:55`), the same pattern as
   `MODELS_DIR`, so the host path is valid inside.
3. `bench/run_scenario.py` `start_gz` (~:200): the `build_world` coupling (old :182-186) is removed. `build_world` import removed
   (:25). `bench/model_variant.py`: `build_world` deleted (old :103-112, no caller left), docstring :10 updated.
4. `--imu-rate` (:496): sensor only, default None -> the model's own rate (`MODEL_IMU_RATE` :36: quad5in 800, x500 250). A
   differing value goes through the model-variant path (x500 only, as before; quad5in raises SystemExit, `apply_model_variant`).
5. `sim/models/quad5in_base/model.sdf:174` IMU `<update_rate>` 250 -> 800 (the other sensors 50/100/30 are unchanged).
6. `--rate-hz {800,400,267}` (:499), default 800. Sets `PX4_PARAM_IMU_GYRO_RATEMAX` in the px4 env at boot (:568), together with
   `IMU_GYRO_CUTOFF` 40 Hz and `IMU_DGYRO_CUTOFF` 20 Hz (:569-570, constants :39; PX4 defaults, pinned explicitly, fixed for
   all rates). A `--params` file that sets any of these three is rejected (:534-536), so nothing changes them unseen.
   Decimation N = round(800 / RATEMAX) = 1, 2, 3 -> 800, 400, 266.7 Hz.
7. Metadata (`meta`, :522-526, written to run.json): `physics_step_s` (parsed from the world file by `world_step_s` :91, 0.00125),
   `world`, `imu_rate`, `rate_hz`, `imu_filter_hz`. `imu_rate` is now always recorded (it was only when != 250).
8. `LOG_TOPICS` (:67): `vehicle_imu_status`, `sensor_gyro` added (instance 0, interval 0 = every update).

## Item 4: controller rate default and IMU parameters
- Stock default for this airframe is already 800: `ROMFS/px4fmu_common/init.d/rc.mc_defaults:13-15` does
  `if param compare IMU_GYRO_RATEMAX 400 -> param set-default IMU_GYRO_RATEMAX 800` (module default is 400, so every
  multicopter boots at 800). `4040_gz_quad5in` sets no IMU_GYRO_RATEMAX/CUTOFF/DGYRO_CUTOFF (grep: only SIM_GZ_* lines). So
  the runner default is 800 (= stock), NOT 400. 400 and 267 are explicit choices.
- `px4-rc.simulator:7` sets `IMU_INTEG_RATE` 250 (feeds vehicle_imu/EKF only, not the rate loop); `rcS:173` IMU_GYRO_FFT_EN 1
  (sim default; the FFT is a gyro consumer, a small CPU cost at 800 Hz). Not changed.
- Env var PX4_PARAM_IMU_GYRO_RATEMAX makes the value non-default, so `param compare ... 400` in rc.mc_defaults is false for 400
  (stays 400) and true-or-irrelevant for 800 (set-default 800 does not override a user value). Same result either way.
  UNVERIFIED that the env override is applied before rc.mc_defaults (the runner already uses this for SIM_GZ_* and
  SENS_GNSS0_DELAY; the pre-test checks the value with `px4-param show IMU_GYRO_RATEMAX` or the ULog rate).

## Item 6: units
- eRPM latency (`GZMixingInterfaceESC.cpp:128-183`): `motorSpeedCallback` subscribes to `/<model>/command/motor_speed`
  (:54), i.e. the PX4 actuator command frames the bridge itself publishes, NOT a gz physics topic. One callback = one ESC
  output frame = one actuator_motors update (one rate-loop cycle, unless MixingOutput throttles it; UNVERIFIED). So the unit
  is output frames, independent of the physics step. `SIM_GZ_ERPM_LAT` (module.yaml:116, int 0..8, default 0, boot-time) adds
  frames on top of the fixed one-frame reply (:150 comment). The airframe does not set it (only scenario `lat`,
  scenarios.py:148, sets 2).
  Latency with the current setting (ERPM_LAT 0): one frame = 1 output period = 4 ms at a 250 Hz output, 1.25 ms at 800 Hz
  (and 2.5 ms at 400, 3.75 ms at 267). It follows the controller rate, not the 4 ms / 1.25 ms physics step. With LAT 2: 12 ms
  at 250 Hz, 3.75 ms at 800 Hz. The rotor speed sampled (`_rotor_rpm`) is updated by the JointStatePublisher once per physics
  step (`update_rate 0`), a further quantisation of up to one step (4 ms old, 1.25 ms new).
- `MC_INDI_DELAY` and `MC_INDI_ERPM_DLY` (`mc_indi_rate_control_params.yaml:113-128`): controller cycles (int, 0..4; defaults
  0 and 1). `MC_INDI_DT_MAX` (:151) per cycle, not per second. In seconds at 800/400/267 Hz: 1 cycle = 1.25/2.5/3.75 ms.
  The 4 ms-era meaning of "1 cycle" no longer holds; scale per rate in stage 3 (D-SIM-STEP consequence). Firmware untouched.

## Checks done
- `python3 -m py_compile` run_scenario.py, model_variant.py: ok. `bench/tests/test_applied_timing.py`, `test_metrics.py` run
  directly (python3 -I): both pass; neither imports run_scenario/model_variant (no test touches the changed code).
- No other file references `build_world` or `--imu-rate` (grep in bench/).

## Only a simulation pre-test can confirm
1. World step really 1.25 ms: the `set_physics` call in px4.log ("max_step_size=0.00125"), and gz sim time advance per step
   (`gz topic -e -t /world/default/stats`), plus run.json `physics_step_s`.
2. gz IMU really 800 Hz: sensor_gyro ~800 Hz in sim time (ULog), `vehicle_imu_status.gyro_raw_rate_hz`; jitter of sample dt.
3. `vehicle_angular_velocity` rate = 800 / 400 / 266.7 Hz within 1 % for `--rate-hz` 800/400/267, timestamp_sample spacing.
4. IMU_GYRO_RATEMAX/CUTOFF/DGYRO_CUTOFF values actually in force (env override before rc.mc_defaults).
5. Speed-4 wall/sim ratio with the 1.25 ms world and 800 Hz callbacks (fallback in D-SIM-STEP is the 0.25 ms option).
6. Logger drops ("logger: ... dropped" in px4.log) with sensor_gyro 800 Hz plus the full-rate topics at 800 Hz (expected log
   rates: sensor_gyro ~800 Hz, vehicle_angular_velocity/actuator_motors/esc_status/vehicle_torque_setpoint/
   vehicle_thrust_setpoint/control_allocator_status ~ rate_hz; vehicle_imu_status low, on change or at its fixed publish
   interval, the 4 ms-era ~1/4 volume no longer applies: ~3x the 250 Hz volume at 800 Hz).
7. The plant with the 1.25 ms step (rotor dynamics, contact) vs the 4 ms world: PID baseline re-flown (overturn condition).
8. ERPM output frame rate (is actuator_motors/ESC output 1 per rate-loop cycle?) to turn the latency frames into ms.
9. Hover/arm timing constants (T_ARM_S etc.) were tuned on the 4 ms world; EKF/arming may differ with the 800 Hz IMU.
