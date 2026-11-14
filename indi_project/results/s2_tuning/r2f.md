# v2 PID tuning round r2f (FAC config) and the v2 tuned PID baseline

16 candidates x 3 seeds on the 5 tuning scenarios, v2 sim, `v2_fac.params` base, centred on r1f c05
(`bench/params/pid_r1f_c05.json`), span 1.5, sampler seed 1; script `bench/s2_pid_tune_r2f.sh`; c00 = the centre.
Ratios vs the `ref_fac` reference (PX4 defaults, seeds 1-3). Data `pid/r2f/summary.csv`. 0 failures.

| cand | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| c15 | 0.891 | 0.50 | 0.87 | 0.99 | 0.94 | 1.10 |
| c00 (= r1f c05) | 0.911 | 0.66 | 0.93 | 0.92 | 0.85 | 1.01 |
| c04 | 0.915 | 0.55 | 0.99 | 0.91 | 0.91 | 1.01 |
| c13 | 0.938 | 0.53 | 0.84 | 0.95 | 0.84 | 0.95 |

Reading:
- The centre reproduces its r1f score (0.925 on seeds 1-2, 0.911 on seeds 1-3) and its step-axis gains over the
  defaults (r1f 0.92 / 0.89 / 0.85, r2f 0.93 / 0.92 / 0.85 on roll / pitch / yaw steps): the gain is consistent, not
  seed luck.
- c15 is 2 % better in J, all of it from the hover ratio, which is noise-dominated (D-hovernoise; hover ratios of
  0.50-0.66 for nearly every candidate), and it is 10 % worse on rate pulses. Under the v1 r2 rule (a challenger
  must beat the centre by more than run-to-run noise on the tracking terms), the centre stays.
- **v2 tuned PID baseline = r1f c05 (`bench/params/pid_r1f_c05.json` on `v2_fac.params`), D-v2pid.** PX4 defaults
  (on `v2_fac.params`) stay as the second PID baseline. Tuning effort on v2 FAC: r1f 24 x 2 seeds + r2f 16 x 3
  seeds = 96 candidate-seed sets x 5 scenarios.
