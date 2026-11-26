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

/**
 * @file indi_rate_control.cpp
 */

#include "indi_rate_control.hpp"

#include <float.h>

#include <px4_platform_common/defines.h>

using namespace matrix;

void IndiRateControl::setActuatorTimeConstant(float actuator_tc)
{
	// a non finite value falls back to the default instead of poisoning the actuator model
	_actuator_tc = math::isFinite(actuator_tc) ? math::constrain(actuator_tc, 0.001f, 0.2f) : 0.02f;
}

void IndiRateControl::setActuatorBlendTimeConstant(float blend_tc_s)
{
	// non positive and non finite values disable the blend, stored as 0
	_blend_tc = (math::isFinite(blend_tc_s) && (blend_tc_s > 0.f)) ? math::min(blend_tc_s, kMaxBlendTimeConstant) : 0.f;
}

void IndiRateControl::setFilterCutoffs(float gyro_cutoff_hz, float dgyro_cutoff_hz)
{
	// non positive and non finite cutoffs mean pass-through, stored as 0
	_gyro_cutoff_hz = (math::isFinite(gyro_cutoff_hz) && (gyro_cutoff_hz > 0.f)) ? gyro_cutoff_hz : 0.f;
	_dgyro_cutoff_hz = (math::isFinite(dgyro_cutoff_hz) && (dgyro_cutoff_hz > 0.f)) ? dgyro_cutoff_hz : 0.f;
}

bool IndiRateControl::paramsValid() const
{
	for (int i = 0; i < 3; i++) {
		// written so that NaN fails the comparison
		if (!(_g1(i) >= kMinG1) || !PX4_ISFINITE(_g1(i))) {
			return false;
		}

		if (!(_rate_bandwidth_gain(i) >= 0.f) || !PX4_ISFINITE(_rate_bandwidth_gain(i))) {
			return false;
		}
	}

	return true;
}

void IndiRateControl::designSyncFilters(float sample_freq, bool reset_states)
{
	for (int i = 0; i < 3; i++) {
		// LowPassFilter2p disables itself (pass-through) for a cutoff <= 0 or >= Nyquist
		_lpf[i].set_cutoff_frequency(sample_freq, _gyro_cutoff_hz);

		if (!_alpha[i].setCutoffFreq(sample_freq, _dgyro_cutoff_hz)) {
			_alpha[i].setAlpha(1.f); // pass-through, the default alpha of 0 would freeze the output
		}

		// a cutoff change settles the filters at the current modelled torque; on a sample rate change the
		// low pass restarts from its last output (its setter zeroes the states) and the alpha filter keeps its
		// state, resetting t_f to the model state would drop its group delay while a_f keeps it
		// the measurement path uses the identical design and the same reset rule
		_meas_lpf[i].set_cutoff_frequency(sample_freq, _gyro_cutoff_hz);

		if (!_meas_alpha[i].setCutoffFreq(sample_freq, _dgyro_cutoff_hz)) {
			_meas_alpha[i].setAlpha(1.f);
		}

		if (reset_states) {
			_lpf[i].reset(_torque_actuator_model(i));
			_alpha[i].reset(_torque_actuator_model(i));
			_meas_lpf[i].reset(_torque_actuator_model(i));
			_meas_alpha[i].reset(_torque_actuator_model(i));

		} else {
			_lpf[i].reset(_torque_lowpass_state(i));
			_meas_lpf[i].reset(_meas_t_lpf(i));
		}
	}

	_design_sample_freq = sample_freq;
	_design_gyro_cutoff_hz = _gyro_cutoff_hz;
	_design_dgyro_cutoff_hz = _dgyro_cutoff_hz;
}

