# T55 player attitude / trajectory setpoints (session 26, not committed)

Status log (update as work proceeds): step 1 notes written; steps 2-6 pending.

## 1. What the MAVLink runner path does today (read before the change)
Runner: `bench/run_scenario.py` (`send_att` :438, `send_pva` :422, `send_pos` :416, `traj_phase/traj_pos/traj_pva` :449-485,
scenario loop :770-800). Setpoint stream: `sim.run(dur, sp=...)` calls `sp()` whenever `sim.t >= next_sp` and a new
ATTITUDE tick arrived, `SETPOINT_PERIOD = 0.02` sim s (50 Hz, jittered by telemetry ticks).
Timeline (non-sched): arm 30 s, climb, hold captured at T_HOLD = 51 s (pos, yaw), POSITION_TARGET stream of hold to
T_OFFBOARD 52 s, DO_SET_MODE offboard, observed, 3 s `offboard_settle` still streaming the hold position, then the
scenario segments (sim.t at that moment = t_seg0), then `recover` 4 s of hold position, then MAV_CMD 21 land.
- Attitude mode (step_roll): MAVLink SET_ATTITUDE_TARGET, `type_mask 0b00000111` (roll/pitch/yaw RATE ignored, attitude
  and thrust used), q = ZYX euler(roll, pitch, hold_yaw + yaw_step), body rates 0, thrust = `thr_cmd(tilt)` at EVERY
  message: `clamp(thr0/tilt + ALT_KP*e + ALT_KD*vz, 0.1, 0.95)`, thr0 = hover_thrust_estimate read at T_HOLD (0.5 if
  not in 0.1..0.9), tilt = max(0.3, cos r cos p) of the commanded roll/pitch, e = z - hold_z (NED, + = too low),
  vz = NED velocity from telemetry, ALT_KP 0.04, ALT_KD 0.10. So thrust is closed loop on altitude (not a constant).
  step_roll segments (scenarios.py:_attitude_steps): settle 2 s 0 deg, up 3 s +15, zero1 3 s 0, down 3 s -15, zero2 3 s 0
  (pitch 0, yaw offset 0 = hold yaw).
- MavlinkReceiver (`handle_message_set_attitude_target` mavlink_receiver.cpp:1880): attitude=true, body_rates=false (mask
  bits), has_thrust. Publishes `offboard_control_mode` {attitude=true, all else false} on every message; publishes
  `vehicle_attitude_setpoint` {q_d, yaw_sp_move_rate = NAN (BODY_YAW_RATE_IGNORE set), thrust_body = (0, 0, -thrust)
  for MAV_TYPE_QUADROTOR (fill_thrust :1826)} ONLY when vehicle_status.nav_state == OFFBOARD (not accepts_offboard_setpoints).
  No trajectory_setpoint at all in attitude mode.
- Trajectory mode (traj_lemniscate): MAVLink SET_POSITION_TARGET_LOCAL_NED frame LOCAL_NED, `type_mask 0b100000000000`
  (only yaw RATE ignored): position = hold_pos + traj_pos(phase(t)), velocity and acceleration = central differences
  (h = 1 ms) of that path (traj_pva), yaw = hold_yaw, target sys/comp 1/1. LEMNISCATE: ax 4, ay 2, w = 5/sqrt(32), laps 2,
  ramp 3 s -> traj duration 17.2 s; segments settle 3 s (hold position), traj 17.2 s, hold 3 s (hold position).
  Receiver (:1236-1345): trajectory_setpoint {position, velocity, acceleration, yaw = hold_yaw, yawspeed = NAN, jerk 0};
  `fill_offboard_control_mode`: position, velocity, acceleration = true, attitude = isfinite(yaw) = true, body_rate = false;
  offboard_control_mode published on every message, trajectory_setpoint only when accepts_offboard_setpoints.
- Peak speed 5 m/s (lemniscate, phi = 0), peak acceleration ~3.1 m/s^2 (x), jerk ~11 m/s^3 (y component).

