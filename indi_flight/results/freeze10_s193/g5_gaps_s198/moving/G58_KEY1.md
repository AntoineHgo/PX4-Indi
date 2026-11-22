# G5.8 at 3 m/s, key 1 (S198 flights, `--moving`)

Script `indi_flight/bench/g58_moving_check.py RUN_DIR --out FILE` (self-test `bench/tests/test_g58_moving_check.py`, 5 tests, plain python, pass). Per-flight outputs `g58_key1_mov_*.txt/.json` in this folder.
Gate text (GATES row G5.8, Q8 add.3 (i)): excursion = max horizontal deviation of ground truth from the setpoint the failsafe action commands <= 1 m; failsafe entered <= 1 s after its timeout (S144 reference: rc = manual_control_signal_lost rise - COM_RC_LOSS_T 0.5 s; link = last gcs heartbeat in telemetry_status + COM_DL_LOSS_T 3 s; offboard = last offboard_control_mode + COM_OF_LOSS_T 4 s; reference code copied from g5_rows_check).

## Definitions used
- Entry = first vehicle_status.nav_state change after the event; nav entered = the new state.
- Commanded setpoint = trajectory_setpoint position x, y. NaN position (velocity-only offboard setpoints) samples are excluded from the deviation (nothing positional is commanded); their fraction in the window is reported (at most the first setpoint at entry: 0 or 1 sample of 293-535). An informational velocity-integrated reference over those samples gave the same maximum.
- Truth = vehicle_local_position_groundtruth x, y, shifted into the estimator frame by median(estimator - truth) over [T0-8 s, T0-0.5 s] (hover before the schedule); offsets 1-3 cm (printed per flight). Deviation evaluated at setpoint sample times (truth interpolated).
- Window = entry until the next nav_state change (the script re-enters offboard) or the kill event, max 15 s.

## Result
| flight | event | timeout ref (s) | entry (s) | nav entered | entry - ref (ms) | NaN pos in window | excursion (m) | speed at onset (m/s) | window (s, end) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| INDI s1 | rc_loss | 54.256 | 54.766 | 4 hold | 510 | 1/526 (0.2 %) | 0.211 | 2.99 | 10.49, nav_state change to 14 | PASS |
| INDI s1 | link_loss | 76.766 | 76.786 | 4 hold | 20 | 1/325 (0.3 %) | 0.191 | 2.99 | 6.47, nav_state change to 14 | PASS |
| INDI s1 | offboard_loss | 94.239 | 94.266 | 4 hold | 28 | 0/399 (0.0 %) | 0.212 | 3.00 | 7.97, kill event | PASS |
| INDI s2 | rc_loss | 54.453 | 54.962 | 4 hold | 510 | 1/526 (0.2 %) | 0.209 | 3.02 | 10.49, nav_state change to 14 | PASS |
| INDI s2 | link_loss | 77.599 | 77.614 | 4 hold | 15 | 1/293 (0.3 %) | 0.251 | 3.00 | 5.84, nav_state change to 14 | PASS |
| INDI s2 | offboard_loss | 94.441 | 94.464 | 4 hold | 22 | 0/399 (0.0 %) | 0.229 | 3.01 | 7.97, kill event | PASS |
| INDI s3 | rc_loss | 54.151 | 54.661 | 4 hold | 510 | 0/535 (0.0 %) | 0.158 | 3.00 | 10.69, nav_state change to 14 | PASS |
| INDI s3 | link_loss | 76.620 | 76.631 | 4 hold | 11 | 0/336 (0.0 %) | 0.216 | 3.01 | 6.72, nav_state change to 14 | PASS |
| INDI s3 | offboard_loss | 94.335 | 94.361 | 4 hold | 26 | 0/398 (0.0 %) | 0.196 | 2.99 | 7.97, kill event | PASS |
| PID s1 (reference) | rc_loss | 56.261 | 56.771 | 4 hold | 510 | 1/531 (0.2 %) | 0.479 | 2.89 | 10.59, nav_state change to 14 | PASS |
| PID s1 (reference) | link_loss | 79.509 | 79.521 | 4 hold | 12 | 1/293 (0.3 %) | 0.514 | 2.87 | 5.84, nav_state change to 14 | PASS |
| PID s1 (reference) | offboard_loss | 96.347 | 96.371 | 4 hold | 24 | 0/399 (0.0 %) | 0.458 | 2.83 | 7.97, kill event | PASS |

All INDI events PASS: entry 11-28 ms after its timeout for link and offboard, 510 ms for rc (which is the 0.5 s COM_RC_LOSS_T plus one cycle: the reference is the flag rise minus 0.5 s, hence a fixed 510 ms; within 1 s), excursion 0.16-0.25 m (limit 1 m), speed at onset 2.99-3.02 m/s.

## Link-loss nav state (the "nav 14" report)
The failsafe did enter hold (nav 4) on all three INDI flights and on the PID flight. The earlier "entered nav 14" comes from g5_rows_check.entry_time(), which takes the earliest of nav-change and vehicle_status.gcs_connection_lost rise (the flag rises 10 ms before the nav change: 76.776 vs 76.786 s in s1) and then reads the nav state at the flag instant, which is still 14. Before the timeout the vehicle stays in offboard (nav 14) and keeps flying the velocity stream (about 4.5 s, i.e. 13 m) because the 3 s timeout runs from the last heartbeat; the failsafe then switches to hold and brakes. Excursion is measured from that entry.

## PID reference (not a pass condition)
Flown once: `g5_events.py --controller pid_default --model quad5in --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --seed 1 --moving --out moving/g5_events_mov_pid_s1` through `indi_project/docker/run.sh -n s198g5_mov_pid_s1 -t 900`, `timeout 1000` as fly.sh, leftover containers stopped first. No `--params` file: the S157 file is INDI-only (MC_INDI_EN 1 would switch the rate loop to INDI via the runner alias); the failsafe parameters (NAV_*_ACT, COM_*_T) are set by g5_events itself (run.json params_applied). The option name is `pid_default` (run_scenario has no `pid`). PID link-loss also goes nav 14 -> 4 (hold) at 79.521 s, 12 ms after its timeout, so it does not stay in 14 either. PID excursions 0.46-0.51 m (about twice the INDI values), all PASS by the same rule. The stdout log shows one skipped param (COM_RC_OVERRIDE not present in this build), harmless. The existing g5_rows_check.py crashes on this PID flight in its INDI-only G5.9d step; not touched.
