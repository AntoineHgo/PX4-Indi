# T203 review: commit dff2b7a805 (hoist want_indi before _control.update)

File: src/modules/mc_indi_pos_control/McIndiPosControl.cpp

## (1) Inputs of the moved want_indi expression: OK
- flying_but_ground_contact: const local, defined once at line 727 (after updateTakeoffState at 721). Snapshot, not re-read; unchanged.
- _takeoff state: written only in TakeoffHandling::updateTakeoffState (src/modules/mc_pos_control/Takeoff/Takeoff.cpp lines 56-108). updateRamp (Takeoff.cpp:112, called at line 794) only reads _takeoff_state. Later updateTakeoffState call (line 886) is after the new position. Value at 820 equals the value at the old position.
- _vehicle_control_mode: not assigned between 700 and 880 (only read; assigned near the top of Run, line ~616 region).
- Nothing between the old and new positions (old position was after _control.update) writes any of these: the intervening calls are _control.setState, _control.update, the fallback/failsafe path, getLocalPositionSetpoint, getAttitudeSetpoint.

## (2) Integrator zeroing: OK
- Pre-update: `if (want_indi) _control.resetIntegral();` at lines 828-830, before `_control.setState` and `_control.update(dt)`. When want_indi is false this block does nothing.
- Caveat (not a defect of this commit): the pre-existing `if (not_taken_off || flying_but_ground_contact) resetIntegral()` at lines 741-747 still zeroes the integrator in the bypass states, so "not zeroed when false" holds only for the want_indi block itself.
- Post-update: `if (_indi_active) _control.resetIntegral();` at lines 870-872 still exists.

## (3) Post-update reset present: OK (lines 870-872)

## (4) Other uses of want_indi: OK
- Single declaration (line 820); old declaration removed, no duplicate. No earlier use in Run().
- Only other use: runIndiStage(..., want_indi, ...) at line 867.

## Finding (design risk, medium): comment A2 overstates the bypass case
want_indi being true does not mean the INDI stage runs. In runIndiStage (lines 186-188) `can_run` also needs fresh_att, fresh_acc, finite accel, rate > 5 and `_indi.update()` must succeed; otherwise it takes the bypass path (line 279 sets `_indi_active = false`).
- Pre-update zero (828) fires on want_indi, and post-update zero (870) fires only on _indi_active. So when want_indi is true but the stage is bypassed (stale/invalid inputs, low rate, lib update failure), the stock integrator is zeroed every cycle and never accumulates. The stock path (attitude setpoint from the stock controller) then runs with no I term.
- The old code gated on previous-cycle _indi_active, so this case kept the integrator running.
- The commit message says "zero the integrator whenever INDI is requested", so this may be intentional, but the comment at lines 826-827 ("In bypass ... keeps running") is not true for this sub-case. Either correct the comment or gate the pre-update zero on the stage actually running.
- Suggested check: confirm that the stock I term is wanted when INDI is requested but the stage bypasses; otherwise gate on the actual result.

## Verdict
No defect in the stated fix (first active cycle after a bypass no longer carries the stock integral). Open point: the want_indi-but-bypassed sub-case (design risk above).
