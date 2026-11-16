# T53 player kinds, session 25 (not committed)

Extends `sim_scenario_player` (see t49_player_s24.md). Steps 1-4 done; SITL build rc=0 (Docker, `make px4_sitl_default`,
astyle run on the two C++ files).

## File format (additions to t49)
`t_sim_us kind fields`, `#` comments. New kinds:
- `sp_hold [dx dy dz]`: setpoint = vehicle_local_position x,y,z (+ offsets, default 0, NED m) and `heading`, read at apply
  time (needs xy_valid and z_valid, else error printed and setpoint unchanged). Replaces the hard-coded hold of the runner.
- `anchor nav_state=<N>`: the row is activated at its time like any row, then the whole schedule is suspended until
  vehicle_status.nav_state == N and arming_state == ARMED. The anchor instant is the `timestamp` of the vehicle_status
  message that first shows that (never earlier than the activation). Every row after the anchor holds its time as an
  OFFSET (us) from the anchor instant; sort order restarts at 0 after each anchor row. Several anchors allowed: the rows
  after the second are relative to the second (the second anchor row itself is relative to the first). No timeout: if the
  state is never reached the schedule stays suspended.
- `takeoff [alt]`: VEHICLE_CMD_NAV_TAKEOFF, params as the runner's MAV_CMD 22 (p1 NAN, p2 0, p3 0, p4..p6 NAN, p7 = alt, default NAN).
- `land`: VEHICLE_CMD_NAV_LAND, params as the runner's MAV_CMD 21 (all 0 except p4..p6 NAN).
Applied topic `sim_schedule_applied` gained `anchor_us` (anchor the row is based on, 0 before any), `sp[4]` (setpoint
applied by sp / sp_hold, NAN else) and KIND_SP_HOLD 5, KIND_ANCHOR 6, KIND_TAKEOFF 7, KIND_LAND 8. `t_sched_us` of a
relative row is the absolute time (anchor + offset); the anchor row logs its activation time in `t_sched_us`, the observed
instant in `anchor_us`, so `timestamp - t_sched_us` of the anchor row is the wait.

## Changes (file:line, working tree)
- `msg/SimScheduleApplied.msg:8,16-22`: kinds, anchor_us, sp[4].
- `src/modules/simulation/sim_scenario_player/SimScenarioPlayer.hpp`: format doc at the class comment, `Row::rel`,
  `_local_pos_sub:109`, anchor state `:119-123`, `apply()` and `publish_command()` signatures (all 7 params).
- `SimScenarioPlayer.cpp`: parse `:74,94,142-180` (sp_hold, takeoff, land, anchor, rel flag); `publish_command:210`;
  `apply:275` (sp_hold `:301`, takeoff `:321`, land `:326`, anchor `:331`, applied fields `:337`); `Run:343-390`
  (anchor wait/activation `:356-383`).
- `indi_flight/bench/run_scenario.py`: `SCHED_HOLD_POS/YAW` removed (`:87-88`), rows in `start_px4` `:241-246`
  (`sp_hold` instead of `sp 0 0 -5 1.585`), new `--sched-anchor` (`:551`) appends `anchor nav_state=14` + `3000000 sp_hold`
  + `6000000 sp_hold` (SCHED_ANCHOR_ROWS `:87`).
- New `indi_flight/bench/t53_check.py` (ULog check, run through docker: pyulog not on the host).

## Pre-test (hover, quad5in, pid_default, seed 1, speed 4, `--sched --sched-anchor`, exit_status ok)
Out: `indi_flight/results/t53_pretest_s25/hover_r1` (analysis.txt = t53_check.py output).
| Check | Result |
|---|---|
| Armed | row 0 arm applied 30.000000 s (err 0), vehicle_status arming_state 2 at 30.003750 s |
| sp_hold at 51.000 s | err 0; captured (0.047, 0.021, -4.968) m, heading 1.587 rad (was hard-coded 0, 0, -5, 1.585) |
| Offboard | mode row at 52.000000 s (err 0); vehicle_status nav_state 14 at 52.015000 s |
| Anchor instant | anchor_us = 52015000 = logged nav_state change, exactly (0 us) |
| Rows after anchor | applied 55015000 and 58015000 = anchor + 3 s / + 6 s, error 0 us both; captured (0.059, 0.051, -4.965) and (0.060, 0.027, -4.969) |
| Hover | z mean -4.960 (anchor+1..3 s), -4.965 (+3..6), -4.973 (+6..12); max abs x 0.08, y 0.064 m |
The 15 ms between the offboard row and the anchor is Commander's mode-change latency (A-17), now absorbed by the anchor.

## Unverified
- `takeoff` and `land` kinds: built only, never flown (the runner still sends MAV_CMD 22/21 over MAVLink).
- Second anchor in one file, anchor wait with a state never reached (no timeout), anchor when already in the state.
- sp_hold with invalid local position (error path), nonzero offsets.
- One run only; no 5-run G1.6 spread with the anchored rows. Hold captured on a 1 s-old climb tail would differ slightly
  between runs (z -4.968 vs -4.965): the hold value is a flight quantity, not a scenario constant.
- Format of the msg change vs. real hardware: msg is sim-only, but `msg/` is shared (all boards regenerate).
- `make check_format` not run on the host; astyle run in Docker only.
