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

TEST(IndiRateControlTest, InvalidInputsHoldLastOutputAndFault)
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
		// a single bad sample holds the last valid output and leaves the states untouched
		const Vector3f filtered_torque = ctrl.getFilteredTorque();
		const Vector3f out = ctrl.update(c.rate, c.rate_sp, c.accel, c.prev, c.dt, false);
		EXPECT_EQ(out, valid);
		EXPECT_TRUE(ctrl.getFault());
		EXPECT_EQ(ctrl.getFilteredTorque(), filtered_torque);

		// the next valid call works and clears the fault
		valid = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
		EXPECT_FALSE(ctrl.getFault());
		EXPECT_TRUE(valid.isAllFinite());
		EXPECT_GT(fabsf(valid(0)), 0.f);
	}

	// invalid effectiveness, consecutive rejected cycles: held output, then zero torque from reset states
	int rejected = 0;

	for (int axis = 0; axis < 3; axis++) {
		for (const float g1_bad : {0.f, 0.0005f, -5.f, nan}) {
			Vector3f g1(kG1True, kG1True, kG1True);
			g1(axis) = g1_bad;
			ctrl.setG1(g1);
			const Vector3f out = ctrl.update(rate, rate_sp, accel, prev, kDt, false);
			EXPECT_EQ(out, (rejected < IndiRateControl::kFaultHoldCycles) ? valid : Vector3f());
			EXPECT_TRUE(ctrl.getFault());
			rejected++;
		}
	}

	EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());

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

TEST(IndiRateControlTest, DtJitterWithRampingTorqueKeepsOutputContinuous)
{
	// +-20 % dt jitter (hardware gyro publication) while the allocated torque ramps: the design rate is
	// low-passed, so t_f keeps its group delay instead of jumping to the actuator model state
	IndiRateControl ctrl = makeController();
	constexpr float kRampPerS = 2.f;
	float t = 0.f;
	float t_f_prev = 0.f;
	float max_step = 0.f;

	for (int i = 0; i < 400; i++) {
		const float dt = (i % 2 == 0) ? 1.2f * kDt : 0.8f * kDt;
		t += dt;
		const float torque = math::min(kRampPerS * t, 0.8f);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(torque, torque, torque), dt, false);

		if (i > 0) {
			max_step = math::max(max_step, fabsf(ctrl.getFilteredTorque()(0) - t_f_prev));
		}

		t_f_prev = ctrl.getFilteredTorque()(0);
		EXPECT_FALSE(ctrl.getFault());
	}

	// a reset of t_f to the model state jumps by ramp x filter delay (~0.025); the ramp alone moves
	// t_f by at most kRampPerS * 1.2 kDt = 0.006 per cycle
	EXPECT_LT(max_step, 1.5f * kRampPerS * 1.2f * kDt);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.8f, 1e-2f);
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

namespace
{

/// Closed loop with white noise on the measured yaw rate only. Returns the RMS of the sample to sample
/// change of the yaw output, out_roll_pitch receives the sum of the roll and pitch outputs.
float runYawRateNoise(IndiRateControl &ctrl, float &out_roll_pitch)
{
	Lcg noise;
	Vector3f command;
	float prev = 0.f;
	float sum_sq = 0.f;
	int count = 0;
	out_roll_pitch = 0.f;

	for (int i = 0; i < 1100; i++) {
		const Vector3f rate(0.f, 0.f, 0.5f * noise.next());
		command = ctrl.update(rate, Vector3f(), Vector3f(), command, kDtYaw, false);

		if (i >= 100) { // skip the filter start-up
			const float delta = command(2) - prev;
			sum_sq += delta * delta;
			count++;
			out_roll_pitch += command(0) + command(1);
		}

		prev = command(2);
	}

	return sqrtf(sum_sq / count);
}

} // namespace

