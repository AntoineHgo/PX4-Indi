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
#include <complex>
#include <vector>
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
	ctrl.setLeadScale(0.f); // the rate lead has dedicated tests
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

TEST(IndiRateControlBlendTest, DisabledIsBitIdenticalToNoSetterCall)
{
	const float disabled[] = {0.f, NAN, -0.5f, -INFINITY};

	for (const float tb : disabled) {
		IndiRateControl ref = makeController();
		IndiRateControl ctrl = makeController();
		ctrl.setActuatorBlendTimeConstant(tb);

		for (int i = 0; i < 400; i++) {
			// valid measurement that differs from the model
			ref.setMeasuredTorque(Vector3f(0.2f, -0.1f, 0.3f), true);
			ctrl.setMeasuredTorque(Vector3f(0.2f, -0.1f, 0.3f), true);
			const Vector3f a = step(ref, i);
			const Vector3f b = step(ctrl, i);
			ASSERT_EQ(a, b) << "tb " << tb << " cycle " << i;
			ASSERT_EQ(ref.getFilteredTorque(), ctrl.getFilteredTorque());
		}

		ASSERT_TRUE(ctrl.measurementInUse());
		EXPECT_EQ(ctrl.getFilteredTorque(), ctrl.getFilteredMeasuredTorque());
	}
}

TEST(IndiRateControlBlendTest, SteadyGapConvergesToModel)
{
	const Vector3f alloc(0.5f, 0.f, 0.f);
	const Vector3f meas(0.35f, 0.f, 0.f); // 0.7 x the settled model torque
	IndiRateControl ctrl = makeController();
	IndiRateControl ref = makeController();
	ctrl.setActuatorBlendTimeConstant(0.3f);

	// 1200 cycles of kDt are 10 Tb
	runConstantMeasurement(ctrl, alloc, meas, 1200);
	runConstantMeasurement(ref, alloc, meas, 1200);

	ASSERT_TRUE(ctrl.measurementInUse());
	EXPECT_NEAR(ctrl.getFilteredModelTorque()(0), 0.5f, 1e-3f);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), ctrl.getFilteredModelTorque()(0), 0.01f * 0.5f);
	EXPECT_NEAR(ctrl.getActuatorBlend()(0), 0.15f, 1e-3f);

	// without the blend the fed back torque is the measured value
	EXPECT_NEAR(ref.getFilteredTorque()(0), 0.35f, 1e-3f);
}

TEST(IndiRateControlBlendTest, HighFrequencyFollowsMeasurement)
{
	const Vector3f alloc(0.5f, 0.f, 0.f);
	IndiRateControl ctrl = makeController();
	IndiRateControl ref = makeController();
	ctrl.setActuatorBlendTimeConstant(0.3f);
	runConstantMeasurement(ctrl, alloc, Vector3f(0.35f, 0.f, 0.f), 1200);
	runConstantMeasurement(ref, alloc, Vector3f(0.35f, 0.f, 0.f), 1200);
	const float t_f_before = ctrl.getFilteredTorque()(0);
	const float ref_before = ref.getFilteredTorque()(0);

	// step of the measured torque only, the allocated torque stays the same
	runConstantMeasurement(ctrl, alloc, Vector3f(0.65f, 0.f, 0.f), 6);
	runConstantMeasurement(ref, alloc, Vector3f(0.65f, 0.f, 0.f), 6);

	const float response = ctrl.getFilteredTorque()(0) - t_f_before;
	const float ref_response = ref.getFilteredTorque()(0) - ref_before;
	ASSERT_GT(ref_response, 0.05f);
	EXPECT_GE(response, 0.9f * ref_response);
}

TEST(IndiRateControlBlendTest, SwitchFromModelToMeasurementIsBumpless)
{
	const Vector3f alloc(0.5f, 0.f, 0.f);
	IndiRateControl ctrl = makeController();
	ctrl.setActuatorBlendTimeConstant(0.3f);

	// measurement invalid, the model settles
	for (int i = 0; i < 300; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.35f, 0.f, 0.f), false);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	}

	float t_f_prev = ctrl.getFilteredTorque()(0);
	float model_prev = ctrl.getFilteredModelTorque()(0);
	bool switched = false;

	for (int i = 1; i <= kN + 5; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.35f, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
		const float t_f = ctrl.getFilteredTorque()(0);
		const float model = ctrl.getFilteredModelTorque()(0);
		// the measurement filters are still converging from the model value, a few 1e-4 per cycle, against a gap of 0.15
		EXPECT_LE(fabsf(t_f - t_f_prev), fabsf(model - model_prev) + 1e-3f) << "cycle " << i;
		switched = switched || ctrl.measurementInUse();
		t_f_prev = t_f;
		model_prev = model;
	}

	EXPECT_TRUE(switched);
}

