# O-12 watchdog replay over recorded flights

Script: `bench/watchdog_replay.py`. Thresholds: tilt > 60 deg for >= 0.5 s; height < 0.3 m; > 3.0 m below z setpoint for >= 1.0 s; non-finite attitude. Window: as the online watchdog, takeoff completion (t_offboard - 5 s) to the land command (t_window_end + 4 s) from run.json; without those keys, landed==false trimmed by 3 s at both ends.

- flight.ulg scanned: 3985
- parse failures / unusable (skipped): 0
- analysed: 3985

## Trips (100 trips in 48 runs)

| run | reason | t (s, log) | value | failure marks in run.json/metrics.json |
|---|---|---|---|---|
| runs/motor_loss_2/indi_tuned/seed1 | height < 0.3 m | 44.8 | 0.29 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed1 | > 3.0 m below z setpoint for >= 1.0 s | 44.9 | 4.76 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed10 | height < 0.3 m | 45.7 | 0.29 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed10 | > 3.0 m below z setpoint for >= 1.0 s | 45.8 | 4.77 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed2 | tilt > 60 deg for >= 0.5 s | 52.2 | 177.88 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed2 | height < 0.3 m | 43.0 | 0.30 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed2 | > 3.0 m below z setpoint for >= 1.0 s | 42.9 | 4.77 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed3 | height < 0.3 m | 42.7 | 0.29 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed3 | > 3.0 m below z setpoint for >= 1.0 s | 42.7 | 4.77 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed4 | height < 0.3 m | 42.6 | 0.28 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed4 | > 3.0 m below z setpoint for >= 1.0 s | 42.7 | 4.79 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed5 | tilt > 60 deg for >= 0.5 s | 57.8 | 179.97 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed5 | height < 0.3 m | 45.6 | 0.29 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed5 | > 3.0 m below z setpoint for >= 1.0 s | 45.6 | 4.77 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed6 | height < 0.3 m | 45.8 | 0.30 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed6 | > 3.0 m below z setpoint for >= 1.0 s | 55.6 | 5.40 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed7 | tilt > 60 deg for >= 0.5 s | 49.7 | 177.63 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed7 | height < 0.3 m | 45.7 | 0.30 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed7 | > 3.0 m below z setpoint for >= 1.0 s | 45.7 | 4.76 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed8 | tilt > 60 deg for >= 0.5 s | 56.8 | 176.81 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed8 | height < 0.3 m | 45.8 | 0.29 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed8 | > 3.0 m below z setpoint for >= 1.0 s | 52.7 | 4.70 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed9 | tilt > 60 deg for >= 0.5 s | 48.9 | 179.56 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed9 | height < 0.3 m | 45.8 | 0.30 | run.json:error=null |
| runs/motor_loss_2/indi_tuned/seed9 | > 3.0 m below z setpoint for >= 1.0 s | 45.8 | 4.78 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed1 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed1 | > 3.0 m below z setpoint for >= 1.0 s | 44.5 | 4.53 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed10 | height < 0.3 m | 44.6 | 0.30 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed10 | > 3.0 m below z setpoint for >= 1.0 s | 51.4 | 3.48 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed2 | height < 0.3 m | 41.4 | 0.30 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed2 | > 3.0 m below z setpoint for >= 1.0 s | 41.2 | 4.55 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed3 | height < 0.3 m | 44.6 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed3 | > 3.0 m below z setpoint for >= 1.0 s | 44.5 | 4.56 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed4 | height < 0.3 m | 45.6 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed4 | > 3.0 m below z setpoint for >= 1.0 s | 45.5 | 4.56 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed5 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed5 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.56 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed6 | height < 0.3 m | 41.5 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed6 | > 3.0 m below z setpoint for >= 1.0 s | 41.4 | 4.53 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed7 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed7 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.55 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed8 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed8 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.54 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed9 | height < 0.3 m | 44.4 | 0.29 | run.json:error=null |
| runs/motor_loss_2/pid_default/seed9 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.58 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed1 | height < 0.3 m | 51.9 | 0.30 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed1 | > 3.0 m below z setpoint for >= 1.0 s | 50.9 | 4.01 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed2 | height < 0.3 m | 50.4 | 0.30 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed2 | > 3.0 m below z setpoint for >= 1.0 s | 49.9 | 4.20 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed3 | height < 0.3 m | 52.8 | 0.30 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed3 | > 3.0 m below z setpoint for >= 1.0 s | 52.1 | 4.04 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed4 | height < 0.3 m | 50.0 | 0.30 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed4 | > 3.0 m below z setpoint for >= 1.0 s | 49.2 | 4.01 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed5 | height < 0.3 m | 52.5 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/indi_v2/seed5 | > 3.0 m below z setpoint for >= 1.0 s | 51.7 | 4.05 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed1 | height < 0.3 m | 39.8 | 0.30 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed1 | > 3.0 m below z setpoint for >= 1.0 s | 39.7 | 4.50 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed2 | height < 0.3 m | 43.3 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed2 | > 3.0 m below z setpoint for >= 1.0 s | 52.4 | 3.89 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed3 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed3 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.54 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed4 | height < 0.3 m | 41.3 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed4 | > 3.0 m below z setpoint for >= 1.0 s | 50.9 | 3.89 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed5 | height < 0.3 m | 45.3 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_default/seed5 | > 3.0 m below z setpoint for >= 1.0 s | 54.8 | 3.83 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed1 | height < 0.3 m | 44.7 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed1 | > 3.0 m below z setpoint for >= 1.0 s | 54.5 | 3.94 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed2 | height < 0.3 m | 42.2 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed2 | > 3.0 m below z setpoint for >= 1.0 s | 50.6 | 4.70 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed3 | tilt > 60 deg for >= 0.5 s | 50.4 | 178.97 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed3 | height < 0.3 m | 42.4 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed3 | > 3.0 m below z setpoint for >= 1.0 s | 42.4 | 4.67 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed4 | height < 0.3 m | 45.4 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed4 | > 3.0 m below z setpoint for >= 1.0 s | 45.4 | 4.66 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed5 | height < 0.3 m | 44.5 | 0.29 | run.json:error=null |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed5 | > 3.0 m below z setpoint for >= 1.0 s | 44.4 | 4.66 | run.json:error=null |
| s2_seen_v2/runs/step_pitch/pid_default/seed2 | tilt > 60 deg for >= 0.5 s | 56.4 | 179.91 | run.json:error=null |
| s2_seen_v2/runs/step_yaw/indi_v2/seed2 | height < 0.3 m | 49.8 | -0.25 | run.json:error=null |
| tuning/indi/r2/c05/rate_step_roll/seed1_x4 | height < 0.3 m | 66.5 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/rate_step_roll/seed1_x4 | > 3.0 m below z setpoint for >= 1.0 s | 66.1 | 4.53 | run.json:error=null |
| tuning/indi/r2/c05/rate_step_roll/seed3_x4 | height < 0.3 m | 72.3 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/rate_step_roll/seed3_x4 | > 3.0 m below z setpoint for >= 1.0 s | 72.3 | 4.69 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed1_x4 | height < 0.3 m | 51.9 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed1_x4 | > 3.0 m below z setpoint for >= 1.0 s | 63.2 | 4.16 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed2_x4 | height < 0.3 m | 45.8 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed2_x4 | > 3.0 m below z setpoint for >= 1.0 s | 56.3 | 5.95 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed3_x4 | height < 0.3 m | 51.9 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_pitch/seed3_x4 | > 3.0 m below z setpoint for >= 1.0 s | 63.3 | 4.94 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed1_x4 | height < 0.3 m | 57.4 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed1_x4 | > 3.0 m below z setpoint for >= 1.0 s | 68.4 | 4.54 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed2_x4 | height < 0.3 m | 52.4 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed2_x4 | > 3.0 m below z setpoint for >= 1.0 s | 63.2 | 4.87 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed3_x4 | height < 0.3 m | 52.3 | 0.29 | run.json:error=null |
| tuning/indi/r2/c05/step_roll/seed3_x4 | > 3.0 m below z setpoint for >= 1.0 s | 63.6 | 4.18 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed1_x4 | height < 0.3 m | 51.4 | 0.28 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed1_x4 | > 3.0 m below z setpoint for >= 1.0 s | 67.1 | 3.56 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed2_x4 | height < 0.3 m | 51.2 | 0.28 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed2_x4 | > 3.0 m below z setpoint for >= 1.0 s | 67.4 | 3.67 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed3_x4 | height < 0.3 m | 45.3 | 0.28 | run.json:error=null |
| tuning/indi/r2/c05/step_yaw/seed3_x4 | > 3.0 m below z setpoint for >= 1.0 s | 60.5 | 4.98 | run.json:error=null |