TEST(IndiRateControlTest, YawRateFilterCutoffZeroLeavesOutputsUnchanged)
{
	IndiRateControl untouched = makeController();
	IndiRateControl disabled = makeController();
	disabled.setYawCutoff(0.f);

	Lcg noise;
	Vector3f command_a;
	Vector3f command_b;

	for (int i = 0; i < 500; i++) { // noisy measured rate on all axes
		const Vector3f rate(0.3f * noise.next(), 0.3f * noise.next(), 0.3f * noise.next());
		const float sp = (i % 100 < 50) ? 1.f : -0.5f;
		const Vector3f rate_sp(sp, sp, sp);
		const Vector3f accel(5.f * noise.next(), 5.f * noise.next(), 5.f * noise.next());
		command_a = untouched.update(rate, rate_sp, accel, command_a, kDtYaw, false);
		command_b = disabled.update(rate, rate_sp, accel, command_b, kDtYaw, false);

		EXPECT_EQ(command_a, command_b);
		EXPECT_EQ(untouched.getNu(), disabled.getNu());
	}
}

TEST(IndiRateControlTest, YawRateFilterReducesYawRateNoiseOnly)
{
	IndiRateControl off = makeController();
	IndiRateControl on = makeController();
	on.setYawCutoff(2.f);

	float roll_pitch_off = 0.f;
	float roll_pitch_on = 0.f;
	const float rms_off = runYawRateNoise(off, roll_pitch_off);
	const float rms_on = runYawRateNoise(on, roll_pitch_on);

	EXPECT_GT(rms_off, 0.f);
	EXPECT_LT(rms_on, rms_off / 3.f);
	EXPECT_EQ(roll_pitch_on, roll_pitch_off); // roll and pitch untouched
	EXPECT_FALSE(on.getFault());
}

TEST(IndiRateControlTest, YawRateFilterSteadyStateNuIsGainTimesError)
{
	IndiRateControl ctrl = makeController();
	ctrl.setYawCutoff(2.f);

	const float rate_sp = 1.f;
	const float rate_meas = 0.4f;
	Vector3f command;

	for (int i = 0; i < 1500; i++) { // 6 s, many filter time constants
		command = ctrl.update(Vector3f(0.f, 0.f, rate_meas), Vector3f(0.f, 0.f, rate_sp), Vector3f(), command, kDtYaw, false);
	}

	// the gain is not exposed, so compare with the unfiltered controller which gives K_Y * (r_sp - r) at once
	IndiRateControl ref = makeController();
	ref.update(Vector3f(0.f, 0.f, rate_meas), Vector3f(0.f, 0.f, rate_sp), Vector3f(), Vector3f(), kDtYaw, false);

	EXPECT_GT(ref.getNu()(2), 0.f);
	EXPECT_NEAR(ctrl.getNu()(2), ref.getNu()(2), 1e-4f * ref.getNu()(2));
}

TEST(IndiRateControlTest, YawCutoffSmoothsYawRateSetpointStep)
{
	IndiRateControl off = makeController();
	IndiRateControl on = makeController();
	on.setYawCutoff(2.f);

	Vector3f command_off;
	Vector3f command_on;
	const Vector3f rate_sp(0.f, 0.f, 1.f);

	for (int i = 0; i < 50; i++) { // settle at zero error so the filters are initialised
		command_off = off.update(Vector3f(), Vector3f(), Vector3f(), command_off, kDtYaw, false);
		command_on = on.update(Vector3f(), Vector3f(), Vector3f(), command_on, kDtYaw, false);
	}

	command_off = off.update(Vector3f(), rate_sp, Vector3f(), command_off, kDtYaw, false);
	command_on = on.update(Vector3f(), rate_sp, Vector3f(), command_on, kDtYaw, false);

	// unfiltered nu jumps to K_Y at once, the filtered one only starts to rise
	EXPECT_GT(off.getNu()(2), 0.f);
	EXPECT_GT(on.getNu()(2), 0.f);
	EXPECT_LT(on.getNu()(2), 0.1f * off.getNu()(2));
	EXPECT_EQ(on.getNu()(0), off.getNu()(0));
	EXPECT_EQ(on.getNu()(1), off.getNu()(1));

	for (int i = 0; i < 1500; i++) { // 6 s, many filter time constants
		command_off = off.update(Vector3f(), rate_sp, Vector3f(), command_off, kDtYaw, false);
		command_on = on.update(Vector3f(), rate_sp, Vector3f(), command_on, kDtYaw, false);
	}

	EXPECT_NEAR(on.getNu()(2), off.getNu()(2), 1e-3f * off.getNu()(2));
	EXPECT_FALSE(on.getFault());
}

