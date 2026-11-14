# Outer-gain check: is INDI v2's nominal step deficit the attitude-loop tuning? (session 46, diagnostic)

Script `bench/s2_outer_check.sh`, 2026-11-15 00:01-00:07, host otherwise idle, same binary and v2 sim config as the
seen set. 5 nominal entries x seeds 1-3 x {pid_tuned (r1f c05), indi_v2 (frozen r2 c01), indi_v2_pidouter}, 45 runs,
0 failures. `indi_v2_pidouter` = indi_v2 with the shared outer gains set to tuned PID's (MC_ROLL_P 3.167 -> 5.122,
MC_PITCH_P 5.19 -> 5.797, MC_YAW_P 2.757 -> 3.238); INDI inner-loop params unchanged
(`bench/params/indi_v2_pidouter.params`). Diagnostic only, not a tuning candidate; the frozen V verdict stands.

Primary metric as a ratio to pid_tuned (mean of 3 seeds); effort = motor-rate RMS ratio.

| entry | pid_tuned | indi_v2 | effort | indi_v2_pidouter | effort | pidouter < pid (seeds) |
|---|---|---|---|---|---|---|
| step_roll (roll RMS deg) | 3.092 | 1.20 | 0.62 | **1.01** | 0.94 | 1/3 |
| step_pitch (pitch RMS deg) | 3.045 | 1.08 | 0.95 | 1.04 | 0.88 | 0/3 |
| step_yaw (yaw RMS deg) | 12.63 | 1.26 | 0.56 | 1.29 | 0.74 | 0/3 |
| step_diag (rotation RMS deg) | 5.858 | 1.13 | 0.78 | 1.04 | 1.25 | 0/3 |
| rate_step_roll (roll rate RMS rad/s) | 0.3705 | 0.92 | 1.08 | 0.91 | 1.17 | 3/3 |

## Reading

- Roll: the outer gain explains the whole gap (1.20x -> 1.01x, effort 0.62 -> 0.94). The roll/pitch/diag step
  deficit of the frozen v2 tuning is an outer-loop tuning artefact (low MC_ROLL_P chosen under a hover-noise-driven J).
- With equal outer gains INDI reaches parity on attitude steps, not an advantage: nominal setpoint tracking is not
  where INDI is expected to win (its gain is disturbance/plant-change rejection; rate pulses 0.91x remain).
- Yaw: NOT explained by MC_YAW_P (1.26x -> 1.29x). The yaw deficit sits in the INDI yaw rate loop (K_Y 2.73 rad/s
  behind the 1.67 Hz YAW_CUT filter on the rate error, D-yawsp, vs PID ~3.6 rad/s behind 4.0 Hz). Not tested here.
- 3 seeds: indicative, not a validation result.
