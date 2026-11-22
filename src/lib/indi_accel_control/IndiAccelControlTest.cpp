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
#include <lib/indi_accel_control/indi_accel_control.hpp>

#include <cmath>
#include <limits>

using namespace matrix;

namespace
{

constexpr float kG = IndiAccelControl::kGravity;
constexpr float kGt = 20.f;
constexpr float kDt = 0.01f;
constexpr float kNaN = std::numeric_limits<float>::quiet_NaN();

class IndiAccelControlTest : public ::testing::Test
{
protected:
	void SetUp() override
	{
		_ctrl.setGains(Vector3f(1.f, 1.f, 1.f), Vector3f(2.f, 2.f, 4.f));
		_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.1f, 1.f);
		_ctrl.setThrustModel(kGt, 1.f);
		_ctrl.setFilter(0.f, 0.f);
		_ctrl.setMeasurementDelay(0);
		_ctrl.setFeedforward(true);
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	}

	/// hover state, level attitude, references equal to the state, a_c = 0 unless a_ref is set
	static IndiAccelControl::Input hoverInput()
	{
		IndiAccelControl::Input in;
		in.p = Vector3f(1.f, 2.f, -3.f);
		in.v = Vector3f(0.f, 0.f, 0.f);
		in.q = Quatf();
		in.f_b = Vector3f(0.f, 0.f, -kG);
		in.mean_u = kG / kGt;
		in.mean_u_valid = true;
		in.p_ref = in.p;
		in.v_ref = Vector3f(0.f, 0.f, 0.f);
		in.a_ref = Vector3f(0.f, 0.f, 0.f);
		in.j_ref = Vector3f(0.f, 0.f, 0.f);
		in.yaw_ref = 0.f;
		in.yawspeed_ref = 0.f;
		in.dt = kDt;
		return in;
	}

	/// angle between -t_c and -e3
	static float tilt(const Vector3f &t_c) { return atan2f(Vector2f(t_c(0), t_c(1)).norm(), -t_c(2)); }

	IndiAccelControl _ctrl;
};

} // namespace

TEST_F(IndiAccelControlTest, HoverEquilibrium)
{
	_ctrl.setThrustModel(kGt, 1.1f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt / 1.1f, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.yaw_ref = 0.5f;
	IndiAccelControl::Output out;

	for (int i = 0; i < 5; i++) {
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	EXPECT_NEAR(out.a_c.norm(), 0.f, 1e-5f);
	EXPECT_NEAR(out.a_f.norm(), 0.f, 1e-5f);
	EXPECT_NEAR((out.t_c - out.t_f).norm(), 0.f, 1e-5f);
	EXPECT_NEAR(out.t_c(2), -kG, 1e-4f);
	EXPECT_NEAR(out.thrust, kG / (kGt * 1.1f), 1e-5f);
	const Eulerf e(out.q_d);
	EXPECT_NEAR(e.phi(), 0.f, 1e-5f);
	EXPECT_NEAR(e.theta(), 0.f, 1e-5f);
	EXPECT_NEAR(e.psi(), 0.5f, 1e-5f);
	EXPECT_NEAR(out.omega_ff.norm(), 0.f, 1e-6f);
}

TEST_F(IndiAccelControlTest, AccelOnlyEntryStartsAtARef)
{
	const float G = 14.f;			// effectiveness, specific force per unit normalised thrust
	const float T_meas = kG / G;		// hover collective
	_ctrl.setThrustModel(G, 1.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), T_meas, T_meas);
	IndiAccelControl::Input in = hoverInput();
	in.accel_only = true;
	in.p = Vector3f(NAN, NAN, NAN);	// p and v are not required in this mode
	in.v = Vector3f(NAN, NAN, NAN);
	in.p_ref = Vector3f(5.f, 5.f, 5.f);	// and are ignored
	in.mean_u = T_meas;
	in.mean_u_valid = true;
	in.a_ref = Vector3f(0.f, 0.f, 0.f);
	IndiAccelControl::Output out;

	// steady state, a_meas == a_ref: the thrust output is the measured thrust
	for (int i = 0; i < 5; i++) {
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	EXPECT_NEAR(out.thrust, T_meas, 1e-5f);
	EXPECT_NEAR(out.a_c.norm(), 0.f, 1e-6f);

	// step of 1 m/s^2 upwards in a_ref with unchanged measurements: thrust moves by delta_a / G
	in.a_ref = Vector3f(0.f, 0.f, -1.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.thrust, T_meas + 1.f / G, 1e-5f);
	EXPECT_NEAR(out.a_c(2), -1.f, 1e-6f);
}

TEST_F(IndiAccelControlTest, PureIndiIncrement)
{
	_ctrl.setThrustModel(kGt, 1.1f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(0.f, 0.f, -1.f); // a_c - a_f = (0, 0, -1)
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));

	EXPECT_NEAR(out.t_c(2), -kG - 1.f, 1e-4f);
	EXPECT_NEAR(out.thrust, kG / (kGt * 1.1f) + 1.f / (kGt * 1.1f), 1e-5f);
	EXPECT_NEAR(Vector2f(out.t_c(0), out.t_c(1)).norm(), 0.f, 1e-6f);
}

TEST_F(IndiAccelControlTest, ModelErrorIsRemovedByMeasuredAcceleration)
{
	// the accelerometer shows a_f = (0, 0, +1) (e.g. extra drag/mass): the command rises by exactly 1
	IndiAccelControl::Input in = hoverInput();
	in.f_b = Vector3f(0.f, 0.f, -kG + 1.f);
	_ctrl.reset(in.f_b, in.mean_u, in.mean_u);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_f(2), 1.f, 1e-5f);
	EXPECT_NEAR(out.t_c(2), -kG - 1.f, 1e-4f);
}

TEST_F(IndiAccelControlTest, TiltLimitKeepsVerticalComponent)
{
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.5f, 0.1f, 1.f); // 28.6 deg
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(20.f, 0.f, 0.f);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));

	EXPECT_NEAR(tilt(out.t_c), 0.5f, 1e-4f);
	EXPECT_NEAR(out.t_c(2), -kG, 1e-4f);
	EXPECT_GT(out.t_c(0), 0.f);
	// attitude: thrust toward +x means body z tilted toward -x (z_b = -t_c / c)
	const Dcmf R_d(out.q_d);
	EXPECT_NEAR(R_d(0, 2), -sinf(0.5f), 1e-4f);
	EXPECT_NEAR(R_d(2, 2), cosf(0.5f), 1e-4f);
}

TEST_F(IndiAccelControlTest, ThrustSaturationKeepsVertical)
{
	_ctrl.setLimits(10.f, 3.f, 1.5f, 1.2f, 0.1f, 0.6f); // c_max = 12 m/s^2
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(8.f, 0.f, -1.5f); // z = -11.30665, horizontal 8
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));

	const float z = kG + 1.5f;
	EXPECT_NEAR(out.t_c(2), -z, 1e-4f);
	EXPECT_NEAR(out.t_c.norm(), 12.f, 1e-4f);
	EXPECT_NEAR(out.t_c(0), sqrtf(144.f - z * z), 1e-3f);
	EXPECT_NEAR(out.thrust, 0.6f, 1e-5f);

	// vertical demand alone above the maximum: all horizontal part dropped, thrust at the maximum
	in.a_ref = Vector3f(8.f, 0.f, -5.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.t_c(0), 0.f, 1e-5f);
	EXPECT_NEAR(out.t_c(2), -12.f, 1e-4f);
	EXPECT_NEAR(out.thrust, 0.6f, 1e-5f);
}

TEST_F(IndiAccelControlTest, ThrustPointsUpAndMinimumThrust)
{
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(0.f, 0.f, 3.f * kG); // asks for a downward thrust
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_LT(out.t_c(2), 0.f);
	EXPECT_NEAR(out.thrust, 0.1f, 1e-5f);
	EXPECT_NEAR(out.t_c(2), -kGt * 0.1f, 1e-4f);
	EXPECT_NEAR(out.omega_ff.norm(), 0.f, 1e-6f);
	EXPECT_NEAR(out.q_d.norm(), 1.f, 1e-5f);
}

