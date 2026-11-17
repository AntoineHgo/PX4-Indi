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
#include "TorqueStampTracker.hpp"

TEST(IndiTorqueStampTrackerTest, OwnStampsNoFlag)
{
	TorqueStampTracker t;

	for (uint64_t ts = 1000; ts < 1000 + 500 * 4000; ts += 4000) {
		t.recordOwn(ts);
		EXPECT_FALSE(t.checkReceived(ts));
	}

	EXPECT_FALSE(t.foreignDetected());
}

TEST(IndiTorqueStampTrackerTest, InterleavedForeignFlagsWithinFewMessages)
{
	TorqueStampTracker t;
	int first_flag = -1;

	for (int i = 0; i < 20; i++) {
		const uint64_t own = 1000 + i * 4000;
		t.recordOwn(own);
		// every second message received is from another publisher
		const uint64_t rx = (i % 2) ? own + 1777 : own;
		t.checkReceived(rx);

		if (first_flag < 0 && t.foreignDetected()) { first_flag = i; }
	}

	EXPECT_GE(first_flag, 0);
	EXPECT_LE(first_flag, 2);
	EXPECT_TRUE(t.foreignDetected());
}

TEST(IndiTorqueStampTrackerTest, FlagClearsAfterOwnOnlyMessages)
{
	TorqueStampTracker t;
	EXPECT_TRUE(t.checkReceived(99));
	EXPECT_TRUE(t.foreignDetected());

	for (int i = 0; i < TorqueStampTracker::CLEAR_COUNT; i++) {
		t.recordOwn(5000 + i);
		t.checkReceived(5000 + i);
	}

	EXPECT_FALSE(t.foreignDetected());
}

TEST(IndiTorqueStampTrackerTest, OldOwnStampStillMatchesWithinRing)
{
	TorqueStampTracker t;

	for (uint64_t i = 1; i <= 4; i++) { t.recordOwn(i * 100); }

	EXPECT_FALSE(t.checkReceived(100));
	t.recordOwn(500);
	EXPECT_TRUE(t.checkReceived(100)); // pushed out of the ring
}
