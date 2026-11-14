# v2 PID tuning round r1f (FAC config, D-omega2)

24 candidates x 2 seeds on the 5 tuning scenarios, v2 sim, `v2_fac.params` base (THR_MDL_FAC 0.683), sampler seed 0,
span 2.0; script `bench/s2_pid_tune_r1f.sh`; c00 = PX4 defaults. Ratios are vs the `ref_fac` reference (defaults).

| cand | J | failures | ratio_hover | ratio_step_roll | ratio_step_pitch | ratio_step_yaw | ratio_rate_step_roll |
|---|---|---|---|---|---|---|---|
| c05 | 0.925 | 0 | 0.728 | 0.925 | 0.894 | 0.847 | 0.999 |
| c00 | 0.966 | 0 | 0.798 | 0.996 | 1.001 | 1.005 | 0.998 |
| c09 | 0.995 | 0 | 0.708 | 0.957 | 1.231 | 1.060 | 0.850 |
| c07 | 1.005 | 0 | 0.760 | 0.872 | 1.176 | 1.027 | 0.820 |
| c12 | 1.007 | 0 | 0.816 | 1.104 | 1.034 | 1.028 | 1.054 |
| c01 | 1.013 | 0 | 0.636 | 1.139 | 0.827 | 1.114 | 0.857 |

Best c05 J 0.925 vs defaults 0.966 (-4 %). Unlike the earlier v2 rounds, the gain is not hover only: c05 step ratios
0.92/0.89/0.85 (roll/pitch/yaw), rate step 1.00. Two seeds and a hover term known to be noisy (D-hovernoise) do not
decide it: round r2f (16 x 3 seeds centred on c05, `bench/params/pid_r1f_c05.json`) is queued, as in v1 r2. The v2
`pid_tuned` is chosen after r2f with the v1 noise rule.
