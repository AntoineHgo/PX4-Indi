# S90 code-to-spec review: attitude break (commit b41dd6ec81 vs attitude_break_s86.md s1-3, s8)

Paths relative to src/modules/mc_indi_rate_control (MIRC). Review only, no source edited.

## Verdicts per question

1. AX = 0 or PT = 0: law input and published torque identical to parent.
   - PT 0 (or any PT != 1), AX 0: `IndiInjectionStep.cpp:55-58` calls `indi.update(rates, rates_sp, ...)` with the member setpoint
     itself, same arguments and order as the parent; `torque_sp = c + 0` (lines 64-66, `c + zero` is bit exact for finite c; -0 + 0 = +0 is
     the only bit difference, and the parent also added a zero `inject` vector). Parent added `inject` the same way. OK.
   - PT 1, AX 0: `rate_sp_break` false (line 39), same path. OK. Published torque is `step.torque_sp` (McIndiRateControl.cpp:248-250). OK.
   - Side effect: `parameters_updated()` (McIndiRateControl.cpp:112-115) chooses AMP vs RAMP; only the amplitude of the generator changes.
     With AX 0 the generator is unused. OK.
2. PT 1, AX != 0: x = y + d on one axis before the update (`IndiInjectionStep.cpp:41-52`, axis from `injection.axis()`, other two
   components copy y). u = c (`:53-54` torque_inject zero, torque_sp = pre_inject). `_prev_torque_setpoint` is set from the published
   `vehicle_torque_setpoint` (McIndiRateControl.cpp:434), i.e. u = c, and `torque_allocated_prev` is built before the step (:219-223).
   Both unchanged. OK. `_rates_setpoint` member is never written (passed const ref). OK.
3. Gating: see findings M1, M2, m1.
4. Parameters: see findings M3, m2, m3.
5. Tests: see section below.
6. Real time: no allocation; one extra 36-byte copy, three Vector3f; see m4.

## Findings

### BLOCKING
None.

### MAJOR
- M1 Generator state is not reset when the gate is closed while disarmed. `IndiInjectionStep.cpp:44-46` calls `injection.update()` only
  when `rate_sp_break_allowed && !fault`. The only `_started = false` reset is inside `update()` on `!armed`
  (IndiInjection.cpp, `update`, the `!armed` branch). `rate_sp_break_allowed = !_rate_sp_stale && flag_control_attitude_enabled`
  (McIndiRateControl.cpp:239). If the vehicle disarms while the gate is closed (acro, offboard rates-only, or any mode where
  attitude is not enabled when disarmed), `update()` never sees `armed == false`, `_started` stays true, `_t0_us` is the old flight's.
  Next arm + attitude mode: no restart, no DLY; t is measured from the previous flight, so d is mid-sequence or already past
  NP*Tp (zero for the whole flight). Spec s3 "DLY after the first armed, airborne cycle" and "a new flight restarts" are violated.
  Same for PT 0? No: PT 0 calls `update()` every cycle (:60-62), so only PT 1 is affected. Fix: pass armed/landed-reset to the
  generator even when the gate is closed (e.g. call `injection.update()` always and multiply/zero the result, or add a
  `reset()` on `!in.armed`). Not caught by any test (see 5).
- M2 Resume after a gate closes mid-window is a step, not a restart, and the time base is silently shifted. While gated, the
  generator is not called, so `_started` and `_t0_us` hold; on resume `t = timestamp - _t0_us` has advanced by the gated time and
  d jumps from 0 to the multisine value (peak about 5x amp, 0.25 rad/s at default) in one cycle; the lead (`rate_sp_dot`)
  sees it as a step (clamped at 1000 rad/s^2 by the law, so a transient, not a fault). The window (NP*Tp from first start) also
  elapses during the gate, so a long stale/fault gap eats periods, and a gap at the start delays t0 instead of DLY (DLY counts from the
  first allowed cycle, not the first armed airborne cycle as spec s3 states). Spec s3/s8 do not say which is intended; the
  estimator's validity rule needs "d equals the generator on timestamp_sample", which still holds because the generator is a pure
  function of time, so analysis is fine, but the step is a plant disturbance. Decide and document: either ramp d in, or discard
  the windows that contain a gate transition (the log fields `rate_sp_stale`, `fault`, but not `flag_control_attitude_enabled`,
  are enough to find stale/fault; ACRO transitions are not logged in indi_rate_status, `sp_source` is: McIndiRateControl.cpp:377).
- M3 Amplitude cannot be checked against the setpoint it was built for after a PT change in flight when AMP == RAMP, and the
  restart on PT change is implicit. `parameters_updated()` re-runs on every parameter_update (McIndiRateControl.cpp:291-292), so
  PT change in flight does rebuild: amp changes from AMP to RAMP, `setParameters` sees a difference and resets `_started`
  and `_num`. If AMP == RAMP numerically (both can be 0.05 by hand) `setParameters` early-returns, no restart, and d switches
  injection point (torque -> rate) mid-window with no restart; the change of break point leaves the vehicle without a clean window.
  Low probability bench-only; classify MAJOR only because the spec (s3) promises one axis/one break per flight. Suggest: add PT to
  the early-out comparison key or forbid PT change while armed.

### MINOR
- m1 `getFault()` gate (`IndiInjectionStep.cpp:44`) uses the previous cycle's flag, as s8 says. It is also true for the first cycle
  after a fault clears: not an issue. But `getFault()` is evaluated before the first `update()` of the very first cycle (false). OK.
  Only note: `fault` clears on any good cycle (indi_rate_control.cpp:479), so gating is per cycle and produces d steps
  (see M2), not a latched stop.