TEST(IndiRateControlBlendTest, LandedBlendTracksWithoutAccumulating)
{
	const Vector3f alloc(0.5f, 0.f, 0.f);
	IndiRateControl ctrl = makeController();
	ctrl.setActuatorBlendTimeConstant(0.3f);

	// on ground with a gap between model and measurement
	for (int i = 0; i < 600; i++) {
		ctrl.setMeasuredTorque(Vector3f(0.35f, 0.f, 0.f), true);
		ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, true);
		EXPECT_EQ(ctrl.getFilteredTorque(), Vector3f());
		EXPECT_NEAR(ctrl.getActuatorBlend()(0),
			    ctrl.getFilteredModelTorque()(0) - ctrl.getFilteredMeasuredTorque()(0), 1e-6f);
	}

	ASSERT_TRUE(ctrl.measurementInUse());

	// the first airborne value is the modelled torque, no blend memory of its own
	ctrl.setMeasuredTorque(Vector3f(0.35f, 0.f, 0.f), true);
	ctrl.update(Vector3f(), Vector3f(), Vector3f(), alloc, kDt, false);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), ctrl.getFilteredModelTorque()(0), 1e-4f);
	EXPECT_NEAR(ctrl.getFilteredTorque()(0), 0.5f, 1e-3f);
}

// ---------------------------------------------------------------------------------------------------------------
// Rate prediction lead (D-RATE-LEAD): num_i = nu_i - (1 + c_i) a_f_i + ..., c_i = lead K_i tau_c, 0 on ground, <= 2
// ---------------------------------------------------------------------------------------------------------------

namespace
{

/// controller for the lead tests: K 20/40/10, G1 100, ACT_TC 0.02, no filters on a_f (the argument is used as is)
IndiRateControl makeLeadController(float lead)
{
	IndiRateControl ctrl = makeController();
	ctrl.setGainK(Vector3f(20.f, 40.f, 10.f));
	ctrl.setLeadScale(lead);
	return ctrl;
}

} // namespace

TEST(IndiRateControlLeadTest, LeadZeroIsBitIdentical)
{
	// scale 0 is the law without lead, however it is set (0, NaN and negative all give 0), on a noisy sequence
	IndiRateControl a = makeLeadController(0.f);
	IndiRateControl b = makeLeadController(std::numeric_limits<float>::quiet_NaN());
	IndiRateControl c = makeLeadController(-3.f);
	IndiRateControl on = makeLeadController(1.f);
	bool lead_differs = false;

	for (int i = 0; i < 600; i++) {
		const Vector3f ua = step(a, i);
		ASSERT_EQ(ua, step(b, i)) << i;
		ASSERT_EQ(ua, step(c, i)) << i;
		lead_differs = lead_differs || (step(on, i) != ua);
	}

	EXPECT_TRUE(lead_differs);

	// first cycle against the law written out: t = (K e - a_f)/G1 exactly as before the lead was added
	IndiRateControl d = makeLeadController(0.f);
	const Vector3f out = d.update(Vector3f(), Vector3f(1.f, 1.f, 1.f), Vector3f(5.f, 5.f, 5.f), Vector3f(), kDt, false);
	EXPECT_EQ(out(0), (20.f * 1.f - 5.f) / kG1True);
	EXPECT_EQ(out(1), (40.f * 1.f - 5.f) / kG1True);
	EXPECT_EQ(out(2), (10.f * 1.f - 5.f) / kG1True);
}

