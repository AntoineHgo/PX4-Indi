Verdict: BLOCKING

# S95 review: D-GAP collective blend, firmware vs specification

Scope: `src/lib/indi_accel_control/indi_accel_control.{hpp,cpp}`, `src/modules/mc_indi_pos_control/McIndiPosControl.cpp`,
D-GAP tests in `src/lib/indi_accel_control/IndiAccelControlTest.cpp` (:678-852), against `indi_flight/DECISIONS.md` D-GAP
(:416-461, S71 amendment items 1-5) and the D-GAP part of D-RATE-BLD-EDGE (:488-509). This is a code read only. Nothing was
built or flown. Transient sizes are estimates (UNVERIFIED).

What matches the spec: b = LP_tb(u_model_f - u_meas_f), with both paths sharing the same delay and LPF (cpp:290-305). |b| <= 0.3
(cpp:305). b is frozen when the hold flag is set, when mean_u is invalid, or when the collective was clamped on the previous
cycle (cpp:301). reset() keeps b and restarts the model path at u + b (cpp:106-136). The module sets the hold on
landed || maybe_landed (McIndiPosControl.cpp:208) and on every bypass (:250). While telemetry is invalid, u_f = u_model_f (cpp:309).
NaN and dt checks (cpp:225-233) return false. The module then bypasses and calls reset(), which keeps b. A false maybe_landed in
flight only holds b. u_f = u_meas_f + b keeps the held value, so there is no thrust drop. A standing error appears only if the
gap changes during the hold.

## Findings

1. BLOCKING. Step of +b in the collective at every bypass-to-active edge (take-off, mode switch, every recovery from a bypass).
   - File: McIndiPosControl.cpp:252-255 (bypass branch), indi_accel_control.cpp:106-125.
   - Spec: D-GAP item 1 says "b resumes ... no snap". Item 5 says each freeze test resumes "without a step afterwards" at the
     A3/A8 bypass and e7 edges. It also requires |dz| < 0.15 m in the first 5 s after take-off. The library contract
     (hpp:172) says reset() takes the measured mean_u.
   - Code: the module passes the commanded collective (`_coll_meas` = vehicle_thrust_setpoint, or the stock thrust) as mean_u.
     reset() sets the measured path to c and the model path and `_thrust_prev` to c + b. With a steady gap the real eRPM value
     is about c - b. So on the first active cycle u_f = u_meas_f + b = c + b. That is wrong by +b, and t_c = t_f + (a_c - a_f)
     commands c + b.
   - Effect: the error decays as u_meas_f settles toward the real mean_u over the delay plus the LPF time (UNVERIFIED, about
     tens of ms).
   - Failure scenario: the rampup-to-flight transition. want_indi needs TakeoffState::flight (:836-838). With b held from the
     previous flight, the collective steps by b, up to +-0.3. A negative b (hover-thrust estimate too high) gives a thrust drop
     right after lift-off, close to the ground. The same step follows every POSCTL entry from ALTCTL, every stale-attitude or
     accel bypass, and every invalid setpoint.
   - Test gap: `FrozenAtBypassA3A8` (:808) and `NoDriftAfterResetWithoutHold` (:825) call reset() with the MEASURED value
     (kScale * u_cmd, or 0.6 with u_cmd = 0.6/kScale). That is the opposite of what the module passes, and the tests check only
     b, never `out.thrust`. The unit evidence for the bypass edge therefore does not cover the shipped call.
   - Fix: make reset take both values: model path and `_thrust_prev` = commanded c; measured path = mean_u when it is valid,
     otherwise c - b. Or have the module pass `fresh_esc ? _mean_u : c - _indi.blend()`. Add a test that drives the module's
     convention and asserts |thrust(k+1) - c| < 0.01 at the first active cycle.

2. MAJOR. Step of +b in the collective at telemetry recovery.
   - File: indi_accel_control.cpp:291, 309.
   - Spec: item 1 says "coll_f switches back to coll_meas + b on the first valid mean_u sample", without a step (item 5). It
     covers the telemetry-loss edge "and its recovery".
   - Code: while mean_u is invalid, the measured path is fed `u_model`, not `u_model - b`. After a loss longer than the delay plus
     the LPF time, u_meas_f is about u_model_f. On the first valid sample, u_f jumps from u_model_f to u_model_f + b and then
     decays over the delay plus LPF time. b also drifts a little toward 0 during that transient: the freeze is released while the
     innovation is still near 0.
   - Failure scenario: ESC telemetry dropouts longer than 100 ms (`kEscMaxAge`) in flight with a gap. Each recovery gives a
     collective kick of b, up to 0.3.
   - Test gap: `FrozenOnTelemetryLossAndRecovery` (:773) checks only b, so it would not fail.
   - Fix: feed `u_in = u_model - _b` while the telemetry is invalid, so that u_meas_f + b stays continuous. Add an
     `out.thrust` continuity assert to the test.

