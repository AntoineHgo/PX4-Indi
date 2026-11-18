# Delay line hooks for G3 (S94 design note, no code written)

Scope: hook A (added loop delay 0-10 ms, actuator path and IMU path) and hook B (GNSS sample latency 80-250 ms).
Both listed MISSING in `gates_g3_g8_final_s94.md` section 1. Pattern to reuse: `SIM_GZ_ERPM_LAT`
(`GZMixingInterfaceESC.cpp:161-163`, fixed ring `ERPM_DELAY_LEN`, `module.yaml:116`, reboot_required).
Fixed-seed rng pattern: `_random_state` at `GZMixingInterfaceESC.hpp:131`.

## 0. Facts checked in the tree
- IMU: `GZBridge::imuCallback` (`GZBridge.cpp:653`). `timestamp_sample` is the gz header stamp, `timestamp = min(stamp, hrt_absolute_time())`
  (line 665). Output is `_px4_accel[i].update(timestamp, ...)` / `_px4_gyro[i].update(...)` (lines 685-686, in PX4Accelerometer/Gyroscope,
  `PX4Accelerometer::update(timestamp_sample, x,y,z)`). Rotor vibration is added before (line 681), keep it before the delay line.
- Motors: `GZMixingInterfaceESC::updateOutputs` (`GZMixingInterfaceESC.cpp:75`) builds `gz::msgs::Actuators` and calls `_actuators_pub.Publish`
  (about line 114). This is the single point where motor commands leave PX4. Servo and wheel interfaces are separate (out of scope, quad only).
- GNSS: `GZBridge::navSatCallback` (`GZBridge.cpp:899`) builds `sensor_gnss_s`, sets `timestamp = timestamp_sample = timestamp` (line ~971-972,
  the local `timestamp`), then `failure_injection::process_gnss(...)` and `_sensor_gnss_pub[i].publish` (end of function). There is also
  `sensor_gps_sim` (`src/modules/simulation/sensor_gps_sim/SensorGpsSim.cpp`), a separate publisher; it is NOT the path used by the gz
  bridge when `SIM_GZ_EN_GPS` > 0 (UNVERIFIED which one the indi SITL start script enables; check `bench/` startup before building).
- Receiver side: `SENS_GNSS0_DELAY` (ms) is consumed in `VehicleGPSPosition.cpp:162` (stored as us) and read by `EKF2.cpp:995`; the EKF
  subtracts it from the GNSS sample time. So `timestamp_sample` must stay the TRUE measurement time and `timestamp` must be the delivery time.
- Physics step 4 ms (`Tools/simulation/gz/worlds/*.sdf` `max_step_size`, at least frictionless/aruco; the indi world not checked).
  SITL time is slaved to gz clock (`clockCallback`, `GZBridge.cpp:476`). Hence all delays are quantised to 4 ms at the IMU/clock rate.

## 1. Parameters (module.yaml in gz_bridge, group next to SIM_GZ_ERPM_LAT)
| Name | Type | Unit | Range | Default | Meaning |
|---|---|---|---|---|---|
| `SIM_GZ_DLY_ACT` | int32 | ms | 0-10 | 0 | motor command delay, PX4 -> gz |
| `SIM_GZ_DLY_IMU` | int32 | ms | 0-10 | 0 | IMU delay, gz -> PX4 sensors |
| `SIM_GZ_GPS_DLY` | int32 | ms | 0-250 | 0 | GNSS delivery latency L |
| `SIM_GZ_DLY_RAND` | int32 | - | 0-1 | 0 | optional: 0 = constant delay only (no jitter; not needed for G3, omit unless asked) |
All reboot_required (like ERPM_LAT) so the ring is sized once at init. Default 0 means the code path is skipped
(`if (delay_us == 0) { publish immediately }`) so the output is bit-identical to today. 0 must not push through the ring.
Delay-split convention for "added loop delay D": D = act + imu, the campaign sets the split explicitly; log both.

