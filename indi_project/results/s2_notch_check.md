# Stage-2 gyro notch check (session 29, 2026-11-14)

Question: the v2 nominal vibration (D-vib 1.0/0.05) makes PID motor-rate effort 30x the no-vibration level
(`s2_pid_baseline.md`). Is a gyro notch the fair answer for both controllers?

Effort by axis (`bench/effort_axes.py`, PID defaults hover, v2 nominal, seeds 1-3): roll/pitch torque std
0.0012-0.0020 with sample-to-sample drms ~2x std (high-frequency chatter), yaw torque unchanged (0.0002), no vibration
0.0001. The vibration passes through the roll/pitch rate loop only.

Check: PID defaults + `IMU_GYRO_DNF_EN 1` (ESC-rpm dynamic notch, PX4 defaults HMC 3, MIN 25 Hz; rpm from the AM32 eRPM
model, so with its latency, rounding and 1 % drops), `bench/params/pid_dnf.params`, `bench/s2_notch_cmd.sh`,
runs `s2_notch/`. Cells: primary metric / motor_rate_rms_per_s, seeds 1-3.

| scenario | no notch (`s2_pid_baseline`) | ESC-rpm notch |
|---|---|---|
| hover rms_3d_m | 0.0206/0.716 0.0225/1.143 0.0584/0.988 | 0.0193/0.058 0.0239/0.026 0.0187/0.027 |
| step_roll roll_rms_deg | 3.292/2.654 3.374/1.959 3.337/2.093 | 3.340/0.679 3.345/0.614 3.307/0.624 |
| rate_step_roll roll_rms_rad_s | 0.3356/4.014 0.3349/4.256 0.3358/4.148 | 0.3377/3.437 0.3332/3.766 0.3413/3.448 |

Result: the notch brings hover effort back to the no-vibration level (0.026) and cuts step effort 3x; tracking is
unchanged within the seed spread. Decision D-notch: the ESC-rpm dynamic notch is part of the v2 configuration for
both controllers.
