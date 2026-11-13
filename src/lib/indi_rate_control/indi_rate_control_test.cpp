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
#include <lib/indi_rate_control/indi_rate_control.hpp>

#include <cmath>
#include <limits>

using namespace matrix;

namespace
{

constexpr float kDt = 0.0025f;
constexpr float kG1True = 100.f;
constexpr float kActuatorTc = 0.02f;

/**
 * Roll axis plant: first order actuator, rigid body, measured angular acceleration
 * filtered like PX4's gyro derivative (LPF2p then alpha filter).
 */
class RollPlant
{
public:
	RollPlant()
	{
		_lpf.set_cutoff_frequency(1.f / kDt, 40.f);
		_alpha.setCutoffFreq(1.f / kDt, 20.f);
	}

	/// apply the command for one cycle, returns the torque the allocator actually used
	void step(float torque_applied, float disturbance)
	{
		_torque += (1.f - expf(-kDt / kActuatorTc)) * (torque_applied - _torque);
		const float accel = kG1True * _torque + disturbance;
		_accel_f = _alpha.update(_lpf.apply(accel));
		_rate += accel * kDt;
	}

	float rate() const { return _rate; }
	float accelFiltered() const { return _accel_f; }

private:
	math::LowPassFilter2p<float> _lpf;
	AlphaFilter<float> _alpha;
	float _torque{0.f};
	float _accel_f{0.f};
	float _rate{0.f};
};

IndiRateControl makeController()
{
	IndiRateControl ctrl;
	ctrl.setGainK(Vector3f(20.f, 20.f, 20.f));
	ctrl.setG1(Vector3f(kG1True, kG1True, kG1True));
	ctrl.setG2Yaw(0.f);
	ctrl.setActuatorTimeConstant(kActuatorTc);
	ctrl.setFilterCutoffs(40.f, 20.f);
	ctrl.setDelaySamples(0);
	ctrl.setMaxIncrement(1.f);
	return ctrl;
}

} // namespace

TEST(IndiRateControlTest, ZeroInputsGiveExactlyZero)
{
	IndiRateControl ctrl = makeController();
	ctrl.reset();

	for (int i = 0; i < 400; i++) {
		const Vector3f torque = ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(), kDt, false);
		EXPECT_EQ(torque, Vector3f());
	}

	EXPECT_FALSE(ctrl.getFault());
}

TEST(IndiRateControlTest, RateStepResponse)
{
	IndiRateControl ctrl = makeController();
	RollPlant plant;
	float command = 0.f;
	float max_rate = 0.f;
	bool reached = false;

	for (int i = 0; i < 400; i++) { // 1 s
		const float t = i * kDt;
		const Vector3f torque = ctrl.update(Vector3f(plant.rate(), 0.f, 0.f), Vector3f(1.f, 0.f, 0.f),
						    Vector3f(plant.accelFiltered(), 0.f, 0.f), Vector3f(command, 0.f, 0.f), kDt, false);
		command = torque(0);
		plant.step(command, 0.f);

		max_rate = fmaxf(max_rate, plant.rate());

		if ((t <= 0.5f) && (plant.rate() > 0.95f)) {
			reached = true;
		}

		ASSERT_TRUE(std::isfinite(plant.rate()));
		ASSERT_LE(fabsf(command), 1.f);
	}

	EXPECT_TRUE(reached);
	EXPECT_LT(max_rate, 1.2f); // overshoot < 20 %
	EXPECT_NEAR(plant.rate(), 1.f, 0.05f);
}

TEST(IndiRateControlTest, ConstantDisturbanceRejectedWithoutIntegrator)
{
	IndiRateControl ctrl = makeController();
	RollPlant plant;
	float command = 0.f;

	for (int i = 0; i < 800; i++) { // 2 s
		const Vector3f torque = ctrl.update(Vector3f(plant.rate(), 0.f, 0.f), Vector3f(),
						    Vector3f(plant.accelFiltered(), 0.f, 0.f), Vector3f(command, 0.f, 0.f), kDt, false);
		command = torque(0);
		plant.step(command, -30.f);
		ASSERT_TRUE(std::isfinite(plant.rate()));
	}

	EXPECT_LT(fabsf(plant.rate()), 0.05f);
}

