
## Minor fixes (round 2)
- McIndiRateControl.hpp updateArmingCheck comment and McIndiRateControl.cpp geometry-fallback comment now describe the new refusal.
- IndiErpmArmingCheck.hpp: `not_configured` comment shortened to one line.
- IndiErpmArmingCheckTest.cpp test 6: asserts motor_mask == 0 on both not-configured paths.
- Docker unit run (unit_final.log): 16/16 passed, functional-IndiErpmArmingCheck passed (5 tests). Format (format_check.log): rc=0 for all 5 files; git diff --check clean.
