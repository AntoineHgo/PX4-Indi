# G5 re-score with the S175 owner amendments (S176, no flights)

Evidence: g5_freeze_s157 (firmware of the freeze) and g511_fix_s161 (firmware d1b65d0f09). Numbers only, no gate verdicts.
Amended checkers are UNREVIEWED until the independent review. All commands: `bash indi_flight/results/g5_rescore_s176/rescore.sh`
(repo root; each line runs `indi_project/docker/run.sh -n s176rs -t 600 -- python3 indi_flight/bench/<checker> --out/--json <here> <run dirs>`;
outputs are written here, never into the run dirs). Raw output: g52_rescore.txt, g5_rows_freeze.txt, g5_rows_s161.txt,
g510_sat_sustained_s{1,2,3}.txt, g511_s161.txt, g511_freeze.txt, plus json folders g52/ g5_rows_*/ g511/ g511_freeze/.
Sanity: with the old 2 % band the new code reproduces the old z settle exactly (posctl s1 4.15 s, s2/s3 0.36/0.35 s).

## Table (old = pre-S175 checker output in the freeze/S161 READMEs; new = this folder)
| row | run | old | new | threshold |
|---|---|---|---|---|
| G5.2 altctl z settle | stick_pos_steps_s1/s2/s3_altctl | 0.35/0.35/0.35 s PASS | 0.26/0.25/0.26 s PASS (band 0.100 m) | <= 4 s, band max(2 % d, 0.10 m); os 0.023/0.009/0.020 m <= 0.3 |
| G5.2 posctl z settle | stick_pos_steps_s1_posctl | 4.15 s FAIL | 0.22 s PASS (band 0.100 m, d 1.96 m) | <= 4 s |
| G5.2 posctl z settle | s2_posctl / s3_posctl | 0.36 / 0.35 s PASS | 0.27 / 0.26 s PASS | <= 4 s |
| G5.2 posctl x settle (band stays 2 % d) | s1 / s2 / s3 | 3.20 / 3.34 / 3.32 s PASS | unchanged 3.20 / 3.34 / 3.32 s PASS | <= 4 s, os <= 0.5 m (0.092/0.099/0.103) |
| G5.2 PID reference | stick_pos_steps_s1_posctl_pid | z 3.39 s PASS | z 0.38 s PASS | <= 4 s |
| G5.9a motors 0 from kill flag | freeze g5_events_s1/s2/s3 | s1 FAIL (3.75 ms after switch), s2/s3 PASS | outputs 0 at 0.00 ms after actuator_armed.kill rise, all 3 PASS (sample spacing 1.25 ms) | <= 1.25 ms |
| G5.9a commander latency (info) switch -> kill flag | freeze s1/s2/s3 | 3.75 / 1.25 / 1.25 ms | 3.75 / 1.25 / 1.25 ms (event applied -> kill flag 40.00 / 49.50 / 32.50 ms) | reported only |
| G5.9a motors 0 from kill flag | g511_fix_s161 g5_events_s1/s2/s3 | s1, s3 FAIL (8.75 / 6.25 ms after switch), s2 PASS | 0.00 ms after kill rise, all 3 PASS | <= 1.25 ms |
| G5.9a commander latency (info) | s161 s1/s2/s3 | 8.75 / 1.25 / 6.25 ms | 8.75 / 1.25 / 6.25 ms (applied -> kill flag 37.00 / 37.75 / 38.75 ms) | reported only |
| G5.10 tilt (limit MPC_TILTMAX_AIR 45 + 5 = 50 deg, read from log) | sat_sustained_s1/s2/s3 | 45.3 deg vs 20 deg FAIL | 45.31 / 45.34 / 45.32 deg PASS | <= 50 deg |
| G5.10 alt loss, recovery (unchanged) | same | 1.76/1.76/1.77 m PASS; back_sat PASS (1.95/1.63/1.83 s) | same | <= 2.0 m, <= 5 s |
| G5.10 other | same | INVALID (AGG part saturation fraction 0.0), back_agg FAIL (never back) | unchanged INVALID, back_agg FAIL | out of scope: new SAT / stabilized flights |
| G5.11 xy | g511_fix_s161 s1/s2/s3 | tilt jump 5.81/6.24/6.74 deg FAIL | horizontal truth excursion 0.209 / 0.155 / 0.197 m, osc none: PASS (tilt jump reported only) | horizontal excursion <= 0.5 m, no oscillation |
| G5.11 yaw | g511_fix_s161 s1/s2/s3 | jump 0.76/1.21/0.83 deg: PASS/FAIL/PASS | excess = jump - no-event p95 (0.77/1.02/1.22) = -0.01 / 0.19 / -0.39 deg: all PASS (excursion 0.051/0.060/0.100 m, osc none) | excess <= 1 deg |
| G5.11 xy / yaw, freeze firmware (pre-fix, supplementary) | g5_freeze_s157 g5_events_s1/s2/s3 | xy FAIL 3/3; yaw 1.94/1.78/1.84 FAIL 3/3 | xy PASS 3/3 (excursion 0.193/0.154/0.158 m); yaw excess 1.14 / 0.76 / 0.87 deg = FAIL / PASS / PASS | as above |
| G5.11 PID reference | g5_events_s1_pid | xy 7.82 deg FAIL, yaw 0.48 PASS | xy excursion 0.181 m PASS; yaw excess -0.35 deg PASS | as above |
| G5.11 z reset | all | (not computed) | not tested, owner decision Q8(b) | - |
| G5.6 false maybe_landed | all | NOT TESTED | not tested, owner decision Q8(b) | - |

