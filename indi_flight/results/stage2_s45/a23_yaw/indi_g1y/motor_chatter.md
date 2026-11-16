# S44 motor-command chatter: a23_test / indi_g1derived

- Log: `indi_flight/results/stage2_s45/a23_yaw/indi_g1y/flight.ulg`
- Time base: seconds since boot (topic `timestamp` / 1e6).
- Window: [52.0, 82.0) s since boot.
- Motor command: `actuator_motors.control[0]`.
- Measured proxy: `esc_status.esc[0].esc_rpm`, omega = rpm * 2*pi/60, u_meas = (omega / 2700)^2 (2700 rad/s taken from the task, not verified).

## Logged rates (window)

| topic | samples in window | mean rate Hz (n/30 s) | median-dt rate Hz | median dt ms | max gap ms |
|---|---|---|---|---|---|
| actuator_motors | 23999 | 799.97 | 800.00 | 1.2500 | 2.500 |
| esc_status | 23671 | 789.03 | 800.00 | 1.2500 | 3.750 |
| indi_rate_status | 23999 | 799.97 | 800.00 | 1.2500 | 2.500 |

## 1. actuator_motors control[0]

- Samples in window: 23999; fs (median dt) 800.00 Hz, Nyquist 400.0 Hz.
- mean 0.1367, std 0.0008525, min 0.129, max 0.1451.
- Samples outside [0, 1]: 0.

Histogram, 10 bins over [0, 1]:

| bin | count | fraction |
|---|---|---|
| [0.0, 0.1) | 0 | 0 |
| [0.1, 0.2) | 23999 | 1 |
| [0.2, 0.3) | 0 | 0 |
| [0.3, 0.4) | 0 | 0 |
| [0.4, 0.5) | 0 | 0 |
| [0.5, 0.6) | 0 | 0 |
| [0.6, 0.7) | 0 | 0 |
| [0.7, 0.8) | 0 | 0 |
| [0.8, 0.9) | 0 | 0 |
| [0.9, 1.0) | 0 | 0 |

Welch PSD (Hann, 4096-sample segments, 50% overlap, 10 segments, linear detrend, uniform grid at 800.00 Hz):
- Dominant frequency (search f >= 0.5 Hz): 45.703 Hz; peak / median over band: 1.049e+05.
- Fraction of power above 50 Hz (of f > 0): 0.03352.
- Fraction of power in top 10% of band (f >= 0.9 * Nyquist = 360.0 Hz): 3.227e-05.

Sample-to-sample behaviour:
- Fraction of consecutive sample pairs where the difference reverses sign: 0.1213 (1.0 = strict alternation every sample).
- Fraction of zero first differences: 0.
- Lag-1 autocorrelation of control[0]: 0.9422.

Run length of consecutive samples with control[0] < 0.005: runs = 0, mean length = nan samples, median = nan, fraction of runs of length 1 = nan.
- Fraction of window samples with control[0] < 0.005: 0.

## 2. esc_status esc[0] vs command

- esc_status rate: samples in window 23671, median-dt rate 800.00 Hz.
- esc[0].esc_rpm raw: min 9500, max 9571, mean 9536.87, std 8.006; fraction zero 0.
- Unit check: Consistent with mechanical rpm: max omega / 2700 = 0.371. Not proven (pole count not in log). UNVERIFIED.
- omega (rad/s) mean 998.7, std 0.8384.

| quantity | mean | std |  samples |
|---|---|---|---|
| control[0] (raw samples, actuator_motors) | 0.1367 | 0.0008525 | 23999 |
| u_meas = (omega/2700)^2 (raw samples, esc_status) | 0.1368 | 0.0002297 | 23671 |
| control[0] (resampled to esc grid, 800.0 Hz) | 0.1367 | 0.0008514 | 24000 |
| u_meas (resampled, same grid) | 0.1368 | 0.0002298 | 24000 |

- mean(u_meas) - mean(control[0]) on the resampled grid: 0.0001534.
- Cross-correlation (detrended, search +/- 50 ms): max r = 0.5122 at lag 7.50 ms (6 samples). Positive lag = u_meas lags command.
- Cross-correlation (high-pass residual, moving-average width 100 ms): max r = 0.6134 at lag 7.50 ms (6 samples).

## 3. indi_rate_status

- Fields (23): angular_accel_filtered[0], angular_accel_filtered[1], angular_accel_filtered[2], fault, inject[0], inject[1], inject[2], measured_torque_in_use, nu[0], nu[1], nu[2], torque_filtered[0], torque_filtered[1], torque_filtered[2], torque_increment[0], torque_increment[1], torque_increment[2], torque_sp[0], torque_sp[1], torque_sp[2], torque_sp_pre_inject[0], torque_sp_pre_inject[1], torque_sp_pre_inject[2]
- Fields naming motors/actuators: none. No rotor-speed or motor-domain measured-u / delta-u field is logged; the fields below are in torque or angular-acceleration units.

| field | mean | std | min | max |
|---|---|---|---|---|
| angular_accel_filtered[0] | -0.0003731 | 0.07615 | -0.4861 | 0.5138 |
| angular_accel_filtered[1] | 0.0006633 | 0.07764 | -0.6115 | 0.5128 |
| angular_accel_filtered[2] | 4.804e-05 | 0.1593 | -1.623 | 1.478 |
| fault | 0 | 0 | 0 | 0 |
| inject[0] | 0 | 0 | 0 | 0 |
| inject[1] | 0 | 0 | 0 | 0 |
| inject[2] | 0 | 0 | 0 | 0 |
| measured_torque_in_use | 1 | 0 | 1 | 1 |
| nu[0] | 0.002317 | 0.09871 | -0.5355 | 0.6036 |
| nu[1] | 0.001238 | 0.102 | -0.5683 | 0.9 |
| nu[2] | 0.0001963 | 0.01595 | -0.139 | 0.1564 |
| torque_filtered[0] | -1.863e-06 | 6.035e-05 | -0.0002948 | 0.0002948 |
| torque_filtered[1] | 1.467e-07 | 6.407e-05 | -0.0005667 | 0.0002948 |
| torque_filtered[2] | 1.016e-06 | 3.49e-05 | -0.0002659 | 0.000286 |
| torque_increment[0] | 1.532e-06 | 5.783e-05 | -0.0003484 | 0.000352 |
| torque_increment[1] | 3.595e-07 | 6.374e-05 | -0.0003528 | 0.0006454 |
| torque_increment[2] | 6.895e-07 | 0.0008056 | -0.00743 | 0.00822 |
| torque_sp[0] | -3.305e-07 | 5.385e-05 | -0.000334 | 0.0005061 |
| torque_sp[1] | 5.063e-07 | 5.947e-05 | -0.0006036 | 0.0005124 |
| torque_sp[2] | 1.706e-06 | 0.0008216 | -0.007625 | 0.008467 |
| torque_sp_pre_inject[0] | -3.305e-07 | 5.385e-05 | -0.000334 | 0.0005061 |
| torque_sp_pre_inject[1] | 5.063e-07 | 5.947e-05 | -0.0006036 | 0.0005124 |
| torque_sp_pre_inject[2] | 1.706e-06 | 0.0008216 | -0.007625 | 0.008467 |

## Notes

- No topic in the log carries true rotor speed; esc_status is the only speed source.
- esc_rpm unit (mechanical vs electrical) and the 2700 rad/s scale are UNVERIFIED.
- Resolution of the lag estimate is one sample (about 1.3 ms at the esc rate).
