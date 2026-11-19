# S130 D-STAGE-STALE implementation (not committed)
Files: msg/IndiPosStatus.msg (+stage_mode, STAGE_MODE_* consts), src/modules/mc_indi_pos_control/{IndiStageMode.hpp (new), IndiStageModeTest.cpp (new), CMakeLists.txt, McIndiPosControl.cpp/.hpp}.

## Library check for (a) (src/lib/indi_accel_control/indi_accel_control.cpp)
- :318 `u_in = in.mean_u_valid ? in.mean_u : (u_model - _b)` -> with mean_u invalid the measured path is the modelled one (u_model = _thrust_prev*_k_cmd, :316).
- :332 blend_frozen includes `!in.mean_u_valid` -> b is held (module also sets setBlendHold(true)); :339 u_f = u_meas_f + b = u_model_f.
- :335 b update skipped when frozen. :345 t_c = t_f + (a_c - a_f), with t_f = z_b*(-g_t*u_f) (:340) and a_f from the modelled f_b (:309).
  With f_b = (0,0,-G c_prev) and u_f = model, t_f - (-a_f) cancels: t_c ~ a_c - g (model inversion), exact up to the LPF/delay lag of u_model_f vs c_prev (not exactly zero when the collective changes fast). UNVERIFIED numerically.
- update() rejects non-finite f_b (:237), mean_u_valid with non-finite mean_u (:239).

## Behaviour
- selectStageMode: want false -> Bypass; att/aref/rate bad -> Hold; acc bad -> IndiModelAccel; else Indi. update() false -> Hold (call site).
- Hold: zero-order hold of q_d, thrust_body, local_pos_sp.thrust stored (storeHeld) on every successful INDI cycle AND on every bypass cycle. Edge: first active cycle failing holds the last bypass (ground/rampup handover) value; if no cycle ever ran, level attitude at hover thrust `ht`.
- Hold publishes indi_pos_status with stage_mode 3 (only thrust, a_c_pre_inject, mean_u fields filled); library not updated during hold (filters not advanced; resume after hold is not step-checked: UNVERIFIED).
- Modelled accel: c_prev = _last_thrust if finite >0 else ht; blend hold forced; status.mean_u_valid = false.
- WARN once per episode if mode 2/3 lasts > 0.5 s (trackDegraded).
- Integral reset: `if (want_indi) _control.resetIntegral();` (no freshness condition); comments updated. want_indi/z_only now via computeWantIndi/deriveZOnly.
- Note: stageInputsFresh()/its declaration is now unused by the cycle (left in place).

## Tests (docker: indi_project/docker/run.sh -n build 'make tests TESTFILTER=indi', then ctest -R)
- IndiStageMode 7 tests pass; IndiAccelControl, IndiPosInjection, IndiInjection, IndiRateSetpointWatchdog, IndiTorqueStampTracker, IndiInjectionStep pass (7/7 ctest targets; IndiInjectionStep failed once when run in the same command right after ninja rebuild, passed 3/3 on rerun: race, not related).
- Break checks: (1) `return acc_ok ? Indi : IndiModelAccel` -> `return StageMode::Bypass` : "IndiStageModeTest.cpp:15: Failure" / `[ FAILED ] IndiStageModeTest.WantedIsNeverBypass` (+ AccelStaleOnly fails, 2 ctest targets failed incl. unit-IndiStageMode). (2) first `return StageMode::Hold` -> Bypass: IndiStageModeTest.cpp:15 Failure (3 assertion failures). Both reverted (diff of header vs backup clean).
## Build
- `make px4_sitl_default` in docker: no warnings/errors in grep; module compiled (seen in the test build McIndiPosControl.cpp.o linked). Final exit code not captured.
- make format: NOT run (no command from s128 notes; astyle not applied; check_format UNVERIFIED).
- UNVERIFIED: any flight/SITL run; rc.mc_apps untouched.
