# KEY2: item-1 horizontal excursion vs trajectory setpoint (S186)

Implementation: indi_flight/bench/g3_checks_key2.py (`excursion()`, `LAND_NAV`, `--out DIR`); test: indi_flight/bench/tests/test_g3_excursion_key2.py.
Outputs: indi_flight/results/g3_excursion_s186/key2/run_NNN.json (full key-2 JSON; item1_loc holds excursion_m, excursion_sp_nan_frac, split fractions, span_s).

## Change
- Old: max horizontal distance from one fixed point (position at hold start) over the hold. Removed (`max_horiz_m` gone).
- New: max over [airborne start, min(airborne end, land/RTL start)] of |truth xy - setpoint xy|, setpoint (trajectory_setpoint position[0..1]) linearly interpolated onto the 800 Hz truth timestamps. A truth sample is excluded if outside the first/last setpoint time or if either bracketing setpoint sample has NaN x/y. Excluded fraction of span samples = `excursion_sp_nan_frac` (any reason; split in `excursion_sp_nan_only_frac` and `excursion_sp_outside_frac`). No usable sample -> excursion None (skipped, not failing). Limit 5.0 m unchanged. Computed only for scenario o1_lemniscate (position mode, as score.sh); others skipped.
- Airborne start/end: unchanged key-2 rule (h > mean(h[:800]) + 0.3 m). Land/RTL start: first vehicle_status nav_state in (5 RTL, 18 LAND, 20 PRECLAND), or run.json t_land_cmd_us if earlier (they agree within ~15 ms in run_000).
- Frame: key-2 applies NO alignment between sim_ground_truth and the estimator frame (truth x,y used raw; both NED, origin at arming position, start offsets about 0.01 m). The setpoint is compared raw, same treatment (code comment in excursion()).
- Item-1 other criteria (tilt, drop, NaN, ground contact) untouched.

## Logged rates (run_000)
sim_ground_truth 800 Hz (66124 samples); trajectory_setpoint 50.0 Hz (4134 samples, no NaN x/y in run_000 and run_017); vehicle_local_position 88.9 Hz.

## Self-test
`python3 indi_flight/bench/tests/test_g3_excursion_key2.py`: 6 tests PASS (1 m constant offset on a moving 20 m circle gives 1.000 m; 6 m departure gives 6.0 m and item 1 fails while the 1 m case passes; linear interpolation beats ZOH; NaN exclusion and fraction; no usable sample gives None; beyond-range exclusion). Existing `--self-test` and key-2 q14/q15 test unchanged (self-test PASS; pytest not installed, q14/q15 not re-run).

## Results (20 pre-test runs + run_017_pid_s185)
| run | new excursion (m) | sp_nan_frac | item-1 pass | span (s) |
|---|---|---|---|---|
| run_000 | 0.853 | 0.0000 | True | 34.5-83.3 |
| run_001 | 1.008 | 0.0000 | True | 33.1-83.4 |
| run_002 | 2.436 | 0.0000 | True | 34.3-83.4 |
| run_003 | 1.973 | 0.0000 | True | 32.8-83.3 |
| run_004 | skipped (non-position scenario) | - | True | - |
| run_005 | 1.997 | 0.0000 | True | 34.5-83.4 |
| run_006 | 0.857 | 0.0000 | True | 34.0-83.4 |
| run_007 | 0.960 | 0.0000 | True | 34.4-83.3 |
| run_008 | 1.001 | 0.0000 | True | 33.1-83.3 |
| run_009 | 1.284 | 0.0000 | True | 33.7-83.3 |
| run_010 | skipped (non-position scenario) | - | True | - |
| run_011 | 0.845 | 0.0000 | True | 33.0-83.4 |
| run_012 | 0.901 | 0.0000 | True | 33.7-83.3 |
| run_013 | 1.184 | 0.0000 | True | 34.3-83.3 |
| run_014 | 0.876 | 0.0000 | True | 34.3-83.3 |
| run_015 | 0.889 | 0.0000 | True | 33.4-83.3 |
| run_016 | skipped (non-position scenario) | - | True | - |
| run_017 | 1.455 | 0.0000 | False | 34.6-83.3 |
| run_017_pid_s185 | 1.306 | 0.0000 | True | 35.4-83.3 |
| run_018 | 1.001 | 0.0000 | True | 32.8-83.3 |
| run_019 | 0.907 | 0.0000 | True | 32.9-83.4 |

Notes: run_017 is the INDI run that fails. run_017_pid_s185 is the PID reference; its README quotes the old fixed-reference excursion 4.95 m for it.
