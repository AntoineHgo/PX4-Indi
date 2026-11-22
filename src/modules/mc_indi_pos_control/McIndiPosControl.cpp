/****************************************************************************
 *
 *   Copyright (c) 2013-2020 PX4 Development Team. All rights reserved.
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
#include "IndiStageMode.hpp"

#include <float.h>
#include <lib/mathlib/mathlib.h>
#include <lib/matrix/matrix/math.hpp>
#include <px4_platform_common/events.h>
#include "PositionControl/ControlMath.hpp"

using namespace matrix;

ModuleBase::Descriptor McIndiPosControl::desc{task_spawn, custom_command, print_usage};

McIndiPosControl::McIndiPosControl(bool vtol) :
	ModuleParams(nullptr),
	ScheduledWorkItem(MODULE_NAME, px4::wq_configurations::nav_and_controllers),
	_vehicle_attitude_setpoint_pub(vtol ? ORB_ID(mc_virtual_attitude_setpoint) : ORB_ID(vehicle_attitude_setpoint))
{
	_sample_interval_s.update(0.01f); // 100 Hz default
	parameters_update(true);
	_tilt_limit_slew_rate.setSlewRate(.2f);
	_takeoff_status_pub.advertise();
	_w_max_handle = param_find("MC_INDI_W_MAX");
	_accel_control.setFeedforward(true); // jerk -> body rate feed-forward, consumed by mc_indi_rate_control
}

McIndiPosControl::~McIndiPosControl()
{
	perf_free(_cycle_perf);
}

bool McIndiPosControl::init()
{
	if (!_local_pos_sub.registerCallback() || !_acceleration_sub.registerCallback()) {
		PX4_ERR("callback registration failed");
		return false;
	}

	_time_stamp_last_loop = hrt_absolute_time();
	ScheduleNow();

	return true;
}

void McIndiPosControl::pollStageInputs()
{
	vehicle_attitude_s att;

	if (_attitude_sub.update(&att)) {
		_q = matrix::Quatf(att.q);
		_q_time = att.timestamp;
	}

	pollAcceleration();
}

void McIndiPosControl::pollAcceleration()
{
	vehicle_acceleration_s acc;

	// vehicle_acceleration has queue length 1 and is published at ~267 Hz: every sample is drained here, on every
	// wakeup (the module is also scheduled on vehicle_acceleration), so each sample reaches the native-rate force filter
	// before the INDI loop decimates
	if (_acceleration_sub.update(&acc)) {
		const matrix::Vector3f specific_force(acc.xyz);
		const hrt_abstime sample_time = (acc.timestamp_sample != 0) ? acc.timestamp_sample : acc.timestamp;

		if (_acc_sample_time != 0 && sample_time > _acc_sample_time) {
			const float dt = math::constrain((sample_time - _acc_sample_time) * 1e-6f, 1e-3f, 0.05f);
			_accel_control.sampleSpecificForce(specific_force, dt);
		}

		_acc_sample_time = sample_time;
		_specific_force_body_mps2 = specific_force;
		_acc_time = acc.timestamp;
	}
}

void McIndiPosControl::runIndiStage(float raw_dt, hrt_abstime now, bool want_active, bool model_force, bool flying, float tilt_limit_rad,
				    float ht,
				    vehicle_local_position_setpoint_s &local_pos_sp, vehicle_attitude_setpoint_s &att_sp)
{
	constexpr hrt_abstime kMaxAge = kStageMaxAge;
	constexpr hrt_abstime kEscMaxAge = 100_ms;
	constexpr hrt_abstime kAllocMaxAge = 200_ms;
	using matrix::Vector3f;

	_omega_ff_valid = false; // set by an active INDI cycle below

	// attitude and specific force were polled before PositionControl::update (pollStageInputs): use the samples the
	// freshness check saw, so the integrator reset and can_run agree within a cycle

	vehicle_thrust_setpoint_s thr;

	if (_thrust_setpoint_sub.update(&thr)) {
		_coll_meas = -thr.xyz[2];
		_thr_time = thr.timestamp;
	}

	esc_status_s esc_status;

	if (_esc_status_sub.update(&esc_status)) {
		// mean normalised rotor thrust u = (omega / omega_max)^2, valid only if all motors report
		const float rpm_max = _rotor_w_max * (60.f / (2.f * M_PI_F));
		const int n = math::min((int)esc_status.esc_count, (int)esc_status_s::CONNECTED_ESC_MAX);
		float rotor_thrust_sum = 0.f;
		uint32_t seen = 0;
		bool ok = (_rotor_w_max > 0.f);

		for (int j = 0; j < n && ok; j++) {
			const esc_report_s &esc = esc_status.esc[j];
			const int motor = (int)esc.actuator_function - (int)esc_report_s::ACTUATOR_FUNCTION_MOTOR1;

			if (motor < 0 || motor >= 4) {
				continue;
			}

			float rotor_thrust = 0.f;

			if (!(esc_status.esc_online_flags & (1u << j))
			    || !IndiRateControl::normalisedThrustFromRpm((float)esc.esc_rpm, rpm_max, rotor_thrust)) {
				ok = false;
				break;
			}

			rotor_thrust_sum += rotor_thrust;
			seen |= (1u << motor);
		}

		_mean_rotor_thrust_valid = ok && (seen == 0xFu);
		_mean_rotor_thrust = _mean_rotor_thrust_valid ? (rotor_thrust_sum / 4.f) : NAN;
		_esc_time = (esc_status.timestamp != 0) ? esc_status.timestamp : now;
	}

	// the library sees the true interval (lower-clamped, up to kStageDtMax); a longer interval holds (rate < 5 Hz).
	// Filter set-up: rate of the true interval, protected against jitter by the hysteresis below (no per-cycle reconfiguration)
	const bool interval_ok = stageIntervalOk(raw_dt);
	const float dt = stageDt(raw_dt);
	const float rate = interval_ok ? roundf(1.f / dt) : 0.f;
	const float cutoff_hz = _param_indi_lpf.get();

	// hysteresis: a rate deviation of more than 20 % must persist for kRateDevCycles cycles (a single late
	// sample must not re-configure the filters, and the return from it must not either); after a Hold a deviated rate re-configures at once
	constexpr int kRateDevCycles = 5;
	const bool rate_dev = (rate >= 5.f) && (fabsf(rate - _filter_hz) > 0.2f * _filter_hz);
	_rate_dev_count = rate_dev ? math::min(_rate_dev_count + 1, kRateDevCycles) : 0;

	if (rate >= 5.f && (_filter_hz <= 0.f || _rate_dev_count >= kRateDevCycles || (_stage_was_hold && rate_dev)
			    || !isEqualF(cutoff_hz, _filter_cut))) {
		_filter_hz = rate;
		_filter_cut = cutoff_hz;
		_rate_dev_count = 0;
		_accel_control.setFilter(_filter_hz, cutoff_hz); // re-seeds the filters from their last output (no zero state)
	}

	// control allocator saturation (holds the collective blend), fresh reports only
	control_allocator_status_s alloc;

	if (_alloc_status_sub.update(&alloc)) {
		bool sat = !alloc.thrust_setpoint_achieved;

		for (int j = 0; j < 4; j++) {
			sat = sat || (alloc.actuator_saturation[j] != control_allocator_status_s::ACTUATOR_SATURATION_OK);
		}

		_alloc_saturated = sat;
		_alloc_time = (alloc.timestamp != 0) ? alloc.timestamp : now;
	}

	const float accel_per_thrust_mps2 = IndiAccelControl::kGravity / math::max(ht, 0.05f);
	_accel_control.setThrustModel(accel_per_thrust_mps2, 1.f);
	_accel_control.setLimits(_param_mpc_xy_vel_max.get(), _param_mpc_z_vel_max_up.get(), _param_mpc_z_vel_max_dn.get(),
				 tilt_limit_rad, flying ? _param_mpc_thr_min.get() : 0.f, _param_mpc_thr_max.get()); // as stock: ramp from zero

	// a sample newer than this cycle's 'now' (published after it was taken) has age 0, not stale
	auto age = [now](hrt_abstime t) { return (now > t) ? (now - t) : hrt_abstime{0}; };
	const bool fresh_att = _q_time != 0 && age(_q_time) <= kMaxAge;
	const bool fresh_acc = _acc_time != 0 && age(_acc_time) <= kMaxAge;
	const bool fresh_thr = _thr_time != 0 && age(_thr_time) <= kMaxAge;
	const bool fresh_esc = _mean_rotor_thrust_valid && age(_esc_time) <= kEscMaxAge;
	// commanded acceleration of the stock position loop, the input of the INDI loop
	const Vector3f accel_command_pre_inject(local_pos_sp.acceleration[0], local_pos_sp.acceleration[1], local_pos_sp.acceleration[2]);

	const float yaw_sp = matrix::Eulerf(matrix::Quatf(att_sp.q_d)).psi();
	const bool att_ok = fresh_att && _q.isAllFinite() && (_q.norm() >= 0.5f);
	// hysteresis: leave the modelled-acceleration mode only after 20 ms of continuously fresh acceleration
	const bool acc_fresh_now = fresh_acc && _specific_force_body_mps2.isAllFinite();

	if (!acc_fresh_now) {
		_acc_fresh_since = 0;
		_acc_stale_latched = true;

	} else if (_acc_fresh_since == 0) {
		_acc_fresh_since = now;
	}

	if (acc_fresh_now && _acc_stale_latched && (age(_acc_fresh_since) >= kAccRecoverTime)) {
		_acc_stale_latched = false;
	}

	const bool acc_ok = acc_fresh_now && !_acc_stale_latched;
	const bool aref_ok = accel_command_pre_inject.isAllFinite();
	StageMode mode = selectStageMode(want_active, att_ok, acc_ok, aref_ok, interval_ok, model_force);
	const bool can_run = (mode == StageMode::Indi) || (mode == StageMode::IndiModelAccel);

	// re-entry to position control: restart the loop and refresh the held setpoint from the current attitude and the
	// measured collective, so a Hold on the first cycle never publishes a pre-switch setpoint
	if (_pos_entry_pending) {
		_pos_entry_pending = false;
		_indi_reset_pending = true;
		const float hold_collective_raw = fresh_thr ? _coll_meas : _last_thrust;

		if (att_ok && PX4_ISFINITE(hold_collective_raw)) {
			const float hold_collective = math::max(hold_collective_raw, 0.f);
			const Vector3f thr_b(0.f, 0.f, -hold_collective);
			const Vector3f thr_n = matrix::Dcmf(_q) * thr_b;
			vehicle_attitude_setpoint_s held_att{};
			vehicle_local_position_setpoint_s held_pos{};
			_q.copyTo(held_att.q_d);
			thr_b.copyTo(held_att.thrust_body);
			thr_n.copyTo(held_pos.thrust);
			storeHeld(held_att, held_pos);

		} else {
			_held_valid = false;
		}
	}

	// Hold -> run: the time base did not advance in Hold
	if (shouldResetOnHoldToRun(_stage_was_hold, can_run)) {
		_indi_reset_pending = true;
	}

	_stage_was_hold = (mode == StageMode::Hold);

	// log each change of the run conditions (bit set = condition met), capped
	const bool lib_ok_prev = _indi_active;
	const int reason = (want_active ? 1 : 0) | (fresh_att ? 2 : 0) | (fresh_acc ? 4 : 0) | (accel_command_pre_inject.isAllFinite() ? 8 : 0)
			   | (interval_ok ? 16 : 0) | (fresh_esc ? 32 : 0) | (lib_ok_prev ? 64 : 0);

	if (reason != _stage_reason && _stage_reports < 20) {
		PX4_INFO("INDI stage cond 0x%02x (want att acc aref rate esc active) rate %.0f", reason, (double)rate);
		_stage_reports++;
	}

	_stage_reason = reason;

	if (can_run) {
		// bench loop-break excitation d on one NED axis, not computed (u == c) when MC_INDI_PINJ_AX is 0
		Vector3f inject{};
		const int inject_axis = _injection.axis();

		if ((inject_axis >= 0) && (mode == StageMode::Indi)) {
			inject(inject_axis) = _injection.update(now, _vehicle_control_mode.flag_armed, _vehicle_land_detected.landed);
		}

		// u = c + d replaces c in the whole loop: thrust vector, previous thrust command, blend model path and jerk
		// difference are all computed from u, so every feedback path closes through u
		// MC_INDI_PINJ_PT = 1 moves d to the loop output instead (acceleration-loop break): reference = c
		const bool inject_output = (_param_indi_pinj_pt.get() == 1) && (inject_axis >= 0);
		const Vector3f accel_reference = inject_output ? accel_command_pre_inject : (accel_command_pre_inject + inject);

		if (_indi_reset_pending) {
			// restart (position-control entry, Hold -> run, state reset): differencing restarts from the current state
			// (reset() keeps the blend, so no collective step)
			const float collective_raw = fresh_thr ? _coll_meas : _last_thrust;
			const float collective = PX4_ISFINITE(collective_raw) ? math::max(collective_raw, 0.f) : 0.f;
			_accel_control.reset((fresh_acc && !model_force) ? _specific_force_body_mps2 : Vector3f(0.f, 0.f, -collective * accel_per_thrust_mps2),
					     collective, fresh_esc ? _mean_rotor_thrust : NAN);
			_indi_reset_pending = false;
			_indi_jerk_reset_pending = false;

		} else if (_indi_jerk_reset_pending) {
			// estimator reset while the loop runs: forget the jerk difference history so that a setpoint step from the reset
			// is not differentiated. The measured force/collective filters are frame independent and kept (re-seeding them with
			// one raw sample gave a 1.9 deg tilt spike at a yaw reset)
			_accel_control.resetJerkHistory();
			_indi_jerk_reset_pending = false;
		}

		IndiAccelControl::Input in;
		in.accel_only = true;
		// climb rate only (no position, no velocity control): INDI collective, stock thrust direction
		in.z_only = deriveZOnly(_vehicle_control_mode.flag_control_position_enabled,
					_vehicle_control_mode.flag_control_velocity_enabled);
		in.thrust_dir = Vector3f(local_pos_sp.thrust[0], local_pos_sp.thrust[1], local_pos_sp.thrust[2]);

		if (in.z_only && isZeroThrustDir(in.thrust_dir(0), in.thrust_dir(1), in.thrust_dir(2))) {
			in.thrust_dir = Vector3f(0.f, 0.f, -1.f); // stock thrust is zero (altitude mode on the ground): straight up
		}

		in.q = _q;
		const bool model_acc = (mode == StageMode::IndiModelAccel);
		// with f_b_valid = false the library substitutes the delayed modelled specific force
		in.f_b = _specific_force_body_mps2;
		in.f_b_valid = !model_acc;
		in.mean_u = _mean_rotor_thrust;
		in.mean_u_valid = fresh_esc && !model_acc;
		in.alloc_saturated = _alloc_saturated && (_alloc_time != 0) && (age(_alloc_time) <= kAllocMaxAge);
		in.a_ref = accel_reference;
		in.a_ff = _accel_feedforward_mps2; // feed-forward only: the jerk difference must not see the P/D feedback or the injection
		// the jerk feed-forward always comes from the library's difference of a_ff. The stock
		// trajectory_setpoint.jerk is not used: in auto modes it is the generator's bang-bang jerk (+-MPC_JERK_AUTO),
		// not the derivative of the published acceleration.
		in.j_ref = matrix::Vector3f(NAN, NAN, NAN);
		in.yaw_ref = yaw_sp;
		in.dt = dt;
		IndiAccelControl::Output out;

		// the collective blend is held on the ground (the clamp, invalid telemetry and bypass cases are held inside
		// the library, which is not updated while bypassed and whose reset() keeps the blend)
		const bool blend_hold = _vehicle_land_detected.landed || _vehicle_land_detected.maybe_landed || model_acc;
		_accel_control.setBlendHold(blend_hold);

		if (_accel_control.update(in, out)) {
			// output point: u_o = t_c + d is what the vehicle gets; the library models the actuator from it
			Vector3f thrust_command_applied = out.t_c;

			if (inject_output && (fabsf(inject(inject_axis)) > 0.f)) {
				thrust_command_applied += inject;
				_accel_control.setAppliedThrust(thrust_command_applied.norm());
			}

			indi_pos_status_s status{};
			status.timestamp = hrt_absolute_time();
			out.a_c.copyTo(status.a_c); // c + d
			accel_command_pre_inject.copyTo(status.a_c_pre_inject);
			inject.copyTo(status.inject);
			out.a_f.copyTo(status.a_f);
			out.t_f.copyTo(status.t_f);
			out.t_c.copyTo(status.t_c);
			thrust_command_applied.copyTo(status.t_c_applied);
			out.omega_ff.copyTo(status.omega_ff);
			_omega_ff_out = out.omega_ff;
			// only the full INDI loop on the measured force in flight (not ramp/ground, landed, z only)
			_omega_ff_valid = (mode == StageMode::Indi) && !model_force && flying && !_vehicle_land_detected.landed
					  && !in.z_only && out.omega_ff.isAllFinite();
			status.mean_u = _mean_rotor_thrust;
			status.mean_u_valid = in.mean_u_valid;
			status.stage_mode = static_cast<uint8_t>(mode);
			status.thrust = out.thrust;
			status.blend = out.blend;
			status.blend_hold = blend_hold;
			status.blend_frozen = out.blend_frozen;
			_indi_pos_status_pub.publish(status);

			const Vector3f thr_vec = thrust_command_applied / accel_per_thrust_mps2; // normalised thrust vector (NED), norm = collective
			ControlMath::thrustToAttitude(thr_vec, yaw_sp, att_sp);
			local_pos_sp.thrust[0] = thr_vec(0);
			local_pos_sp.thrust[1] = thr_vec(1);
			local_pos_sp.thrust[2] = thr_vec(2);
			_last_thrust = out.thrust;
			_indi_active = true;
			storeHeld(att_sp, local_pos_sp);
			trackDegraded(model_force ? StageMode::Indi : mode, now); // planned modelled force (ground/ramp) is not degraded
			return;
		}

		// update() rejected its inputs: hold
		mode = StageMode::Hold;
		_stage_was_hold = true;
	}

	if (mode == StageMode::Hold) {
		// zero-order hold of the last attitude setpoint and thrust published by an INDI cycle. Edge: if no INDI cycle
		// has run yet, the held values are those of the last bypass cycle (the ground/rampup handover value, stored
		// there); with no cycle at all, a level attitude at hover thrust in flight, zero thrust otherwise.
		// The stock thrust is never published.
		if (_held_valid) {
			for (int i = 0; i < 4; i++) { att_sp.q_d[i] = _held_q_d[i]; }

			for (int i = 0; i < 3; i++) { att_sp.thrust_body[i] = _held_thrust_body[i]; local_pos_sp.thrust[i] = _held_thrust_ned[i]; }

			_last_thrust = -_held_thrust_body[2];

		} else {
			const Vector3f thr_vec(0.f, 0.f, -holdFallbackThrust(flying, ht));
			const float yaw_hold = PX4_ISFINITE(yaw_sp) ? yaw_sp : (att_ok ? matrix::Eulerf(_q).psi() : 0.f);
			ControlMath::thrustToAttitude(thr_vec, yaw_hold, att_sp);
			thr_vec.copyTo(local_pos_sp.thrust);
			_last_thrust = -att_sp.thrust_body[2];
		}

		indi_pos_status_s status{};
		status.timestamp = hrt_absolute_time();
		accel_command_pre_inject.copyTo(status.a_c_pre_inject);
		status.mean_u = _mean_rotor_thrust;
		status.mean_u_valid = false;
		status.thrust = -att_sp.thrust_body[2];
		status.blend_hold = true;
		status.stage_mode = static_cast<uint8_t>(StageMode::Hold);
		_indi_pos_status_pub.publish(status);
		_indi_active = true;
		trackDegraded(StageMode::Hold, now);
		return;
	}

	trackDegraded(StageMode::Bypass, now);
	_indi_reset_pending = false; // the bypass branch below resets the INDI loop every cycle
	_indi_jerk_reset_pending = false;

	// bypass: stock attitude setpoint is published, the INDI loop tracks the thrust actually commanded
	// reset() below keeps the blend; model path from the commanded collective, measured path from the ESC mean u
	_accel_control.setBlendHold(true);
	const float stock_collective = -att_sp.thrust_body[2];
	const float collective_raw = fresh_thr ? _coll_meas : (PX4_ISFINITE(stock_collective) ? stock_collective : _last_thrust);
	const float collective = PX4_ISFINITE(collective_raw) ? math::max(collective_raw, 0.f) : 0.f;
	// c is the COMMANDED collective (not measured): the measured mean u is passed separately (NaN: use the model path)
	_accel_control.reset(fresh_acc ? _specific_force_body_mps2 : Vector3f(0.f, 0.f, -collective * accel_per_thrust_mps2), collective,
			     fresh_esc ? _mean_rotor_thrust : NAN);
	_last_thrust = PX4_ISFINITE(stock_collective) ? stock_collective : collective;
	_indi_active = false;
	storeHeld(att_sp, local_pos_sp); // handover value for a hold before any INDI cycle
}

void McIndiPosControl::resetStageState()
{
	_accel_control.resetBlend();
	_acc_stale_latched = false;
	_acc_fresh_since = 0;
	_held_valid = false;
	_last_thrust = 0.f;
	_indi_active = false;
	_indi_reset_pending = true; // filters and differencing restart on the next cycle
}

void McIndiPosControl::storeHeld(const vehicle_attitude_setpoint_s &att_sp, const vehicle_local_position_setpoint_s &local_pos_sp)
{
	bool ok = true;

	for (int i = 0; i < 4; i++) { ok = ok && PX4_ISFINITE(att_sp.q_d[i]); }

	for (int i = 0; i < 3; i++) { ok = ok && PX4_ISFINITE(att_sp.thrust_body[i]) && PX4_ISFINITE(local_pos_sp.thrust[i]); }

	if (!ok) {
		return;
	}

	for (int i = 0; i < 4; i++) { _held_q_d[i] = att_sp.q_d[i]; }

	for (int i = 0; i < 3; i++) { _held_thrust_body[i] = att_sp.thrust_body[i]; _held_thrust_ned[i] = local_pos_sp.thrust[i]; }

	_held_valid = true;
}

void McIndiPosControl::trackDegraded(StageMode mode, hrt_abstime now)
{
	const bool degraded = (mode == StageMode::IndiModelAccel) || (mode == StageMode::Hold);

	if (!degraded) {
		_degraded_since = 0;
		_degraded_warned = false;
		return;
	}

	if (_degraded_since == 0) {
		_degraded_since = now;
	}

	if (!_degraded_warned && (now - _degraded_since > 500_ms)) {
		PX4_WARN("INDI stage degraded (mode %d: %s) for > 0.5 s", (int)mode,
			 (mode == StageMode::Hold) ? "hold" : "modelled acceleration");
		_degraded_warned = true;
	}
}

void McIndiPosControl::parameters_update(bool force)
{
	// check for parameter updates
	if (_parameter_update_sub.updated() || force) {
		// clear update
		parameter_update_s pupdate;
		_parameter_update_sub.copy(&pupdate);

		// update parameters from storage
		ModuleParams::updateParams();

		float sample_freq_hz = 1.f / _sample_interval_s.mean();

		// velocity notch filter
		if ((_param_mpc_vel_nf_frq.get() > 0.f) && (_param_mpc_vel_nf_bw.get() > 0.f)) {
			_vel_xy_notch_filter.setParameters(sample_freq_hz, _param_mpc_vel_nf_frq.get(), _param_mpc_vel_nf_bw.get());
			_vel_z_notch_filter.setParameters(sample_freq_hz, _param_mpc_vel_nf_frq.get(), _param_mpc_vel_nf_bw.get());

		} else {
			_vel_xy_notch_filter.disable();
			_vel_z_notch_filter.disable();
		}

		// velocity xy/z low pass filter, unfiltered when the cutoff is not achievable
		if (!((_param_mpc_vel_lp.get() > 0.f)
		      && _vel_xy_lp_filter.setCutoffFreq(sample_freq_hz, _param_mpc_vel_lp.get())
		      && _vel_z_lp_filter.setCutoffFreq(sample_freq_hz, _param_mpc_vel_lp.get()))) {
			_vel_xy_lp_filter.setAlpha(1.f);
			_vel_z_lp_filter.setAlpha(1.f);
		}

		// velocity derivative xy/z low pass filter, unfiltered when the cutoff is not achievable
		if (!((_param_mpc_veld_lp.get() > 0.f)
		      && _vel_deriv_xy_lp_filter.setCutoffFreq(sample_freq_hz, _param_mpc_veld_lp.get())
		      && _vel_deriv_z_lp_filter.setCutoffFreq(sample_freq_hz, _param_mpc_veld_lp.get()))) {
			_vel_deriv_xy_lp_filter.setAlpha(1.f);
			_vel_deriv_z_lp_filter.setAlpha(1.f);
		}



		int num_changed = 0;

		if (_param_sys_vehicle_resp.get() >= 0.f) {
			// make it less sensitive at the lower end
			float responsiveness = _param_sys_vehicle_resp.get() * _param_sys_vehicle_resp.get();

			num_changed += _param_mpc_acc_hor.commit_no_notification(math::lerp(1.f, 15.f, responsiveness));
			num_changed += _param_mpc_acc_hor_max.commit_no_notification(math::lerp(2.f, 15.f, responsiveness));
			num_changed += _param_mpc_man_y_max.commit_no_notification(math::lerp(80.f, 450.f, responsiveness));

			if (responsiveness > 0.6f) {
				num_changed += _param_mpc_man_y_tau.commit_no_notification(0.f);

			} else {
				num_changed += _param_mpc_man_y_tau.commit_no_notification(math::lerp(0.5f, 0.f, responsiveness / 0.6f));
			}

			if (responsiveness < 0.5f) {
				num_changed += _param_mpc_tiltmax_air.commit_no_notification(45.f);

			} else {
				num_changed += _param_mpc_tiltmax_air.commit_no_notification(math::min(MAX_SAFE_TILT_DEG, math::lerp(45.f, 70.f,
						(responsiveness - 0.5f) * 2.f)));
			}

			num_changed += _param_mpc_acc_down_max.commit_no_notification(math::lerp(0.8f, 15.f, responsiveness));
			num_changed += _param_mpc_acc_up_max.commit_no_notification(math::lerp(1.f, 15.f, responsiveness));
			num_changed += _param_mpc_jerk_max.commit_no_notification(math::lerp(2.f, 50.f, responsiveness));
			num_changed += _param_mpc_jerk_auto.commit_no_notification(math::lerp(1.f, 25.f, responsiveness));
		}

		if (_param_mpc_xy_vel_all.get() >= 0.f) {
			float xy_vel = _param_mpc_xy_vel_all.get();
			num_changed += _param_mpc_vel_manual.commit_no_notification(xy_vel);
			num_changed += _param_mpc_vel_man_back.commit_no_notification(-1.f);
			num_changed += _param_mpc_vel_man_side.commit_no_notification(-1.f);
			num_changed += _param_mpc_xy_cruise.commit_no_notification(xy_vel);
			num_changed += _param_mpc_xy_vel_max.commit_no_notification(xy_vel);
		}

		if (_param_mpc_z_vel_all.get() >= 0.f) {
			float z_vel = _param_mpc_z_vel_all.get();
			num_changed += _param_mpc_z_v_auto_up.commit_no_notification(z_vel);
			num_changed += _param_mpc_z_vel_max_up.commit_no_notification(z_vel);
			num_changed += _param_mpc_z_v_auto_dn.commit_no_notification(z_vel * 0.75f);
			num_changed += _param_mpc_z_vel_max_dn.commit_no_notification(z_vel * 0.75f);
			num_changed += _param_mpc_tko_speed.commit_no_notification(z_vel * 0.6f);
			num_changed += _param_mpc_land_speed.commit_no_notification(z_vel * 0.5f);
		}

		if (num_changed > 0) {
			param_notify_changes();
		}

		if (_param_mpc_tiltmax_air.get() > MAX_SAFE_TILT_DEG) {
			_param_mpc_tiltmax_air.set(MAX_SAFE_TILT_DEG);
			_param_mpc_tiltmax_air.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Tilt constrained to safe value\t");
			/* EVENT
			 * @description <param>MPC_TILTMAX_AIR</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_tilt_set"), events::Log::Warning,
					    "Maximum tilt limit has been constrained to a safe value", MAX_SAFE_TILT_DEG);
		}

		if (_param_mpc_tiltmax_lnd.get() > _param_mpc_tiltmax_air.get()) {
			_param_mpc_tiltmax_lnd.set(_param_mpc_tiltmax_air.get());
			_param_mpc_tiltmax_lnd.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Land tilt has been constrained by max tilt\t");
			/* EVENT
			 * @description <param>MPC_TILTMAX_LND</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_land_tilt_set"), events::Log::Warning,
					    "Land tilt limit has been constrained by maximum tilt", _param_mpc_tiltmax_air.get());
		}

		_control.setPositionGains(Vector3f(_param_indi_xy_p.get(), _param_indi_xy_p.get(), _param_mpc_z_p.get()));
		_control.setVelocityGains(
			Vector3f(_param_indi_xy_vp.get(), _param_indi_xy_vp.get(), _param_mpc_z_vel_p_acc.get()),
			Vector3f(_param_mpc_xy_vel_i_acc.get(), _param_mpc_xy_vel_i_acc.get(), _param_mpc_z_vel_i_acc.get()),
			Vector3f(_param_mpc_xy_vel_d_acc.get(), _param_mpc_xy_vel_d_acc.get(), _param_mpc_z_vel_d_acc.get()));
		_control.setHorizontalThrustMargin(_param_mpc_thr_xy_marg.get());
		_accel_control.setMeasurementDelay(_param_indi_dly.get());
		_accel_control.setBlendTimeConstant(_param_indi_tb.get());
		// bench-only loop-break excitation, rebuilt only when one of its values changed
		_injection.setParameters(_param_indi_pinj_ax.get(), _param_indi_pinj_amp.get(), _param_indi_pinj_tp.get(),
					 _param_indi_pinj_flo.get(), _param_indi_pinj_fhi.get(), _param_indi_pinj_np.get(), _param_indi_pinj_dly.get());

		float w_max = 0.f;
		_rotor_w_max = (_w_max_handle != PARAM_INVALID && param_get(_w_max_handle, &w_max) == PX4_OK
				&& PX4_ISFINITE(w_max) && w_max > 0.f) ? w_max : 0.f;
		_goto_control.setParamMpcAccHor(_param_mpc_acc_hor.get());
		_goto_control.setParamMpcAccDownMax(_param_mpc_acc_down_max.get());
		_goto_control.setParamMpcAccUpMax(_param_mpc_acc_up_max.get());
		_goto_control.setParamMpcJerkAuto(_param_mpc_jerk_auto.get());
		_goto_control.setParamMpcXyCruise(_param_mpc_xy_cruise.get());
		_goto_control.setParamMpcXyErrMax(_param_mpc_xy_err_max.get());
		_goto_control.setParamMpcXyVelMax(_param_mpc_xy_vel_max.get());
		_goto_control.setParamMpcYawrautoMax(_param_mpc_yawrauto_max.get());
		_goto_control.setParamMpcYawrautoAcc(_param_mpc_yawrauto_acc.get());
		_goto_control.setParamMpcZVAutoDn(_param_mpc_z_v_auto_dn.get());
		_goto_control.setParamMpcZVAutoUp(_param_mpc_z_v_auto_up.get());

		// Check that the design parameters are inside the absolute maximum constraints
		if (_param_mpc_xy_cruise.get() > _param_mpc_xy_vel_max.get()) {
			_param_mpc_xy_cruise.set(_param_mpc_xy_vel_max.get());
			_param_mpc_xy_cruise.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Cruise speed has been constrained by max speed\t");
			/* EVENT
			 * @description <param>MPC_XY_CRUISE</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_cruise_set"), events::Log::Warning,
					    "Cruise speed has been constrained by maximum speed", _param_mpc_xy_vel_max.get());
		}

		if (_param_mpc_vel_manual.get() > _param_mpc_xy_vel_max.get()) {
			_param_mpc_vel_manual.set(_param_mpc_xy_vel_max.get());
			_param_mpc_vel_manual.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Manual speed has been constrained by max speed\t");
			/* EVENT
			 * @description <param>MPC_VEL_MANUAL</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_man_vel_set"), events::Log::Warning,
					    "Manual speed has been constrained by maximum speed", _param_mpc_xy_vel_max.get());
		}

		if (_param_mpc_vel_man_back.get() > _param_mpc_vel_manual.get()) {
			_param_mpc_vel_man_back.set(_param_mpc_vel_manual.get());
			_param_mpc_vel_man_back.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Manual backward speed has been constrained by forward speed\t");
			/* EVENT
			 * @description <param>MPC_VEL_MAN_BACK</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_man_vel_back_set"), events::Log::Warning,
					    "Manual backward speed has been constrained by forward speed", _param_mpc_vel_manual.get());
		}

		if (_param_mpc_vel_man_side.get() > _param_mpc_vel_manual.get()) {
			_param_mpc_vel_man_side.set(_param_mpc_vel_manual.get());
			_param_mpc_vel_man_side.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Manual sideways speed has been constrained by forward speed\t");
			/* EVENT
			 * @description <param>MPC_VEL_MAN_SIDE</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_man_vel_side_set"), events::Log::Warning,
					    "Manual sideways speed has been constrained by forward speed", _param_mpc_vel_manual.get());
		}

		if (_param_mpc_z_v_auto_up.get() > _param_mpc_z_vel_max_up.get()) {
			_param_mpc_z_v_auto_up.set(_param_mpc_z_vel_max_up.get());
			_param_mpc_z_v_auto_up.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Ascent speed has been constrained by max speed\t");
			/* EVENT
			 * @description <param>MPC_Z_V_AUTO_UP</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_up_vel_set"), events::Log::Warning,
					    "Ascent speed has been constrained by max speed", _param_mpc_z_vel_max_up.get());
		}

		if (_param_mpc_z_v_auto_dn.get() > _param_mpc_z_vel_max_dn.get()) {
			_param_mpc_z_v_auto_dn.set(_param_mpc_z_vel_max_dn.get());
			_param_mpc_z_v_auto_dn.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Descent speed has been constrained by max speed\t");
			/* EVENT
			 * @description <param>MPC_Z_V_AUTO_DN</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_down_vel_set"), events::Log::Warning,
					    "Descent speed has been constrained by max speed", _param_mpc_z_vel_max_dn.get());
		}

		if (_param_mpc_thr_hover.get() > _param_mpc_thr_max.get() ||
		    _param_mpc_thr_hover.get() < _param_mpc_thr_min.get()) {
			_param_mpc_thr_hover.set(math::constrain(_param_mpc_thr_hover.get(), _param_mpc_thr_min.get(),
						 _param_mpc_thr_max.get()));
			_param_mpc_thr_hover.commit();
			mavlink_log_critical(&_mavlink_log_pub, "Hover thrust has been constrained by min/max\t");
			/* EVENT
			 * @description <param>MPC_THR_HOVER</param> is set to {1:.0}.
			 */
			events::send<float>(events::ID("mc_indi_pos_ctrl_hover_thrust_set"), events::Log::Warning,
					    "Hover thrust has been constrained by min/max thrust", _param_mpc_thr_hover.get());
		}

		if (!_hover_thrust_initialized) {
			_control.setHoverThrust(_param_mpc_thr_hover.get());
			_hover_thrust_initialized = true;
		}

		// initialize vectors from params and enforce constraints
		_param_mpc_tko_speed.set(math::min(_param_mpc_tko_speed.get(), _param_mpc_z_vel_max_up.get()));
		_param_mpc_land_speed.set(math::min(_param_mpc_land_speed.get(), _param_mpc_z_vel_max_dn.get()));

		_takeoff.setSpoolupTime(_param_com_spoolup_time.get());
		_takeoff.setTakeoffRampTime(_param_mpc_tko_ramp_t.get());
		_takeoff.generateInitialRampValue(_param_mpc_z_vel_p_acc.get());
	}
}

