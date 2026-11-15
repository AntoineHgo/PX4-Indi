# Stage-8 arm D smoke: indi_pos_v3 on seen entries (session 54, 2026-11-15)

`bench/s8j_pos_v3_smoke.sh`, v2 sim with vibration, seed 1, speed 1. Seen entries only (T5 lemniscate, T1 hover): no
O-set entry was flown. Not a verdict.

| run | traj rms 3D (m) | max dev (m) | attitude rms (deg) | motor rate rms (1/s) | saturation |
|---|---|---|---|---|---|
| T5 pid_tuned (stock pipeline) | 0.38 | 1.17 | 7.2 | 0.59 | 0 |
| T5 indi_pos_v3 | 0.64 | 1.72 | 3.2 (vs q_d) | 1.44 | 0 |
| T1 hover indi_pos_v3 | - (pos rms 0.023 m) | - | 0.36 | 0.109 | 0 |

Hover effort 0.109 is below the pid_tuned hover distribution (about 0.14, D-hover-spread), so criterion 4 is not
at risk. On T5, INDI POS is 1.7x worse in tracking at 2.4x the effort.
Error decomposition (`trajectory_setpoint` vs local position where |v_ref| > 1 m/s; logged setpoint rate is low, n ~ 92):
INDI POS along-track +0.25 m mean (it runs AHEAD of the reference, median lead 66 ms), cross-track rms 0.31 m;
pid_tuned along-track -0.07 m (24 ms lag), cross-track 0.21 m. A lead points at the feedforward path (a_ref and the
differenced jerk). The jerk difference itself is a backward difference and should lag, so the cause is not yet
identified. Next test: arm C (MC_INDIP_FF 0) on T5 seed 1, `bench/s8j2_pos_v3_ff0.sh` ->
`s8j_pos_v3_smoke/traj_lemniscate/indi_pos_v3_ff0/seed1`.

## Arm C (MC_INDIP_FF 0) on T5 seed 1 (`bench/s8j2_pos_v3_ff0.sh`)

| run | traj rms 3D (m) | max dev (m) | attitude rms (deg) | motor rate rms (1/s) | along-track mean (m) | cross-track rms (m) |
|---|---|---|---|---|---|---|
| pid_tuned | 0.38 | 1.17 | 7.2 | 0.59 | -0.07 (24 ms lag) | 0.21 |
| indi_pos_v3 (D) | 0.64 | 1.72 | 3.2 | 1.44 | +0.25 (66 ms lead) | 0.31 |
| indi_pos_v3_ff0 (C) | 0.76 | 1.87 | 9.3 | 0.64 | +0.31 (94 ms lead) | 0.41 |

Findings (one seed, to confirm):
1. The 2.4x effort of D comes from the feedforward path: with FF off, effort drops to PID's level (0.64 vs 0.59). The
   prime suspect is the jerk obtained by differencing a step-wise a_ref from the offboard stream (spikes clamped at
   kMaxJerk, fed straight into omega_ff). Candidates: the runner sends the analytic jerk in `trajectory_setpoint.jerk`
   (the path is known in closed form; under O-9 the flatness terms are part of the INDI design), or the difference is
   low-pass filtered. Check `indi_pos_status.jerk_source` and the raw j_ref first.
2. The lead is NOT caused by the feedforward: it persists, and grows, with FF off. A feedback loop tracking a moving
   reference without anticipation should lag, so either the reference the module uses is ahead of the logged
   `trajectory_setpoint` (timestamp or ordering), or the along-track error alternates sign with the path phase
   (overshoot after the curvature peaks, a damping problem) and the mean is misleading. Next: plot the along-track
   error against path phase for D and C, compare the module's p_ref (if `IndiPosStatus` logs it) with the logged
   setpoint, and compare the MC_INDIP position/velocity gains with pid_tuned's MPC_XY_P / MPC_XY_VEL_* gains.
No gain change before these causes are found.

## Session 55: cause of the lead and of the effort (`bench/s8_track_diag.py`, analytic reference)

