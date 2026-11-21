# F2 probe (S180): extrapolate held trajectory_setpoint between sender samples
Change: src/modules/mc_indi_pos_control/SetpointExtrapolation.hpp (pure fn extrapolateSetpoint, cap = TRAJECTORY_STREAM_TIMEOUT_US 500 ms),
called at `_control.setInputSetpoint(...)` in McIndiPosControl.cpp (copy; stored _setpoint untouched). Test: SetpointExtrapolationTest.cpp (5 tests, CMakeLists).
Unit (build/px4_sitl_test, docker): SetpointExtrapolation 5/5, FailsafeSetpoint 2/2, EkfResetDetect 5/5, IndiStageMode 15/15, IndiPosInjection 6/6 (unit_tests.txt).
Break check (function returns input unchanged): SetpointExtrapolationTest fails (unit_tests_broken.txt), header restored, tests re-passed.
Build px4_sitl_default OK (build.log). Flight cruise_typ_s1 (seed 1, traj_lemniscate, params_xyp12, typical noise) rc=0, container f2fly.
## Scoring (score_out.txt, reconcile_out.txt, skip_key1.md; RAW into this folder, tracked raw file untouched)
Lemniscate window 36-53.5 s, both keys agree (identical RMS to 3 digits). 33.5 Hz line: ABSENT (no flagged window near 33 Hz).
89 Hz line: PRESENT and now on all four motors: sustained on m0..m3 (88.5-89.25 Hz), 8-12 of 14 windows flagged, per-window RMS 5.2e-4..7.7e-4
(max 7.7e-4 m0 t0 39/46; GP 89.25 Hz was 5.5-6.7e-4 m2 only). Key1 span 35-53 s 88.8 Hz max RMS 7.6e-4; key2 worst m0 88.75 Hz x504 7.66e-4.
G4 table: R20 0.030 % (GP 0.053), C20 1.14e-3 (GP 1.55e-3), R4 0.388, chatter CHATTER both keys, item2 FAIL, item1 PASS, item3 FAIL (known window artefact, S180 reconcile).
Land line (outside lemniscate): 20.3 Hz 1.9e-3 (AUTO_LAND, 66-71 s), as GP (20-21 Hz 2.3e-3). Skip key1: no non-skipped-land fix, CHATTER from the 88.8 Hz span.
## Verdict vs criterion (no line at 33.5 or 89 Hz with RMS >= 5e-4): FAIL. 33.5 Hz removed, 89 Hz not removed (slightly higher, wider).
