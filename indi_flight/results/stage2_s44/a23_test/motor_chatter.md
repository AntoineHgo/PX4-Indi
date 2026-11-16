# S44 motor-command chatter: a23_test / indi_g1derived

- Log: `results/stage2_s44/a23_test/indi_g1derived/flight.ulg`
- Time base: seconds since boot (topic `timestamp` / 1e6).
- Window: [52.0, 82.0) s since boot.
- Motor command: `actuator_motors.control[0]`.
- Measured proxy: `esc_status.esc[0].esc_rpm`, omega = rpm * 2*pi/60, u_meas = (omega / 2700)^2 (2700 rad/s taken from the task, not verified).

## Logged rates (window)

| topic | samples in window | mean rate Hz (n/30 s) | median-dt rate Hz | median dt ms | max gap ms |
|---|---|---|---|---|---|
| actuator_motors | 23988 | 799.60 | 800.00 | 1.2500 | 8.750 |
| esc_status | 23697 | 789.90 | 800.00 | 1.2500 | 8.750 |
| indi_rate_status | 23987 | 799.57 | 800.00 | 1.2500 | 8.750 |

## 1. actuator_motors control[0]

- Samples in window: 23988; fs (median dt) 800.00 Hz, Nyquist 400.0 Hz.
- mean 0.2494, std 0.2423, min 0, max 0.5144.
- Samples outside [0, 1]: 0.

Histogram, 10 bins over [0, 1]:

| bin | count | fraction |
|---|---|---|
| [0.0, 0.1) | 11413 | 0.4758 |
| [0.1, 0.2) | 304 | 0.01267 |
| [0.2, 0.3) | 559 | 0.0233 |
| [0.3, 0.4) | 297 | 0.01238 |
| [0.4, 0.5) | 7772 | 0.324 |
| [0.5, 0.6) | 3643 | 0.1519 |
| [0.6, 0.7) | 0 | 0 |
| [0.7, 0.8) | 0 | 0 |
| [0.8, 0.9) | 0 | 0 |
| [0.9, 1.0) | 0 | 0 |

Welch PSD (Hann, 4096-sample segments, 50% overlap, 10 segments, linear detrend, uniform grid at 800.00 Hz):
- Dominant frequency (search f >= 0.5 Hz): 45.898 Hz; peak / median over band: 4780.
- Fraction of power above 50 Hz (of f > 0): 0.1615.
- Fraction of power in top 10% of band (f >= 0.9 * Nyquist = 360.0 Hz): 0.006557.

Sample-to-sample behaviour:
- Fraction of consecutive sample pairs where the difference reverses sign: 0.2406 (1.0 = strict alternation every sample).
- Fraction of zero first differences: 0.2019.
- Lag-1 autocorrelation of control[0]: 0.8165.

Run length of consecutive samples with control[0] < 0.005: runs = 1360, mean length = 8.107 samples, median = 8, fraction of runs of length 1 = 0.006618.
- Fraction of window samples with control[0] < 0.005: 0.4596.

## 2. esc_status esc[0] vs command

- esc_status rate: samples in window 23697, median-dt rate 800.00 Hz.
- esc[0].esc_rpm raw: min 7257, max 11614, mean 9495.35, std 872.2; fraction zero 0.
- Unit check: Consistent with mechanical rpm: max omega / 2700 = 0.45. Not proven (pole count not in log). UNVERIFIED.
- omega (rad/s) mean 994.4, std 91.34.

| quantity | mean | std |  samples |
|---|---|---|---|
| control[0] (raw samples, actuator_motors) | 0.2494 | 0.2423 | 23988 |
| u_meas = (omega/2700)^2 (raw samples, esc_status) | 0.1368 | 0.02493 | 23697 |
| control[0] (resampled to esc grid, 800.0 Hz) | 0.2494 | 0.2422 | 24000 |
| u_meas (resampled, same grid) | 0.1368 | 0.02491 | 24000 |

- mean(u_meas) - mean(control[0]) on the resampled grid: -0.1125.
- Cross-correlation (detrended, search +/- 50 ms): max r = 0.8532 at lag -15.00 ms (-12 samples). Positive lag = u_meas lags command.
- Cross-correlation (high-pass residual, moving-average width 100 ms): max r = 0.8458 at lag -15.00 ms (-12 samples).

## 3. indi_rate_status

- Fields (23): angular_accel_filtered[0], angular_accel_filtered[1], angular_accel_filtered[2], fault, inject[0], inject[1], inject[2], measured_torque_in_use, nu[0], nu[1], nu[2], torque_filtered[0], torque_filtered[1], torque_filtered[2], torque_increment[0], torque_increment[1], torque_increment[2], torque_sp[0], torque_sp[1], torque_sp[2], torque_sp_pre_inject[0], torque_sp_pre_inject[1], torque_sp_pre_inject[2]
- Fields naming motors/actuators: none. No rotor-speed or motor-domain measured-u / delta-u field is logged; the fields below are in torque or angular-acceleration units.

| field | mean | std | min | max |
|---|---|---|---|---|
| angular_accel_filtered[0] | -0.002712 | 2.352 | -12.26 | 15.43 |
| angular_accel_filtered[1] | 0.003589 | 1.963 | -11.35 | 8.132 |
| angular_accel_filtered[2] | -0.01012 | 44.07 | -107.5 | 84.85 |
| fault | 0 | 0 | 0 | 0 |
| inject[0] | 0 | 0 | 0 | 0 |
| inject[1] | 0 | 0 | 0 | 0 |
| inject[2] | 0 | 0 | 0 | 0 |
| measured_torque_in_use | 1 | 0 | 1 | 1 |
| nu[0] | -0.01214 | 0.9376 | -5.796 | 5.382 |
| nu[1] | 0.001191 | 0.7629 | -3.822 | 5.209 |
| nu[2] | 0.006918 | 4.354 | -11.19 | 13.14 |
| torque_filtered[0] | 5.772e-07 | 0.001338 | -0.006755 | 0.008933 |
| torque_filtered[1] | 2.968e-06 | 0.001196 | -0.006859 | 0.004938 |
| torque_filtered[2] | -3.243e-05 | 0.006539 | -0.02042 | 0.01985 |
| torque_increment[0] | -5.368e-06 | 0.001597 | -0.01053 | 0.008341 |
| torque_increment[1] | -1.499e-06 | 0.001461 | -0.006202 | 0.009618 |
| torque_increment[2] | 6.811e-05 | 0.8952 | -1 | 1 |
| torque_sp[0] | -4.791e-06 | 0.0005076 | -0.003192 | 0.002955 |
| torque_sp[1] | 1.469e-06 | 0.0005117 | -0.002474 | 0.003446 |
| torque_sp[2] | 6.442e-05 | 0.8954 | -1 | 1 |
| torque_sp_pre_inject[0] | -4.791e-06 | 0.0005076 | -0.003192 | 0.002955 |
| torque_sp_pre_inject[1] | 1.469e-06 | 0.0005117 | -0.002474 | 0.003446 |
| torque_sp_pre_inject[2] | 6.442e-05 | 0.8954 | -1 | 1 |

## Notes

- No topic in the log carries true rotor speed; esc_status is the only speed source.
- esc_rpm unit (mechanical vs electrical) and the 2700 rad/s scale are UNVERIFIED.
- Resolution of the lag estimate is one sample (about 1.3 ms at the esc rate).
