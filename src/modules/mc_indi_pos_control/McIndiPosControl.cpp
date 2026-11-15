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

#include "McIndiPosControl.hpp"

#include <float.h>
#include <string.h>

#include <lib/mathlib/mathlib.h>

using namespace matrix;

ModuleBase::Descriptor McIndiPosControl::desc{task_spawn, custom_command, print_usage};

McIndiPosControl::McIndiPosControl() :
	ModuleParams(nullptr),
	ScheduledWorkItem(MODULE_NAME, px4::wq_configurations::nav_and_controllers),
	_loop_perf(perf_alloc(PC_ELAPSED, MODULE_NAME": cycle"))
{
	// the rotor speed at full thrust is owned by the INDI rate controller; absent if that module is not built
	_param_w_max_handle = param_find("MC_INDI_W_MAX");
	_last_thrust = _param_mpc_thr_hover.get();
	parameters_updated();
}

McIndiPosControl::~McIndiPosControl()
{
	perf_free(_loop_perf);
}

bool
McIndiPosControl::init()
{
	if (!_local_position_sub.registerCallback()) {
		PX4_ERR("callback registration failed");
		return false;
	}

	// advertise before the logger starts, otherwise the optional topic is never logged
	_status_pub.advertise();

	registerMode();
	ScheduleDelayed(kBackupPeriod);
	return true;
}

void
McIndiPosControl::registerMode()
{
	register_ext_component_request_s request{};
	request.timestamp = hrt_absolute_time();
	strncpy(request.name, "INDI POS", sizeof(request.name) - 1);
	request.request_id = EXT_COMPONENT_REQUEST_ID;
	request.px4_ros2_api_version = register_ext_component_request_s::LATEST_PX4_ROS2_API_VERSION;
	request.register_arming_check = true;
	request.register_mode = true;
	request.enable_replace_internal_mode = _param_offb.get();
	request.replace_internal_mode = vehicle_status_s::NAVIGATION_STATE_OFFBOARD;
	request.request_offboard_setpoints = true;
	_register_request_pub.publish(request);
}

void
McIndiPosControl::parameters_updated()
{
	// outer loop: same gains and limits as the stock position controller
	_indi.setGains(Vector3f(_param_mpc_xy_p.get(), _param_mpc_xy_p.get(), _param_mpc_z_p.get()),
		       Vector3f(_param_mpc_xy_vel_p_acc.get(), _param_mpc_xy_vel_p_acc.get(), _param_mpc_z_vel_p_acc.get()));
	_indi.setLimits(_param_mpc_xy_vel_max.get(), _param_mpc_z_vel_max_up.get(), _param_mpc_z_vel_max_dn.get(),
			math::radians(_param_mpc_tiltmax_air.get()), _param_mpc_thr_min.get(), _param_mpc_thr_max.get());
	_indi.setThrustModel(_param_g_t.get(), _param_k_cmd.get());
	_indi.setMeasurementDelay(_param_dly.get());
	_indi.setFeedforward(_param_ff.get());
	applyFilterConfig();

	// attitude loop: mirrors MulticopterAttitudeControl::parameters_updated()
	_attitude_control.setProportionalGain(Vector3f(_param_mc_roll_p.get(), _param_mc_pitch_p.get(),
					      _param_mc_yaw_p.get()), _param_mc_yaw_weight.get());

	using math::radians;

	_attitude_control.setRateLimit(Vector3f(radians(_param_mc_rollrate_max.get()), radians(_param_mc_pitchrate_max.get()),
						radians(_param_mc_yawrate_max.get())));

	_attitude_control.setRefModelFrequency(_param_mc_ref_w_n.get());
	_attitude_control.setFeedForwardGain(_param_mc_ref_ff.get());
	_attitude_control.setFeedForwardLimit(math::radians(_param_mc_ref_ff_max.get()));

	// rotor speed at full thrust, rad/s
	float w_max = 0.f;

	if (_param_w_max_handle != PARAM_INVALID && param_get(_param_w_max_handle, &w_max) == PX4_OK
	    && PX4_ISFINITE(w_max) && w_max > 0.f) {
		_rotor_w_max = w_max;

	} else {
		_rotor_w_max = 0.f;
	}
}

void
McIndiPosControl::applyFilterConfig()
{
	if (_filter_ready) {
		_indi.setFilter(_filter_rate_hz, _param_lpf_cut.get());
		_needs_reset = true;
	}
}

