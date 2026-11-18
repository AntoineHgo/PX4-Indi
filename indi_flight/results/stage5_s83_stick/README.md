# S83 stick-path re-fly with sim-time grid pacing

Why: the second key of the stub (`../stage5_s81_stick/second_key.md`, DISAGREE) found that three of four S81 rows
were flown before the S82 grid-pacing fix (33 Hz, brief asks >= 40 Hz), and that the README claim "both stacks"
rested on them. All four rows are re-flown here on one firmware (a38533428f), scenario stick_zsine_o6, quad5in,
seed 1, speed 2. Commands: `bash flyall.sh` (calls `fly.sh NAME MODE [indi.params]`), then
`indi_project/docker/run.sh -n s83sc -t 300 -- python3 indi_flight/bench/stick_check.py <4 dirs>`.

| run | nav_state | stick Hz | lag ms | corr | gain | rms err m/s |
|---|---|---|---|---|---|---|
| pid_altctl | [1] | 50.0 | 100 | 0.9862 | 0.859 | 0.217 |
| pid_posctl | [2] | 50.0 | 100 | 0.9872 | 0.859 | 0.215 |
| indi_altctl | [1] | 50.0 | 120 | 0.9873 | 0.862 | 0.211 |
| indi_posctl | [2] | 50.0 | 120 | 0.9865 | 0.859 | 0.217 |

Reading:
- The brief's >= 40 Hz criterion is met on all four rows, and nav_state is the requested one in every window.
  The DEVIATION of the second key is closed by these flights.
- PID and INDI agree to 0.003 in gain and 20 ms in lag. The response to the raw stick demand is set by the stock
  manual setpoint shaping, not by the controller (as in S81). The S81 claim "same gain and lag to 0.005" holds here
  for gain only. Lag differs by one 20 ms step: 100 ms PID, 120 ms INDI.
- Still open from the second key: MISSING generalised nav_state schedule anchor (`--stick-mode` refused with
  `--sched`). This is needed for mode switches in motion (G5), not for this stub. G5 metric vs
  vehicle_local_position_setpoint is not written yet.
