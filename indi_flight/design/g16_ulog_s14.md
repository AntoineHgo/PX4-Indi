# G1.6 ULog analysis, session 14 (skeleton)

Scope: 30 same-seed SITL flights, det_g16 (speed factor 1) and det_g16_s4 (speed factor 4).
Scenarios: hover, step_roll, traj_lemniscate; runs r1..r5.

## Task 1: arm and OFFBOARD instants
arm_s spreads (max-min, 5 runs): det_g16 hover 0.008, step_roll 0.512, traj_lemniscate 0.016; det_g16_s4 hover 0.588, step_roll 1.000, traj_lemniscate 0.508 s. offboard_s spreads: 0.004-0.016 s in all six groups. Full table in the script output below.

## Task 2: window.start_s vs OFFBOARD
window.start_s equals run.json t_window_start_us in 30/30 runs. Source: indi_flight/bench/run_scenario.py:615 sets t_offboard_us = sim.t when the harness sees main_mode == 6 (sim.run, lines 613-614); line 617 runs the 3.0 s offboard_settle; line 621 sets t_window_start_us = sim.t. window.start_s - offboard_s ranges 3.032 to 3.980 s (spread 0.948 s), so it is NOT constant. Example s4/hover/r5: t_offboard_us = 52.204 s vs ULog nav_state 14 at 52.032 s, so window start = harness detection lag + 3.0 s. The lag source is unverified.

## Task 3: det_g16_s4/hover/r5 max position deviation
s4/hover/r5: max_dev_3d = 0.0629 m (recomputed, matches metrics.json). Peak at t = 7.648 s into a 30.004 s window (mid-window; 7.6 s from start, 22.4 s from end). Axis D: (N, E, D) = (-0.0076, +0.0186, +0.0596) m. Not an edge peak. For comparison, s4/hover/r3 peaks at 29.996 s, i.e. the window end.

## Open items / unverified
- Arm outliers: det_g16_s4 step_roll r5 arms at 31.008 s and hover r4 at 30.600 s. Not investigated.
- Harness detection lag (task 2) mechanism not verified; the speed-4 spread may come from it.
- Assumes run.json (harness sim.t) and ULog share the time base, as metrics.py assumes.
- Task 1 offboard_s uses nav_state == 14 only; the 14/23 span start is identical in all 30 runs.

## Script output (tasks 1-3, auto-appended by /tmp scratchpad g16_s14.py)

## Task 1: arm and OFFBOARD instants (nav_state == 14), seconds, ULog time
| set | scenario | run | arm_s | offboard_s |
|---|---|---|---|---|
| det_g16 | hover | r1 | 30.016 | 52.024 |
| det_g16 | hover | r2 | 30.008 | 52.028 |
| det_g16 | hover | r3 | 30.012 | 52.020 |
| det_g16 | hover | r4 | 30.012 | 52.020 |
| det_g16 | hover | r5 | 30.012 | 52.020 |
| det_g16 | step_roll | r1 | 30.020 | 52.028 |
| det_g16 | step_roll | r2 | 30.524 | 52.028 |
| det_g16 | step_roll | r3 | 30.012 | 52.032 |
| det_g16 | step_roll | r4 | 30.016 | 52.024 |
| det_g16 | step_roll | r5 | 30.016 | 52.024 |
| det_g16 | traj_lemniscate | r1 | 30.020 | 52.028 |
| det_g16 | traj_lemniscate | r2 | 30.024 | 52.032 |
| det_g16 | traj_lemniscate | r3 | 30.020 | 52.028 |
| det_g16 | traj_lemniscate | r4 | 30.008 | 52.028 |
| det_g16 | traj_lemniscate | r5 | 30.020 | 52.028 |
| det_g16_s4 | hover | r1 | 30.016 | 52.024 |
| det_g16_s4 | hover | r2 | 30.012 | 52.020 |
| det_g16_s4 | hover | r3 | 30.016 | 52.036 |
| det_g16_s4 | hover | r4 | 30.600 | 52.032 |
| det_g16_s4 | hover | r5 | 30.012 | 52.032 |
| det_g16_s4 | step_roll | r1 | 30.164 | 52.028 |
| det_g16_s4 | step_roll | r2 | 30.008 | 52.020 |
| det_g16_s4 | step_roll | r3 | 30.312 | 52.032 |
| det_g16_s4 | step_roll | r4 | 30.016 | 52.028 |
| det_g16_s4 | step_roll | r5 | 31.008 | 52.020 |
| det_g16_s4 | traj_lemniscate | r1 | 30.016 | 52.024 |
| det_g16_s4 | traj_lemniscate | r2 | 30.016 | 52.024 |
| det_g16_s4 | traj_lemniscate | r3 | 30.524 | 52.020 |
| det_g16_s4 | traj_lemniscate | r4 | 30.252 | 52.032 |
| det_g16_s4 | traj_lemniscate | r5 | 30.400 | 52.024 |

