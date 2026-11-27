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

#include "IndiEscThrust.hpp"

namespace
{

constexpr float kRotorWMax_radps = 1000.f;
constexpr float kRpmMax = kRotorWMax_radps * (60.f / (2.f *M_PI_F));

esc_status_s makeStatus(const float ratio[4])
{
	esc_status_s status{};
	status.esc_count = 4;
	status.esc_online_flags = 0xF;

	for (int j = 0; j < 4; j++) {
		status.esc[j].actuator_function = esc_report_s::ACTUATOR_FUNCTION_MOTOR1 + j;
		status.esc[j].esc_rpm = (int32_t)(ratio[j] * kRpmMax);
	}

	return status;
}

bool evaluate(const esc_status_s &status, float rotor_w_max, float &mean)
{
	const IndiEscThrust::MeanRotorThrust result = IndiEscThrust::meanRotorThrust(status, rotor_w_max);
	mean = result.thrust;
	return result.valid;
}

constexpr float kHalfAndFull[4] = {0.5f, 0.5f, 1.f, 1.f};

} // namespace

TEST(IndiEscThrustTest, FourMotorsGiveTheMeanOfTheSquaredRatios)
{
	const esc_status_s status = makeStatus(kHalfAndFull);
	float mean = 0.f;
	EXPECT_TRUE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_NEAR(mean, (0.25f + 0.25f + 1.f + 1.f) / 4.f, 1e-3f);
}

TEST(IndiEscThrustTest, MissingMotorIsInvalid)
{
	esc_status_s status = makeStatus(kHalfAndFull);
	status.esc_count = 3;
	float mean = 0.f;
	EXPECT_FALSE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_TRUE(std::isnan(mean));
}

TEST(IndiEscThrustTest, DuplicateMotorDoesNotCompleteTheSet)
{
	esc_status_s status = makeStatus(kHalfAndFull);
	status.esc[3].actuator_function = esc_report_s::ACTUATOR_FUNCTION_MOTOR1;
	float mean = 0.f;
	EXPECT_FALSE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_TRUE(std::isnan(mean));
}

TEST(IndiEscThrustTest, OfflineMotorIsInvalid)
{
	for (int j = 0; j < 4; j++) {
		esc_status_s status = makeStatus(kHalfAndFull);
		status.esc_online_flags &= ~(1u << j);
		float mean = 0.f;
		EXPECT_FALSE(evaluate(status, kRotorWMax_radps, mean)) << j;
		EXPECT_TRUE(std::isnan(mean)) << j;
	}
}

TEST(IndiEscThrustTest, EntriesOfOtherFunctionsAreIgnored)
{
	esc_status_s status = makeStatus(kHalfAndFull);
	status.esc_count = 5;
	status.esc[4].actuator_function = 0;
	status.esc[4].esc_rpm = -1;
	status.esc_online_flags = 0xF; // the extra entry is offline and invalid, and does not matter
	float mean = 0.f;
	EXPECT_TRUE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_NEAR(mean, 0.625f, 1e-3f);
}

TEST(IndiEscThrustTest, RpmAboveOneAndAHalfTimesMaxIsRejectedBelowItIsClamped)
{
	const float over[4] = {0.5f, 0.5f, 1.f, 1.49f};
	esc_status_s status = makeStatus(over);
	float mean = 0.f;
	EXPECT_TRUE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_NEAR(mean, 0.625f, 1e-3f); // 1.49 of the maximum counts as full thrust

	status.esc[3].esc_rpm = (int32_t)(1.51f * kRpmMax);
	EXPECT_FALSE(evaluate(status, kRotorWMax_radps, mean));
	EXPECT_TRUE(std::isnan(mean));

	status.esc[3].esc_rpm = -1; // reverse rotation is rejected as well
	EXPECT_FALSE(evaluate(status, kRotorWMax_radps, mean));
}

TEST(IndiEscThrustTest, NoRotorSpeedLimitIsInvalid)
{
	const esc_status_s status = makeStatus(kHalfAndFull);
	float mean = 0.f;
	EXPECT_FALSE(evaluate(status, 0.f, mean));
	EXPECT_TRUE(std::isnan(mean));
}

TEST(IndiEscThrustTest, FreshnessBoundaryIsInclusive)
{
	constexpr uint64_t kStamp_us = 1'000'000;
	constexpr uint64_t kMaxAge_us = 100'000;
	EXPECT_TRUE(IndiEscThrust::isFresh(true, kStamp_us, kStamp_us, kMaxAge_us));
	EXPECT_TRUE(IndiEscThrust::isFresh(true, kStamp_us + kMaxAge_us, kStamp_us, kMaxAge_us));
	EXPECT_FALSE(IndiEscThrust::isFresh(true, kStamp_us + kMaxAge_us + 1, kStamp_us, kMaxAge_us));
}

TEST(IndiEscThrustTest, SampleFromTheFutureHasAgeZero)
{
	// stamped after the cycle time (published while the cycle ran): fresh, also with a huge difference
	EXPECT_TRUE(IndiEscThrust::isFresh(true, 1000, 1500, 100'000));
	EXPECT_TRUE(IndiEscThrust::isFresh(true, 0, UINT64_MAX / 2, 100'000));
}

TEST(IndiEscThrustTest, InvalidSampleIsNeverFresh)
{
	EXPECT_FALSE(IndiEscThrust::isFresh(false, 1000, 1000, 100'000));
}
