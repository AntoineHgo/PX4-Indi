# S63: A-28 closing test (estimator minus truth around attitude steps)

Command (no flight; S62 logs, raw logs untracked):
`python3 bench/a28_offset_course.py results/stage3_s63/a28_course.md results/stage3_s62/steps_seed{1,3}/step_roll_indi results/stage3_s62/steps_seed{3,2}/step_pitch_indi results/stage3_s62/steps_seed2/step_yaw_indi`
and the same with `steps_seed1/step_roll_pid steps_seed2/step_yaw_pid` into `a28_course_pid.md`.
Bins relative to t_on (setpoint 50 % crossing); d = est - truth, e = truth - setpoint.

Findings
1. Roll/pitch, INDI seeds 1-3: d ~ 0 before the step and up to 0.45 s after it, then grows to +0.19-0.21 deg by
   1.0-1.5 s and +0.21-0.24 deg over 1.5-3 s. The controller holds |est - sp| <= 0.06 deg from 1 s on; the truth
   follows the setpoint minus d. Mechanism (not instrumented further): the 15 deg tilt accelerates the vehicle
   sideways in attitude mode and the EKF tilt estimate drifts while it does.
2. PID seed1 roll: same course, d +0.20 / +0.23 deg over 1.0-1.5 / 1.5-3 s. The drift is the estimator's, not INDI's.
3. Yaw: standing bias, INDI seed2 d +0.73 deg before the step, +0.97 deg after; PID seed2 +1.0 / +0.8 deg.
4. The T127 'seed3 roll exits the band at 2.96 s' is the return step: roll/pitch hold 3.0 s
   (`bench/scenarios.py` step_roll), metric window 3.0 s from a t_on that lags the scheduled step by 13-23 ms. Seed3
   roll/pitch and seed2 pitch show |est - sp| of 9-13 deg in the last bin for that reason.

Consequence: G2-STEP measurement definition written in GATES.md (t_on on the setpoint crossing, window ends 50 ms
before the return step, pass metrics on the estimate as written S61, truth overshoot also a pass condition,
estimator error reported apart). A-28 closed. The primary metric script (`results/indi_vs_pid/plot_compare.py`)
and the T127 key must both adopt that window before the first G2-STEP test.
