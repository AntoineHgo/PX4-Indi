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

TEST_F(IndiMeasuredTorqueTest, NegativeRotorSpeedIsInvalid)
{
	// header: u_valid means finite, non negative and plausible. A negative rpm of plausible magnitude (-0.5 omega_max,
	// squared it would give u = 0.25) must not be used, the motor is not valid and the torque is not valid
	const uint64_t now = 1000000;

	for (int motor = 0; motor < kNumRotors; motor++) {
		_model.setMotorSample(motor, rpmFromThrust(0.25f), 0, now - 1000);
	}

	ASSERT_TRUE(_model.compute(now).valid);

	_model.setMotorSample(1, -rpmFromThrust(0.25f), 0, now);
	const IndiMeasuredTorque::Result result = _model.compute(now);
	EXPECT_FALSE(result.valid);
	EXPECT_EQ(result.motor_valid_mask, 0x0D);
}

TEST_F(IndiMeasuredTorqueTest, DroppedFrameKeepsPreviousSampleValueAndTime)
{
	// header of setMotorSample: on an error count increment the previous sample and its time are kept, so a run of
	// dropped frames ages it out. The frame carries a very different rpm and a fresh time: neither may be used
	const uint64_t t0 = 1000000;

	for (int motor = 0; motor < kNumRotors; motor++) {
		_model.setMotorSample(motor, rpmFromThrust(0.25f), 0, t0);
	}

	const IndiMeasuredTorque::Result before = _model.compute(t0);
	ASSERT_TRUE(before.valid);

	_model.setMotorSample(0, rpmFromThrust(1.f), 1, t0 + 15000);
	const IndiMeasuredTorque::Result after = _model.compute(t0 + 15000);
	EXPECT_TRUE(after.valid);
	EXPECT_EQ(after.timestamp_sample, t0); // not t0 + 15000
	EXPECT_EQ(after.torque[0], before.torque[0]);
	EXPECT_EQ(after.torque[1], before.torque[1]);
	EXPECT_EQ(after.torque[2], before.torque[2]);

	// the kept sample ages out although a (dropped) frame arrived recently
	EXPECT_FALSE(_model.compute(t0 + IndiMeasuredTorque::SAMPLE_MAX_AGE_US + 1).valid);
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

// frozen (stuck) rotor speed detection
class IndiFrozenRpmTest : public IndiMeasuredTorqueTest
{
public:
	static constexpr uint64_t kStep = 2500; // us

	void SetUp() override
	{
		IndiMeasuredTorqueTest::SetUp();
		_model.setFrozenWindow(0.5f);
		_model.setArmed(true);
	}

	// one cycle: all motors get a command and an rpm sample. Motor 1 uses frozen_rpm if it is not NAN, the others
	// follow the (varying or constant) command with the given rpm noise
	IndiMeasuredTorque::Result cycle(bool vary_command, float frozen_rpm, float rpm_noise)
	{
		_t += kStep;
		_k++;
		const float command = 0.5f + (vary_command ? 0.05f * sinf(0.05f * _k) : 0.f);

		for (int motor = 0; motor < kNumRotors; motor++) {
			const float noise = rpm_noise * (((_k * 7 + motor * 3) % 5) - 2) / 2.f; // deterministic, +-rpm_noise
			float rpm = rpmFromThrust(command) + noise;

			if (motor == 1 && PX4_ISFINITE(frozen_rpm)) {
				rpm = frozen_rpm;
			}

			_model.setMotorCommand(motor, command, _t);
			_model.setMotorSample(motor, rpm, 0, _t);
		}

		return _model.compute(_t);
	}

	uint64_t _t{1000000};
	int _k{0};
};

TEST_F(IndiFrozenRpmTest, FrozenRpmFallsBack)
{
	IndiMeasuredTorque::Result result{};

	for (int i = 0; i < 100; i++) { // 0.25 s: still valid
		result = cycle(true, 5000.f, 0.f);
	}

	EXPECT_TRUE(result.valid);

	for (int i = 0; i < 140; i++) { // 0.6 s in total
		result = cycle(true, 5000.f, 0.f);
	}

	// the other motors have a (deterministic) noise free rpm that follows the command, so only motor 1 is frozen
	EXPECT_FALSE(result.valid);
	EXPECT_EQ(result.motor_frozen_mask, 0x02);
	EXPECT_EQ(result.motor_valid_mask, 0x0D);
}

TEST_F(IndiFrozenRpmTest, ConstantRpmConstantCommandStaysValid)
{
	for (int i = 0; i < 4000; i++) { // 10 s, every rpm bit-identical, command constant
		const IndiMeasuredTorque::Result result = cycle(false, NAN, 0.f);
		ASSERT_TRUE(result.valid) << i;
		ASSERT_EQ(result.motor_frozen_mask, 0) << i;
	}

	// disarmed: a frozen pattern with a varying command never trips either
	_model.setArmed(false);

	for (int i = 0; i < 400; i++) {
		EXPECT_EQ(cycle(true, 5000.f, 0.f).motor_frozen_mask, 0) << i;
	}
}

TEST_F(IndiFrozenRpmTest, NoisyRpmVaryingCommandValid)
{
	for (int i = 0; i < 4000; i++) {
		const IndiMeasuredTorque::Result result = cycle(true, NAN, 3.f);
		ASSERT_TRUE(result.valid) << i;
		ASSERT_EQ(result.motor_frozen_mask, 0) << i;
	}
}

TEST_F(IndiFrozenRpmTest, FrozenRecovers)
{
	IndiMeasuredTorque::Result result{};

	for (int i = 0; i < 300; i++) {
		result = cycle(true, 5000.f, 0.f);
	}

	ASSERT_FALSE(result.valid);
	ASSERT_EQ(result.motor_frozen_mask, 0x02);

	result = cycle(true, NAN, 0.f); // the rpm changes again: valid within this one sample
	EXPECT_TRUE(result.valid);
	EXPECT_EQ(result.motor_frozen_mask, 0);
}

TEST_F(IndiFrozenRpmTest, ArmingEdgeStartsANewWindow)
{
	// disarmed for 1 s with a constant rpm on motor 1, then armed: the window starts at the arming edge, so a
	// varying command in the first 0.1 s after arming must not trip on the rpm that was constant before arming
	_model.setArmed(false);

	for (int i = 0; i < 400; i++) {
		cycle(true, 5000.f, 0.f);
	}

	_model.setArmed(true);

	for (int i = 0; i < 40; i++) {
		ASSERT_EQ(cycle(true, 5000.f, 0.f).motor_frozen_mask, 0) << i;
	}
}

// age of the ESC sample against the telemetry timeout
TEST(IndiSampleFreshnessTest, BoundaryAtTimeout)
{
	constexpr uint64_t kStamp = 5000000;
	constexpr float kTimeout_s = 0.5f;
	constexpr uint64_t kTimeout_us = 500000;

	EXPECT_TRUE(IndiMeasuredTorque::isSampleFresh(kStamp, kStamp, kTimeout_s));
	EXPECT_TRUE(IndiMeasuredTorque::isSampleFresh(kStamp + kTimeout_us - 1, kStamp, kTimeout_s));
	EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(kStamp + kTimeout_us, kStamp, kTimeout_s));
	EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(kStamp + kTimeout_us + 1, kStamp, kTimeout_s));
}