TEST(IndiRateControlLeadTest, DefaultScaleIsOne)
{
	IndiRateControl ctrl; // never called setLeadScale
	ctrl.setGainK(Vector3f(20.f, 20.f, 20.f));
	ctrl.setG1(Vector3f(kG1True, kG1True, kG1True));
	ctrl.setActuatorTimeConstant(0.02f);
	ctrl.update(Vector3f(), Vector3f(), Vector3f(1.f, 0.f, 0.f), Vector3f(), kDt, false);
	EXPECT_NEAR(ctrl.getLeadGain()(0), 0.4f, 1e-6f);
}

TEST(IndiRateControlLeadTest, LeadAddsKTauAccel)
{
	IndiRateControl ctrl = makeLeadController(1.f);
	const Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(5.f, 0.f, 0.f), Vector3f(), kDt, false);
	EXPECT_NEAR(out(0), -(1.f + 20.f * 0.02f) * 5.f / kG1True, 1e-6f); // -0.07, not -0.03 (sign flip) or -0.05 (no tau)
	EXPECT_NEAR(ctrl.getLeadGain()(0), 0.4f, 1e-6f);
	EXPECT_EQ(ctrl.getNu()(0), 0.f); // nu stays K e
}

TEST(IndiRateControlLeadTest, LeadUsesActuatorTc)
{
	IndiRateControl ctrl = makeLeadController(1.f);
	ctrl.setActuatorTimeConstant(0.05f);
	const Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(5.f, 0.f, 0.f), Vector3f(), kDt, false);
	EXPECT_NEAR(out(0), -(1.f + 20.f * 0.05f) * 5.f / kG1True, 1e-6f);
}

TEST(IndiRateControlLeadTest, LeadPerAxisGain)
{
	IndiRateControl ctrl = makeLeadController(1.f);
	Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(5.f, 5.f, 5.f), Vector3f(), kDt, false);
	EXPECT_NEAR(out(0), -(1.f + 20.f * 0.02f) * 5.f / kG1True, 1e-6f);
	EXPECT_NEAR(out(1), -(1.f + 40.f * 0.02f) * 5.f / kG1True, 1e-6f);
	EXPECT_NEAR(out(2), -(1.f + 10.f * 0.02f) * 5.f / kG1True, 1e-6f);

	IndiRateControl pitch_only = makeLeadController(1.f);
	out = pitch_only.update(Vector3f(), Vector3f(), Vector3f(0.f, 5.f, 0.f), Vector3f(), kDt, false);
	EXPECT_EQ(out(0), 0.f);
	EXPECT_EQ(out(2), 0.f);
	EXPECT_NEAR(out(1), -(1.f + 40.f * 0.02f) * 5.f / kG1True, 1e-6f);
}

TEST(IndiRateControlLeadTest, LeadRateErrorUnchanged)
{
	IndiRateControl on = makeLeadController(1.f);
	IndiRateControl off = makeLeadController(0.f);

	for (int i = 0; i < 50; i++) {
		const Vector3f a = on.update(Vector3f(), Vector3f(1.f, -1.f, 0.5f), Vector3f(), Vector3f(), kDt, false);
		const Vector3f b = off.update(Vector3f(), Vector3f(1.f, -1.f, 0.5f), Vector3f(), Vector3f(), kDt, false);
		ASSERT_EQ(a, b);
		ASSERT_EQ(on.getNu(), off.getNu());
	}
}

TEST(IndiRateControlLeadTest, LeadOffWhenLanded)
{
	IndiRateControl on = makeLeadController(1.f);
	IndiRateControl off = makeLeadController(0.f);

	for (int i = 0; i < 100; i++) {
		const Excitation e = excitation(i);
		const Vector3f a = on.update(e.rate, e.rate_sp, e.accel, e.alloc, kDt, true);
		const Vector3f b = off.update(e.rate, e.rate_sp, e.accel, e.alloc, kDt, true);
		ASSERT_EQ(a, b) << i;
		ASSERT_EQ(on.getLeadGain(), Vector3f());
	}
}

TEST(IndiRateControlLeadTest, LeadYawWithSpinUp)
{
	IndiRateControl ctrl = makeLeadController(1.f);
	ctrl.setG2Yaw(2.f);
	const Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(0.f, 0.f, 5.f), Vector3f(), kDt, false);
	const float c_y = 10.f * 0.02f;
	// the lead sits in the numerator, inside the (G1 + G2/dt) denominator
	EXPECT_NEAR(out(2), -(1.f + c_y) * 5.f / (kG1True + 2.f / kDt), 1e-6f);
	EXPECT_NEAR(ctrl.getLeadGain()(2), c_y, 1e-6f);
}

