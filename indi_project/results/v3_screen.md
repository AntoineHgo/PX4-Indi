# v3 stage-1 screening of the actuator blend time constant (session 46, O-12)

Script `bench/v3_screen_tb.sh`, 2026-11-15 00:34-00:37, v3 binary, v2 sim config, seed 1, watchdog on. All INDI
configs = frozen indi_v2 inner loop + tuned PID's outer gains (D-outer-check) + `MC_INDI_ACT_BLD` Tb. Reference
pid_tuned (r1f c05) flown in the same batch. Tb 0 = v2 behaviour (`results/v3_smoke.md`).

| config | motor_loss_0 roll / pitch RMS (deg) | rotation RMS (deg) | position RMS (m) | mismatch_combined_rate roll-rate RMS | step_roll roll RMS (deg) |
|---|---|---|---|---|---|
| pid_tuned | 0.80 / 0.90 | 8.56 | 3.9 | 0.385 | 3.15 |
| Tb 0 (v2) | 5.31 / 7.69 | 14.5 | 67.6 | 0.369 | 3.08 |
| Tb 0.1 | **watchdog trip** (> 3 m below hold altitude 1 s, t = 53.7 s) | - | - | 0.376 | 3.17 |
| Tb 0.3 | 0.67 / 1.03 | 11.3 | 3.3 | 0.366 | 3.06 |
| Tb 1.0 | 1.06 / 1.57 | 10.9 | 8.5 | 0.366 | 3.04 |

Effort (motor-rate RMS ratio to PID): motor_loss_0 0.77-0.88, mismatch_combined_rate 1.06-1.29, step_roll 0.84-1.13.

## Reading
- The blend does what D-v3-blend designed it for: the steady post-fault tilt of v2 (Tb 0) is gone at Tb 0.3 and 1.0;
  roll/pitch RMS return to PID's level and position no longer drifts away (67.6 m -> 3.3 m).
- The rotation-angle RMS (V's primary metric for motor_loss_0) stays above PID (11 vs 8.6 deg) at every Tb: the
  remainder is yaw after the fault, not roll/pitch. Unexplained so far: check yaw in stage 2 before freezing.
- Tb 0.1 lost altitude after the fault (single seed, not yet explained): pruned under O-12 rather than investigated
  now. Hypothesis to check if it matters: the fast blend hands the low-frequency loop the full motor gap while the
  failed motor saturates.
- The nominal and rate entries do not separate the Tb values (within 3 %), as expected for a low-frequency term.
- With the outer gains matched, step_roll is 0.96-0.97x PID for every INDI config (v2 frozen tuning: 1.20x).

Survivors to stage 2: Tb 0.3 and 1.0, seeds 2-3, same entries (`V3_STAGE2_DONE` in `results/v3_screen.log`).
1 seed: screening only, not a result.
