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
 * @file IndiInjectionStep.hpp
 *
 * The part of one INDI rate cycle that carries the system identification excitation: where d enters (torque setpoint or
 * rate setpoint) and which setpoint the INDI law receives. Kept out of McIndiRateControl so that a unit test runs
 * the same code path as the module.
 */

#pragma once

#include <matrix/matrix/math.hpp>
#include <stdint.h>

#include <lib/indi_rate_control/indi_rate_control.hpp>

#include "IndiInjection.hpp"

struct IndiInjectionStepIn {
	int point{0};			///< MC_INDI_INJ_PT: 0 adds the excitation to the torque output, 1 to the rate setpoint
	bool armed{false};
	bool landed{false};
	bool maybe_landed{false};
	bool rate_sp_break_allowed{false};	///< PT 1 only: attitude controlled mode and setpoint not stale
	uint64_t timestamp_sample{0};		///< gyro sample time, clock of the injection
	float dt{0.f};
};

struct IndiInjectionStepOut {
	matrix::Vector3f torque_pre_inject{};	///< c
	matrix::Vector3f torque_inject{};	///< d on the torque setpoint (PT 0)
	matrix::Vector3f torque_sp{};		///< u = c + d
	matrix::Vector3f rates_sp_pre_inject{};	///< y, only filled while the rate setpoint break is active (PT 1, axis set)
	matrix::Vector3f rates_sp_inject{};	///< d on the rate setpoint
	matrix::Vector3f rates_sp_applied{};	///< x = y + d, the setpoint the INDI law received
};

/**
 * Run the INDI law with the excitation. With MC_INDI_INJ_AX off (injection.axis() < 0) the law receives
 * rates_sp itself and nothing else is computed. With PT 1 the law receives the rate setpoint plus the excitation
 * (rates_sp itself is not changed, the torque is not injected). d is 0 while !rate_sp_break_allowed or while the law reports a fault from the last cycle.
 */
void runIndiInjectionStep(IndiRateControl &indi, IndiInjection &injection, const IndiInjectionStepIn &in,
			  const matrix::Vector3f &rates, const matrix::Vector3f &rates_sp, const matrix::Vector3f &angular_accel,
			  const matrix::Vector3f &torque_allocated_prev, IndiInjectionStepOut &out);
