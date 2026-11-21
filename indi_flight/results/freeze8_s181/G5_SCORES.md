# Freeze-8 (S181) G5 and G2-STEP scores

Numbers and per-row verdicts against the stated limits only; no gate verdicts. Scored with existing scripts (indi_flight/bench), no
edits, run on the host (pyulog present), repo root. Run dirs and flights were not modified except that the checkers wrote their
own json (g55.json, g53.json, check.json, g5_rows.json, g511_check.json) into the run dirs as at freeze-7. Provenance as
queue.sh (plant quad5in, sim v2, --speed 4, gps/gnss delay 110, vib-acc 10, imu-noise-scale 4.0, params g5_freeze_s157/params.params,
no MC_INDI_XY_P/XY_VP; steps: g2_step_s64/indi.params, 800 Hz). Freeze-7 reference: freeze7_s177/SCORES.md.

## G5.5 (24 rows)
Command (existing checker, as g5_freeze_s157/checks.sh and freeze7): `python3 indi_flight/bench/g55_check.py g55/<scenario>_s<seed> --json g55/<scenario>_s<seed>/g55.json > g55/<scenario>_s<seed>.check.txt` (24 files, rc 0 all).
Key2: `python3 indi_flight/bench/g55_g57_key2.py g55 g55/*_s?` -> g55/key2_g55.txt (rc 0).
Limits (GATES.md 5b): o1-o7 H RMS <= 0.5 m, V RMS <= 0.3 m; offb_vel_step vx RMS last 3 s <= 0.2 m/s, |vx| end <= 0.1 m/s, dz max <= 0.3 m. All rows: invalid none, mc_pos_control absent in px4 log, key2 LOC none.

| scenario | seed | key1 | key2 | key1 verdict | key2 verdict |
|---|---|---|---|---|---|
| o1_lemniscate | 1 | H 0.302 / V 0.041 | H 0.3015 / V 0.0413 | PASS | PASS |
| o1_lemniscate | 2 | H 0.303 / V 0.078 | H 0.3029 / V 0.0781 | PASS | PASS |
| o1_lemniscate | 3 | H 0.300 / V 0.051 | H 0.2996 / V 0.0506 | PASS | PASS |
| o2_circle_z | 1 | H 0.302 / V 0.096 | H 0.3018 / V 0.0962 | PASS | PASS |
| o2_circle_z | 2 | H 0.313 / V 0.044 | H 0.3128 / V 0.0446 | PASS | PASS |
| o2_circle_z | 3 | H 0.302 / V 0.069 | H 0.3022 / V 0.0694 | PASS | PASS |
| o3_lemniscate_gust | 1 | H 0.317 / V 0.052 | H 0.3172 / V 0.0524 | PASS | PASS |
| o3_lemniscate_gust | 2 | H 0.320 / V 0.067 | H 0.3195 / V 0.0673 | PASS | PASS |
| o3_lemniscate_gust | 3 | H 0.322 / V 0.065 | H 0.3219 / V 0.0651 | PASS | PASS |
| o4_lemniscate_payload | 1 | H 0.277 / V 0.035 | H 0.2768 / V 0.0347 | PASS | PASS |
| o4_lemniscate_payload | 2 | H 0.283 / V 0.042 | H 0.2824 / V 0.0415 | PASS | PASS |
| o4_lemniscate_payload | 3 | H 0.278 / V 0.070 | H 0.2784 / V 0.0698 | PASS | PASS |
| o5_zsine_com_shift | 1 | H 0.041 / V 0.046 | H 0.0410 / V 0.0456 | PASS | PASS |
| o5_zsine_com_shift | 2 | H 0.035 / V 0.026 | H 0.0349 / V 0.0259 | PASS | PASS |
| o5_zsine_com_shift | 3 | H 0.048 / V 0.035 | H 0.0482 / V 0.0350 | PASS | PASS |
| o6_zsine_mass | 1 | H 0.047 / V 0.034 | H 0.0474 / V 0.0339 | PASS | PASS |
| o6_zsine_mass | 2 | H 0.026 / V 0.038 | H 0.0261 / V 0.0386 | PASS | PASS |
| o6_zsine_mass | 3 | H 0.031 / V 0.025 | H 0.0310 / V 0.0252 | PASS | PASS |
| o7_lemniscate_tau2 | 1 | H 0.290 / V 0.034 | H 0.2901 / V 0.0341 | PASS | PASS |
| o7_lemniscate_tau2 | 2 | H 0.291 / V 0.113 | H 0.2909 / V 0.1133 | PASS | PASS |
| o7_lemniscate_tau2 | 3 | H 0.303 / V 0.039 | H 0.3029 / V 0.0388 | PASS | PASS |
| offb_vel_step | 1 | vx_rms 0.0071 / vx_end 0.0061 / dz 0.092 | vx_rms 0.0071 / vx_end 0.0061 / dz 0.0915 | PASS | PASS |
| offb_vel_step | 2 | vx_rms 0.0046 / vx_end 0.0030 / dz 0.095 | vx_rms 0.0046 / vx_end 0.0030 / dz 0.0956 | PASS | PASS |
| offb_vel_step | 3 | vx_rms 0.0108 / vx_end 0.0035 / dz 0.105 | vx_rms 0.0110 / vx_end 0.0035 / dz 0.1063 | PASS | PASS |

