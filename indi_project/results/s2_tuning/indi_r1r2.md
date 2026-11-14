# v2 INDI tuning rounds r1 and r2 (O-11 build, FAC config, identified G1/ACT_TC)

Same budget and cost as the v2 PID rounds (r1f 24 x 2 seeds, r2f 16 x 3 seeds): r1 = 24 candidates x 2 seeds,
sampler seed 0, span 2.0, centre `bench/params/indi_v2_start.params` (D-v2indi-start), script
`bench/s2_indi_tune_r1.sh`; r2 = 16 x 3 seeds centred on the r1 best (`bench/params/indi_v2_r1_best.json`),
script `bench/s2_indi_tune_r2.sh`. Search space (D-v2indi-tune): K_R, K_P, K_Y, YAW_CUT, ROLL_P, PITCH_P,
YAW_P. G1 174/174/12.2, ACT_TC 0.0125 s, ERPM_DLY 1 are identified and never tuned (owner review of v1).
Ratios are vs PID defaults on the FAC config (`ref_fac`); J = mean ratio + 0.2 (effort ratio - 1) above 1.25.
Raw tables: `indi/r1/summary.csv`, `indi/r2/summary.csv`.

## r1 (240 flights, 1 failure: c12)

| cand | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| c09 | 0.938 | 0.63 | 0.99 | 0.96 | 1.11 | 0.88 |
| c05 | 0.971 | 0.67 | 0.94 | 0.83 | 1.29 | 0.97 |
| c16 | 1.011 | 0.75 | 1.08 | 1.10 | 1.02 | 0.93 |
| c00 (start) | 1.251 | 2.13 | 0.89 | 0.96 | 1.25 | 0.96 |

c00's J is dominated by one hover excursion (D-hovernoise) and by roll effort (session 39 note).

## r2 (240 flights, 0 failures)

| cand | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| c01 | 0.933 | 0.61 | 1.09 | 0.96 | 1.08 | 0.92 |
| c11 | 0.940 | 0.56 | 1.02 | 0.97 | 1.16 | 0.92 |
| c10 | 0.978 | 0.55 | 1.12 | 0.99 | 1.22 | 0.87 |
| c00 (= r1 c09) | 0.985 | 0.70 | 0.99 | 0.96 | 1.12 | 0.91 |

Motor-rate effort ratio vs PID defaults (mean of 3 seeds; tuned PID = r2f c00 = r1f c05 for comparison):

| scenario | r2 c00 | r2 c01 | r2 c11 | tuned PID |
|---|---|---|---|---|
| hover | 1.15 | 0.77 | 0.83 | 0.58 |
| step_roll | 1.54 | 0.86 | 1.15 | 1.13 |
| step_pitch | 1.08 | 0.90 | 1.00 | 0.95 |
| step_yaw | 1.06 | 1.17 | 1.34 | 1.95 |
| rate_step_roll | 1.52 | 0.92 | 0.98 | 0.87 |

## Choice (D-v2indi)

v2 tuned INDI = **r2 c01** (`bench/params/indi_v2_tuned.params`: K_R 28.77, K_P 16.76, K_Y 2.733, YAW_CUT 1.665,
ROLL_P 3.167, PITCH_P 5.19, YAW_P 2.757). Lowest J in r2, no effort penalty on any scenario. The r1 best (re-flown
as r2 c00, 0.938 -> 0.985 on 3 seeds) pays the effort penalty on roll steps and rate pulses (1.5x PID defaults);
its 0.10 better step_roll ratio does not outweigh that under the frozen cost. c01's lead over c00 is not a hover-only
gain (the D-v2pid rule): it comes from effort (roll axis) and yaw.

On the tuning set, tuned INDI (J 0.933) and tuned PID (r2f J 0.911) are within the hover noise of each other. INDI
is better on rate pulses (0.92 vs 1.01), equal on pitch steps, worse on roll steps (1.09 vs 0.93) and yaw steps
(1.08 vs 0.85). This is a "seen" comparison; the verdict comes from the held-out set V (`results/s2_heldout_v2/`).
No round 3, same stopping rule as v1 r2 and as the v2 PID.
