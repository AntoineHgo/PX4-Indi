# EVENT_HOVER_SPEC (S230): interface of the G3 event-hover scenario for the key-2 author

Source of the rules: GATES.md "Owner amendment Q33" (line ~871) and DECISIONS.md D-OWNER-Q33. This file gives only the
interface (run metadata) and the definition of each window and reference; no key-1 code. Thresholds are the GATES ones, unchanged.

## 1. Scenario (what the runs now fly)
Segments, in order: `settle` (3 s) -> `event` (event hover, 23 s) -> main segment -> `hold` (35 s).
- Main segment: `traj` (lemniscate, position mode scenario `g3_lemniscate`) or `stick` (vertical sine, stick-mode scenario
  `g3_stick_zsine`, flight modes stabilized / acro). The `event` segment is a hover at the settle position (position mode:
  hover setpoint; stick modes: neutral sticks).
- Event hover length = gust end + 10 s, derived in `scenarios.py` from the `disturbance.py` gust_x profile constants
  (ramp 2 s + hold 10 s -> gust starts 12 s after the profile start, gust lasts 1 s, + 10 s = 23 s). Do not hard-code 23 or 12:
  read the metadata below.
- At t0 (start of the `event` segment): the drawn motor fault step(s) (weak motor and/or saturation) and the wind profile start
  (wind ramp 0 -> steady over 2 s, steady wind). At t0 + 12 s: the gust (1-cosine, 1 s). Steady wind and the motor faults stay on to
  the end of the run. Telemetry loss / frozen windows (drawn start offset 1-5 s after t0, 1 s long) are also anchored at t0 now.
- Battery sag is NOT an event: a linear ramp from the scenario start (the start of `settle`) to `sag_ramp_end_us`, constant after.
- Not every run has every event: `fault_on` false = no motor fault step, `wind_on` false = no wind profile (no gust).

## 2. Metadata: run.json top-level object `g3_timeline` (written by g3_run.finalize after the flight)
| field | type | meaning |
|---|---|---|
| `version` | int | 1 |
| `time_base` | str | text description of the time base (below) |
| `scenario` | str | `g3_lemniscate` or `g3_stick_zsine` |
| `main_segment` | str | `traj` or `stick` |
| `fault_on` | bool | a drawn motor fault step (weak motor / saturation) is applied at t0 |
| `wind_on` | bool | the wind profile (steady wind + gust) is on |
| `event_t0_us` | int | t0 = start of the event hover = fault step start = wind ramp start |
| `gust_us` | int or null | gust start = t0 + 12 s; null when `wind_on` is false |
| `event_end_us` | int | end of the event hover = t0 + 23 s (= `main_start_us`) |
| `main_start_us`, `main_end_us` | int | main segment start and end (end = start + segment length) |
| `hold_start_us`, `hold_end_us` | int | hold segment start and end (35 s) |
| `sag_ramp_start_us`, `sag_ramp_end_us` | int or null | sag ramp start (scenario start) and end; null when no sag |

Time base and units: every `*_us` is an integer in microseconds on the PX4 clock = the simulation time base of
`run.json["events"][].t_us` (not wall time). Ulog time in seconds is `us * 1e-6 - ulog start_timestamp * 1e-6` (the ulog
`start_timestamp` of the flight log), the same conversion as for `events[].t_us`. Values are the ACTUAL segment start times of the
flight (taken from `events[]`), plus the fixed offsets (12 s, segment lengths) from the scenario.
Other run.json blocks that already exist and are unchanged: `events[]` (name, t_us, dur_s; names `settle`, `event`, `traj` or `stick`,
`hold`), `motor_fault` (event_us = fault application time on the same clock, a few ms after t0), `disturbance` (onset_us), `thrust_sag` (t0_us,
dur_s). A run without `g3_timeline` and without an `event` segment is a pre-Q33 run (anchor = main-segment start): not covered here.
A Q33 run (has an `event` segment) without `g3_timeline` must be refused, not scored.

## 3. Definitions per item (changes only; everything else as in GATES and as before)
Item 5 (recovery after each injected event)
- Events = {t0 if `fault_on`} + {`gust_us` if `wind_on`}. The wind ramp start is not an event. Telemetry loss/frozen are not events.
- Reference (static, set by the event hover; both events are inside it):
  - position mode (scenario `g3_lemniscate`): the hover setpoint = `trajectory_setpoint` position (x, y, z), which is constant during the
    event hover. Error = 3-D distance, truth vs setpoint, same height convention as the other position items. Plus the GATES 3 item 5
    tilt term: tilt angle between truth attitude and `vehicle_attitude_setpoint` q_d (yaw excluded) <= 3 deg; in band = both
    terms in band (orchestrator S230: Q33 changes the reference, not the criterion).
  - attitude / stabilized mode (stick scenario, flight mode stabilized): `vehicle_attitude_setpoint` q_d, which is level with zero sticks.
    Error = tilt angle between the truth attitude and q_d (yaw excluded). No position term.
  - rate mode (acro): item 5 not applicable (reported as such, counts as pass).
- Rule per event (GATES, thresholds unchanged): back within 0.3 m and 3 deg (position mode) / 3 deg (attitude mode) of the reference within <= 5 s of
  the event, then no excursion of the position error (attitude mode: tilt error) beyond its limit for the following 5 s. The event hover is long enough for both windows of the gust
  (the gust event needs gust + 5 s + 5 s = gust + 10 s <= `event_end_us`). Both events are
  scored separately and both must pass.
- Replaces the S227 reading (commanded path at the same time as position reference).
Item 2 (sustained oscillation), skip windows
- The existing S225 rule (a 4 s rate window that contains a fault or gust step start is skipped, counts as unflagged, no line chains across
  it) now has two skip points: t0 (when `fault_on` or `wind_on`, as before for the main-segment start) and `gust_us` (when `wind_on`). A window
  [w0, w0 + 4) is skipped if w0 <= point < w0 + 4. Telemetry loss / frozen starts are not skip points. The table of skipped windows is
  reported for both stacks as before. Everything else in item 2 is unchanged.
Item 4 (position tracking, position scenario only)
- Window = the main segment only: [`main_start_us`, `main_end_us`] converted to ulog time. The event hover and the hold are not in it. Limits
  unchanged (horizontal RMS 0.5 m, vertical RMS 0.3 m). Not applicable in the stick scenario.
Unchanged: item 1, item 3 (last 10 s of the `hold` event), item 6 (last 20 s of `hold`, acro), item 2 position limit cycle (3 x 10 s from the hold start).
