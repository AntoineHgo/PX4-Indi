# S134 F-7 implementation: one INDI controller from arming to disarming (uncommitted)
Module `src/modules/mc_indi_pos_control/`. Spec: DECISIONS.md D-F7-GROUND.

## What changed
- `IndiStageMode.hpp`: `computeWantIndi(armed,pos,vel,climb)` (no takeoff/ground args); new pure `useModelledForce(takeoff_flight, ground_contact, maybe_landed)` = `!flight || ground_contact || maybe_landed`; `selectStageMode(..., model_force=false)` returns `IndiModelAccel` when `model_force` even with fresh acceleration (failures still `Hold`).
- `McIndiPosControl.cpp`: `want_indi` no longer depends on takeoff state/ground contact (~l.958); `model_force` computed next (~l.962) and passed to `runIndiStage` (new arg). In the stage `in.f_b_valid = !model_acc` already gave f_b=(0,0,-G c_prev), mean_u invalid, blend_hold true: reused unchanged. `HandoverBlend` calls removed (apply/decay/bypass/clear). `syncHoverThrust` replaced by `_control.setHoverThrust(ht)` (~l.876). Planned modelled mode is not counted as degraded in `trackDegraded` (no 0.5 s warning on ground).
- Remaining `Bypass` branch = disarmed or pass-through modes only (stock setpoint, nothing INDI); the `want_indi`-false-while-armed stock branch is gone. Stock integrator reset every cycle while armed in these modes (existing `if (want_indi) resetIntegral()`).
- Removed: `HandoverBlend.hpp`, `HandoverBlendTest.cpp`, `HoverThrustSync.hpp`, `HoverThrustSyncTest.cpp`, CMake test entries, `_handover`, `_control_ht`. HoverThrustSync only shifted the stock vertical integrator on ht change; the integrator never integrates now, so it was bypass-only. Plain `setHoverThrust` kept (stock attitude/thrust-direction scale).
- `msg/IndiPosStatus.msg`: comment only; reused `stage_mode` (2 = modelled force, now also ground/ramp). No new field.

## Tests (docker, `indi_project/docker/run.sh -n t134 -- 'make tests TESTFILTER=Indi'` then ctest -R)
- Module gtests: 4 suites pass (IndiStageMode 9 tests incl. 2 new, IndiPosInjection, FailsafeSetpoint, EkfResetDetect). make tests TESTFILTER=Indi: 8/8 suites pass.
- Break check: `useModelledForce` forced to `return false` -> unit-IndiStageMode FAILED (lines 50,51); restored.
- `make px4_sitl_default` built OK (294/294).
- astyle `check_code_style.sh` on the 4 changed C/C++ files: no output (clean).

## Unverified
- No flight/SITL run: ground idle (+100 m/s^2 -> `_thr_min`) and rampup behaviour of the modelled path, edge step at flight, are G5.4 measurements.
- Library clamps ground collective via `_thr_min` (indi_accel_control.cpp:416); not exercised with the real stock setpoint.
- On ground, `reason` instrument and Hold-with-no-INDI-cycle edge (held values) unchanged; untested.
- Stage on ground with `landed` but takeoff state flight and no contact/maybe_landed uses measured force (spec).

## Key fixes (key_s134_f7.md MAJOR 3, 4, and the reset-seed MINOR)
- MAJOR 3: `runIndiStage` takes `flying` (takeoff state >= flight); `setLimits` thr_min = `flying ? MPC_THR_MIN : 0` (as stock, McIndiPosControl.cpp ~l.182). Ground/ramp collective can reach 0 (library kMinUpThrust keeps t_c finite).
- MAJOR 4: pure `shouldResetStageState(prev_armed, armed)` (IndiStageMode.hpp) on the control-mode edge calls new `resetStageState()`: `IndiAccelControl::resetBlend()` (new, b=0), `_acc_stale_latched=false`, `_acc_fresh_since=0`, `_held_valid=false`, `_last_thrust=0`, `_indi_reset_pending=true` (filters/differencing via the existing T10 path; the bypass branch also resets each disarmed cycle). `_filter_hz` is a parameter cache, left alone.
- MINOR: reset-pending path seeds the filter with the modelled force when `model_force`.
- Test: `ArmEdgesResetStageState`. Break check: helper returning false -> IndiStageModeTest.cpp:78 failed; restored. It tests only the decision, not that `resetStageState()` clears each member (unverified by test).
- Re-run: `make tests TESTFILTER=Indi` 8/8 pass; astyle fixed McIndiPosControl.cpp (check was failing); `make px4_sitl_default` rebuilt after f7_smoke_s134/README.md existed. IndiAccelControl lib test not run (no filter matched). Ground xy tilt MINOR not addressed.