TEST_F(IndiAccelControlTest, NonFiniteInputReturnsFalseAndLeavesOutputUntouched)
{
	IndiAccelControl::Output ref;
	ASSERT_TRUE(_ctrl.update(hoverInput(), ref));

	for (int k = 0; k < 7; k++) {
		IndiAccelControl::Input in = hoverInput();

		switch (k) {
		case 0: in.p(1) = kNaN; break;

		case 1: in.v(2) = INFINITY; break;

		case 2: in.q(0) = kNaN; break;

		case 3: in.f_b(0) = kNaN; break;

		case 4: in.mean_u = kNaN; break; // valid flag set

		case 5: in.dt = kNaN; break;

		case 6: in.dt = 0.f; break;
		}

		IndiAccelControl::Output out;
		out.thrust = 123.f;
		out.t_c = Vector3f(1.f, 2.f, 3.f);
		EXPECT_FALSE(_ctrl.update(in, out)) << "case " << k;
		EXPECT_EQ(out.thrust, 123.f);
		EXPECT_EQ(out.t_c(1), 2.f);
	}

	// non finite reference components are not errors
	IndiAccelControl::Input in = hoverInput();
	in.p_ref = Vector3f(kNaN, kNaN, kNaN);
	in.v_ref = Vector3f(kNaN, kNaN, kNaN);
	in.a_ref = Vector3f(kNaN, kNaN, kNaN);
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	in.yaw_ref = kNaN;
	in.yawspeed_ref = kNaN;
	in.mean_u = kNaN;
	in.mean_u_valid = false;
	IndiAccelControl::Output out;
	EXPECT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.yawspeed_ff, 0.f);
	EXPECT_NEAR(Eulerf(out.q_d).psi(), 0.f, 1e-5f);
}

TEST_F(IndiAccelControlTest, NaNYawKeepsCurrentYaw)
{
	IndiAccelControl::Input in = hoverInput();
	in.q = Quatf(Eulerf(0.f, 0.f, 1.2f));
	in.yaw_ref = kNaN;
	in.yawspeed_ref = 0.3f;
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(Eulerf(out.q_d).psi(), 1.2f, 1e-4f);
	EXPECT_NEAR(out.yawspeed_ff, 0.3f, 1e-6f);
}

TEST_F(IndiAccelControlTest, ResetGivesZeroIncrementOnFirstCycle)
{
	_ctrl.setFilter(100.f, 10.f);
	IndiAccelControl::Input in = hoverInput();
	in.f_b = Vector3f(0.5f, -0.3f, -12.f);
	in.mean_u = 0.6f;
	_ctrl.reset(in.f_b, in.mean_u, in.mean_u);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	// a_f from the measurement and t_f from the model are both initialised to the sample
	EXPECT_NEAR(out.a_f(0), 0.5f, 1e-4f);
	EXPECT_NEAR(out.a_f(2), -12.f + kG, 1e-4f);
	EXPECT_NEAR(out.t_f(2), -kGt * 0.6f, 1e-4f);
	in.a_ref = out.a_f; // a_c = a_f
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR((out.t_c - out.t_f).norm(), 0.f, 1e-4f);
}

TEST_F(IndiAccelControlTest, ResetJerkHistoryKeepsMeasuredFilters)
{
	// D-T10-RESET: an estimator reset must not re-seed the measured force / collective filters with a raw sample
	_ctrl.setFilter(100.f, 10.f);
	IndiAccelControl::Input in = hoverInput();
	_ctrl.reset(in.f_b, in.mean_u, in.mean_u);
	IndiAccelControl::Output out;

	for (int k = 0; k < 50; k++) {
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	IndiAccelControl ref = _ctrl;
	in.f_b(0) += 0.3f; // one noisy accelerometer sample at the reset cycle
	in.mean_u += 0.05f;
	IndiAccelControl::Output out_ref;
	ASSERT_TRUE(ref.update(in, out_ref));
	_ctrl.resetJerkHistory();
	ASSERT_TRUE(_ctrl.update(in, out));

	for (int i = 0; i < 3; i++) {
		EXPECT_FLOAT_EQ(out.a_f(i), out_ref.a_f(i));
		EXPECT_FLOAT_EQ(out.t_f(i), out_ref.t_f(i));
		EXPECT_FLOAT_EQ(out.t_c(i), out_ref.t_c(i));
	}

	// the filtered value moved by less than the raw step (the full reset() would put the raw sample through)
	EXPECT_LT(fabsf(out.a_f(0)), 0.2f);
}

TEST_F(IndiAccelControlTest, FilterMatching)
{
	// same step (scaled) on f_b and on mean u: identical normalised responses, also with a delay
	for (int delay = 0; delay <= 2; delay++) {
		_ctrl.setMeasurementDelay(delay);
		_ctrl.setFilter(100.f, 10.f);
		const float f0 = -kG;
		const float u0 = kG / kGt;
		const float df = -2.f;
		const float du = 0.1f;
		_ctrl.reset(Vector3f(0.f, 0.f, f0), u0, u0);
		IndiAccelControl::Input in = hoverInput();
		IndiAccelControl::Output out;
		float resp_f[20];
		float resp_u[20];

		for (int i = 0; i < 20; i++) {
			in.f_b = Vector3f(0.f, 0.f, f0 + ((i >= 3) ? df : 0.f));
			in.mean_u = u0 + ((i >= 3) ? du : 0.f);
			ASSERT_TRUE(_ctrl.update(in, out));
			resp_f[i] = out.a_f(2) / df;
			resp_u[i] = (-out.t_f(2) / kGt - u0) / du;
		}

		for (int i = 0; i < 20; i++) {
			const int j = (i - delay >= 0) ? i - delay : 0;
			// the f_b response is 'delay' samples earlier than the u response
			EXPECT_NEAR(resp_u[i], (i - delay >= 0) ? resp_f[i - delay] : 0.f, 1e-5f) << "delay " << delay << " i " << i << " j " << j;
		}

		EXPECT_GT(resp_f[19], 0.5f);
		EXPECT_LT(resp_f[3], 0.5f); // actually filtered
	}
}

TEST_F(IndiAccelControlTest, MeasurementDelayClamp)
{
	_ctrl.setMeasurementDelay(10);
	EXPECT_EQ(_ctrl.measurementDelay(), IndiAccelControl::kMaxDelaySamples);
	_ctrl.setMeasurementDelay(-3);
	EXPECT_EQ(_ctrl.measurementDelay(), 0);

	// no filter: a step on mean u appears exactly kMaxDelaySamples cycles later
	_ctrl.setMeasurementDelay(100);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), 0.5f, 0.5f);
	IndiAccelControl::Input in = hoverInput();
	IndiAccelControl::Output out;

	for (int i = 0; i < 10; i++) {
		in.mean_u = (i >= 2) ? 0.7f : 0.5f;
		ASSERT_TRUE(_ctrl.update(in, out));
		const float expected = (i >= 2 + IndiAccelControl::kMaxDelaySamples) ? 0.7f : 0.5f;
		EXPECT_NEAR(-out.t_f(2) / kGt, expected, 1e-6f) << "i " << i;
	}
}

