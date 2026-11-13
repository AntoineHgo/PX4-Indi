# PX4 analysis for INDI integration (read-only code analysis)

Paths are relative to the repo root unless noted. "CA" = `src/modules/control_allocator/ControlAllocator.cpp`,
"hpp" = same dir `.hpp`. Line numbers are from the checkout on branch feat/indi-control.

## 1. Control allocator

### 1.1 Inputs
- Subscribes (as a work-item callback, so the allocator runs once per torque setpoint) to `vehicle_torque_setpoint`
  (hpp:205) and polls `vehicle_thrust_setpoint` (hpp:206). Second instances (index 1) are read for VTOL's second matrix (hpp:208-209).
- Allocation is triggered ONLY by a new torque setpoint (`do_update = true`, CA:383-396). Thrust is latched from its last
  sample and only used when a torque message arrives (CA:398-402). So a controller must publish torque every cycle;
  thrust alone does not run the allocator.
- Non-finite torque components are zeroed (CA:386-391). Thrust NaN -> motors stopped via `stopMotorsBasedOnThrustSetpoint`
  (CA:400) then `nanToZero`.
- Control vector c = [Mx My Mz Fx Fy Fz] (6 axes, CA:416-421). For a multirotor Fz (thrust_z) is negative-up
  (FRD; thrust effectiveness uses `ct*axis`, axis z = -1 for upward rotors).
- `dt` is measured from the previous run and clamped to [0.2 ms, 20 ms] (CA:373).
- Units: torque/thrust setpoints are normalised (mc_rate_control outputs [-1,1] range), NOT N.m. The effectiveness
  matrix is then renormalised so the mix is dimensionless (see 1.2). The topic doc says nothing physical; the
  normalisation is `ControlAllocationPseudoInverse::updateControlAllocationMatrixScale` (src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp:85-152).

### 1.2 Effectiveness matrix for a multirotor
- `ActuatorEffectivenessMultirotor::getEffectivenessMatrix` (src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessMultirotor.cpp:44-56 (addActuators call at :53))
  returns false unless there is an external update (param change / motor activation), then calls `_mc_rotors.addActuators(configuration)`.
  So the matrix is static, rebuilt only on parameter changes (rate-limited to 100 ms, CA:487-490), not from measured rpm.
- `ActuatorEffectivenessRotors::computeEffectivenessMatrix` (VehicleActuatorEffectiveness/ActuatorEffectivenessRotors.cpp:143-232):
  per rotor i, with unit axis `a` (CA_ROTOR{i}_AX/AY/AZ), position `p` (CA_ROTOR{i}_PX/PY/PZ, metres rel. to CoG), `ct`=CA_ROTOR{i}_CT, `km`=CA_ROTOR{i}_KM:
  - `thrust = ct * a` (rows 3-5), `moment = ct * (p x a) - ct * km * a` (rows 0-2) (ActuatorEffectivenessRotors.cpp:194, 197).
  - Rotors with |ct| < eps or bad axis are skipped (cpp:164-181 area).
  - Therefore the matrix B is LINEAR in the normalised motor command u in [0,1]: column i = [ct*(p x a) - ct*km*a ; ct*a].
- Parameter definitions: `CA_ROTOR${i}_CT` default 6.5, doc "Thrust = CT * u^2" (module.yaml:207-220) but the matrix uses it as a
  linear gain (thrust per unit u); `CA_ROTOR${i}_KM` default 0.05, "Torque = KM * Thrust", sign + = CCW (module.yaml:222-236);
  `CA_ROTOR${i}_PX` etc. unit m (module.yaml:139-149). Rows with all |entries| < 0.05 are zeroed (CA:596-606 region, "weak authority").
  Reaction torque from propeller is the `-ct*km*a` term; there is no rotor inertia / gyroscopic / drag term.
- Motors are limited to [0, 1] (reversible: [-1,1] or [-CA_REV_THR_FRAC,...]) (CA:529-536, max = 1 at CA:556).
- `getNormalizeRPY` = true for multirotor (hpp ActuatorEffectivenessMultirotor.hpp:52-55) so roll/pitch share one scale, yaw separate
  (ControlAllocationPseudoInverse.cpp:88-120); thrust axes scaled by mean of |mix| (cpp:128-151).
