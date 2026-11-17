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
#include "RateSetpointWatchdog.hpp"

static constexpr uint64_t DT = 4000;
static constexpr uint64_t T0 = 10000000;

class IndiRateSetpointWatchdogTest : public ::testing::Test
{
protected:
	void SetUp() override { w.setTimeout(0.5f); }
	RateSetpointWatchdog w;
};

TEST_F(IndiRateSetpointWatchdogTest, StaleAfterTimeoutZeroesRates)
{
	EXPECT_FALSE(w.update(T0, T0 + 500000, true, true).stale); // exactly timeout: not yet
	const auto r = w.update(T0, T0 + 500000 + DT, true, true);
	EXPECT_TRUE(r.stale);
	EXPECT_TRUE(r.zero_rates);
	EXPECT_TRUE(r.warn);
}

TEST_F(IndiRateSetpointWatchdogTest, NoTripOneCycleBeforeTimeout)
{
	EXPECT_FALSE(w.update(T0, T0 + 500000 - DT, true, true).stale);
}

TEST_F(IndiRateSetpointWatchdogTest, FreshMessageClearsInOneCycle)
{
	EXPECT_TRUE(w.update(T0, T0 + 600000, true, true).stale);
	const uint64_t fresh = T0 + 600000 + DT;
	const auto r = w.update(fresh, fresh, true, true);
	EXPECT_FALSE(r.stale);
	EXPECT_FALSE(r.zero_rates);
}

TEST_F(IndiRateSetpointWatchdogTest, InactiveDisarmedOrAcro)
{
	EXPECT_FALSE(w.update(T0, T0 + 5000000, false, true).stale);
	EXPECT_FALSE(w.update(T0, T0 + 5000000, true, false).stale);
	EXPECT_FALSE(w.update(0, T0, false, true).stale);
}

TEST_F(IndiRateSetpointWatchdogTest, NeverReceivedWhileArmedIsStale)
{
	const auto r = w.update(0, T0, true, true);
	EXPECT_TRUE(r.stale);
	EXPECT_TRUE(r.zero_rates);
}

TEST_F(IndiRateSetpointWatchdogTest, WarningIsRateLimited)
{
	int warns = 0;

	for (uint64_t t = T0 + 600000; t < T0 + 600000 + 5000000; t += DT) {
		warns += w.update(T0, t, true, true).warn;
	}

	EXPECT_GE(warns, 2);
	EXPECT_LE(warns, 3);
}
