# T202 second key: review of bf44ece093 (D-GAP edge fixes)

Verdict: NO BLOCKING. 1 MAJOR (test for finding 2 is vacuous; first-cycle stock integral at bypass-to-active edge),
rest OK/MINOR. Unit test target `IndiAccelControl` passes (1/1, run once). Module compile was not exercised by that target.

## Findings 1-5

1. Bypass-to-active step: OK (code), MINOR (test).
   - indi_accel_control.cpp:113-137: u_model = c*k_cmd, `_thrust_prev` = c, `_u_buf` = measured u (mean_u, else u_model - b), `_um_buf` = u_model,
     all filters seeded to those. With mean_u ~ c*k_cmd - b, u_meas_f + b = u_model on the first cycle, and thrust is c. Units are consistent
     (c is thrust units, u is omega^2; the k_cmd factor is applied once, in u_model).
   - Module McIndiPosControl.cpp:277: passes c and `fresh_esc ? _mean_u : NAN`, matching the contract.
   - Test NoCollectiveStepAtBypassEdgeModuleConvention asserts `_out.thrust` (|thrust - c| < 0.01, b ~ 0.09 here) for NaN and valid mean_u.
     The old module convention would fail it (step of about b).
   - MINOR: the test seeds exact steady values with kScale constant, so it does not cover a mean_u that lags c*k_cmd - b
     (collective ramping at the edge, residual error ~ lag * dc/dt).
2. Telemetry loss/recovery: OK (code), MAJOR (test). cpp:308 feeds u_model - b, and cpp:333 uses u_meas_f + b, so thrust is continuous at both edges.
   - Test `ThrustContinuousAtTelemetryLossAndRecovery` (Test.cpp ~:278) is vacuous. The fixture SetUp uses setFilter(0,0) and delay 0 and
     the test never calls setFilter(100,10). So u_meas_f is instantaneous: with the old code the invalid path gives u_f = u_model_f, and the first valid sample gives real + b (b frozen) = u_model.
     The old step arises only through filter or delay lag, so this test would PASS on the reverted code.
   - Fix: add setFilter(100,10) and setMeasurementDelay(>0) in that test, invalidate for more than the filter time, and assert on out.thrust at recovery.
3. Stock integrator in bypass: MAJOR (new defect), the change itself is OK.
   - McIndiPosControl.cpp:822 uses `_indi_active` of the previous cycle. On the first active cycle after bypass the integral was not zeroed before
     `_control.update()`, so a_ref contains the accumulated stock integral once (the post-stage reset at :868 only helps from the next cycle).
   - Effect: a_c step = vel_i (MPC_Z_VEL_I_ACC integral, order 1-3 m/s^2, bounded by the controller clamp) gives a collective blip of vel_i/g_t (~0.05-0.15 u) for one cycle,
     then a_ref falls back, which also gives a jerk backward-difference spike (omega_ff, clamped by kMaxOmegaFf).
     It double-counts the gap compensation together with the held b.
   - Minimal fix: zero the integral before `_control.update()` whenever INDI is going to run this cycle: hoist the `want_indi` computation above :822
     (it needs only the control-mode flags and the takeoff state), or use `_indi_active || want_indi`. Keep the :868 reset.
4. Anti-windup: OK / MINOR.
   - cpp:318-319 freezes b on mean_u >= 0.98 (kMeanUSatLimit) and on `alloc_saturated`. The module (:154-164, :222) reads control_allocator_status
     (thrust_setpoint_achieved or any of actuator_saturation[0..3]), and the flag is fresh only within 200 ms of the report time.
   - Test FrozenWhenMeasuredUAtLimit passes mean_u = 0.995 with a hover model and fails if the limit test is removed. FrozenWhenAllocatorSaturated asserts the blend_frozen output and b.
   - MINOR: only the upper mean_u limit is tested (the lower limit is not). Instance 0 of the allocator status only.
   - Consequence of a permanently saturated motor (e.g. a motor pinned at max/min by CoM offset or failure, or thrust_setpoint_achieved stuck false):
     b is frozen forever at its last value. There is no windup, but the D-GAP compensation stops tracking, e.g. with battery sag the standing altitude error
     equals the change in gap since the freeze. The stock integral is zero while INDI runs, so nothing compensates. Consider a timeout or a
     "frozen for more than X s" fallback, or ignore the lower-side flags in hover.
5. setFilter re-seed: OK.
   - cpp:84-88 re-seeds `_lpf_f`, `_lpf_u`, `_lpf_um` and `_lpf_j` from the last outputs. `_j_diff_f` (cpp:182) is the jerk filter's last output, so the value is correct.
   - The module hysteresis (5 cycles) is OK. Test SetFilterReconfigDoesNotStepThrust uses an updraft (_dist = 2) and asserts `_u_cmd`/thrust. It would fail on zeroed
     filters (a_f falls to +g, no updraft information).

## Extras

- tb == 0 path: OK. u_f = u_meas_f; b is 0 (setBlendTimeConstant zeroes it), so u_model - b = u_model and reset/invalid behaviour equals the old one.
- alloc freshness: OK (200 ms, timestamp based). The allocator publishes every cycle (ControlAllocator.cpp:470).
- resetIntegral change: see item 3 (one stock-integral blip plus a jerk spike on the first active cycle).
