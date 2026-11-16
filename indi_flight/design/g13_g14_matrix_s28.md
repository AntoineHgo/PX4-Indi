# G1.3 (two keys) / G1.4 (self-tests) evidence matrix, gate-bearing metrics, session 28

Scope: metrics named in `design/route_check_27.md` item 2. Source: `bench/metrics.py` (line numbers as of this session),
`bench/tests/test_metrics.py` (plain-assert runner: `cd indi_flight/bench && python3 tests/test_metrics.py`; pytest is NOT installed on the host).
Second-key scripts present: `second_key_t46.py`, `second_key_traj.py`, `second_key_window.py`, `second_key_player.py`, `second_key_t55.py`
(and `g16_spread.py`, which is a same-seed spread tool, not a second key). Nothing was run on simulator logs this session.

## Matrix

"Break-checked" = the new or existing test was shown to FAIL when the metric was deliberately broken (see break-check log). Existing tests: NO (no file says otherwise).

| # | Gate-bearing metric | metrics.py | Second key | Logs compared, result (README) | Self-test | Analytic answer? | Break-checked |
|---|---|---|---|---|---|---|---|
| 1 | Rate tracking error (rms of ZOH rate setpoint minus measured rate, per axis) | `compute` L383-395 (`rt[...]` L394), `zoh` L84, `rms` L78 | `second_key_t46.py` (`window_metrics`, rate RMS roll/pitch/yaw) | `a15_s21/hover` only, one log: AGREE (all < 0.01 % on the metrics.py window; 2.1 % roll miss on a different window was a window effect). `results/second_key_t46_s23/README.md` | `test_rate_tracking_analytic` (NEW, L216) | YES (0.2, 0.5/sqrt2, 0.05, ZOH step sqrt(3/4)) | YES (sign flip, wrong axis) |
| 2 | Attitude tracking error (rotation angle, roll/pitch/yaw rms vs q_d) | `compute` L397-421 (`ang` and `wrap` use), `quat_to_euler` L92, `wrap` L100 | NONE | none | `test_attitude_tracking_analytic` (NEW, L239) | YES (0.1 rad offset = 5.7296 deg; yaw wrap across +-pi = 0.02 rad; q_d sign flip invariance) | YES (wrap dropped, angle factor 2 dropped, abs(dot) dropped) |
| 3 | Motor effort: `motor_rate_rms_per_s` (rms of first difference of actuator_motors) | `compute` L530-548 (`eff`, L541) | `second_key_t46.py` (`fd_rms`) | `a15_s21/hover` only: AGREE (0.006788 vs 0.006790 /s, -0.03 %) on the metrics.py window; spec window DISAGREE only because it included a nav_state 18 segment. | `test_sample_stamp_over_publish_stamp` (L144) | PARTIAL: range 3.2-3.9 /s around analytic 3.55 /s, not a tight value; checks the stamp choice, not the rms formula | NO |
| 4 | Hover position deviation (`position.rms_3d/horizontal/vertical`, `max_dev_*`) | `compute` L458-470 | NONE (`second_key_traj.py` covers trajectory scenarios only; `second_key_t55` check 3 compares setpoints, not this metric) | none | NONE (only the window and trajectory paths are tested; `position` is never asserted) | n/a | n/a (candidate for the next self-test) |
| 5 | Step response: delay, rise 10-90, overshoot, settle 5 %, final error | `step_metrics` L139-172, driver L423-457 | NONE for the response metrics. `second_key_t55` check 2 "roll steps AGREE" appears to compare step event timing/amplitude with the schedule (INFERRED from the summary table only, not read) | `det_g16`/t55 step_roll logs for the timing check only | `test_step_metrics_analytic` (NEW, L180) | YES (tau ln 9, tau ln 20, tau ln(1/0.9), exp(-pi z/sqrt(1-z^2)) = 16.30 %, negative step, floor skip, not settled) | YES (rise sign, overshoot x10, settle band 5 -> 10 %) |
| 6 | Trajectory tracking error vs analytic reference (truth and estimate) | `trajectory_error_analytic` L338, `analytic_reference` L330, `traj_phase` L279, `traj_pos` L297, `error_stats` L322 | `second_key_traj.py` | Archive runs s8g, o1 (lemniscate), o2 (circle_z), one seed each: AGREE to 3 digits (o1 0.7178/0.6481 m, o2 0.8188/0.7350 m, s8g 0.0547/0.0368 m). Key's author saw archive metrics.json, so not fully blind. `results/second_key_traj.md` | `test_exact_and_lag`, `test_trajectory_functions`, `test_zoh_defect_and_fix`, `test_compute_end_to_end` (L36-L122) | YES (exact 0; lag d gives d*v_rms within 5 %) | NO |
| 7 | Input of the spectral oscillation detector | does not exist in `metrics.py` | NONE | none | NONE | n/a | n/a. "spectral" appears only in `design/route_check_10/22/27.md`; no detector or detector input is implemented yet. |
| 8 | (supporting) Evaluation window start/end | `offboard_anchor_us` L114, `compute` L351-382 | `second_key_window.py` | `det_g16` hover/step_roll/traj_lemniscate x r1..r5, 30 runs: AGREE, max diff 0.000000 ms (`results/second_key_window_s15.md`) | `test_window_anchor_from_ulog` (L124) | YES | NO |

