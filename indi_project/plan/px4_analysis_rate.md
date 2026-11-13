# PX4 current rate-control path: analysis for INDI design

Read-only analysis, repo checkout on branch feat/indi-control. Paths relative to repo root.
Abbreviations: MRC = src/modules/mc_rate_control/MulticopterRateControl.{cpp,hpp}.

## 1. Module `mc_rate_control`

### Trigger and scheduling
- WorkItem on WQ `px4::wq_configurations::rate_ctrl` (MRC.cpp:50).
- Triggered by a uORB callback on `vehicle_angular_velocity` (`SubscriptionCallbackWorkItem`, MRC.hpp:109; `registerCallback()` in init, MRC.cpp:69). So loop rate == publish rate of vehicle_angular_velocity (see section 3), i.e. one controller run per filtered gyro publication. No fixed timer.
- dt = `timestamp_sample` difference, clamped to [0.125 ms, 20 ms] (MRC.cpp:133-137).

### Inputs
- `vehicle_angular_velocity.xyz` (filtered, bias-corrected rates, FRD rad/s) -> `rates` (MRC.cpp:139) and `.xyz_derivative` (filtered angular acceleration rad/s^2) -> `angular_accel` (MRC.cpp:140). Msg: msg/versioned/VehicleAngularVelocity.msg.
- `vehicle_rates_setpoint` (roll/pitch/yaw rad/s + `thrust_body[3]`), only re-read when updated; non-finite axis replaced by the measured rate (MRC.cpp:184-188). Values are held between updates (members `_rates_setpoint`, `_thrust_setpoint`, MRC.hpp:129,132).
- Acro mode (manual && !attitude): rates setpoint generated from `manual_control_setpoint` via superexpo and MC_ACRO_*_MAX; thrust_body z = -(throttle+1)/2; module also publishes `vehicle_rates_setpoint` itself (MRC.cpp:159-182).
- Thrust is NOT computed by the rate controller: `_thrust_setpoint` from rates setpoint is passed through unchanged to `vehicle_thrust_setpoint` (MRC.cpp:248).
- Other subs: `vehicle_control_mode`, `vehicle_land_detected` (landed, maybe_landed), `vehicle_status`, `control_allocator_status`, `battery_status`, `parameter_update` (MRC.hpp:99-109).

### Outputs
- `vehicle_torque_setpoint` and `vehicle_thrust_setpoint` (or `*_virtual_mc` when started with `vtol` arg) (MRC.cpp:51-52, 245-277). `timestamp_sample` copied from the gyro sample (MRC.cpp:271,275).
- Torque xyz: non-finite -> 0 (MRC.cpp:249-251).
- Also `rate_ctrl_status` (integrators only, lib rate_control.cpp:120-125), `actuator_controls_status_0` (control power over 0.5 s, MRC.cpp:287-309), `vehicle_rates_setpoint` (acro only), gain_compression topic.
- Optional battery scaling: `MC_BAT_SCALE_EN`; multiplies thrust and torque by battery_status.scale and constrains to [-1,1] (MRC.cpp:253-269).

### Control law call and post-processing (MRC.cpp:227-236)
1. `_rate_control.update(rates, _rates_setpoint, angular_accel, dt, _maybe_landed || _landed)` (MRC.cpp:228-229). Law detailed in section 2.
2. GainCompression3d (MC_GC_EN, default 0; MC_GC_GAIN_MIN default 0.3): multiplies torque by a per-axis gain in [min,1] reduced when an HPF'd torque oscillation is detected (src/lib/rate_control/gain_compression.cpp:~70-100; params in gain_compression_params.yaml:22-36). Applied on the controller output (MRC.cpp:232-233).
3. Yaw-only low-pass `AlphaFilter _output_lpf_yaw` on torque z, cutoff MC_YAW_TQ_CUTOFF (default 2 Hz) (MRC.cpp:236, 104; yaml:227-237).

### Angular acceleration use (D term)
- The "D term" is `-_gain_d .* angular_accel` where angular_accel is `xyz_derivative` straight from the sensor module, so it is a derivative of measurement (not of error), no setpoint kick (lib rate_control.cpp:78). No filtering in the controller; filtering is done upstream by IMU_DGYRO_CUTOFF (section 3).