## 2. New row kinds (file format additions to t49/t53)
- `sp_back`: setpoint = x y z heading captured by the last `sp_hold` (the runner's `pos_sp`/hold_pos), position stream.
- `att roll pitch yaw thrust`: roll, pitch [rad], yaw [rad] OFFSET to the heading of the last sp_hold (the runner's
  hold_yaw + step), thrust 0..1 or `auto` (= hover_thrust_estimate read at the last sp_hold / tilt + ALT_KP*(z-hold_z) +
  ALT_KD*vz from vehicle_local_position at every publish, clamp 0.1..0.95, exactly the runner's thr_cmd; the only
  difference is the source of z/vz: uORB estimate at the publish tick instead of MAVLink telemetry). Stream: `offboard_control_mode`
  {attitude} every 20 ms of sim time, `vehicle_attitude_setpoint` {q_d = Quatf(Eulerf), yaw_sp_move_rate NAN,
  thrust_body (0,0,-thrust)} only in nav_state OFFBOARD, as MavlinkReceiver. No trajectory_setpoint.
- `pva dx dy dz vx vy vz ax ay az`: position = sp_hold position + offsets, yaw = sp_hold heading, yawspeed NAN, jerk 0.
  Stream `offboard_control_mode` {position, velocity, acceleration, attitude} every 20 ms, `trajectory_setpoint` when
  accepts_offboard_setpoints (as MavlinkReceiver).
  DECISION on stale rows: both. Runner writes one row per 20 ms (= SETPOINT_PERIOD, the MAVLink sample rate, so the
  reference is the one the MAVLink path sends); the player ALSO propagates p + v dt + a dt^2/2, v + a dt from the row time to the
  publish time (dt capped at 0.2 s), so a sparser file (user choice) does not hold a stale position. Why: the loop runs on
  the 800 Hz gyro tick, the cost is a few flops, and it removes the hold error: without propagation the worst hold error
  at the peak speed 5 m/s over one 20 ms row is 0.10 m (the unavoidable zero-order hold of the MAVLink path itself, since
  the receiver publishes once per message); with it, residual = jerk dt^3/6 = 11 * 8e-6 / 6 = 15 um at 20 ms and 1.8 mm at
  100 ms rows. In the 20 ms file the row is applied on the same tick it is published, so dt < 1.25 ms (6 mm at 5 m/s
  recovered).
- `sim_schedule_applied` (sim-only msg extended): KIND_ATT 9 (sp = roll, pitch, yaw absolute, thrust or NAN for auto),
  KIND_PVA 10 (sp = absolute x y z yaw at the row time), KIND_SP_BACK 11 (sp = x y z yaw). `sp_hold` rows now also capture
  the hold used by att / pva / sp_back (hold position, heading, hover thrust). att/pva/sp_back before any sp_hold: error
  printed, row ignored.
- Row struct f[4] -> f[9]; `_rows.reserve(2048)`. No fixed row limit (std::vector), Row = 8+1+1+36 -> 56 bytes.

## 3. Runner (indi_flight/bench/run_scenario.py)
- `sched_scenario_rows(sc)` (above `hover_thrust`), `SCHED_SETTLE_S = 3.0`; start_px4 rows block; `--sched` refusal now only
  for rate mode or scenarios with runner-side hooks (disturbance, motor_fault, erpm_loss, thrust_sag: they use the
  runner's segment times); in sched mode every scenario `sp` is None (the runner only waits sim time).
- Rows: offsets (us) after `anchor nav_state=14` with --sched-anchor (scenario starts anchor + 3 s, like metrics.py
  OFFBOARD_SETTLE_S), else absolute T_OFFBOARD_S + offset. Without --sched-anchor the scenario would shift with the
  Commander latency; use --sched-anchor.
- Row counts generated: step_roll 6 rows (5 att + sp_back, thrust PD runs inside the player); traj_lemniscate 862 rows
  (861 pva at 20 ms for 17.217 s + sp_back) plus arm, sp_hold, mode_offboard, anchor = 866 total. Memory
  866 x 56 B = 48 kB (vector capacity 2048 x 56 = 115 kB reserved). Applied topic: one publish per row, rows 20 ms apart,
  queue 8 never overrun at that spacing.
- Runner time base fix found by the first pre-test: run.json segment times (events, t_window_*, trajectory t0) came from the
  runner's own sim.t at the observed mode change (HEARTBEAT, 0.7 s late in the first traj run), so metrics.py scored the
  lemniscate against a reference 0.7 s late: rms_3d 1.62 m (estimate). Fix in the runner (metrics.py untouched):
  `sched_anchor_s()` reads `anchor_us` of the last `sim_schedule_applied` through px4-listener, `sched_t0 = anchor + 3 s`,
  `seg_now()` gives the events / window / trajectory t0 (`meta["sched_t0_us"]`). First (wrong-t0) runs are kept in
  `*_r1_noanchor_t0` (same flights otherwise).

## 4. File:line of changes (working tree, nothing committed)
- `msg/SimScheduleApplied.msg:17-19` (KIND_ATT/PVA/SP_BACK), `:25` (sp comment).
- `src/modules/simulation/sim_scenario_player/SimScenarioPlayer.hpp`: format doc (class comment), includes, `Row::f[9]`,
  constants ALT_KP/ALT_KD/PVA_DT_MAX_S, `enum Stream`, `publish_position/attitude/pva`, hold/att/pva state.
- `SimScenarioPlayer.cpp`: `read_floats`, load() kinds sp_back / att / pva, `publish_setpoint` dispatcher + `publish_attitude`
  + `publish_pva`, apply() cases SP_BACK / ATT / PVA, sp_hold captures hold + hover thrust, `reserve(2048)`.
- `indi_flight/bench/run_scenario.py`: `SCHED_SETTLE_S`, `sched_scenario_rows`, `sched_anchor_s`, start_px4 rows, main
  (`--sched` check, `sp = None` in sched, `sched_t0` / `seg_now`).
- New: `indi_flight/bench/t55_check.py`, `indi_flight/bench/t55_row1.py` (Docker: pyulog).
- Zero diff outside these (git status: 4 modified files + 2 new scripts + result dirs).

## 5. Build
`indi_project/docker/run.sh -n t55build -t 1800 -- bash -c "Tools/astyle/fix_code_style.sh <cpp> <hpp>; make px4_sitl_default"`:
astyle "Unchanged" on both files (already conformant), build rc=0 (1443 steps, full rebuild because the msg changed).

## 6. Pre-tests (quad5in, pid_default, seed 1, speed 4, --sched --sched-anchor, wall 34 s and 37 s, exit_status ok, no crash, landed)
Out: `indi_flight/results/t55_pretest_s26/{step_roll,traj_lemniscate}_r1` (analysis.txt = t55_check.py).
| Check | step_roll | traj_lemniscate |
|---|---|---|
| Flew | yes, exit ok, final z -0.03 m | yes, exit ok, landed |
| Rows in file / applied | 10 / 10, row_index contiguous | 866 / 866, contiguous |
| Applied - scheduled (us) | all 0 except anchor row 18750 (the wait for nav_state 14) | all 0 except anchor 15000 and sp_back 275 (its time 23217225 is off the 1.25 ms grid, < 1 tick); 861 pva rows err 0 |
| Anchor vs vehicle_status nav_state 14 | equal (diff 0) | equal (diff 0) |
| Setpoint seen by the controller | vehicle_attitude_setpoint roll at anchor+3 s +2/+5/+8/+11 s: 0 -> +15.000 -> 0 -> -15.000 -> 0 deg, jumps exactly at the scheduled times (first sample 0 us after), constant within segments; thrust_body z = -0.13..-0.142 (auto PD); altitude z -5.132..-5.003 (hold -5.018) | trajectory_setpoint position vs hold + traj_pos(traj_phase) for all 861 samples in the window: max err 0.0000 m (float precision); 5 instants (t_traj 1.72, 5.16, 8.60, 12.04, 15.48 s) all |err| 0.0000 m; velocity sp e.g. (2.02, 1.63, 0), (-3.52, 3.47, 0), (3.54, 3.54, 0) m/s |
| Tracking (metrics.py, window = ULog anchor + 3 s) | rise 10-90 0.186 s, delay 0.064 s, overshoot 0.003 %, settle 5 % 0.30 s, 4 steps, none unsettled; roll rms 2.61 deg | trajectory rms_3d vs estimate 0.495 m (horizontal 0.495, vertical 0.022), max 1.02 m; vs truth 0.718 m, max 1.46 m (pid_default baseline) |
Earlier first run of traj_lemniscate (same build, `_noanchor_t0`): 861 pva rows, 4 of them applied 1-2 ticks late (max 2500 us, mean err 29 us) - a
non-zero tail seen once in two runs, cause not investigated (sensor_gyro callback tick skipped under host load?).

## 7. Row-1 answer (t53 hover_r1, `t55_row1.py`, `results/t55_pretest_s26/row1_analysis.txt`)
sp_hold row 1 at 51.000000 s: sp (0.04686, 0.02137, -4.96844). The first trajectory_setpoint after it (51.011 s) is (0.0323,
0.0380, -4.9563), 1.45 / 1.66 / 1.22 cm away, with velocity (0, 0, -0.001) (not NaN) and 41 distinct positions among the 51
samples before 52.015 s. vehicle_status.accepts_offboard_setpoints is 0 until 52.015 s, so the player publishes NO trajectory_setpoint
in that interval (it publishes only when accepted, like MavlinkReceiver). The publisher is the other one: FlightModeManager
(`FlightModeManager.cpp:364`, `_trajectory_setpoint_pub`, the Hold flight task, finite velocity). At 52.020 s the first player
sample equals the row's sp to 0.0 cm (velocity NaN). So the 1.5 cm is Hold mode, confirmed; the player is exact.

## 8. Unverified
- One flight per scenario (no 5-run spread, no byte-compare of the setpoints between runs); G1.6 gate not run.
- Equality with the MAVLink path was shown by construction (same functions, mask, thrust formula) and against the analytic
  reference, not by flying the same scenario with the non-sched runner and diffing logs. The `auto` thrust reads z and vz from
  vehicle_local_position at the publish tick (MAVLink: telemetry), and hover thrust at the sp_hold row (51 s, runner: T_HOLD 51 s CLI read).
- Propagation inside the player is implemented but not exercised: every pva row was published on its own tick (dt < 1.25 ms).
- Yaw offsets (step_yaw), pitch and rollpitch attitude scenarios, circle/zmulti trajectories: rows are generated by the same code, not flown.
- Land (MAV_CMD 21) is still sent over MAVLink by the runner after the scenario + 4 s recover; the 4 s recover and hold are the
  player's `sp_back` position hold.
- Runner-side hooks (disturbance, motor_fault, erpm_loss, thrust_sag) refused with --sched. Without --sched-anchor the scenario
  is on absolute times (T_OFFBOARD_S + 3 s...), and run.json times then come from the runner's sim.t (not corrected).
- `make format`/`check_format` on the host not run; astyle ran in Docker (Unchanged).
- First sample of the attitude settle segment can come from mc_pos_control (roll -0.135 deg in the second run): the topic has two publishers around the mode switch.
