#include <gtest/gtest.h>
#include <cmath>
#include "HoverThrustSync.hpp"

namespace
{
void setup(PositionControl &pc)
{
	pc.setPositionGains(matrix::Vector3f(1.f, 1.f, 1.f));
	pc.setVelocityGains(matrix::Vector3f(4.f, 4.f, 4.f), matrix::Vector3f(2.f, 2.f, 2.f), matrix::Vector3f(2.f, 2.f, 2.f));
	pc.setVelocityLimits(12.f, 12.f, 3.f);
	pc.setThrustLimits(0.12f, 0.9f);
	pc.setHorizontalThrustMargin(0.3f);
	pc.setTiltLimit(0.5f);
}

// One bypass-style cycle (sinking at 0.3 m/s, hold velocity 0) and the resulting collective thrust
float cycle(PositionControl &pc)
{
	PositionControlStates states{};
	states.velocity = matrix::Vector3f(0.f, 0.f, 0.3f);
	pc.setState(states);
	trajectory_setpoint_s sp = PositionControl::empty_trajectory_setpoint;
	sp.velocity[0] = sp.velocity[1] = sp.velocity[2] = 0.f;
	pc.setInputSetpoint(sp);
	const bool ok = pc.update(0.01f);
	EXPECT_TRUE(ok);
	vehicle_attitude_setpoint_s att{};
	pc.getAttitudeSetpoint(att);
	return -att.thrust_body[2];
}
}

TEST(HoverThrustSync, IntegratorShiftKeepsThrustContinuous)
{
	PositionControl pc;
	setup(pc);
	float last = NAN;
	float before = 0.f;

	for (int i = 0; i < 200; i++) { syncHoverThrust(pc, last, 0.5f); before = cycle(pc); }

	syncHoverThrust(pc, last, 0.6f); // HTE-style change
	EXPECT_NEAR(cycle(pc), before, 1e-3f);
}

TEST(HoverThrustSync, PlainSetStepsThrust)
{
	PositionControl pc;
	setup(pc);
	float last = NAN;
	float before = 0.f;

	for (int i = 0; i < 200; i++) { syncHoverThrust(pc, last, 0.5f); before = cycle(pc); }

	pc.setHoverThrust(0.6f); // the old behaviour
	EXPECT_GT(std::fabs(cycle(pc) - before), 0.02f);
}
