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
 * @file IndiMeasuredTorque.cpp
 */

#include "IndiMeasuredTorque.hpp"

#include <math.h>

#include <mathlib/math/Functions.hpp>
#include <px4_platform_common/defines.h>

using matrix::Vector;

Vector<float, ControlAllocation::NUM_AXES>
IndiControlAllocation::getControlFromActuators(const ActuatorVector &actuator) const
{
	ActuatorVector actuator_copy{actuator};
	actuator_copy.nanToZero();
	return (_effectiveness * (actuator_copy - _actuator_trim)).emult(_control_allocation_scale);
}

void
IndiMeasuredTorque::setEffectiveness(const ActuatorEffectiveness::EffectivenessMatrix &effectiveness,
				     const ControlAllocation::ActuatorVector &trim,
				     const ControlAllocation::ActuatorVector &linearization_point, int num_rotors, bool normalize_rpy)
{
	_num_rotors = math::constrain(num_rotors, 0, math::min((int)ControlAllocation::NUM_ACTUATORS, MAX_MOTORS));

	// Set all the elements of a row to 0 if that row has weak authority, as the control allocator does
	ActuatorEffectiveness::EffectivenessMatrix matrix = effectiveness;

	for (int n = 0; n < ControlAllocation::NUM_AXES; n++) {
		bool all_entries_small = true;

		for (int m = 0; m < _num_rotors; m++) {
			if (fabsf(matrix(n, m)) > 0.05f) {
				all_entries_small = false;
			}
		}

		if (all_entries_small) {
			matrix.row(n) = 0.f;
		}
	}

	_allocation.setNormalizeRPY(normalize_rpy);
	_allocation.setEffectivenessMatrix(matrix, trim, linearization_point, _num_rotors, true);

	// The normalisation scale is computed lazily by the next allocation: run one (zero control setpoint) so the
	// scale is the one the control allocator applies.
	_allocation.setControlSetpoint(matrix::Vector<float, ControlAllocation::NUM_AXES>());
	_allocation.allocate();
}

void
IndiMeasuredTorque::setMotorOffline(int motor)
{
	if (motor < 0 || motor >= MAX_MOTORS) {
		return;
	}

	_samples[motor].online = false;
	_samples[motor].has_value = false;
}

void
IndiMeasuredTorque::setMotorSample(int motor, float rpm, uint32_t error_count, uint64_t timestamp)
{
	if (motor < 0 || motor >= MAX_MOTORS) {
		return;
	}

	Sample &sample = _samples[motor];
	sample.online = true;

	const bool dropped = sample.has_value && (error_count != sample.error_count);
	sample.error_count = error_count;

	if (dropped) {
		return;
	}

	// omega = rpm * 2 pi / 60, then u = (omega / omega_max)^2 clamped to [0, 1]
	const float omega = rpm * (2.f * M_PI_F / 60.f);
	const float ratio = omega / _omega_max;

	sample.u_valid = PX4_ISFINITE(ratio) && (omega >= 0.f) && (ratio <= MAX_OMEGA_RATIO);
	sample.u = sample.u_valid ? math::constrain(ratio * ratio, 0.f, 1.f) : 0.f;
	sample.timestamp_good = timestamp;
	sample.has_value = true;
}

IndiMeasuredTorque::Result
IndiMeasuredTorque::compute(uint64_t now) const
{
	Result result{};

	if (!enabled()) {
		return result;
	}

	ControlAllocation::ActuatorVector actuator = _allocation.actuatorTrim();
	bool valid = true;
	uint64_t oldest = 0;

	for (int motor = 0; motor < _num_rotors; motor++) {
		const Sample &sample = _samples[motor];
		const bool fresh = sample.online && sample.has_value && sample.u_valid
				   && (sample.timestamp_good <= now) && ((now - sample.timestamp_good) < SAMPLE_MAX_AGE_US);

		if (fresh) {
			actuator(motor) = sample.u;

			if (motor < 8) {
				result.motor_valid_mask |= (uint8_t)(1u << motor);
			}

			if (oldest == 0 || sample.timestamp_good < oldest) {
				oldest = sample.timestamp_good;
			}

		} else {
			valid = false;
		}
	}

	const Vector<float, ControlAllocation::NUM_AXES> control = _allocation.getControlFromActuators(actuator);

	for (int i = 0; i < 3; i++) {
		result.torque[i] = control(i);
	}

	result.timestamp_sample = oldest;
	result.valid = valid && PX4_ISFINITE(control(0)) && PX4_ISFINITE(control(1)) && PX4_ISFINITE(control(2));
	return result;
}