Counts (rows 1-7, rate/attitude/effort/hover/step/trajectory/spectral):
- with a recorded second-key AGREE: 3 of 7 (rate, effort, trajectory); rate and effort rest on ONE hover log (`a15_s21/hover`); G1.3 needs >= 5 logs spanning hover, steps, trajectory, disturbance, so none of the three meets the gate yet.
- NO second key: attitude, hover position, step response metrics, spectral input (nonexistent).
- with a self-test with a known analytic answer: 5 of 7 (rate, attitude, step, trajectory, plus effort partial); hover position and spectral have none.
- break-checked: 3 of 7 (rate, attitude, step; all three new this session); trajectory, effort, window tests not break-checked.

## Break-check log (session 28)

Method: copy of `metrics.py` kept in the scratchpad, one edit at a time, `python3 -B tests/test_metrics.py`, `__pycache__` cleared before each run
(a first attempt without that was discarded: same-size edits within one second can reuse a stale .pyc; those results were not used).
Restored byte-identical afterwards (`cmp` against the saved copy, `git diff metrics.py` empty).

| Metric | Edit to metrics.py | Result |
|---|---|---|
| step_metrics | rise `t90 - t10` -> `t90 + t10` | `test_step_metrics_analytic` FAILS |
| step_metrics | overshoot `* 100.0` -> `* 10.0` | FAILS (1.63 vs 16.30 %) |
| step_metrics | settle band 0.05 -> 0.10 | FAILS |
| rate_tracking | `rms(sp - av)` -> `rms(sp + av)` | `test_rate_tracking_analytic` FAILS |
| rate_tracking | axis index `xyz[{i}]` -> `xyz[0]` | FAILS (pitch 0.30, yaw 0.35 reported) |
| attitude_tracking | `e = wrap(e)` -> `e = e` | `test_attitude_tracking_analytic` FAILS (yaw 358.85 deg) |
| attitude_tracking | `2 * np.arccos` -> `np.arccos` | FAILS (2.86 vs 5.73 deg) |
| attitude_tracking | `np.abs(dot)` -> `dot` | FAILS (180 deg for the sign-flipped q_d) |

Unbroken run after restore: ALL PASS (all 9 test functions).

## Metrics in metrics.py that no G2-G5 verdict would read: "single key, not gate-bearing"

Judged from the route-check list only; GATES.md G2-G5 rows were not re-read for this, so confirm before relying on it.
- `disturbance_metrics` L175 (peak deviations, recovery_s) and `motor_fault_metrics` L234 (tilt error, saturation_time_s, motor means). No test, no second key.
- Effort extras: `motor_spread_mean_abs`, `motor_mean`, `saturation_frac_motors/high/low` (L541-549), `allocator.*` (L557). No test, no second key. (If a later gate uses saturation as a pass/fail, promote it.)
- `step_summary` aggregates (mean/max/n/`n_not_settled`), derived from #5.
- `trajectory.zoh_legacy` / `trajectory_error_zoh` L344: legacy defective metric, kept for errata (its defect is demonstrated in `test_zoh_defect_and_fix`).
- `trajectory.*.rate_hz`, `truth_minus_estimate_pre_t0_ned_m`, `time_base`: diagnostics.
- `error_stats` extras (`max_dev_3d_m`, horizontal and vertical splits) are covered only indirectly by test #6.

## Suspected defects / gaps (nothing fixed)

1. The gate wording "rate/attitude tracking error against simulator truth" is NOT what `metrics.py` computes. Rate tracking (L388-395) uses `vehicle_angular_velocity` (the estimate) and attitude tracking (L397-421) uses `vehicle_attitude` (the estimate); only position error has a truth variant (`sim_ground_truth`, L478-). `second_key_t46.py` logs `sim_ground_truth` and `sensor_gyro` gaps but its rate RMS also uses `vehicle_angular_velocity`. If truth rates/attitude are gate-required, a truth-based metric does not exist yet.
2. "Motor effort at a fixed bandwidth" is not what `motor_rate_rms_per_s` (L541) is: it is a raw first difference at the logged sample rate with no filter, so its value depends on the logging rate and sensor noise. The matrix row 3 verified the formula as implemented, not the fixed-bandwidth property.
3. `step_metrics` L158-165: `settle` is reported 0.0 when the response never leaves the 5 % band (including if it starts inside it), and `overshoot_pct` clamps at 0 (no undershoot information). Behaviour as designed, noted for the reader of G3 verdicts; not asserted wrong.
4. `compute` L401-409: attitude Euler errors are differences of Euler angles (roll/pitch not wrapped, only yaw is). Near pitch +-90 deg or large roll the per-axis numbers are not meaningful; `rotation_angle_rms_deg` is the safe one. Not a defect at hover/step amplitudes.

## Unverified

- The second-key results quoted were copied from the READMEs/markdown, not re-run (no ULog tooling run, per instruction).
- `second_key_t55` check 2 content was inferred from the README summary line.
- Test `test_sample_stamp_over_publish_stamp` and trajectory tests were not break-checked.
- Hover position deviation (row 4) still has neither a self-test nor a second key.
