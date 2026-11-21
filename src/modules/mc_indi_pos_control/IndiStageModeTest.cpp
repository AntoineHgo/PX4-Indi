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

// D-F7-GROUND: the landed / ramp case must use the modelled specific force, never the measured one
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
	EXPECT_FALSE(isZeroThrustDir(NAN, 0.f, 0.f));   // non-finite still goes to the D-STAGE-STALE hold
}

TEST(IndiStageModeTest, HoldFallbackNeverHoverThrustOnGround)
{
	EXPECT_FLOAT_EQ(holdFallbackThrust(false, 0.3f), 0.f);
	EXPECT_FLOAT_EQ(holdFallbackThrust(true, 0.3f), 0.3f);
	EXPECT_FLOAT_EQ(holdFallbackThrust(true, NAN), 0.5f);
}
