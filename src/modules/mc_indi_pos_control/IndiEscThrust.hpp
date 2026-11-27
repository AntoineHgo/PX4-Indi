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

#pragma once

#include <math.h>
#include <stdint.h>

#include <lib/indi_rate_control/indi_rate_control.hpp>
#include <lib/mathlib/mathlib.h>
#include <uORB/topics/esc_status.h>

/**
 * Mean normalised rotor thrust u = (omega / omega_max)^2 of the four motors, from esc_status. Pure functions, no
 * module state.
 */
namespace IndiEscThrust
{

struct MeanRotorThrust {
	bool valid;
	float thrust;
};

/**
 * @param esc_status ESC report; motors are identified by the actuator function, entries of other functions are ignored
 * @param rotor_w_max maximum rotor speed [rad/s]
 * @return valid if all four motors are reported, online and have a plausible rpm (see normalisedThrustFromRpm);
 *         thrust is the mean of the four motors, NAN if not valid
 */
inline MeanRotorThrust meanRotorThrust(const esc_status_s &esc_status, float rotor_w_max)
{
	const float rpm_max = rotor_w_max * (60.f / (2.f * M_PI_F));
	const int n = math::min((int)esc_status.esc_count, (int)esc_status_s::CONNECTED_ESC_MAX);
	float rotor_thrust_sum = 0.f;
	uint32_t seen = 0;
	bool ok = (rotor_w_max > 0.f);

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

	const bool valid = ok && (seen == 0xFu);
	return {valid, valid ? (rotor_thrust_sum / 4.f) : NAN};
}

/// A sample stamped after now has age 0, not stale. Times in microseconds.
inline bool isFresh(bool valid, uint64_t now_us, uint64_t sample_us, uint64_t max_age_us)
{
	const uint64_t age_us = (now_us > sample_us) ? (now_us - sample_us) : uint64_t{0};
	return valid && age_us <= max_age_us;
}

} // namespace IndiEscThrust
