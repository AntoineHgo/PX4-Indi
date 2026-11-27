/****************************************************************************
 *
 *   Copyright (c) 2026 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

#include "McIndiRateControl.hpp"
#include "IndiInjectionStep.hpp"

#include "IndiErpmArmingCheck.hpp"

#include <drivers/drv_hrt.h>
#include <mathlib/math/Limits.hpp>
#include <mathlib/math/Functions.hpp>
#include <px4_platform_common/events.h>

using namespace matrix;
using namespace time_literals;
using math::radians;

ModuleBase::Descriptor McIndiRateControl::desc{task_spawn, custom_command, print_usage};

static_assert(IndiMeasuredTorque::MAX_MOTORS == actuator_motors_s::NUM_CONTROLS, "motor count mismatch");

McIndiRateControl::McIndiRateControl() :
	ModuleParams(nullptr),
	WorkItem(MODULE_NAME, px4::wq_configurations::rate_ctrl),
	_loop_perf(perf_alloc(PC_ELAPSED, MODULE_NAME": cycle"))
{
	_vehicle_status.vehicle_type = vehicle_status_s::VEHICLE_TYPE_ROTARY_WING;

	_param_imu_gyro_cutoff = param_find("IMU_GYRO_CUTOFF");
	_param_imu_dgyro_cutoff = param_find("IMU_DGYRO_CUTOFF");

	parameters_updated();
}

McIndiRateControl::~McIndiRateControl()
{
	perf_free(_loop_perf);
}

bool
McIndiRateControl::init()
{
	// another rate controller already publishes the torque setpoint: refuse to start a second one
	vehicle_torque_setpoint_s existing{};

	if (_vehicle_torque_setpoint_sub.advertised() && _vehicle_torque_setpoint_sub.copy(&existing)
	    && (hrt_elapsed_time(&existing.timestamp) < 500_ms)) {
		PX4_ERR("vehicle_torque_setpoint already published by another controller, not starting");
		return false;
	}

	// skip history, only messages after start are compared with the own ones
	_vehicle_torque_setpoint_sub.update(&existing);

	if (!_vehicle_angular_velocity_sub.registerCallback()) {
		PX4_ERR("callback registration failed");
		return false;
	}

	return true;
}

void
McIndiRateControl::parameters_updated()
{
	// manual rate control acro mode rate limits
	_acro_rate_max = Vector3f(radians(_param_mc_acro_r_max.get()), radians(_param_mc_acro_p_max.get()),
				  radians(_param_mc_acro_y_max.get()));

	// INDI rate law
	_indi.setGainK(indiEffectiveGainK(Vector3f(_param_mc_indi_k_r.get(), _param_mc_indi_k_p.get(), _param_mc_indi_k_y.get()),
					  _param_mc_indi_id_ok.get() == 1));
	_indi.setG1(Vector3f(_param_mc_indi_g1_r.get(), _param_mc_indi_g1_p.get(), _param_mc_indi_g1_y.get()));
	_indi.setG2Yaw(_param_mc_indi_g2_y.get());
	_indi.setActuatorTimeConstant(_param_mc_indi_act_tc.get());
	_indi.setActuatorBlendTimeConstant(_param_mc_indi_act_bld.get());
	_indi.setLeadScale(_param_mc_indi_lead.get());
	_indi.setDelaySamples(_param_mc_indi_delay.get());
	_indi.setMeasurementDelaySamples(_param_mc_indi_erpm_dly.get());
	_indi.setMaxIncrement(_param_mc_indi_inc_max.get());
	_indi.setLandedSlew(_param_mc_indi_lnd_slew.get());
	_indi.setYawCutoff(_param_mc_indi_yaw_cut.get());
	_rate_sp_watchdog.setTimeout(_param_mc_indi_sp_to.get());

	// system identification excitation, rebuilt only when one of its values changed
	// PT 1 (rate setpoint, rad/s) takes its amplitude from MC_INDI_INJ_AMPR, MC_INDI_INJ_AMP (torque) is ignored then
	const float inject_amp = (_param_mc_indi_inj_pt.get() == 1) ? _param_mc_indi_inj_ampr.get() : _param_mc_indi_inj_amp.get();
	_injection.setParameters(_param_mc_indi_inj_ax.get(), inject_amp, _param_mc_indi_inj_tp.get(),
				 _param_mc_indi_inj_fmin.get(), _param_mc_indi_inj_fmax.get(), _param_mc_indi_inj_np.get(), _param_mc_indi_inj_dly.get());

	// a break-point change never continues a running sequence at the other point
	if (_param_mc_indi_inj_pt.get() != _inject_point_prev) {
		_inject_point_prev = _param_mc_indi_inj_pt.get();
		_injection.restart();
	}

	// the actuator model filter must match the sensor filter chain of the angular acceleration
	float gyro_cutoff = 0.f;
	float dgyro_cutoff = 0.f;

	if (_param_imu_gyro_cutoff != PARAM_INVALID) {
		param_get(_param_imu_gyro_cutoff, &gyro_cutoff);
	}

	if (_param_imu_dgyro_cutoff != PARAM_INVALID) {
		param_get(_param_imu_dgyro_cutoff, &dgyro_cutoff);
	}

	_indi.setFilterCutoffs(gyro_cutoff, dgyro_cutoff);

	// measured torque from the ESC rpm
	_measured_torque.setRotorSpeedMax(_param_mc_indi_w_max.get());
	updateMeasuredTorqueEffectiveness();
}

void
McIndiRateControl::updateMeasuredTorqueEffectiveness()
{
	ActuatorEffectiveness::Configuration config{};

	if (_effectiveness.getEffectivenessMatrix(config, EffectivenessUpdateReason::CONFIGURATION_UPDATE)) {
		bool normalize_rpy[ActuatorEffectiveness::MAX_NUM_MATRICES] {};
		_effectiveness.getNormalizeRPY(normalize_rpy);

		_measured_torque.setEffectiveness(config.effectiveness_matrices[0], config.trim[0],
						  config.linearization_point[0], config.num_actuators_matrix[0], normalize_rpy[0]);

	} else {
		// no valid rotor geometry: no measured torque, arming is refused
		_measured_torque.setEffectiveness(ActuatorEffectiveness::EffectivenessMatrix{}, ActuatorEffectiveness::ActuatorVector{},
						  ActuatorEffectiveness::ActuatorVector{}, 0, true);
	}
}

void
McIndiRateControl::updateMeasuredTorque()
{
	if (!_measured_torque.enabled()) {
		_torque_measured = actuator_torque_measured_s{};
		return;
	}

	_measured_torque.setArmed(_vehicle_control_mode.flag_armed);
	_measured_torque.setFrozenWindow(_param_mc_indi_erpm_frz.get());

	// per motor command for the frozen rpm detection
	actuator_motors_s motors;

	if (_actuator_motors_sub.update(&motors)) {
		const hrt_abstime t_motors = hrt_absolute_time();

		for (int motor = 0; motor < IndiMeasuredTorque::MAX_MOTORS; motor++) {
			_measured_torque.setMotorCommand(motor, motors.control[motor], t_motors);
		}
	}

	esc_status_s esc_status;

	if (_esc_status_sub.update(&esc_status)) {
		const int num_escs = math::min((int)esc_status.esc_count, (int)esc_status_s::CONNECTED_ESC_MAX);

		for (int j = 0; j < num_escs; j++) {
			const esc_report_s &esc = esc_status.esc[j];
			const int motor = (int)esc.actuator_function - (int)esc_report_s::ACTUATOR_FUNCTION_MOTOR1;

			if (motor < 0 || motor >= IndiMeasuredTorque::MAX_MOTORS) {
				continue;
			}

			if (!(esc_status.esc_online_flags & (1u << j))) {
				_measured_torque.setMotorOffline(motor);

			} else {
				_measured_torque.setMotorSample(motor, (float)esc.esc_rpm, esc.esc_errorcount, esc.timestamp);
			}
		}
	}

	const IndiMeasuredTorque::Result result = _measured_torque.compute(hrt_absolute_time());

	actuator_torque_measured_s msg{};
	msg.timestamp = hrt_absolute_time();
	msg.timestamp_sample = result.timestamp_sample;
	msg.torque[0] = result.torque[0];
	msg.torque[1] = result.torque[1];
	msg.torque[2] = result.torque[2];
	msg.valid = result.valid;
	msg.motor_valid_mask = result.motor_valid_mask;
	msg.motor_frozen_mask = result.motor_frozen_mask;
	_actuator_torque_measured_pub.publish(msg);
	_torque_measured = msg;
}

void
McIndiRateControl::updateArmingCheck()
{
	static constexpr hrt_abstime REGISTRATION_RETRY_INTERVAL = 1_s;
	static constexpr hrt_abstime REQUEST_TIMEOUT = 1_s; // requests every ~300 ms, commander drops after ~1.2 s
	static constexpr hrt_abstime EVENT_DELAY = 2_s;     // telemetry takes a moment to start after boot
	static constexpr hrt_abstime EVENT_INTERVAL = 10_s;

	const hrt_abstime now = hrt_absolute_time();
	const bool armed = _vehicle_control_mode.flag_armed;

	register_ext_component_reply_s registration_reply;
	int tries = register_ext_component_reply_s::ORB_QUEUE_LENGTH;

	while (_register_ext_component_reply_sub.update(&registration_reply) && --tries >= 0) {
		if (registration_reply.request_id == ARMING_CHECK_REQUEST_ID && registration_reply.success) {
			if (_arming_check_id != registration_reply.arming_check_id) {
				PX4_INFO("arming check registered, id %d", (int)registration_reply.arming_check_id);
			}

			_arming_check_id = registration_reply.arming_check_id;
			_last_arming_check_request = now;
		}
	}

	// the commander only takes registrations while disarmed and drops a component that stops answering
	if (!armed) {
		if ((_arming_check_id >= 0) && (now > _last_arming_check_request + REQUEST_TIMEOUT)) {
			_arming_check_id = -1;
		}

		if ((_arming_check_id < 0) && (now > _last_registration_request + REGISTRATION_RETRY_INTERVAL)) {
			register_ext_component_request_s request{};
			request.timestamp = now;
			request.request_id = ARMING_CHECK_REQUEST_ID;
			strncpy(request.name, ARMING_CHECK_NAME, sizeof(request.name) - 1);
			request.px4_ros2_api_version = register_ext_component_request_s::LATEST_PX4_ROS2_API_VERSION;
			request.register_arming_check = true;
			_register_ext_component_request_pub.publish(request);
			_last_registration_request = now;
		}
	}

	arming_check_request_s request;

	if (!_arming_check_request_sub.update(&request) || (_arming_check_id < 0)) {
		return;
	}

	_last_arming_check_request = now;

	const IndiErpmArmingCheck::Verdict verdict =
		IndiErpmArmingCheck::evaluate(_measured_torque, now, _param_mc_indi_erpm_to.get(), armed);

	if (verdict.can_arm) {
		_erpm_refused_since = 0;

	} else {
		if (_erpm_refused_since == 0) {
			_erpm_refused_since = now;
		}

		if ((now > _erpm_refused_since + EVENT_DELAY) && (now > _last_erpm_event + EVENT_INTERVAL)) {
			if (verdict.not_configured) {
				/* EVENT
				 * @description
				 * INDI needs the ESC rpm telemetry of every motor. Set <param>MC_INDI_W_MAX</param> and the rotor geometry
				 * (<param>CA_ROTOR0_PX</param> and the other CA_ROTORn parameters) of the airframe.
				 */
				events::send(events::ID("mc_indi_rate_control_rpm_not_configured"), events::Log::Error,
					     "Arming denied: set MC_INDI_W_MAX and the rotor geometry");

			} else {
				/* EVENT
				 * @description
				 * Every motor must report its rpm: the ESC telemetry is not connected or not enabled, or a motor is not
				 * responding.
				 */
				events::send<uint16_t>(events::ID("mc_indi_rate_control_erpm_missing"), events::Log::Error,
						       "Arming denied: no rpm telemetry from motors (bit mask {1})", verdict.motor_mask);
			}

			_last_erpm_event = now;
		}
	}

	arming_check_reply_s reply{};
	reply.timestamp = now;
	reply.request_id = request.request_id;
	reply.registration_id = _arming_check_id;
	reply.health_component_index = arming_check_reply_s::HEALTH_COMPONENT_INDEX_NONE;
	reply.can_arm_and_run = verdict.can_arm;
	_arming_check_reply_pub.publish(reply);
}

