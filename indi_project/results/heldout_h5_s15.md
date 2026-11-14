# H5 mismatch_combined: 10 seeds per controller, and diagnosis (session 15)

Frozen candidates: PID = PX4 defaults, INDI = `results/tuning/indi/r4f/c00/params` (D-freeze). Plant: gz x500 with
Ixx, Iyy, Izz x0.8, mass x1.15 (2.3 kg, read back from gz), motor timeConstantUp/Down x2 (0.025/0.05 s), controllers
unchanged (D-h5). Speed 4 (attitude/rate metrics, D-speed). Logs: `results/h5_s15.log`, `results/diag_h5_s15.log`.
Position rows are meaningless in attitude/rate mode (no position hold) and are ignored.

## Result: INDI loses H5

Roll-rate RMS (rad/s, mean ± std over 10 seeds, paired by seed; from `metrics.json` rate_tracking):

| run | PID | INDI | ratio | INDI lower |
|---|---|---|---|---|
| mismatch_combined_att (T2 pattern) | 0.0883 ± 0.0018 | 0.340 ± 0.039 | 3.86 | 0/10 |
| mismatch_combined_rate (T4 pattern, primary metric of T4) | 0.356 ± 0.004 | 0.562 ± 0.006 | 1.58 | 0/10 |

Roll attitude RMS on the T2 pattern is still lower for INDI (2.97 vs 3.27 deg, 10/10, p 0.002), but only because the
steps dominate it: INDI carries a sustained roll oscillation, and motor-rate effort is 3.1x PID (1.92 vs 0.62 /s).
On the T4 pattern INDI saturates 3.4 % of the window vs 1.6 %. Full tables from `bench/summarize_seeds.py`:


### mismatch_combined_att (pid_default n=10, indi_tuned n=10, paired 10)

| metric | pid_default | indi_tuned | ratio b/a | b<a | med impr | p |
|---|---|---|---|---|---|---|
| att rot rms deg | 3.27 ± 0.077 | 2.98 ± 0.075 | 0.91 | 10/10 | 10 % | 0.00195 |
| roll rms deg | 3.27 ± 0.077 | 2.97 ± 0.073 | 0.91 | 10/10 | 10 % | 0.00195 |
| pitch rms deg | 0.0547 ± 0.0034 | 0.0315 ± 0.014 | 0.58 | 10/10 | 41 % | 0.00195 |
| yaw rms deg | 0.133 ± 0.028 | 0.148 ± 0.074 | 1.11 | 5/10 | -3 % | 0.625 |
| pos rms horiz m | 19.5 ± 0.14 | 20 ± 0.23 | 1.03 | 1/10 | -3 % | 0.00391 |
| pos max dev 3d m | 29.9 ± 0.15 | 30.7 ± 0.26 | 1.03 | 0/10 | -3 % | 0.00195 |
| motor rate rms /s | 0.623 ± 0.094 | 1.92 ± 0.24 | 3.08 | 0/10 | -232 % | 0.00195 |
| sat frac | 0 ± 0 | 0 ± 0 | nan | 0/10 | - | 1 |

### mismatch_combined_rate (pid_default n=10, indi_tuned n=10, paired 10)

| metric | pid_default | indi_tuned | ratio b/a | b<a | med impr | p |
|---|---|---|---|---|---|---|
| att rot rms deg | 17.9 ± 0.35 | 19.3 ± 0.61 | 1.08 | 0/10 | -8 % | 0.00195 |
| roll rms deg | 17.7 ± 0.26 | 19.3 ± 0.62 | 1.09 | 0/10 | -10 % | 0.00195 |
| pitch rms deg | 0.728 ± 0.058 | 0.127 ± 0.048 | 0.17 | 10/10 | 83 % | 0.00195 |
| yaw rms deg | 2.49 ± 0.79 | 1.08 ± 0.71 | 0.43 | 9/10 | 61 % | 0.00391 |
| pos rms horiz m | 61.7 ± 2.7 | 81.5 ± 6.5 | 1.32 | 0/10 | -33 % | 0.00195 |
| pos max dev 3d m | 123 ± 5.6 | 173 ± 15 | 1.41 | 0/10 | -42 % | 0.00195 |
| motor rate rms /s | 3.34 ± 0.037 | 3.64 ± 0.034 | 1.09 | 0/10 | -8 % | 0.00195 |
| sat frac | 0.0164 ± 0.00016 | 0.0338 ± 0.00085 | 2.06 | 0/10 | -105 % | 0.00195 |

## Diagnosis (diagnostic scenarios `diag_h5_*` in `bench/scenarios.py`, INDI only, seeds 1-2, never used for tuning)

Roll-rate standard deviation over the level-hold segment `zero1` (last 2 s), and its dominant frequency:

| plant | INDI ACT_TC | hover roll-rate std (rad/s) | peak | roll-rate RMS (window) |
|---|---|---|---|---|
| H5 combined, seed 1 | 0.0114 (frozen) | 0.256 | 6.5 Hz | 0.34 |
| PID on H5 combined, seed 1 | - | 0.001 | - | 0.088 |
| T9 inertia x1.3 (INDI, seed 1) | 0.0114 | 0.002 | - | - |
| inertia x0.8 + mass x1.15 only | 0.0114 | 0.002 | - | 0.117 |
| motor time constants x2 only | 0.0114 | 0.267 / 0.278 | 5.2 / 5.6 Hz | 0.332 / 0.344 |
| motor time constants x2 only | 0.0228 (matched x2) | 0.004 / 0.004 | - | 0.191 / 0.191 |

Cause: the motor-lag mismatch alone. INDI computes the torque increment against an actuator-state estimate built from a
first-order actuator model (MC_INDI_ACT_TC). When the real motors are twice as slow, the modelled actuator state leads
the real one, so the synchronisation between the actuator-state and angular-acceleration filters (the core
assumption of incremental control) is broken, the loop under-counts the lag it is acting through, and at the frozen
K_R 23.9 rad/s it settles into a 5-7 Hz limit cycle. With ACT_TC matched to the new plant the oscillation disappears
(the remaining extra rate error comes from the slower actuator itself). Inertia and mass errors, which only scale G1,
are tolerated. This is the failure mode the literature predicts (actuator dynamics must be known or measured, e.g.
via RPM feedback); PID, which has no actuator model, degrades gracefully.

The matched-ACT_TC run is a diagnosis, not a retune: the held-out result stays the frozen-candidate result above.
Implication for real flight: identify the motor time constant on the vehicle, or use ESC RPM telemetry as the
actuator state, before relying on INDI; a robustness margin on ACT_TC (or a lower K_R) is a design trade not yet
evaluated.
