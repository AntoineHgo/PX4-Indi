# v3 yaw rate loop stage-1 screening (session 46, O-12)

Script `bench/v3_screen_yaw.sh`, 2026-11-15 ~00:47-00:55, v3 binary, v2 sim config, seed 1, watchdog on. INDI configs
= `indi_v3_tb0.3` (Tb 0.3, outer gains = tuned PID's) with MC_INDI_K_Y x MC_INDI_YAW_CUT; k2.733_c1.665 is the Tb 0.3
config unchanged. Effort = motor-rate RMS (1/s).

| config | step_yaw yaw RMS (deg), effort | motor_loss_0 yaw / roll / pitch RMS (deg) | hover effort | status (step_yaw, motor_loss_0, hover) |
|---|---|---|---|---|
| pid_tuned | 12.71, 1.17 | 8.41 / 0.80 / 0.90 | 0.023 | ok, ok, ok |
| K_Y 2.733, cut 1.665 | 15.93, 0.87 | 11.09 / 0.67 / 1.03 | 0.046 | ok, ok, ok |
| K_Y 2.733, cut 3.0 | 14.25, 0.87 | 9.63 / 0.60 / 0.91 | 0.052 | ok, ok, ok |
| K_Y 4.0, cut 1.665 | - | - | 0.053 | **failed, failed**, ok |
| K_Y 4.0, cut 3.0 | 13.30, 1.19 | 10.22 / 0.76 / 1.16 | 0.049 | ok, ok, ok |
| K_Y 5.5, cut 1.665 | 36.65, 2.20 | - | 0.061 | ok (oscillating), **failed**, ok |
| K_Y 5.5, cut 3.0 | 13.01, 1.59 | - | 0.061 | ok, **failed**, ok |

## Reading (screening, 1 seed)
- A higher yaw gain behind the 1.67 Hz YAW_CUT filter is unstable (K_Y 4.0 failed twice, K_Y 5.5 oscillates): the
  filter's phase lag limits K_Y, as expected from D-yawsp. Raising YAW_CUT to 3 Hz admits a higher K_Y.
- Pruned: K_Y 4.0/cut 1.665 and both K_Y 5.5 (failures). Survivors: K_Y 2.733/cut 3.0 (step_yaw 1.12x PID, motor-loss
  yaw 1.14x, roll/pitch better than PID, lower step effort) and K_Y 4.0/cut 3.0 (1.05x, 1.21x, 1.0x effort).
- No config closes the yaw gap: yaw stays 1.05-1.25x PID. Consistent with r4 (v1: yaw near-parity is structural).
- **Hover effort flag:** every INDI config is ~2x pid_tuned here (0.046-0.061 vs 0.023), above the 1.5x limit of V'
  criterion 4. Single-seed hover effort is noisy (v2 seen set, 10 seeds: 1.26x), and the Tb 0.3 base is already
  2x, so check the blend's hover effort over several seeds before freezing (session 47).
