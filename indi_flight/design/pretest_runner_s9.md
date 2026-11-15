# Pre-test: ported runner run_scenario.py, PID, quad5in

## Status: RUN OK

Command (run from repo root, background, wall timeout 900 s):
```
indi_project/docker/run.sh -n pretest_s9 -t 900 -- python3 indi_flight/bench/run_scenario.py \
    --scenario hover --controller pid_default --model quad5in --seed 1 --speed 1 \
    --out indi_flight/results/pretest_runner_s9
```
Stdout log: `indi_flight/results/pretest_runner_s9_stdout.log` (empty). Container exit 0.

## Checks
- run.json: exit_status "ok", error null, arm_attempts 1, hold 30.0 s in position mode, hold_pos_ned z -4.93 m.
- Airframe: px4.log line 13-17 `found model autostart file as SYS_AUTOSTART=4040`, `SYS_AUTOSTART: curr: 0 -> new: 4040`; line 29 `model: quad5in_0`. Confirms 4040_gz_quad5in loaded.
- flight.ulg present (24 MB).
- sends.csv: 1605 rows, columns kind, intended_sim_time_us, sim_time_before_us, sim_time_after_us, wall_time_s, wall_after_s, payload.
  - send_pos: 1600 rows. param: 5 rows. No other kinds.
  - intended_sim_time_us non-decreasing across the 1600 send rows: yes.
  - param sim_time_after - before: min/median/max = 14468 / 14468 / 14468 ms (all five identical; suspicious, see below).
- metrics.py: `python3 indi_flight/bench/metrics.py .../flight.ulg --run-json .../run.json` ran, wrote metrics.json, no warnings printed (exit status not separately captured).

## Unverified
- Why every param set takes exactly 14.468 s of sim time (likely a fixed wait in the runner; not investigated).
- Whether the 1600 sends match the scenario's setpoint count.
- Metric values and tracking quality (only that metrics.py runs).

## Orchestrator check (S9)
- The identical 14468 ms on the five param rows is not a jitter measurement: these are pre-arm params set before
  the first ATTITUDE message (self.t = 0), so `sim_time_before_us` = 0 and `sim_time_after_us` is the first
  ATTITUDE tick (PX4 boot). Pre-arm rows carry no timing information; `applied_timing.py` must skip rows with
  `sim_time_before_us` = 0. Only in-flight sends (setpoints, sag) are measured. Wall cost per param set ~12 ms.
