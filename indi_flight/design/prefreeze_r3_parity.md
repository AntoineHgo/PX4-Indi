# Pre-freeze review 3/3: module parity checklist

Date 2026-11-21. Scope: checklist of indi_project/review/external_review_s59_notes/module_parity.md (Tasks 1-3) against the
current code of mc_indi_rate_control (A, RC), src/lib/indi_rate_control, mc_indi_pos_control (B, PC), where B now replaces
mc_pos_control (MC_INDI_POS_EN) and serves all modes. Commit under review: 4013def8a9 (docs(indi-flight): S154 STATE trim).
Line numbers are current. Read-only review; no code changed. Verdicts: CLOSED / OPEN / PARTIAL / N/A / DEFERRED.
Severity (OPEN/PARTIAL only): SAFETY or MINOR. RC = src/modules/mc_indi_rate_control/McIndiRateControl.cpp,
PC = src/modules/mc_indi_pos_control/McIndiPosControl.cpp, IMT = .../IndiMeasuredTorque.cpp.

## Task 1: A vs stock mc_rate_control

| Id | Verdict | Evidence | Reasoning |
|---|---|---|---|
| T1.1 | CLOSED (rate_ctrl_status gap MINOR, accepted) | RC:258-262 indi_rate_status; logged_topics.cpp:91; rc.mc_apps:31-38 | Autotune is not started with INDI ("autotune disabled with INDI"); logging via indi_rate_status instead of rate_ctrl_status. |
| T1.2 | DEFERRED | RC:437 comment; DECISIONS.md:31 (remedy absorbs sag) | Battery scaling intentionally absent; steady-gap remedy and ESC telemetry absorb sag. |
| T1.3 | CLOSED | RC:228-229, :433-434 | Allocator unallocated_torque is applied only when newer than the previous setpoint; stale feedback falls back to the model by design. |
| T1.4 | CLOSED | RC:424-427, :436-438 | landed/maybe_landed passed to the law; no difference that matters (as in the note). |
| T1.5 | PARTIAL (MINOR) | RC:398-407, :421-427 | No INDI reset on the rising edge of flag_control_rates_enabled; only the setpoint lead resets (sp_source change) and the library resets while disarmed. With rates enabled in every armed MC mode the edge practically occurs only at arm. Fix if wanted: _indi.reset() on the edge. |
| T1.6 | CLOSED | n/a (equal to stock) | No kill handling in either; unchanged. |
| T1.7 | CLOSED | RC:380-381 | acro_branch handled explicitly; stick-loss behaviour equal to stock. |
| T1.8 | PARTIAL (MINOR) | RC:497-518 (argv ignored); rc.vtol_apps:17 starts mc_rate_control vtol only | A does not refuse "vtol"; the VTOL startup script never starts it, so only a manual start can mix. MINOR (VTOL out of scope for the freeze). Fix: refuse argv "vtol" in task_spawn. |
| T1.9 | CLOSED | n/a (equal to stock) | dt identical. |
| T1.10 | CLOSED | RC:110, :379-382, :415-416; IndiRateSetpointWatchdogTest; prefreeze_r2_stage3.md F3 (MC_INDI_SP_TO, 0.5 s) | Setpoint-age watchdog: zero rates, thrust held, warning. |
| T1.11 | CLOSED | n/a | Equal. |
| T1.12 | CLOSED | RC:70-76 (refuse if vehicle_torque_setpoint published < 500 ms ago); rc.mc_apps:17-24; DECISIONS.md:836 (F8) | Second rate controller refused. Reboot requirement for MC_INDI_EN remains implicit (MINOR, doc). |

## Task 2: eRPM path

| Id | Verdict | Evidence | Reasoning |
|---|---|---|---|
| T2.timestamp | DEFERRED | IMT hpp:74 SAMPLE_MAX_AGE_US; param MC_INDI_ERPM_DLY (yaml:144) | Driver stamp is not frame capture time; modelled by ERPM_DLY (calibrated on hardware). Driver is out of scope. |
| T2.errcount | CLOSED | RC:197-203 (setMotorSample with esc_errorcount); IMT:190 (any rpm change restarts detection); IndiMeasuredTorqueTest | Counter-change drop kept. |
| T2.frozen | CLOSED for A, PARTIAL (MINOR) for B | IMT:103-136, :215; RC:171 (MC_INDI_ERPM_FRZ); PC:128-146 | A detects an rpm unchanged while the command varies (frozen latch). B mean_u (PC:136-144) has only the online flag and the rpm range check, no frozen/error check; one frozen channel biases a 4-motor mean. DECISIONS.md:836 keeps S95 F4 deferred. |
| T2.online | CLOSED | RC:197-198; PC:136 | Offline motor invalidates torque / mean_u. |
| T2.index | CLOSED | RC:190-195; PC:128-133 | Motor from actuator_function, flag bit from index j; fine for contiguous quad. |
| T2.pole | DEFERRED | MC_INDI_W_MAX calibration, defaults_audit_s138.md | Calibration note, not code. |
| T2.negative/3D | N/A | IMT:120 | Quad with 1D outputs only. |
| T2.zero rpm | CLOSED | IMT:120; PC:136 | Valid zero; INDI reset while disarmed (RC:424). |
| T2.fresh | PARTIAL (MINOR) | IMT hpp:74 (20 ms hard-coded) vs RC:236 MC_INDI_ERPM_TO | Two separate age knobs remain. Safe (invalid -> fallback). |
| T2.drain | DEFERRED | RC:184-215 | Drain order unchanged; the delay is covered by MC_INDI_ERPM_DLY. |
| T2.unset | CLOSED | RC:192-194 | motor<0 skipped. |