## Margins over all analysed runs

Percentiles over runs (p50 / p99 / max; for min-type values p50 / p1 / min), inside the airborne window.

| quantity | threshold | p50 / p99 / max |
|---|---|---|
| max tilt, any instant (deg) | - | 42.86 / 51.42 / 180.00 |
| tilt level held >= 0.5 s (deg) | > 60 trips | 40.08 / 45.02 / 179.93 |
| min height -z (m) | < 0.3 trips | 4.85 / -0.13 / -2.26 |
| max depth below z setpoint, instant (m) | - | 0.06 / 4.99 / 7.25 |
| depth below z setpoint held >= 1.0 s (m) | > 3.0 trips | 0.01 / 4.46 / 6.92 |

Runs without a usable z setpoint are excluded from the setpoint rows; runs counted there: 3985 of 3985.

### Highest sustained tilt (held 0.5 s)

| run | tilt held 0.5 s (deg) | max tilt (deg) | min height (m) |
|---|---|---|---|
| runs/motor_loss_2/indi_tuned/seed8 | 179.9 | 180.0 | -1.84 |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed3 | 179.9 | 180.0 | -1.83 |
| runs/motor_loss_2/indi_tuned/seed9 | 179.9 | 180.0 | -2.26 |
| runs/motor_loss_2/indi_tuned/seed2 | 179.8 | 180.0 | -1.69 |
| runs/motor_loss_2/indi_tuned/seed5 | 179.7 | 180.0 | -1.81 |
| s2_seen_v2/runs/step_pitch/pid_default/seed2 | 152.7 | 179.9 | 4.56 |
| runs/motor_loss_2/indi_tuned/seed7 | 74.5 | 177.6 | -1.17 |
| s2_seen_v2/runs/step_pitch/indi_v2/seed2 | 59.2 | 179.5 | 2.10 |