## 2. Hook A1: actuator path (file `GZMixingInterfaceESC.cpp`, function `updateOutputs`)
- Insert after the `rotor_velocity_message` is built and before `_actuators_pub.Publish`. Hold a ring of `{sim_time_us, vector<double> vel}`.
- Key: `hrt_absolute_time()` at the `updateOutputs` call (this is sim time, the clock is slaved to gz). Entry released when
  `now >= t_in + delay_us`. Release is evaluated in `updateOutputs` (called at the mixer rate) AND must also be flushed from `Run()` or a
  timer so a delay shorter than the output period is not stretched to the next call. Design choice: delivery is quantised to the next
  mixer call, so effective delay = ceil(delay / T_out) * T_out when the mixer is slower than the delay. State this in the log (see section 5).
  If the mixer runs at 250 Hz (4 ms) the 0-10 ms range gives steps of 4 ms (0,4,8,12): the 10 ms upper end cannot be exact. Alternative: run the
  mixer at >= 1 kHz in the delay test world, or accept quantisation and log applied delay. UNVERIFIED actual `SIM_GZ_EC` output rate.
- Size: `ceil(10 ms / T_out) + 2` entries, static array with `MAX_ACTUATORS` doubles, no allocation at runtime.
- Latest-wins: if two entries are due in one call, publish the older then the newer is not wanted (gz keeps the last); publish only the
  newest due entry (drop the intermediate ones, count them in the log).

## 3. Hook A2: IMU path (file `GZBridge.cpp`, function `imuCallback`)
- Insert just before lines 685-686. Ring entry: `{timestamp_sample, accel_b (3), gyro_b (3)}` per instance `[_MAX_IMU_SENSORS]`.
- Key: header stamp `timestamp_sample` (sim time). Release in the same callback and the following callbacks (IMU callbacks arrive at the
  gz IMU rate, so release is exact to one IMU period; at 250 Hz gz IMU this is 4 ms, same quantisation note as A1).
- Size: `ceil(10 ms / T_imu) + 2`, T_imu from the sdf `update_rate` (UNVERIFIED; take the worst case 1 kHz => 12 entries).
- Timestamp rule: delayed sample is published with `timestamp_sample` = ORIGINAL sample time minus nothing, and `timestamp` = delivery time
  (`hrt_absolute_time()` at release). The driver `PX4Accelerometer::update(timestamp_sample, ...)` takes only the sample time and stamps
  `timestamp` itself, so call `update(original_sample_time, ...)`. A real IMU with a filter delay reports the same: the sample time is the
  measurement instant. Do NOT shift `timestamp_sample` forward (that would hide the delay from the estimator and the loop would see no
  added latency in the logged data but a real one in the dynamics: the lesson on mixing the two). Groundtruth topics at lines 714-778 use the
  non-delayed timestamp, leave them untouched (truth must stay truth).
- Same delay for accel and gyro of one instance, or the gyro/accel skew would be a different hook.

## 4. Hook B: GNSS sample delay (file `GZBridge.cpp`, function `navSatCallback`)
- Insert replacing the final `process_gnss ... publish`. Ring per instance of fully built `sensor_gnss_s` structs (already contains
  `timestamp_sample`). Size: L_max 250 ms at max GNSS rate. gz navsat rate is UNVERIFIED (assume 10 Hz, worst case 50 Hz): `ceil(0.25*50)+2 = 15` entries
  of `sensor_gnss_s` (~200 B) per instance, static array.
- Key: `sensor_gnss.timestamp_sample` (sim time of generation t). Release when `hrt_absolute_time() >= timestamp_sample + L`.
  Release check runs in `navSatCallback` and in the 10 ms `ScheduleDelayed` Run loop (`GZBridge.cpp:201`) so delivery is not tied to the next
  fix arriving. Resolution = Run period 10 ms (or the clock tick, whichever is coarser) => report applied L.
- Timestamps at publish: `timestamp_sample` UNCHANGED (true measurement time t, which is what a receiver with PVT latency does when it back-dates
  or what `SENS_GNSS0_DELAY` is meant to model: the EKF compares with `now - delay`). `timestamp` = delivery time (`hrt_absolute_time()`
  at release, not `t`). Never rewrite `timestamp_sample` to the delivery time: then the EKF-side delay compensation would be applied twice
  and matched/mismatched tests would be meaningless.
- Failure injection: apply `process_gnss` at generation time (before the ring) or at release? Choose at release, so a stuck/dropout
  window is keyed on delivery time as for a real link. State this choice in the PR; UNVERIFIED how `_gnss_stuck` is wired.
- Matched case: `SENS_GNSS0_DELAY` = L. Mismatched case: any other value. Keep `SIM_GZ_GPS_DLY` independent of `SENS_GNSS0_DELAY`.
- sensor_gps_sim: if the indi SITL uses it instead, an equivalent ring is needed in its publish site (not read yet).