void
McIndiRateControl::unregisterArmingCheck()
{
	if (_arming_check_id < 0) {
		return;
	}

	unregister_ext_component_s unregister{};
	unregister.timestamp = hrt_absolute_time();
	strncpy(unregister.name, ARMING_CHECK_NAME, sizeof(unregister.name) - 1);
	unregister.arming_check_id = _arming_check_id;
	unregister.mode_id = -1;
	unregister.mode_executor_id = -1;
	_unregister_ext_component_pub.publish(unregister);
	_arming_check_id = -1;
}

Vector3f
McIndiRateControl::runIndiRateControl(const Vector3f &rates, const Vector3f &angular_accel, float dt, bool landed, bool maybe_landed,
				      hrt_abstime timestamp_sample, bool armed)
{
	// torque the allocator produced from the previous setpoint, only if its feedback belongs to that setpoint
	Vector3f torque_allocated_prev = _prev_torque_setpoint;

	if (_unallocated_torque_time > _prev_torque_setpoint_time) {
		torque_allocated_prev -= _unallocated_torque;
	}

	// measured actuator torque from the ESC rpm, used only while complete, fresh and finite
	const Vector3f torque_measured(_torque_measured.torque);
	const hrt_abstime now = hrt_absolute_time();
	const bool measurement_valid = _torque_measured.valid
				       && IndiMeasuredTorque::isSampleFresh(now, _torque_measured.timestamp_sample, _param_mc_indi_erpm_to.get())
				       && torque_measured.isAllFinite();
	_indi.setMeasuredTorque(torque_measured, measurement_valid);

	// controller output and system identification excitation (torque setpoint or rate setpoint, MC_INDI_INJ_PT)
	IndiInjectionStepIn step_in{};
	step_in.point = _param_mc_indi_inj_pt.get();
	step_in.armed = armed;
	step_in.landed = landed;
	step_in.maybe_landed = maybe_landed;
	step_in.rate_sp_break_allowed = !_rate_sp_stale && _vehicle_control_mode.flag_control_attitude_enabled;
	step_in.timestamp_sample = timestamp_sample;
	step_in.dt = dt;
	IndiInjectionStepOut step{};
	runIndiInjectionStep(_indi, _injection, step_in, rates, _rates_setpoint + _omega_ff_applied, angular_accel, torque_allocated_prev,
			     step);

	// published and stored previous setpoint = controller output + excitation, so every feedback path sees what was applied
	const Vector3f torque_setpoint_pre_inject = step.torque_pre_inject;
	const Vector3f inject = step.torque_inject;
	const Vector3f torque_setpoint = step.torque_sp;

	indi_rate_status_s indi_rate_status{};
	indi_rate_status.timestamp_sample = timestamp_sample;
	torque_setpoint_pre_inject.copyTo(indi_rate_status.torque_sp_pre_inject);
	inject.copyTo(indi_rate_status.inject);
	torque_setpoint.copyTo(indi_rate_status.torque_sp);
	step.rates_sp_pre_inject.copyTo(indi_rate_status.rates_sp_pre_inject);
	step.rates_sp_inject.copyTo(indi_rate_status.rates_sp_inject);
	step.rates_sp_applied.copyTo(indi_rate_status.rates_sp_applied);
	_indi.getNu().copyTo(indi_rate_status.nu);
	_indi.getLeadGain().copyTo(indi_rate_status.lead_gain);
	_indi.getRateSpDot().copyTo(indi_rate_status.rate_sp_dot);
	_indi.getFilteredAngularAccel().copyTo(indi_rate_status.angular_accel_filtered);
	_indi.getFilteredTorque().copyTo(indi_rate_status.torque_filtered);
	_indi.getTorqueIncrement().copyTo(indi_rate_status.torque_increment);
	indi_rate_status.fault = _indi.getFault();
	indi_rate_status.measured_torque_in_use = _indi.measurementInUse();
	indi_rate_status.rate_sp_stale = _rate_sp_stale;
	indi_rate_status.foreign_torque_pub = _torque_stamps.foreignDetected();
	indi_rate_status.timestamp = hrt_absolute_time();
	_indi_rate_status_pub.publish(indi_rate_status);

	return torque_setpoint;
}