TEST(IndiRateControlTest, LandedYawOutputUnaffectedByYawCutoff)
{
	IndiRateControl ctrl = makeController();
	ctrl.setYawCutoff(2.f);
	Vector3f torque;

	for (int i = 0; i < 400; i++) { // 1 s on ground, constant yaw rate error 0.5 rad/s
		torque = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.5f), Vector3f(), torque, kDt, true);

		// the yaw filters restart from the current input each landed cycle: same P form as roll in
		// LandedOutputIsBoundedIncrementOnly, nu = 20 * 0.5 = 10 rad/s^2, increment = 10 / 100
		EXPECT_NEAR(torque(2), 0.1f, 1e-4f); // filter reset then apply rounds in float
	}

	// takeoff: the first airborne cycle adds the modelled torque, settled at the landed output, to the same
	// increment, the yaw filters continue from the landed values
	const Vector3f airborne = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.5f), Vector3f(), torque, kDt, false);
	EXPECT_NEAR(airborne(2), 0.2f, 0.01f);
}

TEST(IndiRateControlTest, LandedKeepsActuatorModelRunning)
{
	IndiRateControl ctrl = makeController();
	ctrl.setMaxIncrement(0.05f);
	Vector3f torque;

	for (int i = 0; i < 400; i++) { // 1 s on ground (maybe_landed), constant roll rate error 0.5 rad/s
		torque = ctrl.update(Vector3f(), Vector3f(0.5f, 0.f, 0.f), Vector3f(), torque, kDt, true);
		EXPECT_FLOAT_EQ(torque(0), 0.05f); // increment only, clamped
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	}

	// takeoff: the model already follows the applied torque, the step is one bounded increment
	const Vector3f airborne = ctrl.update(Vector3f(), Vector3f(0.5f, 0.f, 0.f), Vector3f(), torque, kDt, false);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.05f, 1e-3f);
	EXPECT_NEAR(airborne(0), 0.1f, 1e-3f);
	EXPECT_LE(airborne(0) - torque(0), 0.05f + 1e-3f);
}

TEST(IndiRateControlTest, DelayChangeMidRunMovesOneSamplePerCycle)
{
	IndiRateControl ctrl = makeController();
	ctrl.setFilterCutoffs(0.f, 0.f); // pass-through, so t_f is the delayed actuator model output
	ctrl.setActuatorTimeConstant(0.001f);

	// applied torque ramps up by 0.002 per cycle; with tc = 1 ms the model tracks it within one ramp step
	const float slope = 0.002f;
	Vector3f prev;
	float t_f_last = 0.f;

	for (int i = 0; i < 40; i++) {
		prev = Vector3f(slope * i, 0.f, 0.f);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
		t_f_last = ctrl.getFilteredTorque()(0);
	}

	// 0 -> 4 in flight: t_f holds for 4 cycles instead of jumping back 4 cycles of history
	ctrl.setDelaySamples(4);

	for (int i = 40; i < 50; i++) {
		prev = Vector3f(slope * i, 0.f, 0.f);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
		const float t_f = ctrl.getFilteredTorque()(0);
		EXPECT_GE(t_f, t_f_last - 1e-6f);
		EXPECT_LE(t_f - t_f_last, slope + 1e-4f);
		t_f_last = t_f;
	}

	// 4 -> 0: one skipped sample per cycle, never a jump of the whole delay
	ctrl.setDelaySamples(0);

	for (int i = 50; i < 60; i++) {
		prev = Vector3f(slope * i, 0.f, 0.f);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), prev, kDt, false);
		const float t_f = ctrl.getFilteredTorque()(0);
		EXPECT_GE(t_f, t_f_last - 1e-6f);
		EXPECT_LE(t_f - t_f_last, 2.f * slope + 1e-4f);
		t_f_last = t_f;
	}

	// settled at delay 0: the model output trails the applied torque by less than one ramp step
	EXPECT_NEAR(t_f_last, slope * 59, slope);
}

