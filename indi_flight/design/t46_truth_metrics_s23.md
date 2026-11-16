# T46 truth metrics and time bases (session 23)

Status: done (not committed). Files changed: `bench/metrics.py`, `bench/g1_checks.py`, `bench/tests/test_metrics.py`. No thresholds in GATES.md touched.

## Diff summary (bench/metrics.py)
- New `tstamp(d)`: `timestamp_sample` if the field exists and every value is > 0, else `timestamp`.
- New `ctrl_topic(ulog, name, notes)`: returns a copy of the topic dict whose `"timestamp"` is `tstamp(d)`, stable-sorted (all columns) if that stamp is not monotonic. Original publish stamp kept as `timestamp_publish`. Per topic it records `{stamp, sorted, zero_dt_pairs}` in `metrics.json` -> `stamps`. Downstream code is unchanged because it already reads `d["timestamp"]`.
- New `truth_local_position(ulog, notes)`: `sim_ground_truth` when logged, else `vehicle_local_position_groundtruth` (archived logs), else `(None, None)`. Result in `metrics.json` -> `truth_source`.
- `compute()`: `vehicle_angular_velocity`, `vehicle_rates_setpoint`, `actuator_motors`, `vehicle_attitude`, `vehicle_attitude_setpoint`, `indi_pos_status` now via `ctrl_topic`; trajectory truth via `truth_local_position`; motor_fault metrics now receive the converted att/asp/am; warning text updated for missing truth.
- Unchanged on purpose: origin handling (`truth_minus_estimate_pre_t0_ned_m` stays a diagnostic, NOT applied; truth and estimate are both NED, same hold_pos reference), windowing, vehicle_status (event topic, `timestamp`), `vehicle_local_position` (estimator output, 88.9 Hz, no zero-dt; kept on `timestamp`), trajectory_setpoint, control_allocator_status.
- `vehicle_rates_setpoint`, `vehicle_attitude_setpoint` have no timestamp_sample in the log -> fall back to `timestamp` (recorded in `stamps`).

## g1_checks.py
- DECLARED: the three `*_groundtruth` rows replaced by one row `sim_ground_truth` (declared = controller rate; same rate and gap rule, GAP_PERIODS=3). Rows read `timestamp_sample` already.

## Self-tests
- `python3 bench/tests/test_metrics.py`: ALL PASS (existing 5 + new `test_sample_stamp_over_publish_stamp`; end-to-end test now feeds `sim_ground_truth` and asserts `truth_source`). `python3 bench/g1_checks.py selftest`: ok.
- New test: actuator_motors with 1000 zero-dt publish-stamp pairs and a clean timestamp_sample; asserts stamp=timestamp_sample, zero_dt_pairs=0, motor_rate_rms in 3.2..3.9 /s (got 3.554), and that the publish stamp gives a >5 % different value (3.078). Also covers sorting of a non-monotonic stamp and truth source selection (sim wins, fallback, none).
- Broken once: `tstamp` forced to ignore timestamp_sample -> the new test FAILED (AssertionError: stamp 'timestamp', zero_dt_pairs 1000). Restored (diff vs backup identical), test passes. Note: a stale `.pyc` made the first post-restore run still fail; deleting `bench/__pycache__/*.pyc` fixed it (mtime-second + size collision), the code was fine.

## Before / after, hover log results/a15_s21/hover/flight.ulg (truth_source = sim_ground_truth; old = HEAD metrics.py)
Hover has no trajectory block, so no truth-based metric exists for it: position.* uses vehicle_local_position (estimate, unchanged). Only stamp changes act.

| metric | old | new | diff % |
|---|---|---|---|
| rate_tracking roll/pitch/yaw rms rad/s | 7.978e-4 / 8.608e-4 / 3.297e-4 | 7.978e-4 / 8.605e-4 / 3.297e-4 | 0.006 / 0.026 / 0.002 |
| attitude rotation_angle / roll / pitch / yaw rms deg | 0.04407 / 0.03343 / 0.03884 / 0.01192 | 0.04405 / 0.03340 / 0.03882 / 0.01192 | 0.062 / 0.074 / 0.057 / 0 |
| position rms 3d / horiz / vert m, max_dev_3d | 0.01910 / 0.01751 / 0.00763 / 0.04224 | identical | 0 |
| effort.motor_rate_rms_per_s | 0.006780 | 0.006790 | 0.137 |
| effort motor_mean, spread, saturation, allocator.* | | identical | 0 |

All differences < 1 %. Rate/attitude shifts are the sub-tick re-alignment of ZOH pairs; motor_rate shifts because 856 zero-dt pairs of actuator_motors (and 324 of vehicle_angular_velocity) change the stamp axis (old code skipped dt<=0 pairs, new stamps have none). In new.json all `stamps.*.zero_dt_pairs` = 0, none needed sorting. Scratch: /tmp/claude-1001/t46/{old,new}.json, metrics_old.py.

## g1.1 on the same log (rate_hz 800)

| topic | median Hz | max gap ms | limit ms | verdict |
|---|---|---|---|---|
| sensor_gyro | 800.0 | 5.0 | 3.8 | FAIL |
| vehicle_angular_velocity | 800.0 | 6.3 | 3.8 | FAIL |
| actuator_motors | 800.0 | 6.3 | 3.8 | FAIL |
| vehicle_torque_setpoint | 800.0 | 6.3 | 3.8 | FAIL |
| esc_status | 800.0 | 6.3 | 3.8 | FAIL |
| vehicle_local_position (88) | 88.9 | 15.0 | 34.1 | pass |
| sim_ground_truth | 800.0 | 5.0 | 3.8 | FAIL |

Verdict FAIL (exit 1). sim_ground_truth and sensor_gyro each have exactly ONE gap > 3.75 ms: 5.0 ms (4 ticks) at 54.58 s into the stream, identical in both, so it looks like a simulator step-timing event, not logger loss. The 6.3 ms gaps on controller topics: not diagnosed here (a16 late-publish pairing suspected). Pre-existing, not caused by this change.

## Open / unverified
- Rate and attitude tracking are still scored estimator vs setpoints, as before; no truth-based rate/attitude metric was added (task only repointed existing truth reads; only trajectory.truth exists). The comment in g1_checks.py says tracking is "scored against truth": not yet true in metrics.py.
- trajectory.truth with sim_ground_truth is exercised only by the synthetic end-to-end test, not on a real trajectory log.
- Archived logs without sim_ground_truth now FAIL (MISSING) in g1.1 by design.
- Old-topic fallback now also uses timestamp_sample (was timestamp): few-ms shift possible on archived trajectory truth.
