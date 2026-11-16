# T55 pretest, second key (session 26)

Independent check of the two T55 flights, written from the raw logs only. Script:
`indi_flight/bench/second_key_t55.py` (run in the px4-indi-sim image, pyulog).
Per-row CSVs in this folder: `check1_step_roll_r1.csv`, `check1_traj_lemniscate_r1.csv`,
`check3_traj_lemniscate_r1.csv`.

Inputs: `indi_flight/results/t55_pretest_s26/{step_roll_r1,traj_lemniscate_r1}/{flight.ulg,sched.txt,run.json}`.

Conventions found in the data (not assumed):
- `sim_schedule_applied.t_sched_us` holds the absolute time: the sched.txt time for rows before the anchor, and `anchor_us + offset` for rows after it. It is not the bare offset.
- Kind codes are not given in the task. From counts and times: 1 = arm (30 s), 3 = mode_offboard (52 s), 5 = sp_hold, 6 = anchor, 9 = att, 10 = pva, 11 = sp_back. Codes 1, 3 and 11 are inferred from these matches.
- `anchor_us` is 52.018750 s (step) and 52.015000 s (traj). The sched.txt anchor row is nominally 52.000 s. The offsets are measured from `anchor_us`, so using 52.000 s would be off by 18.75 ms and 15 ms.

## Check 1: sched.txt rows vs sim_schedule_applied

Expected time = `anchor_us + offset` for rows after the anchor. The table covers the rows that have an offset.

| flight | sched rows | applied rows | rows with offset | max abs err (us) | rows > 1250 us | duplicate (kind, t_sched) | max abs sp error vs expected |
|---|---|---|---|---|---|---|---|
| step_roll_r1 | 10 | 10 | 6 (5 att + sp_back) | 0 | 0 | 0 | 7.1e-9 |
| traj_lemniscate_r1 | 866 | 866 | 862 (861 pva + sp_back) | 275 | 0 | 0 | 2.3e-7 |

Per kind (sched rows / applied rows): step arm 1/1, mode_offboard 1/1, sp_hold 1/1, anchor 1/1, att 5/5, sp_back 1/1. traj arm 1/1, mode_offboard 1/1, sp_hold 1/1, anchor 1/1, pva 861/861, sp_back 1/1.

- The only nonzero timestamp error is the traj sp_back row: applied 75.232500 s, expected 75.232225 s, error +275 us. The mean error of 0.3 us over 862 rows is consistent with that single row.
- Applied sp values match the expected values: att roll and pitch are absolute, and yaw is hold yaw (1.5875 rad) plus the offset. pva x, y, z are the hold position plus the offset.

Verdict: **AGREE** for both flights.

## Check 2: step_roll, vehicle_attitude_setpoint roll (from q_d)

| sched offset (s) | sched roll (deg) | log change, rel. anchor (s) | latency (ms) | log roll median +0.3..+0.7 s (deg) | diff (deg) |
|---|---|---|---|---|---|
| 3.000 | 0.00 | no change (0 to 0) | n/a | 0.00 | 0.00 |
| 5.000 | 15.00 | 5.000 | 0.0 | 15.00 | 0.00 |
| 8.000 | 0.00 | 8.000 | 0.0 | 0.00 | 0.00 |
| 11.000 | -15.00 | 11.000 | 0.0 | -15.00 | 0.00 |
| 14.000 | 0.00 | 14.000 | 0.0 | 0.00 | 0.00 |

The steps land on the scheduled instants, at the first sample at or after each one. Latency is measured against the 0.1 s pre-window, so only the 3 s row (which is a no-op) reads a negative value. The log also shows a roll change at 17.508 s (0.00 to -9.55 deg, then about 0.6 deg) and one at 22.716 s (-0.45 to 0.06 deg). Both come after sp_back at 17.000 s and are not schedule rows.

Verdict: **AGREE**.

## Check 3: traj_lemniscate, pva rows vs trajectory_setpoint.position

