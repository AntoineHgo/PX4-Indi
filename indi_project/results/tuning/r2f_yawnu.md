# r2 c11 (YAW_CUT 2 Hz) with D-yawnu firmware: tuning-set score (session 11)

Command: `python3 bench/tune.py --family indi --round-name r2f_yawnu --n-candidates 1 --seeds 1 2 3 --jobs 6
--sampler-seed 0 --span-factor 1.0 --base-params bench/params/indi_v1.params --center bench/params/indi_c11_yc2.json`
(cwd indi_project, firmware d2fb64330f). 15 flights, 0 failures.

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| PID defaults (r2) | 0.958-0.964 | | | | | |
| INDI r2 c11 (YAW_CUT 4.6, old firmware) | 1.150 | 0.821 | 0.843 | 0.875 | 0.851 | 1.018 |
| INDI c11 YAW_CUT 2, D-yawnu | 1.197 | 0.986 | 0.861 | 0.879 | 0.905 | 1.011 |

Motor-rate effort ratio to PID per scenario (min-max over seeds 1-3):

| | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|
| r2 c11 | 2.18-2.24 | 1.19-1.39 | 0.88-0.89 | 5.59-6.63 | 0.77-0.80 |
| D-yawnu | 1.07-1.12 | 1.30-1.34 | 0.89-0.95 | 6.65-7.79 | 0.79-0.79 |

## Reading

D-yawnu removed the hover effort penalty (2.2x -> 1.1x, below the 1.25
threshold) as intended, but J did not improve. Under the frozen cost, the
remaining penalty is almost all **step_yaw transient effort (~7x PID)**:
0.2 x (7 - 1) = 1.2 per step_yaw term, ~0.24 of J. INDI tracks the yaw step only
~10 % better than PID (0.90) for that effort. The yaw tracking gain shrank
from 0.85 to 0.90 with the extra rate-feedback lag. The hover ratio
(0.82 -> 0.99) is within the known hover non-repeatability.

Probable cause (not yet verified on the logs): the yaw setpoint step passes
unfiltered into nu = K_Y (r_sp - r_f) (by design, D-yawnu leaves the
setpoint unfiltered). With YAW_P 5 (PID 2.8) and the small G1_Y (7.4), the
yaw torque increment nu/G1_Y is large and pushes differential motor rates
hard. PID's 2 Hz yaw output filter smooths the same step.

Next: on step_yaw seed 1, plot or compute nu_y/G1, the yaw torque and the motor
spread around the step (`indi_terms.py` with a step window). Then let round 3
explore YAW_P and K_Y lower (span 1.5 around c11 / YAW_CUT 2) under the new
firmware, before any structural change such as a yaw setpoint pre-filter.
A pre-filter would also have to be offered to PID for fairness.
