# s8 design verification (source reading only, no build/flight)

Paths relative to repo root. "UNVERIFIED" = not confirmed from code.

## Q1. mc_raptor external-mode registration and setpoint reception

Registration (src/modules/mc_raptor/mc_raptor.cpp:254-264):
- `register_ext_component_request.name` = "RAPTOR" (char[25], msg/versioned/RegisterExtComponentRequest.msg:8)
- `request_id`, `px4_ros2_api_version = LATEST_PX4_ROS2_API_VERSION` - `register_arming_check = true`, `register_mode = true` (:259-260) - `enable_replace_internal_mode = _param_mc_raptor_offboard.get()`, `replace_internal_mode = NAVIGATION_STATE_OFFBOARD` (:261-262)
- `request_offboard_setpoints = true` (:263), published via `_register_ext_component_request_pub` (:264)
- It also answers `arming_check_request` with `arming_check_reply` (mc_raptor.cpp:438) and unregisters on exit (:452-456); a new
  module must do the same (reply field requirements: UNVERIFIED).
Commander side (src/modules/commander/ModeManagement.cpp:337-344): `mode.replaces_nav_state = request.replace_internal_mode`
(only if enable_replace_internal_mode), `mode.request_offboard_setpoints = request.request_offboard_setpoints`.
`currentModeAcceptsOffboardSetpoints()` returns that flag for the active external mode (ModeManagement.cpp:768-778) and
Commander copies it into `vehicle_status.accepts_offboard_setpoints` (Commander.cpp:2187).
Setpoint reception: YES, trajectory_setpoint is delivered when request_offboard_setpoints is true, but only via MAVLink.
src/modules/mavlink/mavlink_receiver.cpp:1340-1343: `if (vehicle_status.accepts_offboard_setpoints) { ... _trajectory_setpoint_pub.publish(setpoint); }`
(SET_POSITION_TARGET_LOCAL_NED handler; requires ocm.position||velocity||acceleration, :1333). The mavlink handler also publishes
offboard_control_mode (:1335-1337). mc_raptor just subscribes `trajectory_setpoint` (mc_raptor.hpp:151) and reads it with
`_trajectory_setpoint_sub.update(...)` after an isfinite check on position, velocity, yaw, yawspeed (mc_raptor.cpp:572-585).
MAVLink mapping (mavlink_receiver.cpp ~1270-1321): position, velocity and acceleration are copied unless the type_mask ignores them
(ignored -> NaN, e.g. `matrix::Vector3f(NAN,NAN,NAN).copyTo(setpoint.acceleration)`); acceleration goes through `R * acceleration_body_sp`
(frame rotation, check frame handling when speccing a_ref); yaw/yawspeed likewise (:1319-1320 region). No jerk is written there (see Q5).
mc_raptor publishes (mc_raptor.hpp:155-162): `actuator_motors` (:893), `raptor_status`, `raptor_input`, `tune_control`,
`register_ext_component_request`, `unregister_ext_component`, `setpoint_config` (:526-531, TYPE_DIRECT_ACTUATORS, source_id =
ext mode id, should_apply = true, sent on the inactive->active edge of `vehicle_status.nav_state == ext_component_mode_id`, :522-531),
`arming_check_reply`.
mc_raptor does NOT publish vehicle_rates_setpoint; our module publishes TYPE_RATES instead (see Q2).
## Q2. Control-mode flags for an external mode publishing vehicle_rates_setpoint

Mechanism: external mode publishes `setpoint_config` (msg/versioned/SetpointConfig.msg: `type`, `source_id` = nav_state of mode,
`should_apply`, `timeout_ms`; `TYPE_RATES = 5 # VehicleRatesSetpoint`). Commander (ModeManagement.cpp:658-690,
`checkConfigControlSetpointUpdates`) validates with `isSetpointTypeValid`, then if `should_apply` stores `mode.current_setpoint_type`
(:686) and answers `setpoint_config_reply`. In-tree name of the "config_control_setpoint" is the local `vehicle_control_mode_s
config_control_setpoint` filled by `mode_util::getControlMode(setpoint_type, ...)` (:673-674).
Then Commander.cpp:2820-2823 calls `mode_util::getVehicleControlMode(nav_state, ..., external_mode_setpoint_type)`;
control_mode.cpp:155-156: `case NAVIGATION_STATE_EXTERNAL1 ... EXTERNAL8: getControlMode(external_mode_setpoint_type, vehicle_control_mode)`.
OFFBOARD replacement via `replaces_nav_state` (ModeManagement.cpp:337): mapping logic not read, UNVERIFIED.

