# T49 sim_scenario_player, session 24

## Files changed (not committed)
- New `src/modules/simulation/sim_scenario_player/` (Kconfig `MODULES_SIMULATION_SIM_SCENARIO_PLAYER`, CMakeLists.txt,
  SimScenarioPlayer.hpp/.cpp). `px4::WorkItem` (hp_default) with a `SubscriptionCallbackWorkItem` on `sensor_gyro`.
- New `msg/SimScheduleApplied.msg` (timestamp, t_sched_us, row_index, kind; queue 8), listed in `msg/CMakeLists.txt`.
- `boards/px4/sitl/default.px4board`: `CONFIG_MODULES_SIMULATION_SIM_SCENARIO_PLAYER=y` (only SITL default).
- `ROMFS/px4fmu_common/init.d-posix/rcS`: after `mavlink boot_complete`, `[ -e sim_schedule.txt ]` then
  `sim_scenario_player start -f sim_schedule.txt` (path relative to the px4 working dir).
- `indi_flight/bench/run_scenario.py`: `--sched`, `sim_schedule_applied` in LOG_TOPICS, schedule writer in `start_px4`.
- New `indi_flight/bench/player_check.py`, `indi_flight/results/player_s24/` (README, two runs).

## Schedule file
Plain text, `t_sim_us kind fields...`, `#` comments, rows sorted by time. Kinds: `arm`, `disarm`, `mode_offboard`,
`sp x y z yaw` (NED m, rad, `nan` allowed). New kinds = new keyword in `load()` and a case in `apply()`; unknown kind
aborts the start. The px4 working dir is the runner's `<out>/rootfs` (`px4 -w`), so the runner writes
`rootfs/sim_schedule.txt` (and a copy `<out>/sched.txt`). Hover schedule: `30e6 arm`, `51e6 sp 0 0 -5 1.585`,
`52e6 mode_offboard` (T_ARM_S, T_OFFBOARD_S - PRESTREAM_S, T_OFFBOARD_S).

## Verified facts
- hrt in SITL is sim time: the build has `-DENABLE_LOCKSTEP_SCHEDULER`; `hrt_absolute_time()` returns
  `lockstep_scheduler.get_absolute_time()` (drv_hrt.cpp:112-122), set by `px4_clock_settime(CLOCK_MONOTONIC)` from the gz
  clock callback (GZBridge.cpp:475-489). It is 0 until the first gz clock message and jumps by one physics step
  (1.25 ms) per clock message. It does not start at wall time. The runner's `sim.t` (ATTITUDE time_boot_ms) is the same
  base, and both pre-test runs armed at row time 30.000 s exactly, so the schedule times are directly sim time.
- Rows are applied on the first `sensor_gyro` callback with hrt >= t_sim_us, in file order, then the held setpoint is
  published on the same tick when due. Stream: `offboard_control_mode` always, `trajectory_setpoint` only when
  `vehicle_status.accepts_offboard_setpoints` (as mavlink_receiver.cpp:1333-1343), every 20 ms of sim time.
- vehicle_command fields as COMMAND_LONG from the runner: `from_external=true`, source 255/0, target comp 1,
  target_system = vehicle_status.system_id (fallback 1). ARM param1 1 / DISARM 0 / DO_SET_MODE (1, 6).
- Build: `make px4_sitl_default` in Docker, rc=0 (first attempt failed: missing `sensor_gyro.h` in the .hpp, fixed).
- Format: `Tools/astyle/fix_code_style.sh` run on the two new C++ files in Docker (see end of session output).

## Pre-test (hover, speed 4, seed 1, two identical runs, both `exit_status ok`)
1. Arms and enters offboard: vehicle_status arming_state 2 at 30.006250 s, nav_state 14 at 52.016250 s. Hover over
   10 s starting 3 s after offboard: z mean -5.0016 m (min -5.018, max -4.989), |x| < 0.04 m, |y| < 0.021 m. PASS.
2. applied timestamp - t_sched_us = 0 us for all 3 rows in both runs (rows sit on the 1.25 ms tick grid; bound < 1250 us).
   PASS.
3. vehicle_status change after the applied row: arm 6250 us (5 IMU periods), offboard 16250 us (13 IMU periods).
   FAIL against "1-2 IMU periods", but identical in both runs (spread 0 us). The latency is Commander's own: it runs
   as a task with `px4_usleep(10 ms)` (Commander.cpp:2211, COMMANDER_MONITORING_INTERVAL 10 ms) and the mode change takes
   several loops. It is not the player. For G1.6(a) the quantity that matters is the spread across runs: 0 us here
   against 7.5-11 ms before (2 runs only, not the 5-run gate).

## UNVERIFIED / limits
- Take-off (MAV_CMD 22) and land (21) are still sent over MAVLink by the runner; only arm, offboard switch and the
  setpoint stream are scheduled. The arm-to-takeoff and land instants are therefore still wall-clock jittered.
- The hold setpoint is a constant (0, 0, -5, yaw 1.585) taken from earlier runs, not captured from the flight; yaw is
  model/spawn dependent (quad5in and x500 both face East in these runs). Other models need their own value.
- `--sched` supports position scenarios only; no arm retry (a rejected arm times out 30 s wall).
- A different scenario with stick or trajectory setpoints needs further kinds (`sp` has no velocity/acceleration fields).
- Not run: 5-run G1.6 gate, gz restarts (hrt starting offset if gz world time does not start at 0 is irrelevant here since
  rows use absolute sim time and arm happened at the scheduled 30.000 s).

## If cut: next step
1. Decide on criterion 3 (Commander latency 6.25 / 16.25 ms, deterministic) and rerun G1.6(a) with `--sched` on 5 runs.
2. Add `takeoff` and `land` kinds (vehicle_command 22 / 21) and an incremental file reload (player polls the file size
   at 10 Hz sim time) so the runner can append rows after take-off with the captured hold position.
3. Then `manual_control`, param step and injector-trigger kinds.
