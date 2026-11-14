# v3 yaw screening, stage 2 (session 47)

Stage-1 base (K_Y 2.733, YAW_CUT 1.665 = indi_v3_tb0.3) and its two survivors (`results/v3_screen_yaw.md`) vs
pid_tuned, seeds 2-3 (`bench/v3_screen_yaw2.sh`, 16 flights, 0 failures, no watchdog trip); seed 1 from stage 1.
step_yaw at speed 4, motor_loss_0 at speed 1, v2 sim config. Means over seeds 1-3; effort = motor-rate RMS (1/s).

| config | step_yaw yaw RMS (deg) | step_yaw effort | motor_loss_0 yaw / roll / pitch RMS (deg) | hover effort x PID (5 seeds) |
|---|---|---|---|---|
| pid_tuned | 12.76 (1.00x) | 1.23 | 8.49 / 0.80 / 0.90 | 1.00 |
| K_Y 2.733, cut 1.665 | 16.36 (1.28x) | 0.94 | 11.23 / 0.67 / 1.03 | 2.03 |
| K_Y 2.733, cut 3.0 | 15.08 (1.18x) | 1.32 (seed 3: 2.15) | 9.72 / 0.60 / 0.92 | 2.14 |
| K_Y 4.0, cut 3.0 | 13.39 (1.05x) | 1.35 | 10.23 / 0.76 / 1.15 | 2.36 |

Per-seed values agree within ~10 % except step_yaw of K_Y 2.733/cut 3.0 (14.3-16.4 deg, effort spike on seed 3).

## Decision (D-v3-freeze)
indi_v3 = K_Y 2.733, YAW_CUT 3.0 on Tb 0.3 (`bench/params/indi_v3.params`): the best roll/pitch under motor loss of
all configs including PID (tilt is what V' W1/W2 judge, and v3 was built for it), motor-loss yaw closest to PID, hover
effort between the two others. K_Y 4.0 tracks yaw steps better but loses pitch under motor loss (1.15 vs PID 0.90)
and has the highest hover effort. The yaw gap to PID stays (1.15-1.18x): reported as a known weakness.
