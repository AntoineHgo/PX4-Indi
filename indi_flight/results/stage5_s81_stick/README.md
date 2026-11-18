# Stick-path stub pre-test (T169, S81 agent, finished S82 by the orchestrator)

Brief: `design/brief_rc_stub_s80.md`. Scenario `stick_zsine_o6` (throttle stick = vertical-velocity demand from the
ZSINE_O6 z profile, peak 1.57 m/s), quad5in, seed 1, speed 2. Command: `bash fly.sh NAME MODE [indi.params]`, then
`python3 bench/stick_check.py DIRS` (writes `stick_check.json`). Raw logs untracked.

| run | nav_state in window | stick rate Hz | lag ms | corr | gain vz/demand | rms err m/s |
|---|---|---|---|---|---|---|
| pid_altctl | 1 (ALTCTL) | 33.4 | 120 | 0.987 | 0.859 | 0.216 |
| pid_posctl | 2 (POSCTL) | 33.3 | 120 | 0.986 | 0.858 | 0.220 |
| indi_altctl | 1 (ALTCTL) | 33.3 | 120 | 0.987 | 0.863 | 0.210 |
| indi_posctl (S82 re-fly, grid pacing) | 2 (POSCTL) | 50.0 | 100 | 0.984 | 0.850 | 0.251 |

Findings
- Pre-test 1 gain 0.30 came from the hard-coded stick expo 0.6 (`src/lib/sticks/Sticks.hpp`); inverting it in
  `bench/stick_profile.py` gives gain 0.86 on both stacks.
- The S81 pacing fix (period 0.0199 s) did not work: the runner's sim clock advances on ATTITUDE ticks ~15 ms apart,
  so t + 20 ms always lands on the 3rd tick (33 Hz, 1488 of 1526 intervals at 30 ms). S82: stick mode sends on a
  fixed sim-time grid (`Sim.sp_grid`); offboard paths keep `t + period` (unchanged).
- PID and INDI give the same gain and lag to 0.005: the response to the raw stick demand is dominated by the stock
  manual setpoint shaping (acceleration/jerk limits), not by the controller. The residual 0.86 is not a tracking
  fault. A controller-level measure needs vz against `vehicle_local_position_setpoint` (stamped in sim time), a
  follow-up for the G5 metric, not for this stub.
- Status: stub works in ALTCTL and POSCTL on both stacks; acro and stabilized are wired (main modes 5 and 7) but
  not flown. Second key (haiku, code to brief) pending, next session.
