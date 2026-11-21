# Freeze-9 (S183) G5 scores

Numbers and per-row verdicts against the stated limits only; no gate verdicts. Same scripts, commands and limits as freeze8_s181/G5_SCORES.md (indi_flight/bench, no edits, no new metric code), run on the host (pyulog), repo root, no Docker. Checkers wrote their own json (g55.json, g53.json, check.json) into the run dirs as at freeze-8. Firmware difference vs freeze-8: MC_INDI_XY_VP default 2.4 (was 3.6). All queue items rc 0. Format: freeze-9 value (freeze-8 value).

## G5.5 (24 rows)
Command: `python3 indi_flight/bench/g55_check.py g55/<scenario>_s<seed> --json g55/<scenario>_s<seed>/g55.json > g55/<scenario>_s<seed>.check.txt` (24 files, rc 0 all). Key2: `python3 indi_flight/bench/g55_g57_key2.py g55 g55/*_s? > g55/key2_g55.txt` (rc 0).
Limits (GATES.md 5b): o1-o7 H RMS <= 0.5 m, V RMS <= 0.3 m; offb_vel_step vx RMS last 3 s <= 0.2 m/s, |vx| end <= 0.1 m/s, dz max <= 0.3 m. All rows: invalid none, mc_pos_control absent in px4 log, key2 LOC none.

