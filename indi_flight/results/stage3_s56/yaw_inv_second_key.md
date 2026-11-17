# Second key, commit 23e9d30cc0 (yaw spin-up as low pass on the increment)

Verdict: AGREE-WITH-ISSUES

Spec: indi_flight/design/yaw_inv_review_r1.md (findings 1-9), indi_flight/DECISIONS.md:299-322.
Code: src/lib/indi_rate_control/indi_rate_control.cpp, indi_rate_control.hpp, mc_indi_rate_control_params.yaml.

## Checks (a)-(g)

| Check | Result | Evidence |
|---|---|---|
| (a) state written after step-9 clamps and isAllFinite, as t_cmd(2) - t_fb(2) | PASS | finite check cpp:396; clamps cpp:404-407; write cpp:411 `_yaw_inc_prev = landed ? 0.f : (t_cmd(2) - t_fb(2))` |
| (b) 0 when landed | PASS for the stored value; GAP for the next cycle, see issue 1 | cpp:411 writes 0 when landed; but cpp:391 reads `_yaw_inc_prev` ungated by `landed` |
| (c) zeroed in resetStates(); reached by reset(), faultOutput(true), hold expiry | PASS | cpp:175 zero; reset() calls resetStates() cpp:181; faultOutput(true) cpp:196-198; hold expiry calls reset() cpp:206 |
| (d) rejected cycles do not write | PASS | early return cpp:226 (inputs/dt/params) and cpp:398 (non-finite dt_cmd) both precede the write at cpp:411; no other return between cpp:411 and cpp:426 |
| (e) roll/pitch numerators bit-identical | PASS | cpp:390 g2_over_dt = 0.f and cpp:391 prev_inc = 0.f for i<2; cpp:392 adds 0.f*0.f, old code added 0.f*(t_f - t_f_prev); x + 0 == x, denominator unchanged cpp:393 |
| (f) same dt in both G2/dt terms | PASS | single `g2_over_dt = _g2_yaw / dt` cpp:390, used in cpp:392 and cpp:393 |
| (g) G2 = 0 gives old law with G2 = 0 | PASS | g2_over_dt = 0 so cpp:392-393 reduce to nu - (1+c)a_f over G1, identical to old numerator with G2 = 0 |

Steady state (hand derivation): with a = G2/dt, the recursion is Delta_k = (N + a Delta_{k-1}) / (G1 + a).
Fixed point D: D (G1 + a) = N + a D, so D G1 = N, D = N/G1. Yes, it equals N/G1.
From Delta_0 = 0: Delta_k = (N/G1)(1 - p^k), p = a/(G1 + a) in [0, 1) for G1 > 0, a >= 0. Converges, pole independent of N.

## Findings 1-9

| # | Finding | Verdict | Evidence |
|---|---|---|---|
| 1 | MAJOR applied-increment state | IMPLEMENTED | cpp:406 clamp, cpp:411 write t_cmd(2)-t_fb(2); hpp:327 `_yaw_inc_prev` replaces `_t_f_prev` |
| 2 | MAJOR landed zero, ground law | IMPLEMENTED as literally specified, with a gap | cpp:374 t_fb=0 on landed; cpp:411 zero after step; gap: cpp:391 uses stale prev on first landed cycle (issue 1) |
| 3 | MAJOR param/comment text | IMPLEMENTED | yaml MC_INDI_G2_Y long text (no "remove yaw rate feedback" left), yaml max 1000; hpp:54-58 law comment |
| 4 | MAJOR reset paths, rejected cycles | IMPLEMENTED | cpp:175, 181, 197, 206; rejected return cpp:226, cpp:398; test FaultHoldThenRecoveryHasNoStep (test.cpp:1720) |
| 5 | MINOR same dt in both terms | IMPLEMENTED | cpp:390, 392, 393 |
| 6 | MINOR G2 change in flight | IMPLEMENTED by construction | state is a torque (cpp:411); no test of a mid-flight G2 change |
| 7 | MINOR source switch | IMPLEMENTED by construction | dt_cmd does not read t_f (cpp:392); t_f enters only via t_fb in cpp:406; no test |
| 8 | MINOR allocator saturation | N/A | no change required; t_f path not in the diff |
| 9 | MINOR logging semantics | NOT IMPLEMENTED | getTorqueIncrement still returns the per-cycle clamped increment dt_cmd (cpp:424, hpp:234), not a persistent offset; test read at indi_rate_control_test.cpp:453 unchanged |
| C | remove _t_f_prev, keep lead | IMPLEMENTED | no src refs left (only test locals test.cpp:363, 1216); lead kept cpp:386, 392 |
| D | default G2 = 0 | IMPLEMENTED | yaml default 0.0 for MC_INDI_G2_Y |

## Issues

1. MINOR-MODERATE, cpp:391-392: `prev_inc` is not gated by `landed`. On the first landed cycle after flight, the numerator carries (G2/dt) times the last in-flight increment, so ground output is (nu - a_f + (G2/dt) X)/(G1 + G2/dt) rather than (nu - a_f)/(G1 + G2/dt) as finding 2 requires. Only active when G2 > 0. Suggested fix: `const float prev_inc = (i == 2 && !landed) ? _yaw_inc_prev : 0.f;`. The test LandedStateIsZeroAndTakeoffHasNoDoubleCount (indi_rate_control_test.cpp:1706) starts from a fresh controller and does not cover flight-to-landed.
2. Finding 9 not done: logging semantics unchanged (cpp:424), and the yaw spin-up test at indi_rate_control_test.cpp:453 was not updated. Either change the logging or record in the spec that torque_increment(2) stays the per-cycle increment.