PositionControlStates McIndiPosControl::set_vehicle_states(const vehicle_local_position_s
		&vehicle_local_position, const float dt_s)
{
	PositionControlStates states;

	const Vector2f position_xy(vehicle_local_position.x, vehicle_local_position.y);

	// only set position states if valid and finite
	if (vehicle_local_position.xy_valid && position_xy.isAllFinite()) {
		states.position.xy() = position_xy;

	} else {
		states.position(0) = states.position(1) = NAN;
	}

	if (PX4_ISFINITE(vehicle_local_position.z) && vehicle_local_position.z_valid) {
		states.position(2) = vehicle_local_position.z;

	} else {
		states.position(2) = NAN;
	}

	const Vector2f velocity_xy(vehicle_local_position.vx, vehicle_local_position.vy);

	if (vehicle_local_position.v_xy_valid && velocity_xy.isAllFinite()) {
		const Vector2f vel_xy_prev = _vel_xy_lp_filter.getState();

		// vel xy notch filter, then low pass filter
		states.velocity.xy() = _vel_xy_lp_filter.update(_vel_xy_notch_filter.apply(velocity_xy));

		// vel xy derivative low pass filter
		states.acceleration.xy() = _vel_deriv_xy_lp_filter.update((_vel_xy_lp_filter.getState() - vel_xy_prev) / dt_s);

	} else {
		states.velocity(0) = states.velocity(1) = NAN;
		states.acceleration(0) = states.acceleration(1) = NAN;

		// reset filters to prevent acceleration spikes when regaining velocity
		_vel_xy_lp_filter.reset({});
		_vel_xy_notch_filter.reset();
		_vel_deriv_xy_lp_filter.reset({});
	}

	if (PX4_ISFINITE(vehicle_local_position.vz) && vehicle_local_position.v_z_valid) {

		const float vel_z_prev = _vel_z_lp_filter.getState();

		// vel z notch filter, then low pass filter
		states.velocity(2) = _vel_z_lp_filter.update(_vel_z_notch_filter.apply(vehicle_local_position.vz));

		// vel z derivative low pass filter
		states.acceleration(2) = _vel_deriv_z_lp_filter.update((_vel_z_lp_filter.getState() - vel_z_prev) / dt_s);

	} else {
		states.velocity(2) = NAN;
		states.acceleration(2) = NAN;

		// reset filters to prevent acceleration spikes when regaining velocity
		_vel_z_lp_filter.reset({});
		_vel_z_notch_filter.reset();
		_vel_deriv_z_lp_filter.reset({});
	}

	states.yaw = vehicle_local_position.heading;

	return states;
}

