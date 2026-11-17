# S64 outlier vs S67 normal repeat: step_roll_indi

Outlier: `g2_step_s64_400/steps_seed1/step_roll_indi` (rise 188.7 ms, settle 312.5 ms, overshoot 1.78 %)
Normal: `g16_indi_s67/s4_r1/step_roll_indi` (202.7 ms, 356.25 ms, 0.65 %)

## 1. run.json diff

Same: params, seeds, scenario, speed, rate, physics_step_s, exit_status, step schedule, params file hash.

Differing keys:
- `git.commit`: outlier f183dad4d28 (dirty: true) vs normal 361ae4fcbc (dirty: false)
- timing (sim-time and wall-time, expected run-to-run noise): `t_before_arm_wait_s` 18.556 vs 19.377, `t_arm_sent_s`, `t_arm_us`, `t_climb_done_s` 39.715 vs 40.408, `t_hold_s`, `t_offboard_sent_s`, `t_offboard_us`, `t_window_start_us`, `t_window_end_us`, every `t_us` in the step list, `wall_time_s` 44.3 vs 35.0
- hold state: `hold_pos` x -0.0451 / 0.0801, y 0.0157 / -0.0377, z -5.0513 / -4.9517; `hold_yaw_rad` 1.5852 / 1.5910; `hover_thrust_estimate` 0.13667 / 0.13668

## 2. PX4 parameters in the ULogs

1191 initial parameters per log, 0 differences.

## 3. Flight-level comparison (ULog)

- Hover throttle before step (motors 30-38 s): 0.1366 on all four motors in both runs.
- Battery voltage: 16.8 V at start and end in both runs.
- Roll step: peak rate setpoint -1.778 rad/s (outlier) vs -1.755 rad/s (normal), about 1.3 % larger.
- Hover altitude 45-52 s: z mean -5.124 m (outlier) vs -5.018 m (normal).
- sends.csv: identical command content order; outlier has 845 non-param rows vs 831 (stream counts depend on wall-clock pacing). The first send_pos carries the hold point above (z -5.0513 vs -4.9517).
- PX4 source: `git diff f183dad 361ae4f -- src ROMFS boards msg` is empty, so the firmware sources match. The outlier's build was dirty, so the binary cannot be proven identical from git alone.

## Verdict

Not found as a parameter or config difference. The parameter set (1191 values), hover throttle, battery and step command are identical or within 1.3 %. The candidate is the state at the step start: the outlier hovered about 0.1 m off in x/z and at a different hold yaw, and its step peak is about 1.3 % larger. The dirty build at f183dad is the other unverified difference. Not confirmed as cause.
