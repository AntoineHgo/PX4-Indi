# Simulation fidelity of gz_x500 (written session 17, after the benchmark was flown)

`bench/scenarios.md` section 7 asked for this note before the disturbance and held-out scenarios. It was written
late, from the model files, and it changes no result. Every value below was read from the file named, in session 17.

| Item | gz_x500 value | Source | Real-vehicle gap |
|---|---|---|---|
| Motor dynamics | first order, tau 0.0125 s up / 0.025 s down | `Tools/simulation/gz/models/x500/model.sdf` (`timeConstantUp/Down`) | no ESC delay, no voltage sag |
| Thrust / moment constants | k_f 8.54858e-6, k_m/k_f 0.016 | same file | PX4 allocator assumes CA_ROTOR*_KM 0.05 (`4001_gz_x500`): ~3x yaw-moment model error, the same for both controllers |
| Rotor speed feedback | none measured (esc_rpm echoes the command) | report ch. 4 / `plan/px4_analysis_verification.md` | INDI uses its onboard motor model |
| IMU rate | 250 Hz | `Tools/simulation/gz/models/x500_base/model.sdf` `imu_sensor` | real IMUs run 1-8 kHz with anti-aliasing |
| Gyro noise | Gaussian white, std 8.7e-4 rad/s (0.05 deg/s) per axis, no bias, no bias drift | same | no vibration, no bias instability |
| Accel noise | Gaussian white, std 0.00637 m/s^2 (x, y), 0.00686 (z), no bias | same | no vibration-induced noise |
| Baro / mag | baro 50 Hz std 3 Pa; mag 100 Hz std 3e-7 T | same | |
| Disturbances | none in the stock model; gusts, payload and CoM shift added by `bench/disturbance.py` (ApplyLinkWrench) | `bench/scenarios.md` | no rotor-wake or ground effect, no blade flapping |
| Plant mismatch | inertia, mass, motor tau via `bench/model_variant.py` | `plan/t9_model_variant_log.md` | |

Not measured: end-to-end sensor-to-actuator latency in SITL (lockstep makes it one or two control cycles; it is not
characterised against hardware). Consequences for the conclusions are discussed in report ch. 9: a low-noise,
bias-free, vibration-free gyro favours INDI, whose angular-acceleration estimate differentiates the gyro, so the
disturbance-rejection margins measured here are upper bounds for real flight.