void McIndiPosControl::Run()
{
	if (should_exit()) {
		_local_pos_sub.unregisterCallback();
		_acceleration_sub.unregisterCallback();
		exit_and_cleanup(desc);
		return;
	}

	// reschedule backup
	ScheduleDelayed(100_ms);

	parameters_update(false);

	pollAcceleration(); // every wakeup (vehicle_acceleration or local position): no force sample is skipped

	perf_begin(_cycle_perf);
	vehicle_local_position_s vehicle_local_position;

	if (_local_pos_sub.update(&vehicle_local_position)) {
		const float raw_dt = (vehicle_local_position.timestamp_sample - _time_stamp_last_loop) * 1e-6f; // true interval for the INDI loop
		const float dt = math::constrain(raw_dt, kStageDtMin, 0.04f); // stock-style consumers keep the clamp
		_time_stamp_last_loop = vehicle_local_position.timestamp_sample;

		_sample_interval_s.update(dt);

		if (_vehicle_control_mode_sub.updated()) {
			const vehicle_control_mode_s previous = _vehicle_control_mode;

			if (_vehicle_control_mode_sub.copy(&_vehicle_control_mode)) {
				if (shouldResetStageState(previous.flag_armed, _vehicle_control_mode.flag_armed)) {
					resetStageState();
				}

				if (previous.flag_armed && !_vehicle_control_mode.flag_armed) {
					_injection.reset(); // the INDI loop does not run disarmed: the disarm edge restarts the bench window for the next arm
				}

				if (!previous.flag_multicopter_position_control_enabled && _vehicle_control_mode.flag_multicopter_position_control_enabled) {
					_time_position_control_enabled = _vehicle_control_mode.timestamp;
					_pos_entry_pending = shouldResetOnPosControlEntry(previous.flag_multicopter_position_control_enabled, true);

				} else if (previous.flag_multicopter_position_control_enabled && !_vehicle_control_mode.flag_multicopter_position_control_enabled) {
					// clear existing setpoint when controller is no longer active
					_setpoint = PositionControl::empty_trajectory_setpoint;
					_control.setInputSetpoint(_setpoint);
				}

				// Restart the decaying velocity limits when the controlled axes change e.g. altitude to position or VTOL back transition
				if ((previous.flag_multicopter_position_control_enabled != _vehicle_control_mode.flag_multicopter_position_control_enabled)
				    || (previous.flag_control_velocity_enabled != _vehicle_control_mode.flag_control_velocity_enabled)
				    || (previous.flag_control_climb_rate_enabled != _vehicle_control_mode.flag_control_climb_rate_enabled)) {
					_vel_limit_xy = NAN;
					_vel_limit_up = NAN;
					_vel_limit_down = NAN;
					_time_vel_limit_reset = _vehicle_control_mode.timestamp;
				}
			}
		}

		_vehicle_land_detected_sub.update(&_vehicle_land_detected);

		if (_hover_thrust_estimate_sub.updated()) {
			hover_thrust_estimate_s hte;

			if (_hover_thrust_estimate_sub.copy(&hte)) {
				// the hover thrust never enters the PositionControl integrator
				_hte_valid = hte.valid && PX4_ISFINITE(hte.hover_thrust);
				_hte = hte.hover_thrust;
			}
		}

		PositionControlStates states{set_vehicle_states(vehicle_local_position, dt)};

		// If a goto setpoint is available this publishes a trajectory setpoint to go there
		// If trajectory_setpoint is published elsewhere, do not use the goto setpoint
		const bool goto_setpoint_enable = _vehicle_control_mode.flag_multicopter_position_control_enabled
						  && !_trajectory_setpoint_sub.updated();

		if (_goto_control.checkForSetpoint(vehicle_local_position.timestamp_sample, goto_setpoint_enable)) {
			_goto_control.update(dt, states.position, states.velocity, states.acceleration, states.yaw);
		}

		_trajectory_setpoint_sub.update(&_setpoint);

		adjustSetpointForEKFResets(vehicle_local_position, _setpoint, _last_valid_setpoint);

		// any estimator reset is a step for the loop's acceleration/jerk differencing: reset it once (runIndiStage)
		EkfResetCounters reset_counters;
		reset_counters.xy = vehicle_local_position.xy_reset_counter;
		reset_counters.z = vehicle_local_position.z_reset_counter;
		reset_counters.vxy = vehicle_local_position.vxy_reset_counter;
		reset_counters.vz = vehicle_local_position.vz_reset_counter;
		reset_counters.heading = vehicle_local_position.heading_reset_counter;

		if (_indi_reset_detector.update(reset_counters)) {
			_indi_jerk_reset_pending = true;
		}

		if (_vehicle_control_mode.flag_multicopter_position_control_enabled) {
			// set failsafe setpoint if there hasn't been a new
			// trajectory setpoint since position control started
			if ((_setpoint.timestamp < _time_position_control_enabled)
			    && (vehicle_local_position.timestamp_sample > _time_position_control_enabled)) {

				_setpoint = generateFailsafeSetpoint(vehicle_local_position.timestamp_sample, states, false);
			}
		}

		if (_vehicle_control_mode.flag_multicopter_position_control_enabled
		    && (_setpoint.timestamp >= _time_position_control_enabled)) {

			// update vehicle constraints and handle smooth takeoff
			_vehicle_constraints_sub.update(&_vehicle_constraints);

			// fix to prevent the takeoff ramp to ramp to a too high value or get stuck because of NAN
			// TODO: this should get obsolete once the takeoff limiting moves into the flight tasks
			if (!PX4_ISFINITE(_vehicle_constraints.speed_up) || (_vehicle_constraints.speed_up > _param_mpc_z_vel_max_up.get())) {
				_vehicle_constraints.speed_up = _param_mpc_z_vel_max_up.get();
			}

			if (_vehicle_control_mode.flag_control_offboard_enabled) {

				const bool want_takeoff = _vehicle_control_mode.flag_armed
							  && (vehicle_local_position.timestamp_sample < _setpoint.timestamp + 1_s);

				if (want_takeoff && PX4_ISFINITE(_setpoint.position[2])
				    && (_setpoint.position[2] < states.position(2))) {

					_vehicle_constraints.want_takeoff = true;

				} else if (want_takeoff && PX4_ISFINITE(_setpoint.velocity[2])
					   && (_setpoint.velocity[2] < 0.f)) {

					_vehicle_constraints.want_takeoff = true;

				} else if (want_takeoff && PX4_ISFINITE(_setpoint.acceleration[2])
					   && (_setpoint.acceleration[2] < 0.f)) {

					_vehicle_constraints.want_takeoff = true;

				} else {
					_vehicle_constraints.want_takeoff = false;
				}

				// override with defaults
				_vehicle_constraints.speed_up = _param_mpc_z_vel_max_up.get();
				_vehicle_constraints.speed_down = _param_mpc_z_vel_max_dn.get();
			}

			bool skip_takeoff = _param_com_throw_en.get();
			// handle smooth takeoff
			_takeoff.updateTakeoffState(_vehicle_control_mode.flag_armed, _vehicle_land_detected.landed,
						    _vehicle_constraints.want_takeoff,
						    _vehicle_constraints.speed_up, skip_takeoff, vehicle_local_position.timestamp_sample);

			const bool not_taken_off             = (_takeoff.getTakeoffState() < TakeoffState::rampup);
			const bool flying                    = (_takeoff.getTakeoffState() >= TakeoffState::flight);
			const bool flying_but_ground_contact = (flying && _vehicle_land_detected.ground_contact);

			// Same condition as the [0, 0, 100] idle setpoint below: coupled, it points body_z down
			// and limitTilt commands full tilt
			_control.decoupleHorizontalAndVecticalAcceleration(_param_mpc_acc_decouple.get() || not_taken_off || flying_but_ground_contact);

			const float ht = (flying && _hte_valid) ? _hte : _param_mpc_thr_hover.get();
			// the stock integrator never integrates while armed here, so no integrator shift
			_control.setHoverThrust(ht);

			// make sure takeoff ramp is not amended by acceleration feed-forward
			if (_takeoff.getTakeoffState() == TakeoffState::rampup && PX4_ISFINITE(_setpoint.velocity[2])) {
				_setpoint.acceleration[2] = NAN;
			}

			if (not_taken_off || flying_but_ground_contact) {
				// we are not flying yet and need to avoid any corrections
				_setpoint = PositionControl::empty_trajectory_setpoint;
				_setpoint.timestamp = vehicle_local_position.timestamp_sample;
				Vector3f(0.f, 0.f, 100.f).copyTo(_setpoint.acceleration); // High downwards acceleration to make sure there's no thrust

				// prevent any integrator windup
				_control.resetIntegral();
			}

			// limit tilt during takeoff ramupup
			const float tilt_limit_deg = (_takeoff.getTakeoffState() < TakeoffState::flight)
						     ? _param_mpc_tiltmax_lnd.get() : _param_mpc_tiltmax_air.get();
			_control.setTiltLimit(_tilt_limit_slew_rate.update(math::radians(tilt_limit_deg), dt));

			const float speed_up = PX4_ISFINITE(_vehicle_constraints.speed_up) ? _vehicle_constraints.speed_up : _param_mpc_z_vel_max_up.get();
			const float speed_down = PX4_ISFINITE(_vehicle_constraints.speed_down) ? _vehicle_constraints.speed_down : _param_mpc_z_vel_max_dn.get();

			// Allow ramping from zero thrust on takeoff
			const float minimum_thrust = flying ? _param_mpc_thr_min.get() : 0.f;
			_control.setThrustLimits(minimum_thrust, _param_mpc_thr_max.get());

			float max_speed_xy = _param_mpc_xy_vel_max.get();

			if (PX4_ISFINITE(vehicle_local_position.vxy_max)) {
				max_speed_xy = math::min(max_speed_xy, vehicle_local_position.vxy_max);
			}

			float limit_speed_up = math::min(speed_up, _param_mpc_z_vel_max_up.get());
			float limit_speed_down = math::max(speed_down, 0.f);

			// When changing mode flying faster than the limit, allow braking with a decaying limit to
			// avoid a large velocity error from clamping alone driving the integrator against the brake.
			// The limit starts at the measured speed, holds while the jerk limited braking builds up and then
			// ramps down open loop, so it doesn't interfere with the brake but is guaranteed to reach the configured limit.
			const auto decayingLimit = [&](float & ramp, float measured_speed, float limit) {
				if (PX4_ISFINITE(ramp)) {
					if (vehicle_local_position.timestamp_sample > _time_vel_limit_reset + 1_s) {
						ramp = math::max(ramp - 5.f * dt, 0.f);
					}

				} else {
					ramp = PX4_ISFINITE(measured_speed) ? math::max(measured_speed, 0.f) : 0.f;
				}

				return math::max(limit, ramp);
			};

			const Vector2f velocity_xy(states.velocity);
			max_speed_xy = decayingLimit(_vel_limit_xy, velocity_xy.norm(), max_speed_xy);
			limit_speed_up = decayingLimit(_vel_limit_up, -states.velocity(2), limit_speed_up);
			limit_speed_down = decayingLimit(_vel_limit_down, states.velocity(2), limit_speed_down);

			limit_speed_up = _takeoff.updateRamp(dt, limit_speed_up); // Takeoff ramp goes last to not be overridden

			_control.setVelocityLimits(max_speed_xy, limit_speed_up, limit_speed_down);

			// extrapolate a copy of the held sample between sender samples (the stored sample stays untouched)
			_control.setInputSetpoint(extrapolateSetpoint(_setpoint, hrt_absolute_time(), TRAJECTORY_STREAM_TIMEOUT_US));

			// update states
			if (!PX4_ISFINITE(_setpoint.position[2])
			    && PX4_ISFINITE(_setpoint.velocity[2]) && (fabsf(_setpoint.velocity[2]) > FLT_EPSILON)
			    && PX4_ISFINITE(vehicle_local_position.z_deriv) && vehicle_local_position.z_valid && vehicle_local_position.v_z_valid) {
				// A change in velocity is demanded and the altitude is not controlled.
				// Set velocity to the derivative of position
				// because it has less bias but blend it in across the landing speed range
				//  <  MPC_LAND_SPEED: ramp up using altitude derivative without a step
				//  >= MPC_LAND_SPEED: use altitude derivative
				float weighting = fminf(fabsf(_setpoint.velocity[2]) / _param_mpc_land_speed.get(), 1.f);
				states.velocity(2) = vehicle_local_position.z_deriv * weighting + vehicle_local_position.vz * (1.f - weighting);
			}

			if ((!PX4_ISFINITE(_setpoint.velocity[0]) || !PX4_ISFINITE(_setpoint.velocity[1]))
			    && (!PX4_ISFINITE(_setpoint.position[0]) || !PX4_ISFINITE(_setpoint.position[1]))) {
				// Horizontal velocity is not controlled, reset the integrators to avoid
				// over-corrections when starting again.
				_control.resetIntegralXY();
			}

			const bool want_indi = computeWantIndi(_vehicle_control_mode.flag_armed,
							       _vehicle_control_mode.flag_control_position_enabled,
							       _vehicle_control_mode.flag_control_velocity_enabled,
							       _vehicle_control_mode.flag_control_climb_rate_enabled);
			// modelled specific force on ground and during the ramp, measured from flight without contact
			const bool model_force = useModelledForce(_takeoff.getTakeoffState() >= TakeoffState::flight,
						 _vehicle_land_detected.ground_contact, _vehicle_land_detected.maybe_landed);

			const hrt_abstime now = hrt_absolute_time();
			pollStageInputs();

			// reference acceleration = feed-forward + P/D whenever armed in these modes, whatever the
			// freshness of its inputs and the takeoff state: the stock integrator never integrates
			if (want_indi) {
				_control.resetIntegral();
			}

			_control.setState(states);

			// Run position control
			if (_control.update(dt)) {

				// Valid control update - store for the stock failsafe-setpoint timeout path
				_last_valid_setpoint = _setpoint;

			} else {

				// Initial update failed - Try fallback if within timeout
				if (now < _last_valid_setpoint.timestamp + 200_ms) {
					// Already moved into the current estimate frame by adjustSetpointForEKFResets()
					_control.setInputSetpoint(_last_valid_setpoint);
				}

				// Still failing / not within timeout - Go to failsafe
				if (!_control.update(dt)) {

					_vehicle_constraints = {0, NAN, NAN, false, {}}; // reset constraints

					_control.setInputSetpoint(generateFailsafeSetpoint(vehicle_local_position.timestamp_sample, states, true));
					_control.setVelocityLimits(_param_mpc_xy_vel_max.get(), _param_mpc_z_vel_max_up.get(), _param_mpc_z_vel_max_dn.get());

					_control.update(dt);
				}
			}

			vehicle_local_position_setpoint_s local_pos_sp{};
			_control.getLocalPositionSetpoint(local_pos_sp);
			vehicle_attitude_setpoint_s attitude_setpoint{};
			_control.getAttitudeSetpoint(attitude_setpoint);

			// the trajectory setpoint the position controller used as feed-forward (after the takeoff and
			// failsafe edits above). The jerk is differenced from it inside runIndiStage.
			_accel_feedforward_mps2 = matrix::Vector3f(_setpoint.acceleration);

			runIndiStage(raw_dt, now, want_indi, model_force, flying, _tilt_limit_slew_rate.getState(), ht, local_pos_sp, attitude_setpoint);

			// zero the stock integrator only on cycles where the INDI loop actually ran (this cycle)
			if (_indi_active) {
				_control.resetIntegral();
			}

			// Publish internal position control setpoints
			// on top of the input/feed-forward setpoints these containt the PID corrections
			// This message is used by other modules (such as Landdetector) to determine vehicle intention.
			local_pos_sp.timestamp = hrt_absolute_time();
			_local_pos_sp_pub.publish(local_pos_sp);

			// Publish attitude setpoint output
			attitude_setpoint.timestamp = hrt_absolute_time();
			_vehicle_attitude_setpoint_pub.publish(attitude_setpoint);

			// rate feed-forward belonging to this attitude setpoint (invalid unless the INDI loop ran)
			indi_rate_feedforward_s rate_ff{};
			rate_ff.timestamp = attitude_setpoint.timestamp;
			rate_ff.valid = _omega_ff_valid;

			if (_omega_ff_valid) {
				_omega_ff_out.copyTo(rate_ff.omega_ff);
			}

			_indi_rate_ff_pub.publish(rate_ff);

		} else {
			// an update is necessary here because otherwise the takeoff state doesn't get skipped with non-altitude-controlled modes
			_takeoff.updateTakeoffState(_vehicle_control_mode.flag_armed, _vehicle_land_detected.landed, false, 10.f, true,
						    vehicle_local_position.timestamp_sample);
			_control.resetIntegral();
		}

		// Publish takeoff status
		const uint8_t takeoff_state = static_cast<uint8_t>(_takeoff.getTakeoffState());

		if (takeoff_state != _takeoff_status_pub.get().takeoff_state
		    || !isEqualF(_tilt_limit_slew_rate.getState(), _takeoff_status_pub.get().tilt_limit)) {
			_takeoff_status_pub.get().takeoff_state = takeoff_state;
			_takeoff_status_pub.get().tilt_limit = _tilt_limit_slew_rate.getState();
			_takeoff_status_pub.get().timestamp = hrt_absolute_time();
			_takeoff_status_pub.update();
		}
	}

	perf_end(_cycle_perf);
}