void
McIndiRateControl::Run()
{
	if (should_exit()) {
		_vehicle_angular_velocity_sub.unregisterCallback();
		unregisterArmingCheck();
		exit_and_cleanup(desc);
		return;
	}

	perf_begin(_loop_perf);

	// Check if parameters have changed
	if (_parameter_update_sub.updated()) {
		// clear update
		parameter_update_s param_update;
		_parameter_update_sub.copy(&param_update);

		updateParams();
		parameters_updated();
	}

	/* run controller on gyro changes */
	vehicle_angular_velocity_s angular_velocity;

	if (_vehicle_angular_velocity_sub.update(&angular_velocity)) {

		const hrt_abstime now = angular_velocity.timestamp_sample;

		// Guard against too small (< 0.125ms) and too large (> 20ms) dt's.
		const float dt = math::constrain(((now - _last_run) * 1e-6f), 0.000125f, 0.02f);
		_last_run = now;

		const Vector3f rates{angular_velocity.xyz};
		const Vector3f angular_accel{angular_velocity.xyz_derivative};

		/* check for updates in other topics */
		_vehicle_control_mode_sub.update(&_vehicle_control_mode);

		updateArmingCheck();

		if (_vehicle_land_detected_sub.updated()) {
			vehicle_land_detected_s vehicle_land_detected;

			if (_vehicle_land_detected_sub.copy(&vehicle_land_detected)) {
				_landed = vehicle_land_detected.landed;
				_maybe_landed = vehicle_land_detected.maybe_landed;
			}
		}

		_vehicle_status_sub.update(&_vehicle_status);

		// second publisher of the torque setpoint: the latest message must be one of the own
		vehicle_torque_setpoint_s torque_rx;

		if (_vehicle_torque_setpoint_sub.update(&torque_rx) && _torque_stamps.checkReceived(torque_rx.timestamp)) {
			if (hrt_elapsed_time(&_last_foreign_warn) > 2_s) {
				PX4_ERR("vehicle_torque_setpoint published by another controller");
				_last_foreign_warn = hrt_absolute_time();
			}
		}

		// use rates setpoint topic
		vehicle_rates_setpoint_s vehicle_rates_setpoint{};

		if (_vehicle_control_mode.flag_control_manual_enabled && !_vehicle_control_mode.flag_control_attitude_enabled) {
			// generate the rate setpoint from sticks
			manual_control_setpoint_s manual_control_setpoint;

			if (_manual_control_setpoint_sub.update(&manual_control_setpoint)) {
				// manual rates control - ACRO mode
				const Vector3f man_rate_sp{
					math::superexpo(manual_control_setpoint.roll, _param_mc_acro_expo.get(), _param_mc_acro_supexpo.get()),
					math::superexpo(-manual_control_setpoint.pitch, _param_mc_acro_expo.get(), _param_mc_acro_supexpo.get()),
					math::superexpo(manual_control_setpoint.yaw, _param_mc_acro_expo_y.get(), _param_mc_acro_supexpoy.get())};

				_rates_setpoint = man_rate_sp.emult(_acro_rate_max);
				_thrust_setpoint(2) = -(manual_control_setpoint.throttle + 1.f) * .5f;
				_thrust_setpoint(0) = _thrust_setpoint(1) = 0.f;

				// publish rate setpoint
				vehicle_rates_setpoint.roll = _rates_setpoint(0);
				vehicle_rates_setpoint.pitch = _rates_setpoint(1);
				vehicle_rates_setpoint.yaw = _rates_setpoint(2);
				_thrust_setpoint.copyTo(vehicle_rates_setpoint.thrust_body);
				vehicle_rates_setpoint.timestamp = hrt_absolute_time();

				_vehicle_rates_setpoint_pub.publish(vehicle_rates_setpoint);
			}

		} else if (_vehicle_rates_setpoint_sub.update(&vehicle_rates_setpoint)) {
			_rates_setpoint(0) = PX4_ISFINITE(vehicle_rates_setpoint.roll)  ? vehicle_rates_setpoint.roll  : rates(0);
			_rates_setpoint(1) = PX4_ISFINITE(vehicle_rates_setpoint.pitch) ? vehicle_rates_setpoint.pitch : rates(1);
			_rates_setpoint(2) = PX4_ISFINITE(vehicle_rates_setpoint.yaw)   ? vehicle_rates_setpoint.yaw   : rates(2);
			_thrust_setpoint = Vector3f(vehicle_rates_setpoint.thrust_body);
			_last_rates_sp_time = hrt_absolute_time(); // receipt time, not the publisher's stamp
		}

		// rate setpoint timeout (MC_INDI_SP_TO): zero rates, thrust held
		const bool acro_branch = _vehicle_control_mode.flag_control_manual_enabled
					 && !_vehicle_control_mode.flag_control_attitude_enabled;
		const RateSetpointWatchdog::Result wd = _rate_sp_watchdog.update(_last_rates_sp_time, hrt_absolute_time(),
							_vehicle_control_mode.flag_armed, !acro_branch && _vehicle_control_mode.flag_control_rates_enabled);
		_rate_sp_stale = wd.stale;

		// Outer-loop jerk feed-forward (roll, pitch), added to the setpoint at use, never stored in it.
		// Evaluated before the source check: a change of the enable condition steps the effective setpoint, so it restarts the lead too
		_indi_rate_feedforward_sub.update(&_omega_ff_msg);
		_omega_ff_applied.zero();

		const bool omega_ff_on = IndiRateFeedforwardGate::allow(_omega_ff_msg.valid, _omega_ff_msg.timestamp,
					 hrt_absolute_time(), _landed, acro_branch, wd.stale)
					 && PX4_ISFINITE(_omega_ff_msg.omega_ff[0]) && PX4_ISFINITE(_omega_ff_msg.omega_ff[1]);

		if (omega_ff_on) {
			_omega_ff_applied(0) = _omega_ff_msg.omega_ff[0];
			_omega_ff_applied(1) = _omega_ff_msg.omega_ff[1];
		}

		// the rate setpoint source changed (control mode flags, setpoint timeout or recovery): restart its derivative
		const uint8_t sp_source = IndiRateSetpointSource::mask(_vehicle_control_mode.flag_control_attitude_enabled,
					  _vehicle_control_mode.flag_control_rates_enabled, _vehicle_control_mode.flag_control_manual_enabled,
					  _vehicle_control_mode.flag_control_offboard_enabled, wd.stale, omega_ff_on);

		if (sp_source != _sp_source_prev) {
			_indi.resetSetpointLead();
			_sp_source_prev = sp_source;
		}

		if (wd.zero_rates) {
			_rates_setpoint.zero();
		}


		if (wd.warn) {
			PX4_WARN("rate setpoint timeout, rates zeroed, thrust held");
		}

		// run the rate controller
		if (_vehicle_control_mode.flag_control_rates_enabled) {

			// reset the INDI states while disarmed
			if (!_vehicle_control_mode.flag_armed || _vehicle_status.vehicle_type != vehicle_status_s::VEHICLE_TYPE_ROTARY_WING) {
				_indi.reset();
				_prev_torque_setpoint.zero();
			}

			// allocator feedback for the INDI actuator model
			control_allocator_status_s control_allocator_status;

			if (_control_allocator_status_sub.update(&control_allocator_status)) {
				_unallocated_torque = Vector3f(control_allocator_status.unallocated_torque);
				_unallocated_torque_time = control_allocator_status.timestamp;
			}

			// INDI has its own actuator model: no yaw low-pass filter and no battery scaling
			const Vector3f torque_setpoint = runIndiRateControl(rates, angular_accel, dt, _landed, _maybe_landed,
							 angular_velocity.timestamp_sample, _vehicle_control_mode.flag_armed);

			// publish thrust and torque setpoints
			vehicle_thrust_setpoint_s vehicle_thrust_setpoint{};
			vehicle_torque_setpoint_s vehicle_torque_setpoint{};

			_thrust_setpoint.copyTo(vehicle_thrust_setpoint.xyz);
			vehicle_torque_setpoint.xyz[0] = PX4_ISFINITE(torque_setpoint(0)) ? torque_setpoint(0) : 0.f;
			vehicle_torque_setpoint.xyz[1] = PX4_ISFINITE(torque_setpoint(1)) ? torque_setpoint(1) : 0.f;
			vehicle_torque_setpoint.xyz[2] = PX4_ISFINITE(torque_setpoint(2)) ? torque_setpoint(2) : 0.f;

			vehicle_thrust_setpoint.timestamp_sample = angular_velocity.timestamp_sample;
			vehicle_thrust_setpoint.timestamp = hrt_absolute_time();
			_vehicle_thrust_setpoint_pub.publish(vehicle_thrust_setpoint);

			vehicle_torque_setpoint.timestamp_sample = angular_velocity.timestamp_sample;
			vehicle_torque_setpoint.timestamp = hrt_absolute_time();
			_vehicle_torque_setpoint_pub.publish(vehicle_torque_setpoint);

			_prev_torque_setpoint = Vector3f(vehicle_torque_setpoint.xyz);
			_prev_torque_setpoint_time = vehicle_torque_setpoint.timestamp;
			_torque_stamps.recordOwn(vehicle_torque_setpoint.timestamp);

			updateActuatorControlsStatus(vehicle_torque_setpoint, dt);

			// Measured torque of the rotors at this point, as the control allocator publishes it right after the
			// torque setpoint: the next cycle uses it.
			updateMeasuredTorque();
		}
	}

	perf_end(_loop_perf);
}