TEST_F(IndiAccelControlTest, InvalidMeanUUsesPreviousThrustCommand)
{
	_ctrl.setThrustModel(kGt, 1.2f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(0.f, 0.f, -2.f);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	const float thrust_prev = out.thrust;
	in.mean_u = kNaN;
	in.mean_u_valid = false;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(-out.t_f(2), kGt * thrust_prev * 1.2f, 1e-4f);
}

TEST_F(IndiAccelControlTest, InvalidFbConvergesToModelInversionWithDelay)
{
	// D-STAGE-STALE (a): f_b replaced by the delayed modelled specific force: t_c = a_ref - g, no recursion
	for (int delay = 2; delay <= 3; delay++) {
		_ctrl.setFilter(100.f, 10.f);
		_ctrl.setMeasurementDelay(delay);
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
		IndiAccelControl::Input in = hoverInput();
		in.a_ref = Vector3f(0.5f, 0.f, -1.f);
		in.f_b = Vector3f(kNaN, kNaN, kNaN); // not read while f_b_valid is false
		in.f_b_valid = false;
		in.mean_u_valid = false;
		IndiAccelControl::Output out;
		float max_err = 0.f;

		for (int i = 0; i < 300; i++) {
			ASSERT_TRUE(_ctrl.update(in, out)) << "delay " << delay << " i " << i;
			const Vector3f expected(0.5f, 0.f, -1.f - kG);
			max_err = fmaxf(max_err, (out.t_c - expected).norm());
			ASSERT_TRUE(out.t_c.isAllFinite());
		}

		EXPECT_LT(max_err, 0.05f) << "delay " << delay;
		EXPECT_NEAR(out.t_c(0), 0.5f, 1e-3f) << "delay " << delay;
		EXPECT_NEAR(out.t_c(2), -1.f - kG, 1e-3f) << "delay " << delay;
	}
}

TEST_F(IndiAccelControlTest, InvalidFbStepInARefIsBounded)
{
	_ctrl.setFilter(100.f, 10.f);
	_ctrl.setMeasurementDelay(2);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.f_b = Vector3f(kNaN, kNaN, kNaN);
	in.f_b_valid = false;
	in.mean_u_valid = false;
	IndiAccelControl::Output out;

	for (int i = 0; i < 100; i++) {
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	in.a_ref = Vector3f(0.f, 0.f, -3.f); // step: expected t_c(2) = -3 - g
	float peak = 0.f;

	for (int i = 0; i < 300; i++) {
		ASSERT_TRUE(_ctrl.update(in, out));
		peak = fmaxf(peak, fabsf(out.t_c(2)));
	}

	EXPECT_LT(peak, kG + 3.f + 1.f);
	EXPECT_NEAR(out.t_c(2), -3.f - kG, 1e-3f);
}

TEST_F(IndiAccelControlTest, AppliedThrustSetsModelPath)
{
	// stage-output loop break: with invalid telemetry the model path must follow the applied collective, not t_c
	_ctrl.setThrustModel(kGt, 1.2f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.a_ref = Vector3f(0.f, 0.f, -2.f);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	const float c_applied = 0.9f * kG;
	_ctrl.setAppliedThrust(c_applied);
	in.mean_u = kNaN;
	in.mean_u_valid = false;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(-out.t_f(2), c_applied, 1e-3f);
	// non finite is ignored
	const float before = out.thrust;
	_ctrl.setAppliedThrust(kNaN);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(-out.t_f(2), kGt * before * 1.2f, 1e-3f);
}

TEST_F(IndiAccelControlTest, ReferenceHandlingAndVelocityLimits)
{
	IndiAccelControl::Input in = hoverInput();
	IndiAccelControl::Output out;

	// position error 1 m on x: v_sp = 1, a_c = 2
	in.p_ref = in.p + Vector3f(1.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_c(0), 2.f, 1e-5f);

	// NaN p_ref on x: no position term; v_ref still feeds forward (1 m/s -> a_c = 2)
	in.p_ref(0) = kNaN;
	in.v_ref = Vector3f(1.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_c(0), 2.f, 1e-5f);

	// NaN v_ref with position term active
	in.p_ref = in.p + Vector3f(1.f, 0.f, 0.f);
	in.v_ref = Vector3f(kNaN, kNaN, kNaN);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_c(0), 2.f, 1e-5f);

	// xy norm limit 10 m/s, z limits -3 (up) / +1.5 (down), a_ref added
	in.p_ref = in.p + Vector3f(30.f, 40.f, 20.f);
	in.a_ref = Vector3f(0.f, 0.f, 0.5f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_c(0), 2.f * 6.f, 1e-4f);
	EXPECT_NEAR(out.a_c(1), 2.f * 8.f, 1e-4f);
	EXPECT_NEAR(out.a_c(2), 4.f * 1.5f + 0.5f, 1e-4f);
	in.p_ref = in.p + Vector3f(0.f, 0.f, -20.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_c(2), -4.f * 3.f + 0.5f, 1e-4f);
}

TEST_F(IndiAccelControlTest, BodyzToAttitudeMatchesExpected)
{
	const float yaws[] = {0.f, 0.7f, -2.f};
	const float tilts[] = {0.f, 0.3f, 0.9f};

	for (float yaw : yaws) {
		for (float tl : tilts) {
			// expected: yaw about z then tilt about the heading-rotated y axis
			const Dcmf Rz(AxisAnglef(Vector3f(0.f, 0.f, 1.f), yaw));
			const Dcmf Ry(AxisAnglef(Vector3f(0.f, 1.f, 0.f), tl));
			const Dcmf R_exp = Rz * Ry;
			const Vector3f body_z = R_exp.col(2);
			const Quatf q = IndiAccelControl::bodyzToAttitude(body_z * 3.f, yaw);
			const Dcmf R(q);

			for (int i = 0; i < 3; i++) {
				for (int j = 0; j < 3; j++) {
					EXPECT_NEAR(R(i, j), R_exp(i, j), 1e-5f) << "yaw " << yaw << " tilt " << tl;
				}
			}
		}
	}

	// zero vector: level
	const Quatf q0 = IndiAccelControl::bodyzToAttitude(Vector3f(), 0.4f);
	EXPECT_NEAR(Dcmf(q0)(2, 2), 1.f, 1e-5f);
	EXPECT_NEAR(Eulerf(q0).psi(), 0.4f, 1e-5f);
}

TEST_F(IndiAccelControlTest, JerkFeedforwardSign)
{
	IndiAccelControl::Input in = hoverInput();
	IndiAccelControl::Output out;
	const float c = kG;

	// jerk along -x_b: nose up (positive pitch rate)
	in.j_ref = Vector3f(-1.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.omega_ff(1), 1.f / c, 1e-5f);
	EXPECT_NEAR(out.omega_ff(0), 0.f, 1e-6f);
	EXPECT_EQ(out.omega_ff(2), 0.f);

	// jerk along +y_b: positive roll rate
	in.j_ref = Vector3f(0.f, 1.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.omega_ff(0), 1.f / c, 1e-5f);
	EXPECT_NEAR(out.omega_ff(1), 0.f, 1e-6f);

	// rotated heading: x_b = (0,1,0), y_b = (-1,0,0) for yaw = 90 deg
	in.yaw_ref = M_PI_2_F;
	in.j_ref = Vector3f(0.f, -1.f, 0.f); // along -x_b
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.omega_ff(1), 1.f / c, 1e-4f);
	EXPECT_NEAR(out.omega_ff(0), 0.f, 1e-5f);

	// clamp at 3 rad/s and j clamp at 50 m/s^3
	in.yaw_ref = 0.f;
	in.j_ref = Vector3f(-1000.f, 0.f, 0.f);
	_ctrl.setThrustModel(kGt, 1.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.j_used(0), -50.f, 1e-6f);
	EXPECT_NEAR(out.omega_ff(1), 3.f, 1e-6f); // 50 / c = 5.1 rad/s is clamped
}

TEST_F(IndiAccelControlTest, JerkFeedforwardDisabledAndLowThrust)
{
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(-5.f, 3.f, 0.f);
	IndiAccelControl::Output out;
	_ctrl.setFeedforward(false);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.omega_ff.norm(), 0.f);
	_ctrl.setFeedforward(true);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_GT(out.omega_ff.norm(), 0.f);

	// thrust below 1 m/s^2: zero
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.0f, 1.f);
	_ctrl.setThrustModel(kGt, 1.f);
	in.a_ref = Vector3f(0.f, 0.f, kG - 0.5f); // t_c,z = -0.5 -> forced to -kMinUpThrust, c = 0.1 (thr_min 0)
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_LT(out.t_c.norm(), 1.f);
	EXPECT_EQ(out.omega_ff.norm(), 0.f);
}

TEST_F(IndiAccelControlTest, JerkFeedforwardCoordinatedTurn)
{
	// constant speed circle of radius R, yaw fixed, a = -V^2/R (cos th, sin th, 0), j = V^3/R^2 (sin th, -cos th, 0)
	const float V = 5.f;
	const float R = 10.f;
	const float ac = V * V / R;
	const float jc = V * V * V / (R * R);
	const float c = sqrtf(ac * ac + kG * kG);
	const float thetas[] = {0.f, M_PI_2_F, 0.7f, 3.f};

	for (int ti = 0; ti < 4; ti++) {
		const float th = thetas[ti];
		const Vector3f a(-ac * cosf(th), -ac * sinf(th), 0.f);
		const Vector3f j(jc * sinf(th), -jc * cosf(th), 0.f);

		// vehicle in steady state: accelerometer consistent with a, attitude from the thrust direction
		const Vector3f t = a - Vector3f(0.f, 0.f, kG);
		const Quatf q = IndiAccelControl::bodyzToAttitude(-t, 0.f);
		const Dcmf Rb(q);
		IndiAccelControl::Input in = hoverInput();
		in.q = q;
		in.f_b = Rb.transpose() * (a - Vector3f(0.f, 0.f, kG));
		in.mean_u = c / kGt;
		in.p_ref = Vector3f(kNaN, kNaN, kNaN);
		in.v_ref = Vector3f(kNaN, kNaN, kNaN);
		in.v = Vector3f(0.f, 0.f, 0.f);
		in.a_ref = a;
		in.j_ref = j;
		in.yaw_ref = 0.f;
		_ctrl.setLimits(10.f, 3.f, 1.5f, 1.2f, 0.1f, 1.f);
		_ctrl.reset(in.f_b, in.mean_u, in.mean_u);
		IndiAccelControl::Output out;
		ASSERT_TRUE(_ctrl.update(in, out));

		// a_c = a_ref = a_f: the commanded thrust is the steady one
		EXPECT_NEAR(out.t_c.norm(), c, 1e-3f);
		// analytic body rates from the thrust derivative, with x_b, y_b of the desired attitude
		const Dcmf Rd(out.q_d);
		const Vector3f x_b = Rd.col(0);
		const Vector3f y_b = Rd.col(1);
		EXPECT_NEAR(out.omega_ff(0), j.dot(y_b) / c, 1e-5f);
		EXPECT_NEAR(out.omega_ff(1), -j.dot(x_b) / c, 1e-5f);

		if (ti == 0) {
			EXPECT_NEAR(out.omega_ff(0), -jc / c, 1e-4f);
			EXPECT_NEAR(out.omega_ff(1), 0.f, 1e-4f);
		}

		if (ti == 1) {
			EXPECT_NEAR(out.omega_ff(0), 0.f, 1e-4f);
			EXPECT_NEAR(out.omega_ff(1), -jc / c, 1e-4f);
		}

		// finite difference check: z_b of q_d moves with the commanded body rates
		// z_b' = q x_b - p y_b must equal d/dt(-t/c) for t' = j
		const Vector3f z_b = Rd.col(2);
		const Vector3f zdot_model = out.omega_ff(1) * x_b - out.omega_ff(0) * y_b;
		const float h = 1e-3f;
		Vector3f t2 = t + j * h;
		const Vector3f zdot_num = (-t2 / t2.norm() - z_b) / h;
		EXPECT_NEAR((zdot_model - zdot_num).norm(), 0.f, 2e-3f);
	}
}

