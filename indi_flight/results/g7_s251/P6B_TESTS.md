# P6B: tests for G7 (b) inventory rows 7 and 8 (items 6-7)

Docker only (indi_project/docker/run.sh, image px4-indi-sim), build dir build/px4_sitl_o11; build/px4_sitl_default untouched. Scripts here: tests.sh, brk.sh, brk_all.sh, obj_build.sh, fmt.sh (copies of the S250 ones, obj_build.sh extended to the pos module). Raw logs: brk_all.txt, tests_final.txt, tests_extract_diff.txt, obj/*.dis.

## Commits
- 042e38a1dd refactor(mc_indi_pos_control): extract the ESC mean thrust and freshness check (also the rate setpoint source mask)
- 1ac5d58c89 test(mc_indi_pos_control): add tests for the ESC mean thrust, freshness and rate setpoint source

## Extraction neutrality
- IndiEscThrust::meanRotorThrust / isFresh (pos module, new header IndiEscThrust.hpp) and IndiRateSetpointSource::mask (rate module, IndiRateSetpointSource.hpp). IndiMeasuredTorque::isSampleFresh not reused: it is `< timeout_s` on a float, the pos rule is `<= 100 ms` with future = age 0.
- Rate module: objdump -dr of McIndiRateControl.cpp.o before vs after is identical except the file name line (obj/McIndiRateControl_{before,after}.dis).
- Pos module: NOT bit-identical. McIndiPosControl.cpp.o text differs in the inlined runIndiStage only by register allocation, stack slots (frame 0x4b8 -> 0x4c8 in one variant), branch inversion and scheduling; thunk sections are emitted in swapped order; 6920 vs 6923 instructions; the relocation lists (calls, constants) are identical. Several source shapes tried (out-param, struct return, with/without helper freshness): none gave identical text, the helper moves compiler decisions.
- Neutrality shown instead by a differential test (temporary, not committed, run in tests_extract_diff.txt): 2,000,000 random esc_status (count 0-13, random online flags, random functions, rpm -500..16500, rotor_w_max in {-100,0,100,700..1700}) comparing the helper with a verbatim copy of the pre-extraction inline code: valid flag equal and mean bit-identical (memcmp) in all cases (338,887 valid), isFresh equal to `valid && age <= 100 ms` with the original age expression for random now/stamp. 12/12 targets green on that tree.
- The same source and compile flags otherwise: no change of any other function.

## Break table (one edit to the code under test, test failed, reverted, target green; logs brk_all.txt)
| item | test | file | break | fail seen | revert pass |
|---|---|---|---|---|---|
| row 7 mean | IndiEscThrustTest.FourMotorsGiveTheMeanOfTheSquaredRatios | mc_indi_pos_control/IndiEscThrust.hpp | `/ 4.f` -> `/ 3.f` (e1) | yes (+2 more) | yes 10/10 |
| row 7 3 of 4 | MissingMotorIsInvalid, DuplicateMotorDoesNotCompleteTheSet | same | `seen == 0xFu` -> `seen != 0` (e2) | yes, both | yes |
| row 7 offline | OfflineMotorIsInvalid | same | online test `&` -> `|` (e3) | yes | yes |
| row 7 rpm cap | RpmAboveOneAndAHalfTimesMaxIsRejectedBelowItIsClamped | lib/indi_rate_control/indi_rate_control.hpp | kMaxRpmRatio 1.5 -> 100 (e4) | yes | yes |
| row 7 age boundary | FreshnessBoundaryIsInclusive | IndiEscThrust.hpp | `<=` -> `<` (e5) | yes | yes |
| row 7 future | SampleFromTheFutureHasAgeZero | same | age without the now>stamp guard (e6) | yes | yes |
| row 7 other functions | EntriesOfOtherFunctionsAreIgnored | same | `motor < 0 ||` dropped (e7) | yes | yes |
| row 8 mask | IndiRateSetpointSourceTest.OmegaFeedForwardToggleChangesTheMask (+EachInput, InputsDoNotAlias) | mc_indi_rate_control/IndiRateSetpointSource.hpp | omega_ff term -> 0 (m1) | yes, all 3 | yes 3/3 |
| row 8 lead restart | IndiRateControlSetpointLeadTest.FeedForwardEnableStepNeedsTheLeadRestart | lib/indi_rate_control/indi_rate_control.hpp | resetSetpointLead() body emptied (l1) | yes (+2 existing) | yes 77/77 |
| row 8 pulse without reset | same test, no-reset branch | lib/indi_rate_control/indi_rate_control.cpp | lead reset condition `|| true` (l2) | yes (+4 existing) | yes |

Not mutated: `rotor_w_max > 0` guard (redundant: normalisedThrustFromRpm rejects rpm_max 0 anyway, the test NoRotorSpeedLimitIsInvalid still covers the outcome).

## Remaining GLUE
Instance 0 selection of esc_status (uORB subscription index), the call of resetSetpointLead on mask change in McIndiRateControl.cpp (`sp_source != _sp_source_prev`), and the pos-side omega_ff valid flag (:369, :1136) are glue, exercised only by SITL.

## All targets (tests_final.txt)
12/12 green: IndiAccelControl 63, IndiEscThrust 10 (new), IndiInjection 10, IndiInjectionStep 8, IndiPosInjection 12, IndiRateFeedforwardGate 6, IndiRateSetpointSource 3 (new), IndiRateSetpointWatchdog 6, IndiStageMode 15, IndiTorqueStampTracker 6, indi_rate_control_test 77 (+1), functional IndiMeasuredTorque 18. astyle clean on all changed files.