Spread (max-min over 5 runs):
| set | scenario | arm spread_s | offboard spread_s |
|---|---|---|---|
| det_g16 | hover | 0.008 | 0.008 |
| det_g16 | step_roll | 0.512 | 0.008 |
| det_g16 | traj_lemniscate | 0.016 | 0.004 |
| det_g16_s4 | hover | 0.588 | 0.016 |
| det_g16_s4 | step_roll | 1.000 | 0.012 |
| det_g16_s4 | traj_lemniscate | 0.508 | 0.012 |

## Task 2: window.start_s vs offboard_s (nav14)
| set | scenario | run | metrics window.start_s | run.json t_window_start_s | offboard_s | diff = window.start_s - offboard_s | offboard (14/23) start_s |
|---|---|---|---|---|---|---|---|
| det_g16 | hover | r1 | 55.224 | 55.224 | 52.024 | 3.200 | 52.024 |
| det_g16 | hover | r2 | 55.568 | 55.568 | 52.028 | 3.540 | 52.028 |
| det_g16 | hover | r3 | 55.440 | 55.440 | 52.020 | 3.420 | 52.020 |
| det_g16 | hover | r4 | 55.368 | 55.368 | 52.020 | 3.348 | 52.020 |
| det_g16 | hover | r5 | 55.488 | 55.488 | 52.020 | 3.468 | 52.020 |
| det_g16 | step_roll | r1 | 55.932 | 55.932 | 52.028 | 3.904 | 52.028 |
| det_g16 | step_roll | r2 | 55.524 | 55.524 | 52.028 | 3.496 | 52.028 |
| det_g16 | step_roll | r3 | 55.444 | 55.444 | 52.032 | 3.412 | 52.032 |
| det_g16 | step_roll | r4 | 55.384 | 55.384 | 52.024 | 3.360 | 52.024 |
| det_g16 | step_roll | r5 | 55.564 | 55.564 | 52.024 | 3.540 | 52.024 |
| det_g16 | traj_lemniscate | r1 | 55.248 | 55.248 | 52.028 | 3.220 | 52.028 |
| det_g16 | traj_lemniscate | r2 | 55.576 | 55.576 | 52.032 | 3.544 | 52.032 |
| det_g16 | traj_lemniscate | r3 | 55.584 | 55.584 | 52.028 | 3.556 | 52.028 |
| det_g16 | traj_lemniscate | r4 | 55.528 | 55.528 | 52.028 | 3.500 | 52.028 |
| det_g16 | traj_lemniscate | r5 | 55.716 | 55.716 | 52.028 | 3.688 | 52.028 |
| det_g16_s4 | hover | r1 | 55.744 | 55.744 | 52.024 | 3.720 | 52.024 |
| det_g16_s4 | hover | r2 | 55.408 | 55.408 | 52.020 | 3.388 | 52.020 |
| det_g16_s4 | hover | r3 | 56.016 | 56.016 | 52.036 | 3.980 | 52.036 |
| det_g16_s4 | hover | r4 | 55.064 | 55.064 | 52.032 | 3.032 | 52.032 |
| det_g16_s4 | hover | r5 | 55.204 | 55.204 | 52.032 | 3.172 | 52.032 |
| det_g16_s4 | step_roll | r1 | 55.152 | 55.152 | 52.028 | 3.124 | 52.028 |
| det_g16_s4 | step_roll | r2 | 55.268 | 55.268 | 52.020 | 3.248 | 52.020 |
| det_g16_s4 | step_roll | r3 | 55.292 | 55.292 | 52.032 | 3.260 | 52.032 |
| det_g16_s4 | step_roll | r4 | 55.220 | 55.220 | 52.028 | 3.192 | 52.028 |
| det_g16_s4 | step_roll | r5 | 55.508 | 55.508 | 52.020 | 3.488 | 52.020 |
| det_g16_s4 | traj_lemniscate | r1 | 55.672 | 55.672 | 52.024 | 3.648 | 52.024 |
| det_g16_s4 | traj_lemniscate | r2 | 55.224 | 55.224 | 52.024 | 3.200 | 52.024 |
| det_g16_s4 | traj_lemniscate | r3 | 55.980 | 55.980 | 52.020 | 3.960 | 52.020 |
| det_g16_s4 | traj_lemniscate | r4 | 55.236 | 55.236 | 52.032 | 3.204 | 52.032 |
| det_g16_s4 | traj_lemniscate | r5 | 55.380 | 55.380 | 52.024 | 3.356 | 52.024 |

