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

#include "IndiRateSetpointSource.hpp"

using IndiRateSetpointSource::mask;

TEST(IndiRateSetpointSourceTest, EachInputChangesTheMask)
{
	const uint8_t base = mask(true, true, false, false, false, false);
	EXPECT_NE(mask(false, true, false, false, false, false), base);
	EXPECT_NE(mask(true, false, false, false, false, false), base);
	EXPECT_NE(mask(true, true, true, false, false, false), base);
	EXPECT_NE(mask(true, true, false, true, false, false), base);
	EXPECT_NE(mask(true, true, false, false, true, false), base);
	EXPECT_NE(mask(true, true, false, false, false, true), base);
}

TEST(IndiRateSetpointSourceTest, OmegaFeedForwardToggleChangesTheMask)
{
	const uint8_t off = mask(true, true, false, true, false, false);
	const uint8_t on = mask(true, true, false, true, false, true);
	EXPECT_NE(off, on);
	EXPECT_EQ(on, mask(true, true, false, true, false, true)); // unchanged input, unchanged mask
}

TEST(IndiRateSetpointSourceTest, InputsDoNotAlias)
{
	// every combination of the six inputs maps to its own mask
	bool seen[64] = {};

	for (unsigned v = 0; v < 64; v++) {
		const uint8_t m = mask(v & 1, v & 2, v & 4, v & 8, v & 16, v & 32);
		ASSERT_LT(m, 64);
		EXPECT_FALSE(seen[m]) << v;
		seen[m] = true;
	}
}