TEST(IndiSampleFreshnessTest, SampleFromTheFutureIsNotFresh)
{
	// with a huge timeout only the ordering check can reject it (the unsigned difference would wrap)
	EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(1000, 2000, 1e20f));
	EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(1999, 2000, 1e20f));
	EXPECT_TRUE(IndiMeasuredTorque::isSampleFresh(2000, 2000, 1e20f));
}

TEST(IndiSampleFreshnessTest, NoTimeoutMeansNeverFresh)
{
	// a zero, negative or NaN timeout is not a free pass, not even for a sample of the current cycle
	for (const float timeout_s : {0.f, -0.f, -1.f, -INFINITY, (float)NAN}) {
		EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(2000, 2000, timeout_s)) << timeout_s;
		EXPECT_FALSE(IndiMeasuredTorque::isSampleFresh(2100, 2000, timeout_s)) << timeout_s;
	}
}

TEST_F(IndiFrozenRpmTest, WindowFollowsSetFrozenWindowSeconds)
{
	_model.setFrozenWindow(1.0f);
	IndiMeasuredTorque::Result result{};

	for (int i = 0; i < 360; i++) { // 0.9 s: the 0.5 s window of the fixture would have tripped
		result = cycle(true, 5000.f, 0.f);
	}

	EXPECT_TRUE(result.valid);
	EXPECT_EQ(result.motor_frozen_mask, 0);

	for (int i = 0; i < 100; i++) { // 1.15 s
		result = cycle(true, 5000.f, 0.f);
	}

	EXPECT_FALSE(result.valid);
	EXPECT_EQ(result.motor_frozen_mask, 0x02);
}

