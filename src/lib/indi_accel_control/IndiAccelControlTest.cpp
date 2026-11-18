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

TEST_F(IndiAccelControlTest, JerkBackwardDifferenceAndHold)
{
	IndiAccelControl::Input in = hoverInput();
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	IndiAccelControl::Output out;

	const float a_x[] = {0.f, 0.1f, 0.1f, 0.1f, 0.31f, 0.31f, 0.31f};
	const float j_x[] = {0.f, 10.f, 10.f, 10.f, 7.f, 7.f, 7.f};

	for (int i = 0; i < 7; i++) {
		in.a_ref = Vector3f(a_x[i], 0.f, 0.f);
		ASSERT_TRUE(_ctrl.update(in, out));
		EXPECT_NEAR(out.j_used(0), j_x[i], 1e-3f) << "i " << i;
		EXPECT_TRUE(out.jerk_from_difference);
		EXPECT_EQ(out.j_used(1), 0.f);
	}

	// clamp
	in.a_ref = Vector3f(10.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_NEAR(out.j_used(0), 50.f, 1e-6f);

	// a provided j_ref has priority and is not flagged as difference
	in.j_ref = Vector3f(1.f, 2.f, 3.f);
	in.a_ref = Vector3f(11.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_FALSE(out.jerk_from_difference);
	EXPECT_NEAR(out.j_used(1), 2.f, 1e-6f);

	// reset clears the held difference, first cycle after has no history
	in.j_ref = Vector3f(kNaN, kNaN, kNaN);
	_ctrl.reset(Vector3f(0.f, 0.f, -kG), kG / kGt, kG / kGt);
	in.a_ref = Vector3f(20.f, 0.f, 0.f);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);

	// NaN a_ref: zero jerk and no spike when it returns
	in.a_ref = Vector3f(kNaN, kNaN, kNaN);
	ASSERT_TRUE(_ctrl.update(in, out));
	EXPECT_EQ(out.j_used(0), 0.f);
	in.a_ref = Vector3f(5.f, 0.f, 0.f);
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

		in.a_ref = Vector3f(a, 0.f, 0.f);
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
