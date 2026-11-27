# P7A review rows (G7 limit lines)

Limit lines written in `report/04_limits.md`, new section 4.6 (4.6.1 to 4.6.7). REVIEW_ITEMS.md not edited. 11.3d not touched (other agent).

| id | new state | where written | evidence |
|---|---|---|---|
| 2.2d, 5.3a | LIMIT | 4.6.1 | ANOMALIES.md A-6 (OPEN, cause unknown, ablation not run); G4 PASSED freeze-10 (GATES.md "G4 verdict at freeze-10", results/freeze10_s193/G4_SCORES.md: 18/18, narrow RMS max 3.46e-4 < 5e-4). Note: no number for the size of the excess itself was found in records; the line states it qualitatively. |
| 3.4c | LIMIT | 4.6.2 | ANOMALIES.md A-4; GATES.md G3 verdict (lines ~726-750, 803-814): failing draws 264, 3, 245 re-flown at speed 1 and reproduce; 77 item-2 indices not re-flown; step_roll seeds 1-3 speed 1 vs 4 test not flown. |
| 4.6b | JUSTIFIED + LIMIT | 4.6.3 | src/lib/indi_rate_control/indi_rate_control.hpp (torque path "same filter chain as the gyro derivative": low-pass only, no notch; notch exists only in mc_indi_pos_control velocity path); McIndiRateControl.cpp reads IMU_GYRO_CUTOFF / IMU_DGYRO_CUTOFF; bench/params/quad5in_indi_defaults.params has no IMU_GYRO_NF*. Bring-up item: notches off for first hover. |
| 11.2c | LIMIT | 4.6.4 | design/scenario_overrides_key_s110.md M-1; direction: drag overstated on a moving vehicle (no damping). |
| 7.g8 | JUSTIFIED (accepted at G7 verdict) | 4.6.7 | REVIEW_ITEMS.md + this file; acceptance itself is the owner/key decision, not recorded yet. |
| 11.3e | CLOSED | none (not a limit) | commits 3ab7c72046, 1ac5d58c89; results/g7_s250/P6A_TESTS.md, results/g7_s251/P6B_TESTS.md (not re-read here, taken from the task statement). |
| 3.5d (weak) | LIMIT added | 4.6.5 | GATES.md sag 1.0-0.7 rows (:282, :382) support the injected sag; no voltage model confirmed; limit was missing, now written. 4.3 shares the line. |
| 6.3/10 (weak) | SUPERSEDED, record thin | none | F-4 in DECISIONS.md is "Archive" (indi_project never modified), only loosely a "fresh start" record; MISSION.md, LESSONS.md, run_orchestrator.sh exist but were not read row by row (a guard hook blocked a combined ls). Closure is by supersession of an archive-era process audit; not row-supported. |
| 11.3b (weak) | LIMIT added | 4.6.6 | SITL G2/G3/G5 on the full plant are real evidence; D-G7-HARNESS not re-read. No outer closed-loop unit test exists; limit written. |
| 11.3c (weak) | LIMIT added | 4.6.6 | grep of src/modules/mc_indi_pos_control/*Test.cpp finds no tilt/roll/pitch/quaternion use: level-only confirmed. SITL tilted flight is cited but not tied to a specific row that would catch a wrong-way rotation. |

Orchestrator, 6.3/10: SUPERSEDED confirmed. Process audit of stage-1 agent management, not delivered code; replaced by the mission's subagent rules (hands-off rule, model and effort per task, purpose lines, at most 3 at a time) and lessons 15 and 21. No limit line needed.
