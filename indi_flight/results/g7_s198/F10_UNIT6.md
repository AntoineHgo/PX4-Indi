# F-10 unit 6: indi_rate_control_test.cpp (comments and names only)

Working tree, not committed.

## Hits
Before: 14 (D-S3-LANDED x5, D-S3-ATT-STEP, D-RATE-LEAD, G7(b) M7/M19/M20/M21, S77 x3 incl. "lesson 9"). After: 0 (grep for D-*, G7, S77, lesson, decision, stage; licence text excluded). Also reworded "stages" -> "filters", "freeze/frozen" -> "hold/held", "(header, ...)" pointers removed.

## Renames (old -> new)
| old | new |
|---|---|
| IndiRateControlBlendTest.MaybeLandedFreezesBlend | IndiRateControlBlendTest.MaybeLandedHoldsBlend |
| local `frozen` (controller in that test) | `held` |
All other test names already state the behaviour and were kept (including suite IndiRateControlYawInvTest and EffectiveGainKIdentStatus, which name a public function / inversion form, not an id).
Removed comment content: ids and "lesson 9" only; no derivation lost (the Tb/(Tb+dt) closed form comment is kept).

## Checks
(i) gcc -fpreprocessed -dD -E -P token compare of HEAD vs new with the rename applied to HEAD: identical (rename done forward because HEAD already has an unrelated local `held` in another test). PASS.
(ii) `ninja -C build/px4_sitl_test unit-indi_rate_control_test` and run: 75 tests from 8 suites PASSED (log f10_u6_test.log); 75 TEST/TEST_F in HEAD and in the new file; unit 5 run on the HEAD test file also gave 75 (f10_u5_test.log). PASS.
(iii) names above.
(iv) make format (no further diff) and PX4_ASTYLE_FIX=0 check_code_style.sh on the file rc=0 (f10_u6_format.log). PASS.

## For the report
No derivation removed.