| scenario | seed | key1 | key2 | key1 verdict | key2 verdict |
|---|---|---|---|---|---|
| o1_lemniscate | 1 | H 0.444 / V 0.045 (H 0.302 / V 0.041) | H 0.4450 / V 0.0450 (H 0.3015 / V 0.0413) | PASS | PASS |
| o1_lemniscate | 2 | H 0.441 / V 0.071 (H 0.303 / V 0.078) | H 0.4414 / V 0.0712 (H 0.3029 / V 0.0781) | PASS | PASS |
| o1_lemniscate | 3 | H 0.440 / V 0.084 (H 0.300 / V 0.051) | H 0.4397 / V 0.0842 (H 0.2996 / V 0.0506) | PASS | PASS |
| o2_circle_z | 1 | H 0.488 / V 0.031 (H 0.302 / V 0.096) | H 0.4880 / V 0.0307 (H 0.3018 / V 0.0962) | PASS | PASS |
| o2_circle_z | 2 | H 0.497 / V 0.037 (H 0.313 / V 0.044) | H 0.4967 / V 0.0371 (H 0.3128 / V 0.0446) | PASS | PASS |
| o2_circle_z | 3 | H 0.499 / V 0.031 (H 0.302 / V 0.069) | H 0.4984 / V 0.0314 (H 0.3022 / V 0.0694) | PASS | PASS |
| o3_lemniscate_gust | 1 | H 0.472 / V 0.119 (H 0.317 / V 0.052) | H 0.4715 / V 0.1192 (H 0.3172 / V 0.0524) | PASS | PASS |
| o3_lemniscate_gust | 2 | H 0.464 / V 0.076 (H 0.320 / V 0.067) | H 0.4648 / V 0.0757 (H 0.3195 / V 0.0673) | PASS | PASS |
| o3_lemniscate_gust | 3 | H 0.464 / V 0.060 (H 0.322 / V 0.065) | H 0.4643 / V 0.0602 (H 0.3219 / V 0.0651) | PASS | PASS |
| o4_lemniscate_payload | 1 | H 0.409 / V 0.064 (H 0.277 / V 0.035) | H 0.4095 / V 0.0637 (H 0.2768 / V 0.0347) | PASS | PASS |
| o4_lemniscate_payload | 2 | H 0.398 / V 0.068 (H 0.283 / V 0.042) | H 0.3975 / V 0.0675 (H 0.2824 / V 0.0415) | PASS | PASS |
| o4_lemniscate_payload | 3 | H 0.416 / V 0.078 (H 0.278 / V 0.070) | H 0.4163 / V 0.0785 (H 0.2784 / V 0.0698) | PASS | PASS |
| o5_zsine_com_shift | 1 | H 0.038 / V 0.026 (H 0.041 / V 0.046) | H 0.0376 / V 0.0260 (H 0.0410 / V 0.0456) | PASS | PASS |
| o5_zsine_com_shift | 2 | H 0.042 / V 0.040 (H 0.035 / V 0.026) | H 0.0417 / V 0.0395 (H 0.0349 / V 0.0259) | PASS | PASS |
| o5_zsine_com_shift | 3 | H 0.040 / V 0.029 (H 0.048 / V 0.035) | H 0.0404 / V 0.0288 (H 0.0482 / V 0.0350) | PASS | PASS |
| o6_zsine_mass | 1 | H 0.036 / V 0.036 (H 0.047 / V 0.034) | H 0.0357 / V 0.0363 (H 0.0474 / V 0.0339) | PASS | PASS |
| o6_zsine_mass | 2 | H 0.047 / V 0.043 (H 0.026 / V 0.038) | H 0.0470 / V 0.0426 (H 0.0261 / V 0.0386) | PASS | PASS |
| o6_zsine_mass | 3 | H 0.053 / V 0.080 (H 0.031 / V 0.025) | H 0.0528 / V 0.0804 (H 0.0310 / V 0.0252) | PASS | PASS |
| o7_lemniscate_tau2 | 1 | H 0.439 / V 0.104 (H 0.290 / V 0.034) | H 0.4399 / V 0.1036 (H 0.2901 / V 0.0341) | PASS | PASS |
| o7_lemniscate_tau2 | 2 | H 0.451 / V 0.047 (H 0.291 / V 0.113) | H 0.4516 / V 0.0466 (H 0.2909 / V 0.1133) | PASS | PASS |
| o7_lemniscate_tau2 | 3 | H 0.438 / V 0.076 (H 0.303 / V 0.039) | H 0.4380 / V 0.0758 (H 0.3029 / V 0.0388) | PASS | PASS |
| offb_vel_step | 1 | vx_rms 0.0087 / vx_end 0.0027 / dz 0.075 (vx_rms 0.0071 / vx_end 0.0061 / dz 0.092) | vx_rms 0.0086 / vx_end 0.0027 / dz 0.0743 (vx_rms 0.0071 / vx_end 0.0061 / dz 0.0915) | PASS | PASS |
| offb_vel_step | 2 | vx_rms 0.0073 / vx_end 0.0029 / dz 0.050 (vx_rms 0.0046 / vx_end 0.0030 / dz 0.095) | vx_rms 0.0073 / vx_end 0.0029 / dz 0.0510 (vx_rms 0.0046 / vx_end 0.0030 / dz 0.0956) | PASS | PASS |
| offb_vel_step | 3 | vx_rms 0.0082 / vx_end 0.0148 / dz 0.030 (vx_rms 0.0108 / vx_end 0.0035 / dz 0.105) | vx_rms 0.0081 / vx_end 0.0142 / dz 0.0287 (vx_rms 0.0110 / vx_end 0.0035 / dz 0.1063) | PASS | PASS |

Count: key1 24/24 PASS, key2 24/24 PASS; keys agree on every row (largest H/V difference 0.0017 m, offb rows within 0.0007 m/s, 0.0006 m/s, 0.003 m dz).
Worst: H 0.499 m (o2_circle_z s3, key1 0.4987 / key2 0.4984, limit 0.5; margin about 0.001 m), also o2 s2 0.497 and s1 0.488; the o1/o3/o7 lemniscates 0.398-0.472. V worst 0.119 m (o3_lemniscate_gust s1, limit 0.3). offb_vel_step worst vx_rms 0.0087 (0.2), vx_end 0.0148 (0.1, s3), dz 0.075 (0.3).
Change vs freeze-8: H on o1-o4, o7 rose from 0.28-0.32 to 0.40-0.50 m (XY_VP 2.4 lowers the horizontal crossover); o5/o6 (z sine) unchanged at 0.04-0.05 m. Freeze-8: 24/24 PASS, worst H 0.322 m (o3 s3), V 0.113 m.