void McIndiRateControl::updateActuatorControlsStatus(const vehicle_torque_setpoint_s &vehicle_torque_setpoint,
		float dt)
{
	for (int i = 0; i < 3; i++) {
		_control_energy[i] += vehicle_torque_setpoint.xyz[i] * vehicle_torque_setpoint.xyz[i] * dt;
	}

	_energy_integration_time += dt;

	if (_energy_integration_time > 500e-3f) {

		actuator_controls_status_s status;
		status.timestamp = vehicle_torque_setpoint.timestamp;

		for (int i = 0; i < 3; i++) {
			status.control_power[i] = _control_energy[i] / _energy_integration_time;
			_control_energy[i] = 0.f;
		}

		_actuator_controls_status_pub.publish(status);
		_energy_integration_time = 0.f;
	}
}

int McIndiRateControl::task_spawn(int argc, char *argv[])
{
	McIndiRateControl *instance = new McIndiRateControl();

	if (instance) {
		desc.object.store(instance);
		desc.task_id = task_id_is_work_queue;

		if (instance->init()) {
			return PX4_OK;
		}

	} else {
		PX4_ERR("alloc failed");
	}

	delete instance;
	desc.object.store(nullptr);
	desc.task_id = -1;

	return PX4_ERROR;
}

int McIndiRateControl::custom_command(int argc, char *argv[])
{
	return print_usage("unknown command");
}