TEST_F(IndiAccelControlTest, ResetJerkHistoryForgetsDifference)
{
	// D-T10-RESET: a step of a_ff right after resetJerkHistory() is not differentiated into jerk
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	IndiAccelControl::Output out;
	in.a_ff = Vector3f(0.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	ASSERT_TRUE(_ctrl.update(in, out));
	_ctrl.resetJerkHistory();
	in.a_ff = Vector3f(0.3f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);
}

TEST_F(IndiAccelControlTest, JerkBackwardDifferenceAndHold)
{
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	IndiAccelControl::Output out;

	const float a_x[] = {0.f, 0.1f, 0.1f, 0.1f, 0.31f, 0.31f, 0.31f};
	const float j_x[] = {0.f, 10.f, 10.f, 10.f, 7.f, 7.f, 7.f};

	for (int i = 0; i < 7; i++) {
		in.a_ff = Vector3f(a_x[i], 0.f, 0.f);
		ASSERT_TRUE(_ctrl.update(in, out));
		EXPECT_NEAR(out.j_used(0), j_x[i], 1e-3f) << "i " << i;
		EXPECT_TRUE(out.jerk_from_difference);
		EXPECT_EQ(out.j_used(1), 0.f);
	}

	// clamp
	in.a_ff = Vector3f(10.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.j_used(0), 50.f, 1e-6f);

	// a provided j_ref has priority and is not flagged as difference
	in.j_ref = Vector3f(1.f, 2.f, 3.f);
	in.a_ff = Vector3f(11.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_FALSE(out.jerk_from_difference);
	EXPECT_NEAR(out.j_used(1), 2.f, 1e-6f);

	// reset clears the held difference, first cycle after has no history
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.a_ff = Vector3f(20.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);

	// NaN a_ref: zero jerk and no spike when it returns
	in.a_ff = Vector3f(kNaN, kNaN, kNaN);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);
	in.a_ff = Vector3f(5.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);
}

TEST_F(IndiAccelControlTest, JerkDifferenceFiltered)
{
	// a_ref ramp at 5 m/s^3 that only changes every second cycle (setpoint stream at half the loop rate)
	_ctrl.setFilter(100.f, 10.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	IndiAccelControl::Output out;
	float a = 0.f;

	for (int i = 0; i < 100; i++) {
		if ((i % 2) == 0) {
			a = 5.f * in.dt * i;
		}

		in.a_ff = Vector3f(a, 0.f, 0.f);
		ASSERT_TRUE(_ctrl.update(in, out));

		// the filter smooths the onset: the raw difference jumps to 5 at the first change
		if (i == 2) {
			EXPECT_LT(out.j_used(0), 2.5f);
		}
	}

	EXPECT_NEAR(out.j_used(0), 5.f, 0.01f);
	EXPECT_TRUE(out.jerk_from_difference);
}

TEST_F(IndiAccelControlTest, OmegaFfIndependentOfYawRate)
{
	// A-9 guard: the attitude controller already feeds the yaw rate forward (AttitudeControl, _omega_command), so
	// omega_ff must carry the jerk term only. Same tilted state and jerk, yaw rate 0 vs 1 rad/s: identical omega_ff.
	for (const float tilt_deg : {0.f, 15.f, 30.f}) {
		const float a_h = kG * tanf(math::radians(tilt_deg));
		IndiAccelControl::Output outs[2];

		for (int k = 0; k < 2; k++) {
			_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
			IndiAccelControl::Input in = hoverInput();
			in.a_ref = Vector3f(a_h, 0.f, 0.f);
			in.j_ref = Vector3f(0.4f, 0.7f, 0.f);
			in.yawspeed_ref = static_cast<float>(k); // 0 and 1 rad/s
			ASSERT_TRUE(_ctrl.update(in, outs[k]));
		}

		const Vector3f &out0 = outs[0].omega_ff;
		const Vector3f &out1 = outs[1].omega_ff;

		EXPECT_GT(out0.norm(), 0.01f) << "tilt " << tilt_deg; // the check is not vacuous
		EXPECT_NEAR(out1(0), out0(0), 1e-6f) << "tilt " << tilt_deg;
		EXPECT_NEAR(out1(1), out0(1), 1e-6f) << "tilt " << tilt_deg;
	}
}

// ---- D-GAP collective blend ----

namespace
{

/// Plant with thrust scale k: the measured mean u is k times the previous collective command
class IndiAccelBlendTest : public IndiAccelControlTest
{
protected:
	static constexpr float kScale = 0.85f;

	void startBlend(float tb)
	{
		_ctrl.setBlendTimeConstant(tb);
		_u_cmd = kG / kGt;
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), _u_cmd, kScale * _u_cmd);
	}

	/// one cycle at hover (a_ref = 0), plant feedback from the previous collective
	bool step(bool valid = true)
	{
		IndiAccelControl::Input in = hoverInput();
		const float u_meas = kScale * _u_cmd;
		in.f_b = Vector3f(0.f, 0.f, -kGt * u_meas - _dist);
		in.mean_u = u_meas;
		in.mean_u_valid = valid;
		IndiAccelControl::Output out;
		const bool ok = _ctrl.update(in, out);

		if (ok) {
			_u_cmd = out.thrust;
			_out = out;
		}

		return ok;
	}

	void run(int n, bool valid = true)
	{
		for (int i = 0; i < n; i++) {
			ASSERT_TRUE(step(valid));
		}
	}

	/// b part-way to its final value (not converged, not zero)
	void warmUp()
	{
		startBlend(1.f);
		run(50);
		ASSERT_GT(_ctrl.blend(), 0.01f);
	}

	/// the first free-running cycle after a freeze must not jump b to the instantaneous gap
	void expectNoStepAfter(float b0)
	{
		ASSERT_TRUE(step());
		EXPECT_LT(fabsf(_ctrl.blend() - b0), 0.003f);
	}

	/// module bypass convention: reset(f_b, c, mean_u) with c the commanded collective, mean_u the measured one
	void moduleReset(float c, float mean_u)
	{
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), c, mean_u);
	}

	/// largest change of the thrust command between consecutive cycles over n cycles (the first one against _u_cmd)
	float maxThrustStep(int n, bool valid = true)
	{
		float m = 0.f;

		for (int i = 0; i < n; i++) {
			const float prev = _u_cmd;
			EXPECT_TRUE(step(valid));
			m = fmaxf(m, fabsf(_u_cmd - prev));
		}

		return m;
	}

	float _u_cmd{kG / kGt};
	float _dist{0.f};	///< unmodelled upward acceleration (m/s^2)
	IndiAccelControl::Output _out{};
};

} // namespace

TEST_F(IndiAccelBlendTest, ConvergesToThrustGap)
{
	startBlend(1.f);
	run(1000); // 10 tb
	const float ideal = kG / (kGt * kScale);
	EXPECT_LT(fabsf(_u_cmd - ideal), 0.01f);
	EXPECT_LE(fabsf(_ctrl.blend()), IndiAccelControl::kMaxBlend);
}