void IndiRateControl::designYawFilters(float sample_freq)
{
	// the yaw low pass is bypassed (not just pass-through) when disabled, so the outputs are unchanged
	_yaw_filter_active = (_yaw_cutoff_hz > 0.f) && (_yaw_cutoff_hz < kMaxYawCutoffRatio * sample_freq);

	if (_yaw_filter_active) {
		_yaw_lpf_accel.set_cutoff_frequency(sample_freq, _yaw_cutoff_hz);
		_yaw_lpf_torque.set_cutoff_frequency(sample_freq, _yaw_cutoff_hz);
		_yaw_error_lpf.set_cutoff_frequency(sample_freq, _yaw_cutoff_hz);
		_yaw_sp_lpf.set_cutoff_frequency(sample_freq, _yaw_cutoff_hz);
	}

	// settled at the next unfiltered values, in update()
	_yaw_filter_reset_pending = _yaw_filter_active;

	// the yaw setpoint entering the derivative switches between raw and filtered: restart the derivative
	_sp_lead_reset = true;
	_design_yaw_cutoff_hz = _yaw_cutoff_hz;
}

void IndiRateControl::resetStates()
{
	_torque_actuator_model.zero();
	_torque_lowpass_state.zero();

	for (int i = 0; i < kDelayBufferSize; i++) {
		_t_delay_buffer[i].zero();
	}

	_delay_head = 0;
	_delay_samples = _delay_samples_target;

	for (int i = 0; i < 3; i++) {
		_lpf[i].reset(0.f);
		_alpha[i].reset(0.f);
	}

	// measurement path, and back to the model until kMeasValidCycles valid cycles have been seen again
	_meas_t_lpf.zero();

	for (int i = 0; i < kDelayBufferSize; i++) {
		_meas_delay_buffer[i].zero();
	}

	_meas_delay_head = 0;
	_meas_delay_samples = _meas_delay_samples_target;

	for (int i = 0; i < 3; i++) {
		_meas_lpf[i].reset(0.f);
		_meas_alpha[i].reset(0.f);
	}

	_meas_valid_cycles = 0;
	_meas_in_use = false;

	_yaw_lpf_accel.reset(0.f);
	_yaw_lpf_torque.reset(0.f);
	_yaw_error_lpf.reset(0.f);
	_yaw_sp_lpf.reset(0.f);
	// restart the yaw filters from the next input, not from zero, which would scale the yaw path by the
	// filter's feed-through gain on every cycle that resets the states (landed, fault recovery)
	_yaw_filter_reset_pending = true;
	_yaw_inc_prev = 0.f;
	_blend.zero();
	_t_fb_prev.zero();
	_landed_ramp = false;
}

void IndiRateControl::reset()
{
	resetStates();
	_nu.zero();
	_a_f.zero();
	_lead_gain.zero();
	_t_f.zero();
	_t_f_model.zero();
	_t_f_meas.zero();
	_torque_increment.zero();
	_t_cmd_last.zero();
	_rate_sp_dot.zero();
	_rate_sp_prev.zero();
	_sp_lead_reset = true;
}

Vector3f IndiRateControl::faultOutput(const bool states_corrupted)
{
	_fault = true;
	// no derivative across a rejected cycle
	_sp_lead_reset = true;
	_rate_sp_dot.zero();

	if (states_corrupted) {
		resetStates();
	}

	// a single bad sample holds the last command instead of becoming a zero-torque cycle and a from-zero restart
	if (_fault_cycles < kFaultHoldCycles) {
		_fault_cycles++;
		return _t_cmd_last;
	}

	reset();
	return Vector3f();
}