Flags for TYPE_RATES (src/modules/commander/ModeUtil/setpoint_types.cpp:85-88): `flag_control_allocation_enabled = true; flag_control_rates_enabled = true;` and nothing else (attitude/altitude/velocity/position/climb_rate all false; manual false for external).
Commander.cpp:2826-2831: `flag_multicopter_position_control_enabled` = rotary wing && (altitude || climb_rate || position || velocity) -> false.
Published in `vehicle_control_mode` (Commander.cpp:2832-2833).

Consumers:
- mc_pos_control: all work is gated on `_vehicle_control_mode.flag_multicopter_position_control_enabled`
  (MulticopterPositionControl.cpp:448, :458); its only attitude publish is at :643 (`_vehicle_attitude_setpoint_pub`, topic
  vehicle_attitude_setpoint) inside that gated path -> stops publishing. (I did not read every line between :458 and :643: the
  publish at :643 being inside the gate is inferred from the `if` at :458; UNVERIFIED in detail.)
- mc_att_control: `run_att_ctrl = flag_control_attitude_enabled && (is_hovering || ...)` (mc_att_control_main.cpp:307-308) -> false,
  so it does not publish vehicle_rates_setpoint (that publish is at :382-386 inside the run_att_ctrl block).
- rate controller (stock and INDI): `if (_vehicle_control_mode.flag_control_rates_enabled)` (MulticopterRateControl.cpp:192,
  McIndiRateControl.cpp:295) -> still runs. Its setpoint input: with manual false, the branch at McIndiRateControl.cpp:287
  `else if (_vehicle_rates_setpoint_sub.update(&vehicle_rates_setpoint))` reads roll/pitch/yaw (NaN replaced by measured rate,
  :288-290) and `thrust_body` (:291). Same structure in stock (MulticopterRateControl.cpp:159 manual branch, else rates sub).
  So fields to publish: vehicle_rates_setpoint {timestamp, roll, pitch, yaw, thrust_body[3]}.

## Q3. Accelerometer source

- `vehicle_acceleration` (msg/VehicleAcceleration.msg): `timestamp`, `timestamp_sample`, `xyz` = "Bias corrected acceleration (including
  gravity) in the FRD body frame". It IS low-pass filtered: VehicleAcceleration.cpp:247-248
  `accel_corrected = _calibration.Correct(accel_raw) - _bias; accel_filtered = _lp_filter.apply(accel_corrected)`, published at :257-259
  from the filtered value. Filter: `math::LowPassFilter2p<Vector3f>` (VehicleAcceleration.hpp:98), cutoff `IMU_ACCEL_CUTOFF`
  (:125-126; imu_accel_parameters.yaml:5-12: "2nd order butterworth ... only affects the signal sent to the controllers", default 30 Hz). `_bias` = EKF `estimator_sensor_bias.accel_bias`
  (:142-147). Input is `sensor_accel` (per-sample), not vehicle_imu.
  IMU_ACCEL_CUTOFF=0 would disable it, but that is a global parameter.
- `sensor_combined` (msg/SensorCombined.msg): `accelerometer_m_s2` "average value acceleration measured in the FRD body frame ... over the
  last accelerometer sampling period", `accelerometer_integral_dt`, `accelerometer_timestamp_relative`, `accelerometer_clipping`.
  Built in voted_sensors_update.cpp:188-201 from `vehicle_imu`: `accel_data = delta_velocity * 1e6/delta_velocity_dt`; no LPF.
  Published by `sensors` (sensors.cpp:565-571). Voted primary IMU only (:262).
- `vehicle_imu` (msg/versioned/VehicleImu.msg): `delta_velocity[3]` [m/s over delta_velocity_dt, FRD], `delta_velocity_dt`,
  `delta_velocity_clipping`, `accel_calibration_count`. Calibrated and bias-corrected in VehicleIMU.cpp:569 (`_accel_calibration.Correct(...)`),
  with learned EKF bias offset applied when `accel_bias_valid && accel_bias_stable` and device id matches (VehicleIMU.cpp:791-805),
  published at :658. No low-pass filter. Publish rate (IMU_INTEG_RATE): UNVERIFIED.
- Answer: specific force in body FRD, calibrated + EKF-bias-corrected, with NO low-pass: `sensor_combined.accelerometer_m_s2`
  (or `vehicle_imu.delta_velocity / delta_velocity_dt`, same numbers, per IMU instance). Both are only averaged over the integration
  window (a boxcar, ~ integration period), and the bias term is only applied when the EKF bias is flagged valid and stable
  (otherwise static calibration only). `vehicle_acceleration` is the only one with the Butterworth stage, so unsuitable for matched filtering.
