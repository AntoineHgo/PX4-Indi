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

/**
 * @file IndiErpmArmingCheckTest.cpp
 *
 * Arming is refused unless every motor has a fresh rpm sample, x500 geometry (ROMFS airframe 4001_gz_x500).
 */

#include <gtest/gtest.h>

#include <math.h>

#include "ActuatorEffectivenessRotors.hpp"
#include "IndiErpmArmingCheck.hpp"

using namespace matrix;

namespace
{

constexpr int kNumRotors = 4;
constexpr float kOmegaMax = 1000.f; // rad/s
constexpr float kRpmHover = 5000.f;
constexpr uint64_t kNow = 2000000; // us
constexpr float kTimeout = 0.02f;  // s

void setX500Effectiveness(ActuatorEffectiveness::EffectivenessMatrix &effectiveness)
{
	const float px[kNumRotors] = {0.174f, -0.174f, 0.174f, -0.174f};
	const float py[kNumRotors] = {0.174f, -0.174f, -0.174f, 0.174f};
	const float km[kNumRotors] = {0.05f, 0.05f, -0.05f, -0.05f};

	ActuatorEffectivenessRotors::Geometry geometry{};
	geometry.num_rotors = kNumRotors;

	for (int i = 0; i < kNumRotors; i++) {
		geometry.rotors[i].position = Vector3f(px[i], py[i], 0.f);
		geometry.rotors[i].axis = Vector3f(0.f, 0.f, -1.f);
		geometry.rotors[i].thrust_coef = 6.5f;
		geometry.rotors[i].moment_ratio = km[i];
	}

	ActuatorEffectivenessRotors::computeEffectivenessMatrix(geometry, effectiveness);
}

} // namespace

class IndiErpmArmingCheckTest : public ::testing::Test
{
public:
	void SetUp() override
	{
		ActuatorEffectiveness::EffectivenessMatrix effectiveness;
		ControlAllocation::ActuatorVector trim;
		ControlAllocation::ActuatorVector linearization_point;
		setX500Effectiveness(effectiveness);
		_measured.setEffectiveness(effectiveness, trim, linearization_point, kNumRotors, true);
		_measured.setRotorSpeedMax(kOmegaMax);
	}

	void reportAll(uint64_t timestamp)
	{
		for (int motor = 0; motor < kNumRotors; motor++) {
			_measured.setMotorSample(motor, kRpmHover, 0, timestamp);
		}
	}

	IndiMeasuredTorque _measured;
};

TEST_F(IndiErpmArmingCheckTest, AllMotorsFreshCanArm)
{
	reportAll(kNow - 5000);

	const IndiErpmArmingCheck::Verdict verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_TRUE(verdict.can_arm);
	EXPECT_EQ(verdict.motor_mask, 0);
}

TEST_F(IndiErpmArmingCheckTest, MotorWithoutTelemetryRefuses)
{
	for (int motor = 0; motor < kNumRotors; motor++) {
		if (motor != 2) {
			_measured.setMotorSample(motor, kRpmHover, 0, kNow - 5000);
		}
	}

	IndiErpmArmingCheck::Verdict verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_EQ(verdict.motor_mask, 1 << 2);

	// a motor that reports but is flagged offline by the ESC driver is as good as missing
	_measured.setMotorSample(2, kRpmHover, 0, kNow - 5000);
	_measured.setMotorOffline(2);
	verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_EQ(verdict.motor_mask, 1 << 2);
}

TEST_F(IndiErpmArmingCheckTest, StaleSampleRefuses)
{
	reportAll(kNow - 5000);
	_measured.setMotorSample(1, kRpmHover, 0, kNow - 50000); // older than the sample age limit

	IndiErpmArmingCheck::Verdict verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_EQ(verdict.motor_mask, 1 << 1);

	// fresh for the sample age limit, but older than the configured timeout: no single motor is named
	reportAll(kNow - 5000);
	verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, 0.002f, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_EQ(verdict.motor_mask, (1 << kNumRotors) - 1);
}

TEST_F(IndiErpmArmingCheckTest, NeverRefusesWhileArmed)
{
	// no telemetry at all, and a stale one
	EXPECT_TRUE(IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, true).can_arm);

	reportAll(kNow - 50000);
	EXPECT_TRUE(IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, true).can_arm);
}

TEST_F(IndiErpmArmingCheckTest, NotConfiguredRefusesWhileDisarmed)
{
	reportAll(kNow - 5000);

	// no rotor speed scaling: the telemetry is present but not used
	_measured.setRotorSpeedMax(0.f);
	IndiErpmArmingCheck::Verdict verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_TRUE(verdict.not_configured);
	EXPECT_EQ(verdict.motor_mask, 0);
	EXPECT_TRUE(IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, true).can_arm);

	// no rotor geometry
	IndiMeasuredTorque without_geometry;
	without_geometry.setRotorSpeedMax(kOmegaMax);
	verdict = IndiErpmArmingCheck::evaluate(without_geometry, kNow, kTimeout, false);
	EXPECT_FALSE(verdict.can_arm);
	EXPECT_TRUE(verdict.not_configured);
	EXPECT_EQ(verdict.motor_mask, 0);
	EXPECT_TRUE(IndiErpmArmingCheck::evaluate(without_geometry, kNow, kTimeout, true).can_arm);

	// configured again: arming is allowed and the flag is cleared
	_measured.setRotorSpeedMax(kOmegaMax);
	verdict = IndiErpmArmingCheck::evaluate(_measured, kNow, kTimeout, false);
	EXPECT_TRUE(verdict.can_arm);
	EXPECT_FALSE(verdict.not_configured);
}