Vector3f IndiRateControl::update(const Vector3f &rate, const Vector3f &rate_sp, const Vector3f &angular_accel,
				 const Vector3f &torque_allocated_prev, const float dt, const bool landed, const bool maybe_landed)
{
	// the measurement validity is valid for this call only, whatever happens below; a non finite torque is invalid
	const bool meas_valid = _meas_valid_pending && _tau_meas.isAllFinite();
	_meas_valid_pending = false;

	// validate inputs and parameters, a rejected cycle leaves the states untouched
	const bool dt_valid = math::isFinite(dt) && (dt >= kMinDt) && (dt <= kMaxDt);
	const bool inputs_valid = rate.isAllFinite() && rate_sp.isAllFinite() && angular_accel.isAllFinite()
				  && torque_allocated_prev.isAllFinite();

	if (!dt_valid || !inputs_valid || !paramsValid() || !math::isFinite(_g2_yaw)) {
		// the measurement was not processed this cycle, so it does not count as valid
		_meas_valid_cycles = 0;
		_meas_in_use = false;
		return faultOutput(false);
	}

	// (re)design the synchronisation filters on a low-passed sample rate, as the gyro chain designs on its
	// nominal rate: a jittery dt must neither trigger a redesign nor reset the feedback pair
	const float sample_freq = 1.f / dt;
	_sample_freq_filtered = (_sample_freq_filtered > 0.f)
				? _sample_freq_filtered + kSampleFreqAlpha * (sample_freq - _sample_freq_filtered) : sample_freq;

	const bool cutoffs_changed = (_design_sample_freq <= 0.f)
				     || (fabsf(_gyro_cutoff_hz - _design_gyro_cutoff_hz) > FLT_EPSILON)
				     || (fabsf(_dgyro_cutoff_hz - _design_dgyro_cutoff_hz) > FLT_EPSILON);
	const bool rate_changed = fabsf(_sample_freq_filtered - _design_sample_freq) > kRedesignRatio * _design_sample_freq;

	if (cutoffs_changed || rate_changed) {
		designSyncFilters(_sample_freq_filtered, cutoffs_changed);
		designYawFilters(_sample_freq_filtered);

	} else if (fabsf(_yaw_cutoff_hz - _design_yaw_cutoff_hz) > FLT_EPSILON) {
		// a yaw cutoff change leaves the roll/pitch/yaw synchronisation filters H untouched
		designYawFilters(_design_sample_freq);
	}

	// actuator model, the allocated torque is normalised so bound it to guard the filter against overflow.
	// This also runs while landed, so that the modelled torque follows the torque actually applied and its
	// filter chain stays synchronised with the gyro derivative chain, which runs on every cycle
	Vector3f t_alloc;

	for (int i = 0; i < 3; i++) {
		t_alloc(i) = math::constrain(torque_allocated_prev(i), -1.f, 1.f);
	}

	const float actuator_alpha = 1.f - expf(-dt / _actuator_tc);
	_torque_actuator_model += actuator_alpha * (t_alloc - _torque_actuator_model);

	// delay: ring buffer, _delay_head holds the newest sample. A delay change moves one sample per cycle: up
	// holds t_del for a cycle, down skips one sample
	if (_delay_samples < _delay_samples_target) {
		_delay_samples++;

	} else if (_delay_samples > _delay_samples_target) {
		_delay_samples--;
	}

	_delay_head = (_delay_head + 1) % kDelayBufferSize;
	_t_delay_buffer[_delay_head] = _torque_actuator_model;
	const int delay_index = (_delay_head + kDelayBufferSize - _delay_samples) % kDelayBufferSize;
	const Vector3f t_del = _t_delay_buffer[delay_index];

	// synchronisation filter H, same order as the gyro derivative chain: LPF2p then alpha filter
	Vector3f t_f_model;

	for (int i = 0; i < 3; i++) {
		_torque_lowpass_state(i) = _lpf[i].apply(t_del(i));
		t_f_model(i) = _alpha[i].update(_torque_lowpass_state(i));
	}

	// measurement path, same steps on the measured torque. While it is invalid it is fed the modelled
	// torque so that its filters stay near the right value and the return to the measurement is bumpless
	Vector3f t_meas_in = _torque_actuator_model;

	if (meas_valid) {
		for (int i = 0; i < 3; i++) {
			t_meas_in(i) = math::constrain(_tau_meas(i), -1.f, 1.f);
		}
	}

	if (_meas_delay_samples < _meas_delay_samples_target) {
		_meas_delay_samples++;

	} else if (_meas_delay_samples > _meas_delay_samples_target) {
		_meas_delay_samples--;
	}

	_meas_delay_head = (_meas_delay_head + 1) % kDelayBufferSize;
	_meas_delay_buffer[_meas_delay_head] = t_meas_in;
	const int meas_delay_index = (_meas_delay_head + kDelayBufferSize - _meas_delay_samples) % kDelayBufferSize;
	const Vector3f t_meas_del = _meas_delay_buffer[meas_delay_index];

	Vector3f t_f_meas;

	for (int i = 0; i < 3; i++) {
		_meas_t_lpf(i) = _meas_lpf[i].apply(t_meas_del(i));
		t_f_meas(i) = _meas_alpha[i].update(_meas_t_lpf(i));
	}

	// source selection: the measurement only after kMeasValidCycles consecutive valid cycles, any invalid cycle
	// drops back to the model at once. No per axis mixing, model and measurement differ in lag and units
	_meas_valid_cycles = meas_valid ? math::min(_meas_valid_cycles + 1, kMeasValidCycles) : 0;
	_meas_in_use = (_meas_valid_cycles >= kMeasValidCycles);
	Vector3f t_f = t_f_model;

	// complementary blend: the measurement carries the high frequencies, the model the low ones, so a steady gap
	// between command and output keeps its integral action. It tracks the difference (bumpless) while the
	// measurement is not in use, the blend is disabled or on ground
	const Vector3f t_gap = t_f_model - t_f_meas;

	if (_meas_in_use && (_blend_tc > 0.f) && !landed) {
		// maybe_landed holds the slow integrator only, the rest of the law keeps running
		if (!maybe_landed) {
			const float blend_alpha = dt / (_blend_tc + dt);
			_blend += blend_alpha * (t_gap - _blend);
		}

	} else {
		_blend = t_gap;
	}

	for (int i = 0; i < 3; i++) {
		if (!PX4_ISFINITE(_blend(i))) {
			_blend(i) = PX4_ISFINITE(t_gap(i)) ? t_gap(i) : 0.f;
		}

		_blend(i) = math::constrain(_blend(i), -kMaxBlend, kMaxBlend);
	}

	if (_meas_in_use) {
		t_f = (_blend_tc > 0.f) ? (t_f_meas + _blend) : t_f_meas;
	}

	if (landed) {
		// restart the yaw filters from the current values each landed cycle (bypassed on ground)
		_yaw_filter_reset_pending = true;
	}

	// optional yaw low pass on both members of the feedback pair, same coefficients so they stay synchronised
	Vector3f a_f = angular_accel;
	// rate error used in nu, its yaw component (setpoint included) is filtered like the feedback pair, as the PID
	// yaw torque output filter does for the whole yaw command
	Vector3f rate_error = rate_sp - rate;

	if (_yaw_filter_active) {
		if (_yaw_filter_reset_pending) {
			// enabled or redesigned: start from the current values, no transient
			_yaw_lpf_accel.reset(a_f(2));
			_yaw_lpf_torque.reset(t_f(2));
			_yaw_error_lpf.reset(rate_error(2));
			_yaw_sp_lpf.reset(rate_sp(2));
			_yaw_filter_reset_pending = false;
		}

		a_f(2) = _yaw_lpf_accel.apply(a_f(2));
		t_f(2) = _yaw_lpf_torque.apply(t_f(2));
		rate_error(2) = _yaw_error_lpf.apply(rate_error(2)); // inputs were validated as finite above
	}

	// rate setpoint derivative for the lead on the setpoint path: first order low pass of (sp - sp_prev)/dt, then
	// the magnitude clamp. Yaw differentiates the setpoint as it enters the filtered yaw error. Zero on the first
	// cycle, after resetSetpointLead() and on ground (sp_prev follows the setpoint, so take-off starts at 0)
	Vector3f rate_sp_eff = rate_sp;

	if (_yaw_filter_active) {
		rate_sp_eff(2) = _yaw_sp_lpf.apply(rate_sp(2));
	}

	if (landed || _sp_lead_reset) {
		_rate_sp_dot.zero();
		_sp_lead_reset = false;

	} else {
		const float sp_alpha = dt / (kSetpointLeadTc + dt);

		for (int i = 0; i < 3; i++) {
			const float raw = (rate_sp_eff(i) - _rate_sp_prev(i)) / dt;
			const float filtered = _rate_sp_dot(i) + sp_alpha * (raw - _rate_sp_dot(i));
			_rate_sp_dot(i) = math::constrain(filtered, -kMaxRateSpDot, kMaxRateSpDot);
		}
	}

	_rate_sp_prev = rate_sp_eff;

	// desired angular acceleration
	const Vector3f nu = _rate_bandwidth_gain.emult(rate_error);

	// on ground the measured acceleration carries no information about the torque: hold the feedback torque
	// out of the law so that no increment can accumulate. At takeoff the law steps by the modelled torque, the
	// filtered landed output, which the maximum increment bounds like any in-flight increment
	const Vector3f t_fb_target = landed ? Vector3f() : t_f;
	Vector3f t_fb = t_fb_target;

	// on both edges of landed the feedback torque is ramped with the landed slew instead of stepping;
	// in flight, also while only maybe_landed is set, there is no slew limit
	if (landed != _landed_prev) {
		_landed_ramp = true;
	}

	_landed_prev = landed;

	if (_landed_ramp) {
		const float max_step = _landed_slew * dt;
		bool at_target = true;

		for (int i = 0; i < 3; i++) {
			const float delta = t_fb_target(i) - _t_fb_prev(i);
			t_fb(i) = _t_fb_prev(i) + math::constrain(delta, -max_step, max_step);
			at_target = at_target && (fabsf(delta) <= max_step); // reached the target in this step
		}

		_landed_ramp = !at_target;
	}

	_t_fb_prev = t_fb;

	// incremental inversion, only yaw has the spin-up term (g2 / dt = 0 for roll and pitch). Yaw uses the backward
	// Euler form of (G1 + G2 s) Delta = nu - (1 + c) a_f, a low pass of time constant G2 / G1 on the increment, with
	// Delta_k-1 the increment applied in the previous cycle
	Vector3f torque_increment;

	// rate prediction lead: c_i = lead_scale K_i tau_c cancels the actuator lag in the feedback path, bounded
	// to kMaxLeadGain, off on ground so that the landed output is the law without lead
	Vector3f lead_gain;

	for (int i = 0; i < 3; i++) {
		lead_gain(i) = landed ? 0.f : math::min(_lead_scale * _rate_bandwidth_gain(i) * _actuator_tc, kMaxLeadGain);
	}

	for (int i = 0; i < 3; i++) {
		const float g2_over_dt = (i == 2) ? (_g2_yaw / dt) : 0.f;
		const float prev_inc = (i == 2 && !landed) ? _yaw_inc_prev : 0.f;
		const float numerator = nu(i) - (1.f + lead_gain(i)) * a_f(i) + lead_gain(i) * _rate_sp_dot(i) + g2_over_dt * prev_inc;
		torque_increment(i) = numerator / (_g1(i) + g2_over_dt);
	}

	if (!torque_increment.isAllFinite()) {
		// e.g. overflow from an absurdly large input, which may have reached the filter states
		return faultOutput(true);
	}

	// bound the increment and the output
	Vector3f t_cmd;

	for (int i = 0; i < 3; i++) {
		torque_increment(i) = math::constrain(torque_increment(i), -_max_increment, _max_increment);
		t_cmd(i) = math::constrain(t_fb(i) + torque_increment(i), -1.f, 1.f);
	}

	// the yaw increment state is the one that reached the output (back calculation), never a raw or non finite value,
	// and zero on ground so that flight starts without a double count of the landed output
	_yaw_inc_prev = landed ? 0.f : (t_cmd(2) - t_fb(2));

	_fault = false;
	_fault_cycles = 0;
	_t_cmd_last = t_cmd;

	// logging values
	_nu = nu;
	_a_f = a_f;
	_lead_gain = lead_gain;
	_t_f = t_fb;
	_t_f_model = t_f_model;
	_t_f_meas = t_f_meas;
	_torque_increment = torque_increment;

	return t_cmd;
}
