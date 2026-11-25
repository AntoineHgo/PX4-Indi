# Key 2 (bench/g3_checks_key2.py), S226 tooling for Q30 / Q32

Independent second key. Written from GATES.md (G3 items 1-6, S214, S225) only; key 1 (`g3_checks.py`, `g3_score.sh`) and
`scenarios.py` were not read. Not committed.

## What changed
- `windows_from_run(run.json)`: every window comes from `run.json['events']`. Main segment = first event named `traj`
  (position) or `stick` (stick scenarios); step start = its `t_us`. Hold = event `hold` (`t_us`, `dur_s`). Item 3 = last 10 s of
  the hold, item 6 = last 20 s. Time base: `t_us` is the runner's `sim.t`, the same clock as the ulog / `sim_ground_truth`
  timestamps (the old key 2 already compared `hold.t_us` straight to the truth `timestamp`); no offset. Only the old
  `--t0/--t1` are seconds since `ulog.start_timestamp`.
- Item 3 default window = run.json window. Old CLI kept: `--t0 --t1 --mode --wind --sag --out --self-test --break`.
  With `--t0/--t1` the run is "legacy": item-3 window as given, item-3 mode = the hold event's own `mode` field (old
  behaviour), `pass` = items 1-3 as before, items 4-6 still computed and reported.
- Item 4 `tracking()`, item 5 `recovery()`, item 6 `rate_hold()`; new keys in the JSON: `windows`, `item4_tracking`,
  `item5_recovery`, `item6_rate_hold`, `pass_items_1_3` (S225 pass line), `pass` (items 1-6, campaign definition).
- S225 item 2: `psd_windows(step_pts=...)` skips every 4 s window with `ta <= step_start < ta + 4`; a skipped window is emitted as
  ratio 0, so `sustained()` restarts: no line chains across it. Telemetry loss / frozen are never in `step_t`. The skipped
  windows are in `item2_oscillation.skipped_windows` (start, end, reason, axes, `flagged_if_unskipped`) and printed on the CLI
  (`item2 skipped window start .. end .. reason ..`). The Q15 A nav_state skips use the same table (reason differs).
- Extras: wind / sag flags are read from `g3_draw.json` in the run dir (wind = steady or gust drawn; sag = thrust sag or weak
  motor on; CLI flags are OR-ed) except in legacy mode. `vehicle_attitude_setpoint` is loaded for item 5.
  `position_mode` (item-1 excursion) is now also true when the run has a `traj` event (new G3 scenario names differ from
  `o1_lemniscate`).
- Break-check hook: env `KEY2_BREAK=skip|chain|item3|item4|item5|item6`.

## Tests
`indi_flight/bench/tests/test_g3_checks_key2_s226.py`, 15 tests, synthetic with known answers: windows (position, stick
acro/stabilized, tel event not a step start, legacy override, missing hold); item 2 straddling sine not flagged (control: flagged
without the rule), sine persisting after the fault flagged, no chaining across a skipped window (2 + skip + 2), skipped table
contents and window boundary, nav skip still works; item 3 window (0.5 m offset in the last 10 s fails, same offset 10-20 s
before the end passes); item 4 (0.56 / 0.48 m, 0.36 / 0.28 m known RMS); item 5 (return in 3 s pass, 6 s fail, re-excursion
fail, tilt part, attitude mode, rate N/A, reported-only event does not gate); item 6 (6.0 / 4.0 dps known RMS, burst outside
the 20 s window ignored, drift fails, short hold fails closed); overall pass vs legacy.