### Lowest height

| run | min height (m) |
|---|---|
| runs/motor_loss_2/indi_tuned/seed9 | -2.26 |
| runs/motor_loss_2/indi_tuned/seed8 | -1.84 |
| s2_seen_v2/runs/motor_loss_2/pid_tuned/seed3 | -1.83 |
| runs/motor_loss_2/indi_tuned/seed5 | -1.81 |
| runs/motor_loss_2/indi_tuned/seed2 | -1.69 |
| runs/motor_loss_2/indi_tuned/seed7 | -1.17 |
| runs/motor_loss_2/indi_tuned/seed6 | -0.41 |
| tuning/indi/r2/c05/step_pitch/seed3_x4 | -0.35 |

## Interpretation (orchestrator, session 44; hand-written, not regenerated by the script)

- First replay (landed-flag window) also flagged tip-overs at touchdown; the window now matches the online watchdog
  (takeoff completion to land command, from run.json). Margins inside it: sustained tilt p99 45 deg (trip 60),
  height-deficit p99 4.5 m only because of the crashing runs below.
- H4 motor_loss_2 (both families, v1 and v2): known crashes, trips expected.
- v1 INDI r2 c05 (ACT_TC 0.0084, J 35.9 in `tuning/indi/r2/summary.csv`): every run sinks to the ground. A known
  bad candidate that scored as a huge J instead of a failure: the case O-12 is meant to abort. Correct trip.
- Seen set v2 seed 2 (step_yaw indi_v2, step_pitch pid_default / indi_v2, flown ~22:41): NOT a controller failure.
  Local-position height runs to 35 m at -17 m/s in 4 s and snaps back to -0.3 m (estimator glitch), no failsafe,
  offboard throughout. At that time the session-43 replay (4 workers) was loading the host on top of 6 sims; the
  session-44 replays (22:58-23:05, ~23:15-23:22) did the same. Suspected infrastructure fault (host overload); the
  affected (entry, seed) pairs must be identified and re-flown for all controllers (D-v2-refly rule).
- No threshold change needed: no trip on a run that was flying normally.
