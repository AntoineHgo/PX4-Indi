# Freeze-10 (S193) G5 scores

Firmware 7fe6206fcc (FREEZE-10), queue step 2 23:34-00:20 2026-11-22.

Numbers and per-row verdicts against the stated limits only; no gate verdicts. Same scripts, commands and limits as freeze9_s183/G5_SCORES.md (scored on the host, no re-run, no edits to scorers). Format: freeze-10 value per key, freeze-9 key 1 value in the last column. Freeze-9 values are the first number in freeze-9 cells (freeze-8 values in parentheses there are not repeated).

Summary of counts (both keys unless stated):
- G5.1 stick_steps: acro 3/3 PASS, stab 3/3 PASS.
- G5.2 stick_pos_steps: altctl 3/3 PASS, posctl 3/3 PASS.
- G5.3 mission 3/3 PASS (key 1 only, as freeze-9); hold 3/3 PASS.
- G5.4 auto_tour 3/3 PASS, auto_land10 3/3 PASS (key 2 on auto_land10 only).
- G5.5 offboard: 23/24 PASS, 1 FAIL (o2_circle_z s1, H RMS 0.5027 m vs 0.5; both keys agree).
- G5.7 mode_switch10: 3/3 PASS (freeze-9 3/3 FAIL).
- G5.10 stabilized full-scale (INDI only): 3/3 PASS both keys.
- G5.8 / G5.9 / G5.11 (events_s1, one flight): key 1 PASS on all scored rows; key 2 FAIL on G5.9a kill (see that section).

## G5.1 stick steps (6 rows)
Commands: `python3 indi_flight/bench/g51_check.py g5_modes/stick_steps_s<N>_<acro|stab>` (key 1, `*.key1.txt`); `python3 indi_flight/bench/g51_g52_key2.py g51 g5_modes/stick_steps_s<N>_<mode>` (key 2, `*.key2.txt`). All 12 files present and non-empty.
Limits: acro roll/pitch/yaw rate RMS <= 10 deg/s on 100 deg/s steps; stabilized level within 3 deg 1.0 s after release, yaw rate <= 10 deg/s; LOC none.

| flight | key1 worst metric | key1 verdict | key2 worst metric | key2 verdict | limit | freeze-9 key1 worst |
|---|---|---|---|---|---|---|
| stick_steps acro s1 | yaw rate RMS 1.94 deg/s (roll 1.44, pitch 1.46) | PASS | yaw 1.944 | PASS | <= 10 | yaw 1.82 |
| stick_steps acro s2 | yaw rate RMS 1.94 deg/s (roll 1.44, pitch 1.37) | PASS | yaw 1.943 | PASS | <= 10 | yaw 1.69 |
| stick_steps acro s3 | yaw rate RMS 1.81 deg/s (roll 1.42, pitch 1.45) | PASS | yaw 1.810 | PASS | <= 10 | yaw 1.91 |
| stick_steps stab s1 | tilt 0.12 deg (roll); yaw rate 0.12 deg/s | PASS | tilt 0.120; yaw rate 0.120 | PASS | tilt <= 3, rate <= 10 | pitch 0.11 |
| stick_steps stab s2 | tilt 0.11 deg (roll, pitch); yaw rate 0.14 deg/s | PASS | tilt 0.110; yaw rate 0.112 | PASS | tilt <= 3, rate <= 10 | pitch 0.15 |
| stick_steps stab s3 | tilt 0.08 deg (pitch); yaw rate 0.16 deg/s | PASS | tilt 0.079; yaw rate 0.074 | PASS | tilt <= 3, rate <= 10 | pitch 0.14 |

Count: key 1 6/6 PASS, key 2 6/6 PASS. Acro window tilt max 47.7-48.2 deg (info only). Key 2 acro also reports "excursion 9.6-12.0 m" as shared-LOC extra, not gated here.

## G5.2 stick position steps (6 rows)
Commands: `python3 indi_flight/bench/g52_check.py g5_modes/stick_pos_steps_s<N>_<altctl|posctl>` (key 1); `python3 indi_flight/bench/g51_g52_key2.py g52 g5_modes/stick_pos_steps_s<N>_<mode>` (key 2). All 12 files present and non-empty.
Limits: z step valid >= 1 m, z overshoot <= 0.3 m, z settle <= 4 s; posctl x step valid >= 2 m, x overshoot <= 0.5 m, x settle <= 4 s; LOC none. Settle band (key 1, S175 Q10 B) = max(2 % of step, 0.10 m); key 2 reports the strict 2 % band settle time, which is longer on altctl s2 (1.10 s vs 0.31 s). Both are below the 4 s limit.

