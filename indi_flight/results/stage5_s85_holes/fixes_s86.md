# S86 hole_report fixes (second-key findings 1-3)

Files: indi_flight/bench/hole_report.py, indi_flight/bench/tests/test_hole_report.py (run: `python3 -I indi_flight/bench/tests/test_hole_report.py`, ALL PASS).

## Fixes
| Finding | Change | Location (hole_report.py) | Test (test_hole_report.py) |
|---|---|---|---|
| 2 controller dt vs sim attribution | `_stats(..., hold_gaps=nl)`: max controller dt is taken over all non-logger gaps, including those attributed to a sim hole; count stays attributed | `_stats` and the controller loop in `analyse` (`hold_gaps=nl`) | "S86 12 ms controller hole next to 2.5 ms sim hole FAIL" |
| 3 sim not assessable | if neither sim_ground_truth nor sensor_gyro is present, class sim is forced FAIL with verdict "sim: not assessable (no sim_ground_truth or sensor_gyro in the log)", also printed by `fmt` | `analyse`, `if sim_primary is None:` | "S86 no primary sim topic: not assessable FAIL", plus a presence control |
| 1 count cross-check | new `count_missing()` = round(span/median)+1-n; per controller row `missing_count_based`, `count_disagree` (abs diff to gap-based missing > 1) sets the row to FAIL (not PASS) | `count_missing`, controller loop in `analyse`, `fmt` | "S86 count cross-check disagreement is not PASS" (5 isolated lost samples balanced by 5 far duplicate stamps: gap 5, count 0), plus "agrees on a real hole" |

Deviation from the request: n in the count formula is ALL samples including duplicate stamps, not n_unique. On indi_posctl about 1000 duplicate stamps replace stamps without losing samples (total count is complete), so n_unique would report ~1000 missing and fail a healthy run. Consequence: the check does not catch a lost sample hidden by an adjacent duplicate (that case is indistinguishable by count); it catches gap/count inconsistencies of more than 1 (for example gaps with compensating stray duplicates, median drift). Logger-explained gaps are removed from the count basis. The dup-cancel heuristic is unchanged.

## Break checks (each fix reverted once, tests run, restored from a saved copy)
- Fix 2 reverted (`hold_gaps=None`): FAIL "S86 12 ms controller hole next to 2.5 ms sim hole FAIL".
- Fix 3 reverted (`if False:`): the "no primary sim topic" test failed (before I switched to `.get`, it crashed with KeyError 'verdict', i.e. also a failure).
- Fix 1 reverted (`count_disagree = False`): FAIL "S86 count cross-check disagreement is not PASS".
Restored each time; final run ALL PASS.

## Re-run on the README logs
- stage5_s84_accbreak/hf: OVERALL PASS (sim 5 holes max 6.25 ms; controller 1 hole max 5.0 ms), no count disagreement (count-based missing 1, 1, 0 vs gap-based 1, 1, 1 for angular_velocity, torque_setpoint, actuator_motors). Unchanged.
- stage5_s83_stick/indi_posctl: OVERALL PASS (sim 0; controller 2 holes max 2.5 ms), count-based = gap-based = 2 on all three. Unchanged.
(The committed hf/indi_posctl .txt/.json in this directory were not regenerated.)