## G5.3 mission (3 rows)
Command: `python3 indi_flight/bench/g53_mission_check.py g5/auto_tour_s<N> --json g5/auto_tour_s<N>/g53.json > g5/auto_tour_s<N>.g53.check.txt` (rc 0 x3). No second key exists for the mission row (as freeze-8).
Limits: all 4 waypoints reached within 1.0 m, vmax <= 5.5 m/s.

| flight | wp min dist 1/2/3/4 (m) | vmax (m/s) | verdict |
|---|---|---|---|
| auto_tour s1 | 0.954 / 0.837 / 0.933 / 0.080 (0.846 / 0.863 / 0.839 / 0.046) | 5.198 (5.198) | PASS |
| auto_tour s2 | 0.889 / 0.855 / 0.737 / 0.016 (0.888 / 0.818 / 0.733 / 0.025) | 5.196 (5.204) | PASS |
| auto_tour s3 | 0.928 / 0.919 / 0.798 / 0.002 (0.855 / 0.846 / 0.879 / 0.025) | 5.202 (5.194) | PASS |

3/3 PASS. Worst wp min dist 0.954 m (s1 wp1, limit 1.0; margin 0.046 m; freeze-8 worst 0.888), vmax 5.202 m/s (5.5).

## G5.3 hold (3 rows)
Command: `python3 indi_flight/bench/g53_hold_check.py g5/hold_wind_s{1,2,3} > g5/g53_hold_check.txt`; key2 `python3 indi_flight/bench/g53_hold_key2.py g5/hold_wind_s{1,2,3} > g5/key2_g53_hold.txt`.
Limit: 3-D hold RMS over [t0, t0+28 s] <= 0.3 m, nav_state 4 over the whole window.

| flight | key1 RMS / max (m) | mean offset x,y,z (m) | nav | key2 RMS / max (m) | key1 / key2 |
|---|---|---|---|---|---|
| hold_wind s1 | 0.058 / 0.102 (0.041 / 0.073) | [0.01, 0.041, -0.008] | [4] | 0.0581 / 0.1018 | PASS / PASS (valid yes) |
| hold_wind s2 | 0.056 / 0.093 (0.052 / 0.095) | [0.01, 0.04, -0.005] | [4] | 0.0555 / 0.0930 | PASS / PASS (valid yes) |
| hold_wind s3 | 0.075 / 0.119 (0.060 / 0.112) | [0.056, -0.012, -0.008] | [4] | 0.0746 / 0.1189 | PASS / PASS (valid yes) |

3/3 PASS both keys, keys agree. Worst RMS 0.075 m (s3, limit 0.3); freeze-8 worst 0.060 m.

## G5.4 (6 flights: auto_tour s1-3, auto_land10 s1-3)
Commands: `python3 indi_flight/bench/auto_smoke_check.py g5/<run> --json g5/<run>/check.json > g5/<run>.check.txt` (6 flights, rc 0 all; no INVALID, no FAIL string in any output); key2 on auto_land10: `python3 indi_flight/bench/g54_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54.txt` and `python3 indi_flight/bench/g54_land_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54_land.txt` (rc 0).
Limits: take-off overshoot <= 0.5 m, bounce <= 0.3 m; ramp step <= 10 % hover, edge step <= 10 %, dip <= 0.3 m; touchdown vz <= 0.8 m/s, tilt <= 10 deg, re-lift <= 0.15 m; land mean vz 0.70 +-20 %; contact->disarm <= 3.0 s; RTL height error <= 1 m.

