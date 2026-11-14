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

## Stage 2 (seeds 2-3, Tb 0.3 and 1.0 vs pid_tuned, 18 flights, 0 failures)

Seeds 1-3 agree within 1-3 % on every metric (mean of 3 seeds):

| config | motor_loss_0 roll / pitch / yaw RMS (deg) | rotation RMS | position RMS (m) | mismatch_combined_rate roll-rate RMS | step_roll roll RMS |
|---|---|---|---|---|---|
| pid_tuned | 0.80 / 0.90 / 8.47 | 8.55 | 3.90 | 0.386 | 3.11 |
| Tb 0.3 | 0.67 / 1.03 / 11.2 | 11.2 | 3.30 | 0.366 | 3.09 |
| Tb 1.0 | 1.06 / 1.57 / 10.8 | 11.0 | 8.48 | 0.365 | 3.09 |

- **Tb 0.3 selected** (D-v3-tb): best roll/pitch and position after the motor loss, equal elsewhere.
- The rotation-angle gap to PID on motor_loss_0 is entirely yaw (11.2 vs 8.5 deg). Together with step_yaw (1.26x PID,
  D-outer-check) it points at the INDI yaw rate loop (K_Y behind YAW_CUT), which the blend does not touch.
