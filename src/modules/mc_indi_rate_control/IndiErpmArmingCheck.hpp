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
 * @file IndiErpmArmingCheck.hpp
 *
 * Arming check on the ESC rpm telemetry: arming is refused while the measured torque cannot be computed
 * from fresh rpm samples of every motor. Uses the same criteria as the measured torque in flight.
 */

#pragma once

#include <stdint.h>

#include "IndiMeasuredTorque.hpp"

class IndiErpmArmingCheck
{
public:
	struct Verdict {
		bool can_arm{true};
		uint16_t motor_mask{0}; ///< motors without usable telemetry (bit per motor), all motors if none is singled out
		bool not_configured{false}; ///< refused: no rotor speed scaling or geometry
	};

	/**
	 * @param measured rotor speed samples, same object that feeds the measured torque
	 * @param now_us current time
	 * @param timeout_s maximum age of the oldest sample (MC_INDI_ERPM_TO)
	 * @param armed never blocks while armed
	 * @return can_arm is false if any motor has no fresh rpm sample, or if the measured torque is not in use
	 *         (no rotor speed scaling configured or no rotor geometry)
	 */
	static Verdict evaluate(const IndiMeasuredTorque &measured, uint64_t now_us, float timeout_s, bool armed);
};