void
McIndiPosControl::measureRate(hrt_abstime t)
{
	if (_filter_ready) {
		return;
	}

	if (_rate_count == 0) {
		_rate_t0 = t;
		_rate_count = 1;
		return;
	}

	_rate_count++;

	if (_rate_count >= kRateSamples) {
		const float elapsed = (t > _rate_t0) ? (t - _rate_t0) * 1e-6f : 0.f;
		const float rate = (elapsed > FLT_EPSILON) ? (float)(_rate_count - 1) / elapsed : 0.f;

		if (PX4_ISFINITE(rate) && rate > 5.f && rate < 1000.f) {
			_filter_rate_hz = rate;
			_filter_ready = true;
			applyFilterConfig();

		} else {
			_rate_count = 0;
		}
	}
}

void
McIndiPosControl::updateExternalMode()
{
	register_ext_component_reply_s reply;

	if (_register_reply_sub.update(&reply)) {
		if (reply.request_id == EXT_COMPONENT_REQUEST_ID && reply.success) {
			_arming_check_id = reply.arming_check_id;
			_mode_id = reply.mode_id;
			_mode_state = ModeState::REGISTERED;
			PX4_INFO("INDI POS registered, arming_check_id %d, mode_id %d", (int)_arming_check_id, (int)_mode_id);
		}
	}

	if (_mode_state != ModeState::REGISTERED) {
		return;
	}

	arming_check_request_s request;

	if (_arming_check_request_sub.update(&request)) {
		arming_check_reply_s arming_reply{};
		arming_reply.timestamp = hrt_absolute_time();
		arming_reply.request_id = request.request_id;
		arming_reply.registration_id = _arming_check_id;
		arming_reply.health_component_index = arming_check_reply_s::HEALTH_COMPONENT_INDEX_NONE;
		arming_reply.num_events = 0;
		arming_reply.can_arm_and_run = true;
		arming_reply.mode_req_angular_velocity = true;
		arming_reply.mode_req_local_position = true;
		arming_reply.mode_req_attitude = true;
		arming_reply.mode_req_local_alt = true;
		_arming_check_reply_pub.publish(arming_reply);
	}

	if (_vehicle_status_sub.update(&_vehicle_status)) {
		const bool active = (_vehicle_status.nav_state == _mode_id);

		if (active && !_active) {
			setpoint_config_s config{};
			config.timestamp = hrt_absolute_time();
			config.source_id = _mode_id;
			config.type = setpoint_config_s::TYPE_RATES;
			config.should_apply = true;
			config.timeout_ms = 0;
			_setpoint_config_pub.publish(config);

			_needs_reset = true;
			_hold_count = 0;
			_failure_reported = false;
			_last_rates.zero();
			_last_thrust = _param_mpc_thr_hover.get();
			_last_cycle_time = 0;
		}

		_active = active;
	}
}

void
McIndiPosControl::updateSensors(hrt_abstime now)
{
	vehicle_attitude_s attitude;

	if (_vehicle_attitude_sub.update(&attitude)) {
		_attitude = attitude;
		_have_attitude = true;
	}

	sensor_combined_s sensor;

	if (_sensor_combined_sub.update(&sensor)) {
		_sensor_combined = sensor;
		_have_sensor = true;
	}

	trajectory_setpoint_s trajectory;

	if (_trajectory_setpoint_sub.update(&trajectory)) {
		_trajectory_setpoint = trajectory;
		_have_trajectory = true;
	}

	vehicle_land_detected_s land;

	if (_land_detected_sub.update(&land)) {
		_landed = land.landed || land.maybe_landed;
	}

	// mean normalised rotor thrust, valid only if all motors are online with a plausible rpm
	esc_status_s esc_status;

	if (_esc_status_sub.update(&esc_status)) {
		const float rpm_max = _rotor_w_max * (60.f / (2.f * M_PI_F));
		const int num_escs = math::min((int)esc_status.esc_count, (int)esc_status_s::CONNECTED_ESC_MAX);
		float u_sum = 0.f;
		uint32_t seen = 0;
		bool ok = (_rotor_w_max > 0.f);

		for (int j = 0; j < num_escs && ok; j++) {
			const esc_report_s &esc = esc_status.esc[j];
			const int motor = (int)esc.actuator_function - (int)esc_report_s::ACTUATOR_FUNCTION_MOTOR1;

			if (motor < 0 || motor >= kNumMotors) {
				continue;
			}

			float u = 0.f;

			if (!(esc_status.esc_online_flags & (1u << j))
			    || !IndiRateControl::normalisedThrustFromRpm((float)esc.esc_rpm, rpm_max, u)) {
				ok = false;
				break;
			}

			u_sum += u;
			seen |= (1u << motor);
		}

		_mean_u_valid = ok && (seen == ((1u << kNumMotors) - 1u));
		_mean_u = _mean_u_valid ? (u_sum / (float)kNumMotors) : NAN;
		_esc_time = (esc_status.timestamp != 0) ? esc_status.timestamp : now;
	}
}

