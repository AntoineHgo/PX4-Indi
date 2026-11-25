# Key 2 (bench/g3_checks_key2.py), Q33 event-hover update (S230)

Written from EVENT_HOVER_SPEC.md, GATES.md (G3 list, "Owner amendment Q33") and the S226 KEY2_README only. Key 1 files
(g3_checks.py, test_g3_q33_key1.py, test_g3_checks_s226.py, KEY1_README.md) were NOT opened or grepped. g3_run.py / scenarios.py were
NOT read (the spec was sufficient). Not committed. Thresholds unchanged.

## Changes (g3_checks_key2.py, minimal)
- `windows_from_run`: with `g3_timeline` in run.json: main window = [`main_start_us`, `main_end_us`] (item 4), step starts
  (item-2 skip points) = t0 if `fault_on` or `wind_on`, plus `gust_us` if `wind_on`; item-5 events `ev5` = fault t0 (if `fault_on`)
  and gust (if `wind_on`); `event_win` = [t0, `event_end_us`]. Mode from `main_segment` (traj = position; stick = run.json stick.mode).
  An `event` segment without `g3_timeline` -> `ValueError` (the run is refused, not scored). Runs with neither keep the old
  behaviour (anchor = main start, one step start, one item-5 event).
  Hold and items 3/6 windows still come from the `hold` event (unchanged).
- Item 2: `psd_windows` unchanged; it just receives two skip points (t0, gust). Rule `ta <= point < ta + 4` as before.
- Item 4: `tracking()` unchanged; its window is now the timeline main segment only.
- Item 5 (`recovery`): events from `ev5`; wind ramp start and telemetry loss/frozen are not gated (tel stays reported-only, now anchored
  at event t0 + drawn offset). Position mode: error = 3-D distance truth vs the static hover setpoint (`hover_ref`: median of the
  finite `trajectory_setpoint` x, y, z samples inside the event hover) AND tilt vs `vehicle_attitude_setpoint` q_d (time-matched, as before);
  in band = both. Attitude mode: tilt vs q_d only. Rate mode: not applicable, pass. Rule unchanged: first in-band sample within <= 5 s of
  the event, no excursion beyond the limit for the following 5 s; gust and fault scored separately, all must pass.
- Module docstrings of the two functions updated. Break hook `KEY2_BREAK` untouched (the new rules were break-checked by patching, below).

## Tests
`indi_flight/bench/tests/test_g3_q33_key2.py`: 8 tests (synthetic, known answers; reuses `build`, `box`, `rates` from the S226 test file):
timeline windows (step points, events per fault/wind on-off, mode); missing timeline = error and pre-Q33 run unchanged; item 2 gust skip
(8 skipped windows = 4 per skip point, control without the gust point is flagged, no wind = no gust skip); item 4 window (offsets in event hover and
hold ignored; 0.564 m RMS in the main segment fails; n/a in stick); item 5 position (both events, each failing alone, 3 s return, 6 s too slow, re-excursion);
static hover reference (setpoint blip / moving setpoint after the hover ignored; setpoint 1 m off never in band); position tilt term, attitude mode
(tilt term, no position term); rate n/a, wind ramp and no-fault gust-time not events.

    cd indi_flight/bench/tests && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/g3venv/bin/python -m pytest -q *key2*.py -p no:cacheprovider
    -> 54 passed (8 new + 46 existing key2 tests; the existing 46 pass unchanged), 6.4 s
    g3_checks_key2.py --self-test -> no FAIL lines

## Break-checks (code patched, new file run, code restored byte-identical to the working version, cmp checked)
| patch | failing new tests |
|---|---|
| A gust not a skip point | windows_from_timeline, item2_gust_skip_window |
| B item-4 window starts at event t0 | windows_from_timeline, item4_window_is_main_segment_only |
| C gust not an item-5 event | windows_from_timeline, item5_position_both_events_position_term, item5_position_tilt_term_and_attitude_mode, item5_rate_mode_not_applicable_and_ramp_not_scored |
| D wind ramp start (t0) scored when wind on | windows_from_timeline, item5_rate_mode_not_applicable_and_ramp_not_scored |
| E position term ignored | item5_position_both_events_position_term, item5_position_reference_is_hover_setpoint_not_commanded_path |
| F tilt term ignored (position mode) | item5_position_tilt_term_and_attitude_mode |
| G reference = commanded path at same time (old) | item5_position_reference_is_hover_setpoint_not_commanded_path (after adding the setpoint-blip case; the first version of that test did not bite) |
| H missing timeline not an error | event_segment_without_timeline_is_error_old_runs_unchanged |
| I rate mode scored | item5_rate_mode_not_applicable_and_ramp_not_scored |
| J attitude mode gets a position term | item5_position_tilt_term_and_attitude_mode |

Patch script was /tmp/brk.py (not kept in the repo).

## Interpretations / ambiguity (flag for comparison with key 1)
1. Static hover reference = median of the finite logged setpoints over [t0, event end]. The spec says the setpoint is constant in the event
   hover, so any reading gives the same on real data; it only matters for a blip, which I treated as noise.
2. q_d tilt term stays time-matched (last q_d sample at or before each time), in both position and attitude mode: q_d is the controller output, "level
   with zero sticks" is only the stabilized case; spec says "tilt between truth attitude and q_d".
3. Return rule: pass = t_in - event <= 5 s and no excursion in (t_in, t_in + 5 s], t_in = first in-band sample (as S226). If the vehicle never leaves the band,
   t_in = 0 and only 0..5 s is checked for excursion. The alternative "stay in band from event + 5 to event + 10 s" differs for a late excursion.
   The spec sentence "back within <= 5 s of the event, then no excursion for the following 5 s" was read as "following the return".
4. Wind-only runs: t0 is an item-2 skip point (spec: "t0 when fault_on or wind_on") but not an item-5 event.
5. Fault-only runs: no gust, so no gust skip point and no gust event. Neither on: no events, item 5 applicable and passes trivially.
6. Item 4 window = timeline main segment; the `traj` event's own dur_s is not used for Q33 runs. Hold (items 3, 6) still read from the `hold` event
   rather than `hold_start_us/hold_end_us` (spec says they are the same values; not cross-checked).
7. Time base: `*_us * 1e-6` compared directly to truth timestamps (as `events[].t_us` always was), no ulog start_timestamp subtraction.
8. Fail closed: flight ending before event + 10 s, or fewer than 50 % valid reference samples, fails the event (as S226).

## Unverified
- No real Q33 run exists: `load_run` on a real run.json with `g3_timeline` is untested (synthetic dicts only, field names from the spec).
  `analyse()` is tested on synthetic arrays; `vehicle_attitude_setpoint`/`trajectory_setpoint` presence during the event hover is assumed.
- Whether the draw's tel offsets still apply to t0 (spec says anchored at t0) is only used for reported-only events.