TEST(IndiRateControlTest, SaturatedAllocatorDoesNotWindUp)
{
	IndiRateControl ctrl = makeController();
	RollPlant plant;
	float command = 0.f;
	float allocated = 0.f;

	const int saturated_steps = 800;  // 2 s
	const int release_steps = 400;    // 1 s

	for (int i = 0; i < saturated_steps + release_steps; i++) {
		const bool saturated = i < saturated_steps;
		const float rate_sp = saturated ? 20.f : 0.f;

		const Vector3f torque = ctrl.update(Vector3f(plant.rate(), 0.f, 0.f), Vector3f(rate_sp, 0.f, 0.f),
						    Vector3f(plant.accelFiltered(), 0.f, 0.f), Vector3f(allocated, 0.f, 0.f), kDt, false);
		command = torque(0);

		ASSERT_LE(fabsf(command), 1.f);
		ASSERT_TRUE(std::isfinite(command));

		// the allocator limits the roll torque while saturated, then the limit is lifted
		allocated = saturated ? math::constrain(command, -0.05f, 0.05f) : command;
		plant.step(allocated, 0.f);
		ASSERT_TRUE(std::isfinite(plant.rate()));
	}

	EXPECT_LT(fabsf(plant.rate()), 0.05f);
}

TEST(IndiRateControlTest, LandedOutputIsBoundedIncrementOnly)
{
	IndiRateControl ctrl = makeController();
	Vector3f torque;
	Vector3f torque_prev;

	for (int i = 0; i < 400; i++) { // 1 s, constant rate error 0.5 rad/s, no measured acceleration
		torque = ctrl.update(Vector3f(), Vector3f(0.5f, 0.f, 0.f), Vector3f(), torque_prev, kDt, true);
		torque_prev = torque;

		// nu = 20 * 0.5 = 10 rad/s^2, increment = 10 / 100
		EXPECT_FLOAT_EQ(torque(0), 0.1f);
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	}
}

TEST(IndiRateControlTest, InvalidInputsGiveZeroAndFault)
{
	const float nan = std::numeric_limits<float>::quiet_NaN();
	const float inf = std::numeric_limits<float>::infinity();
	const Vector3f rate(0.1f, 0.2f, 0.3f);
	const Vector3f rate_sp(1.f, 1.f, 1.f);
	const Vector3f accel(1.f, 2.f, 3.f);
	const Vector3f prev(0.1f, 0.1f, 0.1f);
	const Vector3f bad(0.f, nan, 0.f);

	IndiRateControl ctrl = makeController();

	// warm up so that a reset is observable
	Vector3f valid;

	for (int i = 0; i < 20; i++) {
		valid = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
	}

	EXPECT_FALSE(ctrl.getFault());
	EXPECT_NE(valid, Vector3f());

	struct Case {
		Vector3f rate, rate_sp, accel, prev;
		float dt;
	};
	const Case cases[] = {
		{bad, rate_sp, accel, prev, kDt},
		{rate, bad, accel, prev, kDt},
		{rate, rate_sp, bad, prev, kDt},
		{rate, rate_sp, accel, bad, kDt},
		{rate, rate_sp, accel, prev, nan},
		{rate, rate_sp, accel, prev, inf},
		{rate, rate_sp, accel, prev, 0.f},
		{rate, rate_sp, accel, prev, 0.0001f},
		{rate, rate_sp, accel, prev, 0.05f},
		{rate, rate_sp, accel, prev, -kDt},
		{Vector3f(inf, 0.f, 0.f), rate_sp, accel, prev, kDt},
	};

	for (const Case &c : cases) {
		const Vector3f out = ctrl.update(c.rate, c.rate_sp, c.accel, c.prev, c.dt, false);
		EXPECT_EQ(out, Vector3f());
		EXPECT_TRUE(out.isAllFinite());
		EXPECT_TRUE(ctrl.getFault());
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());

		// the next valid call works and clears the fault: from reset states the first output is the P term only
		const Vector3f next = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
		EXPECT_FALSE(ctrl.getFault());
		EXPECT_TRUE(next.isAllFinite());
		EXPECT_GT(fabsf(next(0)), 0.f);
	}

	// invalid effectiveness
	for (int axis = 0; axis < 3; axis++) {
		for (const float g1_bad : {0.f, 0.0005f, -5.f, nan}) {
			Vector3f g1(kG1True, kG1True, kG1True);
			g1(axis) = g1_bad;
			ctrl.setG1(g1);
			const Vector3f out = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
			EXPECT_EQ(out, Vector3f());
			EXPECT_TRUE(ctrl.getFault());
		}
	}

	ctrl.setG1(Vector3f(kG1True, kG1True, kG1True));
	const Vector3f recovered = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
	EXPECT_FALSE(ctrl.getFault());
	EXPECT_TRUE(recovered.isAllFinite());
	EXPECT_NE(recovered, Vector3f());
}