TEST_F(IndiFrozenRpmTest, NegativeWindowDoesNotShortenTheDetection)
{
	// a negative window is clamped to zero and must not fall back to a working window: a frozen rpm is not flagged
	_model.setFrozenWindow(-1.0f);
	IndiMeasuredTorque::Result result{};

	for (int i = 0; i < 800; i++) { // 2 s
		result = cycle(true, 5000.f, 0.f);
		ASSERT_EQ(result.motor_frozen_mask, 0) << i;
	}

	EXPECT_TRUE(result.valid);
}

// command pinned at full thrust
TEST_F(IndiFrozenRpmTest, SaturatedConstantCommandWithConstantRpmStaysValid)
{
	// limit by design: with no command variation a constant rpm is not distinguishable from a legitimate one
	for (int i = 0; i < 4000; i++) { // 10 s
		_t += kStep;

		for (int motor = 0; motor < kNumRotors; motor++) {
			_model.setMotorCommand(motor, 1.f, _t);
			_model.setMotorSample(motor, rpmFromThrust(1.f), 0, _t);
		}

		const IndiMeasuredTorque::Result result = _model.compute(_t);
		ASSERT_TRUE(result.valid) << i;
		ASSERT_EQ(result.motor_frozen_mask, 0) << i;
		ASSERT_EQ(result.motor_valid_mask, 0x0F) << i;
	}
}

TEST_F(IndiFrozenRpmTest, CommandDipFromSaturationWithConstantRpmIsFrozen)
{
	IndiMeasuredTorque::Result result{};

	for (int i = 0; i < 400; i++) { // 1 s pinned at 1.0, then a dip to 0.97 (0.03 > 0.02) at a constant rpm
		_t += kStep;
		const float command = (i < 100) ? 1.f : 0.97f;

		for (int motor = 0; motor < kNumRotors; motor++) {
			_model.setMotorCommand(motor, command, _t);
			_model.setMotorSample(motor, rpmFromThrust(1.f), 0, _t);
		}

		result = _model.compute(_t);

		if (i < 100) {
			ASSERT_TRUE(result.valid) << i;
		}
	}

	EXPECT_FALSE(result.valid);
	EXPECT_EQ(result.motor_frozen_mask, 0x0F);
	EXPECT_EQ(result.motor_valid_mask, 0);
}