TEST_F(IndiAccelBlendTest, ConvergesToLargeThrustGap04)
{
	// steady gap u_model - u_meas = 0.4 (above the old 0.3 bound): measured mean u = previous collective - 0.4
	constexpr float kGap = 0.4f;
	const float u_hover = kG / kGt;
	startBlend(1.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), u_hover, u_hover - kGap);

	for (int i = 0; i < 1000; i++) { // 10 tb
		IndiAccelControl::Input in = hoverInput();
		const float u_meas = _u_cmd - kGap;
		in.f_b = Vector3f(0.f, 0.f, -kGt * u_meas);
		in.mean_u = u_meas;
		in.mean_u_valid = true;
		IndiAccelControl::Output out;
		ASSERT_TRUE(_ctrl.update(in, out));
		_u_cmd = out.thrust;
		_out = out;
	}

	EXPECT_FALSE(_out.blend_frozen);
	EXPECT_NEAR(_ctrl.blend(), kGap, 0.01f);
	// u_f = u_meas + b equals the model (previous collective), the collective settles at hover + gap
	EXPECT_NEAR(_u_cmd, u_hover + kGap, 0.01f);
	EXPECT_NEAR((_u_cmd - kGap) + _ctrl.blend(), _u_cmd, 0.01f);
}

TEST_F(IndiAccelBlendTest, NegativeControlDisabledKeepsGap)
{
	startBlend(0.f);
	run(1000);
	const float ideal = kG / (kGt * kScale);
	EXPECT_GE(ideal - _u_cmd, 0.9f * (1.f - kScale) * kG / kGt);
	EXPECT_EQ(_ctrl.blend(), 0.f);
}

TEST_F(IndiAccelBlendTest, FrozenOnLandedHold)
{
	warmUp();
	const float b0 = _ctrl.blend();
	_ctrl.setBlendHold(true);
	run(50);
	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	EXPECT_TRUE(_out.blend_frozen);
	_ctrl.setBlendHold(false);
	expectNoStepAfter(b0);
}

TEST_F(IndiAccelBlendTest, FrozenOnTelemetryLossAndRecovery)
{
	warmUp();
	const float b0 = _ctrl.blend();
	run(50, false);
	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	EXPECT_TRUE(_out.blend_frozen);
	expectNoStepAfter(b0);
}

TEST_F(IndiAccelBlendTest, ModuleResetDoesNotTouchBlend)
{
	warmUp();
	const float b0 = _ctrl.blend();
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), _u_cmd, kScale * _u_cmd);
	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	expectNoStepAfter(b0);
}

TEST_F(IndiAccelBlendTest, FrozenWhileCollectiveClamped)
{
	warmUp();
	// upper limit just below the collective the loop asks for
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.1f, _u_cmd - 0.005f);
	run(2);
	const float b0 = _ctrl.blend();
	run(50);
	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	EXPECT_TRUE(_out.blend_frozen);
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.1f, 1.f);
	run(2); // the clamp flag of the previous cycle clears
	expectNoStepAfter(_ctrl.blend());
	EXPECT_GE(_ctrl.blend(), b0 - 1e-6f);
}

TEST_F(IndiAccelBlendTest, FrozenAtBypassA3A8)
{
	// bypass: the module sets the hold flag and calls reset() with the stock thrust, update() is not called
	warmUp();
	const float b0 = _ctrl.blend();
	_ctrl.setBlendHold(true);

	for (int i = 0; i < 50; i++) {
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), 0.6f / kScale, 0.6f);
	}

	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	_u_cmd = 0.6f / kScale;
	_ctrl.setBlendHold(false);
	expectNoStepAfter(b0);
}

TEST_F(IndiAccelBlendTest, NoDriftAfterResetWithoutHold)
{
	// reset() at the gap (measured u = scale x command), then active cycles without the hold flag: the model path
	// restarts at u + b, so b sees no innovation across the edge (converged first: 20 tb)
	startBlend(1.f);
	run(2000);
	const float b0 = _ctrl.blend();
	ASSERT_GT(fabsf(b0), 0.01f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), _u_cmd, kScale * _u_cmd);
	_ctrl.setBlendHold(false);

	for (int i = 0; i < 40; i++) {
		ASSERT_TRUE(step());
	}

	EXPECT_LT(fabsf(_ctrl.blend() - b0), 2e-4f);
}

TEST_F(IndiAccelBlendTest, FrozenAtE7EdgeSingleCycle)
{
	warmUp();
	_ctrl.setBlendHold(true);
	const float b0 = _ctrl.blend();
	ASSERT_TRUE(step());
	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
	_ctrl.setBlendHold(false);
	expectNoStepAfter(b0);
}

TEST_F(IndiAccelBlendTest, NoCollectiveStepAtBypassEdgeModuleConvention)
{
	// steady gap, b converged: the module's bypass branch resets with the commanded collective c (it has no measured
	// thrust) and the measured mean_u when ESC telemetry is fresh. The first active cycle must return c.
	_ctrl.setFilter(100.f, 10.f); // as in flight: the measured path settles over the filter time
	startBlend(1.f);
	run(2000);
	ASSERT_GT(fabsf(_ctrl.blend()), 0.01f);
	const float c = _u_cmd;

	for (int telemetry = 0; telemetry < 2; telemetry++) {
		_ctrl.setBlendHold(true);

		for (int i = 0; i < 20; i++) {
			moduleReset(c, telemetry ? kScale *c : kNaN);
		}

		_ctrl.setBlendHold(false);
		_u_cmd = c;
		ASSERT_TRUE(step());
		EXPECT_LT(fabsf(_out.thrust - c), 0.01f) << "telemetry " << telemetry;
		EXPECT_LT(maxThrustStep(100), 0.01f) << "telemetry " << telemetry;
	}
}

TEST_F(IndiAccelBlendTest, ThrustContinuousAtTelemetryLossAndRecovery)
{
	// steady gap, b converged (u_meas + b = u_model): the loss and the recovery must not step the collective.
	// Filter and delay as in flight: without them the measured path follows its input in one sample and the
	// test cannot see what is fed while the telemetry is invalid (S96 second key T202: vacuous otherwise)
	_ctrl.setFilter(100.f, 10.f);
	_ctrl.setMeasurementDelay(3);
	startBlend(1.f);
	run(2000);
	EXPECT_LT(maxThrustStep(5), 0.01f);
	EXPECT_LT(maxThrustStep(1, false), 0.01f);  // loss edge
	EXPECT_LT(maxThrustStep(100, false), 0.01f);
	EXPECT_LT(maxThrustStep(1, true), 0.01f);   // recovery edge
	EXPECT_LT(maxThrustStep(100, true), 0.01f);
}