- Design sec. 6.2 is consistent: calibrated source plus our own LPF; gravity is included (specific force), so adding g e_z is right.
  Sample-to-publish delay: UNVERIFIED.

## Q4. mc_indi_rate_control: measured torque vs measured collective thrust

- Only torque is computed. IndiMeasuredTorque::Result (IndiMeasuredTorque.hpp:~85-91) = `torque[3]`, `timestamp_sample`,
  `motor_valid_mask`, `valid`. `compute()` builds the actuator vector u (`actuator(motor) = sample.u`, IndiMeasuredTorque.cpp ~:145)
  and returns `result.torque[i] = control(i)` (:~163) from the control allocation (`getControlFromActuators`): roll/pitch/yaw only.
  grep for collective/thrust_measured/mean_u in src/modules/mc_indi_rate_control and src/lib/indi_rate_control: no hits.
  => A measured collective thrust does NOT exist; Design sec. 6.3 answer: mean u must be computed by the new module itself.
- Message `actuator_torque_measured` (msg/ActuatorTorqueMeasured.msg): `timestamp`, `timestamp_sample`, `float32[3] torque`,
  `bool valid`, `uint8 motor_valid_mask`. NO per-motor u_i and NO thrust field is published. Per-motor u_i exists only inside
  `IndiMeasuredTorque::Sample.u` (private, IndiMeasuredTorque.hpp `struct Sample`, `u = (omega/omega_max)^2` clamped [0,1]).
  Raw source for the new module: `esc_status.esc[j].esc_rpm`, `esc_report_s.actuator_function - ACTUATOR_FUNCTION_MOTOR1` as motor index,
  `esc_errorcount`, `esc_online_flags` (McIndiRateControl.cpp:141-163 shows the exact read pattern). `MC_INDI_W_MAX` (-> setRotorSpeedMax
  in rad/s; the msg comment says CA_R_W_MAX, name differs: check which param feeds it, McIndiRateControl.cpp:~109 uses `_param_mc_indi_w_max`).
- Reusable helper: `IndiRateControl::normalisedThrustFromRpm(rpm, rpm_max, u)` is a public static in src/lib/indi_rate_control/indi_rate_control.hpp:~166
  (same formula, same plausibility checks, returns false for non-finite/implausible). Note it takes rpm and rpm_max "same unit"
  while IndiMeasuredTorque converts rpm to rad/s first (IndiMeasuredTorque.cpp ~:116 "omega = rpm * 2 pi / 60").
- Filter and delay in the INDI rate library `IndiRateControl` (src/lib/indi_rate_control/, CMake target `IndiRateControl`,
  `target_link_libraries(IndiRateControl PRIVATE mathlib)`, include dir PUBLIC): measurement path = `math::LowPassFilter2p<float> _meas_lpf[3]`
  + `AlphaFilter<float> _meas_alpha[3]` (indi_rate_control.hpp:304-305), preceded by a pure delay ring buffer `_meas_delay_buffer`
  (`Vector3f`, 3 axes, :301-303), delay `MC_INDI_ERPM_DLY` = `setMeasurementDelaySamples` (:145-147), clamped [0, kMaxDelaySamples = 4],
  default 1 cycle (mc_indi_rate_control_params.yaml: MC_INDI_ERPM_DLY, int32, default 1, 0..4). The LPF cut-offs are IMU_GYRO_CUTOFF
  (and IMU_DGYRO_CUTOFF for the alpha), read at McIndiRateControl.cpp:96-107 (`setFilterCutoffs`).
  These members are private and hard-wired to 3-axis torque, in controller cycles (rate loop rate, not the outer loop rate).
  => A new module cannot reuse them as is. What it CAN reuse: the stock mathlib classes `math::LowPassFilter2p<T>` and
  `AlphaFilter<T>` (src/lib/mathlib/math/filter/, headers included at indi_rate_control.hpp:74-75; linked via `mathlib`), and the
  static `normalisedThrustFromRpm`. The delay buffer would have to be re-implemented (small ring buffer) in the new module, or the
  IndiRateControl class generalised (touching the module/lib that the design wants untouched).
- Linking: `IndiMeasuredTorque` is a separate static library target in src/modules/mc_indi_rate_control/CMakeLists.txt:34-39
  (`px4_add_library(IndiMeasuredTorque ...)`, `target_link_libraries(... PUBLIC ControlAllocation mathlib)`, include dirs PUBLIC).
  Its CMake declaration lives under the module directory, but being a regular px4 library target a new module can list it in
  `DEPENDS` (UNVERIFIED: not built; the target exists only when CONFIG_MODULES_MC_INDI_RATE_CONTROL is on). It only gives torque anyway.

