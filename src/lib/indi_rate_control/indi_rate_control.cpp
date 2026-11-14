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

		if (!(_gain_k(i) >= 0.f) || !PX4_ISFINITE(_gain_k(i))) {
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
		if (reset_states) {
			_lpf[i].reset(_t_act(i));
			_alpha[i].reset(_t_act(i));

		} else {
			_lpf[i].reset(_t_lpf(i));
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
	}

	// settled at the next unfiltered values, in update()
	_yaw_filter_reset_pending = _yaw_filter_active;
	_design_yaw_cutoff_hz = _yaw_cutoff_hz;
}

void IndiRateControl::resetStates()
{
	_t_act.zero();
	_t_lpf.zero();

	for (int i = 0; i < kDelayBufferSize; i++) {
		_t_delay_buffer[i].zero();
	}

	_delay_head = 0;

	for (int i = 0; i < 3; i++) {
		_lpf[i].reset(0.f);
		_alpha[i].reset(0.f);
	}

	_yaw_lpf_accel.reset(0.f);
	_yaw_lpf_torque.reset(0.f);
	_yaw_error_lpf.reset(0.f);
	// restart the yaw filters from the next input, not from zero, which would scale the yaw path by the
	// filter's feed-through gain on every cycle that resets the states (landed, fault recovery)
	_yaw_filter_reset_pending = true;
	_t_f_prev.zero();
}

void IndiRateControl::reset()
{
	resetStates();
	_nu.zero();
	_a_f.zero();
	_t_f.zero();
	_dt_cmd.zero();
	_t_cmd_last.zero();
}

Vector3f IndiRateControl::faultOutput(const bool states_corrupted)
{
	_fault = true;

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
				 const Vector3f &torque_allocated_prev, const float dt, const bool landed)
{
	// 1. validate inputs and parameters, a rejected cycle leaves the states untouched
	const bool dt_valid = math::isFinite(dt) && (dt >= kMinDt) && (dt <= kMaxDt);
	const bool inputs_valid = rate.isAllFinite() && rate_sp.isAllFinite() && angular_accel.isAllFinite()
				  && torque_allocated_prev.isAllFinite();

	if (!dt_valid || !inputs_valid || !paramsValid() || !math::isFinite(_g2_yaw)) {
		return faultOutput(false);
	}

	// 2. (re)design the synchronisation filters on a low-passed sample rate, as the gyro chain designs on its
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

	// 3. actuator model, the allocated torque is normalised so bound it to guard the filter against overflow.
	// Steps 3-5 also run while landed, so that the modelled torque follows the torque actually applied and its
	// filter chain stays synchronised with the gyro derivative chain, which runs on every cycle
	Vector3f t_alloc;

	for (int i = 0; i < 3; i++) {
		t_alloc(i) = math::constrain(torque_allocated_prev(i), -1.f, 1.f);
	}

	const float actuator_alpha = 1.f - expf(-dt / _actuator_tc);
	_t_act += actuator_alpha * (t_alloc - _t_act);

	// 4. delay: ring buffer, _delay_head holds the newest sample
	_delay_head = (_delay_head + 1) % kDelayBufferSize;
	_t_delay_buffer[_delay_head] = _t_act;
	const int delay_index = (_delay_head + kDelayBufferSize - _delay_samples) % kDelayBufferSize;
	const Vector3f t_del = _t_delay_buffer[delay_index];

	// 5. synchronisation filter H, same order as the gyro derivative chain: LPF2p then alpha filter
	Vector3f t_f;

	for (int i = 0; i < 3; i++) {
		_t_lpf(i) = _lpf[i].apply(t_del(i));
		t_f(i) = _alpha[i].update(_t_lpf(i));
	}

	if (landed) {
		// restart the yaw filters from the current values each landed cycle (bypassed on ground)
		_yaw_filter_reset_pending = true;
	}

	// 6b. optional yaw low pass on both members of the feedback pair, same coefficients so they stay synchronised
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
			_yaw_filter_reset_pending = false;
		}

		a_f(2) = _yaw_lpf_accel.apply(a_f(2));
		t_f(2) = _yaw_lpf_torque.apply(t_f(2));
		rate_error(2) = _yaw_error_lpf.apply(rate_error(2)); // inputs were validated as finite above
	}

	// 7. desired angular acceleration
	const Vector3f nu = _gain_k.emult(rate_error);

	// 7b. on ground the measured acceleration carries no information about the torque: hold the feedback torque
	// out of the law so that no increment can accumulate. At takeoff the law steps by the modelled torque, the
	// filtered landed output, which the maximum increment bounds like any in-flight increment
	const Vector3f t_fb = landed ? Vector3f() : t_f;

	// 8. incremental inversion, only yaw has the spin-up term (g2 / dt = 0 for roll and pitch)
	Vector3f dt_cmd;

	for (int i = 0; i < 3; i++) {
		const float g2_over_dt = (i == 2) ? (_g2_yaw / dt) : 0.f;
		const float numerator = nu(i) - a_f(i) + g2_over_dt * (t_f(i) - _t_f_prev(i));
		dt_cmd(i) = numerator / (_g1(i) + g2_over_dt);
	}

	_t_f_prev = t_f;

	if (!dt_cmd.isAllFinite()) {
		// e.g. overflow from an absurdly large input, which may have reached the filter states
		return faultOutput(true);
	}

	// 9. bound the increment and the output
	Vector3f t_cmd;

	for (int i = 0; i < 3; i++) {
		dt_cmd(i) = math::constrain(dt_cmd(i), -_max_increment, _max_increment);
		t_cmd(i) = math::constrain(t_fb(i) + dt_cmd(i), -1.f, 1.f);
	}

	_fault = false;
	_fault_cycles = 0;
	_t_cmd_last = t_cmd;

	// 10. logging values
	_nu = nu;
	_a_f = a_f;
	_t_f = t_fb;
	_dt_cmd = dt_cmd;

	return t_cmd;
}