TEST_F(IndiAccelBlendTest, FrozenWhenMeasuredUAtLimit)
{
	// the measured mean_u is stuck at the physical limit below what the model asks for: b must not wind up
	startBlend(1.f);

	for (int i = 0; i < 500; i++) {
		IndiAccelControl::Input in = hoverInput();
		in.mean_u = 0.995f;
		in.f_b = Vector3f(0.f, 0.f, -kGt * in.mean_u);
		in.mean_u_valid = true;
		IndiAccelControl::Output out;
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	EXPECT_LT(fabsf(_ctrl.blend()), 0.01f);
}

TEST_F(IndiAccelBlendTest, FrozenWhenAllocatorSaturated)
{
	startBlend(1.f);
	run(200);
	const float b0 = _ctrl.blend();

	for (int i = 0; i < 300; i++) {
		IndiAccelControl::Input in = hoverInput();
		in.mean_u = 0.3f; // far from the model: would wind b up
		in.mean_u_valid = true;
		in.alloc_saturated = true;
		IndiAccelControl::Output out;
		ASSERT_TRUE(_ctrl.update(in, out));
		EXPECT_TRUE(out.blend_frozen);
	}

	EXPECT_LT(fabsf(_ctrl.blend() - b0), 1e-6f);
}

TEST_F(IndiAccelBlendTest, SetFilterReconfigDoesNotStepThrust)
{
	// steady hover with the thrust gap (b converged): zeroed filters would drop the output to a_c - g e3
	// plus an unmodelled updraft that only the filtered measured acceleration knows about
	_ctrl.setFilter(100.f, 10.f);
	_dist = 2.f;
	startBlend(1.f);
	run(2000);
	const float c = _u_cmd;
	_ctrl.setFilter(80.f, 10.f);
	EXPECT_LT(maxThrustStep(1), 0.01f);
	EXPECT_LT(fabsf(_u_cmd - c), 0.01f);
	EXPECT_LT(maxThrustStep(100), 0.01f);
	EXPECT_LT(fabsf(_u_cmd - c), 0.01f);
}

// ---- D-ALTCTL-Z: z_only (collective INDI, stock direction) ----

namespace
{

class IndiAccelZOnlyTest : public IndiAccelControlTest
{
protected:
	static IndiAccelControl::Input zInput()
	{
		IndiAccelControl::Input in = hoverInput();
		in.a_ref = Vector3f(0.5f, -0.3f, -1.f);
		in.z_only = true;
		in.thrust_dir = Vector3f(2.f, -1.f, -8.f); // arbitrary norm, tilted
		return in;
	}
};

} // namespace

TEST_F(IndiAccelZOnlyTest, OutputParallelToThrustDir)
{
	IndiAccelControl::Input in = zInput();
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	const Vector3f n = in.thrust_dir.normalized();
	EXPECT_NEAR(out.t_c.normalized().dot(n), 1.f, 1e-5f);
	EXPECT_NEAR(out.t_c.cross(n).norm(), 0.f, 1e-4f);
	// attitude z axis equals -n
	const Vector3f zb = Dcmf(out.q_d).col(2);
	EXPECT_NEAR(zb.dot(-n), 1.f, 1e-5f);
}

TEST_F(IndiAccelZOnlyTest, VerticalComponentMatchesThreeAxis)
{
	IndiAccelControl::Input in = zInput();
	IndiAccelControl::Output out_z;
	ASSERT_TRUE(_ctrl.update(in, out_z));

	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.z_only = false;
	IndiAccelControl::Output out_3;
	ASSERT_TRUE(_ctrl.update(in, out_3));
	EXPECT_NEAR(out_z.t_c(2), out_3.t_c(2), 1e-4f);
	// not the same direction as the 3-axis output (xy a_ref differs from the stock direction)
	EXPECT_GT((out_z.t_c - out_3.t_c).norm(), 0.1f);
}

TEST_F(IndiAccelZOnlyTest, InvalidThrustDirReturnsFalse)
{
	IndiAccelControl::Output out;
	out.thrust = 0.77f;
	const Vector3f bad[] = {
		Vector3f(kNaN, 0.f, -1.f), Vector3f(0.f, 0.f, kNaN), Vector3f(1.f, 0.f, 0.f),
		Vector3f(0.f, 0.f, 1.f), Vector3f(1.f, 0.f, -0.05f), Vector3f(0.f, 0.f, 0.f)
	};

	for (const Vector3f &d : bad) {
		IndiAccelControl::Input in = zInput();
		in.thrust_dir = d;
		EXPECT_FALSE(_ctrl.update(in, out));
	}

	EXPECT_EQ(out.thrust, 0.77f);
	// the same input with a valid direction is accepted
	EXPECT_TRUE(_ctrl.update(zInput(), out));
}

TEST_F(IndiAccelZOnlyTest, OmegaFfZero)
{
	IndiAccelControl::Input in = zInput();
	in.j_ref = Vector3f(5.f, 5.f, 5.f);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.omega_ff.norm(), 0.f);

	// negative control: the 3-axis path does produce a feedforward for the same jerk
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.z_only = false;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_GT(out.omega_ff.norm(), 1e-3f);
}

TEST_F(IndiAccelZOnlyTest, CollectiveLimitsApplyNoTiltLimit)
{
	IndiAccelControl::Input in = zInput();
	in.thrust_dir = Vector3f(10.f, 0.f, -1.f); // ~84 deg, beyond the 0.7 rad library limit but z < -0.1 norm fails
	IndiAccelControl::Output out;
	EXPECT_FALSE(_ctrl.update(in, out));

	in.thrust_dir = Vector3f(2.f, 0.f, -1.f); // 63 deg > 0.7 rad (40 deg) limit: kept
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(tilt(out.t_c), atan2f(2.f, 1.f), 1e-4f);

	// thrust max: |t_c| limited to g_t * thr_max, direction kept
	in.a_ref = Vector3f(0.f, 0.f, -30.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.thrust, 1.f, 1e-6f);
	EXPECT_NEAR(out.t_c.norm(), kGt, 1e-3f);
	EXPECT_NEAR(tilt(out.t_c), atan2f(2.f, 1.f), 1e-4f);
}

TEST_F(IndiAccelZOnlyTest, ClosedLoopCollectiveRemovesVerticalError)
{
	// plant: thrust scale 0.85, vertical axis, level vehicle; collective blend active
	const float scale = 0.85f;
	_ctrl.setBlendTimeConstant(0.2f);
	float u_cmd = kG / kGt;
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), u_cmd, scale * u_cmd);
	const float a_ref_z = -1.f;
	IndiAccelControl::Output out;
	float az = 0.f;

	for (int i = 0; i < 600; i++) {
		IndiAccelControl::Input in = hoverInput();
		in.z_only = true;
		in.thrust_dir = Vector3f(0.f, 0.f, -1.f);
		in.a_ref = Vector3f(0.f, 0.f, a_ref_z);
		in.v_ref = Vector3f(NAN, NAN, NAN);
		in.p_ref = Vector3f(NAN, NAN, NAN);
		in.v = Vector3f(0.f, 0.f, 0.f);
		in.accel_only = true;
		const float u_meas = scale * u_cmd;
		in.f_b = Vector3f(0.f, 0.f, -kGt * u_meas);
		in.mean_u = u_meas;
		ASSERT_TRUE(_ctrl.update(in, out));
		u_cmd = out.thrust;
		az = out.a_f(2);
	}

	// measured vertical acceleration converges to a_ref z (it was +kG*(1-0.85)... ~ 1.5 m/s^2 off at start)
	EXPECT_NEAR(az, a_ref_z, 0.05f);
	EXPECT_NEAR(Vector2f(out.t_c(0), out.t_c(1)).norm(), 0.f, 1e-6f);
}

// T206: coverage added after the T205 second-key review (each test was break-checked against a library mutation)

TEST_F(IndiAccelZOnlyTest, TiltedClosedLoopStateConsistentWithNorm)
{
	// stock direction and body z tilted 30 deg; plant vertical a = -g_t u cos(tilt) + g, thrust scale 0.85
	const float tilt_rad = M_PI_F / 6.f;
	const Vector3f n(sinf(tilt_rad), 0.f, -cosf(tilt_rad));
	const Quatf q(Eulerf(0.f, -tilt_rad, 0.f));
	const Vector3f zb = Dcmf(q).col(2);
	ASSERT_NEAR(zb.dot(-n), 1.f, 1e-5f);

	const float scale = 0.85f;
	_ctrl.setBlendTimeConstant(0.2f);
	float u_cmd = kG / (kGt * cosf(tilt_rad));
	_ctrl.reset(Vector3f(0.f, 0.f, -kGt * scale * u_cmd), u_cmd, scale * u_cmd);
	const float a_ref_z = -1.f;
	IndiAccelControl::Output out;
	float az = 0.f;

	for (int i = 0; i < 800; i++) {
		IndiAccelControl::Input in = hoverInput();
		in.z_only = true;
		in.accel_only = true;
		in.thrust_dir = n * 7.f; // arbitrary norm
		in.q = q;
		in.a_ref = Vector3f(0.f, 0.f, a_ref_z);
		in.v_ref = Vector3f(NAN, NAN, NAN);
		in.p_ref = Vector3f(NAN, NAN, NAN);
		const float u_meas = scale * u_cmd;
		in.f_b = Vector3f(0.f, 0.f, -kGt * u_meas);
		in.mean_u = u_meas;
		ASSERT_TRUE(_ctrl.update(in, out));
		// stored state / output thrust is the norm of t_c, not its vertical component
		EXPECT_NEAR(out.thrust, out.t_c.norm() / kGt, 1e-5f);
		EXPECT_NEAR(out.t_c.norm() * cosf(tilt_rad), -out.t_c(2), 1e-4f);
		u_cmd = out.thrust;
		az = out.a_f(2);
	}

	EXPECT_NEAR(az, a_ref_z, 0.05f);
	// steady state: the plant delivers scale * thrust along body z, vertical demand g - a_ref_z
	EXPECT_NEAR(out.thrust, (kG - a_ref_z) / (kGt * cosf(tilt_rad) * scale), 0.01f);
}

