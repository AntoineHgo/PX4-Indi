# Port 1a: bench/metrics.py (gate G1 evidence), trajectory error fix

Files: `indi_flight/bench/metrics.py` (port of `indi_project/bench/metrics.py`, 384 -> 498 lines), `indi_flight/bench/tests/test_metrics.py`. Run: `python3 indi_flight/bench/tests/test_metrics.py`.

## Finding about the brief
`traj_phase` / `traj_pos` / `traj_pva` are NOT in the archive metrics.py. They live in
`indi_project/bench/run_scenario.py:323-358`. They are copied verbatim into `metrics.py:211-246` (keep in sync).

## What changed (everything else is byte-identical, checked with diff)
- `metrics.py:15-17`: `pyulog` import moved into `main()` (line 489), so the module imports without pyulog.
- `metrics.py:209-280`: copied trajectory functions, plus `analytic_reference`, `trajectory_error_analytic`,
  `trajectory_error_zoh` (legacy), `error_stats`, `rate_hz`: array-in/array-out, testable without a ULog.
- `compute()`, "trajectory scenarios" block (replaces archive 309-319): reference is
  `hold_pos_ned + traj_pos(traj_phase(traj, (t_us - t0_us)*1e-6))` (== `traj_pva(...)[0]`) at every position sample time.
  New `trajectory` fields: `truth` (vehicle_local_position_groundtruth, with `rate_hz`), `estimate` (vehicle_local_position),
  `zoh_legacy` (old result, with `setpoint_rate_hz`), `time_base`, `truth_minus_estimate_pre_t0_ned_m` (diagnostic, not applied).
- BREAKING: the old top-level `trajectory.rms_3d_m` etc. are removed on purpose; downstream readers must pick `truth` or `estimate`.
- Window is unchanged (evaluation window, includes settle and hold; the path is zero offset there, so no bias).

## Time base of t0_us
Not host wall-clock. `t0_us = int(t_seg0*1e6)` (`run_scenario.py:565`), `t_seg0 = sim.t` (`:563-564`), and `sim.t` is set from
MAVLink ATTITUDE `time_boot_ms*1e-3` (`run_scenario.py:229`): PX4 boot/sim time, ms resolution. `t_window_*_us` use the same
clock (`run_scenario.py:503,583`) and the metrics docstring already equates it with the ULog base. A guard flags `t0_us` outside the window.
Empirical check on archive run `results/s8g_zsine_delay/seed1` (zmulti): t0 35.845 s lies inside window 32.845-64.857 s,
ULog span 13.88-80.83 s, `compute()` ran clean. Rates there: estimate 125 Hz, groundtruth ~58.8 Hz (median), setpoint 5 Hz.

## Test output
```
ok trajectory functions (lemniscate peak speed 5.000 m/s)
ok lemniscate lag 100 ms: rms 0.2707 m vs d*v_rms 0.2710 m (50/200 ms, circle: within 0.5 %)
ok defect: ZOH perfect 0.301 m > ZOH 100ms-lag 0.157 m ; analytic perfect 0.0e+00 < lag 0.271 m
ok compute(): truth 0.0e+00, estimate(100ms lag) 0.271, zoh_legacy 0.157 m
ALL PASS
```

## UNVERIFIED
- That ULog `timestamp` and `time_boot_ms` agree to the ms: only plausibility (window inclusion). A fixed offset (e.g. one
  ATTITUDE tick, `sim.t` is the last seen tick) would add d*v error (5 m/s * 10 ms = 5 cm). Check by lag-scan on a real run.
- Groundtruth origin vs estimator origin: `truth` is scored against `hold_pos_ned` (taken from the estimator via MAVLink).
  Archive run shows a 3 cm offset (pre-t0 median); not corrected. Groundtruth is logged at ~59 Hz, not the estimator rate.
- Only one archive run was exercised; the full archive was not re-scored; nav_state==14 span was absent in that log (warning).