Reference rebuilt from run.json at every local position sample (not the 5 Hz logged setpoint), cruise |v_ref| > 1 m/s.
x runs at the lemniscate phase rate w = 0.88 rad/s, y at 2w = 1.77 rad/s.

| run | along mean (m) | x shift (ms, + = ahead) / gain | y shift / gain | a_f vs a_c (x, y) | a_c vs a_ref (x, y) |
|---|---|---|---|---|---|
| pid_tuned | -0.08 | -40 / 0.99 | -20 / 1.09 | - | - |
| indi_pos_v3 (D) | +0.29 | +30 / 0.93 | +160 / 1.00 | -20 ms 0.92, -20 ms 1.07 | -110 ms 0.91, +80 ms 0.85 |
| indi_pos_v3_ff0 (C) | +0.34 | +90 / 0.98 | +90 / 1.29 | -220 ms 0.96, -200 ms 0.97 | +200 ms 0.96, +180 ms 1.24 |

1. **The setpoint stream is on time**: the logged `trajectory_setpoint` equals the analytic path delayed by 2 ms (residual
   2.5 mm) in all three runs. The lead is not a timing artefact of the reference.
2. **The lead is the closed-loop response of the outer law, not an error in the feedforward**. With a = D(s) a_c,
   a_c = a_ref + K_v (v_ref - v) + K_v K_p (p_ref - p) and a first-order inner lag D = 1/(1 + tau s):
   p/r = (s^2 + K_v s + K) / (tau s^3 + s^2 + K_v s + K), K = K_v K_p, so that at low frequency
   p/r ~ 1 / (1 - j tau w^3 / K): a PHASE LEAD of about tau w^2 / K seconds. An inner lag together with the full a_ref
   feedforward makes the vehicle run ahead. Arm C (no jerk FF) has tau ~ 0.2 s (a_f lags a_c by 200-220 ms): the formula
   gives ~90 ms at the x frequency (K ~ 1.7 from the stock MPC gains), as measured (+90 ms). The jerk FF shrinks the
   inner lag to ~20 ms (arm D), but D still leads on y (+160 ms) with a 7 % amplitude overshoot of a_f against a_c on
   y: the first-order formula does not account for it fully (not resolved; inner-loop gain and the a_f filter phase
   are candidates). pid_tuned has the same structure but lags: it does not compensate rotor drag (~0.12 m/s^2 per
   m/s, `s8_drag_check.md`), which adds a lag of order drag / K ~ 70 ms; INDI measures and cancels the drag.
3. **The effort of D comes from the differenced jerk being a staircase**: `omega_ff` has the analytic magnitude
   (rms 0.19 / 0.78 rad/s against |j|/g 0.19 / 0.81), but its sample-to-sample change (0.12 rad/s rms on the large
   axis per 8 ms) is ~7x that of the smooth signal: the 50 Hz offboard stream holds the difference for 20 ms at a
   125 Hz loop, and the steps go straight into the rate setpoint (the motor-rate metric is a derivative, so steps
   dominate it). Fix b9fb3ce5a9: the differenced jerk is low-pass filtered at MC_INDIP_LPF_CUT. A jerk field in the
   setpoint is not possible over MAVLink offboard (SET_POSITION_TARGET_LOCAL_NED has no jerk), so the runner cannot
   supply the analytic jerk without a custom path; filtering is the fair option (D-s8-jerk-lpf).
Test: arm D' = indi_pos_v3 after b9fb3ce5a9, T5 seed 1 (`bench/s8j3_pos_v3_jlpf.sh` ->
`s8j_pos_v3_smoke/traj_lemniscate/indi_pos_v3_jlpf/seed1`).

### Arm D' result (T5 seed 1, firmware b9fb3ce5a9, clean tree)

| run | traj rms 3D (m) | vertical rms (m) | max dev (m) | attitude rms (deg) | motor rate rms (1/s) | along mean (m) | y shift (ms) |
|---|---|---|---|---|---|---|---|
| pid_tuned | 0.38 | 0.030 | 1.17 | 7.2 | 0.59 | -0.08 | -20 |
| D (raw difference) | 0.64 | 0.027 | 1.72 | 3.2 | 1.44 | +0.29 | +160 |
| D' (filtered difference) | 0.65 | 0.011 | 1.78 | 3.3 | 0.65 (1.10x) | +0.31 | +160 |

