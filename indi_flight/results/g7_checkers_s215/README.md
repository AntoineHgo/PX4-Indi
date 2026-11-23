# G7 checker defects (S215c)

Scope: bench/offb_vel_check.py, bench/passthrough_check.py (SELFTEST_G7_S194 item 9), pointers g511_check.py:184 and
g510_check.py:115-119. Bench Python only; no threshold changed (GATES.md G5.5 offb_vel_step: RMS(vx-2) last 3 s <= 0.2,
end |vx| <= 0.1, max |dz| <= 0.3, no LOC; pass-through: window exists, 0 att_sp, 0 indi_pos_status inside it). Not committed.
Note: g3_checks.py (LOC helper: tilt_rad, longest_run_s, 60 deg / 0.2 s / 2 m drop) imports scipy at module level via
g4_metrics and scipy is missing on this host, so offb_vel_check.py carries a copy of the same two small functions.

## Defects and fixes
| # | defect | fix (file:line, new code) |
|---|---|---|
| 1 | offb_vel: no verdict, no exit code | offb_vel_check.py:66-68 (PASS/FAIL per limit, RESULT, exit 0/1; INVALID exit 2) |
| 2 | offb_vel: LOC never checked | :58-64: tilt > 60 deg for > 0.2 s (truth vehicle_attitude_groundtruth, as g510/g3), height drop > 2 m below pre-step height, NaN; over step..end of hold |
| 3 | offb_vel: "time to 90%" 0.00 s if vx never > 1.8 | :50-52 prints "never reached (vx max ..)" |
| 4 | offb_vel: final \|vx\| one sample | :53-54 mean \|vx\| over the last 1 s of the hold (END_WIN_S; interpretation of "at the end of the hold", threshold unchanged) |
| 5 | offb_vel and passthrough: IndexError / ValueError on empty or absent topic | offb_vel_check.py:30-39 and window checks; passthrough_check.py:7-8,14-23: INVALID, exit 2 |
| 6 | passthrough: no verdict / exit code | passthrough_check.py:43-46 |
| 7 | passthrough: "all off 0" not flagged (never engaged) | :44 prints "pass-through never engaged", FAIL window_exists |
| 8 | passthrough: indi_pos_status absent/empty counted as 0 samples | now INVALID (criterion not evaluable) |

## Tests added (bench/tests), break-check on the S194 checkers (copies in scratchpad, tree never dirty)
- test_offb_vel_check.py: test_verdict_and_exit_code, test_loc_tilt_and_height (0.3 s vs 0.1 s at 70 deg, 50 deg, drop 2.1 / 1.9 m),
  test_never_reaches_90pct, test_final_vx_is_a_mean, test_empty_topic_is_invalid_not_a_crash. Old checker: all 5 FAIL (the
  6 older cases still pass on both). Empty topic on the old checker raises ValueError (argmax of empty), not IndexError.
  Fixture change: end-of-hold vx now set over the last 1 s. Mutations: 8 -> 11 (window start, LOC tilt, LOC duration, exit code added;
  "[-1]->[0]" replaced), all detected.
- test_passthrough_check.py: test_verdict_and_exit_code, test_never_engaged_is_a_fail, test_empty_or_absent_topic_is_invalid
  (old: all 3 FAIL); test_absent_status_reported kept (ABSENT still printed). Mutations 4 -> 6 (exit code, window_exists), all detected.
- Run: python3 -I indi_flight/bench/tests/test_offb_vel_check.py and test_passthrough_check.py -> both print OK.

## g511_check.py:184 and g510_check.py:115-119: described, NOT changed
- g511_check.py:184 is `excess = tilt - p95`. Event tilt jump is the max over [ta, ta+1]; p95 is the 95th percentile of the
  same function at no-event instants (0.25 s grid). I see no arithmetic error (negative excess passes, NaN p95 -> INVALID at
  :191-192, NaN excess would compare False = FAIL). Possible concern is statistical (a max against a p95), but that is the S175
  design, so no defect I can pin down.
- g510_check.py:115-119 (truth pos, quaternion, tilt = arccos(1-2(q1^2+q2^2)), np.interp onto truth time) matches the
  g3_checks tilt definition. Observation: analyse() line 65 LOC uses `tilt_max >= 60` on any single sample, GATES says
  > 60 deg for > 0.2 s (stricter than GATES, so it cannot turn a GATES-pass into a pass; at worst a false FAIL), and
  np.interp clamps if the attitude truth does not cover the pos truth span (no coverage check). Left unfixed; the STATE
  pointer does not say which of these is meant.

## Re-score (old vs new checker, same logs)
| row | log | old | new | changed |
|---|---|---|---|---|
| G5.5 offb_vel_step s1 (freeze-10) | results/freeze10_s193/g55/offb_vel_step_s1 | last3 RMS 0.007, end 0.007, dz 0.031, no verdict | 0.007, 0.008, 0.031, no LOC, PASS | no |
| G5.5 offb_vel_step s2 | .../offb_vel_step_s2 | 0.012, 0.011, 0.052 | 0.012, 0.008, 0.052, no LOC, PASS | no |
| G5.5 offb_vel_step s3 | .../offb_vel_step_s3 | 0.013, 0.015, 0.078 | 0.013, 0.006, 0.078, no LOC, PASS | no |
| S133 offb_vel (not a G5 gate row, design/impl_s133) | results/s133_passthrough/vel | 0.092, 0.071, 0.040 | same, end 0.071, PASS | no |
| S133 ACRO pass-through (not a freeze-10 row) | results/s133_passthrough/acro/flight.ulg | 71 of 171 off, 0 att_sp, 0 pos_status | PASS | no |
Freeze-10 G5.5 verdict came from bench/g55_check.py (key 1 *.check.txt: PASS, vx_end_abs 0.0068 etc.), which this work does not
touch; offb_vel_check.py is the S133 side check. g510/g511 unchanged, so their rows (G5.10, G5.11) were not re-scored.
Raw .ulg present for all logs above. The new passthrough checker on s133 vel (not pass-through) FAILs window_exists, as it should.

## Conclusion
No G5 gate row changes (G5.5 offb_vel_step 3/3 PASS under old and new checker; no LOC on any log).