Count: key1 24/24 PASS, key2 24/24 PASS, no row differs by more than 0.003 m (H/V) between keys.
Worst: H 0.322 m (o3_lemniscate_gust s3, limit 0.5), V 0.113 m (o7_lemniscate_tau2 s2, limit 0.3); offb_vel_step worst vx_rms 0.0108 (0.2), vx_end 0.0061 (0.1), dz 0.105 (0.3).
Freeze-7: 24/24 PASS, worst H 0.323 m (o3 s3), max V 0.097 m (o4 s1), offb worst vx_rms 0.005, vx_end 0.018, dz 0.127.

## G5.3 mission (3 rows)
Command: `python3 indi_flight/bench/g53_mission_check.py g5/auto_tour_s<N> --json g5/auto_tour_s<N>/g53.json > g5/auto_tour_s<N>.g53.check.txt` (rc 0 x3). No second key exists for the mission row (none listed at freeze-7).
Limits: all 4 waypoints reached within 1.0 m (nav_acc_rad 10 m; wp acceptance in the checker), vmax <= 5.5 m/s.

| flight | wp min dist 1/2/3/4 (m) | vmax (m/s) | verdict |
|---|---|---|---|
| auto_tour s1 | 0.846 / 0.863 / 0.839 / 0.046 | 5.198 | PASS |
| auto_tour s2 | 0.888 / 0.818 / 0.733 / 0.025 | 5.204 | PASS |
| auto_tour s3 | 0.855 / 0.846 / 0.879 / 0.025 | 5.194 | PASS |

3/3 PASS. Worst wp min dist 0.888 m (s2 wp1, limit 1.0), vmax 5.204 m/s (5.5). Freeze-7: 3/3 PASS, worst wp 0.817 m, vmax 5.199.

## G5.3 hold (3 rows)
Command: `python3 indi_flight/bench/g53_hold_check.py g5/hold_wind_s{1,2,3}` (stdout -> g5/g53_hold_check.txt; json per run), as g5_freeze_s157/g53_hold_check.txt. Flown with hold_wind_overrides.json, --stick-mode posctl (queue.sh).
Key2: `python3 indi_flight/bench/g53_hold_key2.py g5/hold_wind_s{1,2,3}` -> g5/key2_g53_hold.txt.
Limit: 3-D hold RMS over [t0, t0+28 s] <= 0.3 m, nav_state 4 over the whole window.

| flight | key1 RMS / max (m) | mean offset x,y,z (m) | nav | key2 RMS / max (m) | key1 / key2 |
|---|---|---|---|---|---|
| hold_wind s1 | 0.041 / 0.073 | [-0.013, -0.002, -0.013] | [4] | 0.0409 / 0.0730 | PASS / PASS (valid yes) |
| hold_wind s2 | 0.052 / 0.095 | [0.027, 0.024, 0.02] | [4] | 0.0520 / 0.0952 | PASS / PASS (valid yes) |
| hold_wind s3 | 0.060 / 0.112 | [0.018, 0.013, -0.04] | [4] | 0.0603 / 0.1122 | PASS / PASS (valid yes) |

3/3 PASS both keys. Worst RMS 0.060 m (s3, limit 0.3). Freeze-7/s157 comparison: s157 hold 0.044 / 0.056 / 0.080 m, 3/3 PASS (freeze-7 had no hold row; the hold row was last scored at g5_freeze_s157).

