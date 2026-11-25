# G3 pretest S227: one lemniscate flight (index 0), scorer check

Command: `bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_pretest_s227 0 0`
(binary 903eae63ceb1..., no `--allow-binary`, speed 1.0, started 2026-11-25 21:32:56, finished 21:35:29)

Lock: `indi_flight/logs/flight_chain.lock` was stale (empty, dated 2026-11-22, no chain pid, no container).

Index: 0 (lowest index in seed-173 draw). Draw scenario `g3_lemniscate` (mode position), confirmed by
`g3_run.py --dry-run --start 0 --stop 0`. Index 4 is the first `g3_stick_zsine`.

Flew: yes. `run.json` exit_status ok, error None, segments settle 3.0 s, traj 17.8 s, hold 35.0 s.
Outcome ok, `g3_done.json` returncode 0, validity valid.

| item | key 1 (g3_checks.json) | key 2 (key2/run_000.json) |
|------|------------------------|---------------------------|
| 1 LOC / tilt / drop | PASS | PASS |
| 2 oscillation | PASS | PASS |
| 3 steady state | PASS | PASS |
| 4 tracking (horiz 0.421 m, limit 0.5) | PASS | PASS |
| 5 recovery (quiet err 0.576 m, limit 0.3 m) | FAIL | FAIL |
| 6 rate hold | PASS (not rate mode) | PASS (not rate mode) |
| overall | FAIL | FAIL |

Scorers: both ran without errors (chain_key1.txt one argument line, chain_key2.txt no traceback).
Key 2 was not skipped. g4 chatter sustained: false for both keys.

Errors: none in chain_key1.txt, chain_key2.txt, g3_stdout.txt, or chain.log.

Topics in `run_000/flight.ulg` (checked by string match, not parsed; pyulog is not installed):
present: vehicle_attitude_setpoint, trajectory_setpoint, vehicle_angular_velocity, vehicle_rates_setpoint,
vehicle_attitude, vehicle_local_position, actuator_motors. Missing: none.
Keys read: trajectory_setpoint, vehicle_attitude_setpoint, actuator_motors, vehicle_status, vehicle_land_detected;
body rates via angular_velocity in the scorer code.

Not verified: ULog content was not parsed, so the topic check is a string match only.
The .ulg (184 MB) stays untracked.
