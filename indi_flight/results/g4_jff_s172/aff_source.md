# S172 omega_ff spike at AUTO_LAND entry (read-only log analysis)

Script: `indi_flight/results/g4_jff_s172/aff_source.py` (run via `indi_project/docker/run.sh -n s172aff`).
Window: entry-2 s to entry+6 s. Entry = nav_state 18: harsh 96.017 s, quiet 95.954 s.

Harsh / quiet findings:
- trajectory_setpoint: 44.44 Hz. Acceleration is all NaN before entry (67-68 samples). After entry no NaN; velocity and position setpoints x,y are finite.
- a_ff post-entry (harsh): x min/max/std -0.96/0.13/0.135, y -2.03/2.35/0.677, z -0.43/0.61/0.244. Quiet: x std 0.004, y std 0.007, z std 0.34 (z max 1.66).
- Largest single-sample step (harsh): x 0.094 m/s^2 at +0.17 s, y 0.094 at +0.17 s. Quiet: 0.045 at +0.04 s. The step is not at entry.
- Smoothness: first-difference std (harsh x/y) 0.018/0.051 vs level std 0.135/0.677. Smooth ramp, not sample-to-sample noise.
- omega_ff peak (harsh): x 24.45 deg/s at +0.28 s, y 27.58 deg/s at +1.38 s. Quiet: x 6.65 at +0.06 s, y 2.54 at +0.21 s.
- Mean |omega_ff| in 1 s bins from entry-2 (harsh x / y): 0, 0, 6.3 / 21.1, 1.0 / 21.3, 0.3 / 4.6, 0.5 / 4.2, 0.3 / 4.0, 0.4 / 5.8. Quiet is 10x to 50x smaller (x 0.63 in the first bin, y 0.43).
- Order-of-magnitude check: 0.094 m/s^2 x 44.4 Hz / 9.81 = 0.42 rad/s = 24 deg/s, matching the harsh x peak. Estimate only, no filter or hold model.
- indi_pos_status fields: a_c, a_c_pre_inject, inject, a_f, t_f, t_c, t_c_applied, omega_ff, q_d, mean_u, thrust, blend, mean_u_valid, blend_hold, blend_frozen, jerk_source, hold_cycles, failure, stage_mode. The only jerk-related field is jerk_source, and it is 0 (FIELD) for the whole window in both runs. `jerk_source` is never assigned anywhere in `src/` at HEAD, so it carries no information.
- vehicle_local_position ax/ay std (harsh, pre/post): 1.83/1.89 and 1.83/1.95. Quiet: 0.036/0.038 and 0.036/0.039. The estimate is noisy and a_ff is smooth, so a_ff does not follow the estimate's noise.
- Check of omega_ff against the backward difference of a_ff (sample-based, no filter/hold): correlation harsh x 0.33, y -0.28; quiet about 0. The implied collective (88 m/s^2 harsh) does not match g, so the logged omega_ff is not reproduced by the current formula from the logged a_ff.

Caveat: run.json records git commit d14489a46c, which is older than 20b4a41b22 ("jerk feed-forward only from the acceleration difference"). The flights may predate that fix, so these logs may not test HEAD.

Conclusion: the spike is a sustained smooth slope of a_ff during the descent, not a single step at entry. It scales with the harsh/quiet a_ff amplitude (about 30x in x, 100x in y), and the spike magnitude matches the largest per-sample a_ff step times 44 Hz / g.