int McIndiRateControl::print_usage(const char *reason)
{
	if (reason) {
		PX4_WARN("%s\n", reason);
	}

	PRINT_MODULE_DESCRIPTION(
		R"DESCR_STR(
### Description
This implements the multicopter rate controller with incremental nonlinear dynamic inversion (INDI).
It takes rate setpoints (in acro mode via `manual_control_setpoint` topic) as inputs and outputs
torque and thrust setpoints.

It replaces `mc_rate_control` (PID): only one of the two is started, selected by the parameter `MC_INDI_EN`
(see rc.mc_apps). With `MC_INDI_W_MAX` set it computes the torque produced by the measured rotor speeds
(ESC rpm telemetry) and publishes it as `actuator_torque_measured`. Arming is refused while `MC_INDI_W_MAX`
or the rotor geometry is not set, or while a motor has no rpm telemetry.

)DESCR_STR");

	PRINT_MODULE_USAGE_NAME("mc_indi_rate_control", "controller");
	PRINT_MODULE_USAGE_COMMAND("start");
	PRINT_MODULE_USAGE_DEFAULT_COMMANDS();

	return 0;
}

extern "C" __EXPORT int mc_indi_rate_control_main(int argc, char *argv[])
{
	return ModuleBase::main(McIndiRateControl::desc, argc, argv);
}