TEST_F(IndiAccelZOnlyTest, InvalidThrustDirLeavesNoState)
{
	// guard before any state update: invalid call (different f_b, mean_u, a_ref) then valid == fresh controller + valid
	IndiAccelControl fresh;
	fresh.setGains(Vector3f(1.f, 1.f, 1.f), Vector3f(2.f, 2.f, 4.f));
	fresh.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.1f, 1.f);
	fresh.setThrustModel(kGt, 1.f);
	fresh.setFilter(50.f, 5.f); // real low pass: any state update would show
	fresh.setMeasurementDelay(0);
	fresh.setFeedforward(true);
	fresh.setBlendTimeConstant(0.2f);
	fresh.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	_ctrl.setFilter(50.f, 5.f);
	_ctrl.setBlendTimeConstant(0.2f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);

	IndiAccelControl::Input bad = zInput();
	bad.thrust_dir = Vector3f(1.f, 0.f, -0.05f);
	bad.f_b = Vector3f(3.f, -2.f, -25.f);
	bad.mean_u = 0.9f;
	bad.a_ref = Vector3f(4.f, 4.f, -7.f);
	IndiAccelControl::Output out_bad;

	for (int i = 0; i < 3; i++) {
		EXPECT_FALSE(_ctrl.update(bad, out_bad));
	}

	for (int i = 0; i < 3; i++) {
		IndiAccelControl::Output a, b;
		ASSERT_TRUE(_ctrl.update(zInput(), a));
		ASSERT_TRUE(fresh.update(zInput(), b));
		EXPECT_EQ(a.thrust, b.thrust);
		EXPECT_EQ(a.blend, b.blend);
		EXPECT_EQ((a.t_c - b.t_c).norm(), 0.f);
		EXPECT_EQ((a.a_f - b.a_f).norm(), 0.f);
		EXPECT_EQ((a.j_used - b.j_used).norm(), 0.f);
	}
}

TEST_F(IndiAccelZOnlyTest, ThrustDirGuardThresholds)
{
	// up-ratio -n_z/|n| must exceed 0.1: 0.08 rejected, 0.12 accepted
	auto dir = [](float r) { return Vector3f(sqrtf(1.f - r * r), 0.f, -r); };
	IndiAccelControl::Output out;
	IndiAccelControl::Input in = zInput();

	in.thrust_dir = dir(0.08f) * 5.f;
	EXPECT_FALSE(_ctrl.update(in, out));
	in.thrust_dir = dir(0.12f) * 5.f;
	EXPECT_TRUE(_ctrl.update(in, out));

	// scale invariance of the ratio test, and a tiny but valid direction is rejected by the norm test
	in.thrust_dir = dir(0.08f) * 1e-3f;
	EXPECT_FALSE(_ctrl.update(in, out));
	in.thrust_dir = Vector3f(0.f, 0.f, -1e-8f);
	EXPECT_FALSE(_ctrl.update(in, out));
}

TEST_F(IndiAccelZOnlyTest, VerticalFloorAndMinCollective)
{
	IndiAccelControl::Output out;
	const float tilt_rad = M_PI_F / 6.f;
	const Vector3f n(sinf(tilt_rad), 0.f, -cosf(tilt_rad));
	IndiAccelControl::Input in = zInput();
	in.thrust_dir = n;
	in.a_ref = Vector3f(0.f, 0.f, 30.f); // commands downward acceleration: t_c,z would be > 0

	// c_min (2.0) > kMinUpThrust: floor value is c_min on the vertical axis, direction kept
	ASSERT_TRUE(_ctrl.update(in, out));
	const float c_min = kGt * 0.1f;
	EXPECT_NEAR(out.t_c(2), -c_min, 1e-4f);
	EXPECT_NEAR(out.thrust, c_min / cosf(tilt_rad) / kGt, 1e-5f);
	EXPECT_NEAR(out.t_c.normalized().dot(n), 1.f, 1e-5f);

	// thr_min = 0: c_min = 0, the up-thrust floor 0.1 applies on the vertical component (not a sign flip)
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.f, 1.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.t_c(2), -0.1f, 1e-5f);
	EXPECT_NEAR(out.t_c.norm(), 0.1f / cosf(tilt_rad), 1e-5f);
	EXPECT_NEAR(out.t_c.normalized().dot(n), 1.f, 1e-5f);

	// level direction, default limits: the same floor via the c_min branch gives thrust == thr_min
	_ctrl.setLimits(10.f, 3.f, 1.5f, 0.7f, 0.1f, 1.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.thrust_dir = Vector3f(0.f, 0.f, -1.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.thrust, 0.1f, 1e-6f);
	EXPECT_NEAR(out.t_c(2), -c_min, 1e-4f);
}

TEST_F(IndiAccelZOnlyTest, VerticalDemandNotLimitedByThreeAxisTiltLimit)
{
	// a_ref has a large horizontal part: the 3-axis path is tilt limited (and shrinks its horizontal part). The
	// z-only vertical output must equal the unlimited demand t_f,z + a_c,z - a_f,z = -(g + 1)
	const float tilt_rad = 0.8726646f;
	IndiAccelControl::Input in = zInput();
	in.thrust_dir = Vector3f(sinf(tilt_rad), 0.f, -cosf(tilt_rad));
	in.a_ref = Vector3f(30.f, 0.f, -1.f);

	IndiAccelControl::Output out_z;
	ASSERT_TRUE(_ctrl.update(in, out_z));
	EXPECT_NEAR(out_z.t_c(2), -(kG + 1.f), 1e-4f);
	EXPECT_NEAR(tilt(out_z.t_c), tilt_rad, 1e-4f); // stock direction, not the 3-axis one

	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.z_only = false;
	IndiAccelControl::Output out_3;
	ASSERT_TRUE(_ctrl.update(in, out_3));
	EXPECT_NEAR(tilt(out_3.t_c), 0.7f, 1e-4f); // the 3-axis path is tilt limited here
	EXPECT_NEAR(out_z.t_c(2), out_3.t_c(2), 1e-4f);
}

// ---- A18: jerk feed-forward from the feed-forward acceleration only ----

TEST_F(IndiAccelControlTest, A18CircleAnalyticBodyRates)
{
	// constant-speed circle, R = 3 m, w = 1 rad/s: a = -A (cos, sin), j = A w (sin, -cos), A = w^2 R = 3
	// Reference: body rates from a finite difference of the desired z axis (flat vehicle, constant |t|):
	// z_b' = w_b x z_b gives p = -z_b'.y_b, q = z_b'.x_b, independent of the library's j.y_b / c formula.
	const float A = 3.f;
	const float yaw = 0.4f;
	auto z_b = [&](float th) {
		const Vector3f t(-A * cosf(th), -A * sinf(th), -kG);
		return Vector3f(-t / t.norm());
	};

	for (const float th : {0.f, 0.7f, 2.0f, 4.0f}) {
		const Vector3f a(-A * cosf(th), -A * sinf(th), 0.f);
		const Vector3f j(A * sinf(th), -A * cosf(th), 0.f);
		IndiAccelControl::Input in = hoverInput();
		in.a_ref = a;
		in.a_ff = a;
		in.j_ref = j;
		in.yaw_ref = yaw;
		IndiAccelControl::Output out;
		_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
		ASSERT_TRUE(_ctrl.update(in, out));

		const float d = 1e-3f;
		const Vector3f zdot = (z_b(th + d) - z_b(th - d)) / (2.f * d); // w = 1 rad/s
		const Dcmf R(IndiAccelControl::bodyzToAttitude(-Vector3f(-A * cosf(th), -A * sinf(th), -kG), yaw));
		const float p = -zdot.dot(R.col(1));
		const float q = zdot.dot(R.col(0));
		EXPECT_NEAR(out.omega_ff(0), p, 2e-3f) << "th " << th;
		EXPECT_NEAR(out.omega_ff(1), q, 2e-3f) << "th " << th;
		EXPECT_GT(fabsf(p) + fabsf(q), 0.1f); // the case is not trivially zero
		EXPECT_EQ(out.omega_ff(2), 0.f);
	}
}

TEST_F(IndiAccelControlTest, A18StepThenHoldGivesZeroJerk)
{
	_ctrl.setFilter(100.f, 10.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	in.a_ff = Vector3f(0.f, 0.f, 0.f);
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));

	in.a_ff = Vector3f(1.f, 0.f, 0.f); // step: held difference
	float pitch_during = 0.f;

	for (int i = 0; i < 60; i++) {
		ASSERT_TRUE(_ctrl.update(in, out));

		if (i == 5) { pitch_during = out.omega_ff(1); }
	}

	EXPECT_LT(pitch_during, -0.1f);               // inside the hold: the pulse is there
	EXPECT_NEAR(out.omega_ff(1), 0.f, 1e-3f);     // 0.6 s later: back to zero
	EXPECT_NEAR(out.j_used(0), 0.f, 1e-3f);
}