Diff over 30 runs: min 3.032 max 3.980 spread 0.948 s
max |metrics start - run.json start| = 0.00e+00 s

## Task 3: max 3D position deviation inside the metrics window
| set | scenario | run | max_dev_3d recomputed (m) | metrics.json (m) | t_peak rel window start (s) | window len (s) | min distance to edge (s) | location | axis of peak | N,E,D dev at peak (m) | sample idx / n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| det_g16 | hover | r1 | 0.0427 | 0.0427 | 24.112 | 30.000 | 5.888 | mid-window | N | +0.0418, +0.0036, -0.0076 | 3014 / 3751 |
| det_g16 | hover | r2 | 0.0386 | 0.0386 | 25.468 | 30.000 | 4.532 | mid-window | E | -0.0089, +0.0376, +0.0009 | 3183 / 3750 |
| det_g16 | hover | r3 | 0.0406 | 0.0406 | 1.000 | 30.000 | 1.000 | mid-window | N | -0.0381, -0.0140, +0.0008 | 125 / 3751 |
| det_g16 | hover | r4 | 0.0409 | 0.0409 | 19.476 | 30.012 | 10.536 | mid-window | N | +0.0377, -0.0064, +0.0143 | 2434 / 3752 |
| det_g16 | hover | r5 | 0.0416 | 0.0416 | 1.836 | 30.000 | 1.836 | mid-window | E | -0.0217, +0.0349, -0.0066 | 229 / 3750 |
| det_g16 | step_roll | r1 | 14.2315 | 14.2315 | 8.456 | 14.000 | 5.544 | mid-window | N | -14.2307, -0.1483, -0.0165 | 1057 / 1751 |
| det_g16 | step_roll | r2 | 14.3046 | 14.3046 | 8.448 | 14.000 | 5.552 | mid-window | N | -14.3043, -0.0635, -0.0725 | 1056 / 1751 |
| det_g16 | step_roll | r3 | 14.1680 | 14.1680 | 8.452 | 14.000 | 5.548 | mid-window | N | -14.1667, -0.1911, -0.0308 | 1056 / 1750 |
| det_g16 | step_roll | r4 | 14.3292 | 14.3292 | 8.460 | 14.000 | 5.540 | mid-window | N | -14.3284, -0.1549, -0.0294 | 1057 / 1750 |
| det_g16 | step_roll | r5 | 14.2707 | 14.2707 | 8.448 | 14.000 | 5.552 | mid-window | N | -14.2696, -0.1654, -0.0607 | 1056 / 1751 |
| det_g16 | traj_lemniscate | r1 | 3.9098 | 3.9098 | 6.764 | 23.220 | 6.764 | mid-window | N | +3.6801, -1.3200, -0.0337 | 845 / 2903 |
| det_g16 | traj_lemniscate | r2 | 3.8917 | 3.8917 | 6.760 | 23.220 | 6.760 | mid-window | N | +3.6638, -1.3123, -0.0071 | 845 / 2903 |
| det_g16 | traj_lemniscate | r3 | 3.9060 | 3.9060 | 6.756 | 23.220 | 6.756 | mid-window | N | +3.6770, -1.3178, -0.0130 | 844 / 2903 |
| det_g16 | traj_lemniscate | r4 | 3.8648 | 3.8648 | 6.760 | 23.220 | 6.760 | mid-window | N | +3.6351, -1.3125, -0.0093 | 845 / 2903 |
| det_g16 | traj_lemniscate | r5 | 3.8993 | 3.8993 | 6.752 | 23.220 | 6.752 | mid-window | N | +3.6860, -1.2715, -0.0259 | 844 / 2903 |
| det_g16_s4 | hover | r1 | 0.0325 | 0.0325 | 22.924 | 30.000 | 7.076 | mid-window | N | +0.0313, +0.0028, +0.0083 | 2864 / 3748 |
| det_g16_s4 | hover | r2 | 0.0472 | 0.0472 | 17.152 | 30.000 | 12.848 | mid-window | E | +0.0252, -0.0397, -0.0033 | 2143 / 3750 |
| det_g16_s4 | hover | r3 | 0.0376 | 0.0376 | 29.996 | 30.000 | 0.004 | edge (<1 s) | N | +0.0376, -0.0011, +0.0011 | 3744 / 3745 |
| det_g16_s4 | hover | r4 | 0.0367 | 0.0367 | 3.656 | 30.000 | 3.656 | mid-window | N | -0.0341, -0.0130, -0.0044 | 457 / 3749 |
| det_g16_s4 | hover | r5 | 0.0629 | 0.0629 | 7.648 | 30.004 | 7.648 | mid-window | D | -0.0076, +0.0186, +0.0596 | 946 / 3741 |
| det_g16_s4 | step_roll | r1 | 14.2044 | 14.2044 | 8.476 | 14.016 | 5.540 | mid-window | N | -14.2041, -0.0563, -0.0569 | 1057 / 1750 |
| det_g16_s4 | step_roll | r2 | 14.1698 | 14.1698 | 8.436 | 14.000 | 5.564 | mid-window | N | -14.1692, -0.1259, -0.0283 | 1054 / 1750 |
| det_g16_s4 | step_roll | r3 | 14.2935 | 14.2935 | 8.464 | 14.000 | 5.536 | mid-window | N | -14.2924, -0.1720, -0.0476 | 1058 / 1750 |
| det_g16_s4 | step_roll | r4 | 14.2108 | 14.2108 | 8.452 | 14.000 | 5.548 | mid-window | N | -14.2087, -0.2406, -0.0264 | 1055 / 1749 |
| det_g16_s4 | step_roll | r5 | 14.2316 | 14.2316 | 8.460 | 14.012 | 5.552 | mid-window | N | -14.2311, -0.1185, -0.0385 | 1056 / 1751 |
| det_g16_s4 | traj_lemniscate | r1 | 3.8644 | 3.8644 | 6.772 | 23.220 | 6.772 | mid-window | N | +3.6335, -1.3157, -0.0161 | 846 / 2897 |
| det_g16_s4 | traj_lemniscate | r2 | 3.8976 | 3.8976 | 6.768 | 23.220 | 6.768 | mid-window | N | +3.6581, -1.3449, -0.0273 | 843 / 2897 |
| det_g16_s4 | traj_lemniscate | r3 | 3.8742 | 3.8742 | 6.760 | 23.220 | 6.760 | mid-window | N | +3.6452, -1.3121, +0.0031 | 845 / 2900 |
| det_g16_s4 | traj_lemniscate | r4 | 3.9196 | 3.9196 | 6.740 | 23.220 | 6.740 | mid-window | N | +3.7036, -1.2831, -0.0167 | 842 / 2900 |
| det_g16_s4 | traj_lemniscate | r5 | 3.8790 | 3.8790 | 6.752 | 23.220 | 6.752 | mid-window | N | +3.6605, -1.2834, -0.0145 | 843 / 2902 |

max |recomputed - metrics.json| max_dev_3d = 0.00e+00 m
