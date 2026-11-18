# T186 / S88: hole_report max-hole spec fixes

## Changes (bench/hole_report.py, bench/tests/test_hole_report.py)
- Fix 1: new `raw_gaps()` takes gaps (dt > 1.5 x median) from the raw sorted timestamps, no duplicate cancelling. `_stats` takes
  max hole from these. The old code dropped a k=2 gap from the list when a duplicate absorbed its missing count.
- Fix 2: hole test is per topic: (dt - median_dt) > LIM_HOLE_MS. LIM_HOLE_MS = 10.0 kept as the EXCESS limit (the code documented
  no other value; the old flat 10 ms was the only number). Rows now carry `max_hole_ms` (raw largest dt) and `max_excess_ms`
  (verdict basis); class rows and the text report show both.
- Logger-explained raw gaps are still excluded (same overlap rule). Controller still holds sim-explained gaps to the limit.
- Count check (missing fraction limits, count cross-check, tolerance) unchanged; nothing found wrong with it.

## Tests (python3 -B indi_flight/bench/tests/test_hole_report.py; the file is a numpy-only script, not pytest; pytest is not installed)
New: S88a k=2 gap + dup reported (raw 2.5 ms, missing 0); S88a 100 Hz dup + 21 ms gap fails on excess 11 ms;
S88b 89 Hz 18.75 ms gap PASS (excess 7.5), 25 ms gap FAIL (excess 13.8); S88c 250 Hz 15 ms gap FAIL (excess 11).
Result on new code: ALL PASS (all old cases + 5 new).
Break check, old code (git HEAD source), behaviour of each scenario run directly:
- S88a k=2 + dup: old PASS, max_hole 0.0 ms (the escape). New test FAILS on old code (also KeyError max_excess_ms).
- S88b 18.75 ms at 89 Hz: old FAIL (flat 10 ms), new PASS. New test fails on old code.
- S88b 25 ms at 89 Hz: old FAIL, new FAIL (regression guard, not a discriminator).
- S88c 250 Hz 15 ms: old FAIL, new FAIL (regression guard; the old flat limit already rejected it).
- S88a 100 Hz dup + 21 ms: old FAIL too (gap > 2 periods stayed listed); regression guard.
Old code cannot run the new tests past the first new assertion (KeyError on the new field), so "fails on old" is shown by the
S88a/S88b-pass assertions plus the direct runs above.

