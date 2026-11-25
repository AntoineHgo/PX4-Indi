# Key 1 G3 tooling for Q30 (S214) and Q32 (S225), S226

Scope: bench code only (no firmware, no flights, no docker). Python used: a throwaway venv `/tmp/g3venv` (system site packages
plus pytest, scipy, pyulog; the host has no pytest or scipy). Pytest needs `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` here (a broken
`xonsh` pytest plugin on the host).

## Files changed
- `bench/scenarios.py`: `G3_HOLD_S = 25.0`; new `g3_lemniscate` (main segment of `o1_lemniscate`, then a 25 s hold) and `g3_stick_zsine`
  (main segment of `stick_zsine_o6`, then a 25 s hold). `o1_lemniscate` and `stick_zsine_o6` untouched (G5).
- `bench/scenario_overrides.py`, `bench/run_scenario.py`, `bench/disturbance.py`: two opt-in hooks, old behaviour unchanged without them.
  `thrust_sag.ramp_s` (ramp over the drawn length from the scenario start, then constant; before: ramp over the whole window) and
  `wind.hold_to_end` (disturbance.py `--duration` = dist segment start to scenario end + 2 s; before: wrench cleared at 28 s,
  which would have fallen inside the 25 s hold).
- `bench/g3_run.py`: default scenarios are now the two G3 ones; `--legacy-scenarios` restores the old stand-ins (pre-S214 behaviour).
  With the G3 scenarios the draw's wind gets `hold_to_end` and the sag its drawn `ramp_s`. `MAIN_SEGMENT` carries all four names;
  `POSITION_SCENARIOS` lists the names for which position-mode gates apply.
- `bench/g3_checks.py` (key 1): `--run-json` (windows from run.json, see below); `--rate-mode`; `--t0/--t1` kept (old runs, no new items);
  items 4, 5, 6; item-2 step-start skip with the skipped-window table.
- `bench/g3_score.sh` (key 1 driver): runs with a `hold` event >= 20 s are scored with `--run-json` (+ `--rate-mode` for acro draws);
  older runs keep the 3 s stand-in window.
- Tests: `bench/tests/test_g3_checks_s226.py` (new, 10 tests), `bench/tests/test_g3_run.py` (two assertions updated to the S214 override
  content, one test added: `test_s214_scenarios_and_legacy_switch`).

## run.json interface used (unchanged runner output)
`events[]` entries `traj` (position) or `stick` (stick) = main segment, and `hold` with `t_us`, `dur_s`. `t_us` is the PX4 clock, the
same clock as the ulog timestamps (checked: a `SIM_GZ_EC_MAX*` change is logged 0.1 s after `motor_fault.event_us`), so
`t_ulog = t_us * 1e-6 - ulog.start_timestamp`. Main-segment start = fault / gust step start. Item 3 = last 10 s of `hold`, item 6 =
last 20 s, item 4 = `[traj start, traj start + dur_s]`.

## Interpretations (flagged)
1. Fault or gust step = a run.json `motor_fault` entry (weak motor or saturation) or `disturbance` (gust_x), at the main-segment start.
   Telemetry loss / frozen and the sag ramp are not step starts (S225 text). A run without a fault or gust has no skip.
2. Skip rule: a 4 s rate-line window `[w0, w0+4)` is skipped when `w0 <= t_step < w0+4` (four 1 s-step windows per step). The skipped window
   counts as unflagged, so no 3-window line chains across it. Position limit-cycle and the G4 chatter windows are not skipped.
   JSON: `item2_skipped_windows` = [{start_s, end_s, reason}] (step starts and the Q15 nav-change skips), `item2_step_starts`.
3. Item 4: horizontal and vertical RMS of truth against the time-matched `trajectory_setpoint` (linear interpolation), over the `traj`
   event; height error with the D-G3-ZREF re-zero as in item 3. Position scenario only (not applicable on stick runs).
4. Item 5 (the loosest reading in the spec): events = the fault / gust step start (= main-segment start, S214 correction); "pre-event
   reference" = the commanded reference at the same time (`trajectory_setpoint` position, `vehicle_attitude_setpoint` q_d, tilt error
   with yaw excluded). In band = 3-D position error <= 0.3 m and tilt error <= 3 deg. t_rec = first in-band time after the event; pass =
   t_rec - event <= 5 s and position error <= 0.3 m for the 5 s after t_rec (tilt error when there is no position reference, stick runs).
   WARNING for the owner: the main segment is a moving trajectory and item 4 allows 0.5 m horizontal RMS, so a 0.3 m band against the
   commanded path can be exceeded by ordinary tracking error. On the old freeze-10 run_001 (3 s hold, hold edited to 20 s only for a CLI smoke
   test) item 4 is 0.494 m (pass) and item 5 fails with a quiet-window maximum of 0.67 m. Expect item 5 to bind on tracking, not on the
   event. Thresholds not changed.
