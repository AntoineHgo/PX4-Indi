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