### Anti-windup / allocator feedback
- Each time `control_allocator_status` has a new sample (MRC.cpp:208): if `!torque_setpoint_achieved`, for each axis `unallocated_torque[i] > FLT_EPSILON` -> positive saturation flag, `< -FLT_EPSILON` -> negative flag (MRC.cpp:212-221). Flags passed via `setSaturationStatus` (MRC.cpp:224). A TODO notes the unallocated value itself is not used (MRC.cpp:223).
- Flags are only used to clip the integrator input (section 2). Note: flags are only refreshed when a new status arrives; otherwise previous values stay in the RateControl object.
- Allocator status definition: msg/ControlAllocatorStatus.msg (`unallocated_torque = torque_setpoint - allocated_torque`, `actuator_saturation[16]`).

### Landed / arming
- Integrator and gain compression reset when `!flag_armed` or vehicle_type != ROTARY_WING (MRC.cpp:195-198). Gain compression reset also when `_landed` (MRC.cpp:201-203).
- When `_maybe_landed || _landed` the integrator is frozen (not reset), but P/D/FF torque still output (MRC.cpp:229; lib rate_control.cpp:81-83).
- Controller runs only if `flag_control_rates_enabled` (MRC.cpp:192); nothing is published otherwise. Initial `_landed=_maybe_landed=true` (MRC.hpp:120-121).

### Parameters (src/modules/mc_rate_control/mc_rate_control_params.yaml)
Per axis (roll/pitch/yaw): `MC_{ROLL,PITCH,YAW}RATE_{P,I,D,FF,K}`, `MC_{RR,PR,YR}_INT_LIM`. Defaults: P 0.15/0.15/0.2, I 0.2/0.2/0.1, D 0.003/0.003/0.0, INT_LIM 0.3 all, FF 0, K 1.0 (yaml lines 5-213). Gains are in the parallel form multiplied by K: gain = K*P etc. (MRC.cpp:83-88; K doc yaml:56-73). Also MC_YAW_TQ_CUTOFF=2 Hz, MC_BAT_SCALE_EN=0, MC_GC_EN=0, MC_ACRO_* (mc_acro_params.yaml). Module built with MODULE_CONFIG both yaml files, DEPENDS RateControl (CMakeLists.txt).

## 2. Library `src/lib/rate_control`

### Exact control law (rate_control.cpp:71-86)
```
e      = rate_sp - rate
torque = Kp.*e + I_state - Kd.*angular_accel + Kff.*rate_sp        (line 78)
if (!landed) updateIntegral(e, dt)   // integrator updated AFTER computing torque (uses previous I)
return torque
```
Everything element-wise (`emult`) on Vector3f, units: torque normalised ([-1,1] per rate_control.hpp:94 doc).

### Integrator (rate_control.cpp:88-118)
- Per axis: if positive saturation flag, `e = min(e,0)`; if negative flag, `e = max(e,0)` (lines 92-99), i.e. conditional integration (clamping) driven by allocator flags.
- Error-dependent factor: `i_factor = max(0, 1 - (e/radians(400))^2)` (lines 107-108).
- `I += i_factor * Ki * e * dt`, forward Euler; only stored if finite, then clamped to +-`_lim_int` (lines 111-115).
- Reset: `resetIntegral()` or per axis (rate_control.hpp:103-115). States: `_rate_int` only; no filter state in the class.
- Setters: setPidGains, setIntegratorLimit, setFeedForwardGain, setSaturationStatus, set{Positive,Negative}SaturationFlag (hpp:59-87). Class is plain C++, no uORB subs, only includes `rate_ctrl_status.h` for status filling (hpp:45, 121) and is trivially unit-testable.

### Unit test (rate_control_test.cpp)
- Only one test exists: `TEST(RateControlTest, AllZeroCase)` (rate_control_test.cpp:39-44): zero inputs, dt=0, expects zero torque. Includes `<gtest/gtest.h>` and `<lib/rate_control/rate_control.hpp>`, `using namespace matrix` (lines 34-37). Very thin; no integrator/saturation tests exist to copy, only the skeleton.
- Build: last line of src/lib/rate_control/CMakeLists.txt: `px4_add_unit_gtest(SRC rate_control_test.cpp LINKLIBS RateControl)`. The library itself: `px4_add_library(RateControl rate_control.cpp ... )`, `target_link_libraries(RateControl PRIVATE mathlib)`, `target_include_directories(... PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})`.
- `px4_add_unit_gtest` is defined in cmake/px4_add_gtest.cmake:73-; active only if BUILD_TESTING. Target name = `unit-` + filename without extension with the string "Test" removed (cmake:~84-86); for `rate_control_test.cpp` (lowercase, nothing removed) -> `unit-rate_control_test`; EXCLUDE_FROM_ALL executable. A file named `IndiRateControlTest.cpp` would give target `unit-IndiRateControl`. (Not built or run here.)