3. MAJOR. The thrust gap is not removed in altitude mode, and in bypass the vehicle has neither INDI nor stock integral action.
   - File: McIndiPosControl.cpp:836-838 and :797, :828.
   - Spec / owner direction: D-GAP restores the integral action. Item 4 says the MPC_*_VEL_I_ACC integrators stay 0 under INDI.
     The owner direction is "all modes".
   - Code: want_indi needs flag_control_position_enabled || flag_control_velocity_enabled. ALTCTL and ALTITUDE_CRUISE clear both
     flags (commander/ModeUtil/control_mode.cpp:74-75). The stage is therefore always bypassed in altitude mode. Even so,
     `_control.resetIntegral()` runs unconditionally every cycle (:797, :828), so the stock velocity integrator is also zeroed.
   - Failure scenario: altitude mode with 4 motors at 0.85 gives a standing z error near the D-GAP "both off" figure (about
     0.37 m, UNVERIFIED, HTE helps partly). That is worse than stock. The same applies during takeoff rampup and
     flying_but_ground_contact.
   - Other modes: position mode (POSCTL, offboard position) and velocity mode (offboard velocity) run the path. Acceleration-only
     offboard (item 4, A10/A15) depends on the commander flags (UNVERIFIED).
   - Fix: add flag_control_climb_rate_enabled (altitude) to want_indi. Or reset the stock integrators only when the INDI stage
     actually ran this cycle.

4. MAJOR. Anti-windup misses the measured mean_u at its limit.
   - File: indi_accel_control.cpp:301, 367.
   - Spec: item 1 says that if the allocator exposes no collective-saturation flag, "the module's own clamp AND the measured
     mean_u at its limit are used".
   - Code: only the module clamp is used (thr_min/thr_max, previous cycle). No mean_u limit test and no allocator flag
     (control_allocator_status is not read).
   - Failure scenario: the allocator desaturates, for example roll/pitch priority with one motor at 1 under a single-motor loss.
     It cuts the collective below the command while the command stays below MPC_THR_MAX. Then a_c - a_f stays > 0, and b
     integrates it like an integrator, up to 0.3. When the saturation clears, the collective overshoots by the wound-up b and
     unwinds with tb (about 1 s), which gives an altitude overshoot.
   - Fix: freeze b when mean_u_valid && mean_u >= thr_max - eps (or <= thr_min + eps). Better, freeze on the allocator saturation
     flags. Add a unit test with a plant whose mean_u saturates below the command.

5. MAJOR. T123 item 1 (reset on re-config) is still not fixed. It now makes the filters drop to zero in flight.
   - File: McIndiPosControl.cpp:145-148, indi_accel_control.cpp:76-82.
   - Spec: slice2_plan_s69.md "T123 deviations" item 1 asks for a reset right after setFilter.
   - Code: `LowPassFilter2p::set_cutoff_frequency` zeroes the delay elements (LowPassFilter2p.hpp:70-72). The "force a reset
     below" reset happens only in the bypass branch. When can_run is true, update() runs on zeroed f_b, u, u_model and jerk
     filters.
   - Trigger: a single dt deviation > 20 % (for example one late vehicle_local_position sample). It fires twice, on the late
     sample and on the return.
   - Effect: for the filter settling time a_f is about +g (as in free fall). The output falls back to about a_c - g e3 + g_t b,
     which is feedforward with no INDI feedback. b also decays a little because the innovation collapses too. The magnitude in
     flight is UNVERIFIED.
   - Fix: call `_indi.reset(f_b, mean_u, ...)` right after setFilter. Or let setFilter re-seed the filters from their last output.
     Add hysteresis to the rate-change trigger.

6. MINOR. setBlendTimeConstant(tb <= 0 or NaN) zeroes b (cpp:95-103).
   - Spec: "b starts at 0 at boot only".
   - Failure scenario: an in-flight change of MC_INDI_TB to 0 gives a -b collective step. Disabling the blend makes the output
     u_meas_f anyway, but zeroing b also loses the learned value if the blend is turned back on.
   - Fix: keep b, and gate its use on tb > 0.

7. MINOR. Leftover state across edges.
   - reset() does not clear `_coll_clamped`, so the first active cycle after a bypass can be frozen. That is harmless.
   - update() changes `_b`, the filters and the jerk state before the late finiteness returns (cpp:319, 385). Those returns
     report "out untouched", but the state has been advanced by one step. This is benign because the bypass calls reset().
   - T123 items 2 (A3 fallback uses this cycle's stock thrust, McIndiPosControl.cpp:252, not `_last_thrust`) and 3 (100 ms
     `kEscMaxAge`, :161) are still present. Whether the spec was amended for them is UNVERIFIED.

8. MINOR. Gaps in test coverage. Behaviour with a test that would fail if broken (b only):
   - Hold flag: `FrozenOnLandedHold`.
   - Telemetry-loss freeze: `FrozenOnTelemetryLossAndRecovery`.
   - reset() keeps b: `ModuleResetDoesNotTouchBlend`.
   - Clamp freeze: `FrozenWhileCollectiveClamped`.
   - e7 edge: `FrozenAtE7EdgeSingleCycle`.
   - Convergence and the negative control: `ConvergesToThrustGap` and `NegativeControlDisabledKeepsGap`.

   Behaviour with NO test:
   - Output (thrust) continuity at any edge (findings 1 and 2).
   - The module's reset argument convention.
   - Landed/maybe_landed wiring in the module (module-level, none).
   - The bypass hold in the module.
   - Altitude-mode activation.
   - mean_u-limit anti-windup.
   - tb change in flight.
   - setFilter without reset.

   Whether each test was break-checked (spec item 5) is UNVERIFIED.