The jerk filter removes the excess effort (1.44 -> 0.65, now 1.10x pid_tuned) at unchanged horizontal tracking, and the
vertical error drops by 2.5x. The effort cause is confirmed. The lead (+0.3 m along-track, +160 ms on y) is
unchanged, so it has a different cause; it now dominates the gap to pid_tuned (0.65 vs 0.38 m). Open candidates:
(i) the 8 % a_f-over-a_c overshoot on y (inner gain not flat in frequency; x 0.92, y 1.08); (ii) an EKF position
delay in the feedback path, which acts like an inner lag in the same formula (the law uses raw accel but EKF
position), checked against ground truth (`vehicle_local_position_groundtruth`) if it is logged; (iii) the
stock MPC outer gains (K = K_v K_p ~ 1.7) are low for a loop whose lead scales as tau w^2 / K. The INDI POS params file
can set MPC_XY_P / MPC_XY_VEL_P_ACC for INDI runs only, without touching pid_tuned's params, so (iii) can be screened
without new firmware parameters.

### EKF against ground truth (session 55, inline check, T5 seed 1, cruise window, per-axis shift/gain vs analytic path)

| run | EKF x | EKF y | ground truth x | ground truth y |
|---|---|---|---|---|
| pid_tuned | -40 ms, 0.99 | -20 ms, 1.11 | -150 ms, 0.96 | -120 ms, 1.02 |
| D' (indi_pos_v3_jlpf) | +20 ms, 0.92 | +160 ms, 1.02 | -90 ms, 0.89 | +70 ms, 0.93 |

(ground truth: mean offset over the window removed, 0.02-0.12 m.) For BOTH controllers the EKF position runs ~90-110 ms
AHEAD of `vehicle_local_position_groundtruth`. The gap between the controllers is the same in both frames (INDI 60-180 ms
ahead of PID). In ground truth, pid_tuned LAGS by 120-150 ms, and INDI POS is closer to in phase. UNVERIFIED and
load-bearing for the metric: it is either a real estimator timing error (the EKF output predictor running ahead of the
truth), or a timestamping delay of the groundtruth topic in the gz bridge. metrics.py scores tracking on the EKF
estimate, which is what a real vehicle would see. If the estimator really leads the truth, the EKF-based score
favours the controller that lags in truth. Check before the set-O verdict: (a) how gz_bridge stamps groundtruth
(sim time of the pose vs hrt at publish); (b) EKF vs ground-truth velocity cross-correlation on a hover step; (c) report
both frames in the verdict if the offset is real.
Lead on (a): `GZBridge::poseInfoCallback` stamps `vehicle_local_position_groundtruth` with `hrt_absolute_time()` at
message RECEPTION, not with the pose's own `header().stamp()`; velocity and acceleration are finite differences over
the reception intervals. If gz delivers pose_info after the lockstep clock has moved on, ground truth is stamped late,
and the EKF appears to "lead" it. That is the more likely explanation (an EKF running 100 ms ahead of the truth would
be unusual). Not yet proven: compare the header stamp with hrt in the bridge (debug print, no commit), or
cross-correlate gt velocity with velocity integrated from the IMU over a fast manoeuvre. Until then, the EKF-frame
metric stands, and the ground-truth phase numbers above are not used.

## Session 56 correction

Superseded by `results/s8k_gnss_delay.md` (D-s8-gnss-delay): the EKF-vs-ground-truth offset is not a gz_bridge stamping
artefact. It comes from SENS_GNSS0_DELAY 110 ms applied to the zero-latency simulated GNSS. With the delay set to 0, the INDI
POS lead disappears (T5 0.649 -> 0.262 m; pid_tuned 0.383 m). The cascade-phase explanation above is not the main
cause of the arm-D/D' gap. The ground-truth phase numbers above were measured under the mismatched delay.
