# T200 D-GAP fixes log

Step 1: wrote break-check tests (old reset(f,c) API via moduleReset helper, Input.alloc_saturated field added without logic).

## Break-check (pre-fix code, docker `make tests TESTFILTER=IndiAccelControl`): 5 new tests FAIL as intended
- NoCollectiveStepAtBypassEdgeModuleConvention (F1): |thrust(first active)-c| = 0.081, max step over 100 cycles 0.024
- ThrustContinuousAtTelemetryLossAndRecovery (F2): step 0.039 at loss, 0.046 at recovery
- FrozenWhenMeasuredUAtLimit (F4): b wound to 0.3 (mean_u stuck at 0.995)
- FrozenWhenAllocatorSaturated (F4): blend_frozen false / b moves (Input.alloc_saturated field added, no logic yet)
- SetFilterReconfigDoesNotStepThrust (F5): thrust step 0.090 at setFilter (needs an unmodelled disturbance: with a pure gap the
  zeroed filters cancel in a_c - a_f + t_f because b carries the gap; the loss is the disturbance estimate)
Note: tests use setFilter(100,10) in F1/F5 (test fixture default is a pass-through filter, which hides the F1 step).

## Fixes applied (all after break-check above). Final: IndiAccelControl 36 gtests pass, IndiPosInjection pass, `make px4_sitl_default` builds. Formatted with Tools/astyle/fix_code_style.sh (docker).
- F1 (BLOCKING): indi_accel_control.cpp reset(f_b, coll_cmd, mean_u): model path/buffer/_thrust_prev from c; measured path = mean_u if finite else u_model - b. hpp contract updated. McIndiPosControl.cpp bypass branch passes (c, fresh_esc ? _mean_u : NAN). Tests: NoCollectiveStepAtBypassEdgeModuleConvention (new; both telemetry/NaN cases); FrozenAtBypassA3A8, NoDriftAfterResetWithoutHold, ModuleResetDoesNotTouchBlend and all other reset() callers moved to the 3-arg call (c commanded, mean_u measured). Fail-before 0.081 step -> pass.
- F2: update(): u_in = u_model - _b when telemetry invalid; u_f = u_meas_f + _b whenever tb>0. Test ThrustContinuousAtTelemetryLossAndRecovery (steady converged gap). Fail-before 0.039/0.046 -> pass. UNVERIFIED/limit: with b NOT converged (u_meas + b != u_model) a loss still steps the collective by the residual; inherent, small once b converged.
- F3: McIndiPosControl.cpp: resetIntegral() now guarded by _indi_active. First site (before _control.update) uses the previous cycle's flag; second site moved after runIndiStage and uses this cycle's flag. Known leftover: on the first active cycle after a bypass the integrator accumulated in bypass is still in that one cycle's a_ref (cleared right after). No unit test (module has no harness): UNVERIFIED beyond compile.
- F4: library: freeze b when valid mean_u >= kMeanUSatLimit (0.98; only the upper limit, the lower limit is covered by the module clamp and the allocator flag) or Input.alloc_saturated. Module: subscribes control_allocator_status; saturated = !thrust_setpoint_achieved || any of actuator_saturation[0..3] != OK (assumes motors are actuators 0-3, as the module assumes 4 motors elsewhere), fresh <= 200 ms. Tests FrozenWhenMeasuredUAtLimit (b 0.3 -> <0.01), FrozenWhenAllocatorSaturated. The module part is UNVERIFIED (no flight/SITL run; torque_setpoint_achieved not used).
- F5: setFilter re-seeds _lpf_f/_lpf_u/_lpf_um/_lpf_j from stored last outputs (_last_f_b, _last_u, _last_um, _j_diff_f). Module: rate deviation >20 % must persist 5 consecutive cycles (or cutoff param change, or first config); removed the useless `_indi_active=false`. Test SetFilterReconfigDoesNotStepThrust (with a 2 m/s^2 unmodelled updraft; a pure gap hides it because b cancels). Fail-before 0.090 -> pass.

## F3 note for the orchestrator: altitude mode
control_mode.cpp (commander/ModeUtil) sets flag_control_altitude_enabled/climb_rate_enabled (:102) but not flag_control_position_enabled / flag_control_velocity_enabled for ALTCTL, so want_indi (position||velocity) is false: INDI is bypassed. The INDI stage is accel_only (a_ref = stock a_c, z comes from the stock climb-rate loop's acceleration setpoint), so it could serve ALTCTL by adding flag_control_climb_rate_enabled to want_indi: the stage only needs a finite a_c; the XY acceleration in altitude mode is whatever the stock loop outputs (tilt-based from the sticks), which the stage would pass through. Not changed (separate design item). With F3 the stock integrator now works in ALTCTL.
