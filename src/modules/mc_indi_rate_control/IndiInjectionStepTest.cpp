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
 * Call-site tests of the bench injection: they run runIndiInjectionStep(), the code runIndiRateControl() executes
 * each cycle, with the real INDI law. Reference = a second law of identical state fed the setpoint by hand.
 */

#include <gtest/gtest.h>
#include <math.h>
#include <string.h>

#include "IndiInjectionStep.hpp"

using matrix::Vector3f;

namespace
{
constexpr float kDt = 0.0025f;
constexpr float kAmp = 0.1f;
constexpr uint64_t kT0 = 1000000;

IndiRateControl makeLaw()
{
	IndiRateControl c;
	c.setGainK(Vector3f(20.f, 20.f, 20.f));
	c.setG1(Vector3f(10.f, 10.f, 10.f));
	c.setG2Yaw(0.f);
	c.setActuatorTimeConstant(0.03f);
	c.setFilterCutoffs(40.f, 20.f);
	c.setDelaySamples(0);
	c.setMaxIncrement(1.f);
	c.setLeadScale(1.f); // the lead on the setpoint path must see d
	return c;
}

void setup(IndiInjection &inj, int axis)
{
	inj.setParameters(axis, kAmp, 10.f, 1.f, 20.f, 3, 0.f);
}

IndiInjectionStepIn stepIn(int point, uint64_t t_us)
{
	IndiInjectionStepIn in{};
	in.point = point;
	in.armed = true;
	in.landed = false;
	in.rate_sp_break_allowed = true;
	in.timestamp_sample = t_us;
	in.dt = kDt;
	return in;
}
}

// Fixed inputs: the law is stateful, so the test and the reference run the same sequence cycle by cycle.
TEST(IndiInjectionStepTest, RateSetpointBreakFeedsLawTheInjectedSetpoint)
{
	IndiRateControl law = makeLaw();
	IndiRateControl ref_x = makeLaw();	// fed y + d by hand
	IndiRateControl ref_y = makeLaw();	// fed y (what a broken call site would pass)
	IndiInjection inj;
	IndiInjection gen;			// the generator for d
	setup(inj, 2);
	setup(gen, 2);
	const Vector3f rates(0.1f, -0.05f, 0.02f), sp(0.2f, 0.1f, 0.f), acc(0.f, 0.f, 0.f), prev(0.f, 0.f, 0.f);
	float max_diff_to_y = 0.f;

	for (int k = 0; k < 400; k++) {
		const uint64_t t = kT0 + (uint64_t)k * 2500;
		IndiInjectionStepOut out{};
		runIndiInjectionStep(law, inj, stepIn(1, t), rates, sp, acc, prev, out);

		Vector3f x = sp;
		const float d = gen.update(t, true, false);
		x(1) += d;
		const Vector3f c_x = ref_x.update(rates, x, acc, prev, kDt, false, false);
		const Vector3f c_y = ref_y.update(rates, sp, acc, prev, kDt, false, false);

		// law got x: output and the lead state equal the reference fed x, to the bit
		EXPECT_EQ(memcmp(&out.torque_pre_inject, &c_x, sizeof(c_x)), 0) << "cycle " << k;
		EXPECT_EQ(law.getRateSpDot()(1), ref_x.getRateSpDot()(1)) << "cycle " << k;
		// u == c: the torque is not injected at this break point
		EXPECT_EQ(memcmp(&out.torque_sp, &out.torque_pre_inject, sizeof(c_x)), 0);
		EXPECT_EQ(out.torque_inject(1), 0.f);
		// logged signals
		EXPECT_EQ(out.rates_sp_applied(1), x(1));
		EXPECT_EQ(out.rates_sp_pre_inject(1), sp(1));
		EXPECT_EQ(out.rates_sp_inject(1), d);

		max_diff_to_y = fmaxf(max_diff_to_y, fabsf(out.torque_pre_inject(1) - c_y(1)));
	}

	// the test must be able to tell x from y: the law output differs when d is fed
	EXPECT_GT(max_diff_to_y, 1e-3f);
}

TEST(IndiInjectionStepTest, RateSetpointBreakOnlySelectedAxisAndSign)
{
	for (int axis = 1; axis <= 3; axis++) {
		IndiRateControl law = makeLaw();
		IndiInjection inj;
		IndiInjection gen;
		setup(inj, axis);
		setup(gen, axis);
		const Vector3f z;
		const Vector3f sp(0.3f, -0.2f, 0.1f);
		float peak = 0.f;

		for (int k = 0; k < 800; k++) {
			const uint64_t t = kT0 + (uint64_t)k * 2500;
			IndiInjectionStepOut out{};
			runIndiInjectionStep(law, inj, stepIn(1, t), z, sp, z, z, out);
			const float d = gen.update(t, true, false);

			for (int i = 0; i < 3; i++) {
				const float want = (i == axis - 1) ? d : 0.f;
				EXPECT_EQ(out.rates_sp_inject(i), want);
				EXPECT_EQ(out.rates_sp_applied(i), sp(i) + want);
				EXPECT_EQ(out.rates_sp_pre_inject(i), sp(i));
			}

			peak = fmaxf(peak, fabsf(d));
		}

		EXPECT_GT(peak, 0.05f); // the generator really excited something
	}
}

