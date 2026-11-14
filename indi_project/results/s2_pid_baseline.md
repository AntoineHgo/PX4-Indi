# Stage-2 PID defaults baseline on the v2 nominal sim (session 28, 2026-11-14)

Config: `SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05`, PX4 default PID gains, seeds 1-3,
hover at speed 1, step scenarios at speed 4 (D-speed). Runs: `s2_pid_baseline/defaults/`. All 15 runs completed.

| scenario | primary metric | seeds 1-3 | effort motor_rate_rms_per_s |
|---|---|---|---|
| hover | rms_3d_m | 0.0206, 0.0225, 0.0584 | 0.716, 1.143, 0.988 |
| step_roll | roll_rms_deg | 3.2923, 3.3735, 3.3374 | 2.654, 1.959, 2.093 |
| step_pitch | pitch_rms_deg | 3.3641, 3.3495, 3.2974 | 2.232, 1.858, 2.309 |
| step_yaw | yaw_rms_deg | 13.8021, 13.7840, 13.7942 | 2.105, 2.992, 2.577 |
| rate_step_roll | roll_rms_rad_s | 0.3356, 0.3349, 0.3358 | 4.014, 4.256, 4.148 |

## Finding: vibration dominates motor-rate effort

Hover, PID defaults, seed 1, 1000 Hz (`s2_vib_check/`): motor_rate_rms_per_s 0.026 without vibration, 0.080 at
0.25/0.02, 1.171 at 2.0/0.1; the nominal 1.0/0.05 gives 0.72-1.14 (above). v1 PID hover effort was 0.037 (250 Hz, no
vibration). The vibration passes through the PID rate loop (D term on the 1 kHz gyro behind IMU_GYRO_CUTOFF 40 Hz /
IMU_DGYRO_CUTOFF 20 Hz) into the motor commands, so in v2 the effort term of the frozen cost is mostly vibration
throughput. The cost is relative to the PID reference, so it stays usable, but:
- v1 effort numbers do not carry over (as O-2/order step 2 expected);
- INDI's differentiated gyro faces the same vibration: its effort ratio is now a direct test of the owner's concern;
- tracking metrics are unchanged in character (step roll/pitch RMS ~3.3 deg as on the 1000 Hz no-vibration runs of
  `s2_imu_cost/`; yaw and rate-step not compared yet).
Open: decompose the effort by axis (`bench/effort_axes.py`) and check whether a gyro notch (IMU_GYRO_NF0_FRQ) is the
fair answer for both controllers, before the PID tuning check.
