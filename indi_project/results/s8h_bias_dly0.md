# s8h: F3 accel-bias fix and MC_INDIP_DLY 0, regression check (session 53, 2026-11-15)

Script `bench/s8h_bias_dly0.sh` (build 41326ec474, v2 sim with vibration, INDI POS `indi_pos_v0` params, seed 1).

| flight | DLY | attitude rms (deg) | pos rms 3D (m) | effort | roll-rate std (rad/s) | roll-rate peak | power share 2-3.2 Hz |
|---|---|---|---|---|---|---|---|
| s8c_accel_window/hover (before F3) | 1 | 0.25 | 0.024 | - | 0.026 | 2.59 Hz | 0.99 |
| s8e_qd_metric/hover (before F3) | 1 | 0.15 | 0.023 | 0.044 | 0.008 | 2.58 Hz | 0.74 |
| s8h hover | 0 | 0.70 | 0.025 | 0.142 | 0.035 | 2.59 Hz | 0.99 |
| s8h hover_dly1 (A/B) | 1 | 0.69 | 0.022 | 0.137 | 0.035 | 2.59 Hz | 0.98 |
| s8h diag_z_multisine | 0 | 0.45 | traj 0.058 | - | - | - | - |

Reading: the higher hover attitude and effort numbers are NOT caused by F3 or DLY 0. DLY 1 and DLY 0 give the
same result, and the EKF accel bias that F3 subtracts is tiny (mean <= 0.009, std <= 0.003 m/s^2, 1 Hz). In every
flight almost all the roll-rate power sits at 2.59 Hz: the lightly damped mode of the pid_tuned rate loop that
`indi_pos_v0` runs underneath (its params are the pid_tuned rate and attitude gains). That mode's amplitude varies
from flight to flight (D-hover-spread), and s8e was a quiet flight of it. Position holds at 0.022-0.025 m in all of
them. Consequence for stage 8: hover metrics of INDI POS on the PID inner loop measure that mode, not the outer law;
arm D of the stage-8 comparison must run on the indi_v3 rate loop as the spec says (plan/s8_impl_spec.md sec. 5).

Lag re-check with DLY 0 on diag_z_multisine: z whitened peak -0.40 cycle, corr 1.00 (DLY 1 flight: +0.71). This
confirms D-s8-delay-final. In hover the z cross-correlation now peaks at -3 cycles with corr 0.97. That is the same
2.59 Hz oscillation coupling into thrust, not a measurement lag.