TEST(IndiRateControlTest, YawWithoutSpinUpMatchesRollPitchForm)
{
	IndiRateControl ctrl = makeController();
	ctrl.setG2Yaw(0.f);

	// identical per axis inputs, so every axis must give the same output
	float command = 0.f;

	for (int i = 0; i < 400; i++) {
		const float t = i * kDt;
		const float rate = 0.8f * sinf(6.f * t);
		const float rate_sp = (i % 100 < 50) ? 1.f : -0.5f;
		const float accel = 4.8f * cosf(6.f * t) * 6.f * 0.2f;
		const Vector3f out = ctrl.update(Vector3f(rate, rate, rate), Vector3f(rate_sp, rate_sp, rate_sp),
						 Vector3f(accel, accel, accel), Vector3f(command, command, command), kDt, false);
		EXPECT_EQ(out(2), out(0));
		EXPECT_EQ(out(1), out(0));
		command = out(0);
	}
}

TEST(IndiRateControlTest, YawSpinUpTermChangesYawOnly)
{
	IndiRateControl with_g2 = makeController();
	with_g2.setG2Yaw(2.f);
	IndiRateControl without_g2 = makeController();

	bool yaw_differs = false;
	float command = 0.f;

	for (int i = 0; i < 200; i++) {
		const float rate_sp = (i < 100) ? 1.f : 0.f;
		const Vector3f in_rate(0.f, 0.f, 0.f);
		const Vector3f sp(rate_sp, rate_sp, rate_sp);
		const Vector3f prev(command, command, command);
		const Vector3f a = with_g2.update(in_rate, sp, Vector3f(), prev, kDt, false);
		const Vector3f b = without_g2.update(in_rate, sp, Vector3f(), prev, kDt, false);

		EXPECT_EQ(a(0), b(0));
		EXPECT_EQ(a(1), b(1));
		EXPECT_TRUE(a.isAllFinite());

		if (fabsf(a(2) - b(2)) > 1e-6f) {
			yaw_differs = true;
		}

		command = b(0);
	}

	EXPECT_TRUE(yaw_differs);
}

TEST(IndiRateControlTest, SampleRateChangeRedesignsFiltersWithoutTransient)
{
	IndiRateControl ctrl = makeController();
	const Vector3f prev(0.3f, 0.3f, 0.3f);
	Vector3f out;

	// settle at 400 Hz with a constant allocated torque and matching acceleration
	for (int i = 0; i < 800; i++) {
		out = ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
	}

	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.3f, 1e-3f);

	// switch to 200 Hz, the filtered torque must stay at the settled value
	out = ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, 0.005f, false);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.3f, 1e-3f);
	EXPECT_FALSE(ctrl.getFault());
}

TEST(IndiRateControlTest, PassThroughFiltersAndDelay)
{
	IndiRateControl ctrl = makeController();
	ctrl.setFilterCutoffs(0.f, 0.f); // both stages pass-through
	ctrl.setActuatorTimeConstant(0.001f);
	ctrl.setDelaySamples(2);

	const Vector3f prev(0.5f, 0.5f, 0.5f);

	// with tc = 1 ms and dt = 2.5 ms the actuator model moves 91 % per step, the delay holds the output back
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
	EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
	EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
	EXPECT_GT(ctrl.getFilteredTorque()(0), 0.4f);

	// out of range delay is clamped to 4
	ctrl.setDelaySamples(100);
	ctrl.reset();

	for (int i = 0; i < 4; i++) {
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	}

	ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
	EXPECT_GT(ctrl.getFilteredTorque()(0), 0.4f);
}

namespace
{

constexpr float kDtYaw = 0.004f; // 250 Hz

/// small linear congruential generator, uniform in [-1, 1)
class Lcg
{
public:
	float next()
	{
		_state = _state * 1664525u + 1013904223u;
		return static_cast<float>(_state >> 8) / 8388608.f - 1.f;
	}

private:
	uint32_t _state{12345u};
};

/// Run a noisy closed loop on all axes and return the std of the yaw torque increment.
/// out_roll_pitch receives the sum of the roll and pitch outputs, for equality checks.
float runYawNoise(IndiRateControl &ctrl, float &out_roll_pitch)
{
	Lcg noise_r;
	Lcg noise_p;
	Lcg noise_y;
	Vector3f command;
	float sum = 0.f;
	float sum_sq = 0.f;
	int count = 0;
	out_roll_pitch = 0.f;

	for (int i = 0; i < 1100; i++) {
		const Vector3f accel(20.f * noise_r.next(), 20.f * noise_p.next(), 20.f * noise_y.next());
		command = ctrl.update(Vector3f(), Vector3f(), accel, command, kDtYaw, false);

		if (i >= 100) { // skip the filter start-up
			const float inc = ctrl.getTorqueIncrement()(2);
			sum += inc;
			sum_sq += inc * inc;
			count++;
			out_roll_pitch += command(0) + command(1);
		}
	}

	const float mean = sum / count;
	return sqrtf(sum_sq / count - mean * mean);
}

} // namespace