trajectory_setpoint_s McIndiPosControl::generateFailsafeSetpoint(const hrt_abstime &now,
		const PositionControlStates &states, bool warn)
{
	// rate limit the warnings
	warn = warn && (now - _last_warn) > 2_s;

	if (warn) {
		PX4_WARN("invalid setpoints");
		_last_warn = now;
	}

	FailsafeInfo info;
	const trajectory_setpoint_s failsafe_setpoint = computeFailsafeSetpoint(now, Vector3f(states.velocity),
			_param_mpc_land_speed.get(), &info);

	if (warn) {
		if (info.stop_and_wait) { PX4_WARN("Failsafe: stop and wait"); }

		if (info.blind_land) { PX4_WARN("Failsafe: blind land"); }

		if (info.blind_descent) { PX4_WARN("Failsafe: blind descent"); }
	}

	return failsafe_setpoint;
}

void McIndiPosControl::adjustSetpointForEKFResets(const vehicle_local_position_s &vehicle_local_position,
		trajectory_setpoint_s &setpoint, trajectory_setpoint_s &fallback_setpoint)
{
	auto apply_reset_deltas = [&](trajectory_setpoint_s & setpoint_to_adjust) {
		if ((setpoint_to_adjust.timestamp != 0) && (setpoint_to_adjust.timestamp < vehicle_local_position.timestamp)) {
			if (vehicle_local_position.xy_reset_counter != _xy_reset_counter) {
				setpoint_to_adjust.position[0] += vehicle_local_position.delta_xy[0];
				setpoint_to_adjust.position[1] += vehicle_local_position.delta_xy[1];
			}

			if (vehicle_local_position.z_reset_counter != _z_reset_counter) {
				setpoint_to_adjust.position[2] += vehicle_local_position.delta_z;
			}

			if (vehicle_local_position.vxy_reset_counter != _vxy_reset_counter) {
				setpoint_to_adjust.velocity[0] += vehicle_local_position.delta_vxy[0];
				setpoint_to_adjust.velocity[1] += vehicle_local_position.delta_vxy[1];
			}

			if (vehicle_local_position.vz_reset_counter != _vz_reset_counter) {
				setpoint_to_adjust.velocity[2] += vehicle_local_position.delta_vz;
			}

			if (vehicle_local_position.heading_reset_counter != _heading_reset_counter) {
				setpoint_to_adjust.yaw = wrap_pi(setpoint_to_adjust.yaw + vehicle_local_position.delta_heading);
			}
		}
	};

	apply_reset_deltas(setpoint);

	// The counters are latched below, so a later call would find nothing changed and leave the
	// stored fallback in the pre-reset frame.
	apply_reset_deltas(fallback_setpoint);

	if (vehicle_local_position.xy_reset_counter != _xy_reset_counter) {
		_goto_control.ekfResetHandlerPosition(Vector3f(vehicle_local_position.x, vehicle_local_position.y, NAN));
		_xy_reset_counter = vehicle_local_position.xy_reset_counter;
	}

	if (vehicle_local_position.z_reset_counter != _z_reset_counter) {
		_goto_control.ekfResetHandlerPosition(Vector3f(NAN, NAN, vehicle_local_position.z));
		_z_reset_counter = vehicle_local_position.z_reset_counter;
	}

	if (vehicle_local_position.vxy_reset_counter != _vxy_reset_counter) {
		_vel_xy_lp_filter.reset(_vel_xy_lp_filter.getState() + Vector2f(vehicle_local_position.delta_vxy));
		_vel_xy_notch_filter.reset();
		_goto_control.ekfResetHandlerVelocity(Vector3f(vehicle_local_position.vx, vehicle_local_position.vy, NAN));
		_vxy_reset_counter = vehicle_local_position.vxy_reset_counter;
	}

	if (vehicle_local_position.vz_reset_counter != _vz_reset_counter) {
		_vel_z_lp_filter.reset(_vel_z_lp_filter.getState() + vehicle_local_position.delta_vz);
		_vel_z_notch_filter.reset();
		_goto_control.ekfResetHandlerVelocity(Vector3f(NAN, NAN, vehicle_local_position.vz));
		_vz_reset_counter = vehicle_local_position.vz_reset_counter;
	}

	if (vehicle_local_position.heading_reset_counter != _heading_reset_counter) {
		_goto_control.ekfResetHandlerHeading(vehicle_local_position.delta_heading);
		_heading_reset_counter = vehicle_local_position.heading_reset_counter;
	}
}

int McIndiPosControl::task_spawn(int argc, char *argv[])
{
	bool vtol = false;

	if (argc > 1) {
		if (strcmp(argv[1], "vtol") == 0) {
			vtol = true;
		}
	}

	McIndiPosControl *instance = new McIndiPosControl(vtol);

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
The controller has two loops: a P loop for position error and a PID loop for velocity error.
Output of the velocity controller is thrust vector that is split to thrust direction
(i.e. rotation matrix for multicopter orientation) and thrust scalar (i.e. multicopter thrust itself).

The controller doesn't use Euler angles for its work, they are generated only for more human-friendly control and
logging.
)DESCR_STR");

	PRINT_MODULE_USAGE_NAME("mc_indi_pos_control", "controller");
	PRINT_MODULE_USAGE_COMMAND("start");
	PRINT_MODULE_USAGE_ARG("vtol", "VTOL mode", true);
	PRINT_MODULE_USAGE_DEFAULT_COMMANDS();

	return 0;
}

extern "C" __EXPORT int mc_indi_pos_control_main(int argc, char *argv[])
{
	return ModuleBase::main(McIndiPosControl::desc, argc, argv);
}