## 3. `src/modules/sensors/vehicle_angular_velocity/` (VehicleAngularVelocity.{cpp,hpp}, imu_gyro_parameters.yaml)

### Trigger and publication rate
- Triggered by callbacks on `sensor_gyro_fifo` (preferred) or `sensor_gyro` (hpp:110-112; selection in cpp:266-306). Filters run at the FULL raw gyro rate (e.g. 8 kHz FIFO); yaml says so explicitly (yaml:63-70). `_filter_sample_rate_hz` = raw gyro rate from `vehicle_imu_status.gyro_raw_rate_hz` or FIFO dt (cpp:105-131, 291).
- Publication throttled by `IMU_GYRO_RATEMAX` (enum 100..2000 Hz, default 400 Hz, reboot required; yaml:63-82). Yaml: "This is the loop rate for the rate controller and outputs" (yaml:66-67). `_publish_interval_min_us = constrain(round(1e6/ratemax - 0.5*publish_interval), 125, 10000)` (cpp:149-150); `set_required_updates(samples)` batches uORB callbacks (cpp:139-146). Published by `CalibrateAndPublish` only if `timestamp_sample >= _last_publish + interval` (cpp:926-949). => mc_rate_control runs at about IMU_GYRO_RATEMAX (default 400 Hz) while filtering is at kHz.
- Published values are the LAST filtered sample of the N-sample FIFO batch (cpp:845-857; `return data[N-1]`, cpp:768-769), no averaging across the batch.

### Angular velocity chain (FilterAngularVelocity, cpp:733-771), applied in place on raw (unscaled) samples, in this order
1. Dynamic notch from ESC RPM (`NotchFilter<float>` per harmonic/axis/ESC; `_dynamic_notch_filter_esc_rpm`, hpp:153-154), enabled by IMU_GYRO_DNF_EN (default 0), IMU_GYRO_DNF_HMC=3 harmonics, DNF_BW=15 Hz, DNF_MIN=25 Hz (yaml:104-144). Compiled out with CONSTRAINED_FLASH.
2. Dynamic notch from FFT peaks (`NotchFilter<float> _dynamic_notch_filter_fft[3][MAX_NUM_FFT_PEAKS]`, hpp:168).
3. Static notches `IMU_GYRO_NF${i}_FRQ/_BW` (default FRQ 0 = off, BW 20 Hz; yaml:8-40; hpp:137 `NotchFilter<float>[NUM_NOTCH_FILTERS][3]`).
4. Low-pass `math::LowPassFilter2p<float> _lp_filter_velocity[3]` (hpp:132), cutoff `IMU_GYRO_CUTOFF` default 40 Hz (yaml:46-62), 2nd-order Butterworth (yaml:50; design in src/lib/mathlib/math/filter/LowPassFilter2p.hpp:61-91: `ohm=tan(pi*fs_ratio)`, Q=1/sqrt2, bilinear, direct form II at :98-109). cutoff <=0 or >= fs/2 -> filter disabled (:63-67).
- Then (cpp:935-940): `xyz = calibration.Correct(filtered_uncalibrated) - _bias` (rotation, scale, in-run bias removal). Bias is NOT removed from `xyz_derivative`.

