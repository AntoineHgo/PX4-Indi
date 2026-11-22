# G7(b) helper survivor tests (S195)

Tests added only to src/modules/mc_indi_rate_control/IndiMeasuredTorqueTest.cpp and IndiTorqueStampTrackerTest.cpp. Production unchanged.
Method as SURVIVOR_TESTS.md: px4-indi-sim image (project docker run wrapper), `make tests TESTFILTER="'...'"` into build/px4_sitl_test, mutation applied by script, `git checkout --` of the prod file right after each run.
Note: build/px4_sitl_test did not exist at start; it was reconfigured from scratch (first ninja run stopped on a generated-header ordering failure, the rerun completed). px4_sitl_default untouched.

| id | test | derivation | HEAD | under mutation |
|---|---|---|---|---|
| H16 | IndiMeasuredTorqueTest.NegativeRotorSpeedIsInvalid | header: u_valid = finite, non negative, plausible. rpm = -rpmFromThrust(0.25) gives ratio -0.5 (plausible magnitude, squared would be a usable 0.25); motor 1 must drop out: result.valid false, motor_valid_mask 0x0D (0x0F minus bit 1) | pass | FAILED (only this test) |
| H19 | IndiMeasuredTorqueTest.DroppedFrameKeepsPreviousSampleValueAndTime | header: on error_count increment the previous sample and its time are kept. All motors 0.25 at t0, motor 0 then reports rpm of u=1 with error_count 1 at t0+15000: torque bit identical to before, timestamp_sample == t0, and compute(t0+SAMPLE_MAX_AGE_US+1) invalid (kept sample ages out). The existing test missed it because all motors shared one timestamp and the torque was not checked | pass | FAILED (only this test), `dropped` forced to false |
| H26 | IndiTorqueStampTrackerTest.ZeroTimestampIsForeign | a fresh tracker has an all-zero ring; a zero timestamp is not one of the module's own: checkReceived(0) true, foreignDetected true | pass | FAILED (only this test) |
| H27 | IndiTorqueStampTrackerTest.FlagStaysUntilClearCountOwnMessages | header: cleared after CLEAR_COUNT consecutive own messages: flag still set after each of CLEAR_COUNT-1 own messages, cleared on the CLEAR_COUNT-th | pass | FAILED (only this test), `>= CLEAR_COUNT` -> `>= 1` |

Intent was clear from the headers for all four.

Final checks
- Full filter 'Indi|indi_rate_control|FailsafeSetpoint|SetpointExtrapolation|EkfResetDetect': 13/13 ctest targets pass (after all mutations reverted, rebuilt).
- astyle dry-run (`Tools/astyle/fix_code_style.sh --dry-run --formatted` on the two test files): no output (clean).
- No containers left running.

`git status --short -- src`:
```
 M src/modules/mc_indi_rate_control/IndiMeasuredTorqueTest.cpp
 M src/modules/mc_indi_rate_control/IndiTorqueStampTrackerTest.cpp
```
