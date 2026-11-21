# kMaxBlend 0.3 -> 0.5 (S150, G5.10)
Diff:
- src/lib/indi_accel_control/indi_accel_control.hpp:85-87 kMaxBlend 0.3f -> 0.5f, comment gives the 2x hover rationale.
- src/lib/indi_accel_control/IndiAccelControlTest.cpp: new test IndiAccelBlendTest.ConvergesToLargeThrustGap04
  (plant u_meas = u_cmd - 0.4, valid telemetry, tb 1 s, 1000 cycles; asserts b within 0.01 of 0.4, not frozen,
  collective = hover + 0.4, u_f = model).
- No other place states the 0.3 bound (msg/IndiPosStatus.msg, mc_indi_pos_control yaml/sources checked, no hit).
  indi_rate_control has its own kMaxBlend = 2, unrelated.
Command: indi_project/docker/run.sh -n kmb "make tests TESTFILTER=Indi"
Result at 0.5: 9/9 Indi* tests passed (unit-IndiAccelControl, IndiPosInjection, IndiStageMode, rate-side ones).
Result at 0.3: unit-IndiAccelControl FAILED, IndiAccelControlTest.cpp:849 (EXPECT_NEAR blend vs 0.4), also :851, :852.
Restored 0.5 and re-ran: pass.
Format: Tools/astyle/check_code_style.sh on both changed files in Docker, rc 0.
Unverified: SITL G5.10 altitude behaviour not run; mc_indi_pos_control has no blend-specific unit test, only
IndiPosInjection/IndiStageMode ran (passed).