- Important for INDI: effectiveness-matrix normalisation scales are internal to the allocator; there is NO published copy of
  B or of the scale. An INDI controller that wants physical (N.m) torque increments must carry its own estimate of the
  inertia and control effectiveness, or reproduce `1/scale`.

### 1.3 Allocation method
- `CA_METHOD` (module.yaml:39-50): 0 pseudo-inverse + clipping, 1 pseudo-inverse + sequential desaturation, 2 auto (default).
  Multirotor desires SEQUENTIAL_DESATURATION (ActuatorEffectivenessMultirotor.hpp:47-50); instantiation CA:166-190.
- Both use the same pseudo-inverse `_mix = geninv(B)` (ControlAllocationPseudoInverse.cpp:66-82), `actuator_sp = trim + mix*(c - c_trim)` (cpp:192).
  `dropDependentAxes` (cpp:195ff) drops linearly dependent axes with priority THRUST_Z, ROLL, PITCH, THRUST_X, THRUST_Y, YAW.
- Sequential desaturation (src/lib/control_allocation/control_allocation/ControlAllocationSequentialDesaturation.cpp):
  `allocate()` picks mode by `MC_AIRMODE` (cpp:52-64): 1 = RP airmode (`mixAirmodeRP`, :122), 2 = RPY (`mixAirmodeRPY`, :146), else disabled
  (`mixAirmodeDisabled`). Desaturation shifts all motors along the collective-thrust vector (`desaturateActuators`, :67-86;
  gain from `computeDesaturationGain`, :88-119). Disabled: thrust desaturation increase-only, then roll, then pitch, yaw added last
  (so yaw is sacrificed first). RPY airmode: collective thrust is shifted to fit roll/pitch/yaw, then yaw is desaturated separately, so
  roll/pitch have priority over yaw (:167-170). Priority order: thrust (collective) shift > roll/pitch > yaw.
- Final step: optional slew limit then hard clip to [min,max] (CA:454-458).
- Not an optimisation: no weighting matrix, no torque-vs-thrust trade-off beyond the above shifting.

### 1.4 Outputs
- `actuator_motors.control[i]` normalised [0,1] (NaN = stopped motor) with `timestamp_sample` copied from the torque setpoint
  (CA:745-782, specifically 776); published via `_actuator_motors_pub` (hpp:214). Servos on `actuator_servos`.
- Thrust curve: the allocator does NOT apply THR_MDL_FAC. It is applied downstream in the output driver / mixer_module:
  `THR_MDL_FAC` (src/lib/mixer_module/motor_params.yaml:5-25, model `rel_thrust = f*u^2 + (1-f)*u`) is inverted in
  `FunctionMotors::updateValues` (src/lib/mixer_module/functions/FunctionMotors.hpp:81-100, inverse quadratic) to convert thrust command to signal.
  So `actuator_motors` is in "thrust-linear" space and is mapped to PWM/DShot-signal space after the allocator.
  The effectiveness matrix is therefore linear in thrust command, consistent with `ct*a` above.
  Also `mixer_module.cpp:270` passes `_param_thr_mdl_fac` to the function providers.

### 1.5 Status published back (`control_allocator_status`)
- `publish_control_allocator_status` (CA:~676-740), rate-limited to 5 ms (CA:466-474):
  - `unallocated_torque[3]`, `unallocated_thrust[3]` = control_sp - allocated_control (same normalised units) (CA:~691-702).
  - `torque_setpoint_achieved`, `thrust_setpoint_achieved` flags with threshold norm^2 < 1e-6 (CA:~709-713).
  - `actuator_saturation[16]` per actuator ACTUATOR_SATURATION_UPPER / LOWER, computed from the actuator setpoint vs min/max with eps (CA:~717-729).
  - `handled_motor_failure_mask`, `motor_stop_mask`, preflight-check flag.
- Consumers: mc_rate_control uses it for integrator anti-windup (rate controller reads it; see section 3).
- Note the allocated control is computed from the final clipped actuator setpoint, so unallocated_* includes loss due to clipping;
  it does not include the slew-rate effect separately.

