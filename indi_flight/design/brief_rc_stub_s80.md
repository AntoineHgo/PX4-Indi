# Brief: runner RC/manual stick-path stub (RC79 point 3, STATE item d), written S80

Status: brief only, not launched (S80 cap $1.05 < 2x expected cost). Launch as one `sonnet` task (~$0.9, ~30 tool
calls) at a session cap >= $1.8; haiku second key in the following session (lesson 17: simulator/bench hook).

## Goal and what it serves
G5 (modes and transitions) and the G3 matrix need flights in manual, acro, stabilized, altitude and position modes,
which take stick input. `bench/run_scenario.py` (931 lines) only drives OFFBOARD through pymavlink
`set_position_target_local_ned_send` (lines ~444-452), with fixed-sim-time arm/offboard (T_ARM_S, T_OFFBOARD_S,
lines ~90-105) and the `--sched` / `--sched-anchor` sim-time schedule (anchor on nav_state 14). No path sends
MANUAL_CONTROL today (grep S80: no `manual_control` in bench/).

## What done looks like
1. `run_scenario.py --stick-mode {posctl,altctl,stabilized,acro}`: sets `COM_RC_IN_MODE` to accept MAVLink
   joystick input (check the value names on this branch's parameter metadata, do not guess), streams
   `manual_control_send` at a fixed SIM-time period (reuse the setpoint pacing, 50 Hz), switches mode with
   MAV_CMD_DO_SET_MODE (PX4 custom main mode) after take-off, and anchors the schedule on the observed nav_state of
   that mode (generalise `--sched-anchor` beyond nav_state 14).
2. Stick profile from the scenario dict: new `mode="stick"` scenarios in `scenarios.py` with a z-axis profile built
   from ZSINE_O6 (throttle stick in altctl/posctl = vertical-velocity demand) and a hold segment; each stick sample
   and its sim time logged to `sticks.csv` in the run dir (G1.5 style: applied, not intended).
3. Pre-test (lesson 23): 1 flight `posctl` + 1 `altctl` with PID on quad5in, then 1 each with the INDI stack
   (`MC_INDI_EN 1`, INDI pos module): ulog shows `manual_control_setpoint` at >= 40 Hz, nav_state as requested,
   vehicle follows the vertical-velocity demand; metric script runs on the output. Results under
   `results/stage5_s8x_stick/`, commit metrics.json, run.json, README.md.
4. A self-test of the stick-profile generator on synthetic input (known samples at known sim times).

## Constraints
Docker only (`indi_project/docker/run.sh`), wall-clock timeout on every run, no firmware change (if one looks
needed, stop and report), offboard behaviour of the runner byte-identical (check one existing scenario's sched.txt
before/after). Write progress to `results/stage5_s8x_stick/NOTES.md` as you go.
