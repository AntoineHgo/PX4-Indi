# KEY1_README (S230): event hover (Q33) in the G3 scenarios and key 1 items 2, 4, 5
Spec for the blind key-2 author: `EVENT_HOVER_SPEC.md` (this directory). Dry-run output: `dry_run_timeline.txt`. No flights, no docker, not committed.

## What changed
- `bench/scenarios.py`: `g3_lemniscate` / `g3_stick_zsine` segments are now settle (3 s), `event` (23 s), main (`traj` / `stick`), hold (35 s).
  New constants `G3_GUST_OFFSET_S` (= WIND_RAMP_T + WIND_HOLD1_T = 12), `G3_GUST_END_S` (13), `G3_EVENT_QUIET_S` (10), `G3_EVENT_HOVER_S` (23, derived
  from `disturbance.py` constants, imported as `_dist`), `G3_EVENT_SEGMENT`. G5 scenarios (`o1_lemniscate`, `stick_zsine_o6`) untouched.
- `bench/g3_run.py`: `ANCHOR_SEGMENT` (G3 scenarios: `event`; legacy stand-ins: the main segment as before) replaces the main segment as the
  anchor of the motor-fault steps, the wind profile (`dist_segment`) and the timed telemetry loss / frozen windows (`build_run`, variable
  `anchor_seg`). New pure functions `timeline`, `plan_timeline` (planned times, scenario start = 0; returned by `build_run` as `timeline_plan`
  and therefore stored in `g3_draw.json`), `run_timeline` (actual times from run.json). `finalize` writes `run.json["g3_timeline"]`.
  Sag ramp: unchanged mechanism (ramp_s from the scenario start); its end is `g3_timeline.sag_ramp_end_us`. `run_scenario.py` NOT edited
  (segment handling is generic: pos_sp hover in trajectory mode / neutral sticks in stick mode; the sched rows hold the setpoint outside `traj`).
- `bench/g3_checks.py` (key 1): `windows_from_run_json` reads `g3_timeline` (new keys `item5_events`, `timeline`; `step_starts` = t0 when fault or wind,
  plus the gust time when wind; `track` = [main_start, main_end]; raises ValueError for an `event` segment without `g3_timeline`; runs without both keep the S225
  reading). `evaluate`: item 5 gets `att_sp` only in attitude mode and `sp_xyz` only in position mode (already so), and is "not applicable" in rate mode;
  `main` passes `item5_events`. Docstrings of the module and of `item5_recovery` updated. Thresholds untouched.
- Tests: new `bench/tests/test_g3_q33_key1.py` (10 tests); `test_g3_run.py` (MAIN_SEGMENT -> ANCHOR_SEGMENT, segment list with `event`, timed-event and sag bounds
  now against the event hover); `test_g3_checks_s226.py::test_item5_recovery` (the 6 deg tilt case now runs in attitude mode; added: position mode ignores tilt).

## Test results (/tmp/g3venv, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 because a system pytest plugin, xonsh, breaks collection)
- 124 passed: test_g3_q33_key1 (10), test_g3_checks_s226 (10), test_g3_align_s227 (3), test_g3_run (19), test_g3_sample (18), test_scenario_overrides (6),
  test_run_scenario_hooks (10), test_g3_harness_abort (3), test_g3_excursion_s186, test_g3_checks_key2_s226, test_g3_checks_key2_q14_q15, test_g3_excursion_key2,
  test_metrics, test_stick_profile (key 2 tests were run, not read). `python3 test_g3_checks.py` (script self-test of key 1): `selftest PASS`.
- Not passing / not run: `test_g3_refly_s212.py::test_chain_halt_on_fail_and_samples_pin` (needs the SITL binary and the flight-chain lock, runs g3_chain.sh;
  FileNotFoundError here, 12 other tests of the file pass; its leftover `results/g3_selftest_smoke_s212_*` dirs were deleted). Not tested on the unmodified
  tree, so "pre-existing" is likely but unproven. The whole-directory pytest collection also fails on script-style test files (sys.exit at import): files run by name.

