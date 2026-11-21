#include <gtest/gtest.h>

#include "SetpointExtrapolation.hpp"

// Known answers are hand computed from p = p0 + v dt + a dt^2/2, v = v0 + a dt.
static trajectory_setpoint_s makeSp(hrt_abstime t)
{
	trajectory_setpoint_s sp{};
	sp.timestamp = t;

	for (int i = 0; i < 3; i++) {
		sp.position[i] = NAN;
		sp.velocity[i] = NAN;
		sp.acceleration[i] = NAN;
	}

	return sp;
}

static constexpr hrt_abstime kCap = 500000; // 0.5 s

TEST(SetpointExtrapolationTest, PositionVelocityAndAcceleration)
{
	trajectory_setpoint_s sp = makeSp(1000000);
	sp.position[0] = 1.f; sp.velocity[0] = 2.f; sp.acceleration[0] = 4.f;
	// dt = 0.1: p = 1 + 0.2 + 0.5*4*0.01 = 1.22, v = 2 + 0.4 = 2.4
	const auto out = extrapolateSetpoint(sp, 1100000, kCap);
	EXPECT_NEAR(1.22f, out.position[0], 1e-5f);
	EXPECT_NEAR(2.4f, out.velocity[0], 1e-5f);
	EXPECT_FLOAT_EQ(4.f, out.acceleration[0]);
	EXPECT_EQ(sp.timestamp, out.timestamp);
	EXPECT_FLOAT_EQ(1.f, sp.position[0]); // input untouched
}

TEST(SetpointExtrapolationTest, WithoutAcceleration)
{
	trajectory_setpoint_s sp = makeSp(0);
	sp.position[1] = -3.f; sp.velocity[1] = 1.5f;
	const auto out = extrapolateSetpoint(sp, 200000, kCap); // dt = 0.2
	EXPECT_NEAR(-2.7f, out.position[1], 1e-5f);
	EXPECT_NEAR(1.5f, out.velocity[1], 1e-6f);
	EXPECT_TRUE(std::isnan(out.acceleration[1]));
}

TEST(SetpointExtrapolationTest, NanComponentsUntouched)
{
	trajectory_setpoint_s sp = makeSp(0);
	sp.position[0] = 1.f; // velocity NaN: position must not move
	sp.velocity[1] = 2.f; // position NaN: only velocity (with a)
	sp.acceleration[1] = 1.f;
	sp.acceleration[2] = 5.f; // acceleration only: nothing to extrapolate
	const auto out = extrapolateSetpoint(sp, 100000, kCap);
	EXPECT_FLOAT_EQ(1.f, out.position[0]);
	EXPECT_TRUE(std::isnan(out.velocity[0]));
	EXPECT_TRUE(std::isnan(out.position[1]));
	EXPECT_NEAR(2.1f, out.velocity[1], 1e-6f);
	EXPECT_TRUE(std::isnan(out.position[2]));
	EXPECT_TRUE(std::isnan(out.velocity[2]));
	EXPECT_FLOAT_EQ(5.f, out.acceleration[2]);
}

TEST(SetpointExtrapolationTest, DtIsCapped)
{
	trajectory_setpoint_s sp = makeSp(0);
	sp.position[0] = 0.f; sp.velocity[0] = 1.f; sp.acceleration[0] = 2.f;
	// 10 s old, capped at 0.5 s: p = 0.5 + 0.25 = 0.75, v = 1 + 1 = 2
	const auto out = extrapolateSetpoint(sp, 10000000, kCap);
	EXPECT_NEAR(0.75f, out.position[0], 1e-5f);
	EXPECT_NEAR(2.f, out.velocity[0], 1e-5f);
}

TEST(SetpointExtrapolationTest, NonPositiveDtUnchanged)
{
	trajectory_setpoint_s sp = makeSp(1000);
	sp.position[0] = 1.f; sp.velocity[0] = 2.f; sp.acceleration[0] = 3.f;

	for (hrt_abstime now : {hrt_abstime(1000), hrt_abstime(500)}) {
		const auto out = extrapolateSetpoint(sp, now, kCap);
		EXPECT_FLOAT_EQ(1.f, out.position[0]);
		EXPECT_FLOAT_EQ(2.f, out.velocity[0]);
		EXPECT_FLOAT_EQ(3.f, out.acceleration[0]);
	}
}
