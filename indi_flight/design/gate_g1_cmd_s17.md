# Gate G1 commands (session 17)

One command per G1 item: `indi_flight/bench/gate_g1.sh <item> [args]` (bash, `set -euo pipefail`, works from any cwd).
Helper: `bench/g1_checks.py` (declared-rate table, G1.1 rule, G1.3 comparison, G1.6(a) check, own self-test).
Exit codes: 0 pass, 1 fail, 2 not implemented / usage. Only edit to an existing tool: `bench/g16_spread.py` writes its
`spread.json` to `$G16_SPREAD_OUT` when set (default unchanged), so the gate does not overwrite evidence files.
Not committed. Evidence set: `results/det_g16_w125/` (1.25 ms world, 800 Hz controller, IMU 800 Hz).

| item | command | sample result |
|---|---|---|
| G1.1 | `gate_g1.sh g1.1 RUN_DIR...` | FAIL (rc 1) |
| G1.2 | `gate_g1.sh g1.2` | not implemented, rc 2 |
| G1.3 | `gate_g1.sh g1.3 [SET_DIR]` | PASS on covered keys (35/35 agree); most primary metrics have no second key |
| G1.4 | `gate_g1.sh g1.4` | existing tests PASS, coverage incomplete (7 scripts without self-test) |
| G1.5 | `gate_g1.sh g1.5` | not implemented, rc 2 |
| G1.6 | `gate_g1.sh g1.6 BATCH_DIR` | (a) FAIL (matches the s17 verdict) |

## G1.1 declared rates and rule

Declared: sensor_gyro, vehicle_angular_velocity, actuator_motors, vehicle_torque_setpoint, esc_status at run.json `rate_hz`
(800 here); vehicle_local_position 125 Hz and vehicle_local_position_groundtruth 50 Hz (both read by `metrics.py` for
trajectory.estimate / trajectory.truth; the two fixed rates are the ones in `design/logging_profile.md`, they are not in run.json).
Sample times: `timestamp_sample` if present. Pass: median rate >= declared and max gap < 3 declared periods for samples
later than 1 s after the first sample (strict, so a gap of exactly 3 periods fails).

Run on r1 of hover, step_roll, traj_lemniscate (output trimmed to the unique conclusions):

```
| run | topic | declared Hz | median Hz | max gap ms | gap limit ms | verdict |
| hover/r1 | sensor_gyro | 800 | 800.0 | 7.5 | 3.8 | FAIL |
| hover/r1 | esc_status | 800 | 800.0 | 11.3 | 3.8 | FAIL |
| hover/r1 | vehicle_local_position | 125 | 88.9 | 11.3 | 24.0 | FAIL |
| hover/r1 | vehicle_local_position_groundtruth | 50 | 14.8 | 68.8 | 60.0 | FAIL |
| step_roll/r1 | sensor_gyro / angular_velocity / actuator_motors / torque_setpoint | 800 | 800.0 | 3.7 | 3.8 | pass |
| step_roll/r1 | esc_status | 800 | 800.0 | 5.0 | 3.8 | FAIL |
| traj_lemniscate/r1 | sensor_gyro ... torque_setpoint | 800 | 800.0 | 10.0 | 3.8 | FAIL |
| traj_lemniscate/r1 | esc_status | 800 | 800.0 | 11.2 | 3.8 | FAIL |
G1.1 verdict: FAIL
```

Observed (one extra look at hover/r1, not a script output): sensor_gyro has exactly one gap > 3 periods after the first second
(7.5 ms at t = 80.36 s, inside the evaluation window); logger dropouts 0. esc_status is jittery (61 gaps of 3.75 ms, median
800 Hz). The ground-truth topic is logged every 67.5 ms (54 physics steps), i.e. 14.8 Hz, not 50 Hz: the `logging_profile.md`
value (20 ms) was an inference from the producer rate and is not met in the log; `trajectory.truth` uses ~345 samples
in a 23 s window. vehicle_local_position is 88.9 Hz, not 125 Hz. Whether the declared 125 / 50 Hz are the right
requirements, and whether the single 7.5 ms gyro gap is a real logging hole or a sim-time stall, is NOT resolved here.

## G1.3 second keys

Covered: `window.start_s` (independent re-derivation of the armed offboard anchor + 3 s, tolerance 1 ms, same logic as
`second_key_window.py`) and `trajectory.{truth,estimate}.{rms_3d_m,max_dev_3d_m}` (`second_key_traj.py`, "window only"
scoring, 1 % or 1 mm). 15 runs: all window.start_s agree to < 1 ms; trajectory keys, example (traj r5):

```
| traj_lemniscate/r5 | trajectory.truth.rms_3d_m | 0.7311 | 0.7330 | agree |   (0.26 % rel)
| traj_lemniscate/r5 | trajectory.estimate.rms_3d_m | 0.4995 | 0.5000 | agree |
G1.3 compared keys: 35, disagreements: 0
```

Primary metrics with NO second key yet: rate_tracking (roll/pitch/yaw rms), attitude_tracking (rotation/roll/pitch/yaw rms),
hover position (rms / max_dev), steps (rise/settle/overshoot), effort (also rate dependent, A-11), disturbance (peaks,
recovery), motor_fault, control_allocator_status metrics, trajectory horizontal/vertical splits, rate_hz, zoh_legacy.
The window check was not wired to `second_key_window.py` itself because that script is hard-coded to det_g16 and det_g16_s4
and appends to a results file on every run; its logic was re-implemented in `g1_checks.py` (same 1 ms rule). The G1.3
absolute floors of 0.1 deg and 0.1 % FS are defined in `g1_checks.py` but unused (no covered attitude key).

## G1.4 self-tests

Run (pytest not installed on the host, so each test file runs with python3; the pytest branch is untested):
`tests/test_applied_timing.py` OK, `tests/test_metrics.py` ALL PASS, `a11_effort_rate.py --selftest` ok,
`second_key_traj.py --selftest` ok (rel err 4.2e-4), `g1_checks.py selftest` ok.
Scripts without a self-test: disturbance.py, model_variant.py, t3_analyze.py, timebase_check.py, second_key_window.py,
g16_spread.py, check_rates.py. Not checked: the "each test fails when its script is broken" part of G1.4 (lesson 20);
no closed-loop identification tests exist; metrics.py tests cover trajectory scoring and the window anchor only, not
rate/attitude/step/effort/disturbance metrics.

## G1.6 (a) mode instant

`gate_g1.sh g1.6 results/det_g16_w125` (runs `g16_spread.py`, then compares the spread of `window.ulog_anchor_s`, the ULog
armed-offboard instant stored in metrics.json, with 2 IMU periods; IMU rate 800 Hz default, override `G1_IMU_HZ`):

```
| hover | 5 | 11.25 | 800 | 2.50 | FAIL |
| step_roll | 5 | 7.50 | 800 | 2.50 | FAIL |
| traj_lemniscate | 5 | 7.50 | 800 | 2.50 | FAIL |
G1.6(a) verdict: FAIL
```
Same as the s17 verdict in GATES.md (NOT MET, 7.5-11 ms). Sub-items (b)-(d) are not automated.

## G1.2 and G1.5

Print "not implemented: needs simulator work (stage 1)" and exit 2.
