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
disturbance-rejection margins measured here are likely optimistic for real flight (not tested).

## Stage-2 additions (session 27)

- `--sim v2true`: esc_rpm = rotor joint speed x 10 (true motor speed of the plant, first-order up 0.0125 s / down
  0.025 s), via JointStatePublisher + `SIM_GZ_ESC_FB=1` (D-escfb).
- `--sim v2`: the same speed through the eRPM model (`SIM_GZ_ESC_FB=2`, D-erpm): one output period latency (250 Hz:
  4 ms), AM32 period encoding, PX4 100-eRPM rounding, 14 poles, drop probability `--erpm-drop` (held value).
  Not modelled: ESC measurement age within a frame (AM32 rebuilds the reply once per frame from a period averaged
  over one electrical revolution, ~1.2 ms at hover), turnaround (no constant in AM32 source), offline after 200
  consecutive drops. IMU rate and vibration are still the v1 values (next step).