No-event definition (G5.11 yaw): instants on a 0.25 s grid in the same flight with nav_state constant (= the event's, 4) over +-1 s and
no event applied time within [t_ev - 2 s, t_ev + 10 s]; metric = the same tilt_jump_deg (max angle over [t, t+1 s] of the attitude
setpoint body z vs its mean over [t-1, t)); n = 51-63 instants per flight, p95 and max are in g511_*.txt. Pre-S175 verdict is kept
as "legacy" in the g511 line; the 2 % z settle as "2%-band" in the g52 line.

## Code changes
- bench/g52_check.py: `step_metrics` (z band max(2 % d, 0.10 m), new keys settle_band_m, settle_s_2pct), `line`, `check`/`__main__` (`--out DIR`).
- bench/g5_rows_check.py: `g59a` (reference = actuator_armed.kill rise, fallback kill_switch change; new row "G5.9a commander latency (info)"), `main` (`--out DIR`).
- bench/g510_check.py: `analyse` (tilt_lim_deg arg, default legacy 20), `main` (reads MPC_TILTMAX_AIR from the log, + TILT_MARGIN_DEG 5; legacy flag reported as tilt_ok_legacy_20deg).
- bench/g511_check.py: new `excursion_h_m`, `noevent_tilt_jumps`, `noevent_p95`, `verdict_s175`; `check_run` (new fields, new verdict, `--out`), `line`. Old `verdict` kept as "legacy". Oscillation detector and validity unchanged.
- bench/tests: test_g52_check.py (test_z_band_floor_s175, test_pass_known_values updated), test_g5_rows_check.py (test_g59a_kill_flag_reference_s175), test_g510_check.py (tilt limit asserts), test_g511_check.py (test_excursion_h_and_verdict_s175, test_noevent_p95_excess_s175).
- Tests: 25 passed in Docker (g52, g5_rows, g510, g511, g5_events). Each new rule was broken once and the matching test failed (z band floor 0, G5.9a switch reference, G5.10 legacy limit, G5.11 xy 3-D excursion, G5.11 p95 -> median).

## Unverified / not scorable
- G5.9a: "MAVLink kill command -> kill flag" is measured from the kill_switch change in manual_control_switches (RC-style switch the injector sets) and from the event applied time; no MAVLink command timestamp is logged.
- G5.10: new SAT / stabilized flights not in scope; existing sat_sustained logs stay INVALID (AGG not saturating). Older g5_g510_s147..151 probe dirs not re-scored.
- G5.11 yaw: the first-event yaw tilt excess uses 51-63 grid instants that overlap each other (0.25 s grid, 2 s windows); p95 is of correlated samples.
- G5.2 / G5.9a checkers keep the existing key2 checkers (g51_g52_key2.py etc.) unamended: they still encode the old rules.
