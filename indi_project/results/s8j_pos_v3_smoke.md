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
