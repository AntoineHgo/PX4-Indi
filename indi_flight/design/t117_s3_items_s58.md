# T117 stage-3 items 1 and 4 (S58)

## Plan
- Item 1 (D-S3-LANDED): `IndiRateControl::update(..., landed, maybe_landed=false)`. maybe_landed alone freezes only the
  blend integrator (value held; no slew, lead and yaw state untouched). landed keeps the old zeroing (t_fb 0, lead 0,
  yaw reset) but t_fb is ramped per axis with `MC_INDI_LND_SLEW` (default 5, min 0.5, max 100) on both edges of landed
  (ramp flag set on an edge, cleared once the target is reached; in flight there is no slew).
- Item 4 (D-S3-FROZEN): per motor window in `IndiMeasuredTorque`. rpm bit-identical (memcmp) for `MC_INDI_ERPM_FRZ` while
  armed and cmd max-min > 0.02 in that window => latched frozen, motor treated as not fresh (vector invalid, modelled
  fallback, existing hysteresis). An rpm change restarts the window and clears the latch (valid in the same sample).
  A window with constant command restarts (never trips). Disarmed: no detection, latch cleared.

## Files touched
- src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}, indi_rate_control_test.cpp
- src/modules/mc_indi_rate_control/McIndiRateControl.{hpp,cpp}: passes `_landed`, `_maybe_landed` separately; subscribes
  actuator_motors (per motor command into the model); setArmed, setFrozenWindow; publishes frozen mask
- src/modules/mc_indi_rate_control/IndiMeasuredTorque.{hpp,cpp}, IndiMeasuredTorqueTest.cpp
- src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml: MC_INDI_LND_SLEW, MC_INDI_ERPM_FRZ
- msg/ActuatorTorqueMeasured.msg: new field `uint8 motor_frozen_mask` (the only log field; not added to indi_rate_status)

## Existing tests changed (expected consequence of the ramp, not regressions)
Four lib tests encoded the old one-cycle takeoff step and now expect one slew step (5*dt = 0.0125) of the ramp:
LandedYawOutputUnaffectedByYawCutoff, LandedKeepsActuatorModelRunning, LandedBlendTracksWithoutAccumulating,
FirstLandedCycleIgnoresTheFlightIncrement (the last accounts for the ramp of t_fb from its in-flight value).

## New tests
Lib (IndiRateControlLandedTest): MaybeLandedPulseNoStep (asserts: |u_pulse - u_nopulse| <= 1e-6 every cycle over
200 cycles with a 50 cycle maybe_landed pulse, steady trim 0.1 with model + measurement + blend converged; the
frozen blend does not change the value because the gap is converged), TakeoffRamp, TouchdownRamp (per-cycle change of
t_fb and of u <= 5*dt+1e-6; reaches target within 0.5 s).
Module (IndiFrozenRpmTest): FrozenRpmFallsBack, ConstantRpmConstantCommandStaysValid (10 s, plus disarmed),
NoisyRpmVaryingCommandValid, FrozenRecovers.

## Test results
`make tests 'TESTFILTER=[iI]ndi'` in Docker (note: the filter `indi` alone does not match functional-IndiMeasuredTorque;
a pipe in TESTFILTER breaks the shell): 4/4 ctest targets pass (IndiAccelControl, indi_rate_control_test,
IndiInjection, IndiMeasuredTorque). See break-checks below for the final restored run.

## Break-checks
Each done once in Docker, then restored; final run after restore: 4/4 ctest targets pass.
1. Combined flag again (landed := landed || maybe_landed inside update): MaybeLandedPulseNoStep FAILS (only that test).
2. Ramp removed (`if (_landed_ramp)` -> `if (false)`): TakeoffRamp, TouchdownRamp FAIL, plus the four existing landed tests
   whose expectations were moved to the ramp (LandedBlendTracks..., LandedUsesMeasurementLikeModel, LandedKeepsActuatorModelRunning).
3. Command-variation condition removed from the frozen test: ConstantRpmConstantCommandStaysValid FAILS.
Not break-checked: FrozenRpmFallsBack / NoisyRpmVaryingCommandValid / FrozenRecovers (no dedicated revert run).

## UNVERIFIED
- McIndiRateControl.cpp/.hpp were NOT compiled (the px4_sitl_test board does not build the module); the changes there
  are small but unbuilt. Needs `make px4_sitl_default` (or the firmware target).
- msg field and params not checked against a full build/param metadata generation; msgs instruction file only reviewed.
- Slew default 5.0 and the 0.02 / 0.5 s thresholds are decided values, not checked against flight logs.
- actuator_motors command is stamped with hrt_absolute_time at read; motor index = control[] index assumed to match
  esc actuator_function MOTORn (same assumption as the existing code).
- make format not run.

## Orchestrator check (S58)
- Diff read (law ramp, module wiring, frozen window). Suspected false trip at the arming edge (window_start 0): not
  reachable, the first command after any window restart has zero spread and restarts the window. Guard added, then
  removed as redundant; test `ArmingEdgeStartsANewWindow` kept (passes with and without the guard, regression only).
- `make px4_sitl_default` rc 0 (module compiled, `results/s58_sitl_build.log`); `make tests TESTFILTER=[iI]ndi` 4/4
  targets pass (`results/s58_tests.log.1`); `make format` clean, touched only these files.
- Four existing tests adapted to the ramp: exact expected values changed to one slew step, none loosened.
- Open: opus review of the DIFF (route check 57 rec 2) after items 2 and 3 are coded; frozen detection not yet
  exercised in SITL (needs a frozen-value injector in gz_bridge telemetry, G3 list).
