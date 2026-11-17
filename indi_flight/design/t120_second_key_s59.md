# T120 second-key review (S59): code vs D-S3-SPTO and start-up/foreign-publisher exclusion

Verdict: AGREE-WITH-ISSUES

Scope: `git diff` of src/modules/mc_indi_rate_control/ and msg/IndiRateStatus.msg, new RateSetpointWatchdog.{hpp,cpp}, TorqueStampTracker.{hpp,cpp}, and their two gtest files. No source edited.

## Spec coverage

- (A) timeout, zero rates, hold thrust, flag, rate-limited warning, armed/acro gating, recovery on next message: implemented.
  - Off-by-one: `age > _timeout_us` (RateSetpointWatchdog.cpp:42). Exactly-timeout is not stale, matching "older than". Asserted by IndiRateSetpointWatchdogTest.cpp:49.
  - Thrust held: `_thrust_setpoint` is written only at McIndiRateControl.cpp:44 (acro) and :61 (new rates message). The watchdog only zeroes `_rates_setpoint` (McIndiRateControl.cpp:72-74). Correct by reading.
  - Gating: `armed && uses_setpoint` where `uses_setpoint = !acro_branch && flag_control_rates_enabled` (McIndiRateControl.cpp:66-69). Correct.
- (B) init refusal and run-time foreign flag with rate-limited error: implemented (McIndiRateControl.cpp:70-79, :315-322).

## Issues

1. Thrust-hold is not tested. No test in either gtest file, and no functional test, asserts that thrust is unchanged while stale. The hold is only verified by reading the code (McIndiRateControl.cpp:361-378). Reachable in flight: no, but it is an unverified spec point.
2. Init refusal uses the publish `timestamp`, not the sample time (McIndiRateControl.cpp:73). The spec says "sample". Interpretation issue, minor. Reachable: no.
3. Init refusal false positive: a stop/start of the module within 0.5 s of its own last publish is refused as "another controller" (McIndiRateControl.cpp:72-74). Reachable in flight only with a manual quick restart. Low.
4. Staleness uses the publisher's `vehicle_rates_setpoint.timestamp` (McIndiRateControl.cpp:357), not receipt time. A late-delivered message can look older than it is. Reachable only if a publisher stamps early. Low.
5. Never-received counts as stale while armed (RateSetpointWatchdog.cpp:42, `last_rx == 0`). The spec is silent here. Reachable in flight only when rates mode runs with no rates producer. Confirm this is intended.
6. Own-message false foreign: none found. Only one publish site (McIndiRateControl.cpp:116), and its timestamp is recorded at :120. The ring is checked on the latest message only, and the subscription is read every cycle, so the ring cannot overflow before a read. Init skips history (:79). Timestamp 0 is foreign by design (TorqueStampTracker.cpp:41) but the module never publishes 0. Not reachable.
7. Tests do assert spec values: boundary at timeout, fresh-clears, disarmed/acro inactive, rate-limit window, and foreign detection and clear-after-100. The rate-limit test accepts 2 to 3 warnings; 3 is the value the code gives.
