# Stage-8 review finding 1: accelerometer window average (session 52, 2026-11-15)

Fix (firmware commit "average the specific force over the control cycle"): the module is scheduled on every
`sensor_combined` sample and feeds the law the dt-weighted average of all samples since the previous cycle
(boxcar over ~8 ms: near-zero gain at 125 Hz, ~0.02 at 122.5 Hz on top of the 4 ms IMU integration); eRPM mean u
averaged over the same window.

Hover seed 1, v2 sim, pid_tuned inner loops, `indi_pos_v0` params (`bench/s8c_accel_window.sh`):

| run | vibration | attitude rms (deg)* | pos rms 3d (m) | motor rate rms (1/s) | a_f std x/y (m/s^2) |
|---|---|---|---|---|---|
| s8b try 2 (latest sample) | v2 on | 5.47 | 0.210 | 1.87 | ~1.1 |
| s8b vib0 (latest sample) | off | 0.33 | 0.037 | 0.026 | 0.025/0.022 |
| s8c window average | v2 on | 0.25 | 0.024 | 0.10 | 0.065/0.067 |

*attitude metric for INDI POS still suspect (review finding 6, open): use position rms.

The aliasing is removed: with vibration on, the hover is at least as good as the vib-off run with the old input.
The residual a_f noise (0.065) passes into t_c (std 0.054) and gives motor effort 0.10, against pid_tuned per-flight
range 0.022-0.063 (D-hover-spread): the effort criterion stays structurally hard, as the review predicted.
Single flight, diagnostic only, not part of any verdict.
