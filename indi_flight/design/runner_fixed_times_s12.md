# Runner fixed arm/offboard times (s12)

Gate G1.6 (determinism). Source: `design/determinism_s11.md` (same-seed hovers: arm 15.37/17.57/17.54 s sim,
offboard 31.37/33.57/32.54 s; `window.start_s` followed, so each run measured another slice).
Cause: wall time spent before arming (param sets, logger restart + sleep, wait_log, arm retries) while the
lockstep sim runs, so sim time at arm varied. Fix: gate arm and offboard on sim time.

## Constants (`bench/run_scenario.py`, next to SETPOINT_PERIOD)
- `T_ARM_S = 20.0`: latest observed arm 17.57 s (includes retries), +2.4 s margin. If the vehicle is ready later,
  the arm is late and run.json shows `arm_late_s`.
- `T_OFFBOARD_S = T_ARM_S + 20 = 40.0`: arm->offboard was 15-16 s in s11 (climb ~8-10 s to 4.7 m + 5 s hover +
  1 s pre-stream + engage). 20 s leaves ~4 s margin on the 16 s case.
- `HOVER_MIN_S = 5.0`, `PRESTREAM_S = 1.0` (as before), `T_HOLD_S = T_OFFBOARD_S - PRESTREAM_S = 39.0`
  (hold_pos / hold_yaw captured here), `LATE_TOL_S = 0.1`.
- Climb deadline: climb must be done by `T_HOLD_S - HOVER_MIN_S = 34 s` (14 s after arm), else `RunError`
  (no silent slip).

## Diff summary (bench/run_scenario.py only)
- New constants block after SETPOINT_PERIOD.
- New `run_metrics(out_dir)` before `git_info()`: subprocess `sys.executable metrics.py flight.ulg --run-json
  run.json --out metrics.json`, timeout 300 s, never raises, returns a status string.
- `main()` arm sequence: after `sim.run(1.0, "warmup")` (this is what makes sim.t valid: it is 0.0 until the
  first ATTITUDE is pumped, connect() does not pump) record `t_arm_target_s`, `t_offboard_target_s`,
  `t_before_arm_wait_s`, then `sim.run(None, until=sim.t >= T_ARM_S, wall_timeout=...)`, then the existing retry
  loop. New run.json keys: `t_arm_sent_s`, `arm_rejected_t_s` (list), `arm_late_s` (only if the arm succeeded later
  than T_ARM_S + 0.1 s; a rejected first arm costs 1 s per retry and shows up there).
- Climb: `until` also stops at `sim.t > T_HOLD_S - HOVER_MIN_S`, then RunError if altitude not reached. Records
  `t_climb_done_s`.
- Hover: `sim.run(5.0)` replaced by run until `sim.t >= T_HOLD_S`, then hold capture; records `t_hold_s`.
- Pre-stream: `sim.run(1.0, sp)` replaced by stream until `sim.t >= T_OFFBOARD_S`; records `t_offboard_sent_s`
  and `offboard_late_s` (if > 0.1 s late; the hover_thrust CLI call between hold capture and the stream costs
  wall time = sim time). Existing `t_arm_us`, `t_offboard_us` kept.
- `finally`: after the existing run.json dump (metrics needs run.json on disk for the window), if `flight.ulg`
  exists run metrics, set `meta["metrics_status"]` ("ok" / "failed rc=..: ..." / "skipped: no flight.ulg"),
  rewrite run.json. Metrics failure does not change `exit_status` or the return code.
- Every new sim.run has a wall_timeout.

## Tests
- `py_compile` OK. pytest is not installed on the host and `bench/tests/*.py` are plain-assert scripts ("no
  pytest" in their docstring): `python3 test_applied_timing.py` -> OK, `python3 test_metrics.py` -> ALL PASS.
- `run_metrics('/nonexistent')` returns a "failed rc=1: FileNotFoundError ..." string without raising.

## Unverified (needs a flight test)
- The climb duration estimate (~9-10 s) is derived from s11 arm->offboard minus 5+1+engage, not measured; other
  scenarios/models with slower climb could hit the 34 s deadline (RunError).
- Whether hover_thrust CLI wall time keeps offboard within 0.1 s of T_OFFBOARD_S (see `offboard_late_s`).
- Arm is sent within one ATTITUDE tick (10 ms) of T_ARM_S; blocking `cmd()` ack wait advances sim time slightly.
- pyulog availability inside the docker container (metrics_status will say).
- Disturbance onset / sag / trajectory t0 derive from sim.t at window start, so they shift consistently with the
  fixed times; not checked.
