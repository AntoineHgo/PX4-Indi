# Key 2 review of fee02b59b2 (flight2.ulg), verdict: AGREE on the fixes, DISAGREE on the reported applied-commanded times (MINOR/MAJOR below)
1. ekf_yaw (620): EKF2.cpp:624-636 reads param3 = yaw deg (wrap_pi(radians)), param7 = accuracy deg (NaN -> 20 deg); p1/p2/p4-6 ignored. g5_events.py:89 sends p3=yaw+5, p7=1.0: correct.
   Effect is a genuine reset: resetHeadingToExternalObservation -> resetYawByFusion (ekf.h:452). Log: vehicle_command 620 p3=96.0566 p7=1.0 at 46.490000 s, ack result 0 (accepted),
   vehicle_attitude quat_reset_counter 1->2 at 46.49375, single yaw step +5.016 deg (only step >0.3 deg in 46.3-46.8 s). Pre-test text "no reset counter" in verdicts.txt is WRONG (MINOR, fix text).
2. rc_loss: manual_control_signal_lost 0->1 at 65.04375 (failsafe_flags, 2 Hz log), last override 64.482 -> <=0.562 s, consistent with 0.5 s + tick (log sampling only gives an upper bound).
   Falls at 68.05375 after resume 67.988. failsafe action flag 1 at 65.05. Reaction: no nav_state change (vehicle already in Hold, NAV_RCL_ACT=1), so "configured failsafe" is
   only visible as failsafe active, not as a mode change (MINOR, weak evidence for reaction). Not a weakening: rcS:196-203 sets COM_RC_LOSS_T = speed factor (4 s at --speed 4, i.e. 8x the
   0.5 s PX4 default) and the loss lasted 3.5 s; PX4 timers run on sim (lockstep) time, so the scaling is a wall-time workaround that hid the event. 0.5 = default and the checker's timeout.
   Side note: COM_DL_LOSS_T is also overridden (rcS 40 -> 3); equally a restore, not a loosening.
3. Independent applied-minus-commanded, using vehicle_command.timestamp (PX4 receipt) vs run.json t_cmd_us:
   ekf_yaw 3.00 ms (README 1.0), ekf_xy 4.25 (README 3.0), offboard_mode 4.25 (3.0), hold_mode 1.75 (0.0). All 1.25-3 ms later than README (outside 1 ms): the checker uses runner sim.t after send,
   which precedes PX4 receipt by 1-2 physics steps. Pass/fail of G1.5 (1.25 ms) does not change for ekf_xy/rc_loss (already FAIL); ekf_yaw PASS at 1.0 ms becomes 3.0 ms = FAIL by the same limit,
   hold_mode/offboard similarly. MAJOR if G1.5 is judged with these numbers; the effect-after-applied numbers (5.8 ms) shift by the same offset (reset at 46.49375 is 3.75 ms after receipt).
   Stream-stop events (rc_loss, link_loss) cannot be recomputed from the log: no raw RC/heartbeat send times; input_rc last row 64.485 is a 2 Hz sample, telemetry_status gives gcs heartbeat 76.03.
4. link_loss 5.27 s vs 3 s: not runner wall-time cadence. telemetry_status instance 1 shows runner heartbeats every 1.00 s sim (72.03..76.03), last 76.03, and PX4 keeps republishing
   telemetry_status with heartbeat_type_gcs=1 at 77.29 (cleared by 78.55, 2.52 s after the heartbeat); Commander.cpp:3012 stamps _datalink_last_heartbeat_gcs with telemetry.timestamp (publish time),
   so the effective last heartbeat is 77.29, i.e. +1.26 s. 77.29+3 = 80.29; flag at 81.30 leaves ~1.0 s unexplained (likely Commander loop cadence/ordering; not verified).
   The 3 s timeout itself is respected relative to the last stamped heartbeat.
