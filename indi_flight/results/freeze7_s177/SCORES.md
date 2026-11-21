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

## G5.3 / G5.4 (6 flights)
Commands (repo root, existing checkers, same as freeze-6 checks.sh; outputs in g5/): `python3 bench/g53_mission_check.py g5/auto_tour_sN --json g5/auto_tour_sN/g53.json` (G5.3 mission, `*.g53.check.txt`); `bench/auto_smoke_check.py <run> --json <run>/check.json` (G5.4, `<run>.check.txt`); `bench/g54_key2.py g5/auto_land10_s{1,2,3}` (`key2_g54.txt`); `bench/g54_land_key2.py` (`key2_g54_land.txt`). Not run: G5.3 hold (`gust_x`/hold_wind, not flown in this set).
All 6 flights: exit ok, no INVALID flag in any checker output, no phase missing.

G5.3 mission (wp 1.0 m acceptance, speed <= 5.5 m/s): all 4 waypoints reached, wp min dists below.
| flight | wp min dist 1/2/3/4 (m) | vmax (m/s) | verdict | invalid |
|---|---|---|---|---|
| auto_tour s1 | 0.760 / 0.764 / 0.813 / 0.034 | 5.196 | PASS | - |
| auto_tour s2 | 0.783 / 0.785 / 0.802 / 0.020 | 5.191 | PASS | - |
| auto_tour s3 | 0.817 / 0.746 / 0.777 / 0.050 | 5.199 | PASS | - |

G5.4 (take-off overshoot <= 0.5 m, bounce <= 0.3 m; ramp/edge step <= 10 % hover; dip <= 0.3 m; touchdown vz <= 0.8 m/s, tilt <= 10 deg, re-lift <= 0.15 m; land mean vz 0.70 +-20 %; contact->disarm <= 3.0 s; RTL height error <= 1 m):
| flight | overshoot (m) | bounce (m) | ramp max / edge step (% hover) | dip (m) | td vz (m/s) | td tilt (deg) | re-lift (m) | land mean vz (m/s) | contact->disarm (s) | RTL err (m) | verdict | invalid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| auto_tour s1 | -0.090 | 0.200 | 7.5 / 4.0 | 0 | 0.693 | 0.97 | 0.050 | 0.697 | 2.68 | 0.023 | PASS | - |
| auto_tour s2 | -0.075 | 0.200 | 7.5 / 4.0 | 0 | 0.698 | 0.40 | 0.049 | 0.693 | 2.68 | 0.034 | PASS | - |
| auto_tour s3 | -0.026 | 0.200 | 7.5 / 4.6 | 0 | 0.708 | 0.19 | 0.050 | 0.704 | 2.69 | 0.030 | PASS | - |
| auto_land10 s1 | -0.062 | 0.200 | 7.5 / 4.4 | 0 | 0.697 | 0.33 | 0.050 | 0.700 | 2.69 | n/a | PASS | - |
| auto_land10 s2 | -0.091 | 0.200 | 7.5 / 4.6 | 0 | 0.680 | 0.61 | 0.050 | 0.690 | 2.68 | n/a | PASS | - |
| auto_land10 s3 | -0.045 | 0.200 | 7.5 / 4.6 | 0 | 0.700 | 0.47 | 0.049 | 0.702 | 2.68 | n/a | PASS | - |
Key2 (g54_key2 / g54_land_key2) agrees on all 3 auto_land10 flights: td vz 0.680-0.700, tilt <= 0.61 deg, re-lift 0.05 m, edge step 4.4-4.6 %, land mean vz 0.696-0.705, contact->disarm 2.68-2.69 s, all PASS.

Worst case: G5.3 wp min dist 0.817 m (limit 1.0; freeze-6 0.946), vmax 5.199 m/s (limit 5.5; freeze-6 5.04); G5.4 overshoot -0.026 m (0.5), bounce 0.200 (0.3), ramp step 7.5 % / edge 4.6 % (10 %; freeze-6 4.0-4.6 %), td vz 0.708 (0.8; freeze-6 0.70), tilt 0.97 deg (10), re-lift 0.050 (0.15), RTL err 0.034 m (1). 6/6 PASS on both rows.