### 1.6 Motor / actuator dynamics model?
- None. No first-order lag, no rpm state, no inverse dynamics in the allocator. Only:
  (a) optional per-actuator slew rate limit params (`CA_R{i}_SLEW`-style, handles read at CA:66-76, applied CA:454-456,
  `ControlAllocation::applySlewRateLimit` ControlAllocation.cpp:111ff), a rate limiter (default off) and
  (b) static THR_MDL_FAC thrust curve downstream (above).
- `RpmControl` exists in VehicleActuatorEffectiveness/ (RpmControl.cpp) for helicopters; not for multirotor.

## 2. Actuator feedback available to a controller

### 2.1 Topics (message definitions)
- `esc_status` (msg/EscStatus.msg): `esc_count`, `esc_online_flags`, `esc_armed_flags`, `EscReport[12] esc` (EscStatus.msg).
  `EscReport` (msg/EscReport.msg): `timestamp`, `int32 esc_rpm` [rpm, signed], `esc_voltage`, `esc_current`, `esc_temperature`,
  `motor_temperature`, `esc_state`, `actuator_function`, `failures`, `esc_power` [%]. Whether each field is filled depends on the driver.
- `actuator_outputs` (msg/ActuatorOutputs.msg:1-8): `output[16]` "in natural output units" (PWM us / DShot value / for gz: rotor velocity command),
  published by `MixingOutput::setAndPublishActuatorOutputs` (src/lib/mixer_module/mixer_module.cpp:533-534, 659-661). It is the post-mixer command, not a measurement.
  `actuator_outputs_sim` carries [-1,1] values for SITL/HITL/SIH (ActuatorOutputs.msg:10-11).
- Real-hardware rpm sources (drivers that fill `esc_rpm`): DShot bidirectional telemetry (src/drivers/dshot/DShot.cpp:793,803, eRPM / (pole_count/2)),
  UAVCAN ESC (src/drivers/uavcan/actuators/esc.cpp:141), TAP_ESC (src/drivers/tap_esc/TAP_ESC.cpp:298), voxl_esc, vertiq, cyphal.
  Existing consumers: gyro dynamic notch filter (src/modules/sensors/vehicle_angular_velocity/VehicleAngularVelocity.cpp:449ff), commander esc check,
  EscBattery. mc_rate_control does NOT subscribe to esc_status (grep of src/modules/mc_rate_control/MulticopterRateControl.* : no match).
  Rate: DShot telemetry is typically tens-hundreds of Hz and decoded rpm is noisy/quantised; not verified for latency here.

### 2.2 Gazebo SITL path (src/modules/simulation/gz_bridge/)
- `GZMixingInterfaceESC::init` (GZMixingInterfaceESC.cpp:36-60) subscribes to `/<model>/command/motor_speed` (cpp:40-43, comment "ESC feedback")
  AND advertises/publishes on the SAME topic `/<model>/command/motor_speed` (cpp:48-51). `updateOutputs` (cpp:62-105) publishes `outputs[i]` as
  `gz::msgs::Actuators.velocity` (cpp:92-103).
- `motorSpeedCallback` (cpp:118-153) builds `esc_status` from that message: `esc[i].esc_rpm = actuators.velocity(i)` (cpp:132), fixed temperature 50 (cpp:133),
  `esc_online_flags` set (cpp:134), armed flags if velocity > 0 (cpp:142), and publishes on `esc_status` (cpp:149, via failure_injection::process_esc).
- CONSEQUENCE (verified in code): in the Gazebo SITL path `esc_status.esc[i].esc_rpm` is an ECHO of the command PX4 itself just sent
  (value in the output range SIM_GZ_EC_MIN..MAX = 150..1000 for x500, ROMFS/px4fmu_common/init.d-posix/airframes/4001_gz_x500:40-47, i.e. "rad/s" as consumed by
  the gz plugin; the field is labelled rpm but carries the commanded rotor velocity, with no unit conversion and no motor lag).
  It is NOT the measured joint velocity of the simulated rotor, so it carries no motor dynamics. Do not use it as actuator state for INDI.