| flight | key1 worst metric | key1 verdict | key2 worst metric | key2 verdict | limit | freeze-9 key1 worst |
|---|---|---|---|---|---|---|
| altctl s1 | z settle 0.26 s (2 % band 0.35); z overshoot 0.012 m | PASS | z overshoot 0.012; z settle 0.355 | PASS | <= 0.3 m, <= 4 s | z overshoot 0.005, settle 0.26 |
| altctl s2 | z settle 0.31 s (2 % band 1.10); z overshoot 0.011 m | PASS | z overshoot 0.011; z settle 1.097 (strict 2 %) | PASS | <= 0.3 m, <= 4 s | z overshoot 0.010, settle 0.29 |
| altctl s3 | z settle 0.26 s (2 % band 0.35); z overshoot 0.013 m | PASS | z overshoot 0.013; z settle 0.352 | PASS | <= 0.3 m, <= 4 s | z overshoot 0.017, settle 0.31 |
| posctl s1 | x overshoot 0.012 m, x settle 1.54 s; z overshoot 0.016 m | PASS | x overshoot 0.012, x settle 1.537; z overshoot 0.016 | PASS | <= 0.5 m, <= 4 s | x overshoot 0.014, x settle 1.30 |
| posctl s2 | x overshoot 0.066 m, x settle 1.36 s; z overshoot 0.012 m | PASS | x overshoot 0.066, x settle 1.361; z overshoot 0.012 | PASS | <= 0.5 m, <= 4 s | x overshoot 0.001, x settle 1.30 |
| posctl s3 | x overshoot 0.057 m, x settle 1.34 s; z overshoot 0.005 m | PASS | x overshoot 0.057, x settle 1.342; z overshoot 0.005 | PASS | <= 0.5 m, <= 4 s | x overshoot 0.028, x settle 1.31 |

Count: key 1 6/6 PASS, key 2 6/6 PASS. Step sizes z 1.99-2.07 m, x 4.17-4.19 m (valid).

## G5.7 mode switch, 10 edges (3 rows)
Commands: `python3 indi_flight/bench/g57_check.py --validity leaveP g5_modes/mode_switch10_s<N>` (key 1, `*.key1.txt`); `python3 indi_flight/bench/g55_g57_key2.py g57 g5_modes/mode_switch10_s<N>` (key 2, `*.key2.txt`). All 6 files present and non-empty.
Limits: thrust setpoint step <= 20 % of hover; attitude jump <= 5 deg; LOC none; 10 edges in expected order; validity (leaveP speed >= 1.5 m/s at 4 edges leaving posctl) VALID on all three.

| flight | key1 worst metric | key1 verdict | key2 worst metric | key2 verdict | limit | freeze-9 key1 verdict (key2 attitude jump) |
|---|---|---|---|---|---|---|
| mode_switch10 s1 | thrust step 4.9 %; attitude jump 3.94 deg (hold>posctl edge) | PASS | thrust 4.87 %; attitude 3.943 deg; LOC none; min speed 1.99 VALID | PASS | <= 20 %, <= 5 deg | FAIL (5.83 deg) |
| mode_switch10 s2 | thrust step 2.7 %; attitude jump 3.98 deg (4>2 edge) | PASS | thrust 2.70 %; attitude 3.982 deg; min speed 1.96 VALID | PASS | <= 20 %, <= 5 deg | FAIL (9.30 deg) |
| mode_switch10 s3 | thrust step 5.1 %; attitude jump 3.64 deg (4>2 edge) | PASS | thrust 5.13 %; attitude 3.645 deg; min speed 1.97 VALID | PASS | <= 20 %, <= 5 deg | FAIL (10.66 deg) |

Count: key 1 3/3 PASS, key 2 3/3 PASS, keys agree (attitude jump within 0.01 deg, thrust step within 0.05 %). Freeze-9 G5.7 was 3/3 FAIL on both keys; freeze-9 key 1 also reported FAIL. Worst attitude jump 3.98 deg (s2), margin 1.02 deg to the 5 deg limit; freeze-9 worst 10.66 deg.

