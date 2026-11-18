# K110 fixes (S111) - G3 overrides must apply the drawn plant

Plan (items from scenario_overrides_key_s110.md): 1 M-1 air-relative wind drag; 2 M-2 eRPM loss start/duration;
3 M-3 motor_fault list; 4 m-2 single timing anchor; 5 three surviving mutations (tests + break-checks); 6 m-6 window validation.
Tests: `cd indi_flight/bench && python3 -m pytest -q tests/test_scenario_overrides.py tests/test_g3_run.py tests/test_g3_sample.py tests/test_disturbance_sizing.py`.
Decisions: gz body drag = none (only rotorDragCoefficient in the motor model, no LiftDrag/body drag in quad5in/x500 SDF),
so the injector adds the FULL air-relative drag c*(w-v)|w-v|. Anchor for all timed G3 events = start of the main segment (traj/stick).

## Status log (appended as work proceeds)

Test runner: pytest is not installed on the host; every test file runs as `python3 bench/tests/<file>.py` (each has a PASS/FAIL main).
All 20 files in bench/tests exit 0, 0 FAIL (test_g3_run 9 PASS, test_scenario_overrides 6, test_g3_sample 11, test_disturbance_k110 3 new,
test_disturbance_sizing OK). Summary line: "20 test files, 0 FAIL; py_compile OK for run_scenario/g3_run/disturbance/scenario_overrides/g3_sample".
Break-checks were done in a scratchpad copy (bench/ copied, line broken, test run, original restored); live files untouched by them.

## Item 1 M-1 air-relative drag - DONE in code, flight UNVERIFIED
- gz check: quad5in and x500 SDF have only per-rotor rotorDragCoefficient, no body/LiftDrag drag -> injector adds the FULL drag
  F = c_drag (w-v)|w-v| (3-D vector form, w = wind_speed * (cos dir, sin dir, 0)); docstring says so.
- disturbance.py gust_x(..., vel=None) (~l.125-146); vel=None keeps the legacy pure force (bit-identical, test_gust_defaults_bit_identical passes).
  PoseVelocity (finite difference of gz /world/<w>/pose/info stamps, sim time, min dt 4 ms) and the on_pose subscriber in main();
  on_clock passes pv.vel to gust_x at every clock tick (same rate as before). Count of ticks without velocity logged at exit.
- CHANGE OF BEHAVIOUR: every gust_x flight (o3_lemniscate_gust, gust_x scenarios, G3 wind) now has air-relative drag, with a moving vehicle
  the force is lower than before; and the drag has no wind-off damping (gz has no body drag). Old gust_x results are not comparable.
- Tests: test_air_relative_drag, test_pose_velocity (test_disturbance_k110.py). Break-check: sign of vel[0] flipped ->
  `FAIL test_air_relative_drag AssertionError()`.
- UNVERIFIED: that the gz Pose_V topic /world/default/pose/info carries the model under name == a.model (e.g. quad5in_0) with a header
  stamp, in the world frame; the 4 ms difference noise; the injector start-up (first ticks use legacy force until 2 samples). Needs a sim check.

## Item 2 M-2 eRPM loss window - DONE in code, flight UNVERIFIED
- scenario_overrides.py: erpm_loss accepts {motor, start, start_offset_s, duration_s} (the old {motor,start,end} form still valid).
- run_scenario.py (segment loop, "timed eRPM loss" block): the start segment's sim.run is split into pre / loss / post sub-runs,
  SIM_GZ_ERPM_LOSS set at +offset and cleared after duration (sim time). meta erpm_loss gets on_us/off_us.
- g3_run.py: override carries the drawn motor, start_offset_s, duration_s with start = main segment.
- Tests: test_erpm_loss_drawn_motor_and_window. Break-check (motor index (m+1)%4): FAIL test_erpm_loss_drawn_motor_and_window AssertionError();
  offset forced to 0.0: same test FAILS.
- UNVERIFIED: that the split runs keep the player/--sched timeline (with --sched sp=None, sub-runs only advance sim time), and
  the actual off/on_us timing in a flight.

## Item 3 M-3 motor_fault list - DONE in code, flight UNVERIFIED
- scenario_overrides.py: motor_fault is a dict or a list of dicts (validated per entry, empty list rejected), helper fault_entries().
- run_scenario.py: per-motor cumulative scale = product of thrust_scale of all entries applied so far; EC MIN/MAX = nominal*sqrt(scale)
  (single entry gives the same ints as before). meta motor_fault keeps its old keys, plus "entries" for several.
- g3_run.py: weak motor and saturation both go in the list; the drop and not_applied["weak_motor"] are removed.
- Tests: test_overrides_applied_and_valid (updated), test_weak_motor_segment_and_motor (builds a both-on draw by hand if the sampler
  never drew one), test_window_validation_and_fault_list. Break-check (only last fault kept): FAIL test_overrides_applied_and_valid.
- UNVERIFIED: the real EC_MIN/MAX result for a weak motor under saturation (0.8 * 0.9 combined = sqrt(0.72)) in a flight.

## Item 4 m-2 anchor - DONE (doc + g3_run), the timing itself UNVERIFIED
- Recorded: the single anchor of all timed G3 events (tel_loss, weak motor, saturation, wind onset) is the START OF THE MAIN SEGMENT
  (traj / stick). g3_sample.py comments, units strings ("s after anchor (main-segment start)"), hooks "t0", wind "start" and the key
  t_after_hold_start_s -> t_after_anchor_s now say so. The drawn field names/values/ranges are unchanged.
- Not changed (declared): thrust_sag still ramps over the whole window from sim.t at the start (m-1); gust_offset_s is still unused (m-3);
  --sched-anchor (m-5): hooks and disturbance onset use sim.t while the player starts at sched_t0: UNVERIFIED, needs a sim check.

## Item 5 surviving mutations - DONE
- (a) disturbance.wind_profile_args() (pure; main() uses it). Test test_wind_profile_args. Break (`return st, pk,`):
  `FAIL test_wind_profile_args AssertionError()`.
- (b) test_erpm_loss_drawn_motor_and_window: FAILS with the shifted index (see item 2).
- (c) test_weak_motor_segment_and_motor. Break (segment "hold"): `FAIL test_weak_motor_segment_and_motor AssertionError()`.

## Item 6 m-6 window validation - DONE
- scenario_overrides.validate: timed erpm_loss must end inside the scenario; offset >= 0, duration > 0; wind needs the first 13 s
  (ramp+hold+gust) of the gust_x profile to fit from dist_segment (the 15 s steady tail may run past the window, as before: a full 28 s
  check would reject every G3 wind run on o1, window 20.8 s from traj). Test test_window_validation_and_fault_list.
  Break (window check disabled): FAIL ... AssertionError("accepted {'start_offset_s': 20.0}").
- Not checked: that `end` differs from the last segment (old-form only).
