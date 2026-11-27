# P6A: tests for G7 (b) items 1-5 of G7B_TEST_INVENTORY.md

Docker only (indi_project/docker/run.sh, image px4-indi-sim, wall-clock timeouts), build dir build/px4_sitl_o11 (px4_sitl_default + CMAKE_TESTING; build/px4_sitl_default untouched). Scripts here: tests.sh, brk.sh, obj_build.sh, fmt.sh. Raw break logs: brk_<id>.txt, brk_all.txt.

## Commits
- b89a18b4aa refactor(mc_indi_rate_control): extract the ESC sample freshness check
- 3ab7c72046 test(indi_rate_control): add tests for the ESC freshness, frozen window, reset and rpm bounds

## Extraction neutrality (item 1)
IndiMeasuredTorque::isSampleFresh(now_us, timestamp_sample_us, timeout_s) in IndiMeasuredTorque.hpp, same expression as the inline one in McIndiRateControl.cpp.
- objdump -dr of McIndiRateControl.cpp.o (module build, px4_sitl_default flags), before vs after: 3305 lines each, identical except the first-line file name (obj/McIndiRateControl_{before,after}.dis, cmp after dropping the header: identical). The .o files differ only in debug info (line numbers); not kept.
- All 10 targets passed on the extraction commit alone (tests_extract.txt).

## Per item (break = one edit, test failed under it, passed after revert; "revert pass" = target re-run green)
| item | test(s) | file | break applied | fail seen | revert pass |
|---|---|---|---|---|---|
| 1 | IndiSampleFreshnessTest.BoundaryAtTimeout | mc_indi_rate_control/IndiMeasuredTorqueTest.cpp | `< timeout_s` -> `<= timeout_s` (i1a) | yes (also NoTimeoutMeansNeverFresh) | yes |
| 1 | IndiSampleFreshnessTest.SampleFromTheFutureIsNotFresh | same | drop `now_us >= timestamp_sample_us` (i1b) | yes | yes |
| 1 | IndiSampleFreshnessTest.NoTimeoutMeansNeverFresh | same | i1a | yes | yes |
| 2 | IndiAccelBlendTest.ResetWithLaggingMeanUStepsByTheGap | lib/indi_accel_control/IndiAccelControlTest.cpp | reset line 162 always `u_model - _blend_offset` (i2a) | yes, only this test (existing 62 pass) | yes |
| 2 | IndiAccelBlendTest.ResetWithoutMeanUHasNoCollectiveStep | same | line 162 `PX4_ISFINITE(mean_u)` -> `true` (i2b) | yes (also existing NoCollectiveStepAtBypassEdgeModuleConvention) | yes |
| 3 | IndiFrozenRpmTest.WindowFollowsSetFrozenWindowSeconds | IndiMeasuredTorqueTest.cpp | `* 1e6f` -> `* 5e5f` in setFrozenWindow (i3a) | yes | yes |
| 3 | IndiFrozenRpmTest.NegativeWindowDoesNotShortenTheDetection | same | clamp `: 0.f` -> `: 0.5f` (i3b) | yes | yes |
| 4 | IndiRateControlMeasurementTest.NormalisedThrustFromRpmZeroBoundary | lib/indi_rate_control/indi_rate_control_test.cpp | `rpm < 0.f` -> `rpm < -0.5f` (i4a) | yes, only this test (old -1 rpm case still passes it) | yes |
| 4 | same (tiny positive rpm = exact 1e-8) + existing NormalisedThrustFromRpm | same | constrain lower 0 -> 1e-6 (i4b) | yes (both) | yes |
| 5 | IndiFrozenRpmTest.SaturatedConstantCommandWithConstantRpmStaysValid | IndiMeasuredTorqueTest.cpp | frozen also when `cmd_max >= 0.99` (i5b) | yes | yes |
| 5 | IndiFrozenRpmTest.CommandDipFromSaturationWithConstantRpmIsFrozen | same | FROZEN_CMD_VARIATION 0.02 -> 0.05 (i5a) | yes | yes |

Item 4 equivalent mutant: removing the lower constrain clause (`math::min(ratio * ratio, 1.f)`, i4c) survives: ratio*ratio >= 0 for any finite ratio, so the clause is dead code, not a test gap. Only raising the floor is observable (killed, i4b).

## Notes for the report
- Item 5 pins a by-design limit: a motor whose command is constant (e.g. pinned at 1.0) with a constant rpm is never flagged frozen, so a permanently saturated motor with frozen telemetry goes undetected. Only a command variation above 0.02 inside the window enables the flag.
- Item 3 finding: window 0 (what a negative setFrozenWindow gives) disables the detection in practice (the window restarts on every command with no recorded variation), it does not mean "flag at once". The test pins "negative window never flags".
- Item 2: the reset path only shows with measurement delay > 0 (the delayed samples are the ones seeded by reset); with delay 0 line 162 has no effect on the first cycle. The test uses setMeasurementDelay(2).
- No bug found, no control behaviour changed. git diff of src/ after the break runs: only the intended test changes (committed).

## Test run (final, tests_final.txt)
SUMMARY 10/10 targets passed: IndiAccelControl 63, IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointWatchdog 6, IndiStageMode 15, IndiTorqueStampTracker 6, indi_rate_control_test 76, functional-IndiMeasuredTorque 18 (the 10th target, not in the 9 of README_P2, holds the frozen-rpm tests; before: 61/75/11).
Format: astyle dry-run on the 5 changed C/C++ files, checked=5 reported=0 (fmt.sh).
