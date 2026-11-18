# S89 re-run of hole_report on the G2 outer-loop cells (after 688f198ab2)

Command (per cell, host python, numpy + pyulog; no simulation, no Docker):

    python3 -B indi_flight/bench/hole_report.py <cell>/flight.ulg --out <scratch>/holes/<cell>.json

Output text per cell is kept under the session scratchpad (`holes/<cell>.txt`), not committed.
Exit code 0 = PASS, 1 = FAIL, 2 = no usable data.

Cells: `stage5_s86_g2outer/*` (10 incl. `pretest_parallel/pt1_ax3_r800_s1`) and `stage5_s87_xy/*` (16).
The task brief said 28 cells; only 26 cells have a run.json and a flight.ulg on disk, so 26 are run.

| cell | PASS/FAIL | failing topic and reason | max hole (raw gap, topic) |
|---|---|---|---|
| stage5_s86_g2outer/pretest_parallel/pt1_ax3_r800_s1 | FAIL | sim_ground_truth, sensor_gyro: sim missing 0.213 % (limit 0.05 %), excess 13.75 ms; vehicle_angular_velocity, vehicle_torque_setpoint, actuator_motors: controller holes, excess 13.75 ms | 15.00 ms (sim_ground_truth) |
| stage5_s86_g2outer/pt0_ax1_r400_s1 | FAIL | sim_ground_truth, sensor_gyro: sim missing 0.101 % (limit 0.05 %), excess 12.50 ms; vehicle_angular_velocity, vehicle_torque_setpoint, actuator_motors: count-disagree (count-based missing 28-30 vs gap-based 9-10) | 21.25 ms (vehicle_local_position_setpoint) |
| stage5_s86_g2outer/pt0_ax3_r400_s2 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s86_g2outer/pt0_ax3_r800_s1 | PASS | - | 5.00 ms (vehicle_angular_velocity) |
| stage5_s86_g2outer/pt0_ax3_r800_s2 | PASS | - | 18.75 ms (vehicle_local_position_setpoint, excess 7.50 ms) |
| stage5_s86_g2outer/pt1_ax1_r400_s1 | FAIL | sim_ground_truth, sensor_gyro: sim missing 0.100 % (limit 0.05 %), excess 10.00 ms; vehicle_local_position_setpoint: count-disagree (count-based missing -7) | 12.50 ms (sim_ground_truth) |
| stage5_s86_g2outer/pt1_ax3_r400_s1 | PASS | - | 6.25 ms (sim_ground_truth) |
| stage5_s86_g2outer/pt1_ax3_r400_s2 | PASS | - | 6.25 ms (sensor_gyro) |
| stage5_s86_g2outer/pt1_ax3_r800_s1 | PASS | - | 3.75 ms (vehicle_angular_velocity) |
| stage5_s86_g2outer/pt1_ax3_r800_s2 | PASS | - | 5.00 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt0_ax1_r400_s1 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s87_xy/pt0_ax1_r400_s2 | PASS | - | 6.25 ms (actuator_motors) |
| stage5_s87_xy/pt0_ax1_r800_s1 | PASS | - | 3.75 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt0_ax1_r800_s2 | PASS | - | 3.75 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt0_ax2_r400_s1 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s87_xy/pt0_ax2_r400_s2 | PASS | - | 6.25 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt0_ax2_r800_s1 | PASS | - | 10.00 ms (vehicle_angular_velocity, excess 8.75 ms, under the 10 ms limit) |
| stage5_s87_xy/pt0_ax2_r800_s2 | PASS | - | 3.75 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt1_ax1_r400_s1 | PASS | - | 6.25 ms (sensor_gyro) |
| stage5_s87_xy/pt1_ax1_r400_s2 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s87_xy/pt1_ax1_r800_s1 | PASS | - | 3.75 ms (vehicle_angular_velocity) |
| stage5_s87_xy/pt1_ax1_r800_s2 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s87_xy/pt1_ax2_r400_s1 | PASS | - | 6.25 ms (sim_ground_truth) |
| stage5_s87_xy/pt1_ax2_r400_s2 | PASS | - | 5.00 ms (sim_ground_truth) |
| stage5_s87_xy/pt1_ax2_r800_s1 | PASS | - | 3.75 ms (sim_ground_truth) |
| stage5_s87_xy/pt1_ax2_r800_s2 | PASS | - | 3.75 ms (vehicle_angular_velocity) |

Summary: 23 PASS / 3 FAIL (26 cells run; exit codes match the verdicts).

Changes versus the per-cell READMEs (grep of `hole` / table rows):
- `stage5_s86_g2outer/README.md` 800 Hz rows marked "FAIL (count check)" are now PASS: pt0_ax3_r800_s1, pt0_ax3_r800_s2, pt1_ax3_r800_s2 (the count cross-check no longer fails them under the current code; pt1_ax3_r800_s2 and pt0_ax3_r800_s2 were already PASS under the S88 re-fly section), and pt1_ax3_r800_s1 (top-level copy) is now PASS.
- README S86 line 32 ("All 400 Hz cells PASS hole_report") is contradicted: top-level pt0_ax1_r400_s1 and pt1_ax1_r400_s1 FAIL on sim holes (matches the pretest note on lines 8-10 and fixes_s88.md).
- `stage5_s87_xy/README.md`: the first-flight FAIL of pt0_ax2_r400_s1 (line 44 re-fly section) is PASS here, consistent with its re-fly.
- The s86 pretest copy pretest_parallel/pt1_ax3_r800_s1 remains FAIL, consistent with the README note at lines 8-10.
- The brief's 28-cell count does not match the disk: 26 cells have run.json and flight.ulg.

## Orchestrator verdict (S89)
The 3 FAIL cells are all flights of the S86 parallel pre-test (s86 README finding 1: parallel flights make holes):
pretest_parallel/pt1_ax3_r800_s1, pt0_ax1_r400_s1, pt1_ax1_r400_s1. The s86 ax1 cells are superseded by the serial
S87 xy cells and are not G2 evidence. Gate cells: 7 s86 z cells listed + pt0_ax3_r400_s1 (S83 tb10, separate dir) + 16
s87 xy cells: all hole_report PASS with 688f198ab2. The README line "all 400 Hz cells PASS" counted only serial z cells.
hole_report.py is frozen from this point (D-HOLE-FREEZE, route check 89).
