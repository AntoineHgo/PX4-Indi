# Simulator extension audit (s59)

Severity: INVALIDATES / BIASES / NOTE. "suspected" = not traced.

## Wrenches (disturbance.py)
- BIASES (payload_add, com_shift) disturbance.py:76-78,101-103,X500_MASS_KG: payload is a weight force only (no added inertial mass or inertia). Vehicle mass stays 2.06 kg, so payload response is a pure force step, not a heavier vehicle. Documented in RUNNER_NOTES.md:43, but the INDI and PID gain/inertia assumptions differ here from a real payload.
- INVALIDATES (com_shift) disturbance.py:44-46,103: torque (Sy*fz,0,0) is fixed in the WORLD frame while the force and offset belong to the body; at large tilt/yaw it projects on body yaw (already known). Also the offset is world +y, not the body y axis.
- BIASES (gust_x, gust_diag) disturbance.py:25-27,69-71,93-95: drag = C*v_wind*|v_wind| with the WORLD wind velocity, not the air-relative velocity (v_wind - v_vehicle). No aerodynamic damping, so the force does not drop as the vehicle drifts downwind. Fixed CdA (0.06 m^2), independent of attitude. Torque arm r=(0,0,0.05) is world z, not body z (wrong once tilted). Directions are gz ENU (+x = East), not PX4 NED; gust_diag angles are ENU.
- NOTE: wrench is applied on base_link; CoM of base_link is the link origin (inertial has no pose offset in x500_base/model.sdf:8-16), so "at the CoM" holds. The rotor links (mass 0.016 each) sit off-origin, so the system CoM differs by a negligible amount.

## Timing
- OK disturbance.py:183-206: driven by /world/<w>/clock sim time, one-step wrench re-sent every clock message (CSV: 1 ms at 1 kHz physics, 4 ms stock). Not wall-clock. Onset is written by the runner in PX4 sim time; offset 0 (RUNNER_NOTES.md:38).
- BIASES (suspected, run-to-run jitter) disturbance.py:176-181: the wrench travels over gz-transport asynchronously from a Python process, so it is applied at the first physics step after delivery (0-N steps late, depends on host load). In lockstep the sim waits for PX4 but not for this publisher. If two clock messages arrive before one step, the one-step wrench would be summed (ApplyLinkWrench accumulates). This could give a force a multiple of nominal at times (suspected, untraced). CSV logs the commanded value, not the applied one.
- BIASES run_scenario.py:274-292,306-310: setpoints are sent from Python on the sim-time ATTITUDE tick via pump(), but through MAVLink UDP, so the arrival step is jittery with host load. The same applies to sag_tick and set_param (px4-param CLI, run_scenario.py:164, blocks wall time while sim time advances). This is a real non-determinism source for identical seeds. The seed only controls the gz sensor noise (`gz sim --seed`, RUNNER_NOTES.md:9); PX4 baro srand(1234) is fixed; the eRPM drop RNG is a fixed xorshift seed (GZMixingInterfaceESC.hpp _random_state), NOT the run seed: all seeds share the same drop pattern.
- NOTE: _rotor_rpm is written by the gz-transport joint_state thread and read in the motor_speed callback thread, under no fixed order. So the sampled rotor speed at a given esc frame varies by one step run to run (GZMixingInterfaceESC.cpp jointStateCallback / motorSpeedCallback). Another non-determinism source.

## Fault / sag hooks (item 3)
- OK, consistent: both SIM_GZ_THR_SC (GZMixingInterfaceESC.hpp updateParams, sqrt scale at updateOutputs) and the motor_fault MIN/MAX scaling (run_scenario.py:545-552, sqrt) scale the commanded motor SPEED. The plant rotor really spins slower, so the joint-velocity read-back and the eRPM telemetry are consistent with the thrust produced (thrust ~ omega^2). No inconsistency.
- BIASES run_scenario.py:526-541: the sag is a 0.5 s staircase of param sets (each paces on wall time/param latency), not a continuous ramp. NOTE: the scale is applied only to isMotor outputs; in SIM_GZ_ESC_FB=0 (v1) echo mode the esc_rpm reports the COMMAND (actuators.velocity) = not the true rotor speed, and in a fault the echoed value is the scaled command (still consistent), but lags the physical rotor by tau.
- NOTE: the motor_fault changes MIN/MAX of the channel, so the output at fault time can step in command space; the PX4 allocator is unaware, as intended.

