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

#include "IndiStageMode.hpp"

TEST(IndiStageModeTest, NotWantedIsAlwaysBypass)
{
	for (int m = 0; m < 16; m++) {
		EXPECT_EQ(selectStageMode(false, m & 1, m & 2, m & 4, m & 8), StageMode::Bypass) << m;
	}
}

TEST(IndiStageModeTest, WantedIsNeverBypass)
{
	for (int m = 0; m < 16; m++) {
		EXPECT_NE(selectStageMode(true, m & 1, m & 2, m & 4, m & 8), StageMode::Bypass) << m;
	}
}

TEST(IndiStageModeTest, AllOkIsIndi)
{
	EXPECT_EQ(selectStageMode(true, true, true, true, true), StageMode::Indi);
}

TEST(IndiStageModeTest, AccelStaleOnlyIsModelAccel)
{
	EXPECT_EQ(selectStageMode(true, true, false, true, true), StageMode::IndiModelAccel);
}

TEST(IndiStageModeTest, OtherFailuresHold)
{
	for (int acc = 0; acc < 2; acc++) {
		EXPECT_EQ(selectStageMode(true, false, acc, true, true), StageMode::Hold);
		EXPECT_EQ(selectStageMode(true, true, acc, false, true), StageMode::Hold);
		EXPECT_EQ(selectStageMode(true, true, acc, true, false), StageMode::Hold);
	}
}

TEST(IndiStageModeTest, ComputeWantIndi)
{
	EXPECT_TRUE(computeWantIndi(true, true, false, false));
	EXPECT_TRUE(computeWantIndi(true, false, true, false));
	EXPECT_TRUE(computeWantIndi(true, false, false, true));
	EXPECT_FALSE(computeWantIndi(false, true, true, true));  // disarmed
	EXPECT_FALSE(computeWantIndi(true, false, false, false)); // manual / stabilized / acro: pass-through
}

// Landed / ramp case must use the modelled specific force, never the measured one
TEST(IndiStageModeTest, GroundAndRampUseModelledForce)
{
	EXPECT_TRUE(useModelledForce(false, false, false)); // takeoff state < flight (ground, rampup)
	EXPECT_TRUE(useModelledForce(true, true, false));   // flight with ground contact
	EXPECT_TRUE(useModelledForce(true, false, true));   // flight, maybe landed
	EXPECT_FALSE(useModelledForce(true, false, false)); // free flight: measured
}

TEST(IndiStageModeTest, ModelForceSelectsModelAccelEvenWithFreshAccel)
{
	for (int m = 0; m < 2; m++) {
		const bool model = useModelledForce(false, false, false);
		EXPECT_EQ(selectStageMode(true, true, true, true, true, model), StageMode::IndiModelAccel);
		EXPECT_EQ(selectStageMode(true, true, m, true, true, true), StageMode::IndiModelAccel);
	}

	EXPECT_EQ(selectStageMode(true, true, true, true, true, useModelledForce(true, false, false)), StageMode::Indi);
	EXPECT_EQ(selectStageMode(true, false, true, true, true, true), StageMode::Hold); // failures still hold
}

TEST(IndiStageModeTest, DeriveZOnly)
{
	EXPECT_TRUE(deriveZOnly(false, false));  // ALTCTL (climb only)
	EXPECT_FALSE(deriveZOnly(true, false));  // POSCTL
	EXPECT_FALSE(deriveZOnly(true, true));
	EXPECT_FALSE(deriveZOnly(false, true));  // velocity only
}

TEST(IndiStageModeTest, ArmEdgesResetStageState)
{
	EXPECT_TRUE(shouldResetStageState(true, false));  // disarm
	EXPECT_TRUE(shouldResetStageState(false, true));  // arm
	EXPECT_FALSE(shouldResetStageState(true, true));
	EXPECT_FALSE(shouldResetStageState(false, false));
}

TEST(IndiStageModeTest, ZeroStockThrustIsStraightUpInZOnly)
{
	EXPECT_TRUE(isZeroThrustDir(0.f, 0.f, 0.f));   // ALTCTL on ground, MPC thrust min 0
	EXPECT_TRUE(isZeroThrustDir(0.f, 0.f, -0.f));
	EXPECT_FALSE(isZeroThrustDir(0.f, 0.f, -0.1f)); // a real direction is kept
	EXPECT_FALSE(isZeroThrustDir(0.01f, 0.f, 0.f));
	EXPECT_FALSE(isZeroThrustDir(NAN, 0.f, 0.f));   // non-finite still goes to the hold
}

TEST(IndiStageModeTest, HoldFallbackNeverHoverThrustOnGround)
{
	EXPECT_FLOAT_EQ(holdFallbackThrust(false, 0.3f), 0.f);
	EXPECT_FLOAT_EQ(holdFallbackThrust(true, 0.3f), 0.3f);
	EXPECT_FLOAT_EQ(holdFallbackThrust(true, NAN), 0.5f);
}

TEST(IndiStageModeTest, PosControlEntryEdgeRequestsReset)
{
	EXPECT_TRUE(shouldResetOnPosControlEntry(false, true));
	EXPECT_FALSE(shouldResetOnPosControlEntry(true, true));
	EXPECT_FALSE(shouldResetOnPosControlEntry(true, false));
	EXPECT_FALSE(shouldResetOnPosControlEntry(false, false));
}

TEST(IndiStageModeTest, HoldToRunEdgeRequestsReset)
{
	EXPECT_TRUE(shouldResetOnHoldToRun(true, true));
	EXPECT_FALSE(shouldResetOnHoldToRun(false, true));
	EXPECT_FALSE(shouldResetOnHoldToRun(true, false));
}

TEST(IndiStageModeTest, SampleIntervalLimitsHoldAndClamp)
{
	// 0.3 s (3.3 Hz): hold; 0.1 s: run with the true dt; 0.001 s: lower clamp
	EXPECT_FALSE(stageIntervalOk(0.3f));
	EXPECT_TRUE(stageIntervalOk(0.1f));
	EXPECT_FLOAT_EQ(stageDt(0.1f), 0.1f);
	EXPECT_FLOAT_EQ(stageDt(0.001f), 0.002f);
	EXPECT_TRUE(stageIntervalOk(0.001f));
	EXPECT_FALSE(stageIntervalOk(NAN));
	EXPECT_EQ(selectStageMode(true, true, true, true, stageIntervalOk(0.3f)), StageMode::Hold);
	EXPECT_EQ(selectStageMode(true, true, true, true, stageIntervalOk(0.1f)), StageMode::Indi);
}