TEST(IndiRateControlTest, InvalidMaxIncrementKeepsLastValidLimit)
{
	IndiRateControl ctrl = makeController();
	ctrl.setMaxIncrement(0.05f);
	ctrl.setMaxIncrement(0.f);
	ctrl.setMaxIncrement(-1.f);
	ctrl.setMaxIncrement(NAN);

	// a large rate error asks for far more than 0.05, the limit set before the invalid values still applies
	const Vector3f torque = ctrl.update(Vector3f(), Vector3f(1.f, 0.f, 0.f), Vector3f(), Vector3f(), kDt, false);
	EXPECT_NEAR(torque(0), 0.05f, 1e-6f);
}

namespace
{

constexpr int kN = IndiRateControl::kMeasValidCycles;

/// varying but deterministic inputs for the measurement path tests
struct Excitation {
	Vector3f rate;
	Vector3f rate_sp;
	Vector3f accel;
	Vector3f alloc;
};

Excitation excitation(int i)
{
	const float t = i * kDt;
	Excitation e;
	e.rate = Vector3f(0.3f * sinf(7.f * t), 0.2f * cosf(5.f * t), 0.1f * sinf(3.f * t));
	e.rate_sp = Vector3f(0.5f * sinf(2.f * t), 0.4f * cosf(1.5f * t), 0.2f * sinf(t));
	e.accel = Vector3f(2.f * sinf(11.f * t), 1.5f * cosf(9.f * t), 0.5f * sinf(4.f * t));
	e.alloc = Vector3f(0.4f * sinf(6.f * t), 0.3f * cosf(8.f * t), 0.2f * sinf(2.5f * t));
	return e;
}

Vector3f step(IndiRateControl &ctrl, int i)
{
	const Excitation e = excitation(i);
	return ctrl.update(e.rate, e.rate_sp, e.accel, e.alloc, kDt, false);
}

/// constant measured torque, zero everything else, returns after n cycles
void runConstantMeasurement(IndiRateControl &ctrl, const Vector3f &alloc, const Vector3f &meas, int n)
{
	for (int i = 0; i < n; i++) {
		ctrl.setMeasuredTorque(meas, true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}
}

} // namespace

TEST(IndiRateControlMeasurementTest, NeverValidIsBitIdenticalToModelOnly)
{
	IndiRateControl ref = makeController();
	IndiRateControl ctrl = makeController();
	ctrl.setMeasurementDelaySamples(3);
	ref.setDelaySamples(2);
	ctrl.setDelaySamples(2);
	ref.setYawCutoff(15.f);
	ctrl.setYawCutoff(15.f);
	ref.setG2Yaw(0.5f);
	ctrl.setG2Yaw(0.5f);

	for (int i = 0; i < 600; i++) {
		// measurement supplied but never valid, with garbage content, and cycles with no call at all
		if (i % 2 == 0) {
			ctrl.setMeasuredTorque(Vector3f(0.9f, -0.9f, 0.7f), false);
		}

		const Vector3f a = step(ref, i);
		const Vector3f b = step(ctrl, i);
		ASSERT_EQ(a, b) << "cycle " << i;
		ASSERT_EQ(ref.getFilteredTorque(), ctrl.getFilteredTorque());
		ASSERT_FALSE(ctrl.measurementInUse());
	}
}

TEST(IndiRateControlMeasurementTest, MeasurementEqualToModelSwitchesWithoutTransient)
{
	IndiRateControl ref = makeController();
	IndiRateControl ctrl = makeController();
	Vector3f meas;
	const float alpha = 1.f - expf(-kDt / kActuatorTc);
	bool in_use_seen = false;

	for (int i = 0; i < 400; i++) {
		const Excitation e = excitation(i);
		// the actuator model run outside the library on the same allocated torque
		meas += alpha * (e.alloc - meas);
		ctrl.setMeasuredTorque(meas, true);

		const Vector3f a = step(ref, i);
		const Vector3f b = step(ctrl, i);
		in_use_seen = in_use_seen || ctrl.measurementInUse();

		for (int k = 0; k < 3; k++) {
			ASSERT_NEAR(a(k), b(k), 1e-4f) << "cycle " << i << " axis " << k;
		}
	}

	EXPECT_TRUE(in_use_seen);
	EXPECT_TRUE(ctrl.measurementInUse());
}

TEST(IndiRateControlMeasurementTest, SwitchesOnlyAfterRequiredValidCycles)
{
	IndiRateControl ctrl = makeController();

	for (int i = 1; i <= kN + 5; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(0.5f, 0.f, 0.f), kDt, false);
		// the kN-th consecutive valid cycle is the first to use the measurement
		EXPECT_EQ(ctrl.measurementInUse(), i >= kN) << "cycle " << i;
	}
}