## G5.3 mission (3 rows)
Command: `python3 indi_flight/bench/g53_mission_check.py g5/auto_tour_s<N> --json g5/auto_tour_s<N>/g53.json > g5/auto_tour_s<N>.g53.check.txt` (rc 0 x3; files present). No second key exists for the mission row (as freeze-9).
Limits: all 4 waypoints reached within 1.0 m, vmax <= 5.5 m/s.

| flight | wp min dist 1/2/3/4 (m) | vmax (m/s) | key1 verdict | freeze-9 wp min dist 1/2/3/4 (m) | freeze-9 vmax |
|---|---|---|---|---|---|
| auto_tour s1 | 0.964 / 0.889 / 0.817 / 0.004 | 5.108 | PASS | 0.954 / 0.837 / 0.933 / 0.080 | 5.198 |
| auto_tour s2 | 0.915 / 0.926 / 0.913 / 0.003 | 5.133 | PASS | 0.889 / 0.855 / 0.737 / 0.016 | 5.196 |
| auto_tour s3 | 0.929 / 0.970 / 0.839 / 0.015 | 5.123 | PASS | 0.928 / 0.919 / 0.798 / 0.002 | 5.202 |

Count: 3/3 PASS. Worst wp min dist 0.970 m (s3 wp2, limit 1.0; margin 0.030 m; freeze-9 worst 0.954 m, s1 wp1); vmax 5.133 m/s (5.5).

## G5.3 hold (3 rows)
Commands: `python3 indi_flight/bench/g53_hold_check.py g5/hold_wind_s{1,2,3} > g5/g53_hold_check.txt`; key 2 `python3 indi_flight/bench/g53_hold_key2.py g5/hold_wind_s{1,2,3} > g5/key2_g53_hold.txt` (both present).
Limit: 3-D hold RMS over [t0, t0+28 s] <= 0.3 m, nav_state 4 over the whole window.

| flight | key1 RMS / max (m) | key2 RMS / max (m) | nav | key1 / key2 | freeze-9 key1 RMS / max (m) |
|---|---|---|---|---|---|
| hold_wind s1 | 0.047 / 0.087 | 0.0472 / 0.0866 (valid yes) | [4] | PASS / PASS | 0.058 / 0.102 |
| hold_wind s2 | 0.060 / 0.107 | 0.0603 / 0.1068 (valid yes) | [4] | PASS / PASS | 0.056 / 0.093 |
| hold_wind s3 | 0.062 / 0.084 | 0.0624 / 0.0843 (valid yes) | [4] | PASS / PASS | 0.075 / 0.119 |

Count: 3/3 PASS both keys, keys agree within 0.001 m. Worst RMS 0.062 m (s3, limit 0.3); freeze-9 worst 0.075 m.

## G5.4 (6 flights: auto_tour s1-3, auto_land10 s1-3)
Commands: `python3 indi_flight/bench/auto_smoke_check.py g5/<run> --json g5/<run>/check.json > g5/<run>.check.txt` (6 flights, rc 0; no INVALID, no FAIL string in any output; "FAIL" grep empty); key 2 on auto_land10: `python3 indi_flight/bench/g54_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54.txt` and `python3 indi_flight/bench/g54_land_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54_land.txt` (rc 0).
Limits: take-off overshoot <= 0.5 m, bounce <= 0.3 m; ramp step <= 10 % hover, edge step <= 10 %, dip <= 0.3 m; touchdown vz <= 0.8 m/s, tilt <= 10 deg, re-lift <= 0.15 m; land mean vz 0.70 +-20 %; contact->disarm <= 3.0 s; RTL height error <= 1 m.

