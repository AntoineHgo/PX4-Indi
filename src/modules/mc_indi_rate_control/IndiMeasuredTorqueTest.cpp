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
 * @file IndiMeasuredTorqueTest.cpp
 *
 * The torque computed from actuator values must be the one the control allocator allocated, x500 geometry
 * (ROMFS airframe 4001_gz_x500).
 */

#include <gtest/gtest.h>

#include <math.h>

#include "ActuatorEffectivenessRotors.hpp"
#include "IndiMeasuredTorque.hpp"

using namespace matrix;

namespace
{

constexpr int kNumRotors = 4;
constexpr float kOmegaMax = 1000.f; // rad/s

void setX500Effectiveness(ActuatorEffectiveness::EffectivenessMatrix &effectiveness)
{
	// CA_ROTORn_PX, PY, KM of the airframe file, thrust coefficient 6.5 (CA_ROTORn_CT default)
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

float rpmFromThrust(float u)
{
	return sqrtf(u) * kOmegaMax * 60.f / (2.f * M_PI_F);
}

} // namespace

class IndiMeasuredTorqueTest : public ::testing::Test
{
public:
	void SetUp() override
	{
		setX500Effectiveness(_effectiveness);

		// the allocator: normalised roll/pitch/yaw, same matrix
		_allocation.setNormalizeRPY(true);
		_allocation.setEffectivenessMatrix(_effectiveness, _trim, _linearization_point, kNumRotors, true);

		_model.setEffectiveness(_effectiveness, _trim, _linearization_point, kNumRotors, true);
		_model.setRotorSpeedMax(kOmegaMax);
	}

	void allocate(float roll, float pitch, float yaw, float thrust)
	{
		Vector<float, 6> control_sp;
		control_sp(ControlAllocation::ROLL) = roll;
		control_sp(ControlAllocation::PITCH) = pitch;
		control_sp(ControlAllocation::YAW) = yaw;
		control_sp(ControlAllocation::THRUST_Z) = thrust;
		_allocation.setControlSetpoint(control_sp);
		_allocation.allocate();
		_allocation.clipActuatorSetpoint();
	}

	ActuatorEffectiveness::EffectivenessMatrix _effectiveness;
	ControlAllocation::ActuatorVector _trim;
	ControlAllocation::ActuatorVector _linearization_point;
	ControlAllocationPseudoInverse _allocation;
	IndiMeasuredTorque _model;
};

TEST_F(IndiMeasuredTorqueTest, ActuatorsMapBackToAllocatedControl)
{
	const float setpoints[][4] = {
		{0.f, 0.f, 0.f, -0.5f},
		{0.1f, 0.f, 0.f, -0.5f},
		{0.f, -0.08f, 0.f, -0.4f},
		{0.f, 0.f, 0.05f, -0.6f},
		{0.1f, -0.05f, 0.03f, -0.4f},
	};

	for (const auto &sp : setpoints) {
		allocate(sp[0], sp[1], sp[2], sp[3]);

		const Vector<float, 6> expected = _allocation.getAllocatedControl();
		const Vector<float, 6> actual = _model.torqueFromActuators(_allocation.getActuatorSetpoint());

		for (int i = 0; i < 6; i++) {
			EXPECT_NEAR(actual(i), expected(i), 1e-5f) << "axis " << i;
		}

		// and the allocator did what was asked, so the helper reproduces the torque setpoint
		EXPECT_NEAR(actual(ControlAllocation::ROLL), sp[0], 1e-4f);
		EXPECT_NEAR(actual(ControlAllocation::PITCH), sp[1], 1e-4f);
		EXPECT_NEAR(actual(ControlAllocation::YAW), sp[2], 1e-4f);
	}
}

TEST_F(IndiMeasuredTorqueTest, NanActuatorIsZeroThrust)
{
	allocate(0.05f, 0.02f, 0.01f, -0.5f);

	ControlAllocation::ActuatorVector with_nan = _allocation.getActuatorSetpoint();
	with_nan(1) = NAN;
	ControlAllocation::ActuatorVector with_zero = with_nan;
	with_zero(1) = 0.f;

	const Vector<float, 6> torque = _model.torqueFromActuators(with_nan);

	for (int i = 0; i < 6; i++) {
		EXPECT_TRUE(PX4_ISFINITE(torque(i)));
		EXPECT_FLOAT_EQ(torque(i), _model.torqueFromActuators(with_zero)(i));
	}
}

TEST_F(IndiMeasuredTorqueTest, RotorSpeedsGiveAllocatedTorque)
{
	allocate(0.08f, -0.04f, 0.02f, -0.5f);
	const uint64_t now = 1000000;

	for (int motor = 0; motor < kNumRotors; motor++) {
		_model.setMotorSample(motor, rpmFromThrust(_allocation.getActuatorSetpoint()(motor)), 0, now - 1000);
	}

	IndiMeasuredTorque::Result result = _model.compute(now);
	EXPECT_TRUE(result.valid);
	EXPECT_EQ(result.motor_valid_mask, 0x0F);
	EXPECT_EQ(result.timestamp_sample, now - 1000);
	EXPECT_NEAR(result.torque[0], 0.08f, 1e-4f);
	EXPECT_NEAR(result.torque[1], -0.04f, 1e-4f);
	EXPECT_NEAR(result.torque[2], 0.02f, 1e-4f);

	// sample too old
	result = _model.compute(now + IndiMeasuredTorque::SAMPLE_MAX_AGE_US + 1000);
	EXPECT_FALSE(result.valid);

	// a motor goes offline
	_model.setMotorOffline(2);
	result = _model.compute(now);
	EXPECT_FALSE(result.valid);
	EXPECT_EQ(result.motor_valid_mask, 0x0B);

	// repeated frame after an error count increment keeps the old sample time
	_model.setMotorSample(2, rpmFromThrust(0.3f), 0, now - 1000);
	_model.setMotorSample(2, rpmFromThrust(0.9f), 1, now);
	result = _model.compute(now);
	EXPECT_TRUE(result.valid);
	EXPECT_EQ(result.timestamp_sample, now - 1000);

	// implausible and non finite rotor speed
	_model.setMotorSample(0, NAN, 0, now);
	EXPECT_FALSE(_model.compute(now).valid);
	_model.setMotorSample(0, 2.f * rpmFromThrust(1.f), 0, now);
	EXPECT_FALSE(_model.compute(now).valid);
}

TEST_F(IndiMeasuredTorqueTest, DisabledWithoutRotorSpeedMax)
{
	_model.setRotorSpeedMax(0.f);
	EXPECT_FALSE(_model.enabled());

	for (int motor = 0; motor < kNumRotors; motor++) {
		_model.setMotorSample(motor, 1000.f, 0, 1000);
	}

	EXPECT_FALSE(_model.compute(2000).valid);
}
