# v3 hover effort over seeds 1-5 (session 47)

Question (from `results/v3_screen_yaw.md`): is the ~2x hover motor-rate effort of every v3 config on seed 1 real,
and does the actuator blend (Tb 0.3) cause it? V' criterion 4 (`bench/scenarios.md` sec. 9): hover effort at most
1.5x `pid_tuned`. Hover (T1), speed 1, v2 sim config. Seeds 2-5 from `bench/v3_hover_effort.sh`, seed 1 from the yaw
screen (`v3_tb0.3` = `k2.733_c1.665` there, same parameters). Effort = mean motor-rate RMS (1/s). Table from
`python3 bench/v3_hover_effort.py`. 20 flights, no watchdog trip, no failure.

| config | s1 | s2 | s3 | s4 | s5 | mean s2-5 | ratio s2-5 | ratio s1-5 |
|---|---|---|---|---|---|---|---|---|
| pid_tuned | 0.0228 | 0.0236 | 0.0278 | 0.0243 | 0.0273 | 0.0257 | 1.00 | 1.00 |
| v3_tb0 | - | 0.0699 | 0.0482 | 0.0556 | 0.0614 | 0.0588 | 2.28 | 2.34 |
| v3_tb0.3 | 0.0456 | 0.0462 | 0.0578 | 0.0591 | 0.0464 | 0.0524 | 2.03 | 2.03 |
| k2.733_c3.0 | 0.0519 | 0.0455 | 0.0424 | 0.0733 | 0.0564 | 0.0544 | 2.11 | 2.14 |
| k4.0_c3.0 | 0.0495 | 0.0562 | 0.0747 | 0.0635 | 0.0531 | 0.0619 | 2.40 | 2.36 |

## Reading
- **All v3 configs are ~2x pid_tuned (2.03-2.40x over 4-5 seeds), above criterion 4.** The seed-1 flag is real.
- **The blend does not cause it:** Tb 0.3 is the lowest INDI config (2.03x); Tb 0 (the v2 inner loop with PID's outer
  gains) is 2.28x. The yaw survivors do not lower it (2.11x, 2.40x).
- **It is inherited from v2.** In the v2 seen set (`results/s2_seen_v2/runs/hover`), indi_v2 is 0.044-0.052 on seeds
  1-5; pid_tuned is 0.021-0.031 on seeds 1, 2, 5 and 0.064-0.066 on seeds 3-4 (the seeds flown under host overload,
  s44 finding). The reported v2 ratio 1.26x owes its margin to those two PID seeds; on clean seeds v2 is also ~2x.
- **It is command noise, not body motion** (seed 2, `bench/effort_axes.py`, 15-45 s): body-rate std roll/pitch/yaw
  pid_tuned 0.0046/0.0048/0.0012, v3_tb0.3 0.0054/0.0059/0.0027 rad/s (1.2x on roll/pitch), while torque-setpoint
  std is 2-2.3x on every axis. INDI feeds the filtered angular acceleration and the measured eRPM state into the
  command at their filter bandwidth; PID's D term sees the same angular acceleration but with gain D, not 1/G1.
  The shared filters (`IMU_DGYRO_CUTOFF`) are not INDI-only parameters, so lowering them would change PID too.