TEST(IndiRateControlTest, YawCutoffZeroLeavesOutputsUnchanged)
{
	IndiRateControl untouched = makeController();
	IndiRateControl disabled = makeController();
	disabled.setYawCutoff(0.f);

	Lcg noise;
	Vector3f command_a;
	Vector3f command_b;

	for (int i = 0; i < 500; i++) {
		const float a = 10.f * noise.next();
		const float sp = (i % 100 < 50) ? 1.f : -0.5f;
		const Vector3f accel(a, -a, 0.5f * a);
		const Vector3f rate_sp(sp, sp, sp);
		command_a = untouched.update(Vector3f(), rate_sp, accel, command_a, kDtYaw, false);
		command_b = disabled.update(Vector3f(), rate_sp, accel, command_b, kDtYaw, false);

		// bit identical, and the logged feedback pair is the unfiltered one
		EXPECT_EQ(command_a, command_b);
		EXPECT_EQ(disabled.getFilteredAngularAccel(), accel);
	}
}

TEST(IndiRateControlTest, YawCutoffReducesYawNoiseOnly)
{
	IndiRateControl off = makeController();
	IndiRateControl on = makeController();
	on.setYawCutoff(10.f);

	float roll_pitch_off = 0.f;
	float roll_pitch_on = 0.f;
	const float std_off = runYawNoise(off, roll_pitch_off);
	const float std_on = runYawNoise(on, roll_pitch_on);

	EXPECT_GT(std_off, 0.f);
	EXPECT_LT(std_on, 0.7f * std_off);
	EXPECT_EQ(roll_pitch_on, roll_pitch_off); // roll and pitch untouched
	EXPECT_FALSE(on.getFault());
}

TEST(IndiRateControlTest, YawCutoffEnableHasNoTransient)
{
	IndiRateControl ctrl = makeController();
	const float torque = 0.3f;
	const Vector3f prev(torque, torque, torque);
	const Vector3f accel(kG1True * torque, kG1True * torque, kG1True * torque); // t_f * G1 = a_f
	Vector3f out;

	for (int i = 0; i < 1000; i++) { // settle the actuator model and the H filter
		out = ctrl.update(Vector3f(), Vector3f(), accel, prev, kDtYaw, false);
	}

	const Vector3f before = out;
	EXPECT_NEAR(ctrl.getFilteredTorque()(2), torque, 1e-3f);

	ctrl.setYawCutoff(10.f);

	for (int i = 0; i < 50; i++) {
		out = ctrl.update(Vector3f(), Vector3f(), accel, prev, kDtYaw, false);
		EXPECT_NEAR(out(2), before(2), 1e-4f);
		EXPECT_NEAR(ctrl.getFilteredAngularAccel()(2), accel(2), 1e-2f);
		EXPECT_NEAR(ctrl.getFilteredTorque()(2), torque, 1e-3f);
	}

	EXPECT_EQ(out(0), before(0));
	EXPECT_EQ(out(1), before(1));
}

TEST(IndiRateControlTest, YawCutoffInvalidValuesDisableFilter)
{
	const float invalid[] = {std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity(), -5.f, 120.f};

	for (const float cutoff : invalid) { // 120 Hz is above 0.45 x the 250 Hz sample rate
		IndiRateControl reference = makeController();
		IndiRateControl ctrl = makeController();
		ctrl.setYawCutoff(cutoff);

		Lcg noise;
		Vector3f command_a;
		Vector3f command_b;

		for (int i = 0; i < 300; i++) {
			const float a = 10.f * noise.next();
			const Vector3f accel(a, a, a);
			command_a = reference.update(Vector3f(), Vector3f(1.f, 1.f, 1.f), accel, command_a, kDtYaw, false);
			command_b = ctrl.update(Vector3f(), Vector3f(1.f, 1.f, 1.f), accel, command_b, kDtYaw, false);
			EXPECT_EQ(command_a, command_b);
			EXPECT_FALSE(ctrl.getFault());
			EXPECT_TRUE(command_b.isAllFinite());
		}
	}
}