TEST(IndiRateControlLeadTest, LeadScaleInvalidAndClamped)
{
	const float nan = std::numeric_limits<float>::quiet_NaN();
	const float inf = std::numeric_limits<float>::infinity();
	const float scales[] = {nan, -1.f, inf, -inf, 0.5f, 2.f};
	const float expected[] = {0.f, 0.f, 0.f, 0.f, 0.5f, 1.f};

	for (int k = 0; k < 6; k++) {
		IndiRateControl ctrl = makeLeadController(scales[k]);
		const Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(5.f, 0.f, 0.f), Vector3f(), kDt, false);
		EXPECT_FALSE(ctrl.getFault());
		EXPECT_NEAR(ctrl.getLeadGain()(0), expected[k] * 0.4f, 1e-6f) << k;
		EXPECT_NEAR(out(0), -(1.f + expected[k] * 0.4f) * 5.f / kG1True, 1e-6f) << k;
	}
}

TEST(IndiRateControlLeadTest, LeadGainIsClampedToTwo)
{
	IndiRateControl ctrl = makeLeadController(1.f);
	ctrl.setGainK(Vector3f(100.f, 100.f, 100.f));
	ctrl.setActuatorTimeConstant(0.05f); // K tau_c = 5
	const Vector3f out = ctrl.update(Vector3f(), Vector3f(), Vector3f(5.f, 0.f, 0.f), Vector3f(), kDt, false);
	EXPECT_NEAR(ctrl.getLeadGain()(0), 2.f, 1e-6f);
	EXPECT_NEAR(out(0), -3.f * 5.f / kG1True, 1e-6f); // not -6 * 5 / G1
}

TEST(IndiRateControlLeadTest, LeadKeepsFaultHold)
{
	const float nan = std::numeric_limits<float>::quiet_NaN();
	IndiRateControl ctrl = makeLeadController(1.f);
	Vector3f valid;

	for (int i = 0; i < 20; i++) {
		valid = ctrl.update(Vector3f(0.1f, 0.2f, 0.3f), Vector3f(1.f, 1.f, 1.f), Vector3f(1.f, 2.f, 3.f),
				    Vector3f(0.1f, 0.1f, 0.1f), kDt, false);
	}

	EXPECT_FALSE(ctrl.getFault());
	EXPECT_NE(valid, Vector3f());
	const Vector3f held = ctrl.update(Vector3f(0.1f, 0.2f, 0.3f), Vector3f(1.f, 1.f, 1.f), Vector3f(0.f, nan, 0.f),
					  Vector3f(0.1f, 0.1f, 0.1f), kDt, false);
	EXPECT_TRUE(ctrl.getFault());
	EXPECT_EQ(held, valid);
}