| flight | overshoot (m) | bounce (m) | ramp max / edge step (% hover) | dip (m) | td vz (m/s) | td tilt (deg) | re-lift (m) | land mean vz (m/s) | contact->disarm (s) | RTL err (m) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| auto_tour s1 | -0.010 (-0.063) | 0.200 | 7.5 / 4.6 (7.5 / 4.5) | 0.000 | 0.685 (0.693) | 0.29 (0.21) | 0.050 | 0.707 (0.698) | 2.67 (2.69) | 0.010 (0.071) | PASS |
| auto_tour s2 | -0.066 (-0.053) | 0.200 | 7.6 / 4.7 (7.5 / 4.1) | 0.000 | 0.710 (0.696) | 0.42 (0.30) | 0.050 | 0.703 (0.700) | 2.69 (2.68) | 0.055 (0.039) | PASS |
| auto_tour s3 | -0.043 (-0.039) | 0.200 | 7.5 / 4.1 (7.5 / 4.1) | 0.000 | 0.727 (0.696) | 0.26 (0.21) | 0.050 (0.049) | 0.703 (0.691) | 2.69 (2.68) | 0.044 (0.042) | PASS |
| auto_land10 s1 | -0.045 (-0.072) | 0.200 | 7.5 / 4.6 (7.5 / 4.7) | 0.000 | 0.707 (0.711) | 0.54 (0.43) | 0.049 | 0.697 (0.692) | 2.69 | n/a | PASS |
| auto_land10 s2 | -0.077 (-0.084) | 0.200 | 7.5 / 4.6 (7.5 / 4.2) | 0.000 | 0.710 (0.708) | 0.26 (0.17) | 0.049 (0.050) | 0.694 | 2.68 (2.69) | n/a | PASS |
| auto_land10 s3 | -0.086 (-0.032) | 0.200 | 7.5 / 4.1 (7.5 / 4.2) | 0.000 | 0.696 (0.693) | 0.35 (0.48) | 0.050 | 0.697 (0.705) | 2.69 (2.70) | n/a | PASS |

Count: 6/6 PASS (no FAIL string in any of the 6 outputs: 0).
Key2 (auto_land10 only), freeze-9:
```
auto_land10_s1: t_td=64.405 s  v_td=0.707 m/s  tilt=0.54 deg  relift=0.049 m  edge=34.084 s  edge_step=4.63 %  hover=0.1363
auto_land10_s2: t_td=65.526 s  v_td=0.710 m/s  tilt=0.26 deg  relift=0.049 m  edge=35.025 s  edge_step=4.62 %  hover=0.1363
auto_land10_s3: t_td=64.692 s  v_td=0.696 m/s  tilt=0.35 deg  relift=0.050 m  edge=34.475 s  edge_step=4.05 %  hover=0.1364
auto_land10_s1: mean vz 0.698 (window 61.61-64.05 s) vs 0.70 +-20% PASS; contact 64.83 disarm 67.52 -> 2.69 s vs 3.0 PASS
auto_land10_s2: mean vz 0.699 (window 62.74-65.17 s) vs 0.70 +-20% PASS; contact 65.96 disarm 68.64 -> 2.68 s vs 3.0 PASS
auto_land10_s3: mean vz 0.703 (window 61.92-64.33 s) vs 0.70 +-20% PASS; contact 65.12 disarm 67.81 -> 2.69 s vs 3.0 PASS
```
Key2 agrees with key1 on the 3 land10 flights: td vz 0.707 / 0.710 / 0.696 (identical to key1), tilt 0.54 / 0.26 / 0.35 (identical), re-lift 0.049-0.050, edge step 4.63 / 4.62 / 4.05 % (key1 4.6 / 4.6 / 4.1), land mean vz 0.698 / 0.699 / 0.703 (key1 0.697 / 0.694 / 0.697), contact->disarm 2.68-2.69 s; all PASS.
Worst: td vz 0.727 m/s (auto_tour s3, limit 0.8; land10 worst 0.710), tilt 0.54 deg (10), re-lift 0.050 (0.15), bounce 0.200 (0.3), overshoot -0.010 (0.5), ramp step 7.6 % / edge step 4.7 % (10 %), land mean vz 0.694-0.707 (0.56-0.84), contact->disarm 2.69 s (3.0), RTL err 0.055 m (1.0).