The pva rows are offsets relative to the hold point. The sp_hold row captured (kind 5) x, y, z = (0.0027, 0.0168, -7.2011) m NED, which matches `hold_pos_ned` in run.json. For all 861 rows, the first trajectory_setpoint at or after the applied timestamp is exactly at the applied timestamp (0.0 ms gap).

| pva idx | sched offset (s) | sched x y z (m) | applied ts (s) | TSP x y z (m) | err vs raw sched (m) | err vs hold + sched (m) |
|---|---|---|---|---|---|---|
| 0 | 6.000 | 0.000 0.000 0.000 | 58.015 | 0.003 0.017 -7.201 | 7.201 | 0.000 |
| 215 | 10.300 | 2.474 -1.944 0.000 | 62.315 | 2.476 -1.927 -7.201 | 7.201 | 0.000 |
| 430 | 14.600 | -0.030 -0.030 0.000 | 66.615 | -0.028 -0.014 -7.201 | 7.201 | 0.000 |
| 645 | 18.900 | -2.425 1.929 0.000 | 70.915 | -2.423 1.945 -7.201 | 7.201 | 0.000 |
| 860 | 23.200 | -0.000 -0.000 0.000 | 75.215 | 0.003 0.017 -7.201 | 7.201 | 0.000 |

Over all 861 rows, the error against hold + sched is 0.000 m (3 decimals), max. The raw error is 7.201 m, all in z: the z offset is 0, and the hold is at -7.20 m NED.

Caveat: the TSP is the module's own output, so this confirms what the player injects. It does not test PX4 tracking.

Verdict: **AGREE** (positions are offsets to the hold point).

## Check 4: run.json segment starts vs anchor_us

Time base: run.json uses the same microsecond clock as the ULog `timestamp` and `anchor_us`. Each event time equals `anchor_us + offset` to 0.000 ms.

step_roll_r1 (anchor_us 52.018750 s):

| run.json item | t_us | sched offset (s) | diff vs anchor_us (ms) |
|---|---|---|---|
| settle (= sched_t0_us = window start) | 55018750 | 3.000 | 0.000 |
| up | 57018750 | 5.000 | 0.000 |
| zero1 | 60018750 | 8.000 | 0.000 |
| down | 63018750 | 11.000 | 0.000 |
| zero2 | 66018750 | 14.000 | 0.000 |
| window end (sp_back row) | 69018750 | 17.000 | 0.000 |

traj_lemniscate_r1 (anchor_us 52.015000 s):

| run.json item | t_us | sched offset (s) | diff vs anchor_us (ms) |
|---|---|---|---|
| settle (= sched_t0_us = window start) | 55015000 | 3.000 | 0.000 |
| traj (first pva) | 58015000 | 6.000 | 0.000 |
| hold (sp_back row) | 75232225 | 23.217225 | 0.000 (log sp_back applied at 75232500, +0.275 ms) |
| window end | 78232225 | hold + 3 s | CANNOT CHECK: no schedule row, the 3 s is the hold duration |

Not an anchor: run.json `t_offboard_us` is 52865000 (step), 846.25 ms after anchor_us, and 52825000 (traj), 810.00 ms after anchor_us. These are the offboard send times, not the anchor.

Verdict: **AGREE** for every event tied to a schedule row. The window end after the traj hold is CANNOT CHECK.

## Summary

| check | step_roll_r1 | traj_lemniscate_r1 |
|---|---|---|
| 1 row presence and timing | AGREE (max 0 us) | AGREE (max 275 us, sp_back row) |
| 2 roll steps | AGREE | not applicable |
| 3 pva positions vs TSP | not applicable | AGREE (0.000 m vs hold + sched) |
| 4 run.json vs anchor_us | AGREE (0.000 ms) | AGREE (0.000 ms) |

Overall: AGREE on all checks that apply. Out of scope: the sp_back transient in the step roll at 17.5 s, and PX4 tracking error, which these checks do not measure.