// Torque against values worked out by hand for a symmetric quad X.
//
// PX4 motor order and spin: 1 front right CCW, 2 rear left CCW, 3 front left CW, 4 rear right CW (FRD frame).
// Per unit of normalised thrust u, rotor i produces roll = -ct * py, pitch = ct * px, yaw = ct * km, so with
// ct = 5, px = py = +-0.2 and km = +-0.1 the torque of u = (u1, u2, u3, u4) is
//   roll  = -u1 + u2 + u3 - u4
//   pitch =  u1 - u2 + u3 - u4
//   yaw   = 0.5 * (u1 + u2 - u3 - u4)
// The pseudo-inverse columns are the rows divided by their squared norm (the rows are orthogonal), so the
// roll/pitch scale is sqrt((4 / 16) / (4 / 2)) = 1 / (2 sqrt(2)) and the yaw scale is the largest entry, 0.5.
// The normalised torque is the torque times these scales.
namespace
{

float rpmFromSpeedRatio(float omega_over_omega_max)
{
	return omega_over_omega_max * kOmegaMax * 60.f / (2.f * M_PI_F);
}

} // namespace

class IndiMeasuredTorqueQuadXTest : public ::testing::Test
{
public:
	void SetUp() override
	{
		const float px[kNumRotors] = {0.2f, -0.2f, 0.2f, -0.2f};
		const float py[kNumRotors] = {0.2f, -0.2f, -0.2f, 0.2f};
		const float km[kNumRotors] = {0.1f, 0.1f, -0.1f, -0.1f};

		ActuatorEffectivenessRotors::Geometry geometry{};
		geometry.num_rotors = kNumRotors;

		for (int i = 0; i < kNumRotors; i++) {
			geometry.rotors[i].position = Vector3f(px[i], py[i], 0.f);
			geometry.rotors[i].axis = Vector3f(0.f, 0.f, -1.f);
			geometry.rotors[i].thrust_coef = 5.f;
			geometry.rotors[i].moment_ratio = km[i];
		}

		ActuatorEffectivenessRotors::computeEffectivenessMatrix(geometry, _effectiveness);
	}

	// @param speed_ratio omega / omega_max of each motor
	IndiMeasuredTorque::Result torqueAt(const float speed_ratio[kNumRotors], bool normalize)
	{
		IndiMeasuredTorque model;
		model.setEffectiveness(_effectiveness, _trim, _linearization_point, kNumRotors, normalize);
		model.setRotorSpeedMax(kOmegaMax);

		for (int motor = 0; motor < kNumRotors; motor++) {
			model.setMotorSample(motor, rpmFromSpeedRatio(speed_ratio[motor]), 0, kNow - 1000);
		}

		return model.compute(kNow);
	}

	static constexpr uint64_t kNow = 1000000;

	ActuatorEffectiveness::EffectivenessMatrix _effectiveness;
	ControlAllocation::ActuatorVector _trim;
	ControlAllocation::ActuatorVector _linearization_point;
};

TEST_F(IndiMeasuredTorqueQuadXTest, HoverGivesNoTorque)
{
	const float speed_ratio[kNumRotors] = {0.5f, 0.5f, 0.5f, 0.5f};

	const IndiMeasuredTorque::Result result = torqueAt(speed_ratio, true);

	ASSERT_TRUE(result.valid);
	EXPECT_NEAR(result.torque[0], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[1], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[2], 0.f, 1e-6f);
}