### Angular acceleration chain (FilterAngularAcceleration, cpp:775-787)
- Called right after FilterAngularVelocity on the same `data[]` array (cpp:855-856 FIFO, 900-901 non-FIFO). Because applyArray works in place (LowPassFilter2p.hpp:112-117, NotchFilter.hpp:78-88), `data[]` already holds the NOTCH+LPF-FILTERED gyro. So acceleration = backward finite difference of the FILTERED gyro (not raw), per raw sample: `(data[n] - prev)*inverse_dt` (cpp:781), `prev = data[n]` (cpp:783; the member is named `_angular_velocity_raw_prev` but holds the filtered value). Then a first-order low-pass `AlphaFilter<float> _lp_filter_acceleration[3]` (hpp:177) per raw sample, cutoff `IMU_DGYRO_CUTOFF` default 20 Hz (yaml:84-103). The yaml text says "2nd order butterworth" for DGYRO (yaml:86-87), but the code type is `AlphaFilter`, i.e. 1st-order exponential: `state += alpha*(x - state)` (AlphaFilter.hpp:169), `alpha = dt/(tau+dt)`, `tau = 1/(2*pi*fc)` (AlphaFilter.hpp:66-101). DOC/CODE MISMATCH, trust the code.
- DGYRO_CUTOFF=0 (or invalid) -> `setAlpha(1)`, no acceleration filtering (cpp:183-190).
- Output rotated with `calibration.rotation()` only (cpp:941), no scale/bias.
- Filter (re)initialisation: `_reset_filters` on sample-rate or cutoff change (cpp:120-131, 398-404, 438-443); ResetFilters seeds states from last published values (cpp:163-195).

### Effective delay/phase (my low-frequency estimates at defaults, not measured)
- Rate (xyz): LPF2p Butterworth group delay at DC = sqrt(2)/(2*pi*fc) = 5.6 ms at 40 Hz. Notches (if enabled) add little below their band. Upstream IMU/ESC latency not included.
- Acceleration (xyz_derivative): LPF2p 5.6 ms + backward difference half-sample (0.5/fs_raw, negligible at kHz) + AlphaFilter tau = 1/(2*pi*20) = 8.0 ms => about 13.6 ms at DC, i.e. about 8 ms MORE lag than the rate. Above 20 Hz the D chain rolls off at 20 dB/dec (alpha) then -40 dB/dec more above 40 Hz (LPF2p), on top of the differentiator's +20 dB/dec.
- The published value is the last raw-rate sample of a batch, consumed by mc_rate_control with an additional callback/work-queue latency of up to one publish period (2.5 ms at 400 Hz); allocator and ESC/motor dynamics come after that.
- `timestamp_sample` in vehicle_angular_velocity refers to the raw sample time and is NOT compensated for filter delay.

### Exact filter classes to reuse on the actuator signal (synchronisation)
- `math::LowPassFilter2p<float>` (src/lib/mathlib/math/filter/LowPassFilter2p.hpp) for the rate path; `AlphaFilter<float>` (src/lib/mathlib/math/filter/AlphaFilter.hpp) for the acceleration D-filter; `math::NotchFilter<float>` (src/lib/mathlib/math/filter/NotchFilter.hpp) for notches.
- To synchronise, pass the INDI actuator/torque signal through the same cascade as the one behind `xyz_derivative`: same notches -> LPF2p(IMU_GYRO_CUTOFF) -> AlphaFilter(IMU_DGYRO_CUTOFF). The differencing is linear and commutes with these LTI filters, so filtering the torque with the same cascade matches delay and gain of the acceleration estimate. Caveat: the sensor filters run at the raw gyro rate while the controller runs at IMU_GYRO_RATEMAX; a copy in the controller has to be designed for the controller rate (small bilinear-warping difference if fc << fs/2), or the sensor module has to expose the filtered torque path.

## 4. Torque/thrust normalisation and scaling to actuators