## Q5. trajectory_setpoint fields; ControlMath and AttitudeControl libraries

- msg/versioned/TrajectorySetpoint.msg (the only copy; msg/TrajectorySetpoint.msg does not exist): `MESSAGE_VERSION = 0`, `timestamp`,
  `float32[3] position # in meters`, `velocity # in meters/second`, `acceleration # in meters/second^2`,
  `float32[3] jerk # in meters/second^3 (for logging only)` (:14), `float32 yaw # euler angle ... -PI..+PI`, `yawspeed # angular velocity
  around NED frame z-axis` (:16-17). Header comment: "NED local world frame ... setting a value to NaN means the state should not be controlled".
  So jerk is present, documented "for logging only" (matches design sec. 3). mc_pos_control does not consume it (grep for jerk in
  mc_pos_control: only MPC_JERK_* params, never trajectory_setpoint.jerk); MAVLink SET_POSITION_TARGET_LOCAL_NED handler never writes
  it (no `jerk` in mavlink_receiver.cpp, see Q1), so over MAVLink jerk is whatever the zero-initialised struct holds (likely 0, not NaN:
  UNVERIFIED, depends on struct init in the handler). The design's rule "use jerk when finite and non-zero, else backward difference"
  handles both.
- ControlMath: `limitTilt(Vector3f &body_unit, const Vector3f &world_unit, float max_angle)` and
  `bodyzToAttitude(Vector3f body_z, float yaw_sp, vehicle_attitude_setpoint_s &att_sp)` are free functions in namespace ControlMath,
  src/modules/mc_pos_control/PositionControl/ControlMath.{hpp,cpp} (hpp:62, :70; cpp:53, :71). `body_z` is "a world frame 3D vector in
  direction of the desired body z axis" (mc_pos_control calls it with `-thr_sp`, ControlMath.cpp:49), output is the full
  `vehicle_attitude_setpoint_s` (use `.q_d`); zero vector falls back to level (cpp:73-75).
  CMake target: `PositionControl` (src/modules/mc_pos_control/PositionControl/CMakeLists.txt:34-40: ControlMath.cpp + PositionControl.cpp,
  `target_include_directories(PositionControl PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})`, no target_link_libraries). A new module adds
  `PositionControl` to DEPENDS and includes `<ControlMath.hpp>`; no change to mc_pos_control CMake needed. Caveats: (a) the target is
  only defined when mc_pos_control is built (add_subdirectory inside mc_pos_control/CMakeLists.txt:34-36; SITL default enables it,
  boards/px4/sitl/default.px4board:45), so the Kconfig of the new module should `depends on MODULES_MC_POS_CONTROL` (UNVERIFIED: whether
  px4_add_module DEPENDS across module dirs is order-sensitive in this tree: mc_raptor/mc_nn_control precedent not checked);
  (b) linking `PositionControl` also pulls in PositionControl.cpp (UNVERIFIED which libs it needs, e.g. controllib; mc_pos_control lists
  `controllib` in DEPENDS), though the target itself declares none.
- AttitudeControl: target `AttitudeControl` (src/modules/mc_att_control/AttitudeControl/CMakeLists.txt:34-40: AttitudeControl.cpp,
  AttitudeControl.hpp, AttitudeControlMath.hpp, PUBLIC include dir; added by mc_att_control/CMakeLists.txt:34 and listed in its DEPENDS :47).
  Same linking pattern as above. A second copy `AttitudeControlLibrary` exists for spacecraft (not relevant). API
  (AttitudeControl.hpp:65-103): `setProportionalGain(Vector3f, yaw_weight)`, `setRateLimit(Vector3f)`,
  `bool setAttitudeSetpoint(const Quatf &qd, float yawspeed_setpoint, float dt = -1.f)`, `Vector3f update(const Quatf &q) const` -> rate
  setpoint. NOTE: this tree's AttitudeControl has a 2nd-order reference model (`_q_ref`, `propagateReferenceModel`, :108-123), so the
  rate it returns is not the plain `Kp * qerr + yawspeed_ff`; it is the reference-model-based output. Only yawspeed is a feedforward
  argument: Omega_ref (roll/pitch from jerk, design sec. 2 step 6) has to be added by the caller after `update()`.
  (Model details and dt=-1 behaviour: UNVERIFIED, read AttitudeControl.cpp before specifying step 6.)
## Verdict
Sec. 3 TYPE_RATES confirmed (Q2); offboard trajectory_setpoint confirmed but MAVLink-only (Q1); use sensor_combined/vehicle_imu accel (Q3);
no measured collective thrust exists, compute mean u from esc_status and own the delay buffer (Q4); ControlMath/AttitudeControl link as is (Q5).
