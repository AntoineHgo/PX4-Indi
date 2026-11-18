# S77 blend tests
Plan: add 3 blend tests (telemetry recovery, landed->airborne, weak-motor closed loop), break-check each.

## Tests added (indi_rate_control_test.cpp, 66 -> 69 tests, all pass)
1. IndiRateControlBlendTest.TelemetryRecoveryWithSteadyGapHasNoStep: tb=1, meas = 0.8 x model (0.4 vs 0.5), 10 s converge, 200 invalid cycles, then valid again (kMeasValidCycles warm-up included). Max one-cycle change of t_f and of (t_f_meas + blend) < 1e-3 normalised (a failed snap shows ~0.1); t_f back within 2e-3 of the converged value.
2. IndiRateControlBlendTest.LandedToAirborneWithSteadyGapHasNoBlendStep: landed 1200 cycles, blend == tracked gap (1e-6); 400 airborne cycles keep blend within 1e-3 of the gap and t_f_meas + blend within 1e-3 of the model torque.
3. IndiRateControlBlendClosedLoopTest.WeakMotorStandingErrorRemovedByBlend: own plant (actuator tau 0.04 vs controller 0.02, true torque = 0.8 x actuator state, measurement = true torque, constant -20 rad/s2 disturbance, zero rate sp, 10 s). tb=1: |mean rate over last 1 s| < 0.01 (measured 1.6e-5). tb=0: > 0.1 (measured -0.25, matches the analytic 0.2 u G1 / K = 0.25). Lesson 9 reproduced, no STOP condition.

## Break checks (indi_rate_control.cpp restored with git checkout; git diff --stat on it is empty)
- A: inactive branch `_blend = t_gap;` removed (blend frozen). Tests 1 and 2 FAIL (test.cpp:1323 and :1345 Failure). Existing LandedBlendTracksWithoutAccumulating also fails (line 1248).
- B: `t_f = t_f_meas;` (blend term zero). Test 3 FAILS (test.cpp:1427; output "weak motor rate error: tb=1 -0.25, tb=0 -0.25").

## Unverified
- Tests 1/2 are open loop on a constant allocated torque; closed-loop recovery transients are not covered.
- `make format` passed after the edit; the suite was not rebuilt after it (format changed nothing in git diff beyond the test file).
- run.sh here builds and runs the tests in Docker (filter as $1).