## Re-run on all 28 G2 cells (host, pyulog; old verdict = OVERALL line of <cell>_holes.txt)
Worst = topic with the largest excess (may be a sim-info groundtruth topic, which is not in the verdict).
| cell | old | new | worst topic / gap | failing topics (new) |
|---|---|---|---|---|
| s86_g2outer/pt0_ax1_r400_s1 | FAIL | FAIL | sim_ground_truth 15.00 ms raw / exc 12.50 | sim_ground_truth(frac), sensor_gyro(frac), vehicle_angular_velocity(cnt), vehicle_torque_setpoint(cnt), actuator_motors(cnt) |
| s86_g2outer/pt0_ax3_r400_s2 | PASS | PASS | sim_ground_truth 5.00 ms raw / exc 2.50 | - |
| s86_g2outer/pt0_ax3_r800_s1 | PASS | PASS | vehicle_attitude_groundtruth 5.00 ms raw / exc 3.75 | - |
| s86_g2outer/pt0_ax3_r800_s2 | FAIL | PASS | vehicle_local_position_setpoint 18.75 ms raw / exc 7.50 | - |
| s86_g2outer/pt1_ax1_r400_s1 | FAIL | FAIL | sim_ground_truth 12.50 ms raw / exc 10.00 | sim_ground_truth(frac), sensor_gyro(frac), vehicle_local_position_setpoint(cnt) |
| s86_g2outer/pt1_ax3_r400_s1 | PASS | PASS | sim_ground_truth 6.25 ms raw / exc 3.75 | - |
| s86_g2outer/pt1_ax3_r400_s2 | PASS | PASS | sensor_gyro 6.25 ms raw / exc 3.75 | - |
| s86_g2outer/pt1_ax3_r800_s1 | PASS | PASS | vehicle_angular_velocity_groundtruth 5.00 ms raw / exc 3.75 | - |
| s86_g2outer/pt1_ax3_r800_s2 | FAIL | FAIL | vehicle_attitude_groundtruth 13.75 ms raw / exc 12.50 | sim_ground_truth(hole), sensor_gyro(frac), vehicle_angular_velocity(hole), vehicle_torque_setpoint(hole), actuator_motors(hole) |
| s87_xy/pt0_ax1_r400_s1 | PASS | PASS | sim_ground_truth 5.00 ms raw / exc 2.50 | - |
| s87_xy/pt0_ax1_r400_s2 | PASS | PASS | actuator_motors 6.25 ms raw / exc 3.75 | - |
| s87_xy/pt0_ax1_r800_s1 | PASS | PASS | vehicle_attitude_groundtruth 3.75 ms raw / exc 2.50 | - |
| s87_xy/pt0_ax1_r800_s2 | PASS | PASS | vehicle_attitude_groundtruth 3.75 ms raw / exc 2.50 | - |
| s87_xy/pt0_ax2_r400_s1 | FAIL | FAIL | vehicle_local_position_setpoint 28.75 ms raw / exc 17.50 | vehicle_angular_velocity(cnt), actuator_motors(cnt), vehicle_local_position_setpoint(cnt) |
| s87_xy/pt0_ax2_r400_s2 | PASS | PASS | vehicle_angular_velocity 6.25 ms raw / exc 3.75 | - |
| s87_xy/pt0_ax2_r800_s1 | PASS | PASS | vehicle_attitude_groundtruth 11.25 ms raw / exc 10.00 | - |
| s87_xy/pt0_ax2_r800_s2 | PASS | PASS | vehicle_attitude_groundtruth 3.75 ms raw / exc 2.50 | - |
| s87_xy/pt1_ax1_r400_s1 | PASS | PASS | sensor_gyro 6.25 ms raw / exc 3.75 | - |
| s87_xy/pt1_ax1_r400_s2 | PASS | PASS | sim_ground_truth 5.00 ms raw / exc 2.50 | - |
| s87_xy/pt1_ax1_r800_s1 | PASS | PASS | vehicle_attitude_groundtruth 3.75 ms raw / exc 2.50 | - |
| s87_xy/pt1_ax1_r800_s2 | PASS | PASS | sim_ground_truth 5.00 ms raw / exc 3.75 | - |
| s87_xy/pt1_ax2_r400_s1 | PASS | PASS | sim_ground_truth 6.25 ms raw / exc 3.75 | - |
| s87_xy/pt1_ax2_r400_s2 | PASS | PASS | sim_ground_truth 5.00 ms raw / exc 2.50 | - |
| s87_xy/pt1_ax2_r800_s1 | PASS | PASS | sim_ground_truth 3.75 ms raw / exc 2.50 | - |
| s87_xy/pt1_ax2_r800_s2 | PASS | PASS | vehicle_attitude_groundtruth 3.75 ms raw / exc 2.50 | - |

Verdict changes: ONE. s86_g2outer/pt0_ax3_r800_s2 FAIL -> PASS (vehicle_local_position_setpoint, 18.75 ms raw gap, excess 7.5 ms at
~89 Hz; the old flat 10 ms limit rejected it). The other 27 are unchanged: no new FAIL appeared from raw gaps (the k=2+dup
escape did not hide a >10 ms-excess hole in any cell). Note pt0_ax2_r800_s1 has a sim-info groundtruth gap of exactly 10.00 ms
excess (not in the verdict, and the rule is strict >).
Caveat: the old column is the stored verdict text, produced by the code of its day (S86/S87), not a re-run of the HEAD code.

## DECISIONS.md-ready text
- S88 hole_report spec: the single-hole limit is computed per topic from RAW timestamp gaps (before duplicate cancelling/merging).
- A gap is a hole if (gap - topic nominal period) > 10 ms, nominal = median raw dt; the 10 ms is now an excess limit, not a flat gap.
- Count checks (missing fraction, count cross-check) unchanged; effect on G2 cells: pt0_ax3_r800_s2 FAIL -> PASS, no other change.