TEST(IndiInjectionStepTest, TorqueBreakUnchanged)
{
	// PT 0: law gets y, u = c + d, rate setpoint fields stay zero
	IndiRateControl law = makeLaw();
	IndiRateControl ref = makeLaw();
	IndiInjection inj;
	IndiInjection gen;
	setup(inj, 1);
	setup(gen, 1);
	const Vector3f rates(0.1f, 0.f, 0.f), sp(0.2f, 0.f, 0.f), z;

	for (int k = 0; k < 400; k++) {
		const uint64_t t = kT0 + (uint64_t)k * 2500;
		IndiInjectionStepOut out{};
		runIndiInjectionStep(law, inj, stepIn(0, t), rates, sp, z, z, out);
		const Vector3f c = ref.update(rates, sp, z, z, kDt, false, false);
		const float d = gen.update(t, true, false);
		EXPECT_EQ(out.torque_pre_inject(0), c(0));
		EXPECT_EQ(out.torque_inject(0), d);
		EXPECT_EQ(out.torque_sp(0), c(0) + d);
		EXPECT_EQ(out.rates_sp_applied(0), 0.f);
		EXPECT_EQ(out.rates_sp_inject(0), 0.f);
	}
}

TEST(IndiInjectionStepTest, OffIsBitIdentical)
{
	IndiRateControl law = makeLaw();
	IndiRateControl ref = makeLaw();
	IndiInjection inj;
	setup(inj, 0);
	const Vector3f rates(0.1f, 0.02f, 0.f), sp(0.2f, 0.1f, 0.05f), z;

	for (int pt = 0; pt <= 1; pt++) {
		for (int k = 0; k < 100; k++) {
			IndiInjectionStepOut out{};
			runIndiInjectionStep(law, inj, stepIn(pt, kT0 + k * 2500), rates, sp, z, z, out);
			const Vector3f c = ref.update(rates, sp, z, z, kDt, false, false);
			EXPECT_EQ(memcmp(&out.torque_sp, &c, sizeof(c)), 0);
			EXPECT_EQ(out.rates_sp_applied(0), 0.f);
			EXPECT_EQ(out.rates_sp_inject(1), 0.f);
		}
	}
}

TEST(IndiInjectionStepTest, RateSetpointBreakNeedsAllEnableConditions)
{
	const Vector3f z, sp(0.2f, 0.1f, 0.f);

	// each condition alone must give d == 0 and a law input equal to y, in a window where d would be non zero
	for (int g = 0; g < 4; g++) {
		IndiRateControl law = makeLaw();
		IndiInjection inj;
		setup(inj, 1);
		float peak = 0.f;

		for (int k = 0; k < 800; k++) {
			IndiInjectionStepIn in = stepIn(1, kT0 + (uint64_t)k * 2500);
			in.armed = (g != 0);
			in.landed = (g == 1);
			in.rate_sp_break_allowed = (g != 2); // stale or not attitude controlled (ACRO)
			IndiInjectionStepOut out{};
			runIndiInjectionStep(law, inj, in, z, sp, z, z, out);
			peak = fmaxf(peak, fabsf(out.rates_sp_inject(0)));
			EXPECT_EQ(out.rates_sp_applied(0), sp(0) + out.rates_sp_inject(0));
		}

		if (g == 3) {
			EXPECT_GT(peak, 0.05f);

		} else {
			EXPECT_EQ(peak, 0.f) << "condition " << g;
		}
	}
}

// A break enable condition that turns false in flight (v 0: stale or ACRO, v 1: law fault on the previous cycle) zeroes d and restarts the
// sequence from its beginning when it turns true again: d then equals a fresh generator started at the reopening cycle.
TEST(IndiInjectionStepTest, RateSetpointBreakDisabledInFlightRestartsSequence)
{
	const Vector3f z, sp(0.2f, 0.1f, 0.f);
	const Vector3f nan_rates(NAN, 0.f, 0.f);

	for (int v = 0; v < 2; v++) {
		IndiRateControl law = makeLaw();
		IndiInjection inj;
		IndiInjection ref;
		setup(inj, 1);
		setup(ref, 1);
		const int closed_first = (v == 0) ? 300 : 301;
		const int reopen = (v == 0) ? 310 : 302;
		float peak_after = 0.f;

		for (int k = 0; k < 800; k++) {
			const uint64_t t = kT0 + (uint64_t)k * 2500;
			IndiInjectionStepIn in = stepIn(1, t);
			in.rate_sp_break_allowed = !(v == 0 && k >= 300 && k < 310);
			IndiInjectionStepOut out{};
			runIndiInjectionStep(law, inj, in, (v == 1 && k == 300) ? nan_rates : z, sp, z, z, out);

			if (k >= closed_first && k < reopen) {
				EXPECT_EQ(out.rates_sp_inject(0), 0.f) << "v " << v << " k " << k;

			} else if (k >= reopen) {
				EXPECT_EQ(out.rates_sp_inject(0), ref.update(t, true, false)) << "v " << v << " k " << k;
				peak_after = fmaxf(peak_after, fabsf(out.rates_sp_inject(0)));
			}
		}

		EXPECT_GT(peak_after, 0.05f) << "v " << v;
	}
}