TEST(IndiRateControlLeadTest, MeasuredPathStaysBumplessWithLead)
{
	IndiRateControl ref = makeLeadController(1.f);
	IndiRateControl ctrl = makeLeadController(1.f);
	Vector3f meas;
	const float alpha = 1.f - expf(-kDt / kActuatorTc);
	bool in_use_seen = false;

	for (int i = 0; i < 400; i++) {
		const Excitation e = excitation(i);
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
}

// ---------------------------------------------------------------------------------------------------------------
// Closed loop: loop broken numerically by sinusoidal injection d at the command, u = c + d fed back (as the module
// does), L = -c/u. Plant: first order actuator, one sample command delay, gyro derivative filtered like PX4.
// ---------------------------------------------------------------------------------------------------------------

namespace
{

constexpr float kLagDt = 0.00125f;
constexpr float kLagTc = 0.033f;
constexpr float kPAtt = 8.f;

class RollPlantLag
{
public:
	RollPlantLag()
	{
		_lpf.set_cutoff_frequency(1.f / kLagDt, 40.f);
		_alpha.setCutoffFreq(1.f / kLagDt, 20.f);
	}

	void step(float command)
	{
		const float applied = _delayed; // one sample command delay
		_delayed = command;
		_torque += (1.f - expf(-kLagDt / kLagTc)) * (applied - _torque);
		const float accel = kG1True * _torque;
		_accel_f = _alpha.update(_lpf.apply(accel));
		_rate += accel * kLagDt;
		_att += _rate * kLagDt;
	}

	float rate() const { return _rate; }
	float att() const { return _att; }
	float accelFiltered() const { return _accel_f; }

private:
	math::LowPassFilter2p<float> _lpf;
	AlphaFilter<float> _alpha;
	float _delayed{0.f};
	float _torque{0.f};
	float _accel_f{0.f};
	float _rate{0.f};
	float _att{0.f};
};

struct LoopMargins {
	float pm_deg{NAN};
	float gm_db{NAN};
	float crossover_hz{NAN};
	std::vector<double> freq;
	std::vector<std::complex<double>> L;
};

/// L(jw) at one frequency by sinusoidal injection, returns -c/u
std::complex<double> measureL(float lead, float act_tc, float f_hz)
{
	IndiRateControl ctrl = makeController();
	ctrl.setGainK(Vector3f(20.f, 20.f, 20.f));
	ctrl.setActuatorTimeConstant(act_tc);
	ctrl.setLeadScale(lead);
	RollPlantLag plant;

	const int periods_measure = 10;
	const int n_measure = (int)lroundf(periods_measure / (f_hz * kLagDt));
	const double w = 2. * M_PI * periods_measure / (n_measure * (double)kLagDt); // integer number of periods
	const int n_transient = (int)fmaxf(4.f / kLagDt, 10.f / (f_hz * kLagDt)); // >= 4 s and 10 periods
	const float amp = 0.01f;
	float u_prev = 0.f;
	std::complex<double> sum_c{0., 0.};
	std::complex<double> sum_u{0., 0.};

	for (int i = 0; i < n_transient + n_measure; i++) {
		const double t = i * (double)kLagDt;
		const float rate_sp = -kPAtt * plant.att();
		const float c = ctrl.update(Vector3f(plant.rate(), 0.f, 0.f), Vector3f(rate_sp, 0.f, 0.f),
					    Vector3f(plant.accelFiltered(), 0.f, 0.f), Vector3f(u_prev, 0.f, 0.f), kLagDt, false)(0);
		const float u = c + amp * (float)sin(w * t);
		plant.step(u);
		u_prev = u;

		if (i >= n_transient) {
			const std::complex<double> e = std::polar(1., -w * t);
			sum_c += (double)c * e;
			sum_u += (double)u * e;
		}
	}

	return -sum_c / sum_u;
}

LoopMargins loopMargins(float lead, float act_tc)
{
	LoopMargins m;
	// 12 log spaced points 0.5-30 Hz, then points above for the gain margin
	const double extra[] = {40.f, 50.f, 65.f, 80.f, 100.f, 130.f, 170.f};

	for (int k = 0; k < 12; k++) {
		m.freq.push_back(0.5 * pow(60., k / 11.));
	}

	for (double f : extra) {
		m.freq.push_back(f);
	}

	for (size_t k = 0; k < m.freq.size(); k++) {
		m.L.push_back(measureL(lead, act_tc, (float)m.freq[k]));
	}

	// phase unwrapped along frequency, the first point (L ~ K/s) is put in (-270, 90] deg
	std::vector<double> ph(m.L.size()), mag_db(m.L.size());

	for (size_t k = 0; k < m.L.size(); k++) {
		double p = std::arg(m.L[k]);

		if (k == 0) {
			while (p > M_PI / 2.) { p -= 2. * M_PI; }

		} else {
			while (p - ph[k - 1] * M_PI / 180. > M_PI) { p -= 2. * M_PI; }

			while (p - ph[k - 1] * M_PI / 180. < -M_PI) { p += 2. * M_PI; }
		}

		ph[k] = p * 180. / M_PI;
		mag_db[k] = 20. * log10(std::abs(m.L[k]));
	}

	for (size_t k = 1; k < m.L.size(); k++) {
		if (std::isnan(m.pm_deg) && mag_db[k - 1] >= 0. && mag_db[k] < 0.) {
			const double a = mag_db[k - 1] / (mag_db[k - 1] - mag_db[k]);
			const double lf = log(m.freq[k - 1]) + a * (log(m.freq[k]) - log(m.freq[k - 1]));
			m.crossover_hz = (float)exp(lf);
			m.pm_deg = (float)(180. + ph[k - 1] + a * (ph[k] - ph[k - 1]));
		}

		if (std::isnan(m.gm_db) && ph[k - 1] > -180. && ph[k] <= -180.) {
			const double a = (-180. - ph[k - 1]) / (ph[k] - ph[k - 1]);
			m.gm_db = (float)(-(mag_db[k - 1] + a * (mag_db[k] - mag_db[k - 1])));
		}
	}

	return m;
}

void printMargins(const char *name, const LoopMargins &m)
{
	printf("MARGINS %s: PM %.1f deg, GM %.1f dB, crossover %.2f Hz\n", name, (double)m.pm_deg, (double)m.gm_db,
	       (double)m.crossover_hz);

	for (size_t k = 0; k < m.freq.size(); k++) {
		printf("  f %7.2f Hz |L| %8.3f dB arg %8.1f deg\n", m.freq[k], 20. * log10(std::abs(m.L[k])),
		       std::arg(m.L[k]) * 180. / M_PI);
	}
}

} // namespace

TEST(IndiRateControlLeadTest, LeadImprovesPhaseMargin)
{
	const LoopMargins off = loopMargins(0.f, kLagTc);
	const LoopMargins on = loopMargins(1.f, kLagTc);
	const LoopMargins low = loopMargins(1.f, kLagTc * 0.6f);
	const LoopMargins high = loopMargins(1.f, kLagTc * 1.4f);
	printMargins("lead0", off);
	printMargins("lead1_matched", on);
	printMargins("lead1_x0.6", low);
	printMargins("lead1_x1.4", high);

	for (const LoopMargins *m : {&off, &on, &low, &high}) {
		for (const auto &l : m->L) {
			ASSERT_TRUE(std::isfinite(std::abs(l)));
		}

		ASSERT_FALSE(std::isnan(m->pm_deg)); // a crossover exists
		EXPECT_GT(m->pm_deg, 0.f); // no instability
	}

	EXPECT_GE(on.pm_deg, 50.f);
	EXPECT_GE(on.pm_deg - off.pm_deg, 20.f);
	EXPECT_GE(on.gm_db, 10.f);
}

namespace
{

IndiRateControl makeYawSpinUpController(float g2, float g1 = 205.f)
{
	IndiRateControl ctrl = makeController();
	ctrl.setG1(Vector3f(kG1True, kG1True, g1));
	ctrl.setG2Yaw(g2);
	return ctrl;
}

/// yaw increment after n cycles of a constant nu = 20 * 0.1, no measured acceleration, zero allocated torque
float yawIncrementAfter(float dt, int n)
{
	IndiRateControl ctrl = makeYawSpinUpController(27.f);
	Vector3f out;

	for (int i = 0; i < n; i++) {
		out = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.1f), Vector3f(), Vector3f(), dt, false);
	}

	return out(2);
}

