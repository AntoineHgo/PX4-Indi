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
 * @file IndiInjectionTest.cpp
 *
 * The excitation must reproduce indi_flight/bench/margins_est.py log_bins() and multisine().
 */

#include <gtest/gtest.h>

#include "IndiInjection.hpp"

TEST(IndiInjectionTest, OffIsExactZero)
{
	IndiInjection inj;
	inj.setParameters(0, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), -1);
	EXPECT_EQ(inj.numComponents(), 0);
	EXPECT_EQ(inj.update(5000000, true, false), 0.f);
}

TEST(IndiInjectionTest, MatchesMarginsEst)
{
	// margins_est.log_bins(1, 60, 10) = 10, 13, ... 501 (18 bins), multisine amplitude 0.02, Schroeder phases
	IndiInjection inj;
	inj.setParameters(1, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), 0);
	ASSERT_EQ(inj.numComponents(), 18);

	EXPECT_NEAR(inj.waveform(0.0), -2.706168622523819e-16, 1e-9);
	EXPECT_NEAR(inj.waveform(0.123456), 0.013155497388233033, 1e-6);
	EXPECT_NEAR(inj.waveform(3.7), 0.11957619297037093, 1e-6);
	EXPECT_NEAR(inj.waveform(12.34), -0.021955507529366248, 1e-6);

	// bin count with the default frequency range and a long period (margins_est.log_bins(0.5, 60, 20) has 21)
	IndiInjection inj2;
	inj2.setParameters(2, 0.02f, 20.f, 0.5f, 60.f, 3, 0.f);
	EXPECT_EQ(inj2.axis(), 1);
	EXPECT_EQ(inj2.numComponents(), 21);
}

TEST(IndiInjectionTest, Gating)
{
	IndiInjection inj;
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);

	// disarmed or landed: nothing, and the origin is not set
	EXPECT_EQ(inj.update(1000000, false, false), 0.f);
	EXPECT_EQ(inj.update(2000000, true, true), 0.f);

	// origin = first armed and airborne cycle
	const uint64_t t0 = 3000000;
	EXPECT_NEAR(inj.update(t0, true, false), 0.f, 1e-9f);
	EXPECT_NEAR(inj.update(t0 + 3700000, true, false), 0.11957619297037093, 1e-6);

	// landed in the middle: zero, resumes on the same clock
	EXPECT_EQ(inj.update(t0 + 3800000, true, true), 0.f);
	EXPECT_NEAR(inj.update(t0 + 12340000 - 10000000, true, false), inj.waveform(2.34), 1e-6);

	// after n_periods * period: zero
	EXPECT_EQ(inj.update(t0 + 20000000, true, false), 0.f);
	EXPECT_EQ(inj.update(t0 + 30000000, true, false), 0.f);
}

TEST(IndiInjectionTest, ComponentLimit)
{
	IndiInjection inj;
	inj.setParameters(1, 0.02f, 100.f, 0.01f, 200.f, 1, 0.f);
	EXPECT_LE(inj.numComponents(), IndiInjection::MAX_COMPONENTS);
	EXPECT_GT(inj.numComponents(), 0);
}
