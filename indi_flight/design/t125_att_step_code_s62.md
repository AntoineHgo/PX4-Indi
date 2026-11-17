# T125 attitude-step rate-setpoint lead, code (S62)
Goal: D-S3-ATT-STEP: numerator = nu - (1+c) a_f + c r_dot_f (yaw g2 term unchanged), same per-axis c as the feedback lead
(0 landed, bound kMaxLeadGain). No new parameter, MC_INDI_LEAD = 0 turns both off. Not committed.

## Files changed
- src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}: r_dot_f (first order LP, kSetpointLeadTc 0.01 s, actual dt; clamp
  kMaxRateSpDot 1000 rad/s^2 as impulse guard), resetSetpointLead(), getRateSpDot(), header law comment. Zero/re-seed on
  first update, reset(), landed (prev re-seeded each cycle), resetSetpointLead(), faultOutput (invalid dt/inputs/params, non-finite dt_cmd).
  Non-finite rate_sp verified rejected in update() step 1 before any state use.
- Yaw: when the yaw filter is active, an extra LowPassFilter2p `_yaw_sp_lpf` (same design, redesigned/reset with
  the others, reset to rate_sp(2) at the same point as `_yaw_error_lpf`) filters the setpoint and that copy is differentiated, so
  the lead matches the filtered yaw error.
- msg/IndiRateStatus.msg: `float32[3] rate_sp_dot` (unversioned; messages.instructions.md: no versioning unless needed).
- src/modules/mc_indi_rate_control/McIndiRateControl.{cpp,hpp}: publishes rate_sp_dot; bitmask of flag_control_attitude/rates/
  manual/offboard + watchdog `wd.stale` (timeout and recovery); any change calls `_indi.resetSetpointLead()` (member `_sp_source_prev`, init 0xff so first cycle resets).
- src/lib/indi_rate_control/indi_rate_control_test.cpp: IndiRateControlSetpointLeadTest x4.

## Tests
a. AttitudeStepOvershootBounded: tau 0.033, G1 matched, K 20, ACT_TC 0.05, lead 1, P 8, dt 1/800, 8-sample delay on measured
   rate and accel, 0.35 rad step. Overshoot WITH setpoint term 0.51 % (pass, <= 5 %); WITHOUT (term removed temporarily,
   restored) 11.13 % -> test FAILS as required (spec guessed 13-16 %; this plant gives 11.1 %).
b. NoImpulseFromSetpointStepOrReset (5 rad/s step within bound, 500 rad/s step clamps to exactly -1000, zero after
   construction/resetSetpointLead/reset/fault) and LandedHoldsZeroAndTakeoffStartsAtZero. Break-check: removing the `landed ||`
   branch makes the landed test fail (5 failures).
c. LeadZeroIsPreviousLawOnRandomInput: lead 0 vs controller with r_dot forced 0 every cycle, 1000 random cycles, 1e-6 (passes);
   existing LeadZeroIsBitIdentical also still passes.

## Build results
- make tests TESTFILTER=[iI]ndi: rc 0, 6/6 indi targets pass (indi_rate_control_test includes the new tests).
- make px4_sitl_default: rc 0, bin/px4 linked.
- make format: rc 0; git status shows only the files above (STATE.md was already modified before this task).

## Deviations / unverified
- Overshoot without the term 11.1 % vs the 13-16 % expected; with it 0.5 % (model 0.6 %).
- Flight/SITL behaviour, noise of r_dot_f in acro, yaw G2_Y interaction and attitude-break margin are not tested here.
- During a mode-flag change the derivative restarts at 0 for one cycle only (the filter state, not a ramp).
