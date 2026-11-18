# S122: why actuator_torque_measured is empty in g3_refly_s121/run_021

Cause: MC_INDI_W_MAX = 0 in the log (default 0, mc_indi_rate_control_params.yaml:28), so
IndiMeasuredTorque::enabled() is false (`_omega_max > 0.f && _num_rotors > 0`, IndiMeasuredTorque.hpp:99).
McIndiRateControl::updateMeasuredTorque() returns at McIndiRateControl.cpp:164-166 BEFORE
`_actuator_torque_measured_pub.publish(msg)` (line 216), so the topic is never published, not just unlogged.

Logging path is fine: logged_topics.cpp:51 add_optional_topic("actuator_torque_measured") and
indi_flight/bench/run_scenario.py:89 requests it in the runner topic list. esc_status (750 Hz) is present but unused.

Gating params in run_021 initial_parameters:
- MC_INDI_EN 1, MC_INDI_W_MAX 0.0 (the gate), CA_ROTOR_COUNT 4, CA_AIRFRAME 0
- MC_INDI_ERPM_DLY 1, MC_INDI_ERPM_FRZ 0.5, MC_INDI_ERPM_TO 0.02
- SDLOG_PROFILE 17

Measured path active? No. indi_rate_status.measured_torque_in_use: 66225 samples, mean 0.0 (never set).
The controller used its actuator model for the whole flight (setMeasuredTorque gets valid=false, cpp:232-237).

Minimal fix (not applied): set MC_INDI_W_MAX to the sim rotor speed at thrust 1.0 (rad/s) in the runner/g3 param
set, e.g. in indi_flight/bench/g3_run.py or run_scenario.py params, from the gz model (maxRotVelocity of the
motor model; see indi_flight/design/ref_airframe_data.md). No C++ change needed.
Optional: log/warn when MC_INDI_EN=1 and W_MAX==0 so it is not silent.

Unverified: the correct W_MAX value for this gz model (not looked up); whether num_rotors > 0 (effectiveness
config) holds at runtime, since only W_MAX=0 was needed to explain the absence; esc rpm scaling/units vs gz.