TEST_F(IndiMeasuredTorqueQuadXTest, OneMotorFasterGivesItsRollPitchYawSigns)
{
	// motor at 0.7 (u = 0.49) while the others are at 0.5 (u = 0.25): du = 0.24 on that motor
	// roll/pitch = +-0.24 / (2 sqrt(2)) = +-0.0848528, yaw = +-0.5 * 0.24 * 0.5 = +-0.06
	const float roll_pitch = 0.0848528f;
	const float yaw = 0.06f;
	const struct {
		int motor;
		float roll;
		float pitch;
		float yaw;
	} cases[] = {
		{0, -roll_pitch, +roll_pitch, +yaw},
		{1, +roll_pitch, -roll_pitch, +yaw},
		{2, +roll_pitch, +roll_pitch, -yaw},
		{3, -roll_pitch, -roll_pitch, -yaw},
	};

	for (const auto &c : cases) {
		float speed_ratio[kNumRotors] = {0.5f, 0.5f, 0.5f, 0.5f};
		speed_ratio[c.motor] = 0.7f;

		const IndiMeasuredTorque::Result result = torqueAt(speed_ratio, true);

		ASSERT_TRUE(result.valid) << "motor " << c.motor;
		EXPECT_NEAR(result.torque[0], c.roll, 1e-5f) << "motor " << c.motor;
		EXPECT_NEAR(result.torque[1], c.pitch, 1e-5f) << "motor " << c.motor;
		EXPECT_NEAR(result.torque[2], c.yaw, 1e-5f) << "motor " << c.motor;
	}
}

TEST_F(IndiMeasuredTorqueQuadXTest, DiagonalPairFasterIsPureYawWithTheSignOfItsSpin)
{
	// pair at 0.7 (u = 0.49), the other pair at 0.5 (u = 0.25): yaw = +-0.5 * 0.5 * (2 * 0.24) = +-0.12
	const float counter_clockwise_pair[kNumRotors] = {0.7f, 0.7f, 0.5f, 0.5f}; // rear left and front right
	const float clockwise_pair[kNumRotors] = {0.5f, 0.5f, 0.7f, 0.7f};         // front left and rear right

	IndiMeasuredTorque::Result result = torqueAt(counter_clockwise_pair, true);
	ASSERT_TRUE(result.valid);
	EXPECT_NEAR(result.torque[0], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[1], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[2], 0.12f, 1e-5f);

	result = torqueAt(clockwise_pair, true);
	ASSERT_TRUE(result.valid);
	EXPECT_NEAR(result.torque[0], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[1], 0.f, 1e-6f);
	EXPECT_NEAR(result.torque[2], -0.12f, 1e-5f);
}

TEST_F(IndiMeasuredTorqueQuadXTest, DifferentSpeedsOnAllMotors)
{
	// speed ratios 0.7, 0.5, 0.4, 0.6 give u = 0.49, 0.25, 0.16, 0.36
	// roll  = -0.49 + 0.25 + 0.16 - 0.36 = -0.44,  scaled -0.44 / (2 sqrt(2)) = -0.155563
	// pitch =  0.49 - 0.25 + 0.16 - 0.36 =  0.04,  scaled  0.04 / (2 sqrt(2)) =  0.0141421
	// yaw   = 0.5 * (0.49 + 0.25 - 0.16 - 0.36) = 0.11, scaled 0.11 * 0.5 = 0.055
	const float speed_ratio[kNumRotors] = {0.7f, 0.5f, 0.4f, 0.6f};

	const IndiMeasuredTorque::Result result = torqueAt(speed_ratio, true);

	ASSERT_TRUE(result.valid);
	EXPECT_NEAR(result.torque[0], -0.155563f, 1e-5f);
	EXPECT_NEAR(result.torque[1], 0.0141421f, 1e-5f);
	EXPECT_NEAR(result.torque[2], 0.055f, 1e-5f);
}

TEST_F(IndiMeasuredTorqueQuadXTest, WithoutNormalisationTheTorqueIsThePhysicalOne)
{
	// same speeds as above, scales are 1: roll -0.44, pitch 0.04, yaw 0.11
	const float speed_ratio[kNumRotors] = {0.7f, 0.5f, 0.4f, 0.6f};

	const IndiMeasuredTorque::Result result = torqueAt(speed_ratio, false);

	ASSERT_TRUE(result.valid);
	EXPECT_NEAR(result.torque[0], -0.44f, 1e-5f);
	EXPECT_NEAR(result.torque[1], 0.04f, 1e-5f);
	EXPECT_NEAR(result.torque[2], 0.11f, 1e-5f);
}