5. Item 6: per-axis (p, q, r) truth body-rate RMS <= 5 deg/s over the last 20 s of the hold, no mean removal; vector RMS reported, not gated.
   Applies when `g3_draw.json` mode is `acro` (g3_score.sh passes `--rate-mode`). Item 3 roll/pitch gate still applies to acro as before
   (stick runs are scored `--mode attitude`, unchanged).
6. res["pass"] now includes items 4-6 when run.json windows are given (not-applicable items pass); without `--run-json` it is items 1-3 as before.

## Integration notes for the orchestrator (not changed here)
- `bench/g3_chain.sh` line ~524 builds key 2's arguments with `grep -E "^$r --t0 "` on key 1's argument line. With S214 runs key 1 now prints
  `run_NNN --run-json <dir>/run.json --mode ...`, so that grep finds nothing and key 2 would be skipped ("no key-1 argument line"). Key 2 must
  take its own windows from run.json (S214); the chain needs to pass key 2 only `--mode/--wind/--sag/--rate-mode` and `--run-json`.
- `bench/g3_checks_key2.py:225` tests `rj.get("scenario") == "o1_lemniscate"` for position mode: S214 runs have scenario `g3_lemniscate`
  (`g3_run.POSITION_SCENARIOS` lists both).
- Runner behaviour with the 45.8 s scenario (watchdogs, wall timeout in g3_chain.sh, speed-1 wall time) not exercised (no flights).

## Tests run (host, /tmp/g3venv)
See the end of this file for the final counts and the break-check log.

### Results (S226, host python 3.12 in /tmp/g3venv)
Common prefix: `cd <repo root>; export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; /tmp/g3venv/bin/python -m pytest`
- `-k g3 -q` over the whole `indi_flight/bench/tests` directory cannot be collected on this tree, before or after this change:
  `test_hole_report.py`, `test_item2_split.py` and others call `sys.exit` at import (pytest INTERNALERROR). So the g3 files were passed by name:
  `pytest indi_flight/bench/tests/test_g3*.py indi_flight/bench/tests/test_scenario_overrides.py indi_flight/bench/tests/test_run_scenario_hooks.py -q`
  -> **105 passed** in 212 s (includes key 2's `test_g3_checks_key2_s226.py` as present on disk, and the new key 1 tests).
- Script-style self-test unchanged and green: `python indi_flight/bench/tests/test_g3_checks.py` -> PASS; `... --break-check` -> PASS.
- New key 1 tests alone: `pytest indi_flight/bench/tests/test_g3_checks_s226.py -q` -> 10 passed.
- CLI smoke on real data: `g3_checks.py results/g3_campaign_f10/run_001/flight.ulg --run-json <run.json with hold edited to 20 s> --mode position --wind
  --skip-nav-change` -> window [63.663, 73.663], step start 35.843 s, 4 step-skipped windows (start 32.2 .. 35.2 s) next to the nav-change skips,
  items 4 and 5 populated. Not a valid S214 run (no flight exists yet); it only proves the clock mapping and the JSON.

### Break-check log (module patched through G3_BREAK in the test file; matching test must fail, the others stay green)
| command prefix | blinded rule | result |
|---|---|---|
| `G3_BREAK=skip pytest ...test_g3_checks_s226.py -q` | item-2 step skip (`skip_points` ignored) | 3 failed: `test_item2_sine_straddling_fault_is_not_flagged`, `test_item2_skipped_window_table_and_no_chaining`, `test_gust_step_also_skips`; 7 passed (the post-fault and telemetry-loss tests rightly stay green) |
| `G3_BREAK=item3` | item 3 window = whole hold (`ITEM3_LAST_S` 25) | 2 failed: `test_windows_from_run_json_known_answers`, `test_item3_uses_last_10s_of_hold` |
| `G3_BREAK=item4` | tracking limits off | 1 failed: `test_item4_tracking` |
| `G3_BREAK=item5` | recovery check always passes | 1 failed: `test_item5_recovery` |
| `G3_BREAK=item6` | rate limit off | 1 failed: `test_item6_rate_hold_last_20s` |
Also a code-level break of the skip rule (edit `g3_checks.py`: the `for tp in skip_points if w0 <= tp < w1` filter replaced by `if False`, restored from a
backup copy afterwards): the same 3 tests failed, 7 passed; the file was restored (`grep -c "tp < w1" g3_checks.py` = 1).

### Unverified
- No S214 scenario was flown: the runner with the 45.8 s scenario, the injector `--duration`, the sag `ramp_s` hook and the gust ending before
  the hold are checked by unit tests (override merge and flags) and by reading `run_scenario.py` / `disturbance.py`, not in a simulation.
- Item 5 behaviour on real moving-trajectory data (see interpretation 4).
- The `g3_score.sh` change was syntax-checked (`bash -n`) and its embedded Python path was not run end to end (needs pyulog; it uses the same
  keys the script already read, plus `draw["mode"]` from `g3_draw.json`).