void
McIndiPosControl::publishRates(const Vector3f &rates, float thrust)
{
	vehicle_rates_setpoint_s rates_setpoint{};
	rates_setpoint.roll = rates(0);
	rates_setpoint.pitch = rates(1);
	rates_setpoint.yaw = rates(2);
	rates_setpoint.thrust_body[0] = 0.f;
	rates_setpoint.thrust_body[1] = 0.f;
	rates_setpoint.thrust_body[2] = -thrust;
	rates_setpoint.timestamp = hrt_absolute_time();
	_rates_setpoint_pub.publish(rates_setpoint);
}

void
McIndiPosControl::hold(hrt_abstime now)
{
	if (_hold_count < 255) {
		_hold_count++;
	}

	const bool failure = (_hold_count > kMaxHoldCycles);

	if (!failure) {
		publishRates(_last_rates, _last_thrust);

	} else {
		// level attitude rates with the last thrust, the supervising watchdog judges the mode failure
		publishRates(Vector3f(), _last_thrust);

		if (!_failure_reported) {
			PX4_ERR("hold limit exceeded: level rates, last thrust");
			_failure_reported = true;
		}
	}

	indi_pos_status_s status{};
	status.timestamp = now;
	status.mean_u = NAN;
	status.thrust = _last_thrust;
	status.hold_cycles = (uint8_t)_hold_count;
	status.failure = failure;
	_status_pub.publish(status);

	_needs_reset = true;
}

void
McIndiPosControl::publishStatus(const IndiAccelControl::Output &out, float mean_u, bool mean_u_valid)
{
	indi_pos_status_s status{};
	status.timestamp = hrt_absolute_time();
	out.a_c.copyTo(status.a_c);
	out.a_f.copyTo(status.a_f);
	out.t_f.copyTo(status.t_f);
	out.t_c.copyTo(status.t_c);
	out.omega_ff.copyTo(status.omega_ff);
	status.mean_u = mean_u;
	status.mean_u_valid = mean_u_valid;
	status.thrust = out.thrust;
	status.jerk_source = out.jerk_from_difference ? indi_pos_status_s::JERK_SOURCE_DIFFERENCE :
			     indi_pos_status_s::JERK_SOURCE_FIELD;
	status.hold_cycles = 0;
	status.failure = false;
	_status_pub.publish(status);
}

void
McIndiPosControl::runCycle(hrt_abstime now, bool new_position)
{
	// only while the external mode is active: otherwise the stock chain owns vehicle_rates_setpoint
	if (!_active) {
		return;
	}

	// landed: no control law, zero rates and minimum thrust
	if (_landed) {
		_needs_reset = true;
		_hold_count = 0;
		_failure_reported = false;
		_last_cycle_time = 0;

		if (new_position) {
			_last_rates.zero();
			_last_thrust = _param_mpc_thr_min.get();
			publishRates(_last_rates, _last_thrust);
		}

		return;
	}

	const hrt_abstime lp_age = (now >= _local_position.timestamp) ? (now - _local_position.timestamp) : 0;
	const bool local_position_stale = !_have_local_position || (lp_age > kStaleTimeout);

	// the law runs on new local position samples; the backup schedule only detects a missing one
	if (!new_position && !local_position_stale) {
		return;
	}

	const auto fresh = [now](bool have, hrt_abstime t) {
		return have && (t <= now) && ((now - t) <= kStaleTimeout);
	};

	const bool inputs_ok = fresh(_have_local_position, _local_position.timestamp)
			       && fresh(_have_attitude, _attitude.timestamp)
			       && fresh(_have_sensor, _sensor_combined.timestamp)
			       && fresh(_have_trajectory, _trajectory_setpoint.timestamp)
			       && _local_position.xy_valid && _local_position.z_valid
			       && _local_position.v_xy_valid && _local_position.v_z_valid;

	if (!inputs_ok) {
		hold(now);
		return;
	}

	// cycle time from the local position timestamps
	float dt = 0.f;

	if (_last_cycle_time != 0 && _local_position.timestamp > _last_cycle_time) {
		dt = (_local_position.timestamp - _last_cycle_time) * 1e-6f;

	} else if (_filter_ready) {
		dt = 1.f / _filter_rate_hz;

	} else {
		dt = 0.02f;
	}

	dt = math::constrain(dt, kMinDt, kMaxDt);
	_last_cycle_time = _local_position.timestamp;

	const bool esc_fresh = _mean_u_valid && (_esc_time <= now) && ((now - _esc_time) <= kEscMaxAge);
	const Vector3f f_b(_sensor_combined.accelerometer_m_s2);

	if (_needs_reset) {
		_indi.reset(f_b, esc_fresh ? _mean_u : NAN);
		_needs_reset = false;
	}

	IndiAccelControl::Input in;
	in.p = Vector3f(_local_position.x, _local_position.y, _local_position.z);
	in.v = Vector3f(_local_position.vx, _local_position.vy, _local_position.vz);
	in.q = Quatf(_attitude.q);
	in.f_b = f_b;
	in.mean_u = esc_fresh ? _mean_u : NAN;
	in.mean_u_valid = esc_fresh;
	in.p_ref = Vector3f(_trajectory_setpoint.position);
	in.v_ref = Vector3f(_trajectory_setpoint.velocity);
	in.a_ref = Vector3f(_trajectory_setpoint.acceleration);

	// A zero jerk is what an interface without jerk leaves in the message: use the a_ref difference then.
	const Vector3f j_msg(_trajectory_setpoint.jerk);

	if (j_msg.isAllFinite() && j_msg.norm_squared() > 1e-12f) {
		in.j_ref = j_msg;

	} else {
		in.j_ref = Vector3f(NAN, NAN, NAN);
	}

	in.yaw_ref = _trajectory_setpoint.yaw;
	in.yawspeed_ref = _trajectory_setpoint.yawspeed;
	in.dt = dt;

	IndiAccelControl::Output out;

	if (!_indi.update(in, out)) {
		hold(now);
		return;
	}

	if (!_attitude_control.setAttitudeSetpoint(out.q_d, out.yawspeed_ff, dt)) {
		hold(now);
		return;
	}

	const Vector3f rates = _attitude_control.update(in.q) + out.omega_ff;

	if (!rates.isAllFinite() || !PX4_ISFINITE(out.thrust)) {
		hold(now);
		return;
	}

	_last_rates = rates;
	_last_thrust = out.thrust;
	_hold_count = 0;
	_failure_reported = false;

	publishRates(rates, out.thrust);
	publishStatus(out, esc_fresh ? _mean_u : NAN, esc_fresh);
}