## G5.4 (6 flights: auto_tour s1-3, auto_land10 s1-3)
Commands (existing checkers, as freeze-7): `python3 indi_flight/bench/auto_smoke_check.py g5/<run> --json g5/<run>/check.json > g5/<run>.check.txt` (6 flights, rc 0 all; no INVALID line in any output);
key2 on the 3 auto_land10 flights: `python3 indi_flight/bench/g54_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54.txt` and `python3 indi_flight/bench/g54_land_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54_land.txt` (both scripts print to stdout).
Limits: take-off overshoot <= 0.5 m, bounce <= 0.3 m; ramp step <= 10 % hover, edge step <= 10 %, dip <= 0.3 m; touchdown vz <= 0.8 m/s, tilt <= 10 deg, re-lift <= 0.15 m; land mean vz 0.70 +-20 %; contact->disarm <= 3.0 s; RTL height error <= 1 m.

| flight | overshoot (m) | bounce (m) | ramp max / edge step (% hover) | dip (m) | td vz (m/s) | td tilt (deg) | re-lift (m) | land mean vz (m/s) | contact->disarm (s) | RTL err (m) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| auto_tour s1 | -0.063 | 0.200 | 7.5 / 4.5 | 0.000 | 0.693 | 0.21 | 0.050 | 0.698 | 2.69 | 0.071 | PASS |
| auto_tour s2 | -0.053 | 0.200 | 7.5 / 4.1 | 0.000 | 0.696 | 0.30 | 0.050 | 0.700 | 2.68 | 0.039 | PASS |
| auto_tour s3 | -0.039 | 0.200 | 7.5 / 4.1 | 0.000 | 0.696 | 0.21 | 0.049 | 0.691 | 2.68 | 0.042 | PASS |
| auto_land10 s1 | -0.072 | 0.200 | 7.5 / 4.7 | 0.000 | 0.711 | 0.43 | 0.049 | 0.692 | 2.69 | n/a | PASS |
| auto_land10 s2 | -0.084 | 0.200 | 7.5 / 4.2 | 0.000 | 0.708 | 0.17 | 0.050 | 0.694 | 2.69 | n/a | PASS |
| auto_land10 s3 | -0.032 | 0.200 | 7.5 / 4.2 | 0.000 | 0.693 | 0.48 | 0.050 | 0.705 | 2.70 | n/a | PASS |

Count: 6/6 PASS (no FAIL string in any of the 6 outputs: 0).
Key2 (auto_land10 only):
```
auto_land10_s1: t_td=64.270 s  v_td=0.711 m/s  tilt=0.43 deg  relift=0.049 m  edge=34.114 s  edge_step=4.66 %  hover=0.1363
auto_land10_s2: t_td=64.250 s  v_td=0.708 m/s  tilt=0.17 deg  relift=0.050 m  edge=34.188 s  edge_step=4.20 %  hover=0.1363
auto_land10_s3: t_td=64.685 s  v_td=0.693 m/s  tilt=0.48 deg  relift=0.050 m  edge=34.157 s  edge_step=4.23 %  hover=0.1362
auto_land10_s1: mean vz 0.687 (window 61.44-63.91 s) vs 0.70 +-20% PASS; contact 64.69 disarm 67.38 -> 2.69 s vs 3.0 PASS
auto_land10_s2: mean vz 0.690 (window 61.43-63.90 s) vs 0.70 +-20% PASS; contact 64.67 disarm 67.36 -> 2.69 s vs 3.0 PASS
auto_land10_s3: mean vz 0.707 (window 61.92-64.32 s) vs 0.70 +-20% PASS; contact 65.13 disarm 67.82 -> 2.70 s vs 3.0 PASS
```
Key2 agrees with key1 on the 3 land10 flights: td vz 0.711 / 0.708 / 0.693 (key1 0.711 / 0.708 / 0.693), tilt 0.43 / 0.17 / 0.48 (key1 0.43 / 0.17 / 0.48), re-lift 0.049-0.050, edge step 4.66 / 4.20 / 4.23 % (key1 4.7 / 4.2 / 4.2), land mean vz 0.687 / 0.690 / 0.707 (key1 0.692 / 0.694 / 0.705), contact->disarm 2.69-2.70 s; all PASS.
Worst: td vz 0.711 m/s (auto_land10 s1, limit 0.8), tilt 0.48 deg (10), re-lift 0.050 (0.15), bounce 0.200 (0.3), overshoot -0.032 (0.5), ramp step 7.5 % / edge step 4.7 % (10 %), land mean vz 0.691-0.705 (0.56-0.84), contact->disarm 2.70 s (3.0), RTL err 0.071 m (1.0).
Freeze-7: 6/6 PASS, td vz worst 0.708 m/s, ramp step 7.5 %, edge 4.0-4.6 %, RTL err 0.023-0.034 m.
# Freeze-8 (S181) G5 and G2-STEP scores

