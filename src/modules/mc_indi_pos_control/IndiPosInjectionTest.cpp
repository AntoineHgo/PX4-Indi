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
 * @file IndiPosInjectionTest.cpp
 *
 * The excitation must reproduce the log-spaced bins and Schroeder phases of the reference multisine.
 */

#include <gtest/gtest.h>
#include <math.h>

#include "IndiPosInjection.hpp"

TEST(IndiPosInjectionTest, OffIsExactZero)
{
	IndiPosInjection inj;
	inj.setParameters(0, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), -1);
	EXPECT_EQ(inj.numComponents(), 0);
	EXPECT_EQ(inj.update(5000000, true, false), 0.f);
}

TEST(IndiPosInjectionTest, MatchesReferenceMultisine)
{
	// reference bins for 1..60 Hz with Tp = 10 s: 10, 13, ... 501 (18 bins), multisine amplitude 0.02, Schroeder phases
	IndiPosInjection inj;
	inj.setParameters(1, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), 0);
	ASSERT_EQ(inj.numComponents(), 18);

	EXPECT_NEAR(inj.waveform(0.0), -2.706168622523819e-16, 1e-9);
	EXPECT_NEAR(inj.waveform(0.123456), 0.013155497388233033, 1e-6);
	EXPECT_NEAR(inj.waveform(3.7), 0.11957619297037093, 1e-6);
	EXPECT_NEAR(inj.waveform(12.34), -0.021955507529366248, 1e-6);

	// bin count with the default frequency range and a long period (0.5..60 Hz with Tp = 20 s gives 21 bins)
	IndiPosInjection inj2;
	inj2.setParameters(2, 0.02f, 20.f, 0.5f, 60.f, 3, 0.f);
	EXPECT_EQ(inj2.axis(), 1);
	EXPECT_EQ(inj2.numComponents(), 21);
}

TEST(IndiPosInjectionTest, Gating)
{
	IndiPosInjection inj;
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

TEST(IndiPosInjectionTest, RearmRestartsWindow)
{
	// the module cannot call update() while disarmed, it calls reset() instead: a second arm in the same boot starts a new window
	IndiPosInjection inj;
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 1, 2.f);

	const uint64_t t0 = 1000000;
	EXPECT_EQ(inj.update(t0, true, false), 0.f); // origin t0 + 2 s (delay)
	EXPECT_NEAR(inj.update(t0 + 2000000 + 3700000, true, false), 0.11957619297037093, 1e-6);
	EXPECT_EQ(inj.update(t0 + 20000000, true, false), 0.f); // window over (1 period)

	inj.reset(); // disarmed

	const uint64_t t1 = 100000000;
	EXPECT_EQ(inj.update(t1, true, false), 0.f); // new origin t1 + 2 s
	EXPECT_EQ(inj.update(t1 + 1000000, true, false), 0.f); // still in the delay
	EXPECT_NEAR(inj.update(t1 + 2000000 + 3700000, true, false), 0.11957619297037093, 1e-6);
	EXPECT_EQ(inj.update(t1 + 20000000, true, false), 0.f);
}

TEST(IndiPosInjectionTest, ComponentLimit)
{
	IndiPosInjection inj;
	inj.setParameters(1, 0.02f, 100.f, 0.01f, 200.f, 1, 0.f);
	EXPECT_LE(inj.numComponents(), IndiPosInjection::MAX_COMPONENTS);
	EXPECT_GT(inj.numComponents(), 0);
}