TEST(IndiRateControlMeasurementTest, OneInvalidCycleFallsBackAndRestartsCount)
{
	IndiRateControl ctrl = makeController();
	const Vector3f alloc(0.5f, 0.f, 0.f);
	runConstantMeasurement(ctrl, alloc, Vector3f(0.3f, 0.f, 0.f), 300);
	ASSERT_TRUE(ctrl.measurementInUse());
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.3f, 1e-3f);

	// a cycle without any setMeasuredTorque() call is invalid
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	EXPECT_FALSE(ctrl.measurementInUse());
	EXPECT_EQ(ctrl.getFilteredTorque(), ctrl.getFilteredModelTorque());

	// an explicit valid = false is the same, the counter starts over
	ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), false);
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	EXPECT_FALSE(ctrl.measurementInUse());

	for (int i = 1; i <= kN; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
		EXPECT_EQ(ctrl.measurementInUse(), i >= kN) << "cycle " << i;
	}

	// a rejected cycle (non finite input) counts as invalid too
	ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
	ctrl.update(Vector3f(NAN, 0.f, 0.f), Vector3f(), Vector3f(), alloc, kDt, false);
	EXPECT_TRUE(ctrl.getFault());
	EXPECT_FALSE(ctrl.measurementInUse());
}

TEST(IndiRateControlMeasurementTest, InvalidFeedKeepsMeasurementFiltersNearModel)
{
	IndiRateControl ctrl = makeController();
	const Vector3f alloc(0.5f, -0.2f, 0.1f);

	// invalid for a long time: the measurement filters follow the model, not the stale content
	for (int i = 0; i < 300; i++) {
		ctrl.setMeasuredTorque(Vector3f(-0.9f, 0.9f, -0.9f), false);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}

	for (int k = 0; k < 3; k++) {
		EXPECT_NEAR(ctrl.getFilteredMeasuredTorque()(k), alloc(k), 1e-3f);
		EXPECT_NEAR(ctrl.getFilteredModelTorque()(k), alloc(k), 1e-3f);
	}
}

TEST(IndiRateControlMeasurementTest, NonFiniteMeasurementIsInvalid)
{
	IndiRateControl ctrl = makeController();
	const Vector3f alloc(0.5f, 0.f, 0.f);
	runConstantMeasurement(ctrl, alloc, Vector3f(0.3f, 0.f, 0.f), 300);
	ASSERT_TRUE(ctrl.measurementInUse());

	const float bad[3] = {NAN, INFINITY, -INFINITY};

	for (int k = 0; k < 3; k++) {
		Vector3f meas(0.3f, 0.f, 0.f);
		meas(k) = bad[k];
		ctrl.setMeasuredTorque(meas, true); // flagged valid but not finite
		const Vector3f torque = ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
		EXPECT_FALSE(ctrl.measurementInUse());
		EXPECT_TRUE(torque.isAllFinite());
		EXPECT_FALSE(ctrl.getFault());
		EXPECT_TRUE(ctrl.getFilteredMeasuredTorque().isAllFinite());
	}

	// the filters were not poisoned: valid cycles bring the measurement back
	runConstantMeasurement(ctrl, alloc, Vector3f(0.3f, 0.f, 0.f), 300);
	EXPECT_TRUE(ctrl.measurementInUse());
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.3f, 1e-3f);
}