| flight | overshoot (m) | bounce (m) | ramp max / edge step (% hover) | td vz (m/s) | td tilt (deg) | re-lift (m) | land mean vz (m/s) | contact->disarm (s) | RTL err (m) | key1 | freeze-9 td vz / tilt / mean vz / RTL err |
|---|---|---|---|---|---|---|---|---|---|---|---|
| auto_tour s1 | -0.009 | 0.200 | 7.5 / 4.6 | 0.693 | 0.42 | 0.049 | 0.695 | 2.68 | 0.060 | PASS | 0.685 / 0.29 / 0.707 / 0.010 |
| auto_tour s2 | -0.075 | 0.200 | 7.5 / 4.7 | 0.709 | 0.19 | 0.050 | 0.696 | 2.69 | 0.045 | PASS | 0.710 / 0.42 / 0.703 / 0.055 |
| auto_tour s3 | -0.067 | 0.200 | 7.5 / 4.2 | 0.699 | 0.45 | 0.049 | 0.697 | 2.68 | 0.062 | PASS | 0.727 / 0.26 / 0.703 / 0.044 |
| auto_land10 s1 | -0.065 | 0.200 | 7.4 / 4.7 | 0.705 | 0.67 | 0.049 | 0.697 | 2.68 | n/a | PASS | 0.707 / 0.54 / 0.697 / n/a |
| auto_land10 s2 | -0.088 | 0.200 | 7.5 / 4.8 | 0.721 | 0.32 | 0.050 | 0.695 | 2.68 | n/a | PASS | 0.710 / 0.26 / 0.694 / n/a |
| auto_land10 s3 | -0.060 | 0.200 | 7.5 / 4.6 | 0.690 | 0.27 | 0.049 | 0.701 | 2.68 | n/a | PASS | 0.696 / 0.35 / 0.697 / n/a |

Key 2 (auto_land10 only), freeze-10: td vz 0.705 / 0.721 / 0.690 (identical to key 1), tilt 0.67 / 0.32 / 0.27 (identical), re-lift 0.049-0.050, edge step 4.69 / 4.77 / 4.62 %, land mean vz 0.691 / 0.702 / 0.702 (key 1 0.697 / 0.695 / 0.701), contact->disarm 2.68 s on all three; all PASS.

Count: key 1 6/6 PASS; key 2 (land10) 3/3 PASS. Worst: td vz 0.721 m/s (auto_land10 s2, limit 0.8; freeze-9 worst 0.727); tilt 0.67 deg (10); re-lift 0.050 (0.15); bounce 0.200 (0.3); overshoot -0.088 (0.5); ramp 7.5 % / edge 4.8 % (10 %); land mean vz 0.695-0.701 (0.56-0.84); contact->disarm 2.68 s (3.0); RTL err 0.045-0.062 m (1.0).

### G5.4 probe rows in g5_modes (not in freeze-9 table)
Commands as above with `g5_modes/<run>` paths; files auto_tour_typ_s1.check.txt, auto_tour_harsh_s1.check.txt, auto_land10_typ_s1.check.txt, plus auto_tour_{typ,harsh}_s1.g53.check.txt and key2_g54.txt / key2_g54_land.txt (auto_land10_typ_s1).

| probe | overshoot (m) | td vz (m/s) | td tilt (deg) | land mean vz (m/s) | RTL err (m) | key1 |
|---|---|---|---|---|---|---|
| auto_tour_typ s1 | -0.067 | 0.695 | 0.23 | 0.705 | 0.058 | PASS |
| auto_tour_harsh s1 | -0.106 | 0.701 | 0.27 | 0.696 | 0.026 | PASS |
| auto_land10_typ s1 | -0.093 | 0.687 | 0.14 | 0.696 (key 2 0.697) | n/a | PASS |

## G5.5 offboard o1-o7 and offb_vel_step (24 rows)
Command: `python3 indi_flight/bench/g55_check.py g55/<scenario>_s<seed> --json g55/<scenario>_s<seed>/g55.json > g55/<scenario>_s<seed>.check.txt` (24 files, rc 0). Key 2: `python3 indi_flight/bench/g55_g57_key2.py g55 g55/*_s? > g55/key2_g55.txt` (rc 0, present).
Limits (GATES.md 5b): o1-o7 H RMS <= 0.5 m, V RMS <= 0.3 m; offb_vel_step vx RMS last 3 s <= 0.2 m/s, |vx| end <= 0.1 m/s, dz max <= 0.3 m. All rows: invalid none, mc_pos_control absent in px4 log, key 2 LOC none.

