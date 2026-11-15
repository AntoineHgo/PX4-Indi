# Second-key check: groundtruth timing and frame (A-12 fix, hover_s4)

Log: `results/a12_fix_s18/pretest_truth_topics/hover/flight.ulg`

Topics missing from log: none

First armed vehicle_status sample (arming_state == 2): log t = 30.015000 s. vehicle_status samples: 156; samples not armed after first arm: 2 (log t=103.736 s (arming_state 1), log t=104.236 s (arming_state 1)).

## 1-3. Rate, gaps, monotonicity per groundtruth topic

### vehicle_local_position_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 51936. First t=30.018750 s, last t=104.720000 s, duration 74.701 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 51936 | 695.24 | 800.00 | 3.750 | 31.503 (+1.488) | 0 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 1.250 ms. dt histogram (top 6 values): 1.250 ms x44115, 2.500 ms x7814, 3.750 ms x6.
Gaps > 1.5 x median dt (1.875 ms): 7820 (armed at end: 7691, disarmed at end: 129; max 3.750 ms at log t=31.503 s).

No gaps > 5 ms.

### vehicle_attitude_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 52073. First t=30.018750 s, last t=104.720000 s, duration 74.701 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 52073 | 697.07 | 800.00 | 3.750 | 31.503 (+1.488) | 0 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 1.250 ms. dt histogram (top 6 values): 1.250 ms x44389, 2.500 ms x7677, 3.750 ms x6.
Gaps > 1.5 x median dt (1.875 ms): 7683 (armed at end: 7554, disarmed at end: 129; max 3.750 ms at log t=31.503 s).

No gaps > 5 ms.

### vehicle_angular_velocity_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 51899. First t=30.018750 s, last t=104.720000 s, duration 74.701 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 51899 | 694.74 | 800.00 | 3.750 | 31.503 (+1.488) | 0 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 1.250 ms. dt histogram (top 6 values): 1.250 ms x44041, 2.500 ms x7851, 3.750 ms x6.
Gaps > 1.5 x median dt (1.875 ms): 7857 (armed at end: 7728, disarmed at end: 129; max 3.750 ms at log t=31.503 s).

No gaps > 5 ms.

## 4. Frame sanity: vehicle_local_position (EKF) vs groundtruth position, armed only

Comparison samples (armed, inside groundtruth span): 6553. Groundtruth interpolated (linear) onto EKF timestamps. Residual = EKF - truth.

| axis | mean abs diff (m) | max abs diff (m) | mean residual (m) | rms (m) |
|---|---|---|---|---|
| x | 0.0120 | 0.0393 | -0.0005 | 0.0148 |
| y | 0.0147 | 0.0563 | -0.0101 | 0.0181 |
| z | 0.1687 | 2.2176 | -0.1417 | 0.4812 |

| quantity | mean (m) | max (m) | min (m) |
|---|---|---|---|
| groundtruth z, NED (m) | -5.728 | 0.005 | -7.262 |
| EKF z, NED (m) | -5.870 | 0.075 | -7.258 |
| groundtruth altitude = -z (m) | 5.728 | 7.262 | -0.005 |

Groundtruth z at first armed sample: 0.005 m (NED). Groundtruth z at last armed sample: 0.005 m (NED).

## 5. Time base: groundtruth vs sensor_gyro

sensor_gyro multi_id=0 (1 instance(s)): samples 59753, first 30.010000 s, last 104.712500 s, mean rate 799.9 Hz, median rate 800.0 Hz, strictly increasing: yes.

| topic | first (s) | last (s) | first - gyro first (s) | last - gyro last (s) | share of samples inside gyro span |
|---|---|---|---|---|---|
| vehicle_local_position_groundtruth | 30.018750 | 104.720000 | +0.008750 | +0.007500 | 1.000 |
| vehicle_attitude_groundtruth | 30.018750 | 104.720000 | +0.008750 | +0.007500 | 1.000 |
| vehicle_angular_velocity_groundtruth | 30.018750 | 104.720000 | +0.008750 | +0.007500 | 1.000 |

## Flags

- arm at log t=30.015 s; disarmed samples after arm: 2
- vehicle_local_position_groundtruth: no gaps > 5 ms
- vehicle_attitude_groundtruth: no gaps > 5 ms
- vehicle_angular_velocity_groundtruth: no gaps > 5 ms
- EKF-truth max abs z residual while armed: 2.2176 m
- sensor_gyro first t=30.010 s, last t=104.713 s
