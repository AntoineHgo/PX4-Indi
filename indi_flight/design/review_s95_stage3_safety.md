# Review S95: stage-3 safety items, firmware vs specification

Verdict: NOT BLOCKING

Scope: `indi_flight/design/stage3_items_note.md` sec. 1-5 and `DECISIONS.md` D-S3-LANDED / D-S3-FROZEN, against
`src/modules/mc_indi_rate_control/` (M = McIndiRateControl.cpp, W = RateSetpointWatchdog.cpp, T = IndiMeasuredTorque.cpp),
`src/lib/indi_rate_control/indi_rate_control.cpp` (L) and `ROMFS/px4fmu_common/init.d/rc.mc_apps` (rc).
Control-law tuning, results and docs are out of scope. Nothing was built or run; this is a read-only review.
Line numbers are from the working tree at review time (branch feat/indi-flight, HEAD 772e5fe72e).

## Summary per item

| Item | Implemented as specified | Unit test that fails if broken |
|---|---|---|
| 1 Landed / maybe_landed | Yes (D-S3-LANDED) | `IndiRateControlLandedTest.MaybeLandedPulseNoStep`, `.TakeoffRamp`, `.TouchdownRamp`, plus `LeadOffWhenLanded`, `LandedBlendTracksWithoutAccumulating` |
| 2 Start-up exclusion | Yes (init refusal + run-time log, as the note proposes) | None for `init()` refusal (the note accepts this); run-time stamp check: `IndiTorqueStampTrackerTest` (assertions not read) |
| 3 Rate setpoint timeout | Partly: rates zeroed; thrust held with no decay; default 0.5 s, not 0.2 s (see F3) | `IndiRateSetpointWatchdogTest.*` (6 tests) |
| 4 Frozen rpm | Yes (D-S3-FROZEN) | `IndiFrozenRpmTest.FrozenRpmFallsBack`, `.ConstantRpmConstantCommandStaysValid`, `.NoisyRpmVaryingCommandValid`, `.FrozenRecovers`, `.ArmingEdgeStartsANewWindow` |
| 5 Autotune start | NO, rc is unchanged (see F1) | None |

## Findings

### F1. MAJOR: autotune still starts with INDI (item 5 not implemented)
- File: `ROMFS/px4fmu_common/init.d/rc.mc_apps:31-34`. `git diff main...HEAD` touches only the rate-controller and
  position-controller blocks.
- Spec (note sec. 5c): do not start `mc_autotune_attitude_control` when `MC_INDI_EN == 1`, and echo
  "autotune disabled with INDI". Also add a once-only INDI warning when `MC_AT_EN > 0`.
- Code: `if param greater -s MC_AT_EN 0 then mc_autotune_attitude_control start fi`, with no `MC_INDI_EN` check.
  There is no `MC_AT_EN` reference in the module (grep, no match).
- Failure scenario: with `MC_INDI_EN=1 MC_AT_EN=1`, the pilot sends DO_AUTOTUNE_ENABLE. The autotune injects
  excitation through the attitude loop into the INDI rate loop, whose gains are not validated for that excitation.
  It then fits and saves `MC_*RATE_*` PID gains for a controller that is not running. Those gains become active
  the next time `MC_INDI_EN` is set to 0. This does not invalidate existing evidence, since the autotune runs only
  on a command.
- Fix: in rc, nest the autotune start under `if param compare -s MC_INDI_EN 1 then echo ... else ... fi`. Add the SITL
  rc test from note sec. 5e.
- UNVERIFIED: whether a later decision deferred item 5. Only the two DECISIONS sections in scope were read.

### F2. MINOR: the rate-setpoint watchdog trusts the publisher's timestamp instead of the receipt time
- File: `McIndiRateControl.cpp:~372` (`_last_rates_sp_time = vehicle_rates_setpoint.timestamp`), `RateSetpointWatchdog.cpp`
  (`age = now > last_rx ? now - last_rx : 0`, `stale = last_rx == 0 || age > timeout`).
- Spec (note 3c): "`vehicle_rates_setpoint.timestamp` at receipt". The code matches the letter of the note.
- Failure scenarios:
  - (a) A publisher that stamps the message ahead of hrt (an external or bridged source with a clock offset) gives
    `age = 0` until hrt reaches that stamp. The watchdog cannot fire in that period, and the last rate is held,
    which is the defect the item fixes.
  - (b) A publisher that leaves `timestamp = 0` makes the setpoint permanently stale while armed. Rates are zeroed
    on every cycle and the vehicle cannot be steered in that mode.
  - The watchdog does not fire on the first sample of a normal publisher. On a never-received setpoint it fires by
    design (`NeverReceivedWhileArmedIsStale`).
- Fix: store `hrt_absolute_time()` at `_vehicle_rates_setpoint_sub.update()` as the receipt time. Keep the message
  stamp only for logging. Add a test with a future-stamped and a zero-stamped message.

### F3. MINOR: timeout thrust handling and default differ from the note
- Files: `McIndiRateControl.cpp:~375-400` (comment "zero rates, thrust held"), yaml `MC_INDI_SP_TO`
  (default 0.5, min 0.05, max 2).
