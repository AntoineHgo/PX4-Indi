# G1 roll regression with LPF2p(20.0 Hz) on u (S42)

Log `results/stage2_s41/model_long_s2/flight.ulg`, window 52.0-82.0 s since boot (timestamp_sample), dt 1.250 ms, alpha = indi_rate_status.angular_accel_filtered[0], u = torque_sp[0], regressor = LPF2p(lag_tau(u)) delayed k samples, both band-passed 2-10 Hz.

| tau [s] | k | G1 | R^2 |
|---|---|---|---|
| 0.0 | 0 | 107.4 | 0.156 |
| 0.0 | 2 | 128.0 | 0.222 |
| 0.0 | 4 | 147.7 | 0.296 |
| 0.0 | 6 | 166.3 | 0.375 |
| 0.0 | 8 | 183.7 | 0.457 |
| 0.0 | 12 | 213.8 | 0.620 |
| 0.02 | 0 | 279.0 | 0.707 |
| 0.02 | 2 | 291.8 | 0.773 |
| 0.02 | 4 | 302.2 | 0.830 |
| 0.02 | 6 | 310.3 | 0.875 |
| 0.02 | 8 | 316.0 | 0.908 |
| 0.02 | 12 | 320.0 | 0.930 |
| 0.033 | 0 | 377.4 | 0.857 |
| 0.033 | 2 | 385.2 | 0.894 |
| 0.033 | 4 | 390.2 | 0.917 |
| 0.033 | 6 | 392.3 | 0.927 |
| 0.033 | 8 | 391.4 | 0.923 |
| 0.033 | 12 | 380.8 | 0.873 |
| 0.04 | 0 | 427.0 | 0.888 |
| 0.04 | 2 | 432.5 | 0.911 |
| 0.04 | 4 | 434.7 | 0.920 |
| 0.04 | 6 | 433.7 | 0.916 |
| 0.04 | 8 | 429.5 | 0.898 |
| 0.04 | 12 | 411.6 | 0.825 |

Best: tau 0.02, k 12, G1 320.0, R^2 0.930

## Reading (S42, orchestrator)
- T86 (`g1_regression.md`, haiku) regressed the D-filtered `angular_accel_filtered` on an unfiltered u: the LPF2p(20 Hz)
  group delay (~11 ms) appeared as a 17-22 sample "delay" and a falling ratio with frequency. Applying the same filter
  to u (this script) removes most of it. T86's freq-domain and scan tables are superseded by this file.
- G1, tau and delay are still not separable in a 2-10 Hz band: a ridge runs from (tau 0.02, k 12 = 15 ms, G1 320,
  R^2 0.930) through (tau 0.033, k 6 = 7.5 ms, G1 392, R^2 0.927) to (tau 0.04, k 4, G1 435, R^2 0.920).
- With the SDF tau 0.033 and at most 2 samples of delay, G1 = 377-385 (1.18-1.20 x 320), not 1.30 x; with 15 ms of
  unmodelled command latency and tau 0.02, G1 is the default 320. The motor step test (S42 next (c)) fixes tau and
  latency; G1 is then read off this ridge. No second key yet: this is an estimate to plan with, not a result.
- Analytic route (kT 1.5e-6, w_max 2700, arm 0.0795, Ixx 1.40e-3) needs the allocator's roll-row normalisation, not
  read; a full differential (two motors at u 1, two at 0) gives 1242 rad/s^2 physically.