void
McIndiPosControl::Run()
{
	if (should_exit()) {
		_local_position_sub.unregisterCallback();
		ScheduleClear();

		if (_mode_state == ModeState::REGISTERED) {
			unregister_ext_component_s unregister{};
			unregister.timestamp = hrt_absolute_time();
			strncpy(unregister.name, "INDI POS", sizeof(unregister.name) - 1);
			unregister.arming_check_id = _arming_check_id;
			unregister.mode_id = _mode_id;
			unregister.mode_executor_id = -1;
			_unregister_pub.publish(unregister);
		}

		exit_and_cleanup(desc);
		return;
	}

	perf_begin(_loop_perf);

	if (_parameter_update_sub.updated()) {
		parameter_update_s param_update;
		_parameter_update_sub.copy(&param_update);
		updateParams();
		parameters_updated();
	}

	const hrt_abstime now = hrt_absolute_time();

	updateExternalMode();
	updateSensors(now);

	vehicle_local_position_s local_position;
	const bool new_position = _local_position_sub.update(&local_position);

	if (new_position) {
		_local_position = local_position;
		_have_local_position = true;
		measureRate(local_position.timestamp);
	}

	runCycle(now, new_position);

	// backup schedule: arming check replies and stale input detection without local position updates
	ScheduleDelayed(kBackupPeriod);

	perf_end(_loop_perf);
}

int McIndiPosControl::task_spawn(int argc, char *argv[])
{
	McIndiPosControl *instance = new McIndiPosControl();

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

int McIndiPosControl::custom_command(int argc, char *argv[])
{
	return print_usage("unknown command");
}

int McIndiPosControl::print_usage(const char *reason)
{
	if (reason) {
		PX4_WARN("%s\n", reason);
	}

	PRINT_MODULE_DESCRIPTION(
		R"DESCR_STR(
### Description
Outer-loop (acceleration) INDI position controller with jerk feedforward, registered as the external flight mode
"INDI POS" (it replaces the offboard mode if MC_INDIP_OFFB is set). It runs on `vehicle_local_position`, reads
`trajectory_setpoint`, the accelerometer and the ESC rotor speeds and publishes `vehicle_rates_setpoint`. The stock
position, attitude and rate controllers keep serving the other modes. Started from rc.mc_apps if MC_INDIP_EN is 1.
)DESCR_STR");

	PRINT_MODULE_USAGE_NAME("mc_indi_pos_control", "controller");
	PRINT_MODULE_USAGE_COMMAND("start");
	PRINT_MODULE_USAGE_DEFAULT_COMMANDS();

	return 0;
}

extern "C" __EXPORT int mc_indi_pos_control_main(int argc, char *argv[])
{
	return ModuleBase::main(McIndiPosControl::desc, argc, argv);
}
