#pragma once

/**
 * Failsafe trajectory setpoint of the INDI position module. Pure function, no module state, so it is unit tested
 * against the rule table of the stock mc_pos_control generateFailsafeSetpoint().
 */

#include <cmath>

#include <drivers/drv_hrt.h>
#include <matrix/math.hpp>
#include <uORB/topics/trajectory_setpoint.h>

/** Which failsafe rule fired (for the rate limited warnings of the caller). */
struct FailsafeInfo {
	bool stop_and_wait{false}; ///< xy velocity finite: hold still along xy
	bool blind_land{false};    ///< xy velocity invalid: descend at the land speed
	bool blind_descent{false}; ///< vz invalid: acceleration only, a bit below hover
};

/**
 * @param now         timestamp of the setpoint
 * @param velocity    velocity state (NED), NaN components mean invalid
 * @param land_speed  MPC_LAND_SPEED [m/s]
 * @param info        optional, rules that fired
 */
inline trajectory_setpoint_s computeFailsafeSetpoint(const hrt_abstime now, const matrix::Vector3f &velocity,
		const float land_speed, FailsafeInfo *info = nullptr)
{
	FailsafeInfo fi{};
	const float nan = NAN;

	trajectory_setpoint_s sp{};
	sp.timestamp = now;

	for (int i = 0; i < 3; i++) {
		sp.position[i] = nan;
		sp.velocity[i] = nan;
		sp.acceleration[i] = nan;
		sp.jerk[i] = nan;
	}

	sp.yaw = nan;
	sp.yawspeed = nan;

	if (matrix::Vector2f(velocity(0), velocity(1)).isAllFinite()) {
		// don't move along xy
		sp.velocity[0] = sp.velocity[1] = 0.f;
		fi.stop_and_wait = true;

	} else {
		// descend with land speed since we can't stop
		sp.acceleration[0] = sp.acceleration[1] = 0.f;
		sp.velocity[2] = land_speed;
		fi.blind_land = true;
	}

	if (std::isfinite(velocity(2))) {
		// don't move along z if we can stop in all dimensions
		if (!std::isfinite(sp.velocity[2])) {
			sp.velocity[2] = 0.f;
		}

	} else {
		// emergency descend with a bit below hover thrust
		sp.velocity[2] = nan;
		sp.acceleration[2] = .3f;
		fi.blind_descent = true;
	}

	if (info) {
		*info = fi;
	}

	return sp;
}