Numbers and per-row verdicts against the stated limits only; no gate verdicts. Scored with existing scripts (indi_flight/bench), no
edits, run on the host (pyulog present), repo root. Run dirs and flights were not modified except that the checkers wrote their
own json (g55.json, g53.json, check.json, g5_rows.json, g511_check.json) into the run dirs as at freeze-7. Provenance as
queue.sh (plant quad5in, sim v2, --speed 4, gps/gnss delay 110, vib-acc 10, imu-noise-scale 4.0, params g5_freeze_s157/params.params,
no MC_INDI_XY_P/XY_VP; steps: g2_step_s64/indi.params, 800 Hz). Freeze-7 reference: freeze7_s177/SCORES.md.

## G5.5 (24 rows)
Command (existing checker, as g5_freeze_s157/checks.sh and freeze7): `python3 indi_flight/bench/g55_check.py g55/<scenario>_s<seed> --json g55/<scenario>_s<seed>/g55.json > g55/<scenario>_s<seed>.check.txt` (24 files, rc 0 all).
Key2: `python3 indi_flight/bench/g55_g57_key2.py g55 g55/*_s?` -> g55/key2_g55.txt (rc 0).
Limits (GATES.md 5b): o1-o7 H RMS <= 0.5 m, V RMS <= 0.3 m; offb_vel_step vx RMS last 3 s <= 0.2 m/s, |vx| end <= 0.1 m/s, dz max <= 0.3 m. All rows: invalid none, mc_pos_control absent in px4 log, key2 LOC none.

| scenario | seed | key1 | key2 | key1 verdict | key2 verdict |
|---|---|---|---|---|---|
| o1_lemniscate | 1 | H 0.302 / V 0.041 | H 0.3015 / V 0.0413 | PASS | PASS |
| o1_lemniscate | 2 | H 0.303 / V 0.078 | H 0.3029 / V 0.0781 | PASS | PASS |
| o1_lemniscate | 3 | H 0.300 / V 0.051 | H 0.2996 / V 0.0506 | PASS | PASS |
| o2_circle_z | 1 | H 0.302 / V 0.096 | H 0.3018 / V 0.0962 | PASS | PASS |
| o2_circle_z | 2 | H 0.313 / V 0.044 | H 0.3128 / V 0.0446 | PASS | PASS |
| o2_circle_z | 3 | H 0.302 / V 0.069 | H 0.3022 / V 0.0694 | PASS | PASS |
| o3_lemniscate_gust | 1 | H 0.317 / V 0.052 | H 0.3172 / V 0.0524 | PASS | PASS |
| o3_lemniscate_gust | 2 | H 0.320 / V 0.067 | H 0.3195 / V 0.0673 | PASS | PASS |
| o3_lemniscate_gust | 3 | H 0.322 / V 0.065 | H 0.3219 / V 0.0651 | PASS | PASS |
| o4_lemniscate_payload | 1 | H 0.277 / V 0.035 | H 0.2768 / V 0.0347 | PASS | PASS |
| o4_lemniscate_payload | 2 | H 0.283 / V 0.042 | H 0.2824 / V 0.0415 | PASS | PASS |
| o4_lemniscate_payload | 3 | H 0.278 / V 0.070 | H 0.2784 / V 0.0698 | PASS | PASS |
| o5_zsine_com_shift | 1 | H 0.041 / V 0.046 | H 0.0410 / V 0.0456 | PASS | PASS |
| o5_zsine_com_shift | 2 | H 0.035 / V 0.026 | H 0.0349 / V 0.0259 | PASS | PASS |
| o5_zsine_com_shift | 3 | H 0.048 / V 0.035 | H 0.0482 / V 0.0350 | PASS | PASS |
| o6_zsine_mass | 1 | H 0.047 / V 0.034 | H 0.0474 / V 0.0339 | PASS | PASS |
| o6_zsine_mass | 2 | H 0.026 / V 0.038 | H 0.0261 / V 0.0386 | PASS | PASS |
| o6_zsine_mass | 3 | H 0.031 / V 0.025 | H 0.0310 / V 0.0252 | PASS | PASS |
| o7_lemniscate_tau2 | 1 | H 0.290 / V 0.034 | H 0.2901 / V 0.0341 | PASS | PASS |
| o7_lemniscate_tau2 | 2 | H 0.291 / V 0.113 | H 0.2909 / V 0.1133 | PASS | PASS |
| o7_lemniscate_tau2 | 3 | H 0.303 / V 0.039 | H 0.3029 / V 0.0388 | PASS | PASS |
| offb_vel_step | 1 | vx_rms 0.0071 / vx_end 0.0061 / dz 0.092 | vx_rms 0.0071 / vx_end 0.0061 / dz 0.0915 | PASS | PASS |
| offb_vel_step | 2 | vx_rms 0.0046 / vx_end 0.0030 / dz 0.095 | vx_rms 0.0046 / vx_end 0.0030 / dz 0.0956 | PASS | PASS |
| offb_vel_step | 3 | vx_rms 0.0108 / vx_end 0.0035 / dz 0.105 | vx_rms 0.0110 / vx_end 0.0035 / dz 0.1063 | PASS | PASS |