| scenario | seed | key1 H / V (m) | key2 H / V (m) | key1 | key2 | freeze-9 key1 H / V (m) |
|---|---|---|---|---|---|---|
| o1_lemniscate | 1 | 0.449 / 0.098 | 0.4475 / 0.0973 | PASS | PASS | 0.444 / 0.045 |
| o1_lemniscate | 2 | 0.451 / 0.067 | 0.4515 / 0.0673 | PASS | PASS | 0.441 / 0.071 |
| o1_lemniscate | 3 | 0.444 / 0.042 | 0.4438 / 0.0416 | PASS | PASS | 0.440 / 0.084 |
| o2_circle_z | 1 | 0.503 / 0.023 | 0.5027 / 0.0229 | **FAIL** | **FAIL** | 0.488 / 0.031 |
| o2_circle_z | 2 | 0.491 / 0.082 | 0.4913 / 0.0818 | PASS | PASS | 0.497 / 0.037 |
| o2_circle_z | 3 | 0.496 / 0.033 | 0.4955 / 0.0329 | PASS | PASS | 0.499 / 0.031 |
| o3_lemniscate_gust | 1 | 0.457 / 0.054 | 0.4574 / 0.0545 | PASS | PASS | 0.472 / 0.119 |
| o3_lemniscate_gust | 2 | 0.456 / 0.074 | 0.4571 / 0.0744 | PASS | PASS | 0.464 / 0.076 |
| o3_lemniscate_gust | 3 | 0.450 / 0.103 | 0.4509 / 0.1026 | PASS | PASS | 0.464 / 0.060 |
| o4_lemniscate_payload | 1 | 0.422 / 0.065 | 0.4218 / 0.0652 | PASS | PASS | 0.409 / 0.064 |
| o4_lemniscate_payload | 2 | 0.410 / 0.066 | 0.4100 / 0.0660 | PASS | PASS | 0.398 / 0.068 |
| o4_lemniscate_payload | 3 | 0.411 / 0.033 | 0.4108 / 0.0332 | PASS | PASS | 0.416 / 0.078 |
| o5_zsine_com_shift | 1 | 0.044 / 0.044 | 0.0441 / 0.0439 | PASS | PASS | 0.038 / 0.026 |
| o5_zsine_com_shift | 2 | 0.041 / 0.026 | 0.0411 / 0.0261 | PASS | PASS | 0.042 / 0.040 |
| o5_zsine_com_shift | 3 | 0.034 / 0.025 | 0.0344 / 0.0253 | PASS | PASS | 0.040 / 0.029 |
| o6_zsine_mass | 1 | 0.051 / 0.027 | 0.0513 / 0.0269 | PASS | PASS | 0.036 / 0.036 |
| o6_zsine_mass | 2 | 0.030 / 0.033 | 0.0299 / 0.0329 | PASS | PASS | 0.047 / 0.043 |
| o6_zsine_mass | 3 | 0.043 / 0.048 | 0.0431 / 0.0479 | PASS | PASS | 0.053 / 0.080 |
| o7_lemniscate_tau2 | 1 | 0.444 / 0.096 | 0.4451 / 0.0957 | PASS | PASS | 0.439 / 0.104 |
| o7_lemniscate_tau2 | 2 | 0.431 / 0.057 | 0.4317 / 0.0575 | PASS | PASS | 0.451 / 0.047 |
| o7_lemniscate_tau2 | 3 | 0.448 / 0.036 | 0.4481 / 0.0365 | PASS | PASS | 0.438 / 0.076 |

| offb_vel_step | seed | key1 vx RMS (last 3 s) / |vx| end / dz max (m/s, m/s, m) | key2 same | key1 | key2 | freeze-9 key1 |
|---|---|---|---|---|---|---|
| offb_vel_step | 1 | 0.0067 / 0.0068 / 0.031 | 0.0066 / 0.0066 / 0.032 | PASS | PASS | 0.0087 / 0.0027 / 0.075 |
| offb_vel_step | 2 | 0.0125 / 0.0113 / 0.052 | 0.0125 / 0.0109 / 0.052 | PASS | PASS | 0.0073 / 0.0029 / 0.050 |
| offb_vel_step | 3 | 0.0133 / 0.0146 / 0.078 | 0.0132 / 0.0146 / 0.079 | PASS | PASS | 0.0082 / 0.0148 / 0.030 |

