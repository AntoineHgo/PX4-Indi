# Roll G1 regression, stage2_s42

Log: `indi_flight/results/stage2_s41/model_long_s2/flight.ulg`  
Script: `indi_flight/bench/g1_regress_s42.py`

## Signals and rates

- u = `indi_rate_status.torque_sp[0]` (normalised roll torque command), 800.0 Hz (median dt 1.2500 ms)
- alpha (primary) = `indi_rate_status.angular_accel_filtered[0]`, 800.0 Hz, rad/s^2
- alpha (cross-check) = `vehicle_angular_velocity.xyz_derivative[0]`, 800.0 Hz, linearly interpolated onto the indi_rate_status timestamps
- excitation (cross-check regressor) = `indi_rate_status.inject[0]`

## Window and method

- Window: 52-82 s since boot (absolute timestamp_sample; first indi sample at 21.258 s), N = 23992 samples = 29.99 s.
- inject[0] nonzero in window: 23978/23992 samples. Overall nonzero extent: 52.02-82.02 s since boot.
- Regression: alpha = G1 * BP(u_lag(t - k dt)) + b, BP = zero-phase 2-10 Hz FFT mask on both signals.
- Lag applied to u before the delay and band-pass: exact ZOH, a = exp(-dt/tau). tau = 0 means no lag.

## Main table (alpha = angular_accel_filtered[0], regressor = torque_sp[0])

| tau [s] | k | delay [ms] | G1 | R^2 |
|---|---|---|---|---|
| 0.000 | 0 | 0.00 | 6.4 | 0.0006 |
| 0.000 | 1 | 1.25 | 17.2 | 0.0041 |
| 0.000 | 2 | 2.50 | 28.2 | 0.0109 |
| 0.000 | 3 | 3.75 | 39.2 | 0.0210 |
| 0.000 | 4 | 5.00 | 50.2 | 0.0344 |
| 0.020 | 0 | 0.00 | 182.6 | 0.3051 |
| 0.020 | 1 | 1.25 | 193.8 | 0.3436 |
| 0.020 | 2 | 2.50 | 204.6 | 0.3830 |
| 0.020 | 3 | 3.75 | 215.1 | 0.4232 |
| 0.020 | 4 | 5.00 | 225.2 | 0.4638 |
| 0.033 | 0 | 0.00 | 294.0 | 0.5236 |
| 0.033 | 1 | 1.25 | 304.8 | 0.5627 |
| 0.033 | 2 | 2.50 | 315.0 | 0.6012 |
| 0.033 | 3 | 3.75 | 324.7 | 0.6387 |
| 0.033 | 4 | 5.00 | 333.8 | 0.6750 |

**Best R^2 = 0.6750** at tau = 0.033 s, k = 4 (5.00 ms): **G1 = 333.8**, G1 / 320 = 1.043 (hypothesis 1.30 x 320 = 416).

## Cross-checks (best k per tau, by R^2)

| alpha | regressor | tau [s] | best k | G1 | R^2 |
|---|---|---|---|---|---|
| angular_accel_filtered[0] (indi_rate_status) | torque_sp[0] (u) | 0.000 | 4 | 50.2 | 0.0344 |
| angular_accel_filtered[0] (indi_rate_status) | torque_sp[0] (u) | 0.020 | 4 | 225.2 | 0.4638 |
| angular_accel_filtered[0] (indi_rate_status) | torque_sp[0] (u) | 0.033 | 4 | 333.8 | 0.6750 |
| angular_accel_filtered[0] (indi_rate_status) | inject[0] (excitation) | 0.000 | 4 | 274.2 | 0.1832 |
| angular_accel_filtered[0] (indi_rate_status) | inject[0] (excitation) | 0.020 | 0 | 303.7 | 0.1716 |
| angular_accel_filtered[0] (indi_rate_status) | inject[0] (excitation) | 0.033 | 0 | 275.4 | 0.1071 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | torque_sp[0] (u) | 0.000 | 4 | 50.2 | 0.0344 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | torque_sp[0] (u) | 0.020 | 4 | 225.2 | 0.4638 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | torque_sp[0] (u) | 0.033 | 4 | 333.8 | 0.6750 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | inject[0] (excitation) | 0.000 | 4 | 274.2 | 0.1832 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | inject[0] (excitation) | 0.020 | 0 | 303.6 | 0.1716 |
| xyz_derivative[0] (vehicle_angular_velocity, interpolated) | inject[0] (excitation) | 0.033 | 0 | 275.4 | 0.1071 |

## Delay extension (diagnostic, k = 0..12, alpha = angular_accel_filtered[0], u = torque_sp[0])