Count: key1 24/24 PASS, key2 24/24 PASS, no row differs by more than 0.003 m (H/V) between keys.
Worst: H 0.322 m (o3_lemniscate_gust s3, limit 0.5), V 0.113 m (o7_lemniscate_tau2 s2, limit 0.3); offb_vel_step worst vx_rms 0.0108 (0.2), vx_end 0.0061 (0.1), dz 0.105 (0.3).
Freeze-7: 24/24 PASS, worst H 0.323 m (o3 s3), max V 0.097 m (o4 s1), offb worst vx_rms 0.005, vx_end 0.018, dz 0.127.

## G5.3 mission (3 rows)
Command: `python3 indi_flight/bench/g53_mission_check.py g5/auto_tour_s<N> --json g5/auto_tour_s<N>/g53.json > g5/auto_tour_s<N>.g53.check.txt` (rc 0 x3). No second key exists for the mission row (none listed at freeze-7).
Limits: all 4 waypoints reached within 1.0 m (nav_acc_rad 10 m; wp acceptance in the checker), vmax <= 5.5 m/s.

| flight | wp min dist 1/2/3/4 (m) | vmax (m/s) | verdict |
|---|---|---|---|
| auto_tour s1 | 0.846 / 0.863 / 0.839 / 0.046 | 5.198 | PASS |
| auto_tour s2 | 0.888 / 0.818 / 0.733 / 0.025 | 5.204 | PASS |
| auto_tour s3 | 0.855 / 0.846 / 0.879 / 0.025 | 5.194 | PASS |

3/3 PASS. Worst wp min dist 0.888 m (s2 wp1, limit 1.0), vmax 5.204 m/s (5.5). Freeze-7: 3/3 PASS, worst wp 0.817 m, vmax 5.199.

## G5.3 hold (3 rows)
Command: `python3 indi_flight/bench/g53_hold_check.py g5/hold_wind_s{1,2,3}` (stdout -> g5/g53_hold_check.txt; json per run), as g5_freeze_s157/g53_hold_check.txt. Flown with hold_wind_overrides.json, --stick-mode posctl (queue.sh).
Key2: `python3 indi_flight/bench/g53_hold_key2.py g5/hold_wind_s{1,2,3}` -> g5/key2_g53_hold.txt.
Limit: 3-D hold RMS over [t0, t0+28 s] <= 0.3 m, nav_state 4 over the whole window.

| flight | key1 RMS / max (m) | mean offset x,y,z (m) | nav | key2 RMS / max (m) | key1 / key2 |
|---|---|---|---|---|---|
| hold_wind s1 | 0.041 / 0.073 | [-0.013, -0.002, -0.013] | [4] | 0.0409 / 0.0730 | PASS / PASS (valid yes) |
| hold_wind s2 | 0.052 / 0.095 | [0.027, 0.024, 0.02] | [4] | 0.0520 / 0.0952 | PASS / PASS (valid yes) |
| hold_wind s3 | 0.060 / 0.112 | [0.018, 0.013, -0.04] | [4] | 0.0603 / 0.1122 | PASS / PASS (valid yes) |