- I found no code in gz_bridge subscribing to a joint-state / per-motor speed topic, and no `motor_speed/<n>` publisher configured in the x500 sdf
  (the gz-sim MulticopterMotorModel plugin source is not in this repo; whether it can publish an actual speed topic could NOT be verified here).
  GZBridge.cpp itself only handles pose/odometry (ground truth, GZBridge.cpp:625-693, 753-778), IMU, etc.
- Other SITL options: SIH publishes `esc_status` with rpm computed from the throttle command `Thruster::throttle_to_rpm(_u[i], max_rpm)`
  (src/modules/simulation/simulator_sih/sih.cpp:527-548). Whether `_u` includes lag was not checked.

### 2.3 x500 motor plugin parameters (Tools/simulation/gz/models/x500/model.sdf:7-80; model x500_base for inertia)
Identical on all four rotors (first plugin block model.sdf:7-23, then three more blocks of the same shape):
| parameter | value |
|---|---|
| plugin | gz-sim-multicopter-motor-model-system `gz::sim::systems::MulticopterMotorModel` |
| motorType | velocity |
| timeConstantUp | 0.0125 s |
| timeConstantDown | 0.025 s |
| maxRotVelocity | 1000.0 rad/s |
| motorConstant | 8.54858e-06 (thrust = motorConstant * w^2, N, rad/s) |
| momentConstant | 0.016 (reaction torque = momentConstant * thrust) |
| rotorDragCoefficient | 8.06428e-05 |
| rollingMomentCoefficient | 1e-06 |
| rotorVelocitySlowdownSim | 10 (visual only) |
| turning directions | rotor_0, rotor_1 ccw; rotor_2, rotor_3 cw |
- Vehicle: mass 2.0 kg, Ixx=Iyy=0.0216667, Izz=0.04 kg.m2 (Tools/simulation/gz/models/x500_base/model.sdf:9-16). Rotor link inertia (spin axis ~2.6e-5 kg.m2) at x500_base/model.sdf:321-325.
- First-order model: tau_up = 12.5 ms, tau_down = 25 ms (asymmetric; a unified onboard model could use tau ~ 12.5-25 ms, i.e. pole 40-80 rad/s).
  The up/down switching and the exact discretisation are plugin internals (not verified in-repo).
- PX4 side for the same airframe (ROMFS/px4fmu_common/init.d-posix/airframes/4001_gz_x500): CA_ROTOR_COUNT 4 (line 17), rotor positions +-0.174 m (lines 19-33),
  CA_ROTOR*_KM = +-0.05 (lines 21,25,29,33), MPC_THR_HOVER 0.6 (line 50), CA_ROTOR*_CT left at default 6.5 (not set in the file),
  THR_MDL_FAC NOT set for x500 (=0 default; set only for 4006_gz_px4vision = 0.3 and 10044_sihsim_hex = 1).
- Mismatches worth knowing for INDI model-based terms: gz momentConstant 0.016 vs PX4 CA_ROTOR_KM 0.05 (yaw effectiveness differs);
  thrust is quadratic in w in gz and w is linear in u with THR_MDL_FAC=0, so true thrust ~ u^2-like while the allocator assumes linear.
  Both are plugin/param observations; the allocator sees them as model error.

## 3. How alternative controllers integrate and are selected

Paths below relative to repo root.

### 3.1 The standard (PID) chain, which must stay untouched
- Startup: ROMFS/px4fmu_common/init.d/rc.mc_apps:11 `control_allocator start`, :16 `mc_rate_control start`, :21 `mc_att_control start`, then pos control etc.
  VTOL variant: ROMFS/px4fmu_common/init.d/rc.vtol_apps:17 `mc_rate_control start vtol` (publishes the `_virtual_mc` topic variants,
  src/modules/mc_rate_control/MulticopterRateControl.cpp:51-52, 313-321).