Count: key 1 23/24 PASS, key 2 23/24 PASS (the FAIL is the same row on both keys). Worst H 0.503 m (o2_circle_z s1, limit 0.5; over by 0.003 m, key 1 0.5027 / key 2 0.5027). Next worst H: o2 s2 0.491, o2 s3 0.496 (both PASS). Worst V 0.103 m (o3 s3, limit 0.3). offb worst: vx RMS 0.0133 (s3, limit 0.2), |vx| end 0.0146 (s3, limit 0.1), dz 0.079 m (s3, limit 0.3). Key 1 vs key 2 differ by at most 0.0012 m on H and 0.0002 m on V over the 21 o-rows.

## G5.10 stabilized full-scale part (INDI only, 3 rows)
Rule (unchanged from freeze-9, owner Q17 A): no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg (limit 40.0 deg); no windup = attitude error to the stick-commanded attitude <= 5 deg within 1 s after sticks return to centre. The 2.0 m alt-loss limit is not applied (full throttle climbs, ~470 m gain). PID not re-flown at freeze-10 (README: PID stab reference not re-flown); freeze-9 PID reference in freeze9_s183/g510_stab/README.md.
Command: `bash indi_flight/results/freeze10_s193/g510_stab/fly.sh indi <seed>` (scenario g510_stab_full); key 1 `*.score_key1.txt` (g510_score_motors.py), key 2 `*.score_key2.txt` (g510_motors_key2.py). All 6 score files present.

| seed | LOC | tilt_max (limit 40) key1 / key2 | att_err at 1 s after centre, key2 (limit 5) | key1 | key2 | keys agree | freeze-9 tilt_max / att_err at 1 s |
|---|---|---|---|---|---|---|---|
| INDI 1 | no | 35.39 / 35.39 | 0.18 deg | PASS | PASS | yes | 35.42 / 0.23 |
| INDI 2 | no | 35.46 / 35.46 | 0.22 deg | PASS | PASS | yes | 35.50 / 0.22 |
| INDI 3 | no | 35.50 / 35.50 | 0.24 deg | PASS | PASS | yes | 35.62 / 0.18 |

Exit status: all 3 runs "failed: wall timeout (150 s) in phase 'land'" at sim t ~671 s, after the scored window (t ~58-69 s), same as freeze-9. Validity: covered_span True, valid True, all 4 motors >= 0.99 for 0.76-0.77 s of the 1.0 s window (key 1 frac_all4_ge_0.99), motor mean in phase 0.98.
Count: 3/3 PASS both keys. Worst tilt 35.50 deg (limit 40); worst att error at 1 s 0.24 deg (limit 5).

## G5 events (hover, seed 1, one flight: events/g5_events_s1)
Commands: `python3 indi_flight/bench/g5_rows_check.py events/g5_events_s1 > events/g5_rows.txt`; `python3 indi_flight/bench/g511_check.py events/g5_events_s1 > events/g511.txt`; key 2 `python3 indi_flight/bench/g5_rows_key2.py events/g5_events_s1 > events/key2_g5rows_s1.txt` (all present, non-empty). No key 2 script for G5.11 (as freeze-9). G5.6 and G5.11 z reset: not tested (owner decision Q8(b)), as freeze-9.
Limits: as freeze-9 (G5.8 entry-timeout <= 1000 ms, action hold nav 4, excursion <= 1 m; G5.9a motors 0 within one command period 1.25 ms; G5.9b states zero at rearm; G5.9c first second <= 5 %; G5.9d edge step <= 10 % hover, dip <= 0.3 m; G5.11 xy excursion <= 0.5 m, no oscillation; yaw excess <= 1 deg, excursion <= 0.5 m).

