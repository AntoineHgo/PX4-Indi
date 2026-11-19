# S131 T5 (failsafe extraction) and T10 (estimator reset reaction)

## Diff summary (src/modules/mc_indi_pos_control/)
- FailsafeSetpoint.hpp (new): pure `computeFailsafeSetpoint(now, velocity, land_speed, FailsafeInfo*)`. Same rules as stock
  `MulticopterPositionControl.cpp:667-713`. `FailsafeInfo` tells the caller which warning to print.
- McIndiPosControl.cpp ~1050-1066: `generateFailsafeSetpoint` keeps the 2 s warn rate limit and calls the pure function.
- EkfResetDetect.hpp (new): `EkfResetDetector::update(EkfResetCounters)`, first sample only latches.
- McIndiPosControl.cpp ~795-803: detector fed right after `adjustSetpointForEKFResets` (setpoint/filter/goto adjustment untouched,
  already identical to stock); sets `_indi_reset_pending`.
- McIndiPosControl.cpp ~242-249 (runIndiStage, `can_run` branch): if pending, `_indi.reset(...)` once (same arguments as the bypass
  call at ~356, collective from measured thrust else `_last_thrust`), then clear. ~353: flag cleared in bypass (reset every cycle there).
  Hold cycles keep the flag until the next INDI or bypass cycle.
- McIndiPosControl.hpp: includes, members `_indi_reset_detector`, `_indi_reset_pending`.
- CMakeLists.txt: two `px4_add_unit_gtest`.
- Tests: FailsafeSetpointTest.cpp (`MatchesStockRuleTableOnAllCombinations`, `NamedCases`), EkfResetDetectTest.cpp
  (`FirstSampleDoesNotReset`, `NoBumpNoReset`, `EachCounterBumpIsDetectedOnce`, `WrapAroundIsDetected`, `TwoBumpsInOneSampleGiveOneTrue`).

## Stock rule table (read from stock code, used by the test)
Start all NaN. vxy finite: vel xy = 0. vxy invalid: acc xy = 0, vel z = MPC_LAND_SPEED (not NaN xy as the task text said:
vel xy stays NaN, acc xy = 0). vz finite: vel z NaN -> 0 (land speed kept if set). vz invalid: vel z = NaN, acc z = +0.3
(NED, down positive, so a bit below hover). Only `states.velocity` is used by stock; position and acceleration validity are not.
All-invalid velocity: vel z NaN and acc z 0.3 override the land speed.

## Break-check
- Failsafe: acc z .3f -> -.3f: `unit-FailsafeSetpoint` FAILED (acceleration expected 0.3 got -0.3); restored, passes.
- Detector: `changed = _initialized && ...` -> `true && ...`: `EkfResetDetectTest.FirstSampleDoesNotReset` FAILED (1 test); restored, passes.
- Before: 5 gtest targets pass (IndiAccelControl, IndiPosInjection, IndiStageMode, FailsafeSetpoint, EkfResetDetect) in px4_sitl_test.

## Blind-descent behaviour of the stage (report only, control law unchanged)
The stage does not get an all-NaN setpoint. It reads `local_pos_sp.acceleration` after stock `PositionControl::update`
(McIndiPosControl.cpp ~1006-1008), which is the full stock `_acc_sp`, finite (valid check requires it): with vxy and vz
invalid it is (0, 0, 0.3), since NaN state or NaN setpoint terms are skipped by `addIfNotNanVector3f`. `a_ref = a_c_pre_inject` (+inject, zero
by default) -> `in.accel_only = true` -> library `a_c = a_ref` (indi_accel_control.cpp:307), p and v are not required (:237).
Result: INDI collective for a = 0.3 m/s^2 down, thrust direction from the stock vector. Stock: `thrust_ned_z = acc*hover/g - hover`
(PositionControl.cpp:220), same acceleration, so consistent in intent; the numerical thrust differs by the INDI model (accepted
design). The stock integrator is zeroed whenever the stage is requested. xy-valid/z-invalid: acc xy comes from the xy velocity loop.

## Open points / UNVERIFIED
- UNVERIFIED: runtime effect of the T10 reset in flight/SITL (no SITL scenario run; only compile + gtests).
- The call in the module (pending flag, reset args, Hold behaviour) is not unit tested, only the detector.
- A reset with `fresh_acc` false uses the model force; mean_u NaN -> steady relation. Blend is kept by `reset()`.
- The stock adjust code treats a nonzero counter at module start as a reset (existing behaviour); the new detector does not.
- Stock modules untouched (git status). `Tools/astyle/check_code_style.sh` passes on the 6 changed files (rc 0).
