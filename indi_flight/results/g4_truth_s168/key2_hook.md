# G4 truth hook, second-key review (10c741af4b, fc7f74e85a)

File refs: G = src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp (.hpp for header), R = indi_flight/bench/run_scenario.py

1. Truth units/sign/order: PASS (one MINOR).
   - G:293 truth.esc[i].esc_rpm = roundf(_rotor_rpm[i]); _rotor_rpm set at G:314-315 as |joint vel| * SLOWDOWN * 60/2pi, i.e. rpm, abs value.
   - Instance 0 uses the same _rotor_rpm source (G:242, G:259) through erpmTelemetry(), whose output is mechanical rpm (G:350, eRPM/pole_pairs). Same unit, sign (abs) and ordering (rotor_<i>_joint -> index i; esc index i).
   - Truth copies the full esc_status (actuator_function, online flags, count), so index mapping is identical to instance 0.
   - No latency/drop/hold/delay line applied. MINOR: integer rounding to 1 rpm (G:293), against the "no rounding" spec. Negligible (<<0.1% of ~1e3-1e4 rpm) but the truth is int32, not float.
   - MINOR (inherent): the truth is the latest joint_state sample (_rotor_rpm), not a value at the motor_speed callback instant. The comment "at this output instant" (G:289) is slightly overstated; sample age depends on joint_state rate vs the motor_speed rate. If joint_state is slower than ~800 Hz the truth is a zero-order hold. Instance 0's model is fed by the same holds, so the comparison is consistent, but ripple above the joint_state rate cannot be seen. UNVERIFIED: the joint_state publish rate (world/model SDF), not checked.
   - _rotor_rpm_valid false -> truth 0 (same as instance 0 model), fine.

2. Rate/timestamp: PASS.
   - Truth published in the same if-block right after instance 0 (G:284-297), once per motorSpeedCallback. truth is a copy of esc_status, so esc_status.timestamp (G:284, hrt_absolute_time, slaved to the gz clock per G:133 comment) and esc[i].timestamp (G:238) are identical to instance 0. Note instance 0 uses failure_injection::process_esc on a copy; truth is copied before failure injection result (the copy is of the local esc_status, which process_esc takes by const-or-copy; if process_esc mutated in place, truth would inherit it. Evidence: truth built from `esc_status` after the call, G:290. UNVERIFIED whether process_esc mutates its argument; check src/lib/failure_injection/FailureInjection.cpp. Truth rpm and errorcount are overwritten anyway, but esc_online_flags/armed flags could carry injected failures. Not an rpm issue.)

3. Instance 0 and FB 0/1 unchanged: PASS.
   - Instance 0 code path untouched in the diff (only an added block after publish and an added advertise). Advertise and publish of truth are both guarded by _esc_feedback == 2 (G:70, G:288). FB=0/1: no instance 1 advertised; PublicationMulti in .hpp:183 is constructed but never advertised (publish would not run).
   - Minor side effect under FB=2: the mavlink ESC_STATUS/ESC_INFO streams now emit a second ESC set (see 5).

4. Instance determinism: PASS (with caveat).
   - G:68 _esc_status_pub.advertise() precedes G:70-71 _esc_truth_pub.advertise() in the same init(); orb multi advertise takes the next free instance, so 0 then 1.
   - Other publishers of esc_status in simulation: simulator_mavlink (SimulatorMavlink.hpp:220) and simulator_sih (sih.hpp:144), neither started with gz_bridge. No real driver in SITL. Caveat: rely on nothing else (e.g. pwm_out_sim, a fake driver, another gz_bridge instance in the same px4 process) advertising esc_status earlier; none found. Instance numbering also assumes the first advertise in the px4 process is gz_bridge; an early subscriber alone does not claim an instance.
   - Caveat: the Publication (non-multi) uses instance 0 by uORB convention, and the logger runs "esc_status 0 1" which would silently log nothing if instance 1 were absent (see 6).

5. Consumers: PASS (no BLOCKING).
   - McIndiRateControl.hpp:134 uORB::Subscription (instance 0) read at McIndiRateControl.cpp:186. No esc_status use in mc_indi_pos_control; src/lib/indi_rate_control not present / no match.
   - Instance-0-only: VehicleAngularVelocity.hpp:106 (RPM filter), escCheck.hpp:85, EscBattery.hpp:76 (all plain Subscription / callback on instance 0).
   - Multi-instance readers: mavlink streams ESC_STATUS.hpp:61 and ESC_INFO.hpp:61 (SubscriptionMultiArray). MINOR: under FB=2 the GCS link would carry two ESC sets; no flight effect. Logger: logged_topics.cpp:72 (instance 0 at 100 ms profile) unchanged.
   - No loop over ORB_MULTI_MAX_INSTANCES in INDI modules. Not checked exhaustively: other stock modules matched by name in the grep list (fake_imu, voxl_esc, vertiq: not run in gz SITL).

6. Runner logging: UNVERIFIED for the 800 Hz requirement (PASS for syntax/instance).
   - R:294-295 logger_topics.txt keeps "esc_status 0 0" from LOG_TOPICS (R:83) and appends "esc_status 0 1" (format: topic interval instance): interval 0 means every update, instance 1. Correct.
   - Rate achieved depends on (a) the motor_speed topic rate of the gz actuator publisher (not 800 Hz-verified) and (b) logger not dropping samples: esc_status has no uORB queue depth, so the logger can only log what it polls; instance 0 already relied on this, so it carries the same limit. Check offline: median dt of esc_status instance 0 and 1 in the ulog, and that instance 1 count equals instance 0 count. Instance 1 has no ulog entry unless FB=2 is set in the run; a silent absence under FB!=2 is not flagged by the runner (MINOR: no check that FB=2).
   - Comment R:295 labelled S167; fine.

Verdict: No BLOCKING defect; hook gives the true rotor speed on instance 1 consistent with instance 0 and does not change what INDI flies; MINOR items are 1-rpm integer rounding, joint_state sample-and-hold, extra MAVLink ESC set, and unverified logged rate.
