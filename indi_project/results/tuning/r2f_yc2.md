# Follow-up to r2: INDI c11 with the yaw cut-off matched to PID (session 11)

Question (r2.md, "Next"): does INDI's hover effort excess disappear when
`MC_INDI_YAW_CUT` equals PID's `MC_YAW_TQ_CUTOFF` default (2 Hz)?

Run: `python3 bench/tune.py --family indi --round-name r2f_yc2 --n-candidates 1
--seeds 1 2 3 --jobs 6 --sampler-seed 0 --span-factor 1.0 --base-params
bench/params/indi_v1.params --center bench/params/indi_c11_yc2.json`
(c11 gains, YAW_CUT 2 Hz instead of 4.6 Hz; 15 flights, 0 failures, same
pid_default references as r2).

## Cost

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| c11, YAW_CUT 4.6 (r2) | 1.150 | 0.821 | 0.843 | 0.875 | 0.851 | 1.018 |
| c11, YAW_CUT 2.0 | 1.182 | 0.968 | 0.839 | 0.876 | 0.857 | 1.008 |

Step tracking is unchanged (including yaw, so the extra yaw lag costs
nothing measurable). The J difference is the hover ratio, which r1/r2 showed
to vary up to 2x between re-flights of the same seed: not significant.

## Hover effort (seeds 1-3; `bench/effort_axes.py`, `bench/indi_terms.py`)

| | yaw tq std | yaw tq drms | motor-rate RMS (1/s) |
|---|---|---|---|
| PID defaults (r2 c00, seed 1) | 0.0003 | 0.0000 | 0.037 |
| INDI c11, YAW_CUT 4.6 | 0.0009-0.0010 | 0.0003 | 0.081-0.084 |
| INDI c11, YAW_CUT 2.0 | 0.0005-0.0007 | 0.0003 | 0.077-0.080 |

Yaw torque std drops by a third, but its sample-to-sample change (drms),
which is what the motor-rate effort measures, does not move, and effort
stays ~2.1x PID's.

Term split of the yaw increment (seed 1, std/drms, normalised torque):

| YAW_CUT | nu/G1 | a_f/G1 | increment |
|---|---|---|---|
| 4.6 | 0.00085/0.00028 | 0.00110/0.00018 | 0.00110/0.00030 |
| 2.0 | 0.00069/0.00028 | 0.00060/0.00004 | 0.00058/0.00027 |

## Interpretation

The 2 Hz cut removes the a_f chatter (drms 0.00018 -> 0.00004), as designed.
The remaining chatter is the nu term: nu = K_Y (r_sp - r) uses the gyro rate
unfiltered by YAW_CUT (`indi_rate_control.cpp:210`), so gyro noise reaches
the yaw torque with gain K_Y/G1_Y = 5.83/7.4 = 0.79, against PID's yaw
P = 0.2 followed by a 2 Hz output filter. In other words INDI's yaw loop has
~4x PID's proportional gain in torque units, unfiltered; that is a
bandwidth/noise trade, not a synchronisation defect. Roll/pitch increment
drms (0.00017) is a_f-dominated and only ~1.5x PID's.

Unaffected by this follow-up: the r2 conclusion (PID wins under the frozen
cost) stands. Decision on the fix: DECISIONS.md D-yawnu.
