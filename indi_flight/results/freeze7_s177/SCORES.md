# freeze-7 (S177) re-score

Commands (existing checkers only):
- G5.5: the `<name>.check.txt` files in g55/ (JSON from the g55 checker, G5.5 exact test in GATES.md 5b: o1-o7 H RMS <= 0.5 m, V RMS <= 0.3 m; offb_vel_step vx RMS last 3 s <= 0.2, |vx| end <= 0.1, dz max <= 0.3). Not re-run.
(G4 and G5.3/G5.4 commands are listed in their sections.)

## G5.5 (24 flights, all valid, no invalid flags, mc_pos_control absent)
| scenario | seed | metrics (m, m/s) | verdict | invalid |
|---|---|---|---|---|
| o1_lemniscate | 1 | H 0.303 / V 0.039 | PASS | - |
| o1_lemniscate | 2 | H 0.293 / V 0.085 | PASS | - |
| o1_lemniscate | 3 | H 0.311 / V 0.037 | PASS | - |
| o2_circle_z | 1 | H 0.273 / V 0.077 | PASS | - |
| o2_circle_z | 2 | H 0.268 / V 0.061 | PASS | - |
| o2_circle_z | 3 | H 0.274 / V 0.053 | PASS | - |
| o3_lemniscate_gust | 1 | H 0.303 / V 0.064 | PASS | - |
| o3_lemniscate_gust | 2 | H 0.309 / V 0.034 | PASS | - |
| o3_lemniscate_gust | 3 | H 0.323 / V 0.060 | PASS | - |
| o4_lemniscate_payload | 1 | H 0.292 / V 0.097 | PASS | - |
| o4_lemniscate_payload | 2 | H 0.284 / V 0.087 | PASS | - |
| o4_lemniscate_payload | 3 | H 0.288 / V 0.035 | PASS | - |
| o5_zsine_com_shift | 1 | H 0.046 / V 0.054 | PASS | - |
| o5_zsine_com_shift | 2 | H 0.033 / V 0.026 | PASS | - |
| o5_zsine_com_shift | 3 | H 0.039 / V 0.038 | PASS | - |
| o6_zsine_mass | 1 | H 0.024 / V 0.029 | PASS | - |
| o6_zsine_mass | 2 | H 0.040 / V 0.025 | PASS | - |
| o6_zsine_mass | 3 | H 0.031 / V 0.029 | PASS | - |
| o7_lemniscate_tau2 | 1 | H 0.304 / V 0.094 | PASS | - |
| o7_lemniscate_tau2 | 2 | H 0.291 / V 0.079 | PASS | - |
| o7_lemniscate_tau2 | 3 | H 0.298 / V 0.086 | PASS | - |
| offb_vel_step | 1 | vx_rms 0.003 / vx_end 0.005 / dz 0.127 | PASS | - |
| offb_vel_step | 2 | vx_rms 0.005 / vx_end 0.018 / dz 0.111 | PASS | - |
| offb_vel_step | 3 | vx_rms 0.004 / vx_end 0.010 / dz 0.086 | PASS | - |
Worst: o1 s3 H 0.311, o3 s3 H 0.323 (limit 0.5), max V 0.097 (o4 s1, limit 0.3); offb_vel_step worst vx_rms 0.005 (0.2), vx_end 0.018 (0.1), dz 0.127 (0.3). 24/24 PASS. Freeze-6 probe o1 s1 0.297 m; freeze-7 o1 s1 0.303 m.
