# G5.8 moving (3 m/s) failsafe check, key 2

Script `indi_flight/bench/g58_moving_check_key2.py RUN_DIR` (self-test `indi_flight/bench/tests/test_g58_moving_check_key2.py`, all pass). Logs: `g5_events_mov_s{1,2,3}/flight.ulg`.

Definition: reference time = firmware loss flag rise in failsafe_flags (first logged high sample; true rise is in the preceding 0.1-0.6 s gap, the delay upper bound is in the table). Entry = first vehicle_status nav_state change at or after the last low flag sample. Window = entry to next nav change or 15 s. Excursion = max horizontal |sim_ground_truth xy - trajectory_setpoint xy| (truth interpolated to setpoint times, shifted by the ref lat/lon difference of the groundtruth and estimator topics, 0.02-0.03 m). NaN position setpoints: reference integrated from the velocity setpoint, anchored on truth if no earlier reference; exc_valid = valid-position samples only. Limits: delay <= 1 s, excursion <= 1 m. Params in force (from the log): COM_RC_LOSS_T 0.5, COM_DL_LOSS_T 3, COM_OF_LOSS_T 4.0, NAV_RCL_ACT 1 (hold), NAV_DLL_ACT 1 (hold), COM_OBL_RC_ACT 5 (hold); expected nav_state 4 (auto loiter) for all three.

| seed | event | ref time (s) | entry delay (s) [upper bound] | nav entered | NaN fraction | onset speed (m/s) | excursion (m) [valid-only] | verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | rc_loss | 54.756 | 0.010 [0.61] | hold | 0.0 % | 2.99 | 0.210 [0.210] | PASS |
| 1 | link_loss | 76.776 | 0.010 [0.43] | hold | 0.0 % | 3.00 | 0.188 [0.188] | PASS |
| 1 | offboard_loss | 94.256 | 0.010 [0.11] | hold | 0.0 % | 3.00 | 0.211 [0.211] | PASS |
| 2 | rc_loss | 54.953 | 0.010 [0.51] | hold | 0.0 % | 3.02 | 0.213 [0.213] | PASS |
| 2 | link_loss | 77.604 | 0.010 [0.46] | hold | 0.0 % | 3.00 | 0.246 [0.246] | PASS |
| 2 | offboard_loss | 94.454 | 0.010 [0.61] | hold | 0.0 % | 3.00 | 0.233 [0.233] | PASS |
| 3 | rc_loss | 54.651 | 0.010 [0.41] | hold | 0.0 % | 2.99 | 0.170 [0.170] | PASS |
| 3 | link_loss | 76.621 | 0.010 [0.18] | hold | 0.0 % | 3.00 | 0.205 [0.205] | PASS |
| 3 | offboard_loss | 94.351 | 0.010 [0.11] | hold | 0.0 % | 3.00 | 0.207 [0.207] | PASS |

Notes: the post-kill manual_control_signal_lost rise (about 131.5 s, disarmed) is not an event and is ignored (armed filter). NaN fraction is 0 inside every window: trajectory_setpoint carries a valid position from the first sample of the hold; the NaN (velocity-only) samples are all before the nav change, in offboard. Hold setpoint positions lead the truth by up to about 0.25 m while braking from 3 m/s. Residual hover offset truth-minus-estimator is <= 0.012 m (not applied).