3/3 PASS both keys. Worst RMS 0.060 m (s3, limit 0.3). Freeze-7/s157 comparison: s157 hold 0.044 / 0.056 / 0.080 m, 3/3 PASS (freeze-7 had no hold row; the hold row was last scored at g5_freeze_s157).

## G5.4 (6 flights: auto_tour s1-3, auto_land10 s1-3)
Commands (existing checkers, as freeze-7): `python3 indi_flight/bench/auto_smoke_check.py g5/<run> --json g5/<run>/check.json > g5/<run>.check.txt` (6 flights, rc 0 all; no INVALID line in any output);
key2 on the 3 auto_land10 flights: `python3 indi_flight/bench/g54_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54.txt` and `python3 indi_flight/bench/g54_land_key2.py g5/auto_land10_s{1,2,3} > g5/key2_g54_land.txt` (both scripts print to stdout).
Limits: take-off overshoot <= 0.5 m, bounce <= 0.3 m; ramp step <= 10 % hover, edge step <= 10 %, dip <= 0.3 m; touchdown vz <= 0.8 m/s, tilt <= 10 deg, re-lift <= 0.15 m; land mean vz 0.70 +-20 %; contact->disarm <= 3.0 s; RTL height error <= 1 m.

| flight | overshoot (m) | bounce (m) | ramp max / edge step (% hover) | dip (m) | td vz (m/s) | td tilt (deg) | re-lift (m) | land mean vz (m/s) | contact->disarm (s) | RTL err (m) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| auto_tour s1 | -0.063 | 0.200 | 7.5 / 4.5 | 0.000 | 0.693 | 0.21 | 0.050 | 0.698 | 2.69 | 0.071 | PASS |
| auto_tour s2 | -0.053 | 0.200 | 7.5 / 4.1 | 0.000 | 0.696 | 0.30 | 0.050 | 0.700 | 2.68 | 0.039 | PASS |
| auto_tour s3 | -0.039 | 0.200 | 7.5 / 4.1 | 0.000 | 0.696 | 0.21 | 0.049 | 0.691 | 2.68 | 0.042 | PASS |
| auto_land10 s1 | -0.072 | 0.200 | 7.5 / 4.7 | 0.000 | 0.711 | 0.43 | 0.049 | 0.692 | 2.69 | n/a | PASS |
| auto_land10 s2 | -0.084 | 0.200 | 7.5 / 4.2 | 0.000 | 0.708 | 0.17 | 0.050 | 0.694 | 2.69 | n/a | PASS |
| auto_land10 s3 | -0.032 | 0.200 | 7.5 / 4.2 | 0.000 | 0.693 | 0.48 | 0.050 | 0.705 | 2.70 | n/a | PASS |

Count: 6/6 PASS (no FAIL string in any of the 6 outputs: 0).
Key2 (auto_land10 only):
```
auto_land10_s1: t_td=64.270 s  v_td=0.711 m/s  tilt=0.43 deg  relift=0.049 m  edge=34.114 s  edge_step=4.66 %  hover=0.1363
auto_land10_s2: t_td=64.250 s  v_td=0.708 m/s  tilt=0.17 deg  relift=0.050 m  edge=34.188 s  edge_step=4.20 %  hover=0.1363
auto_land10_s3: t_td=64.685 s  v_td=0.693 m/s  tilt=0.48 deg  relift=0.050 m  edge=34.157 s  edge_step=4.23 %  hover=0.1362
auto_land10_s1: mean vz 0.687 (window 61.44-63.91 s) vs 0.70 +-20% PASS; contact 64.69 disarm 67.38 -> 2.69 s vs 3.0 PASS
auto_land10_s2: mean vz 0.690 (window 61.43-63.90 s) vs 0.70 +-20% PASS; contact 64.67 disarm 67.36 -> 2.69 s vs 3.0 PASS
auto_land10_s3: mean vz 0.707 (window 61.92-64.32 s) vs 0.70 +-20% PASS; contact 65.13 disarm 67.82 -> 2.70 s vs 3.0 PASS
```
Key2 agrees with key1 on the 3 land10 flights: td vz 0.711 / 0.708 / 0.693 (key1 0.711 / 0.708 / 0.693), tilt 0.43 / 0.17 / 0.48 (key1 0.43 / 0.17 / 0.48), re-lift 0.049-0.050, edge step 4.66 / 4.20 / 4.23 % (key1 4.7 / 4.2 / 4.2), land mean vz 0.687 / 0.690 / 0.707 (key1 0.692 / 0.694 / 0.705), contact->disarm 2.69-2.70 s; all PASS.
Worst: td vz 0.711 m/s (auto_land10 s1, limit 0.8), tilt 0.48 deg (10), re-lift 0.050 (0.15), bounce 0.200 (0.3), overshoot -0.032 (0.5), ramp step 7.5 % / edge step 4.7 % (10 %), land mean vz 0.691-0.705 (0.56-0.84), contact->disarm 2.70 s (3.0), RTL err 0.071 m (1.0).
Freeze-7: 6/6 PASS, td vz worst 0.708 m/s, ramp step 7.5 %, edge 4.0-4.6 %, RTL err 0.023-0.034 m.