## 5. Determinism and logging
- No wall clock. Only `hrt_absolute_time()` (slaved to gz sim clock) and gz header stamps. No rng in these hooks. Ring state resets at init, not at re-arm.
- Log: new uORB topic is heavy; cheaper options in order: (1) `PX4_INFO` one-line at start with the three applied delays after quantisation,
  (2) a small `sim_delay_status` topic (fields: `timestamp`, `act_delay_us`, `imu_delay_us`, `gnss_delay_us`, `act_dropped`, `ring_overflow`)
  published at 1 Hz and on any overflow, added to the indi logged_topics list. Overflow must be visible, never silent: count and set a flag.
- Per-sample ages are recoverable from the ulog without extra topics: GNSS `timestamp - timestamp_sample`; IMU `timestamp - timestamp_sample`
  (check that the driver topic keeps both).

## 6. G1.5 verification tests (one per hook, each with a negative control)
- A1 actuator: step the motor command in a scripted run; compare `actuator_motors` log time with `esc_status` echo (`SIM_GZ_ESC_FB=0` echoes the
  command as applied by the bridge) or gz joint-velocity response. Cross-correlate commanded vs applied rotor speed on a 4 ms grid: lag must equal
  `act_delay_us` +- one physics step. Negative: with `SIM_GZ_DLY_ACT=8` set the log field to 0 (or drop the ring) and require the test to FAIL.
- A2 IMU: inject a body rate chirp with gz truth topics (`vehicle_angular_velocity_groundtruth`, undelayed) and cross-correlate against
  `sensor_gyro`: lag = `imu_delay_us` +- one IMU period. Negative: the same test with the ring bypassed must report lag 0 and fail the assertion.
- B GNSS: on the log, `median(timestamp - timestamp_sample)` of `sensor_gnss` equals L +- one Run/physics step (10 ms), max over the run < L + 10 ms,
  and no sample has `timestamp_sample` later than `timestamp`. Plus an estimator check: hover with L=200 ms and `SENS_GNSS0_DELAY` 0 vs 200,
  the innovation test ratio / position innovation RMS is lower for the matched case (sign of the check, thresholds to be set in G1.5, not claimed here).
  Negative: stale-clock bug (publishing `timestamp_sample = t+L`) must make the age test report 0 and fail.
- Default-off identity: run today's baseline scenario with all three params 0, compare ulog `sensor_gyro`, `sensor_gnss`, `actuator_motors`
  byte for byte with an existing result (bit-identical required; same fixed seed, same sim speed).
- Overflow test: set L=250 with the GNSS rate at max and assert `ring_overflow == 0`; set the ring artificially at 2 entries and assert the flag.

## 7. Risks to lockstep and scheduling
- The IMU hook runs inside a gz transport callback thread; the actuator hook inside the mixer (`Run` under `_node_mutex`, see `Run()` in
  `GZMixingInterfaceESC.cpp`). Rings need the existing lock (`_node_mutex` for A1) and a separate mutex or single-thread access for A2/B,
  since callbacks of different topics can run concurrently (UNVERIFIED thread model of gz transport; assume concurrent).
- Releasing from the 10 ms `ScheduleDelayed` loop makes delivery depend on the work-queue timing; under `PX4_SIM_SPEED_FACTOR` the loop runs in
  sim time through the slaved clock, so the delay in sim time is preserved, but only to one 10 ms Run period. IMU release must therefore stay in the
  IMU callback (not the Run loop) to avoid adding 10 ms jitter to a 0-10 ms delay.
- Delaying the IMU also delays the EKF/INDI wake-up (they are driven by `sensor_gyro` / `vehicle_angular_velocity` publication), so the loop period
  jitter changes by up to one IMU period: that is the intent, but check no scheduler starvation at `imu_delay` = 10 ms.
- Delay at the ring boundary at start: the first `delay` interval has no data; publish nothing (not zeros) and do not hold arming on it; check
  preflight (`sensor_gyro` stale) is not tripped for the first 10 ms.
- No build, no run made in this note. All line numbers from reading the tree at the S94 commit.

## Orchestrator note (S94)
The 4 ms step was read from the frictionless/aruco worlds. The quad5in runs use the D-SIM-STEP step (800 Hz IMU), so the ring sizes and the delay quantisation must be recomputed from the flown world before the build. Which GNSS path the flown SITL uses (gz navsat or sensor_gps_sim) must be checked first.
