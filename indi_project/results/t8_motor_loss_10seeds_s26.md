# T8 motor loss, 10 seeds (session 26)

Seeds 4-10 were flown in session 14 (commit c883907c92 batch) with the same firmware and the same frozen INDI
candidate (`results/tuning/indi/r4f/c00/params`) as seeds 1-3: `git diff 553c4dbdd0 c883907c92 -- src msg ROMFS Tools`
is empty. They were on disk but never summarised; the report used seeds 1-3 only (review s25 item 1).
Not a new experiment: a summary of existing runs.

## Whole-window metrics (`python3 bench/summarize_seeds.py results/runs motor_loss_0`)

### motor_loss_0 (pid_default n=10, indi_tuned n=10, paired 10)

| metric | pid_default | indi_tuned | ratio b/a | b<a | med impr | p |
|---|---|---|---|---|---|---|
| att rot rms deg | 9.06 ± 0.086 | 10.3 ± 0.054 | 1.14 | 0/10 | -13 % | 0.00195 |
| roll rms deg | 0.715 ± 0.0011 | 0.0816 ± 0.0009 | 0.11 | 10/10 | 89 % | 0.00195 |
| pitch rms deg | 0.684 ± 0.0015 | 0.155 ± 0.0013 | 0.23 | 10/10 | 77 % | 0.00195 |
| yaw rms deg | 9.01 ± 0.087 | 10.3 ± 0.054 | 1.14 | 0/10 | -14 % | 0.00195 |
| pos rms horiz m | 4.68 ± 0.21 | 0.31 ± 0.12 | 0.07 | 10/10 | 94 % | 0.00195 |
| pos max dev 3d m | 7.84 ± 0.37 | 2.03 ± 0.04 | 0.26 | 10/10 | 74 % | 0.00195 |
| motor rate rms /s | 0.391 ± 0.0025 | 0.508 ± 0.0025 | 1.30 | 0/10 | -30 % | 0.00195 |
| sat frac | 0.0756 ± 0.00097 | 0.121 ± 0.0023 | 1.60 | 0/10 | -59 % | 0.00195 |

## Fault-window metrics (`motor_fault` block of each `metrics.json`, mean and min-max over seeds 1-10)

| controller | peak tilt error deg | attitude RMS deg (fault window) | saturation time s | faulty motor at high limit s |
|---|---|---|---|---|
| PID | 5.13 (5.11-5.16) | 1.118 (1.116-1.121) | 1.74 (1.73-1.76) | 1.55 (1.54-1.57) |
| INDI | 1.62 (1.61-1.64) | 0.197 (0.194-0.199) | 2.78 (2.72-2.88) | 2.13 (2.07-2.22) |

INDI is lower than PID on fault-window attitude RMS and peak tilt in 10/10 seeds (exact paired Wilcoxon p = 0.002,
the floor for n = 10); ratios 0.18 and 0.32. INDI saturates longer in 10/10 seeds. The 3-seed values of
`t8_motor_loss_s13.md` are unchanged; seed spread stays negligible (the fault is deterministic).