## G5 events (hover, seed 1, one flight; rows per event as at freeze-8)
Commands: `python3 indi_flight/bench/g5_rows_check.py events/g5_events_s1 > events/g5_rows.txt`; `python3 indi_flight/bench/g511_check.py events/g5_events_s1 > events/g511.txt`; key2 `python3 indi_flight/bench/g5_rows_key2.py events/g5_events_s1 > events/key2_g5rows_s1.txt` (all rc 0). No key2 script for G5.11 (as freeze-8). G5.6 and G5.11 z reset: not tested (owner decision Q8(b)), as freeze-8.
Limits: as freeze-8 (G5.8 entry-timeout <= 1000 ms, action hold nav 4, excursion <= 1 m; G5.9a motors 0 within one command period 1.25 ms of kill rise; G5.9b states zero at rearm; G5.9c first second <= 5 %; G5.9d edge step <= 10 % hover, dip <= 0.3 m; G5.11 xy excursion <= 0.5 m, no oscillation; yaw excess <= 1 deg, excursion <= 0.5 m).

| row | key1 value | limit | key1 verdict | key2 |
|---|---|---|---|---|
| G5.8 rc_loss | entry-timeout 510 ms (510), nav 4, excursion 0.062 m (0.057) | 1000 ms, 1 m | PASS | PASS (entry-ref 0.510 s) |
| G5.8 link_loss | 4 ms (10), nav 4, excursion 0.074 m (0.094) | 1000 ms, 1 m | PASS | consistent (rise-ref 0.004 s) |
| G5.8 offboard_loss | 24 ms (25), nav 4, excursion 0.096 m (0.066) | 1000 ms, 1 m | PASS | PASS (entry-ref 0.024 s) |
| G5.9a kill motors | outputs 0 at 0.00 ms after kill rise (0.00) (spacing 1.25 ms); switch -> kill flag 7.50 ms (info) | <= 1.25 ms from kill rise | PASS | same definition difference as freeze-8: key2 references the switch change (+7.50 ms after switch), 0.00 ms after kill rise agrees with key1 |
| G5.9b rearm states | states non-zero none (of 2 and of 6) | zero | PASS | key2 lists blend / hold_cycles / torque_filtered / rate_sp_dot at arm 0 (first sample after arm maxabs 0) |
| G5.9c first second | 0.01 % full scale (0.01) | <= 5 % | PASS | key2 1.04 % of full scale (0.92) (different measure: first-second command range per motor, W=2700) |
| G5.9d takeoff | step 0.0064 = 4.6 % hover (4.6), dip 0.000 m | 10 %, 0.3 m | PASS | PASS (4.6 %, dip 0.000 m) |
| G5.11 ekf_yaw | tilt jump 0.86 deg (1.09), no-event p95 0.98 (1.23), excess -0.12 deg (-0.14); excursion 3-D 0.053 m (0.053); osc no | excess <= 1 deg, 0.5 m | PASS (legacy rule PASS) | none |
| G5.11 ekf_xy | horizontal excursion 0.236 m (0.157), osc no (tilt jump 8.14 deg, reported only) | 0.5 m | PASS (legacy tilt-jump rule FAIL, as freeze-8) | none |

Count: key1 PASS on all scored rows (G5.8 x3, G5.9a-d x4, G5.11 x2 = 9/9), G5.9a info lines as freeze-8. Key2 agrees on G5.8 and G5.9d; G5.9a differs on the reference definition only; G5.9b/G5.9c key2 cells are a condensed reading (full text in events/key2_g5rows_s1.txt).
Note: G5.11 xy excursion 0.236 m is above the s176 range (0.154-0.209 m) and freeze-8 (0.157 m) but within the 0.5 m limit (one flight only).
Side effect: g5_rows_key2.py overwrote results/g5_events_s145/key2_rows.md (hardcoded path); restored with git checkout (outside freeze9_s183, reverted).

## Rows not re-flown at freeze-9
Freeze-8 listed G5.10 and G3 as "Not included (per brief)" (freeze8_s181/README.md) and G5.6 / G5.11 z reset as not tested (owner decision Q8(b)); it had no G5.7, G5.11 z or other rows in G5_SCORES.md. At freeze-9: G5.10, G3, G5.6, G5.11 z reset, G5.7 and any other G5 row not in this queue: not re-flown at freeze-9. No value is carried over here.