- `vehicle_torque_setpoint.xyz`: "torque setpoint about X, Y, Z body axis (normalized)" (msg/VehicleTorqueSetpoint.msg). `vehicle_thrust_setpoint.xyz`: `@range -1, 1`, thrust along body axes, NaN stops the motors (msg/VehicleThrustSetpoint.msg). Rate controller doc: "[-1,1] normalized torque vector" (rate_control.hpp:94). Not SI: the PID gains (P 0.15, D 0.003, ...) are normalised-torque per rad/s and per rad/s^2.
- Multirotor thrust: `thrust_body` z (negative up, [-1,0]) comes from the upstream controller via `vehicle_rates_setpoint` and passes unchanged (MRC.cpp:188, 248).
- Allocation: ControlAllocator runs on every new `vehicle_torque_setpoint` (callback registered cpp:96; update cpp:383-395; `timestamp_sample` stored cpp:394). Torque and thrust are combined into a 6-vector, `allocate()`, `updateSetpoint`, optional `applySlewRateLimit(dt)` (only if `_has_slew_rate`), `clipActuatorSetpoint()` (cpp:440-458). Output `actuator_motors.control[]` (normalised motor command, NaN = stop) at cpp:764-785, with `timestamp_sample` propagated (cpp:753).
- Effectiveness inverse normalisation: ControlAllocationPseudoInverse computes `_mix = geninv(effectiveness)` then divides columns by `_control_allocation_scale` (src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp:66-80, 155-170). For multirotors `getNormalizeRPY` returns true (src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessMultirotor.hpp:52-55), so roll and pitch share one scale `max(roll_scale, pitch_scale)` with `scale = sqrt(||mix col||^2 / (n_nonzero/2))`, yaw uses `max(mix col 2)` (PseudoInverse.cpp:83-125). Net effect: a unit of normalised torque is a geometry-dependent quantity, independent of inertia and of the physical N*m. The scale is captured at geometry set-up and not refreshed after an actuator failure (cpp:72). Not verified: the numeric relation to physical N*m, and whether `_metric_allocation` is ever enabled for multicopters (PseudoInverse.cpp:59-62 skips normalisation in that mode).
- Allocator feedback `control_allocator_status` is published at most every 5 ms (ControlAllocator.cpp:465-475; comment: "used for slower dynamics (i.e. anti-integrator windup)"). `unallocated_torque = control_setpoint - allocated_control`, same normalised units (cpp:666-684); `torque_setpoint_achieved` = squared norm < 1e-6 (cpp:691-693). `allocated_control` is derived from the commanded actuator setpoint after clipping, not from ESC/motor feedback. The rate controller receives it at 5 ms decimation at most.
- Optional battery scaling in the rate controller (MC_BAT_SCALE_EN) rescales torque/thrust before the allocator (MRC.cpp:253-269).

## 5. Implications for INDI

### Where it hooks in
- Cleanest option: a drop-in replacement of the control law inside `mc_rate_control` (or a sibling module `mc_indi_rate_control` with identical I/O and a parameter switch), keeping the same contract: trigger = `vehicle_angular_velocity` callback (MRC.hpp:109), inputs `vehicle_angular_velocity.{xyz, xyz_derivative}`, `vehicle_rates_setpoint` (rates + `thrust_body`), `vehicle_land_detected`, `vehicle_control_mode`, `control_allocator_status`; outputs `vehicle_torque_setpoint` (normalised) and `vehicle_thrust_setpoint` (pass-through) on the same topics (VTOL variants `*_virtual_mc`). The pure-math class pattern (`RateControl` in src/lib/rate_control, no uORB dependency except the status msg) is the template: a new `IndiRateControl` lib with `update(rate, rate_sp, angular_accel, dt, landed)`-like signature, plus a `*_test.cpp` using `px4_add_unit_gtest` as in section 2. Arming/landed handling, acro setpoint generation, battery scaling, NaN guarding and the yaw output filter can be reused as they are in the module around the library call (MRC.cpp:159-277).
- Everything downstream (control allocator, effectiveness matrix) is unchanged; INDI output is still a normalised torque delta added to the previous command.

### Signals available for the incremental law  tau_k = tau_{k-1} + G^-1 (alpha_cmd - alpha_filt)
- Measured angular acceleration: `xyz_derivative` (filtered, see section 3). Rate: `xyz`. Rate setpoint: `vehicle_rates_setpoint`. Note: no angular acceleration SETPOINT exists upstream; INDI needs `alpha_cmd = Kp*(rate_sp - rate) (+ Kff*d rate_sp/dt)`, to be derived in the controller.
- Previous torque command: the module's own last `vehicle_torque_setpoint` (the code already keeps `vehicle_torque_setpoint` locally, MRC.cpp:246-251). Candidate "actuator" signal for the incremental term. After the allocator the realised torque differs when saturated/slew-limited/clipped; the allocator gives `unallocated_torque` (cpp:678-685) as the closest feedback of "commanded minus achieved", at <=5 ms decimation, but NOT the true motor/ESC state. `actuator_motors` (normalised motor command, cpp:764-785) and `esc_status` RPM (consumed by the dynamic notch, VehicleAngularVelocity.cpp esc handling, hpp:153-162) exist but were not examined for use as feedback.
- Control effectiveness G (rate-of-change of angular acceleration per unit of normalised torque) is not available in PX4: it is inertia-dependent and the normalisation (section 4) is geometry-dependent. It must be a parameter (per axis) or estimated online.