- `MulticopterRateControl` (src/modules/mc_rate_control/MulticopterRateControl.cpp) is a WorkItem triggered by `vehicle_angular_velocity` (hpp:109). Per cycle:
  - rates = `angular_velocity.xyz`, angular acceleration = `angular_velocity.xyz_derivative` (cpp:~137-139). That field is produced in
    `VehicleAngularVelocity` as a differentiated gyro, low-passed at `IMU_DGYRO_CUTOFF` (src/modules/sensors/vehicle_angular_velocity/VehicleAngularVelocity.cpp:184, 777-782, copied at :942).
    An INDI controller can reuse this signal (already filtered, same filter as the D-term).
  - runs only if `vehicle_control_mode.flag_control_rates_enabled` (cpp:192); resets integrators when disarmed (cpp:195-198).
  - reads `control_allocator_status` and converts `torque_setpoint_achieved` / `unallocated_torque` sign into per-axis positive/negative saturation booleans
    for anti-windup (cpp:~201-224, with a TODO "send the unallocated value directly for better anti-windup" at cpp:223).
  - torque = `_rate_control.update(rates, rates_sp, angular_accel, dt, landed)` (cpp:229), gain compression, yaw low-pass,
    publishes `rate_ctrl_status`, then `vehicle_thrust_setpoint` / `vehicle_torque_setpoint` (normalised, optional battery scaling MC_BAT_SCALE_EN; cpp:~238-285).
  - PID core is a library: src/lib/rate_control/rate_control.{hpp,cpp} (`RateControl::update`, rate_control.hpp:96) with a unit test rate_control_test.cpp.
- Build flag `MODULES_MC_RATE_CONTROL` in the board files (boards/px4/sitl/default.px4board:45, boards/px4/fmu-v6x/default.px4board:77);
  Kconfig at src/modules/mc_rate_control/Kconfig (default n); CMake `px4_add_module` with `MODULE_CONFIG mc_acro_params.yaml mc_rate_control_params.yaml`, DEPENDS RateControl (src/modules/mc_rate_control/CMakeLists.txt).

### 3.2 mc_nn_control and mc_raptor (both present in this tree)
Both replace the whole chain (including attitude/position and the allocator) by being a separate external flight mode with direct actuator control:
- They publish `actuator_motors` directly (mc_nn_control.hpp:147, mc_nn_control.cpp:533; mc_raptor.hpp:155), plus debug topics (`neural_control`; `raptor_status`, `raptor_input`).
  They do not publish torque/thrust setpoints.
- Mode registration: `register_ext_component_request` (mc_nn_control.cpp:290-297: name "Neural Control", `register_mode = true`, `register_arming_check = true`;
  mc_raptor.cpp:260-263 with optional `enable_replace_internal_mode` for OFFBOARD via `MC_RAPTOR_OFFB`, module.yaml:22-29).
  When their mode is the active nav_state they publish `setpoint_config` with `TYPE_DIRECT_ACTUATORS` (mc_nn_control.cpp:316-321; mc_raptor.cpp:521-529).
- How mc_rate_control and the allocator are kept from also publishing: commander maps `SetpointType::DirectActuators` to "Nothing enabled"
  (src/modules/commander/ModeUtil/setpoint_types.cpp, `case SetpointType::DirectActuators`, all control-mode flags stay false).
  So `flag_control_rates_enabled = false` stops mc_rate_control (MulticopterRateControl.cpp:192) and `flag_control_allocation_enabled = false` makes the allocator
  stop publishing `actuator_motors` (`_publish_controls`, ControlAllocator.cpp:363-368, 747-749). The exclusion is therefore via vehicle_control_mode flags
  driven by the active mode, not by a parameter checked inside mc_rate_control.
- Startup: ROMFS/px4fmu_common/init.d/rc.mc_apps:49-52 `if param compare -s MC_NN_EN 1 ... mc_nn_control start`; :55-58 `if param compare -s MC_RAPTOR_ENABLE 1 ... mc_raptor start`.
  Params: src/modules/mc_nn_control/mc_nn_control_params.yaml (MC_NN_EN), src/modules/mc_raptor/module.yaml (MC_RAPTOR_ENABLE, MC_RAPTOR_OFFB).
- Registration: Kconfig `MODULES_MC_NN_CONTROL` / `MODULES_MC_RAPTOR`, default n (src/modules/mc_nn_control/Kconfig, src/modules/mc_raptor/Kconfig);
  enabled only in dedicated SITL board variants (boards/px4/sitl/neural.px4board:40, boards/px4/sitl/raptor.px4board:54; both also set MODULES_MC_RATE_CONTROL=y at :42 / :55).
  Each has `px4_add_module(MODULE ... MODULE_CONFIG <params yaml>)` (mc_nn_control/CMakeLists.txt).
