# G5 events injector fix (S144): ekf_yaw and rc_loss now applied and detected
What was wrong (both were injector set-up faults, no firmware change):
1. ekf_yaw: command id 43002 is not MAV_CMD_EXTERNAL_ATTITUDE_ESTIMATE. PX4 uses 620 (msg/versioned/VehicleCommand.msg:95,
   handled in src/modules/ekf2/EKF2.cpp:624 -> resetHeadingToExternalObservation, p3 = yaw deg, p7 = accuracy deg).
   43002 was published and denied (ack result 2), the EKF never saw it. Fix: bench/g5_events.py:89 sends 620, accuracy 1 deg
   (was 0.001 deg).
2. rc_loss: RC from MAVLink is used (COM_RC_IN_MODE 0, input_rc via RC_CHANNELS_OVERRIDE, mavlink_receiver.cpp:2366) and
   the flag name/topic (failsafe_flags.manual_control_signal_lost, rcAndDataLinkCheck.cpp:56) is right. rcS:201-203 sets
   COM_RC_LOSS_T = speed factor = 4 s at --speed 4, the loss lasted 3.5 s, so the flag never rose. Fix: g5_events.py:25
   sets COM_RC_LOSS_T 0.5 (the checker's 0.5 s timeout; no threshold loosened).

Flight command (repo root, same as S142, wall timeout 600 s):
  indi_project/docker/run.sh -n g5s144b -t 600 -- python3 indi_flight/bench/g5_events.py --controller indi --model quad5in
  --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params indi_flight/results/g5_events_s144/params.params
  --out indi_flight/results/g5_events_s144/flight2
flight1 (same, ekf_yaw still 43002 + COM_RC_LOSS_T fix only): rc_loss detected (flag 0.42 s after last msg), ekf_yaw FAIL
(ack DENIED, led to the id finding). flight2 is the reference (verdicts.txt, metrics.json, run.json in each flight dir).

Verdicts flight2 (applied-commanded in ms; G1.5 limit 1.25 ms):
- ekf_yaw: effect PASS, yaw step 5.016 deg of 5 deg, 5.8 ms after applied; applied-commanded 1.0 ms.
- rc_loss: detected, manual_control_signal_lost rose 0.55 s after the last override (timeout 0.5 s); applied-commanded 3.0 ms (FAIL G1.5 timing).
- ekf_xy 3.0 ms (mag 0.988 of 1), link_loss 3.0 ms, offboard_loss 0.0, kill 0.0 (unchanged from S142).
Unverified: G1.5 1-step applied time for MAVLink events remains the S142 Q8 limit (runner tick); ekf_yaw reported as
"no reset counter" in the checker text although resetYawByFusion increments quat_reset_counter (not re-checked on the log);
one seed, one flight; link_loss onset 5.27 s vs 3 s timeout and failsafe_flags 2 Hz logging not investigated.
