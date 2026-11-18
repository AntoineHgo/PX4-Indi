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

#include "IndiInjectionStep.hpp"

void runIndiInjectionStep(IndiRateControl &indi, IndiInjection &injection, const IndiInjectionStepIn &in,
			  const matrix::Vector3f &rates, const matrix::Vector3f &rates_sp, const matrix::Vector3f &angular_accel,
			  const matrix::Vector3f &torque_allocated_prev, IndiInjectionStepOut &out)
{
	const int axis = injection.axis();
	const bool rate_sp_break = (in.point == 1) && (axis >= 0);

	if (rate_sp_break) {
		// x = y + d on one axis, the other two components are y itself. d is gated before the law runs
		matrix::Vector3f rates_sp_applied = rates_sp;
		matrix::Vector3f rates_sp_inject{};

		// the generator runs every cycle; a closed gate acts as a disarm, so the sequence restarts from zero after its
		// delay when the gate reopens (no step into the multisine, no partial window, disarm reset never skipped)
		const bool gate_open = in.rate_sp_break_allowed && !indi.getFault();
		rates_sp_inject(axis) = injection.update(in.timestamp_sample, in.armed && gate_open, in.landed);
		rates_sp_applied(axis) = rates_sp(axis) + rates_sp_inject(axis);

		out.torque_pre_inject = indi.update(rates, rates_sp_applied, angular_accel, torque_allocated_prev, in.dt, in.landed,
						    in.maybe_landed);
		out.torque_inject.zero();
		out.torque_sp = out.torque_pre_inject;
		out.rates_sp_pre_inject = rates_sp;
		out.rates_sp_inject = rates_sp_inject;
		out.rates_sp_applied = rates_sp_applied;
		return;
	}

	// c: controller output, fed the unmodified setpoint
	out.torque_pre_inject = indi.update(rates, rates_sp, angular_accel, torque_allocated_prev, in.dt, in.landed,
					    in.maybe_landed);
	out.torque_inject.zero();

	if (axis >= 0 && in.point == 0) {
		out.torque_inject(axis) = injection.update(in.timestamp_sample, in.armed, in.landed);
	}

	// u = c + d
	out.torque_sp = out.torque_pre_inject + out.torque_inject;
	out.rates_sp_pre_inject.zero();
	out.rates_sp_inject.zero();
	out.rates_sp_applied.zero();
}
