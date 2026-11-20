# T208 A18 jerk feed-forward implementation log

## Files changed
- src/lib/indi_accel_control/indi_accel_control.{hpp,cpp}: new `Input::a_ff` (NaN axis = no jerk, history forgotten), jerk difference now on a_ff only, `kJerkHold = 0.1 s` (unchanged longer -> difference 0), members renamed `_a_ff_prev*`.
- src/lib/indi_accel_control/IndiAccelControlTest.cpp: JerkDifference tests moved to `in.a_ff`; 4 new A18 tests.
- src/modules/mc_indi_pos_control/McIndiPosControl.{hpp,cpp}: `setFeedforward(true)`; `_a_ff = _setpoint.acceleration`, `_j_ff = _setpoint.jerk` (NaN if not finite or all zero) set just before runIndiStage; passed as in.a_ff / in.j_ref; IndiRateFeedforward published after each attitude setpoint publish.
- msg/IndiRateFeedforward.msg (+ msg/CMakeLists.txt, next to IndiPosStatus).
- src/modules/logger/logged_topics.cpp: `add_optional_topic("indi_rate_feedforward")` (one line).
- src/modules/mc_indi_rate_control: IndiRateFeedforwardGate.{hpp,cpp} (in IndiSafety lib), IndiRateFeedforwardGateTest.cpp, CMakeLists.txt, McIndiRateControl.{hpp,cpp} (omega_ff roll/pitch added to `_rates_setpoint` at the injection-step call only, never stored in `_rates_setpoint`).
- Zero diff confirmed (git diff) on mc_rate_control, mc_att_control, mc_pos_control, control_allocator, control_allocation, commander.

## Reset edges (confirm reset() forgets jerk history: yes, reset() clears _a_ff_prev, valid flags, _j_diff and the filter)
1. `_indi_reset_pending` consumed at top of the can_run branch -> `_indi.reset()`. Set by: resetStageState(), and the EKF reset detector (`_indi_reset_detector`, line ~817).
2. Bypass branch: `_indi.reset()` every cycle (landed/ramp/not want_indi/not can_run); also clears pending.
3. Hold mode: library not updated, no reset, but omega_ff published invalid.
4. NOT covered by reset, accepted: a_ff step from failsafe/last_valid_setpoint substitution or takeoff-ramp `acceleration[2]=NaN` edit inside the INDI-active cycle (a NaN axis forgets history by itself; a substitution step gives one bounded pulse, clamp 3 rad/s). The a_ff is read from `_setpoint`, so the failsafe-generated setpoint (separate `_control.setInputSetpoint`) is not seen by the jerk difference (a_ff differs from what the controller used on those cycles). Unverified in flight.

## Tests and break checks (broken once, run, restored)
Library (IndiAccelControl): A18CircleAnalyticBodyRates (a), A18StepThenHoldGivesZeroJerk (b), A18FeedbackOnlyChangeGivesNoJerk (c), A18ResetMidRampGivesNoPulse (d).
- baseline pass. (a) flip sign of omega_ff pitch -> FAIL. (b) kJerkHold=1e9 -> FAIL. (c) difference on a_ref instead of a_ff -> FAIL. (d) delete the valid-flag clear in reset() -> FAIL.
Gate (IndiRateFeedforwardGate): valid, stale, landed, manual, watchdog cases. Breaks: drop `landed`, drop `acro_branch`, age check `|| true`, drop `!valid`, drop `watchdog_stale` -> each FAIL.
IndiRateSetpointWatchdog: pass.

## Build / format
- `make px4_sitl_default`: success (1688/1688, 0 errors).
- astyle: fixed 2 whitespace issues (indi_accel_control.cpp, McIndiRateControl.cpp) with fix_code_style.sh; not rebuilt afterwards (whitespace only).

## Unverified
- No SITL/flight run: omega_ff sign/frame in the real loop, G5.5 gain, uORB runtime behaviour (no module-level test of the pos-control publish or the rate-control consumption).
- `flying` as the "not ramp" criterion in the valid flag (plus model_force, landed) is by reading, not by test.
