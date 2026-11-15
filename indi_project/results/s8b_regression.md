# Stage-8 task B regression (session 51, 2026-11-15)

Build with `mc_indi_pos_control` (5cc5fcd01f) and MC_INDIP_EN 0 (module not started), pid_tuned hover, v2 sim
(imu 1000 Hz, eRPM drop 0.01, vibration 1.0/0.05), seeds 1-2, idle host. Script `bench/s8b_regression.sh`.
Reference: the four idle re-flights of `results/pid_hover_mode/runs/idle` (same setup, D-hover-spread).

| run | attitude rms (deg) | roll rate rms (rad/s) | pitch rate rms (rad/s) |
|-----|--------------------|-----------------------|------------------------|
| s8b seed 1 | 0.075 | 0.0011 | 0.0015 |
| s8b seed 2 | 0.088 | 0.0026 | 0.0035 |
| idle refs (4 flights) | 0.058-0.159 | 0.0010-0.0065 | 0.0015-0.0091 |

Verdict: PASS. Both flights lie inside the per-flight spread of the reference; the stock chain is unchanged.