TEST_F(IndiAccelControlTest, A18FeedbackOnlyChangeGivesNoJerk)
{
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	in.a_ff = Vector3f(0.5f, 0.f, 0.f);
	IndiAccelControl::Output out;

	for (int i = 0; i < 20; i++) {
		in.a_ref = Vector3f(0.5f + 0.1f * static_cast<float>(i), 0.f, 0.f); // P/D part moves, a_ff does not
		ASSERT_TRUE(_ctrl.update(in, out));
		EXPECT_EQ(out.omega_ff(1), 0.f) << "i " << i;
		EXPECT_EQ(out.j_used(0), 0.f);
	}
}

TEST_F(IndiAccelControlTest, A18ResetMidRampGivesNoPulse)
{
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	IndiAccelControl::Output out;
	float a = 0.f;

	for (int i = 0; i < 20; i++) {
		a = 0.05f * static_cast<float>(i); // 5 m/s^3 at 100 Hz
		in.a_ff = Vector3f(a, 0.f, 0.f);
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	EXPECT_GT(fabsf(out.j_used(0)), 1.f); // ramp running

	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.a_ff = Vector3f(a + 0.05f, 0.f, 0.f); // the ramp continues, but the history is gone
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);
	EXPECT_EQ(out.omega_ff(1), 0.f);
}

namespace
{

constexpr float kNativeHz = 267.f;
constexpr int kDecim = 3; // 267 Hz force, stage at 89 Hz
constexpr float kStageHz = kNativeHz / kDecim;
constexpr float kVibHz = 95.73f;
constexpr float kAliasHz = kVibHz - kStageHz; // 6.73 Hz

} // namespace

/// D-AF-ALIAS: a vibration line above the stage rate must be removed at the force rate, not fold into the control band
TEST_F(IndiAccelControlTest, NativeRateFilterRejectsAliasedVibration)
{
	_ctrl.setFilter(kStageHz, 10.f);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.dt = 1.f / kStageHz;
	IndiAccelControl::Output out;
	double re = 0., im = 0.;
	int n = 0;

	for (int k = 0; k < 1500; k++) {
		const float t = (float)k / kNativeHz;
		const Vector3f f(sinf(2.f * M_PI_F * kVibHz * t), 0.f, -kG);
		_ctrl.sampleSpecificForce(f, 1.f / kNativeHz);

		if (k % kDecim == kDecim - 1) {
			in.f_b = f; // the module hands the latest sample to the stage
			ASSERT_TRUE(_ctrl.update(in, out));

			if (k > 600) {
				const double ts = (double)k / (double)kNativeHz;
				re += (double)out.a_f(0) * cos(2. * M_PI * (double)kAliasHz * ts);
				im += (double)out.a_f(0) * sin(2. * M_PI * (double)kAliasHz * ts);
				n++;
			}
		}
	}

	const double amp = 2. * sqrt(re * re + im * im) / n;
	EXPECT_LT(amp, 0.03); // native 2nd-order 10 Hz at 95.73 Hz: ~0.011; decimated form: ~0.9
}

TEST_F(IndiAccelControlTest, NativeRateFilterResetReseedsWithoutStep)
{
	_ctrl.setFilter(kStageHz, 10.f);

	for (int k = 0; k < 50; k++) {
		_ctrl.sampleSpecificForce(Vector3f(1.f, 0.f, -kG), 1.f / kNativeHz);
	}

	const Vector3f f_new(0.f, 2.f, -kG);
	_ctrl.reset(f_new, kG / kGt, kG / kGt);
	IndiAccelControl::Input in = hoverInput();
	in.f_b = f_new;
	in.dt = 1.f / kStageHz;
	IndiAccelControl::Output out;
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_f(0), 0.f, 1e-4f);
	EXPECT_NEAR(out.a_f(1), 2.f, 1e-4f);
	// the next native sample keeps the filtered value at f_new
	_ctrl.sampleSpecificForce(f_new, 1.f / kNativeHz);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.a_f(1), 2.f, 1e-4f);
}

TEST_F(IndiAccelControlTest, NativeRateFilterValidToInvalidSwitchHasNoStep)
{
	_ctrl.setFilter(kStageHz, 10.f);
	IndiAccelControl::Input in = hoverInput();
	in.dt = 1.f / kStageHz;
	IndiAccelControl::Output out;
	// non finite samples are ignored
	_ctrl.sampleSpecificForce(Vector3f(NAN, 0.f, -kG), 1.f / kNativeHz);

	for (int k = 0; k < 300; k++) {
		_ctrl.sampleSpecificForce(Vector3f(0.5f, 0.f, -kG), 1.f / kNativeHz);

		if (k % kDecim == 0) {
			in.f_b = Vector3f(0.5f, 0.f, -kG);
			ASSERT_TRUE(_ctrl.update(in, out));
		}
	}

	EXPECT_NEAR(out.a_f(0), 0.5f, 1e-3f);
	in.f_b_valid = false;
	in.f_b = Vector3f(NAN, NAN, NAN);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_TRUE(out.a_f.isAllFinite());
	// the first invalid cycle continues from the filtered force (0.5): a step to the modelled hover value (0) or beyond
	// the offset would show here
	EXPECT_NEAR(out.a_f(0), 0.5f, 0.05f);
	EXPECT_LT(fabsf(out.a_f(1)), 0.05f);
}

/// M1: invalid -> valid with no native samples during the gap: no step, then convergence to the measured force
TEST_F(IndiAccelControlTest, NativeRateFilterInvalidToValidHasNoStep)
{
	_ctrl.setFilter(kStageHz, 10.f);
	IndiAccelControl::Input in = hoverInput();
	in.dt = 1.f / kStageHz;
	IndiAccelControl::Output out;
	const Vector3f f_meas(0.5f, 0.f, -kG); // offset from the modelled hover force (0, 0, -g)

	for (int k = 0; k < 300; k++) {
		_ctrl.sampleSpecificForce(f_meas, 1.f / kNativeHz);

		if (k % kDecim == 0) {
			in.f_b = f_meas;
			ASSERT_TRUE(_ctrl.update(in, out));
		}
	}

	EXPECT_NEAR(out.a_f(0), 0.5f, 1e-3f);

	// gap: stage runs on the modelled path, no native samples
	in.f_b_valid = false;
	in.f_b = Vector3f(NAN, NAN, NAN);

	for (int k = 0; k < 10; k++) {
		ASSERT_TRUE(_ctrl.update(in, out));
	}

	const float a_gap = out.a_f(0);
	EXPECT_LT(fabsf(a_gap), 0.05f); // modelled hover: the filter has settled to the model

	// valid again, samples resume
	in.f_b_valid = true;
	in.f_b = f_meas;
	_ctrl.sampleSpecificForce(f_meas, 1.f / kNativeHz);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_LT(fabsf(out.a_f(0) - a_gap), 0.05f); // no step at the edge

	// converges to the measured value within a few time constants (fc 10 Hz: tau ~ 16 ms; 0.5 s is ~30 tau)
	for (int k = 0; k < 135; k++) {
		_ctrl.sampleSpecificForce(f_meas, 1.f / kNativeHz);

		if (k % kDecim == 0) {
			ASSERT_TRUE(_ctrl.update(in, out));
		}
	}

	EXPECT_NEAR(out.a_f(0), 0.5f, 1e-3f);
}

// asserts (G7(b) A14): dt outside [kMinDt, kMaxDt] (header) is rejected with the output untouched, both edges; the
// limits themselves are accepted
TEST_F(IndiAccelControlTest, DtOutsideValidRangeReturnsFalseAndLeavesOutputUntouched)
{
	const float bad_dt[] = {IndiAccelControl::kMaxDt * 1.1f, 10.f *IndiAccelControl::kMaxDt,
				IndiAccelControl::kMinDt * 0.9f
			       };

	for (const float dt : bad_dt) {
		IndiAccelControl::Input in = hoverInput();
		in.dt = dt;
		IndiAccelControl::Output out;
		out.thrust = 123.f;
		out.t_c = Vector3f(1.f, 2.f, 3.f);
		EXPECT_FALSE(_ctrl.update(in, out)) << "dt " << dt;
		EXPECT_EQ(out.thrust, 123.f) << "dt " << dt;
		EXPECT_EQ(out.t_c(1), 2.f) << "dt " << dt;
	}

	for (const float dt : {IndiAccelControl::kMinDt, IndiAccelControl::kMaxDt}) {
		IndiAccelControl::Input in = hoverInput();
		in.dt = dt;
		IndiAccelControl::Output out;
		EXPECT_TRUE(_ctrl.update(in, out)) << "dt " << dt;
	}
}
