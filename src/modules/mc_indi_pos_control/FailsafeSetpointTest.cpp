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

#include <gtest/gtest.h>

#include "FailsafeSetpoint.hpp"

// Expected values come from the rule table of the stock MulticopterPositionControl::generateFailsafeSetpoint()
// (src/modules/mc_pos_control/MulticopterPositionControl.cpp), not from the module:
//   start from all NaN (PositionControl::empty_trajectory_setpoint), timestamp = now
//   vxy finite : vel xy = 0
//   vxy invalid: acc xy = 0, vel z = land speed
//   vz finite  : if vel z still NaN -> vel z = 0
//   vz invalid : vel z = NaN, acc z = 0.3
static constexpr float kLand = 0.7f;

static bool bothNan(float a, float b) { return std::isnan(a) && std::isnan(b); }

static void expectSame(float expected, float actual, const char *what)
{
	if (std::isnan(expected)) {
		EXPECT_TRUE(std::isnan(actual)) << what << " expected NaN got " << actual;

	} else {
		EXPECT_FLOAT_EQ(expected, actual) << what;
	}
}

TEST(FailsafeSetpointTest, MatchesStockRuleTableOnAllCombinations)
{
	const float nan = NAN;
	const float vals[] = {0.f, 1.5f, -2.f};

	for (int xy_ok = 0; xy_ok < 2; xy_ok++) {
		for (int vx_nan = 0; vx_nan < 3; vx_nan++) { // xy invalid when either component is NaN: both, only x, only y
			for (int z_ok = 0; z_ok < 2; z_ok++) {
				for (float v : vals) {
					const bool xy_finite = xy_ok;
					float vx = v;
					float vy = -v;

					if (!xy_finite) {
						if (vx_nan == 0) { vx = nan; vy = nan; }

						if (vx_nan == 1) { vx = nan; }

						if (vx_nan == 2) { vy = nan; }

					} else if (vx_nan != 0) {
						continue; // duplicate of the finite case
					}

					const float vz = z_ok ? v : nan;
					FailsafeInfo info;
					const trajectory_setpoint_s sp = computeFailsafeSetpoint(123456, matrix::Vector3f(vx, vy, vz), kLand, &info);

					// expected, derived from the stock table
					float p[3] = {nan, nan, nan};
					float ev[3] = {nan, nan, nan};
					float ea[3] = {nan, nan, nan};

					if (xy_finite) { ev[0] = ev[1] = 0.f; }

					else { ea[0] = ea[1] = 0.f; ev[2] = kLand; }

					if (z_ok) { if (std::isnan(ev[2])) { ev[2] = 0.f; } }

					else { ev[2] = nan; ea[2] = 0.3f; }

					EXPECT_EQ(sp.timestamp, 123456u);

					for (int i = 0; i < 3; i++) {
						expectSame(p[i], sp.position[i], "position");
						expectSame(ev[i], sp.velocity[i], "velocity");
						expectSame(ea[i], sp.acceleration[i], "acceleration");
						EXPECT_TRUE(std::isnan(sp.jerk[i]));
					}

					EXPECT_TRUE(std::isnan(sp.yaw));
					EXPECT_TRUE(std::isnan(sp.yawspeed));
					EXPECT_EQ(info.stop_and_wait, xy_finite);
					EXPECT_EQ(info.blind_land, !xy_finite);
					EXPECT_EQ(info.blind_descent, !z_ok);
				}
			}
		}
	}

	EXPECT_TRUE(bothNan(NAN, NAN));
}

TEST(FailsafeSetpointTest, NamedCases)
{
	const float nan = NAN;
	// all valid: stop in all three axes
	trajectory_setpoint_s sp = computeFailsafeSetpoint(1, matrix::Vector3f(1.f, 2.f, 3.f), kLand);
	EXPECT_EQ(sp.velocity[0], 0.f);
	EXPECT_EQ(sp.velocity[1], 0.f);
	EXPECT_EQ(sp.velocity[2], 0.f);
	EXPECT_TRUE(std::isnan(sp.acceleration[2]));

	// xy invalid, vz valid: land speed down, no xy acceleration
	sp = computeFailsafeSetpoint(1, matrix::Vector3f(nan, nan, 0.f), kLand);
	EXPECT_EQ(sp.velocity[2], kLand);
	EXPECT_EQ(sp.acceleration[0], 0.f);
	EXPECT_EQ(sp.acceleration[1], 0.f);

	// vz invalid only: blind descent, positive NED z = down, 0.3 m/s^2
	sp = computeFailsafeSetpoint(1, matrix::Vector3f(1.f, 1.f, nan), kLand);
	EXPECT_TRUE(std::isnan(sp.velocity[2]));
	EXPECT_EQ(sp.acceleration[2], 0.3f);
	EXPECT_EQ(sp.velocity[0], 0.f);

	// everything invalid: land speed is overridden by the blind descent (vel z NaN, acc z 0.3)
	sp = computeFailsafeSetpoint(1, matrix::Vector3f(nan, nan, nan), kLand);
	EXPECT_TRUE(std::isnan(sp.velocity[2]));
	EXPECT_EQ(sp.acceleration[2], 0.3f);
	EXPECT_EQ(sp.acceleration[0], 0.f);
	EXPECT_TRUE(std::isnan(sp.velocity[0]));
}