TEST(IndiPosInjectionTest, BinContent)
{
	// one period sampled at 2 kHz: each selected bin carries the amplitude, a bin that is not selected carries nothing
	const float tp = 10.f;
	const double amp = 0.3;
	IndiPosInjection inj;
	inj.setParameters(3, (float)amp, tp, 0.5f, 20.f, 1, 0.f);
	EXPECT_EQ(inj.axis(), 2);
	const int n = 20000;
	const double dt = tp / n;

	auto bin = [&](int k) {
		double re = 0.0;
		double im = 0.0;

		for (int i = 0; i < n; i++) {
			const double w = inj.waveform(i * dt);
			const double a = 2.0 * M_PI * k * i / n;
			re += w * cos(a);
			im -= w * sin(a);
		}

		return 2.0 * sqrt(re * re + im * im) / n;
	};

	int on_bins = 0;

	for (int k = 1; k < 200; k++) {
		const double m = bin(k);

		if (m > 0.5 * amp) {
			EXPECT_NEAR(m, amp, 1e-3);
			on_bins++;

		} else {
			EXPECT_LT(m, 1e-3);
		}
	}

	EXPECT_EQ(on_bins, inj.numComponents());
	EXPECT_GT(on_bins, 10);
}

// behaviour stated in the header

TEST(IndiPosInjectionTest, AxisOutOfRangeIsOff)
{
	// header: axis 0 off, 1..3 an axis, anything else off
	IndiPosInjection inj;
	inj.setParameters(4, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), -1);
	EXPECT_EQ(inj.numComponents(), 0);
	EXPECT_EQ(inj.update(5000000, true, false), 0.f);

	inj.setParameters(-1, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), -1);
	EXPECT_EQ(inj.numComponents(), 0);

	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 2, 0.f);
	EXPECT_EQ(inj.axis(), 2);
}

TEST(IndiPosInjectionTest, DelayHoldsOffTheStart)
{
	// origin = first airborne cycle + delay: exactly zero for the whole 2 s delay, then the waveform from its own t = 0
	IndiPosInjection inj;
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 2, 2.f);

	const uint64_t t0 = 1000000;
	EXPECT_EQ(inj.update(t0, true, false), 0.f);
	EXPECT_EQ(inj.update(t0 + 1000000, true, false), 0.f);
	EXPECT_EQ(inj.update(t0 + 1900000, true, false), 0.f);
	EXPECT_NEAR(inj.update(t0 + 2000000 + 3700000, true, false), 0.11957619297037093, 1e-6);
	// the window is n_periods * period = 20 s long from the origin, not from the first cycle
	EXPECT_NEAR(inj.update(t0 + 2000000 + 19900000, true, false), inj.waveform(19.9), 1e-6);
	EXPECT_EQ(inj.update(t0 + 2000000 + 20000000, true, false), 0.f);
}

TEST(IndiPosInjectionTest, InvalidRangeOrCountIsOff)
{
	// axis selected but the spectrum is not defined: no components, exact zero
	IndiPosInjection inj;
	inj.setParameters(1, 0.02f, 10.f, 60.f, 60.f, 2, 0.f); // f_max == f_min
	EXPECT_EQ(inj.numComponents(), 0);
	EXPECT_EQ(inj.update(5000000, true, false), 0.f);

	inj.setParameters(1, 0.02f, 10.f, 60.f, 1.f, 2, 0.f); // f_max < f_min
	EXPECT_EQ(inj.numComponents(), 0);

	inj.setParameters(1, 0.02f, 10.f, 0.f, 60.f, 2, 0.f); // f_min == 0
	EXPECT_EQ(inj.numComponents(), 0);

	inj.setParameters(1, 0.02f, 0.f, 1.f, 60.f, 2, 0.f); // period == 0
	EXPECT_EQ(inj.numComponents(), 0);

	inj.setParameters(1, 0.02f, 10.f, 1.f, 60.f, 0, 0.f); // no period flown
	EXPECT_EQ(inj.numComponents(), 0);
	EXPECT_EQ(inj.update(5000000, true, false), 0.f);

	inj.setParameters(1, 0.02f, 10.f, 1.f, 60.f, 1, 0.f); // valid again
	EXPECT_EQ(inj.numComponents(), 18);
}