## G5 events (hover, seed 1, one flight; rows per event as at freeze-7/s176)
Commands (s176 rescore.sh, amended S175 checkers, host python): `python3 indi_flight/bench/g5_rows_check.py events/g5_events_s1 > events/g5_rows.txt` (G5.8, G5.9a-d); `python3 indi_flight/bench/g511_check.py events/g5_events_s1 > events/g511.txt` (G5.11 xy, yaw); key2 `python3 indi_flight/bench/g5_rows_key2.py events/g5_events_s1 > events/key2_g5rows_s1.txt`. No key2 script for G5.11 was found (g5_rescore_s176 used none). G5.6 and G5.11 z reset: not tested (owner decision Q8(b)), same as s176.
Limits: G5.8 entry - timeout <= 1000 ms, action hold (nav 4), excursion <= 1 m; G5.9a motors 0 within one command period (1.25 ms) of the actuator_armed.kill rise (S175 reference); G5.9b states zero at rearm; G5.9c first second <= 5 % full scale; G5.9d edge step <= 10 % hover, dip <= 0.3 m; G5.11 xy horizontal excursion <= 0.5 m and no oscillation; G5.11 yaw excess over no-event p95 <= 1 deg, excursion <= 0.5 m.

| row | key1 value | limit | key1 verdict | key2 |
|---|---|---|---|---|
| G5.8 rc_loss | entry-timeout 510 ms, nav 4, excursion 0.057 m | 1000 ms, 1 m | PASS | PASS (entry-ref 0.510 s) |
| G5.8 link_loss | 10 ms, nav 4, excursion 0.094 m | 1000 ms, 1 m | PASS | consistent (rise-ref 0.010 s) |
| G5.8 offboard_loss | 25 ms, nav 4, excursion 0.066 m | 1000 ms, 1 m | PASS | PASS (entry-ref 0.025 s) |
| G5.9a kill motors | outputs 0 at 0.00 ms after kill rise (spacing 1.25 ms); switch -> kill flag 7.50 ms (info) | <= 1.25 ms from kill rise | PASS | FAIL as its own text: key2 references the switch change (outputs 0 +7.50 ms after switch, limit one command period from switch); 0.00 ms after kill rise agrees with key1 |
| G5.9b rearm states | states non-zero none (of 2 and of 6) | zero | PASS | key2 lists blend / hold_cycles / torque_filtered / rate_sp_dot at arm 0 (see key2 file) |
| G5.9c first second | 0.01 % full scale | <= 5 % | PASS | key2 0.92 % of full scale (different measure: first-second command range per motor, W=2700) |
| G5.9d takeoff | step 0.0063 = 4.6 % hover, dip 0.000 m | 10 %, 0.3 m | PASS | PASS (4.6 %, dip 0.000 m) |
| G5.11 ekf_yaw | tilt jump 1.09 deg, no-event p95 1.23, excess -0.14 deg; excursion 3-D 0.053 m; osc no | excess <= 1 deg, 0.5 m | PASS (legacy rule FAIL) | none |
| G5.11 ekf_xy | horizontal excursion 0.157 m, osc no (tilt jump 8.87 deg, reported only) | 0.5 m | PASS (legacy tilt-jump rule FAIL) | none |

Count: key1 PASS on all scored rows (G5.8 x3, G5.9a-d x4, G5.11 x2 = 9/9), 1 INFO-only pair. G5.9a key2 disagrees on the reference definition only (see row). The G5.9b/G5.9c key2 cells are a condensed reading; full key2 text is in events/key2_g5rows_s1.txt.
Comparison, s176 rescore of g511_fix_s161 / g5_freeze_s157 (3 seeds there): G5.9a 3/3 PASS at 0.00 ms after kill rise; G5.11 xy excursion 0.154-0.209 m PASS; G5.11 yaw excess -0.39 to 0.19 deg PASS (freeze set 0.76-1.14, one FAIL); G5.8 all PASS. Freeze-8 xy 0.157 m and yaw -0.14 deg fall inside those ranges.