Environment: the host `python3` has no pytest, and `/usr/bin/python3 -m pytest` fails. Used
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/g3venv/bin/python -m pytest ...` (the venv has pytest 9.2 / numpy / pyulog; the broken
xonsh pytest plugin is disabled by the variable). `pytest indi_flight/bench/tests -k key2` on the whole directory aborts in
collection (INTERNALERROR SystemExit) because `test_hole_report.py` and `test_item2_split.py` call `sys.exit` at import
(pre-existing, not touched). Used the file glob instead:

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/g3venv/bin/python -m pytest indi_flight/bench/tests/*key2*.py -q -p no:cacheprovider
    -> 46 passed (15 new + 31 existing key2 tests), 6.5 s
    ... test_g3_checks_key2_s226.py -> 15 passed

## Break-checks (each rule disabled in turn via KEY2_BREAK, then restored; new file only)
Command: `KEY2_BREAK=<x> PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/g3venv/bin/python -m pytest indi_flight/bench/tests/test_g3_checks_key2_s226.py -q -p no:cacheprovider`

| KEY2_BREAK | effect | result | failing tests |
|---|---|---|---|
| (none) | | 15 passed | |
| skip | S225 step skip off | 4 failed, 11 passed | item2_sine_only_straddling_fault_not_flagged, sine_persisting_after_fault_flagged (flagged earlier than the skipped block), no_line_chains_across_skipped_window, window_boundary_and_other_starts_not_skipped |
| chain | skipped windows dropped instead of emitted as ratio 0 | 1 failed, 14 passed | item2_no_line_chains_across_skipped_window |
| item3 | item-3 window = first 10 s of the hold | 3 failed, 12 passed | windows_from_run_position, windows_from_run_stick_modes_and_extras, item3_window_is_last_10s_of_hold |
| item4 | item-4 limits x1e9 | 2 failed, 13 passed | item4_tracking_rms_limits, overall_pass_and_legacy |
| item5 | every item-5 event passes | 2 failed, 13 passed | item5_recovery_position_mode, item5_attitude_part_and_modes |
| item6 | item-6 limit x1e9 | 1 failed, 14 passed | item6_rate_rms_last_20s_of_hold |

After the loop the unset run is 15 passed again. Existing `--self-test` (no FAIL lines) unchanged.

Real-run smoke (no new-scenario run exists yet): `g3_checks_key2.py --out DIR results/g3_campaign_f10/run_000 run_228` runs end
to end on the new path (old runs have a 3 s hold, so items 3 and 6 fail closed there by design: re-score old runs with
`--t0/--t1`; the legacy path was run on run_000 and gives the old items 1-3 result).

## Interpretations (flagged: please compare with key 1)
1. **Skip containment.** "Window contains a step start" = `ta <= t_step < ta + 4 s` (half-open, sample-exact). A window ending
   exactly at the step is not skipped, a window starting exactly at it is. For a step on a whole second this skips 4 windows
   (1 s step). The skip applies to the 4 s rate-line windows (p, q, r) only; the 10 s position limit-cycle windows (hold only)
   and the G4 command-chatter windows are not skipped.
2. **Step starts** = the main-segment start only (S214 correction: gust and faults start there). Telemetry loss / frozen are
   not step starts. If a scenario ever injects a second step later, key 2 would not skip it (it reads only the main event).
3. **Item 5 events.** Gated events = the main-segment start. Telemetry loss/frozen (from `g3_draw.json` start offset + main
   start) are listed as reported-only (`gated: false`); GATES says "gust, fault start", S225 treats telemetry separately.
   If key 1 gates them, the two keys will differ.
4. **Item 5 reference.** "Pre-event reference" is a moving target in position scenarios (lemniscate tilt reaches 30+ deg), so:
   position mode = error to the commanded reference (`trajectory_setpoint` 3-D position, `vehicle_attitude_setpoint` q_d tilt);
   attitude mode = tilt vs the pre-event body-z (median of the 2 s before the event); rate mode = not applicable (item 6 covers
   it). Truth quaternion and q_d are in the same frame (checked on run_000). Position error is 3-D (x, y, altitude). The 3 deg
   is the tilt (roll/pitch) error, yaw excluded as in item 3. Missing reference = fail closed.
5. **Item 5 timing.** t_in = first sample within 0.3 m and 3 deg; pass = t_in - t_event <= 5 s and no excursion beyond the
   controlled limit in (t_in, t_in + 5 s] (position mode: > 0.3 m only, attitude mode: > 3 deg). So the scope is 10 s from
   the event at most. If the vehicle never leaves the box t_in = 0 and only the first 5 s are checked for re-excursion; a
   later excursion is not item 5. The alternative reading (stay inside from event + 5 s to event + 10 s) differs.
6. **Item 4** = RMS over the `traj` event span (start .. start + dur_s, includes the fault/gust response) of truth minus the logged
   `trajectory_setpoint`, horizontal = norm of (x, y), vertical = z (same sign convention as item 3). Position scenario only.
7. **Item 6** = sqrt(mean(p^2 + q^2 + r^2)), 3-axis vector, not detrended (drift counts), <= 5 deg/s. A per-axis reading is
   looser (per-axis values are in the JSON). Rate (acro) mode only. Hold < 20 s fails closed.
8. **Mode** (item 3/5/6) = position if a `traj` event exists, else `run.json['stick']['mode']`: stabilized -> attitude, acro ->
   rate; `--mode` overrides.
9. **Hold** = the last `hold` event if several exist (old key 2 took the first).
10. **Sag flag** for item 3 altitude 0.20: thrust sag or weak motor on; the saturation corner is not counted (GATES text says
    sag or weak motor).
11. **Position limit cycle** (item 2, unchanged): 10 s windows and 3 consecutive needed; a 20 s hold gives only 2 windows, so it can
    never flag (needs a hold >= 30 s). Not changed (thresholds fixed) but worth knowing.
12. **Item 1** `loc()` still uses the hold as its segment start (drop vs height at hold start); unchanged, not in scope.
13. `pass` now includes items 4-6 (campaign pass); `pass_items_1_3` is the S225 pass line (items 4-5 reported).

## Unverified
- No run of the new G3 scenarios exists, so `load_run` on a real new-format run (hold >= 20 s, `traj`/`stick` events,
  `g3_draw.json` flags, tel events) is only checked on old runs and the synthetic tests; `analyse()` is tested on synthetic arrays.
- Time-base alignment was checked by reading the runner (`run_scenario.py`: `t_us = sim.t`) and an old run (`hold.t_us` lies in the
  truth time range); no new-scenario run.
