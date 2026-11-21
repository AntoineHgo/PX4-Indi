# S190 fix: native-rate specific-force filter (D-AF-ALIAS)

Files changed: src/lib/indi_accel_control/{indi_accel_control.hpp,.cpp,IndiAccelControlTest.cpp},
src/modules/mc_indi_pos_control/McIndiPosControl.{hpp,cpp}. Stock modules and msg: zero diff vs main.

## Library
- `sampleSpecificForce(f_b, dt)`: second LowPassFilter2p (`_lpf_f_native`), same cutoff as setFilter, own rate
  (roundf(1/dt)), hysteresis 20 % persistent for 16 samples, re-seed from last output (first sample: from the sample).
  Non-finite f_b / dt<=0 ignored. setFilter updates its cutoff and re-seeds it.
- update(): f_b_valid && fed -> f_bf = native output, `_lpf_f.reset(f_bf)`. Else old path. reset() reseeds native too.

## Module (call-frequency finding)
- vehicle_acceleration has no ORB_QUEUE_LENGTH (queue 1), published ~267 Hz. Run() was woken only by
  vehicle_local_position (~88.9 Hz) and pollStageInputs() ran once per local-position cycle: 2 of 3 samples were lost.
- Fix: `_acceleration_sub` is now a SubscriptionCallbackWorkItem (registered/unregistered like local position), so each
  acceleration publish wakes Run(). New `pollAcceleration()` runs at the top of every Run() (before the local-position
  branch), reads the latest sample, takes dt from timestamp_sample deltas (fallback timestamp, clamped 1..50 ms, first
  sample skipped) and feeds the filter. pollStageInputs() still calls it (no-op if nothing new). The stage stays on local position.
  Residual: if Run() is delayed past two publishes, one sample can still be missed (queue 1, no msg change allowed).

## Tests (px4_sitl_test, target unit-IndiAccelControl, binary found via find in build/px4_sitl_test)
- 56 -> 59 tests, all pass (test.log). New: NativeRateFilterRejectsAliasedVibration, ...ResetReseedsWithoutStep,
  ...ValidToInvalidSwitchHasNoStep.
- Break-check (update() ignores native output): alias test FAILS, amp 0.924 vs limit 0.03 (breakcheck.log); restored -> 59 pass.
  Native form gives well below 0.03 (theory ~0.011).
- astyle (Tools/astyle/fix_code_style.sh): all five files unchanged.
- SITL build px4_sitl_default: OK (build.log), module compiled.

## Unverified
- No SITL flight; mc_indi_pos_control module tests (if any) not run; the module is not compiled by px4_sitl_test.
- Wakeup rate rises to ~267 Hz+89 Hz for the module (Run does parameters_update and a cheap sub check each time): CPU not measured.
