# Port 1a: applied-timing measurement (G1)

## Built
- `bench/applied_timing.py run_dir [...]`: per send kind prints n / matched / unmatched / pre_log / multi-match /
  changed-payload counts and delay p50/p95/max in us and physics steps (4 ms, `physics_step_us` in run.json or
  `--physics-step-us`); with several run dirs also a cross-run table. Writes `applied_timing.json` per run dir.
- Matching is pure numpy (`match_first`, `match_param`, `compute_rows`, `summarize`), pyulog imported lazily.
  Rule: first logged sample with t >= intended and within `--window-s` (2 s) whose payload fields equal the
  columns within `--tol` (1e-3, NaN never matches); several matches -> first. Unmatched rows are counted, not dropped.
- `bench/tests/test_applied_timing.py`: synthetic known-delay log incl. unmatched row, 3-sample match (first used),
  sample-before-intended (not matched), param/sag/pre-log, constant-payload caveat. Passes.
- Mapping: send_pos/send_pva -> trajectory_setpoint; param/sag -> ULog changed_parameters.

## Real run `results/pretest_runner_s9` (hover, PX4 position hold via offboard, 1600 send_pos, 5 param)
- send_pos: 1592 matched, 8 unmatched (all intended >= 68.308 s, after the hold window; trajectory_setpoint there no
  longer equals the hold payload; cause not investigated). Delay p50 104 ms (26 steps), p95 184 ms (46), max 1204 ms.
- With offboard active (intended >= 31.456 s, 1494 rows): p50 84 ms, p95 184 ms, max 192 ms.
- **This is not command latency.** trajectory_setpoint is logged at 5 Hz (median period 200 ms) and the hold payload is
  constant, so every sample matches: delay = wait for the next logged sample (~uniform 0..200 ms). Only 1 row has a
  changed payload. The 98 rows before offboard (max 1.2 s) match flight-task output that coincides with the hold
  position; they are also not evidence of application.
- param (5 rows, intended_us=0 because sent before the first ATTITUDE tick): 0 matched, 5 pre_log. The log starts at
  14.484 s, after those sets; initial_parameters already hold the new values. Unmeasurable from this ULog.
  The log has only 1 changed_parameter record (CAL_BARO0_OFF).

## What this means for G1
- Resolution is limited by the logged topic period, 200 ms, vs 4 ms physics step. The tool cannot bound jitter of
  setpoints below that with this log; it needs a higher trajectory_setpoint log rate (SDLOG_PROFILE / logger topic
  rate for trajectory_setpoint) and a moving payload (circle/lemniscate/step), where `changed` rows are informative.
- Param/sag timing needs sends after log start and parameter changes in the log (unverified, see below).

## Unverified
- send_att / send_rate column mapping (vehicle_attitude_setpoint q_d->euler, thrust_body[2] sign;
  vehicle_rates_setpoint) is untested on a real log.
- Whether a mid-flight set_param (e.g. SIM_GZ_THR_SC sag) produces changed_parameters entries; plant-effect
  fallback (ESC/actuator change) is not implemented.
- Cross-run comparison printed only by code path, run on a single dir; ULog time base == sim time assumed (as metrics.py).
