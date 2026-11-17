# T118 second-key review: D-S3-LANDED and D-S3-FROZEN vs commit 65356c4250 (S58)

Verdict: AGREE-WITH-ISSUES (one minor deviation in frozen detection at arm, see item 3b).

1. maybe_landed (MATCH): the only use in update() is the blend integrator guard,
   indi_rate_control.cpp:327 (`if (!maybe_landed)`). The law, lead, yaw state and the ramp do not read it.
   The ramp (lines 379-401) keys on `landed` only. No slew in flight: `_landed_ramp` is only set on a
   `landed` edge (line 384), so with maybe_landed alone t_fb = t_f unchanged.
2. Ramp (MATCH): both edges via `landed != _landed_prev` (line 384). Slew = `_landed_slew * dt` (line 391).
   Ramp ends when target reached (line 400). Default 5.f in header (indi_rate_control.hpp:304).
3. Frozen (MATCH with one deviation):
   a. Armed and window and cmd variation: IndiMeasuredTorque.cpp evaluateWindow (~line 130-150) requires
      !_armed -> return, window >= _frozen_window_us, cmd_in_window and (cmd_max-cmd_min) > 0.02. OK.
   b. ISSUE (minor, deviates from "same window"): setArmed() calls restartWindow(sample, 0), so window_start
      is 0 and the rpm window is not anchored to arming, while cmd_min/max accumulate from the arm instant.
      Consequence: a motor whose rpm was bit-identical before arming (e.g. stopped, reporting 0) can latch
      frozen on the first command variation after arm, before the ESC telemetry has had time to change.
      Latch clears on the next rpm change, so this is a transient offline of the measured path, not a
      permanent one. Fix: pass the timestamp into setArmed and restart the window at arm time.
   c. Frozen motor -> valid = false: compute() sets fresh=false for frozen motors and valid=false in the
      else branch (IndiMeasuredTorque.cpp compute, ~line 215-245). MATCH.
   d. Recovery: setMotorSample restartWindow on any bit-level rpm change clears `frozen` (~line 190). MATCH.
   e. Mask logged: motor_frozen_mask set in compute (motors 0..7), published (McIndiRateControl.cpp ~193),
      defined in msg/ActuatorTorqueMeasured.msg:11. MATCH.
4. Params (MATCH): MC_INDI_LND_SLEW default 5.0 min 0.5 max 100 (mc_indi_rate_control_params.yaml, new block
   after the MC_INDI_* hunk at ~line 174). MC_INDI_ERPM_FRZ default 0.5 unit s min 0.1 max 5 (~line 187).
   Defaults in code: _frozen_window_us{500000} (IndiMeasuredTorque.hpp:165), _landed_slew{5.f}.
   Non-positive/non-finite slew ignored in setLandedSlew (indi_rate_control.hpp:211-216).
5. Resets (ISSUE minor, no ramp/latch carry-over found):
   - resetStates() (indi_rate_control.cpp:177-178) clears _t_fb_prev and _landed_ramp. Called from reset() on
     disarm (McIndiRateControl.cpp:339 `_indi.reset()` when !flag_armed). No ramp survives disarm.
   - _landed_prev is NOT reset (hpp:306). After disarm it keeps the last landed value. On the next arm, if
     landed differs, that is a real edge and the ramp is correct; no latent error, but it is undocumented.
   - Frozen latch: cleared by setArmed on arm/disarm change (IndiMeasuredTorque.cpp setArmed) and by rpm change.
     compute() also masks with `_armed`. No carry-over into the next flight beyond item 3b.
   - Not verified: whether parameters_updated() runs before the first update() (it is called in the ctor at
     McIndiRateControl.cpp:58, so setLandedSlew is applied at init; NOT-COVERED for runtime param changes beyond that).

Test coverage (NOT-COVERED): no unit test for the ramp or frozen detection was in the commit diff.

## Orchestrator disposition (S58)
- Issue 3 (arming edge): not reachable. After setArmed() the window restarts with cmd_in_window false; the first
  command (or rpm sample) evaluates zero spread and restarts the window at its own time. Checked by guard+break run
  (`design/t117_s3_items_s58.md`), test ArmingEdgeStartsANewWindow kept. No change.
- Issue 4: accepted as is (edge on next arm is the wanted take-off ramp).
- Item 5: wrong scope, the brief listed 4 files; the commit holds 3 landed tests and 5 frozen tests, break-checked.