/// yaw plant: first order rotor lag, acceleration = G1 m + G2 dm/dt, sampled at 800 Hz. Returns the rate trajectory
/// error metrics for a 1 rad/s step: max |rate - 1| over the last second, peak rate and max |command|.
void runYawLoop(float g2_plant, float &tail_err, float &peak, float &max_cmd)
{
	constexpr float dt = 0.00125f;
	constexpr float tau = 0.033f;
	constexpr float g1 = 205.f;
	IndiRateControl ctrl = makeYawSpinUpController(27.f);
	ctrl.setActuatorTimeConstant(tau);
	float m = 0.f;
	float rate = 0.f;
	float accel = 0.f;
	float u = 0.f;
	tail_err = 0.f;
	peak = 0.f;
	max_cmd = 0.f;

	for (int i = 0; i < 4000; i++) { // 5 s
		u = ctrl.update(Vector3f(0.f, 0.f, rate), Vector3f(0.f, 0.f, 1.f), Vector3f(0.f, 0.f, accel),
				Vector3f(0.f, 0.f, u), dt, false)(2);
		const float m_old = m;
		m += (1.f - expf(-dt / tau)) * (u - m);
		accel = g1 * m + g2_plant * (m - m_old) / dt;
		rate += accel * dt;
		peak = fmaxf(peak, rate);
		max_cmd = fmaxf(max_cmd, fabsf(u));

		if (i >= 3200) {
			tail_err = fmaxf(tail_err, fabsf(rate - 1.f));
		}
	}
}

} // namespace