## Break-checks (rule broken in the real source, named test must fail, source restored and verified byte-identical)
| break | test that failed |
|---|---|
| B1 gust dropped from the item 5 events | test_windows_from_timeline_known_answers, test_item5_position_events_are_fault_start_and_gust, test_item5_attitude_mode_reference_is_qd_and_not_position |
| B2 gust dropped from the item-2 skip points | test_windows_from_timeline_known_answers, test_item2_sine_straddling_gust_is_not_flagged |
| B3 item 4 window starts at t0 (includes the event hover) | test_windows_from_timeline_known_answers, test_item4_window_is_the_main_segment_only |
| B4 (superseded S230, see "Mode/reference reading") | test_item5_position_mode_scores_position_and_tilt |
| B5 attitude mode also scores position | test_item5_attitude_mode_reference_is_qd_and_not_position |
| B6 rate mode scored by item 5 | test_item5_rate_mode_not_applicable |
| B7 q_d replaced by a fixed level reference | test_item5_attitude_mode_reference_is_qd_and_not_position |
| B8 segment start times shifted in `plan_timeline` | test_event_hover_scenario_and_timeline |
| B9 `G3_EVENT_QUIET_S` 10 -> 5 (event hover not 23 s) | test_event_hover_scenario_and_timeline, test_run_timeline_from_run_json_and_finalize |
Each break-check ran the whole new test file; other tests stayed green except where listed. The existing item-2 skip break-check of S226 (G3_BREAK=skip) was not rerun.

## Dry run (no simulation)
`dry_run_timeline.txt`: `build_run` on seed-1 draws for both scenarios prints segments and `timeline_plan`: event hover 23.0 s, t0 3.0 s, gust 15.0 s,
event end = main start 26.0 s, main end 43.81 s (traj) / 44.0 s (stick), hold end 78.81 / 79.0 s. All 300 seed-1 draws merge and validate through
`scenario_overrides.merge` on the new scenarios (wind profile and timed telemetry windows fit, all anchored at `event`).

## Unverified / flagged
- Nothing was flown: the segment handling of `run_scenario.py` for an extra neutral segment (trajectory hold, neutral sticks, `--sched` rows, `--stick-pilot` neutral
  pilot in the 23 s `event` segment) is by reading only. The pilot behaviour in a long neutral segment (stabilized / acro) is the main thing to look at in the pre-test.
- `g3_timeline` is written post-flight from run.json by `g3_run.finalize` (the runner's own event times); a run killed before run.json is complete has none and is refused by key 1.
  Event times are segment starts of the flight (PX4 clock); `motor_fault.event_us` is a few ms after t0.
- Mode/reference reading: attitude reference = time-matched `vehicle_attitude_setpoint` q_d (level with zero sticks in stabilized), as the amendment says; a literal fixed
  level (zero tilt) reference would differ only if q_d is not level during the event hover. Orchestrator S230 correction: position mode KEEPS the 3 deg tilt
  term vs q_d (GATES 3 item 5 names both terms; Q33 changes the reference only). Code g3_checks.py item5 call passes att_sp in every
  non-rate mode; test renamed test_item5_position_mode_scores_position_and_tilt (break-check: re-excluding att_sp in position mode
  fails it); test_g3_checks_s226.py position-mode tilt case restored to the pre-Q33 assertion. 39 tests pass after the correction.
- Telemetry loss / frozen windows are anchored at t0 (start offsets 1-5 s, 1 s long, inside the event hover). The amendment does not name them; they stay ungated in item 5 and unskipped in item 2.
- `g3_sample.py` comments / unit strings still say "anchor = main-segment start" (descriptive text in the draw files; no behaviour). Not edited to keep draws byte-identical.
- `g3_score.sh` needs no change (it passes `--run-json`); other bench scripts that read `traj`/`stick` event windows of G3 runs (g3_item2_split.py, g3_box_margins.py etc.) were not reviewed.
- Existing pre-Q33 results rescored with this key keep the S225 reading (no `event` segment, no `g3_timeline`).