- Fit for INDI: poor. These patterns require the user to switch into a special flight mode, bypass the allocator and the standard modes, and (nn) pull in TFLite.
  INDI should act inside Stabilized/Position/Mission etc. as the rate loop, so do not copy the external-mode registration.

### 3.3 Cleanest existing pattern for "INDI selectable at runtime by param, PID path untouched and default"
A) Runtime algorithm switch by an enum parameter inside the owning module (best match for "runtime by param").
   Precedent: `CA_METHOD` (src/modules/control_allocator/module.yaml:39-50, enum, default 2) read by `ControlAllocator::update_allocation_method`
   (ControlAllocator.cpp:138-200), which deletes and re-creates the algorithm object when the param changes (`_allocation_method_id != configured_method`, :149; switch at :180-190).
   Applied to mc_rate_control: add an enum param (e.g. `MC_RATE_CTRL_TYPE`: 0 = PID default, 1 = INDI) to src/modules/mc_rate_control/mc_rate_control_params.yaml, and at
   MulticopterRateControl.cpp:228-229 call an INDI object's update instead of `_rate_control.update(...)` when selected. Everything around it (subscriptions, control-mode gating :192,
   saturation read :201-224, thrust/torque publication, `rate_ctrl_status`, battery scaling, vtol topic variants) is reused, and with default 0 the PID path is unchanged (new code behind one branch).
   Put the INDI core in a new library next to src/lib/rate_control (own CMake + gtest, like rate_control_test.cpp).
   Pros: no rc-script change, no second publisher of `vehicle_torque_setpoint`, vtol path covered, switchable on a live system (reset INDI state on param change, like `parameters_updated()`, cpp:57).
   Cons: touches MulticopterRateControl.{hpp,cpp} slightly; INDI's extra subscriptions (actuator state) are added there.
B) Separate module chosen at start-up by an rc script `if param compare`, as rc.mc_apps:49-58 does for NN/Raptor: replace `mc_rate_control start` (rc.mc_apps:16, rc.vtol_apps:17)
   by an if/else starting either `mc_rate_control` or a new `mc_indi_rate_control`. The two must be mutually exclusive (both publish `vehicle_torque_setpoint`).
   Selection only takes effect when the stack is restarted, and each board needs the new module's Kconfig `MODULES_*` (default n, as in mc_rate_control/Kconfig) enabled in its .px4board file.
   Leaves the PID source untouched, which is good for upstream-merge hygiene, but duplicates module scaffolding.
Avoid: the external-mode DirectActuators pattern of mc_nn_control / mc_raptor (3.2).
Param pattern: a `*_params.yaml` listed in `MODULE_CONFIG`, read via `ModuleParams` / `DEFINE_PARAMETERS` (MulticopterRateControl.hpp:140ff, `ParamFloat<px4::params::...>`).

## 4. Implications for INDI

### 4.1 Torque-space increments ahead of the allocator (INDI output on `vehicle_torque_setpoint`)
- INDI law: tau_cmd = tau_prev + G^-1 (nu - alpha_filt), nu = desired angular acceleration, alpha_filt = filtered measured angular acceleration.
  Needs: (a) angular acceleration, already in `vehicle_angular_velocity.xyz_derivative` (low-passed with IMU_DGYRO_CUTOFF); (b) control effectiveness / inertia to convert rad/s^2 to
  the allocator's DIMENSIONLESS normalised torque units (see 1.1, 1.2; the allocator rescales internally and the scale is not published); (c) tau_prev time-aligned with the filtered acceleration
  (apply the same filter and delay to tau_prev, the known INDI synchronisation requirement).
