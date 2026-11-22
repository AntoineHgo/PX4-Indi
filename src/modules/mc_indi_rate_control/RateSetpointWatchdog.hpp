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

#include <stdint.h>

/**
 * Rate setpoint timeout. Pure logic, times are microseconds.
 * Stale while armed and the rate setpoint is used and none arrived for longer than the timeout
 * (or none ever arrived). While stale the caller zeroes the rate setpoint and holds the thrust setpoint.
 */
class RateSetpointWatchdog
{
public:
	struct Result {
		bool stale{false};
		bool zero_rates{false};  ///< replace the rate setpoint by zero (thrust is held by the caller)
		bool warn{false};        ///< emit a (rate-limited) warning now
	};

	void setTimeout(float timeout_s) { _timeout_us = (uint64_t)(timeout_s * 1e6f); }

	/**
	 * @param last_rx timestamp of the last received vehicle_rates_setpoint, 0 if never received
	 * @param uses_setpoint non-acro branch with rate control enabled
	 */
	Result update(uint64_t last_rx, uint64_t now, bool armed, bool uses_setpoint);

private:
	static constexpr uint64_t WARN_INTERVAL_US = 2000000;
	uint64_t _timeout_us{500000};
	uint64_t _last_warn{0};
	bool _was_stale{false};
};
