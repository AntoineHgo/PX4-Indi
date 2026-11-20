# G5.8 at 3 m/s, one pre-test flight (S146, seed 1)

## Change
`indi_flight/bench/g5_events.py`: new `--moving` flag (default off; the hover branch of the schedule is the unchanged
original code, only indented under `else:`, plus an inert `"vel" in st` test in tick). With `--moving` the hover
events (ekf_yaw, ekf_xy, hover losses) are replaced by three legs, each: offboard velocity stream on (vx = +3 / -3 / +3 m/s
north-south, vz = 0, yaw held), OFFBOARD mode 2 s later, loss 9 s after the leg start (rc_loss, then link_loss, then offboard_loss; same event
names, so g5_rows_check.py scores them unchanged), then kill/re-arm/land as before. rc and link losses are therefore
flown in OFFBOARD at 3 m/s with the stream kept alive, NOT in the AUTO-hold mode of the hover flight (deliberate
simplification: only a velocity setpoint gives a deterministic 3 m/s).

## Command
indi_project/docker/run.sh -n g5mv1 -t 600 -- python3 indi_flight/bench/g5_events.py --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params indi_flight/results/g5_events_s145/params.params --out indi_flight/results/g5_events_s146_move/s1 --moving

## Ground-truth horizontal speed at the loss instant (vehicle_local_position_groundtruth, t_applied)
rc_loss 2.988 m/s, link_loss 2.994 m/s, offboard_loss 2.998 m/s (all within 3 +- 0.3; vz < 0.003). Speed was a steady 3.0 for >= 4 s before each.

## Checker (g5_rows_check.py, unchanged), G5.8 lines
- rc_loss: entry-timeout 510 ms (<= 1000), nav 14->4 hold at 54.650 s, excursion 5.069 m -> FAIL (<= 1 m)
- link_loss: entry-timeout 2 ms, excursion 12.516 m -> FAIL; "entered nav 14: False" is a checker artefact: its entry is the gcs_connection_lost flag rise
  (76.560 s), 10 ms before nav_state 14->4 (76.570 s); the vehicle did enter hold.
- offboard_loss: entry-timeout 30 ms, nav 14->4 hold, excursion 15.542 m -> FAIL
All three print "hover case only, 3 m/s: not flown" (static text of the checker) and "G5.3/G5.4 not computed".

## Is "excursion" meaningful for a moving loss? No.
It is the max 3-D distance from the position at onset to entry + 5 s. At 3 m/s that includes the distance flown before
the failsafe fires (timeout x 3 m/s) plus the braking distance, so <= 1 m cannot be met by any vehicle. The rows FAIL
by construction, not by controller behaviour. Informational numbers from the ground truth (not a checker output):
braking distance from entry to rest (entry + 5 s) = 3.47 m (rc), 3.43 m (link), 3.40 m (offboard); altitude change after onset <= 0.03 m;
vehicle at rest (< 0.1 m/s) about 3.5 s after entry in all three; max tilt 9.2-9.5 deg. A meaningful criterion for the moving case needs a
decision by the gate owner (e.g. overshoot beyond the stop point predicted by the hold action's deceleration, or
braking distance <= X); checker NOT changed, no self-test added.

## Unverified / notes
- Link-loss timeout reference is the last telemetry_status with the GCS heartbeat flag (73.558 s) although the runner stopped
  heartbeats at 72.128 s; telemetry_status is only published at intervals, so the true loss-to-entry time is 4.44 s vs the 3 s timeout
  (+ up to ~1.4 s of publication lag). The 2 ms "entry-timeout" is therefore not an independent proof; same method as the hover flight.
- G5.3-G5.4 limits after the failsafe not evaluated. rc/link losses in AUTO-hold at 3 m/s not flown. Single seed. G5.9 lines of this flight are for
  the kill after a moving sequence only (FAIL on 9a as in the checker's definition; not examined).
- No second-key review done; g5_events.py change needs one.

## Orchestrator reading (S146)
Probe, not counted. Entry-timeout PASS on the firmware reference; excursion FAIL 5.1/12.5/15.5 m is a gate-definition
defect for the 3 m/s case (distance flown during the timeout + braking; braking alone 3.4-3.5 m from 3 m/s, so
no controller following the stock hold behaviour meets 1 m) -> Q8 addendum 3. Second finding, applies to hover too:
the link_loss reference "last telemetry_status GCS heartbeat" lags the last message actually sent by about 2.25 s
(hover fix_s2: run.json last_msg 75.346 s, flag-reference 77.600 s; mavlink receiver presence window, source not
read), so entry is about 5.26 s after the last GCS message for COM_DL_LOSS_T 3 s. Stock behaviour (O-11), same for
PID. Q8 addendum 3. bench/g5_events.py --moving: no second key yet (hover path claimed unchanged, re-indented).
Key2 (key2_moving.md, S146): hover path unchanged (pure re-indent) CONFIRMED. BLOCKING: under --moving the event
records keep the hover TIMES as t_cmd_us (rc_loss t_cmd 63.1 s vs applied 54.1 s); the checker searches from t_cmd,
so the s1 G5.8 lines above are not valid scores even as a probe. MAJOR: st["vel"] not cleared after rc/link resume
(old 3 m/s setpoint streamed 5-7 s). Speed at loss was verified on ground truth by the author (2.99-3.00 m/s).
Fix both, re-fly s1 before any 3 m/s seed set.