- Nothing new is needed from the allocator: output stays on `vehicle_torque_setpoint` / `vehicle_thrust_setpoint` (works with option A or B, and the vtol virtual topics).
- Saturation: the allocator clips and desaturates (shifts collective thrust, sacrifices yaw first; ControlAllocationSequentialDesaturation.cpp:122-170), so the torque actually produced can differ from tau_prev.
  Use "allocated torque" = setpoint - `unallocated_torque` as tau_prev (status published every 5 ms, ControlAllocator.cpp:466-474; computed at :666-690), better than mc_rate_control's sign-only use (TODO at MulticopterRateControl.cpp:223).
- The normalised-torque-to-physical mapping depends on `updateControlAllocationMatrixScale` (ControlAllocationPseudoInverse.cpp:85-152) and CA_ROTOR*_CT/KM/PX/PY, so G must be identified per airframe
  (e.g. from SITL steps) or recomputed from those params.
- Allocator rate: runs once per torque setpoint (ControlAllocator.cpp:383-396), i.e. at rate-controller rate; no extra latency apart from the output stage.

### 4.2 Actuator-space increments (u = u_prev + B^+ (nu - alpha))
- Needs `actuator_motors` as base and B in physical units. Either bypass the allocator (publish `actuator_motors` directly, needing `flag_control_allocation_enabled=false`, i.e. the external-mode path of 3.2,
  which loses the standard flight modes) or add a new allocator input. `ControlAllocator` has none; it would need a new subscription that skips `allocate()` / desaturation and writes `_actuator_sp`
  (public in ControlAllocation, `setActuatorSetpoint` at ControlAllocation.cpp:67-75). Invasive.
- Gains: saturation handled naturally (u_prev clipped to [0,1]), per-motor failure handling, can use measured motor speed for a true incremental law.
- Costs: needs own copy of B (computable from CA_ROTOR* with the formula in 1.2) and loses the allocator's prioritisation (collective thrust > roll/pitch > yaw) unless re-implemented.
- Suggestion: torque-space first (option A); actuator-space only as a later research branch.

### 4.3 Where actuator state could come from
- SITL Gazebo (verified, 2.2): `esc_status.esc[i].esc_rpm` is the echoed command (GZMixingInterfaceESC.cpp:132), no dynamics; `actuator_outputs` is also a command. So an onboard first-order
  estimator is needed: omega_hat' = (omega_cmd - omega_hat)/tau with tau_up 0.0125 s and tau_down 0.025 s (x500 model.sdf, 2.3), driven by `actuator_motors` through the output mapping
  (THR_MDL_FAC = 0 for x500, SIM_GZ_EC_MIN/MAX = 150..1000, 4001_gz_x500:40-47; the linear map from u to omega is my reading of the mixer, not separately verified; in gz thrust ~ omega^2).
  Alternative: bridge a real rotor speed from gz into `esc_status`; I could not verify that the plugin offers such a topic, so it may need a gz-side change.
- Real hardware: DShot bidirectional telemetry `esc_rpm` (DShot.cpp:793,803), UAVCAN / Cyphal ESC rpm; otherwise the same first-order model with an identified tau.
- Design suggestion: a small actuator-model class inside the INDI library with tau_up/tau_down parameters, fed by `actuator_motors`; optionally replace its state by `esc_status` rpm when that is real
  (the gz echo must be excluded explicitly).

### 4.4 How saturation info flows back
- Existing path: allocator -> `control_allocator_status` (`unallocated_torque/thrust`, `torque_setpoint_achieved`, `actuator_saturation[]`, every >= 5 ms) -> controller (mc_rate_control already subscribes, hpp:100).
  INDI can use the same subscription with no PX4 change: (1) stop integrating the increment on axes with same-direction unallocated torque, (2) set tau_prev to the allocated value, (3) per-motor
  `actuator_saturation` flags for actuator-space INDI.
- Caveats: status can be up to one allocation old; with airmode the allocator keeps torque by moving collective thrust, so `unallocated_thrust` must be checked too; status reports static saturation only,
  not slew or motor lag effects.

### 4.5 Not verified
- Source of the gz-sim MulticopterMotorModel plugin (time-constant discretisation, any published speed topic): not in this repo.
- Whether SIH's `_u` (sih.cpp:548) already includes lag.
- Only the SITL x500 airframe and default board files were inspected, not any specific user board.
- Line numbers prefixed with "~" were read from section output rather than dedicated greps and may be off by a few lines.

