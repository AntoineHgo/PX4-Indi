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

#include "EkfResetDetect.hpp"

TEST(EkfResetDetectTest, FirstSampleDoesNotReset)
{
	EkfResetDetector d;
	EkfResetCounters c;
	c.xy = 7; c.vz = 3; // already non zero at start
	EXPECT_FALSE(d.update(c));
	EXPECT_FALSE(d.update(c));
}

TEST(EkfResetDetectTest, NoBumpNoReset)
{
	EkfResetDetector d;
	EkfResetCounters c;
	EXPECT_FALSE(d.update(c));

	for (int i = 0; i < 5; i++) { EXPECT_FALSE(d.update(c)); }
}

TEST(EkfResetDetectTest, EachCounterBumpIsDetectedOnce)
{
	for (int k = 0; k < 5; k++) {
		EkfResetDetector d;
		EkfResetCounters c;
		d.update(c);

		switch (k) {
		case 0: c.xy++; break;

		case 1: c.z++; break;

		case 2: c.vxy++; break;

		case 3: c.vz++; break;

		default: c.heading++; break;
		}

		EXPECT_TRUE(d.update(c)) << "counter " << k;
		EXPECT_FALSE(d.update(c)) << "counter " << k; // once
	}
}

TEST(EkfResetDetectTest, WrapAroundIsDetected)
{
	EkfResetDetector d;
	EkfResetCounters c;
	c.z = 255;
	d.update(c);
	c.z = 0;
	EXPECT_TRUE(d.update(c));
}

TEST(EkfResetDetectTest, TwoBumpsInOneSampleGiveOneTrue)
{
	EkfResetDetector d;
	EkfResetCounters c;
	d.update(c);
	c.xy++; c.heading++;
	EXPECT_TRUE(d.update(c));
	EXPECT_FALSE(d.update(c));
}