TEST(IndiPosInjectionTest, BinsAreUniqueForShortPeriod)
{
	// Tp = 0.1 s: df = 10 Hz, the 19 log spaced candidates 1 .. 63 Hz collapse onto the bins k = 1 .. 6 (10 .. 60 Hz),
	// each kept once (hand derivation: candidates 5.0 .. 12.6 Hz -> k=1, 15.8 / 19.95 -> 2, 25.1 / 31.6 -> 3, 39.8 -> 4,
	// 50.1 -> 5, 63.1 -> 6 and 6 * 10 <= 60 + 5; below 5 Hz k = 0 is dropped)
	IndiPosInjection inj;
	inj.setParameters(1, 0.3f, 0.1f, 1.f, 60.f, 1, 0.f);
	ASSERT_EQ(inj.numComponents(), 6);

	// equal power: one period holds each bin with amplitude 0.3
	const int n = 1000;
	const double dt = 0.1 / n;
	double re = 0.0;
	double im = 0.0;

	for (int i = 0; i < n; i++) {
		const double w = inj.waveform(i * dt);
		const double a = 2.0 * M_PI * 3 * i / n;
		re += w * cos(a);
		im -= w * sin(a);
	}

	EXPECT_NEAR(2.0 * sqrt(re * re + im * im) / n, 0.3, 1e-3);
}

TEST(IndiPosInjectionTest, ParameterChangeRestartsOriginUnchangedKeepsIt)
{
	IndiPosInjection inj;
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 1, 0.f);

	const uint64_t t0 = 1000000;
	EXPECT_NEAR(inj.update(t0, true, false), 0.f, 1e-9f); // origin t0

	// same values again: nothing rebuilt, origin kept
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 1, 0.f);
	EXPECT_NEAR(inj.update(t0 + 3700000, true, false), 0.11957619297037093, 1e-6);

	// a changed amplitude restarts the origin at the next cycle and scales the waveform
	inj.setParameters(3, 0.04f, 10.f, 1.f, 60.f, 1, 0.f);
	const uint64_t t1 = t0 + 5000000;
	EXPECT_NEAR(inj.update(t1, true, false), 0.f, 1e-9f);
	EXPECT_NEAR(inj.update(t1 + 3700000, true, false), 2.0 * 0.11957619297037093, 1e-6);

	// only n_periods changed (1 -> 3): the window is rebuilt and now covers 25 s after the new origin
	EXPECT_EQ(inj.update(t1 + 25000000, true, false), 0.f); // one period only: over
	inj.setParameters(3, 0.04f, 10.f, 1.f, 60.f, 3, 0.f);
	const uint64_t t2 = t1 + 30000000;
	EXPECT_NEAR(inj.update(t2, true, false), 0.f, 1e-9f);
	EXPECT_NEAR(inj.update(t2 + 25000000, true, false), inj.waveform(25.0), 1e-6);
	EXPECT_GT(fabs(inj.waveform(25.0)), 1e-3);
}

TEST(IndiPosInjectionTest, DisarmedUpdateRestartsWindow)
{
	// a disarmed update() is the disarm edge: the next arm starts a new window after its own delay
	IndiPosInjection inj;
	inj.setParameters(3, 0.02f, 10.f, 1.f, 60.f, 1, 2.f);

	const uint64_t t0 = 1000000;
	EXPECT_EQ(inj.update(t0, true, false), 0.f);
	EXPECT_NEAR(inj.update(t0 + 2000000 + 3700000, true, false), 0.11957619297037093, 1e-6);
	EXPECT_EQ(inj.update(t0 + 20000000, true, false), 0.f); // window over

	EXPECT_EQ(inj.update(t0 + 21000000, false, false), 0.f); // disarmed

	const uint64_t t1 = 100000000;
	EXPECT_EQ(inj.update(t1, true, false), 0.f);
	EXPECT_EQ(inj.update(t1 + 1000000, true, false), 0.f);
	EXPECT_NEAR(inj.update(t1 + 2000000 + 3700000, true, false), 0.11957619297037093, 1e-6);
}