TEST(IndiRateControlMeasurementTest, MeasurementDelayClampsAndSlewsOneSamplePerCycle)
{
	IndiRateControl ctrl = makeController();
	ctrl.setFilterCutoffs(0.f, 0.f); // pass-through, so the filtered measurement is the delayed measurement

	const float slope = 0.002f;
	float last = 0.f;

	for (int i = 0; i < 40; i++) {
		ctrl.setMeasuredTorque(Vector3f(slope * i, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(), kDt, false);
		last = ctrl.getFilteredMeasuredTorque()(0);
	}

	EXPECT_NEAR(last, slope * 39, 1e-6f); // delay 0

	// 0 -> 4 in flight, requested far above the maximum: held back one sample per cycle, clamped at 4
	ctrl.setMeasurementDelaySamples(100);

	for (int i = 40; i < 50; i++) {
		ctrl.setMeasuredTorque(Vector3f(slope * i, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(), kDt, false);
		const float value = ctrl.getFilteredMeasuredTorque()(0);
		EXPECT_GE(value, last - 1e-6f);
		EXPECT_LE(value - last, slope + 1e-6f);
		last = value;
	}

	EXPECT_NEAR(last, slope * (49 - IndiRateControl::kMaxDelaySamples), 1e-6f);

	// 4 -> 0 (negative request clamps to 0): one skipped sample per cycle
	ctrl.setMeasurementDelaySamples(-3);

	for (int i = 50; i < 60; i++) {
		ctrl.setMeasuredTorque(Vector3f(slope * i, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(), kDt, false);
		const float value = ctrl.getFilteredMeasuredTorque()(0);
		EXPECT_GE(value, last - 1e-6f);
		EXPECT_LE(value - last, 2.f * slope + 1e-6f);
		last = value;
	}

	EXPECT_NEAR(last, slope * 59, 1e-6f);

	// the model path delay is independent: still 0, the model output is not shifted by the measurement delay
	EXPECT_NEAR(ctrl.getFilteredModelTorque()(0), 0.f, 1e-6f);
}

TEST(IndiRateControlMeasurementTest, FollowsMeasurementWhenModelIsWrong)
{
	// the model time constant is 10 x too slow for the 0.5 allocated torque that is not what is measured
	IndiRateControl ctrl = makeController();
	ctrl.setActuatorTimeConstant(0.2f);
	const Vector3f alloc(0.5f, 0.f, -0.4f);
	const Vector3f meas(0.3f, 0.1f, -0.1f);

	// model only: t_f converges to the allocated torque
	for (int i = 0; i < 1200; i++) {
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}

	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.5f, 1e-3f);

	// measurement valid: after the switch t_f settles at the measurement and the command with it (zero error)
	Vector3f torque;

	for (int i = 0; i < 1200; i++) {
		ctrl.setMeasuredTorque(meas, true);
		torque = ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}

	ASSERT_TRUE(ctrl.measurementInUse());

	for (int k = 0; k < 3; k++) {
		EXPECT_NEAR(ctrl.getFilteredTorque()(k), meas(k), 1e-3f);
		EXPECT_NEAR(torque(k), meas(k), 1e-3f);
	}

	// the model path keeps its own value
	EXPECT_NEAR(ctrl.getFilteredModelTorque()(0), 0.5f, 1e-3f);
}

TEST(IndiRateControlMeasurementTest, LandedUsesMeasurementLikeModel)
{
	IndiRateControl ctrl = makeController();
	Vector3f torque;

	for (int i = 0; i < 100; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
		torque = ctrl.update(Vector3f(), Vector3f(0.5f, 0.f, 0.f), Vector3f(), Vector3f(), kDt, true);
		EXPECT_FLOAT_EQ(torque(0), 0.1f); // increment only, as with the model
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
	}

	// the measurement path ran on ground and is already in use at takeoff
	EXPECT_TRUE(ctrl.measurementInUse());
	EXPECT_NEAR(ctrl.getFilteredMeasuredTorque()(0), 0.3f, 1e-3f);
	ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
	torque = ctrl.update(Vector3f(), Vector3f(0.5f, 0.f, 0.f), Vector3f(), Vector3f(), kDt, false);
	EXPECT_NEAR(torque(0), 0.4f, 1e-3f);
}

TEST(IndiRateControlMeasurementTest, ResetClearsMeasurementPath)
{
	IndiRateControl ctrl = makeController();
	ctrl.setMeasurementDelaySamples(2);
	runConstantMeasurement(ctrl, Vector3f(0.5f, 0.f, 0.f), Vector3f(0.3f, 0.f, 0.f), 300);
	ASSERT_TRUE(ctrl.measurementInUse());

	ctrl.reset();
	EXPECT_FALSE(ctrl.measurementInUse());
	EXPECT_EQ(ctrl.getFilteredMeasuredTorque(), Vector3f());

	// a pending measurement is not carried over by reset() only if it is re-supplied; counting restarts at zero
	for (int i = 1; i <= kN; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.3f, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), Vector3f(0.5f, 0.f, 0.f), kDt, false);
		EXPECT_EQ(ctrl.measurementInUse(), i >= kN) << "cycle " << i;
	}
}