- Spec (note 3c): default 0.2 s. Thrust is held for one more `SP_TO`, then decays at 0.5/s.
- Code: thrust is held indefinitely. Rates are zeroed. A rate-limited warning is issued. The default is 0.5 s.
- Failure scenario: the attitude controller dies in a climb. The held climb thrust with zero rates gives a level
  fly-away in altitude until a commander failsafe. Whether a commander failsafe triggers is UNVERIFIED (note).
- Fix: none if D-S3-SPTO ("coded later") chose a hold. It was out of the reading scope, so this is UNVERIFIED.
  Otherwise, implement the decay or update the note.
- Related, UNVERIFIED: in an offboard body-rate mode, a sender running slower than 2 Hz is allowed by
  COM_OF_LOSS_T but would make the rates toggle to zero between messages. The note itself flags the threshold as
  unverified against the slowest publisher.

### F4. MINOR: frozen detection, residual gaps (within D-S3-FROZEN)
- File: `IndiMeasuredTorque.cpp:~115-195`.
- Implemented as decided:
  - A bit-identical rpm for `MC_INDI_ERPM_FRZ` while armed AND command (max-min) > 0.02 gives frozen. A frozen motor
    is treated as offline, and the mask is logged.
  - A constant command restarts the window, so a hover with a constant rpm cannot trip
    (`ConstantRpmConstantCommandStaysValid`).
  - The arming edge restarts the window. Any rpm change clears the latch.
- Not detected, by design of the decision:
  - (a) A frozen value during a steady hover (command variation < 0.02).
  - (b) A stuck driver that alternates between two stale frames. The bit-identical compare restarts the window on
    each toggle.
  - (c) After one spurious new value the latch clears, and a new full window (0.5 s plus up to one more window,
    because a restart happens on evaluation) is needed before the motor is flagged again.
- Timestamps mix two time bases: the command time is `hrt_absolute_time()` at receipt (`M:~176`), the window start
  is `esc.timestamp`. Both are hrt, and `now < window_start` is guarded, so there is no wrap or underflow.
  `setFrozenWindow(<=0)` disables the detection without a failure, and the yaml minimum is 0.1.
- Fix (optional): count the repeats of the last N distinct values instead of an exact compare, or document (a) and
  (b) as accepted limits in D-S3-FROZEN.

### F5. MINOR: start-up exclusion is one-directional and has no fallback (item 2)
- Files: `McIndiRateControl.cpp:68-87` (init refuses if `vehicle_torque_setpoint` instance 0 is advertised and
  younger than 500 ms), `M:~330-337` (run-time foreign-stamp log, every 2 s at most), rc diff (if/else on `MC_INDI_EN`).
- Spec: as the note proposes (refuse at init, log at run time, keep rc if/else). The code matches.
- Residual gaps, both accepted by the note:
  - `mc_rate_control start` typed after INDI still gives two publishers. The run-time part only logs.
  - If INDI `init()` fails (for example callback registration), rc starts no rate controller at all. This follows
    the owner's no-PID-fallback rule. Whether commander then blocks arming is UNVERIFIED.
- Only instance 0 is checked. A VTOL or second-instance publisher is not detected (UNVERIFIED relevance).
- Test: no unit or SITL test of the init refusal was found (note 2e proposes a SITL shell test).

### F6. Item 1 checks that passed (no finding)
- `maybe_landed` alone freezes only the blend integrator (`L:336-341`). t_fb, lead, yaw filters and `_yaw_inc_prev`
  depend on `landed` only (`L:359-361, 394, 416, 452, 457, 477`). The decision does not ask for a slew in flight on
  `maybe_landed`, and none is applied, so a false `maybe_landed` in flight does not zero the trim.
  `MaybeLandedPulseNoStep` compares the output with and without the pulse at 1e-6.
- On both edges of `landed`, t_fb ramps at `MC_INDI_LND_SLEW` (`L:416-440`).
  - Parameter guard: `setLandedSlew` ignores values <= 0 and NaN. The yaml minimum is 0.5, so the ramp cannot stall
    at 0.
  - `_landed_prev` is not reset in `resetStates()`, so the edge survives a reset. While disarmed, `reset()` runs each
    cycle with landed=true, and `_t_fb_prev` is 0, so the takeoff edge ramps from 0.
- By decision, the lead gain and the yaw filters still step at the takeoff edge. Only t_fb is ramped.
- dt is bounded in the module (`constrain 0.125 ms..20 ms`) and validated in the lib (`kMinDt/kMaxDt`, finite).
  The first sample (`_last_run = 0`) is clamped to 20 ms. There is no division by a zero dt.
- NaN: the lib rejects non-finite inputs and holds the last command (`faultOutput`). The module replaces a
  non-finite published torque by 0. `_thrust_setpoint` from `vehicle_rates_setpoint.thrust_body` is not
  finite-checked, which matches stock mc_rate_control and is out of scope.

## UNVERIFIED
- Whether item 5 or the item-3 thrust decay was deferred or changed by decisions outside D-S3-LANDED / D-S3-FROZEN.
- The assertions of `IndiTorqueStampTrackerTest` and of the watchdog tests were not read; only the test names were.
- Whether commander blocks arming when no rate controller is running (F5).
- Whether offboard or uXRCE publishers stamp `vehicle_rates_setpoint` in hrt (F2, F3).
- Whether `_rate_sp_stale` and `motor_frozen_mask` reach the log (the field exists in the code, the logger topic list
  was not checked).
