# S72 T160: D-GAP implementation (collective blend), seed 1, speed 4, v2 sim, MC_INDI_W_MAX 2700

## Diff summary (uncommitted)
- `src/lib/indi_accel_control/indi_accel_control.{hpp,cpp}`: blend state b (|b| <= 0.3, 0 at construction only), model path = previous clamped
  collective through its own delay buffer and LPF (`_um_buf`, `_lpf_um`), u_f = u_meas + b with b = LP_tb(u_model - u_meas); invalid telemetry: u_f = u_model;
  `setBlendTimeConstant` (0 = disabled, b = 0), `setBlendHold`, `blend()`, Output `blend`, `blend_frozen`. b is frozen (held, never reset) when hold, telemetry
  invalid, or the collective was clamped in the previous update (c_min/c_max/thr limits). `reset()` leaves b alone.
- `src/modules/mc_indi_pos_control/`: new param `MC_INDI_POS_TB` (s, default 1.0, 0 = disabled; yaml follows parameters.instructions.md), hold flag =
  landed || maybe_landed, hold also set on every bypass cycle (lib is not updated there, reset() keeps b); module now publishes `indi_pos_status`
  (it was declared but never published in this tree) with a_c, a_f, t_f, t_c, omega_ff, mean_u, mean_u_valid, thrust, blend, blend_hold, blend_frozen.
- `msg/IndiPosStatus.msg`: + blend, blend_hold, blend_frozen.
- Tests: `IndiAccelControlTest.cpp` fixture `IndiAccelBlendTest` (8 tests).
- No diff in mc_rate_control, mc_att_control, mc_pos_control, control_allocator, allocation lib, commander.

## Unit tests (`make tests TESTFILTER=IndiAccelControl` in Docker; `TESTFILTER=indi_accel_control` finds no test, the ctest name is unit-IndiAccelControl)
Base: 100% passed (`test_base.txt`). Tests: ConvergesToThrustGap (k 0.85, tb 1 s, 10 tb: |u - ideal| < 0.01), NegativeControlDisabledKeepsGap (tb 0: error >= 0.9(1-k)g/g_t, b = 0),
FrozenOnLandedHold, FrozenOnTelemetryLossAndRecovery, ModuleResetDoesNotTouchBlend, FrozenWhileCollectiveClamped, FrozenAtBypassA3A8 (hold + reset(), no update),
FrozenAtE7EdgeSingleCycle. Each asserts |db| < 1e-6 across the edge and a first post-edge step of < 0.003 in b.
Note: the amendment's "0.9 (1-k)" is read as 0.9(1-k)*g/g_t (collective units); the plain 0.9(1-k) = 0.135 exceeds the whole gap (0.087).

Break checks (`test_breaks.txt`, source restored after each, diff verified):
| rule broken | failed tests |
|---|---|
| b jumps to instantaneous gap while hold | FrozenOnLandedHold, FrozenAtE7EdgeSingleCycle |
| reset() zeroes b | ModuleResetDoesNotTouchBlend, FrozenAtBypassA3A8 |
| b zeroed on invalid telemetry | FrozenOnTelemetryLossAndRecovery |
| no freeze while clamped | FrozenWhileCollectiveClamped |

Convergence/negative control are their own pair (tb 0 fails the convergence bound by construction). A3/A8 and e7 are tested at library level
(hold flag + reset(), single-cycle hold); the module-level wiring of these edges is NOT tested (UNVERIFIED beyond the flights below).

## Flights (gap085 uses stage5_s70/gap_htoff.params, loss08 gap.params), `s5_gap_check.py`, standing dz = last 10 s mean (positive = below)
| run | [ev+10,ev+20] mean | last 10 s mean/std | max abs dev | S70 baseline last10 | thrust before->after | b at end | verdict (< 0.06) |
|---|---|---|---|---|---|---|---|
| gap085_indi_htoff | 0.042 | 0.025 / 0.011 | 0.213 | 0.372 | 0.1367 -> 0.1608 (log 0.1597) | 0.0239 (ideal 0.136*(1/0.85-1) = 0.024) | PASS |
| loss08_indi | -0.036 | -0.056 / 0.007 | 0.075 | 0.189 | 0.1367 -> 0.1452 | 0.0084 | PASS, marginal (0.056 vs 0.06) |

b held at its value after the event (frozen fraction 0.2-0.3% of cycles, no hold), see `blend_trace.py`. loss08 ends 0.056 m ABOVE target (HTE on adds to the blend,
double compensation; hypothesis not tested). Pre-test (gap085_indi_htoff) was run before loss08, sequential, no stray containers.

## Land / re-take-off with the gap present: NOT RUN
`bench/scenarios.py` has no land-and-retake-off scenario; run_scenario.py only lands at the end (line ~896, waits for disarm). Missing: a scenario phase
sequence (hold, land, disarm/re-arm, take-off, hold) with motor_fault kept across the landing, and a checker for |b| after re-take-off within 10 % of
pre-landing and max |dz| < 0.15 m in the 5 s after take-off.

## UNVERIFIED
- Margin criteria of amendment item 3 (resonance < 3 dB, overshoot < 25 %, G2 PM >= 45 deg at tb and tb/3) not measured; tb = 1.0 s default only.
- Single seed, single flight each; no determinism spread. e7/A3/A8 module wiring not exercised in flight; landed hold not exercised (no land/re-take-off).
- The rate loop's state reset (indi_rate_control.cpp:336-345) is untouched; the stage-3 safety review filing remains open.

## Orchestrator follow-up (S72)
- Review of the diff: after reset() the model path restarted at u (measured), not u + b, so b drifted at a
  bypass -> active edge (test NoDriftAfterResetWithoutHold: 6.2e-4 broken, < 2e-4 fixed; `test_reset_break.txt`,
  `test_after_reset_fix.txt`). Fixed before commit 3481bdcf9e. The two flights above were flown BEFORE this fix; they
  contain no bypass edge after take-off (landed hold covers take-off), so they stand.
- Second key (`second_key.md`, `bench/second_key_s72.py`, independent, window ending at the LAND setpoint 119.77 s):
  gap085 dz_truth 0.020 (primary 0.025), all estimator error (dz_est 0.000); loss08 dz_truth -0.053 (primary -0.056),
  of which control error -0.040 with a_c-a_f = 0.158 m/s2 held -> anomaly A-33. run.json clock ~0.72 s off the
  ULog (armed 30.01 vs t_arm 30.74), consistent with the S70 time-offset hypothesis.