| k | delay [ms] | G1 (tau 0.020) | R^2 (tau 0.020) | G1 (tau 0.033) | R^2 (tau 0.033) |
|---|---|---|---|---|---|
| 0 | 0.00 | 182.6 | 0.3051 | 294.0 | 0.5236 |
| 1 | 1.25 | 193.8 | 0.3436 | 304.8 | 0.5627 |
| 2 | 2.50 | 204.6 | 0.3830 | 315.0 | 0.6012 |
| 3 | 3.75 | 215.1 | 0.4232 | 324.7 | 0.6387 |
| 4 | 5.00 | 225.2 | 0.4638 | 333.8 | 0.6750 |
| 5 | 6.25 | 234.8 | 0.5046 | 342.3 | 0.7098 |
| 6 | 7.50 | 244.1 | 0.5451 | 350.1 | 0.7429 |
| 7 | 8.75 | 252.8 | 0.5850 | 357.3 | 0.7739 |
| 8 | 10.00 | 261.1 | 0.6241 | 363.9 | 0.8026 |
| 9 | 11.25 | 268.9 | 0.6620 | 369.8 | 0.8288 |
| 10 | 12.50 | 276.2 | 0.6985 | 374.9 | 0.8522 |
| 11 | 13.75 | 283.0 | 0.7332 | 379.4 | 0.8728 |
| 12 | 15.00 | 289.2 | 0.7658 | 383.2 | 0.8903 |

## Frequency-domain estimate (alpha = angular_accel_filtered[0], u = torque_sp[0])

Ratio |FFT(alpha)| / |FFT(u_lag)| at the strongest local peaks of |FFT(u)| in 2-20 Hz, rectangular window over the full window (bin width 0.0333 Hz). k = best R^2 for that tau.

| tau [s] | k | median ratio (G1) | peak frequencies [Hz] | ratios |
|---|---|---|---|---|
| 0.000 | 4 | 247.4 | 3.201, 4.001, 5.002, 5.835, 6.302, 7.903, 10.003, 12.604, 15.805, 16.972 | 371.8, 336.7, 288.6, 256.5, 238.4, 202.7, 153.7, 125.4, 111.0, 341.8 |
| 0.020 | 4 | 311.7 | 3.201, 4.001, 5.002, 5.835, 6.302, 7.903, 10.003, 12.604, 15.805, 16.972 | 403.6, 374.1, 342.5, 320.5, 302.9, 286.3, 247.7, 232.3, 247.3, 806.0 |
| 0.033 | 4 | 398.2 | 3.201, 4.001, 5.002, 5.835, 6.302, 7.903, 10.003, 12.604, 15.805, 16.972 | 449.5, 434.2, 417.8, 405.7, 390.8, 390.0, 355.1, 347.0, 381.0, 1251.8 |

## Diagnostic: joint tau x k grid (beyond the spec)

Tests whether the k=4 best in the main table is an interior optimum. If the best k sits at 24, or G1 keeps rising with k, G1 is not identified by this regression alone.

| tau [s] | best k (0..24) | G1 at best k | best R^2 | G1, R^2 at k=0 | G1, R^2 at k=12 |
|---|---|---|---|---|---|
| 0.000 | 24 | 229.5 | 0.7213 | 6.4, 0.0006 | 134.7, 0.2480 |
| 0.020 | 22 | 318.9 | 0.9317 | 182.6, 0.3051 | 289.2, 0.7658 |
| 0.033 | 17 | 391.1 | 0.9276 | 294.0, 0.5236 | 383.2, 0.8903 |
| 0.050 | 12 | 495.7 | 0.9081 | 427.8, 0.6761 | 495.7, 0.9081 |
| 0.070 | 9 | 623.2 | 0.8804 | 574.6, 0.7481 | 619.5, 0.8701 |
| 0.100 | 7 | 818.3 | 0.8451 | 785.0, 0.7775 | 798.6, 0.8050 |

## UNVERIFIED

- The tau = 0.033 s and 0.020 s lag values come from the task brief; not checked against the sim model or firmware parameters.
- torque_sp[0] assumed to be the exact plant input. Not checked against actuator_motors, mixer or ESC dynamics.
- torque_sp includes the INDI feedback part as well as the injection, so it is correlated with alpha. The inject[0] regressor cross-check is the excitation-only alternative; the two disagree (see table), and the feedback-correlated fit is not verified to be unbiased.
- angular_accel_filtered[0] has an unknown internal filter and delay. Its G1 and k may differ from the true plant. The xyz_derivative[0] cross-check is NOT independent: corr 0.99999999, max abs diff 0.21 rad/s^2 vs window RMS 13.9 rad/s^2, so the two alpha rows are the same signal.
- Units: G1 = (rad/s^2) per normalised torque unit. Comparing it to the firmware default 320 assumes the same units and definition. Not checked against the INDI code.
- '52-82 s after boot' is taken as the absolute indi_rate_status timestamp_sample in s. It matches the inject[0] extent; the ULog boot time itself is not checked.
- The 2-10 Hz band-pass is a brick-wall FFT mask over a rectangular 30 s window (no taper). Edge and leakage effects are not quantified.
- The intercept b absorbs any residual offset; not checked for steady-state torque bias.
- Frequency-domain peaks assume the injection periods are commensurate with the window. Non-integer periods leak into neighbouring bins and bias the ratio.
- Closed loop: the slow loop is removed by band-pass, not modelled. Feedback inside 2-10 Hz is not separated from the injection beyond the inject[0] cross-check.
- G1 is confounded with the (tau, k) lag/delay pair. The joint grid ridge gives G1 from about 320 to 820 at R^2 0.85-0.93. Fitted delays of 20-28 ms at the ridge top are not physical for a motor lag, so the extra delay may absorb an unmodelled filter lag in angular_accel_filtered or feedback correlation. Not resolved here.
- The 1.30 x 320 hypothesis is only compared numerically; no firmware or sim truth value was checked.