TEST(IndiRateControlYawInvTest, DcGainAndTimeConstantIndependentOfDt)
{
	const float dc = 2.f / 205.f; // nu / G1
	const float tc = 27.f / 205.f;

	for (const float dt : {0.0025f, 0.00125f}) {
		const int n_tau = static_cast<int>(tc / dt + 0.5f);
		EXPECT_NEAR(yawIncrementAfter(dt, n_tau), dc * (1.f - expf(-1.f)), 0.05f * dc) << dt;
		EXPECT_NEAR(yawIncrementAfter(dt, 10 * n_tau), dc, 0.01f * dc) << dt;
	}
}

TEST(IndiRateControlYawInvTest, LandedStateIsZeroAndTakeoffHasNoDoubleCount)
{
	IndiRateControl ctrl = makeYawSpinUpController(27.f);
	const float expected = (2.f - 3.f) / (205.f + 27.f / kDt);

	for (int i = 0; i < 20; i++) {
		const Vector3f out = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.1f), Vector3f(0.f, 0.f, 3.f), Vector3f(), kDt, true);
		EXPECT_NEAR(out(2), expected, 1e-7f) << i;
	}

	const Vector3f air = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.1f), Vector3f(0.f, 0.f, 3.f), Vector3f(), kDt, false);
	EXPECT_NEAR(air(2), expected, 1e-7f);
}

TEST(IndiRateControlYawInvTest, FirstLandedCycleIgnoresTheFlightIncrement)
{
	IndiRateControl ctrl = makeYawSpinUpController(27.f);
	const float expected = (2.f - 3.f) / (205.f + 27.f / kDt);
	Vector3f prev;

	for (int i = 0; i < 400; i++) { // in flight the increment converges to (2 - 3) / 205, far from expected
		prev = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.1f), Vector3f(0.f, 0.f, 3.f), prev, kDt, false);
	}

	const Vector3f landed = ctrl.update(Vector3f(), Vector3f(0.f, 0.f, 0.1f), Vector3f(0.f, 0.f, 3.f), prev, kDt, true);
	EXPECT_NEAR(landed(2), expected, 1e-6f);
}

TEST(IndiRateControlYawInvTest, FaultHoldThenRecoveryHasNoStep)
{
	const float nan = std::numeric_limits<float>::quiet_NaN();
	IndiRateControl ctrl = makeYawSpinUpController(27.f);
	IndiRateControl fresh = makeYawSpinUpController(27.f);
	ctrl.setMaxIncrement(0.3f);
	fresh.setMaxIncrement(0.3f);
	const Vector3f sp(0.f, 0.f, 2.f); // nu = 40
	Vector3f prev;

	for (int i = 0; i < 400; i++) {
		prev = ctrl.update(Vector3f(), sp, Vector3f(), prev, kDt, false);
	}

	for (int i = 0; i < 200; i++) { // long enough for the hold to expire and reset everything
		prev = ctrl.update(Vector3f(), sp, Vector3f(nan, 0.f, 0.f), prev, kDt, false);
		EXPECT_TRUE(prev.isAllFinite());
	}

	Vector3f a;
	Vector3f b;

	for (int i = 0; i < 50; i++) {
		const Vector3f last_a = a;
		a = ctrl.update(Vector3f(), sp, Vector3f(), a, kDt, false);
		b = fresh.update(Vector3f(), sp, Vector3f(), b, kDt, false);
		EXPECT_LE(fabsf(a(2) - last_a(2)), 0.3f + 1e-6f) << i;
		EXPECT_NEAR(a(2), b(2), 1e-6f) << i;
	}
}

TEST(IndiRateControlYawInvTest, ClosedLoopYawStepSettlesWithoutOscillation)
{
	for (const float scale : {1.f, 0.5f, 2.f}) {
		float tail_err;
		float peak;
		float max_cmd;
		runYawLoop(27.f * scale, tail_err, peak, max_cmd);
		EXPECT_LT(tail_err, 0.02f) << scale;
		EXPECT_LT(peak, 1.5f) << scale;
		EXPECT_LE(max_cmd, 1.f) << scale;
	}
}
