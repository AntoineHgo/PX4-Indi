# S83 minors fix, bench loop-break injector (second_key.md items 3 and 4). Not committed.

## Changes
- IndiPosInjection.hpp (after `update`): new `void reset() { _started = false; }`.
- IndiPosInjection.cpp (`update`, `!armed` branch): now calls `reset()` (same behaviour, kept for direct callers).
- McIndiPosControl.cpp (Run(), inside `_vehicle_control_mode_sub.copy`): on the armed to disarmed edge
  (`previous.flag_armed && !flag_armed`) call `_injection.reset()`. Edge-driven, reached on every control-mode
  publication, independent of `can_run`. A re-arm in the same boot now starts a new window (new origin plus delay).
  AX = 0: `update` is still never called and `inject` stays an exact zero vector (reset only clears a flag).
- IndiPosInjectionTest.cpp: new test `RearmRestartsWindow` (window, end, reset, second window with delay at a new origin).
- mc_indi_pos_control_params.yaml: MC_INDI_PINJ_AX `long` is now one quoted single-line paragraph, plain words
  (no `u = c + d`, no `|-` wrapped block, option list not repeated); MC_INDI_PINJ_DLY `long` shortened to the facts
  (counted from first armed airborne cycle, only used when AX is not 0). Other PINJ params have only `short`, unchanged.
  Rules read: .github/instructions/parameters.instructions.md (applies to src/**); other matching file is the mc_*control
  one (not param related). YAML parses (`yaml.safe_load`).
- indi_flight/bench/tests/test_pinj_csv.py (new): estimate() of pinj_csv.py is already a pure function of the window
  array, no refactor needed. Known loop L = K e^{-s tau}/(s(s/P+1)), K 5, P 10 rad/s, 8 samples delay, 100 Hz, ZOH
  plant (tau_eff = 8.5 Ts), d = margins_est.multisine (Tp 10, 0.2 to 8 Hz, 3 periods, 0.05), u = c + d, c = -y,
  columns t,d,x=u,y=c. Truth PM 43.37 deg, wc 4.551 rad/s. Tolerance PM 2 deg, wc 3 percent. Numpy only (scipy is not
  installed on this host; the test needs no scipy).
- Item 4 (gap in the window while the stage pauses) is not changed in code: the clock still runs on `now` through
  pauses. Only the re-arm case is closed. Still to check in a log: gaps inside the window.

## Commands and results
- `python3 -I indi_flight/bench/tests/test_pinj_csv.py`: PASS x3 (clean: est PM 43.37, wc 4.551; noise 0.002: PM 43.43, wc 4.546).
- Break check, python: swapped x and y columns -> test_clean, test_noise and layout test FAIL (PM -43.4). Restored, passes.
- `indi_project/docker/run.sh -n s83ut -t 1500 -- bash -c 'cd build/px4_sitl_test && ninja unit-IndiPosInjection && ctest -R IndiPosInjection'`:
  6 tests pass.
- Break check, C++: `reset()` made a no-op -> `RearmRestartsWindow` FAILED (IndiPosInjectionTest.cpp:113), 5 others pass.
  Restored with the real body -> 6/6 pass.
- McIndiPosControl.cpp compiled in docker (build/px4_sitl_default, object target) OK. Not a full px4 link.
- `Tools/astyle/fix_code_style.sh` on the 4 C++ files in docker: Unchanged.

## Unverified
- The disarm edge relies on vehicle_control_mode being republished on disarm (it is, flag_armed is part of it); not
  exercised in SITL with two arms in one boot.
- yaml not run through the param metadata generator (only YAML parse).
