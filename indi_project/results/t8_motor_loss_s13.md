# T8 motor_loss_0: PID defaults vs INDI tuned (session 13)

Scenario T8 (not used in tuning): motor 0 thrust x0.70 at runtime in attitude mode, then a +45 deg yaw step
(`plan/t8_motor_loss_log.md`). Speed 1, seeds 1-3. Commands: `results/t8_pid_s13.log`, `results/t8_indi_s13.log`
(INDI params `results/tuning/indi/r4f/c00/params`, D-freeze). 6 flights, 0 failures.

| controller | seed | rotation RMS deg | roll RMS | pitch RMS | yaw RMS | motor-rate RMS /s | saturated frac |
|---|---|---|---|---|---|---|---|
| PID | 1 | 9.09 | 0.72 | 0.69 | 9.03 | 0.392 | 0.075 |
| PID | 2 | 8.95 | 0.71 | 0.68 | 8.89 | 0.397 | 0.073 |
| PID | 3 | 9.11 | 0.71 | 0.68 | 9.06 | 0.388 | 0.076 |
| INDI | 1 | 10.25 | 0.08 | 0.15 | 10.25 | 0.507 | 0.119 |
| INDI | 2 | 10.36 | 0.08 | 0.16 | 10.36 | 0.507 | 0.122 |
| INDI | 3 | 10.28 | 0.08 | 0.15 | 10.28 | 0.514 | 0.121 |

Reading (first look, not yet checked on the time series): the motor loss acts on INDI as an unmodelled torque that
the incremental law cancels through the measured angular acceleration, so roll/pitch error under the fault is
5-9x lower than PID's (integrator-based rejection). Yaw tracking is ~14 % worse, consistent with the structural yaw
result (`tuning/r4.md`), and INDI runs saturated more often (12 % vs 7.5 %) with 1.3x motor-rate effort: the
yaw step is executed with a degraded motor. Open: peak tilt and recovery time around the fault onset
(`bench/disturbance.py`), and whether the saturation comes from the yaw step or from holding roll/pitch.
