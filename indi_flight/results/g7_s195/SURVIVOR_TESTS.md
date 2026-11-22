# G7(b) survivor tests (S195)

Scope: the five library survivors of BREAK_AUDIT.md section 3. Tests added only to
src/lib/indi_rate_control/indi_rate_control_test.cpp and src/lib/indi_accel_control/IndiAccelControlTest.cpp.
Production .cpp/.hpp unchanged. Build/run: px4-indi-sim image, `make tests TESTFILTER=...` into build/px4_sitl_test
(px4_sitl_default untouched), mutations applied with the audit's mut.sh then `git checkout --` right after each run.

| id | test | expected-value derivation | pass on HEAD | under mutation |
|---|---|---|---|---|
| M7 R:339 | IndiRateControlBlendTest.BlendFollowsFirstOrderStepResponse | once the gap is constant, distance to it decays as d_N = d_0 (Tb/(Tb+dt))^N (closed form of the backward Euler first order step), 1% tolerance, Tb=0.1 s | pass | FAILED (only this test) with alpha = dt/(Tb+2dt) |
| M19 R:338 | IndiRateControlBlendTest.MaybeLandedFreezesBlend | header: maybe_landed freezes the blend integrator, so the blend is bit identical over 100 maybe_landed cycles while the gap still moves it (a free running twin moves it by >0.01, so the freeze is not trivially true) | pass | FAILED (only this test) with `if (!maybe_landed)` -> `if (true)` |
| M20 R:352 | IndiRateControlBlendTest.BlendIsBoundedByMaxBlend | kMaxBlend = 2 (both torques within [-1,1]): model +1 vs measurement stepped to -1 with 180 Hz cutoffs overshoots the filtered gap above 2 (asserted, EXPECT_GT), blend with Tb=1e-4 s follows it, must stay <= 2 | pass | FAILED (only this test) with clamp +-1e9 |
| M21 R:268 | IndiRateControlBlendTest.AllocatedTorqueIsBoundedBeforeActuatorModel | allocated torque (5, -5, 100 and sign flip) must give a modelled torque bit identical to the run fed the bound (+-1) every cycle, and <= 1.1 | pass | FAILED (only this test) with clamp +-100 |
| A14 A:309 | IndiAccelControlTest.DtOutsideValidRangeReturnsFalseAndLeavesOutputUntouched | header range [kMinDt, kMaxDt]: dt = 1.1 kMaxDt, 10 kMaxDt, 0.9 kMinDt return false with output untouched; dt = kMinDt and kMaxDt accepted | pass | FAILED (only this test, 3 expectations at the dt > kMaxDt cases) with `in.dt > kMaxDt` removed |

Notes
- M20: the clamp can only bind through filter overshoot of t_f_model - t_f_meas (inputs are clamped to +-1, so the raw gap is at most 2). With the default-like 100 Hz cutoffs there is no overshoot (gap max 2.0 exactly, test with 100 failed its own EXPECT_GT precondition), so the test uses 180/180 Hz. The clamp is effectively a defence net; the test pins the documented bound, not a physical operating point. kMaxBlend is private, the test mirrors it as a local 2.f (a header change of that constant would need the test updated).
- Intent was clear from the header/comments for all five; none required guessing.
- Test-file debug printf used during M20 development was removed.

Final checks
- Full filter 'Indi|indi_rate_control|FailsafeSetpoint|SetpointExtrapolation|EkfResetDetect': 13/13 ctest targets passed.
- astyle (`Tools/astyle/fix_code_style.sh --dry-run --formatted`): rate test clean; accel test was reported, fixed with fix_code_style.sh (one spacing change in my new code, `10.f *IndiAccelControl::kMaxDt`), dry-run re-check clean.
- `git diff --stat -- src/lib/*/indi_*control.cpp src/lib/*/indi_*control.hpp`: empty.
- `git status --short -- src`: ` M src/lib/indi_accel_control/IndiAccelControlTest.cpp`, ` M src/lib/indi_rate_control/indi_rate_control_test.cpp`.
- No containers left running.
