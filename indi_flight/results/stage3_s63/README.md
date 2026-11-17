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
4. The 9-13 deg |est - sp| in the last bin of seed3 roll/pitch and seed2 pitch is the return step: roll/pitch hold
   3.0 s (`bench/scenarios.py` step_roll), the 3.0 s metric window starts 13-23 ms late. CORRECTION (same session,
   T127 key re-run with the G2-STEP window, which ends 50 ms before the return step): the T127 'seed3 roll truth exits
   the band at 2.96 s' is NOT the return step; truth settle stays 2937 ms with the new window. Truth sits at the band
   edge: est - truth -0.21 deg plus an in-band dip of the controlled estimate from 2.8 s (est - 15 deg down to -0.14 deg,
   2.8-2.95 s), truth - 15 deg reaching -0.30 deg. Dip cause not identified: A-29 (parked, bound 0.15 deg).
   Truth settle is reported, not a pass condition, under the S63 definition; est settle 349 ms.

Consequence: G2-STEP measurement definition written in GATES.md (t_on on the setpoint crossing, window ends 50 ms
before the return step, pass metrics on the estimate as written S61, truth overshoot also a pass condition,
estimator error reported apart). A-28 closed. The primary metric script (`results/indi_vs_pid/plot_compare.py`)
and the T127 key must both adopt that window before the first G2-STEP test.