### Risks
1. Delay mismatch (main one): angular acceleration lags the rate by ~8 ms more and the actuator command by the whole chain (rate LPF 5.6 ms + D alpha 8.0 ms + allocator + motor). INDI requires acceleration and the actuator-increment signal to be time-aligned, otherwise the inversion is wrong and stability margins collapse (see Wang 2019 note in indi_project docs). Mitigation: low-pass the previous torque command with the same filter classes/cutoffs (LPF2p + AlphaFilter, sec. 3), designed at the controller rate; or reduce IMU_DGYRO_CUTOFF lag only if noise allows.
2. D-filter structure: the existing D filter is 1st-order at 20 Hz on a derivative of an already 40 Hz-LPF2p signal; its doc claims Butterworth (code/doc mismatch). INDI tuning will be sensitive to this; its cutoffs are shared global params (IMU_GYRO_CUTOFF also affects the estimator-independent rate input, hpp:196-198, yaml:46-62), so changing them affects the legacy PID simultaneously. Consider a separate acceleration filter chain, or a different estimate (e.g. a high-rate filtered derivative or model-based) selected via param.
3. Normalised units: torque is dimensionless and geometry-scaled (normalize RPY, section 4), the same numeric torque yields different angular acceleration vs vehicle; G must be identified per airframe (or via hover-thrust-like online estimator). The yaw axis has a separate scale (max of column) and its own existing 2 Hz output LPF (MC_YAW_TQ_CUTOFF, MRC.cpp:236) that adds phase; INDI on yaw should probably bypass/replace it. Battery scaling (MRC.cpp:263-268) changes effective G on the fly and also scales torque before the allocator.
4. Loop rate: controller runs at IMU_GYRO_RATEMAX (default 400 Hz, yaml:63-82) while sensor filters run at kHz; dt clamped to [0.125, 20] ms (MRC.cpp:136). INDI incremental sums are dt-sensitive less than integrators but the filter synchronisation depends on it.
5. Saturation/anti-windup: INDI has no integrator by default, but the incremental accumulator (tau_{k-1}) can wind up when the allocator saturates; the available feedback is the 5 ms-decimated `unallocated_torque` / `torque_setpoint_achieved` (cpp:465-475, 691-693) and the existing flag scheme (MRC.cpp:208-225). Plan to clamp tau_{k-1} to the achieved torque (setpoint - unallocated) and to [-1,1]. Note the `torque_setpoint_achieved` threshold (1e-6 on squared norm) and the 5 ms decimation.
6. Landed/arming: the legacy law only freezes the integrator when landed (rate_control.cpp:81-83) but still outputs P/D torque; INDI incremental accumulation on the ground (ground contact, no real acceleration response) would drift, so reset/hold tau_{k-1} when disarmed (as MRC.cpp:195-198) and when landed/maybe_landed.
7. Initialisation / first-run and filter resets: `ResetFilters` re-seeds filters on any cutoff/sample-rate change (cpp:163-195) causing acceleration glitches; gyro FIFO batching means published acceleration is the last sample only (cpp:845-857).
8. Bias: `xyz` is bias-corrected but `xyz_derivative` is not (cpp:935-941); irrelevant for acceleration (bias constant) but note it.

## Items not verified
- No build or run was done; delays are analytic low-frequency estimates, not measured.
- Real raw gyro rate and publish rate in SITL (gz/jmavsim) not checked; sample-rate selection path in cpp:105-160 depends on `vehicle_imu_status`.
- Numeric relation of normalised torque to physical torque; default CA_METHOD and whether `_metric_allocation` is used for multicopters.
- ESC RPM/feedback usage as actuator measurement (not examined).
- `src/modules/mc_rate_control` has no unit tests of its own; the lib test only has a trivial zero-input test (rate_control_test.cpp:39-44).
- A Bash hook (indi_project/guard.sh) blocked one multi-line command late in the session (a false positive on a heredoc/python edit, unrelated to system administration); the content was written with the Edit tool instead.
