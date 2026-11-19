#include <gtest/gtest.h>

#include "HandoverBlend.hpp"

using matrix::Vector3f;

// A-45 numbers: bypass a_z -0.61 (stock integrator included), first stage a_ref z -3.28
TEST(HandoverBlendTest, FirstStageCycleIsContinuous)
{
	HandoverBlend h;
	h.bypass(Vector3f(0.1f, -0.2f, -0.61f));
	const Vector3f out = h.apply(Vector3f(0.f, 0.f, -3.28f), 0.01f);
	EXPECT_NEAR(out(0), 0.1f, 1e-6f);
	EXPECT_NEAR(out(1), -0.2f, 1e-6f);
	EXPECT_NEAR(out(2), -0.61f, 1e-6f);
}

TEST(HandoverBlendTest, OffsetDecaysWithTau)
{
	HandoverBlend h;
	h.setTimeConstant(0.5f);
	h.bypass(Vector3f(0.f, 0.f, -0.61f));
	const Vector3f a_ref(0.f, 0.f, -3.28f);
	h.apply(a_ref, 0.01f);

	for (int i = 0; i < 50; i++) { h.apply(a_ref, 0.01f); } // 0.5 s = tau

	EXPECT_NEAR(h.offset()(2), 2.67f * expf(-1.f), 1e-3f);
	// 0.1 s after the edge the change is < 1 - exp(-0.2) = 18 % of the step
	HandoverBlend g;
	g.bypass(Vector3f(0.f, 0.f, -0.61f));
	const float first = g.apply(a_ref, 0.01f)(2);
	float out = first;

	for (int i = 0; i < 10; i++) { out = g.apply(a_ref, 0.01f)(2); }

	EXPECT_LT(fabsf(out - first), 0.19f * 2.67f);
	EXPECT_GT(fabsf(out - first), 0.17f * 2.67f);
}

TEST(HandoverBlendTest, NoBypassNoOffset)
{
	HandoverBlend h;
	const Vector3f out = h.apply(Vector3f(1.f, 2.f, 3.f), 0.01f);
	EXPECT_EQ(out, Vector3f(1.f, 2.f, 3.f));
}

TEST(HandoverBlendTest, CapturedOnceOnly)
{
	HandoverBlend h;
	h.setTimeConstant(0.5f);
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.apply(Vector3f(0.f, 0.f, -2.f), 0.01f);
	// a later a_ref step while the stage runs is not absorbed
	const Vector3f out = h.apply(Vector3f(0.f, 0.f, -5.f), 0.01f);
	EXPECT_NEAR(out(2), -5.f + expf(-0.02f), 1e-4f);
}

TEST(HandoverBlendTest, NonFiniteInputsGiveNoOffset)
{
	HandoverBlend h;
	h.bypass(Vector3f(NAN, 0.f, 0.f));
	EXPECT_EQ(h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f), Vector3f(0.f, 0.f, -3.f));
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.apply(Vector3f(NAN, 0.f, 0.f), 0.01f);
	EXPECT_EQ(h.offset(), Vector3f{});
}

TEST(HandoverBlendTest, DisabledByTau)
{
	HandoverBlend h;
	h.setTimeConstant(0.f);
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	EXPECT_EQ(h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f), Vector3f(0.f, 0.f, -3.f));
}

TEST(HandoverBlendTest, BypassDropsResidualOffset)
{
	HandoverBlend h;
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f);
	// a bypass with a non-finite acceleration: no capture, and the old offset must not come back
	h.bypass(Vector3f(NAN, 0.f, 0.f));
	EXPECT_EQ(h.apply(Vector3f(0.f, 0.f, -4.f), 0.01f), Vector3f(0.f, 0.f, -4.f));
}

TEST(HandoverBlendTest, DecayRunsDuringHold)
{
	HandoverBlend h;
	h.setTimeConstant(0.5f);
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f); // offset 2

	for (int i = 0; i < 50; i++) { h.decay(0.01f); }

	EXPECT_NEAR(h.offset()(2), 2.f * expf(-1.f), 1e-3f);
	// a pending capture is not decayed away before it happens
	HandoverBlend g;
	g.bypass(Vector3f(0.f, 0.f, -1.f));
	g.decay(1.f);
	EXPECT_NEAR(g.apply(Vector3f(0.f, 0.f, -3.f), 0.01f)(2), -1.f, 1e-6f);
}

TEST(HandoverBlendTest, ClearDropsCaptureAndOffset)
{
	HandoverBlend h;
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f);
	h.clear();
	EXPECT_EQ(h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f), Vector3f(0.f, 0.f, -3.f));
	h.bypass(Vector3f(0.f, 0.f, -1.f));
	h.clear();
	EXPECT_EQ(h.apply(Vector3f(0.f, 0.f, -3.f), 0.01f), Vector3f(0.f, 0.f, -3.f));
}