## Task 3: module B

B is now a stock-structured position controller (flight_mode_manager chain, takeoff ramp, stock failsafe setpoint) with an INDI
stage; it is not a registered external mode, so the external-mode items are N/A.

| Id | Verdict | Evidence | Reasoning |
|---|---|---|---|
| T3.1 | CLOSED | PC:316 blend_hold; PC:1028 useModelledForce; IndiStageMode.hpp:49-52 | No zero-rate / MPC_THR_MIN branch exists; maybe_landed in flight selects the modelled-force stage, and the stage keeps running. |
| T3.2 | CLOSED | PC:883-925, :939-997 (stock takeoff ramp: _takeoff state machine); DECISIONS INDI-from-takeoff-ramp | Takeoff ramp runs through the stage on the modelled force. |
| T3.3 | CLOSED | PC:569-580 (land tilt), PC:1028 | Landing uses the stock chain (MPC_LAND_SPEED, land tilt); ground contact selects modelled force. |
| T3.4 | DEFERRED | PC:364-400 (Hold), :448-462 (0.5 s warning); prefreeze_r2_stage3.md:56; DECISIONS D-STAGE-STALE | Hold = last attitude and thrust, warning after 0.5 s; no can_arm path (not an external mode). Commander failsafe on EKF loss is the end of Hold. Accepted in r2. |
| T3.5 | N/A | no ArmingCheck in PC | Not an external mode. Missing-W_MAX case: PC:124 gives mean_u invalid, falls back to the modelled path (silent except PC:461 warning). MINOR. |
| T3.6 | N/A | PC (no setpoint_config) | The module is the position controller; no setpoint type registration. |
| T3.7 | N/A | PC:892 (offboard flag path) | Stock chain handles offboard setpoint types as stock mc_pos_control. |
| T3.8 | CLOSED | PC:859-866, :1163-1219; EkfResetDetectTest | adjustSetpointForEKFResets (stock) plus library reset on any counter change. |
| T3.9 | DEFERRED | PC:190-199, :364-400; stock failsafe setpoint PC:1130-1156 | Stale local position gives Hold; commander failsafe ends it. Same as T3.4. |
| T3.10 | CLOSED | PC:~220-225 yaw_sp from att_sp; stock yaw logic | Stock behaviour. |
| T3.11 | PARTIAL (MINOR) | PC:196, :309, :448-462 | Telemetry loss selects the model path with a one-time 0.5 s warning; no failsafe. Spec: modelled path is the designed fallback (D-STAGE-STALE). |
| T3.12 | N/A | no registration | No unregister. A-side latch is closed by T1.10. |
| T3.13 | N/A | not an external mode | Landed zero-rate branch no longer exists (T3.1). |
| T3.14 | N/A | no measureRate / _filter_ready in PC | Filter configuration of the old module is gone; dt clamp in IndiStageMode.hpp:96-107, rate<5 Hz hold (DECISIONS.md:817). |

## Gaps needing an independent key

None. No SAFETY OPEN/PARTIAL item found. Closest candidates (all MINOR, accepted by design): T3.4/T3.9 Hold without can_arm
(r2 spec), T2.frozen in B's mean_u (modelled fallback bounded by a 4-motor mean), T1.8 VTOL (never started by rc.vtol_apps).

## Unverified

- T1.5: whether any armed mode sees rates_enabled false -> true in flight (read from flags only; not traced in commander).
- T2.frozen B: whether the 4-motor mean_u bias from a single frozen ESC is bounded by the library blend clamp (not traced in indi_accel_control).
- T3.10 and T3.3: relied on the stock-structure claim; the stage yaw path line was not re-read.
- Test names cited by file only; tests were not run.