## eRPM model vs the real driver (item 4)
- OK GZMixingInterfaceESC.cpp erpmTelemetry: matches dshot.c:899-909 (9-bit mantissa, 3-bit exponent, 65408 cap, /100 rounding) and DShot.cpp rpm=erpm/(pole_count/2) integer division.
- BIASES: latency is a fixed integer number of output frames (+1 frame), computed in the callback of the ESC echo topic (motor_speed), not on a real bidirectional telemetry timeline (reply age within a frame, turnaround: documented as not modelled in sim_fidelity.md). Real quantisation is the same, but the real period is averaged over one electrical revolution (not modelled).
- OK on dropped frame: holds the last value with a fresh timestamp (DShot.cpp:678-701), errorcount incremented, as in the real driver. Not modelled: the real driver sets esc_online_flags off after consecutive drops (the sim keeps online = all). BIASES for the erpm_loss scenario: the INDI loses no "offline" flag signal it may use on hardware (suspected).
- NOTE: publication rate = the actuator echo rate (output rate), esc_status published each callback (GZMixingInterfaceESC.cpp:179-195); real DShot publishes per driver Run. All motors share one timestamp.

## Vibration (item 5)
- BIASES GZBridge.cpp:602-630: generated from rotor speed (1P rotating force + 2P along z, amplitude ~ (rpm/VIB_RPM)^2, phase integrated from sampled rpm). Added AFTER the gz IMU sample at the IMU rate (250 Hz stock, imuCallback), with no anti-alias filter. Hover rotor speed ~ 7300 rpm = 122 Hz: 1P sits at Nyquist (125 Hz) of a 250 Hz IMU, 2P (245 Hz) aliases to ~5 Hz, inside the control bandwidth. At 1 kHz IMU (s8f runs) this does not happen. So the vibration result depends strongly on --imu-rate; real IMUs filter at kHz.
- NOTE: applied to instance 0 only (GZBridge.cpp:659), gyro and accel both, in body FRD after conversion: consistent between sensors, amplitudes are independent (acc m/s^2, gyr rad/s); defaults are 0.0 (module.yaml, SIM_GZ_VIB_*), values come from the runner CLI; no source cited for amplitude values (suspected, check scenarios). SIM_GZ_VIB_RPM 7000 default ~ hover.
- NOTE: the vibration enters only the sensors, not the physics: no true rotor imbalance, so structural coupling is absent.

## model_variant (item 6)
- BIASES model_variant.py:58-63: mass scales only base_link <mass>; rotor links keep 0.016 kg; inertia diagonal terms scaled independently, so a "mass 1.3" variant is 1.3*2.0+4*0.016 (not scaled uniformly), inertia unscaled with mass unless ixx/iyy/izz given too. The PX4 allocator/INDI keeps the nominal mass parameters: intended (mismatch), but report values should say base_link only. Rotor inertia not touched.
- OK model_variant.py:73-87: time constants edited in x500/model.sdf for all 4 rotors (n==8 check). The moment constant and motor constant are NOT scaled (no key), so a "plant mismatch" in km/kf does not exist. A tau variant leaves the INDI onboard motor model (if tau-based) nominal: intended.
- BIASES model_variant.py:103-112 + run_scenario.py:129-133,444: imu_rate edits both the IMU update_rate and the world step (rate-matched), so it changes physics step, motor model integration, clock rate (and the disturbance rate), and the vibration aliasing at once: the factor is confounded, not an isolated IMU change. Also real_time_update_rate set.
- NOTE: JointStatePublisher update_rate 0 = every step (rpm=True), no dynamics effect.

## Ground truth timestamp (item 7)
- BIASES GZBridge.cpp:670-753 (poseInfoCallback): vehicle_local_position_groundtruth, attitude and angular velocity groundtruth use timestamp = hrt_absolute_time() at message RECEPTION (timestamp_sample too), not the pose stamp. In lockstep hrt equals the last clock callback, so it is ahead/behind the pose by up to one clock/transport delay (sub-step jitter, not constant). Anything computing tracking error against ground truth gets 0 to 1 step of time skew (0-4 ms at 250 Hz, velocity error ~ a*dt: small, but nonzero in aggressive manoeuvres). IMU uses the message stamp (min with hrt), so IMU and ground truth are time-skewed against each other by the same amount.
- NOTE: the groundtruth acceleration is a finite difference (suspected, not traced) of velocity with dt clamped (0.001-0.1).

## Not in this audit
- GNSS latency 0 vs SENS_GNSS0_DELAY 110 ms is already known; run_scenario.py:394 has --gnss-delay.
