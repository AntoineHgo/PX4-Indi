# G3 key 1: horizontal excursion vs time-matched setpoint, run_validity aliases (S186)

## What changed
- `bench/run_validity.py`: new `controller_kind()`; `pid_*` (incl. `pid_default`) is checked as "pid", `indi_*` as "indi", exact `indi`/`pid` kept, anything else still void. `check_run` interface unchanged (g3_run.py calls it with CONTROLLER).
- `bench/g3_checks.py`: item-1 horizontal excursion = max over [airborne start, min(airborne end, land/RTL start)] of |truth xy - trajectory_setpoint xy|, setpoint linearly interpolated onto truth timestamps; truth samples outside first/last setpoint sample excluded; truth samples bracketed by a NaN-x/y setpoint sample excluded (no interpolation across NaN gaps); excluded fraction of the span -> `excursion_sp_nan_frac`; no usable sample -> None (skipped); 5.0 m threshold, position mode only. Frame: no alignment applied, truth (sim_ground_truth x,y NED) vs setpoint as logged, exactly as the existing check compares truth with the setpoint-derived reference (stated in code comment). `evaluate()` got a trailing optional `sp=(t, xy)` arg (sp=None -> excursion None); `load()` unchanged, new `load_setpoint_xy()`; docstring updated. Item 2/3 untouched.
- Time base: setpoint stamps `timestamp` minus ulog start_timestamp, same as the existing ref.

## Tests (scipy from earlier scratch pylib on PYTHONPATH; pytest not installed, tests called directly)
- `tests/test_run_validity.py` +3 cases: pid_default valid, pid_default with INDI samples invalid, unknown name void. Old code: pid_default tests FAIL ("unknown controller 'pid_default'"); new code: all PASS.
- `tests/test_g3_excursion_s186.py` (new): 20 m radius moving setpoint, truth 1 m offset -> 1.00 m, item 1 pass (old formula against fixed ref gives ~20 m, fail); 6 m departure for 1 s -> >6.5 m, item 1 FAIL; NaN setpoint gap -> still 1.00 m, nan_frac reported (0.05-0.2); no setpoint -> None. All PASS. The "old fails" for this file was reasoned (old formula measures radius), not run against old code (old evaluate has no `sp` arg).
- `tests/test_g3_checks.py` selftest: PASS. Not run: test_g3_checks_key2_q14_q15.py (needs pytest).

## 20 pre-test runs + PID run 17 (args as score.sh; outputs `key1/run_NNN.json`, args in `key1/args.txt`)
Old = existing g3_checks.json (fixed reference point). Last column = overall pass with the new code (items 2/3 unchanged).

| run | mode | old excursion (m) | new excursion (m) | sp_nan_frac | item-1 pass old / new | overall new |
|---|---|---|---|---|---|---|
| run_000 | position | 5.43 | 0.85 | 0.00 | FAIL / pass | FAIL |
| run_001 | position | 5.62 | 1.01 | 0.00 | FAIL / pass | FAIL |
| run_002 | position | 6.80 | 2.44 | 0.00 | FAIL / pass | FAIL |
| run_003 | position | 5.70 | 1.97 | 0.00 | FAIL / pass | FAIL |
| run_004 | attitude | - | - | - | pass / pass | pass |
| run_005 | position | 6.57 | 2.00 | 0.00 | FAIL / pass | FAIL |
| run_006 | position | 5.43 | 0.86 | 0.00 | FAIL / pass | FAIL |
| run_007 | position | 5.43 | 0.96 | 0.00 | FAIL / pass | FAIL |
| run_008 | position | 5.02 | 1.00 | 0.00 | FAIL / pass | FAIL |
| run_009 | position | 5.94 | 1.28 | 0.00 | FAIL / pass | FAIL |
| run_010 | attitude | - | - | - | pass / pass | FAIL |
| run_011 | position | 5.22 | 0.85 | 0.00 | FAIL / pass | pass |
| run_012 | position | 5.15 | 0.90 | 0.00 | FAIL / pass | pass |
| run_013 | position | 5.14 | 1.18 | 0.00 | FAIL / pass | FAIL |
| run_014 | position | 5.40 | 0.88 | 0.00 | FAIL / pass | FAIL |
| run_015 | position | 5.48 | 0.89 | 0.00 | FAIL / pass | FAIL |
| run_016 | attitude | - | - | - | pass / pass | pass |
| run_017 | position | 5.90 | 1.45 | 0.00 | FAIL / FAIL | FAIL |
| run_017_pid | position | 4.95 | 1.31 | 0.00 | pass / pass | FAIL |
| run_018 | position | 4.94 | 1.00 | 0.00 | pass / pass | FAIL |
| run_019 | position | 5.48 | 0.91 | 0.00 | FAIL / pass | FAIL |

Notes: run_017 (INDI) item 1 still fails with the new definition (excursion 1.45 m, so the fail is from tilt/other item-1 rules, not excursion). Attitude-mode runs have no excursion (skipped). run_017_pid old value is from its own g3_checks.json (4.95 m, README). UNVERIFIED: sp_nan_frac is 0.00 everywhere (these logs have finite x,y setpoints in the span); the excluded-fraction counts truth samples in the span, a reading of the spec's "excluded fraction of the span".
