#pragma once

/**
 * Extrapolation of a held trajectory setpoint of the INDI position module (probe F2). The sender publishes at a lower
 * rate than the controller runs, so a zero-order hold is a staircase in position and velocity that enters the P and D
 * terms. Pure function, no module state: the caller extrapolates a copy of the latest received sample each cycle.
 *
 *   p = p_sp + v_sp dt + a_sp dt^2 / 2,   v = v_sp + a_sp dt
 *
 * per axis, dt = now - timestamp capped at max_dt. Only finite components are used: NaN components stay NaN, position
 * is moved only with a finite velocity, the acceleration term is added only when a_sp is finite. dt <= 0: unchanged.
 */

#include <cmath>

#include <drivers/drv_hrt.h>
#include <uORB/topics/trajectory_setpoint.h>

/**
 * @param sp      latest received setpoint
 * @param now     current time
 * @param max_dt  cap of the extrapolation time [us] (the stream timeout of the module)
 */
inline trajectory_setpoint_s extrapolateSetpoint(const trajectory_setpoint_s &sp, const hrt_abstime now,
		const hrt_abstime max_dt)
{
	trajectory_setpoint_s out = sp;

	if (now <= sp.timestamp) {
		return out;
	}

	hrt_abstime dt_us = now - sp.timestamp;

	if (dt_us > max_dt) {
		dt_us = max_dt;
	}

	const float dt = static_cast<float>(dt_us) * 1e-6f;

	for (int i = 0; i < 3; i++) {
		if (!std::isfinite(sp.velocity[i])) {
			continue;
		}

		const bool has_acc = std::isfinite(sp.acceleration[i]);
		const float acc = has_acc ? sp.acceleration[i] : 0.f;

		if (std::isfinite(sp.position[i])) {
			out.position[i] = sp.position[i] + sp.velocity[i] * dt + 0.5f * acc * dt * dt;
		}

		out.velocity[i] = sp.velocity[i] + acc * dt;
	}

	return out;
}