TEST(IndiRateControlMeasurementTest, SampleRateChangeKeepsMeasurementFiltersContinuous)
{
	IndiRateControl ctrl = makeController();
	const Vector3f alloc(0.5f, 0.f, 0.f);
	const Vector3f meas(0.3f, 0.f, 0.f);

	for (int i = 0; i < 400; i++) {
		ctrl.setMeasuredTorque(meas, true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}

	ASSERT_TRUE(ctrl.measurementInUse());

	// 400 Hz -> 800 Hz redesigns the filters, the filtered measurement must not jump
	for (int i = 0; i < 400; i++) {
		ctrl.setMeasuredTorque(meas, true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt / 2.f, false);
		ASSERT_NEAR(ctrl.getFilteredMeasuredTorque()(0), 0.3f, 2e-3f) << "cycle " << i;
	}
}

TEST(IndiRateControlMeasurementTest, NormalisedThrustFromRpm)
{
	float u = -1.f;

	EXPECT_TRUE(IndiRateControl::normalisedThrustFromRpm(0.f, 10000.f, u));
	EXPECT_FLOAT_EQ(u, 0.f);
	EXPECT_TRUE(IndiRateControl::normalisedThrustFromRpm(5000.f, 10000.f, u));
	EXPECT_FLOAT_EQ(u, 0.25f);
	EXPECT_TRUE(IndiRateControl::normalisedThrustFromRpm(10000.f, 10000.f, u));
	EXPECT_FLOAT_EQ(u, 1.f);

	// above rpm_max but plausible: clamped to 1
	EXPECT_TRUE(IndiRateControl::normalisedThrustFromRpm(12000.f, 10000.f, u));
	EXPECT_FLOAT_EQ(u, 1.f);
	EXPECT_TRUE(IndiRateControl::normalisedThrustFromRpm(15000.f, 10000.f, u));
	EXPECT_FLOAT_EQ(u, 1.f);

	// rejected cases leave u untouched
	u = 0.123f;
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(15001.f, 10000.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(-1.f, 10000.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(5000.f, 0.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(5000.f, -10000.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(NAN, 10000.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(INFINITY, 10000.f, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(5000.f, NAN, u));
	EXPECT_FALSE(IndiRateControl::normalisedThrustFromRpm(5000.f, INFINITY, u));
	EXPECT_FLOAT_EQ(u, 0.123f);
}