- m2 PT outside {0,1}: yaml is `type: enum` with values 0,1 only, so the parameter system does not enforce the range for a
  hand-written value (px4 enum has no min/max enforcement at set time beyond the metadata). In code, PT = 2 or -1 gives
  `in.point != 1` and `in.point != 0` (IndiInjectionStep.cpp:62): no injection at all, silently, while amplitude selection
  (McIndiRateControl.cpp:112) uses AMP. Safe failure (no d), but silent. Optionally add `min: 0 max: 1`.
- m3 Units/bounds: RAMP `unit: rad/s`, min 0, max 1, default 0.05, decimal 3, increment 0.01 (yaml), matches spec s3. Naming follows
  the existing MC_INDI_INJ_* family; `MC_INDI_INJ_PT` mirrors `MC_INDI_PINJ_PT`. parameters.instructions.md (applyTo src/**): one
  owner (OK, module owns it), `long` for PT re-lists both options (the guideline says "Never re-list the options in long";
  the long text also repeats "Bench and system identification only" in two params, cheap after compression). Suggest moving the
  per-option detail to the labels. Param name `RAMP` for an amplitude in rad/s is a poor abbreviation ("rate amplitude"),
  but it is spec-given. messages.instructions.md applyTo `msg/**`: comments are present; no timestamp issue; field names
  follow the existing pattern. (Not re-verified: exact applyTo globs and any msg rule on new fields in a logged topic.)
- m4 Real time: `runIndiInjectionStep` is stack only, no allocation, no virtual calls. The status message grows by 3 x 3 x 4 =
  36 bytes at 800 Hz (about 29 kB/s more published and logged when the topic is logged at full rate); the s8 text defers the
  msg size/drop check to the first flight. `step_in`/`step` are zero-initialised each cycle (about 150 bytes): negligible.
  `indi.getFault()` and the injection are called once per cycle. No concern except the log-rate item.
- m5 `rates_sp_pre_inject` is `rates_sp` only while PT = 1 and AX != 0 (`IndiInjectionStep.cpp:50`); with PT 1 and AX 0, all zero,
  as s8 states, but a log reader cannot tell "break active, d gated" from "break off" except via `rates_sp_inject == 0` and
  `rates_sp_pre_inject != 0` for the former: that is fine for the check script.
- m6 McIndiRateControl.cpp:239 uses `_vehicle_control_mode.flag_control_attitude_enabled` without checking `flag_armed` or
  `_vehicle_control_mode` freshness; it is the module's cached copy, updated at :310 before use. OK.

## 5. Tests (IndiInjectionStepTest.cpp)

1. `RateSetpointBreakFeedsLawTheInjectedSetpoint` (:86): fails if the law is fed y (reference mismatch on c and `rate_sp_dot`, plus a
   guard that y would give a different output) or if x is wrong, or if u != c (:113). Strong. Does not fail if d is applied on the wrong axis
   only when axis 2 is the single tested axis (covered by test 2). Does not cover `_prev_torque_setpoint` (module level).
2. `RateSetpointBreakOnlySelectedAxisAndSign` (:127): fails for wrong axis, sign, or pre-inject y. Good.
3. `TorqueBreakUnchanged` (:159): fails if PT 0 stops adding d to u or if the rate fields are non-zero. Good.
4. `OffIsBitIdentical` (:184): AX 0, PT 0/1, memcmp to a law fed y. Fails if the step modifies c. Note it compares only torque_sp and
   two fields, not `rates_sp_pre_inject` (expected zero) nor `torque_inject`. Weak point: with AX 0 the generator is never called, so it
   would not catch `injection.update()` side effects.
5. `RateSetpointBreakGating` (:204): each of disarmed, landed, rate_sp_break_allowed false gives peak 0; control g = 3 has d. Fails if
   a gate is dropped. Fault gate is not a loop case (g = 3 has no fault; comment lists 4 cases with only 3 gates).

Not caught by any test:
- Law fault gate (`IndiInjectionStep.cpp:44` `!indi.getFault()`): deleting it keeps all 5 tests green (no test drives a law fault).
- M1 (generator not reset when disarmed while the gate is closed) and M2 (resume behaviour, step on resume, DLY base): no test
  has a gate sequence within one run; every gate case is closed for the whole run.
- Module-level items: `_prev_torque_setpoint`/allocated-torque feedback, AMP vs RAMP selection (`parameters_updated`), PT change in
  flight, PT outside {0,1}, `rate_sp_break_allowed` formula (McIndiRateControl.cpp:239, `_rate_sp_stale` and attitude flag), and
  that the member `_rates_setpoint` is not modified. All are in McIndiRateControl.cpp which has no test.
- Yaw with PT 1 (law low-pass on yaw setpoint) is untested; spec s8 defers it.
- `landed` with PT 1 and `maybe_landed`: `in.maybe_landed` passes through but is never varied.

## Summary counts
BLOCKING 0, MAJOR 3 (M1-M3), MINOR 6 (m1-m6).

## Resolution (orchestrator, S90)
- M1, M2: generator now runs every cycle with `armed && gate_open` (IndiInjectionStep.cpp): a closed gate acts as a
  disarm, so the disarm reset is never skipped and the sequence restarts from zero (after DLY) when the gate reopens.
  New test RateSetpointBreakGateClosingRestartsSequence (stale/ACRO gate and law-fault gate); verified failing with the
  old gating, passing after restore. Covers the untested law-fault gate (MINOR).
- M3: `IndiInjection::restart()` called from parameters_updated when MC_INDI_INJ_PT changes. Not unit-tested
  (McIndiRateControl has no test harness): UNVERIFIED until the pre-test flight.
- MINOR: PT enum min/max added, long text no longer re-lists the options. Other MINORs open (msg size check at first flight).