## G2-STEP (9 rows)
Commands (GATES.md G2-STEP, existing scripts): `python3 indi_flight/bench/g2_step_metrics.py steps/g2_step_primary.json steps/seed{1,2,3}/step_{roll,pitch,yaw}_indi > steps/step_out.txt` (rc 0); second key per flight `python3 indi_flight/bench/t127_step_metrics_key.py steps/seed<N>/step_<axis>_indi steps/key2_seed<N>_<axis>.md` (rows est_g2 / gt_g2, collected in steps/step_key2.txt). Same as freeze8_pretest_s181 (g2_step_primary.json).
Pass per seed: roll/pitch overshoot <= 5 %, 2 % settle <= 450 ms; yaw overshoot <= 5 %, settle <= 1350 ms; ground-truth overshoot <= 5 % also a pass condition. Rise 10-90 % reported (no limit). Metrics on the estimated attitude against the setpoint (est), key2 est_g2 in the last columns.

| seed | axis | rise (ms) | overshoot est / truth (%) | settle (ms) | limit settle | verdict | key2 rise / OS / settle (est_g2) |
|---|---|---|---|---|---|---|---|
| 1 | roll | 190.0 | 0.80 / 0.88 | 337.5 | 450 | PASS (script pass True) | 191.2 / 0.80 / 337.5 |
| 1 | pitch | 187.4 | 0.44 / 0.26 | 343.8 | 450 | PASS (script pass True) | 187.5 / 0.44 / 343.8 |
| 1 | yaw | 625.6 | 0.00 / 0.00 | 1207.5 | 1350 | PASS (script pass True) | 626.2 / 0.00 / 1207.5 |
| 2 | roll | 190.4 | 0.47 / 0.25 | 333.8 | 450 | PASS (script pass True) | 191.2 / 0.47 / 333.8 |
| 2 | pitch | 187.0 | 0.41 / 0.34 | 343.8 | 450 | PASS (script pass True) | 187.5 / 0.41 / 343.8 |
| 2 | yaw | 624.3 | 0.10 / 0.00 | 1173.8 | 1350 | PASS (script pass True) | 626.2 / 0.10 / 1173.8 |
| 3 | roll | 190.8 | 0.48 / 0.34 | 333.8 | 450 | PASS (script pass True) | 191.2 / 0.48 / 333.8 |
| 3 | pitch | 190.4 | 0.55 / 0.09 | 345.0 | 450 | PASS (script pass True) | 187.5 / 0.55 / 345.0 |
| 3 | yaw | 622.4 | 0.23 / 0.00 | 1177.5 | 1350 | PASS (script pass True) | 622.5 / 0.23 / 1177.5 |

Count: 9/9 PASS, key2 agrees on every rise, overshoot and settle (within 3 ms of key1 rise, 0.01 % overshoot, 0.3 ms settle). Worst roll/pitch settle 345.0 ms (pitch s3, limit 450), worst roll/pitch overshoot 0.80 % (roll s1, 5 %); yaw settle 1207.5 / 1173.8 / 1177.5 ms (limit 1350; worst 89 % of limit, seed 1), yaw overshoot <= 0.23 %, truth overshoot <= 0.88 %.
Comparison: freeze-8 pre-test (seed 1): roll 190.7 ms rise / 0.47 % / 345.0 ms, pitch 187.8 / 0.83 % / 326.3 ms, yaw 611.1 ms rise / 0.07 % / 1138.8 ms; here seed 1 yaw settle is 1207.5 ms (rise 625.6 ms), seeds 2 and 3 1173.8 / 1177.5 ms. First test S64 (g2_step_s64, 9/9): roll/pitch OS 0.64-1.29 %, settle 341-366 ms; yaw OS 0.18-0.37 %, settle 913-923 ms; the yaw settle rise relative to S64 is the one the pre-test already noted (cause not investigated there). Not verified here: the truth settle column (2.2 s for roll s3, NaN for yaw s3) is reported only, not a pass condition.
- NOTE: g5_rows_key2.py overwrites results/g5_events_s145/key2_rows.md as a side effect (hardcoded path); restored with git checkout after running.
