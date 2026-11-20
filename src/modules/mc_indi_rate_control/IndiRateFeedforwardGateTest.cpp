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
#include "IndiRateFeedforwardGate.hpp"

static constexpr uint64_t T0 = 10000000;

TEST(IndiRateFeedforwardGateTest, ValidAndFreshPasses)
{
	EXPECT_TRUE(IndiRateFeedforwardGate::allow(true, T0, T0, false, false, false));
	EXPECT_TRUE(IndiRateFeedforwardGate::allow(true, T0, T0 + 49999, false, false, false));
	EXPECT_TRUE(IndiRateFeedforwardGate::allow(true, T0 + 100, T0, false, false, false)); // stamp ahead: age 0
}

TEST(IndiRateFeedforwardGateTest, InvalidFlagBlocks)
{
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(false, T0, T0, false, false, false));
}

TEST(IndiRateFeedforwardGateTest, StaleBlocks)
{
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, T0, T0 + 50000, false, false, false));
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, T0, T0 + 500000, false, false, false));
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, 0, T0, false, false, false)); // never received
}

TEST(IndiRateFeedforwardGateTest, LandedBlocks)
{
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, T0, T0, true, false, false));
}

TEST(IndiRateFeedforwardGateTest, ManualAcroBranchBlocks)
{
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, T0, T0, false, true, false));
}

TEST(IndiRateFeedforwardGateTest, WatchdogTrippedBlocks)
{
	EXPECT_FALSE(IndiRateFeedforwardGate::allow(true, T0, T0, false, false, true));
}