TEST(IndiInjectionStepTest, TorqueBreakNotInjectedWhileDisarmedOrLanded)
{
	// PT 0: the generator gets the real armed/landed flags (header of IndiInjection::update: zero when disarmed or landed)
	IndiRateControl law = makeLaw();
	IndiInjection inj;
	setup(inj, 1);
	const Vector3f rates(0.1f, 0.f, 0.f), sp(0.2f, 0.f, 0.f), z;
	IndiInjectionStepOut out{};

	runIndiInjectionStep(law, inj, stepIn(0, kT0), rates, sp, z, z, out); // origin
	runIndiInjectionStep(law, inj, stepIn(0, kT0 + 3700000), rates, sp, z, z, out);
	EXPECT_GT(fabsf(out.torque_inject(0)), 0.01f); // active: 0.1 * 0.1196 / 0.02 = 0.598

	IndiInjectionStepIn in = stepIn(0, kT0 + 3800000);
	in.armed = false;
	runIndiInjectionStep(law, inj, in, rates, sp, z, z, out);
	EXPECT_EQ(out.torque_inject(0), 0.f);
	EXPECT_EQ(out.torque_sp(0), out.torque_pre_inject(0));

	// disarm restarted the sequence: new origin at the next armed cycle, active again 3.7 s later
	const uint64_t t1 = kT0 + 10000000;
	runIndiInjectionStep(law, inj, stepIn(0, t1), rates, sp, z, z, out);
	runIndiInjectionStep(law, inj, stepIn(0, t1 + 3700000), rates, sp, z, z, out);
	EXPECT_GT(fabsf(out.torque_inject(0)), 0.01f);

	in = stepIn(0, t1 + 3800000);
	in.landed = true;
	runIndiInjectionStep(law, inj, in, rates, sp, z, z, out);
	EXPECT_EQ(out.torque_inject(0), 0.f);
}

TEST(IndiInjectionStepTest, ReusedOutputHasNoStaleFieldsAcrossBreakPoints)
{
	// the module keeps the output struct between cycles: the fields of the inactive break point must be cleared
	IndiRateControl law = makeLaw();
	IndiInjection inj;
	setup(inj, 1);
	const Vector3f rates(0.1f, 0.f, 0.f), sp(0.2f, 0.f, 0.f), z;
	IndiInjectionStepOut out{};

	runIndiInjectionStep(law, inj, stepIn(0, kT0), rates, sp, z, z, out);
	runIndiInjectionStep(law, inj, stepIn(0, kT0 + 3700000), rates, sp, z, z, out);
	ASSERT_GT(fabsf(out.torque_inject(0)), 0.01f);

	// PT 1 after PT 0: torque injection must read zero, rate setpoint fields filled
	runIndiInjectionStep(law, inj, stepIn(1, kT0 + 3800000), rates, sp, z, z, out);
	EXPECT_EQ(out.torque_inject(0), 0.f);
	EXPECT_EQ(out.torque_sp(0), out.torque_pre_inject(0));
	ASSERT_GT(fabsf(out.rates_sp_inject(0)), 1e-4f);
	EXPECT_EQ(out.rates_sp_pre_inject(0), sp(0));

	// PT 0 after PT 1: rate setpoint fields must read zero again
	runIndiInjectionStep(law, inj, stepIn(0, kT0 + 3900000), rates, sp, z, z, out);
	EXPECT_EQ(out.rates_sp_pre_inject(0), 0.f);
	EXPECT_EQ(out.rates_sp_inject(0), 0.f);
	EXPECT_EQ(out.rates_sp_applied(0), 0.f);
	EXPECT_GT(fabsf(out.torque_inject(0)), 0.01f);

	// injection switched off with the same stale output: torque injection reads zero
	setup(inj, 0);
	runIndiInjectionStep(law, inj, stepIn(0, kT0 + 4000000), rates, sp, z, z, out);
	EXPECT_EQ(out.torque_inject(0), 0.f);
	EXPECT_EQ(out.torque_sp(0), out.torque_pre_inject(0));
}