| row | key1 value | limit | key1 verdict | key2 | freeze-9 key1 value |
|---|---|---|---|---|---|
| G5.8 rc_loss | entry-timeout 510 ms, nav 4, excursion 0.034 m | 1000 ms, 1 m | PASS | PASS (entry-ref 0.510 s) | 510 ms, 0.062 m |
| G5.8 link_loss | entry-timeout 10 ms, nav 4, excursion 0.067 m | 1000 ms, 1 m | PASS | PASS, flag only (state already hold; rise-ref 0.010 s) | 4 ms, 0.074 m |
| G5.8 offboard_loss | entry-timeout 28 ms, nav 4, excursion 0.098 m | 1000 ms, 1 m | PASS | PASS (entry-ref 0.028 s) | 24 ms, 0.096 m |
| G5.9a kill motors | outputs 0 at 0.00 ms after kill-flag rise (spacing 1.25 ms); switch -> kill flag 2.50 ms (info) | <= 1.25 ms (one command period) | PASS | **FAIL**: outputs 0 at +0.00 ms after kill rise but +2.50 ms after the switch change; key 2 references the switch | PASS (key 2 +7.50 ms after switch, freeze-9 definition difference) |
| G5.9b rearm states | states non-zero none (of 2 and of 6) | zero | PASS | states zero at arm (maxabs 0); no verdict line printed | PASS |
| G5.9c first second | 0.01 % full scale | <= 5 % | PASS | 0.93 % of full scale (W = 2700, different measure); no verdict line printed | 0.01 % (key 2 0.92 %) |
| G5.9d takeoff | step 4.7 % hover, dip 0.000 m | 10 %, 0.3 m | PASS | PASS (4.7 %, dip 0.000 m) | 4.6 %, dip 0.000 m |
| G5.11 ekf_yaw | tilt jump 0.61 deg (report), excess -0.54 deg, excursion 3-D 0.088 m, osc no | excess <= 1 deg, 0.5 m | PASS (legacy PASS) | none | tilt jump 0.86, excess -0.12, excursion 0.053 m |
| G5.11 ekf_xy | horizontal excursion 0.240 m, osc no (tilt jump 7.38 deg, reported only) | 0.5 m | PASS (legacy tilt-jump rule FAIL, as freeze-9) | none | excursion 0.236 m (tilt jump 8.14 deg) |

Count: key 1 PASS on all scored rows (G5.8 x3, G5.9a-d x4, G5.11 x2 = 9/9). Key 2: PASS on G5.8 x3 and G5.9d; G5.9a FAIL (see disagreement below); G5.9b/G5.9c have no verdict line (values within limits); G5.11 has no key 2.

## Scoring integrity
- Expected score files: all present. g5_modes: 30 key files (G5.1 6 flights x 2 keys, G5.2 6 x 2, G5.7 3 x 2), 3 probe check files, 2 probe g53 files, key2_g54 and key2_g54_land; g510_stab: 6 score files (3 x 2 keys); g5: 6 check files, 3 g53 files, g53_hold_check, key2_g53_hold, key2_g54, key2_g54_land; g55: 24 check files and key2_g55; events: g511.txt, g5_rows.txt, key2_g5rows_s1.txt.
- Empty files: none (zero-length *.stdout.log exist for the flights only; they are logs, not score files).
- Tracebacks or Python errors in score files: none. The only "error" strings are run metadata: `error None` in the auto smoke checks; `RunError: wall timeout (150 s) in phase 'land'` in the 3 g510 run.json files (outside the scored window, see G5.10). An `Error:` or Traceback match in gz.log / stdout logs was not treated as a scoring error (gz simulator logs, not score files).
- Flight warnings: fly_all.sh logged "params check failed (ID_OK/RATE_CTL_TYPE not 1)" for all 15 G5.1/G5.2/G5.7 flights. ID_OK = 1 and MC_INDI_EN = 1 are in each run.json; RATE_CTL_TYPE is absent (None) from params_applied. Same WARN pattern in freeze-9 (15 of 15). Flights kept and scored.
- Key disagreement: G5.9a kill motors (key 1 PASS, key 2 FAIL, reference differs: kill-flag rise vs switch change, +2.50 ms). No other row where key 1 and key 2 disagree on a verdict. Definition-only differences, both PASS: G5.2 settle band (key 1 gate band vs key 2 strict 2 %), G5.9c measure.
- Side effect: `indi_flight/results/g5_events_s145/key2_rows.md` shows as modified in git (same hardcoded-path overwrite as freeze-9, from g5_rows_key2.py). Not restored here.

## Rows not re-flown at freeze-10
G5.6 false maybe_landed and G5.11 z reset: not tested (owner decision Q8(b)). G5.10 SAT part: not in this queue (Q21 status as freeze-9). G5.10 PID reference: not re-flown. Freeze-9 values in the columns above are for comparison only.
