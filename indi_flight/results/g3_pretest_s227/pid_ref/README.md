# G3 pretest S227: PID reference on the S227 INDI draw (index 0)

Command: `python3 indi_flight/results/g3_pretest_s227/pid_ref/fly_pid_s227.py` (log in `fly.log`), then
`bash indi_flight/results/g3_pretest_s227/pid_ref/run_pipeline.sh` (fly + key 1 via g3_score.sh + key 2 via g3_checks_key2.py).
Controller `pid_default`, base `g3_pretest_s187/pid_refs/pid_base.params`, seed 173, index 0, g3_lemniscate, 35 s hold, binary 903eae63 (checked).

Draw: identical (`draw` object equal to run_000's). Argv equal except controller. Flew: yes, returncode 0, outcome ok.

| item | PID key 1 | PID key 2 | INDI key 1 | INDI key 2 |
|------|-----------|-----------|------------|------------|
| 1 LOC / tilt / drop | PASS | PASS (items 1-3) | PASS | PASS |
| 2 oscillation | PASS | (items 1-3) | PASS | PASS |
| 3 steady state | PASS | (items 1-3) | PASS | PASS |
| 4 tracking (horiz RMS, limit 0.5 m) | FAIL (0.764 m) | FAIL (0.764 m) | PASS (0.421 m) | PASS (0.421 m) |
| 5 recovery (quiet err, limit 0.3 m) | FAIL (1.210 m) | FAIL (1.210 m) | FAIL (0.576 m) | FAIL (0.576 m) |
| 6 rate hold | PASS | PASS | PASS | PASS |
| overall | FAIL | FAIL | FAIL | FAIL |

Item 5 quiet error: PID 1.210 m (key 1 `position_m`, key 2 `max_err_after_return`), INDI 0.576 m.
Item 4 vertical RMS (limit 0.3 m): PID key 2 field not extracted; INDI 0.089 m.

Not verified: PID item 4 vertical RMS and per-item key 2 detail beyond pass/fail were not extracted.
Raw logs (`run_000/flight.ulg`, `*.gz`) are ignored by `pid_ref/.gitignore`.
