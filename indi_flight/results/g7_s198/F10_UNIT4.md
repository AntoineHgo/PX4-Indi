# F-10 unit 4: IndiAccelControlTest.cpp (comments and names only)

Working tree, not committed.

## Hits
Before: 17. After: 0 (grep for D-*, A18, A14, G7, S96, T20x, stage, freeze, A-9, M1; licence text excluded). Also reworded "stage" to control loop/controller, "freeze" to hold.

## Renames (old -> new)
| old | new |
|---|---|
| IndiAccelBlendTest.FrozenAtBypassA3A8 | FrozenAtBypass |
| IndiAccelBlendTest.FrozenAtE7EdgeSingleCycle | FrozenAtHoldReleaseSingleCycle |
| IndiAccelControlTest.A18CircleAnalyticBodyRates | JerkCircleAnalyticBodyRates |
| IndiAccelControlTest.A18StepThenHoldGivesZeroJerk | JerkStepThenHoldGivesZero |
| IndiAccelControlTest.A18FeedbackOnlyChangeGivesNoJerk | JerkFeedbackOnlyChangeGivesNone |
| IndiAccelControlTest.A18ResetMidRampGivesNoPulse | JerkResetMidRampGivesNoPulse |
| local kStageHz | kLoopHz |
Other Frozen* tests kept: they name the public blend_frozen output.
Removed comment line: "T206: coverage added after the T205 second-key review ..." (bookkeeping only).

## Checks
(i) gcc -fpreprocessed -dD -E -P token compare of the original vs the new file with reverse rename: identical (4721 tokens). PASS.
(ii) indi_project/docker/run.sh 'ninja -C build/px4_sitl_test unit-IndiAccelControl && build/px4_sitl_test/unit-IndiAccelControl': 61 tests from 3 suites PASSED; 61 TEST/TEST_F in the file, unchanged. Log f10_u4_test.log. PASS.
(iii) names above.
(iv) make format (no further diff) and PX4_ASTYLE_FIX=0 Tools/astyle/check_code_style.sh on the file rc=0. PASS.

## For the report
No derivation removed. Baseline binary not re-run separately (count compared with the file's TEST count and the 61 expected).
