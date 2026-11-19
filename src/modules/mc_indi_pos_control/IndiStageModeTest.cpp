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
	EXPECT_TRUE(computeWantIndi(true, true, false, false, true, false));
	EXPECT_TRUE(computeWantIndi(true, false, true, false, true, false));
	EXPECT_TRUE(computeWantIndi(true, false, false, true, true, false));
	EXPECT_FALSE(computeWantIndi(false, true, true, true, true, false));  // disarmed
	EXPECT_FALSE(computeWantIndi(true, true, true, true, false, false));  // takeoff state not flight
	EXPECT_FALSE(computeWantIndi(true, true, true, true, true, true));    // ground contact
	EXPECT_FALSE(computeWantIndi(true, false, false, false, true, false)); // manual
}

TEST(IndiStageModeTest, DeriveZOnly)
{
	EXPECT_TRUE(deriveZOnly(false, false));  // ALTCTL (climb only)
	EXPECT_FALSE(deriveZOnly(true, false));  // POSCTL
	EXPECT_FALSE(deriveZOnly(true, true));
	EXPECT_FALSE(deriveZOnly(false, true));  // velocity only
}
