# Second-key check: groundtruth timing and frame (A-12 fix, hover_s4)

Log: `/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a12_fix_s18/hover_s4/flight.ulg`

Topics missing from log: none

First armed vehicle_status sample (arming_state == 2): log t = 30.016250 s. vehicle_status samples: 150; samples not armed after first arm: 2 (log t=100.468 s (arming_state 1), log t=100.968 s (arming_state 1)).

## 1-3. Rate, gaps, monotonicity per groundtruth topic

### vehicle_local_position_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 49631. First t=30.020000 s, last t=101.466250 s, duration 71.446 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 49631 | 694.65 | 800.00 | 5.000 | 37.156 (+7.140) | 0 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 1.250 ms. dt histogram (top 6 values): 1.250 ms x42108, 2.500 ms x7518, 3.750 ms x3, 5.000 ms x1.
Gaps > 1.5 x median dt (1.875 ms): 7522 (armed at end: 7396, disarmed at end: 126; max 5.000 ms at log t=37.156 s).

No gaps > 5 ms.

### vehicle_attitude_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 7146. First t=30.020000 s, last t=101.461250 s, duration 71.441 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 7146 | 100.01 | 100.00 | 12.500 | 66.593 (+36.576) | 7144 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 10.000 ms. dt histogram (top 6 values): 10.000 ms x5267, 8.750 ms x939, 11.250 ms x937, 12.500 ms x1, 1.250 ms x1.
Gaps > 1.5 x median dt (15.000 ms): 0.

Gaps > 5 ms: 7144 total. Ending before arm: 0. Ending while armed: 7044 (on ground, alt < 0.1 m: 757; airborne: 6287; max alt during armed gaps: 5.061 m). Ending after arm while disarmed: 100.

| gap start, log s | gap end, log s | gap (ms) | armed at end | alt at end (m) |
|---|---|---|---|---|
| 30.021 | 30.031 | 10.000 | yes | -0.005 |
| 30.031 | 30.041 | 10.000 | yes | -0.005 |
| 30.041 | 30.050 | 8.750 | yes | -0.005 |
| 30.050 | 30.060 | 10.000 | yes | -0.005 |
| 30.060 | 30.071 | 11.250 | yes | -0.005 |
| 30.071 | 30.081 | 10.000 | yes | -0.005 |
| 30.081 | 30.090 | 8.750 | yes | -0.005 |
| 30.090 | 30.101 | 11.250 | yes | -0.005 |
| 30.101 | 30.111 | 10.000 | yes | -0.005 |
| 30.111 | 30.121 | 10.000 | yes | -0.005 |
| 30.121 | 30.131 | 10.000 | yes | -0.005 |
| 30.131 | 30.141 | 10.000 | yes | -0.005 |
| 30.141 | 30.150 | 8.750 | yes | -0.005 |
| 30.150 | 30.161 | 11.250 | yes | -0.005 |
| 30.161 | 30.171 | 10.000 | yes | -0.005 |
| 30.171 | 30.181 | 10.000 | yes | -0.005 |
| 30.181 | 30.191 | 10.000 | yes | -0.005 |
| 30.191 | 30.201 | 10.000 | yes | -0.005 |
| 30.201 | 30.210 | 8.750 | yes | -0.005 |
| 30.210 | 30.221 | 11.250 | yes | -0.005 |
| 30.221 | 30.231 | 10.000 | yes | -0.005 |
| 30.231 | 30.241 | 10.000 | yes | -0.005 |
| 30.241 | 30.250 | 8.750 | yes | -0.005 |
| 30.250 | 30.261 | 11.250 | yes | -0.005 |
| 30.261 | 30.271 | 10.000 | yes | -0.005 |
| ... 7119 more rows omitted | | | | |

### vehicle_angular_velocity_groundtruth

Instance multi_id=0 (1 instance(s) in log). Samples: 7146. First t=30.020000 s, last t=101.461250 s, duration 71.441 s.
Strictly increasing: yes; duplicate timestamps: 0; backward steps: 0.

| phase | samples | mean rate (Hz) | median rate (Hz) | max gap (ms) | time of max gap, log s (rel. arm s) | gaps > 5 ms |
|---|---|---|---|---|---|---|
| before arm | 0 | n/a | n/a | n/a | n/a | 0 |
| after arm | 7146 | 100.01 | 100.00 | 12.500 | 66.593 (+36.576) | 7144 |

Rates use samples inside each phase; gaps are attributed to the sample that ends them.

Median dt: 10.000 ms. dt histogram (top 6 values): 10.000 ms x5211, 8.750 ms x967, 11.250 ms x965, 12.500 ms x1, 1.250 ms x1.
Gaps > 1.5 x median dt (15.000 ms): 0.

Gaps > 5 ms: 7144 total. Ending before arm: 0. Ending while armed: 7044 (on ground, alt < 0.1 m: 757; airborne: 6287; max alt during armed gaps: 5.061 m). Ending after arm while disarmed: 100.

| gap start, log s | gap end, log s | gap (ms) | armed at end | alt at end (m) |
|---|---|---|---|---|
| 30.021 | 30.031 | 10.000 | yes | -0.005 |
| 30.031 | 30.041 | 10.000 | yes | -0.005 |
| 30.041 | 30.050 | 8.750 | yes | -0.005 |
| 30.050 | 30.060 | 10.000 | yes | -0.005 |
| 30.060 | 30.071 | 11.250 | yes | -0.005 |
| 30.071 | 30.081 | 10.000 | yes | -0.005 |
| 30.081 | 30.090 | 8.750 | yes | -0.005 |
| 30.090 | 30.101 | 11.250 | yes | -0.005 |
| 30.101 | 30.111 | 10.000 | yes | -0.005 |
| 30.111 | 30.121 | 10.000 | yes | -0.005 |
| 30.121 | 30.131 | 10.000 | yes | -0.005 |
| 30.131 | 30.141 | 10.000 | yes | -0.005 |
| 30.141 | 30.150 | 8.750 | yes | -0.005 |
| 30.150 | 30.161 | 11.250 | yes | -0.005 |
| 30.161 | 30.171 | 10.000 | yes | -0.005 |
| 30.171 | 30.181 | 10.000 | yes | -0.005 |
| 30.181 | 30.191 | 10.000 | yes | -0.005 |
| 30.191 | 30.201 | 10.000 | yes | -0.005 |
| 30.201 | 30.210 | 8.750 | yes | -0.005 |
| 30.210 | 30.221 | 11.250 | yes | -0.005 |
| 30.221 | 30.231 | 10.000 | yes | -0.005 |
| 30.231 | 30.241 | 10.000 | yes | -0.005 |
| 30.241 | 30.250 | 8.750 | yes | -0.005 |
| 30.250 | 30.261 | 11.250 | yes | -0.005 |
| 30.261 | 30.271 | 10.000 | yes | -0.005 |
| ... 7119 more rows omitted | | | | |

## 4. Frame sanity: vehicle_local_position (EKF) vs groundtruth position, armed only

Comparison samples (armed, inside groundtruth span): 6262. Groundtruth interpolated (linear) onto EKF timestamps. Residual = EKF - truth.

| axis | mean abs diff (m) | max abs diff (m) | mean residual (m) | rms (m) |
|---|---|---|---|---|
| x | 0.0135 | 0.0385 | 0.0072 | 0.0163 |
| y | 0.0132 | 0.0459 | -0.0061 | 0.0164 |
| z | 0.0376 | 0.1045 | 0.0281 | 0.0464 |

| quantity | mean (m) | max (m) | min (m) |
|---|---|---|---|
| groundtruth z, NED (m) | -4.038 | 0.006 | -5.061 |
| EKF z, NED (m) | -4.010 | 0.102 | -4.995 |
| groundtruth altitude = -z (m) | 4.038 | 5.061 | -0.006 |

Groundtruth z at first armed sample: 0.005 m (NED). Groundtruth z at last armed sample: 0.005 m (NED).

## 5. Time base: groundtruth vs sensor_gyro

sensor_gyro multi_id=0 (1 instance(s)): samples 57146, first 30.011250 s, last 101.457500 s, mean rate 799.8 Hz, median rate 800.0 Hz, strictly increasing: yes.

| topic | first (s) | last (s) | first - gyro first (s) | last - gyro last (s) | share of samples inside gyro span |
|---|---|---|---|---|---|
| vehicle_local_position_groundtruth | 30.020000 | 101.466250 | +0.008750 | +0.008750 | 1.000 |
| vehicle_attitude_groundtruth | 30.020000 | 101.461250 | +0.008750 | +0.003750 | 1.000 |
| vehicle_angular_velocity_groundtruth | 30.020000 | 101.461250 | +0.008750 | +0.003750 | 1.000 |

## Flags

- arm at log t=30.016 s; disarmed samples after arm: 2
- vehicle_local_position_groundtruth: no gaps > 5 ms
- vehicle_attitude_groundtruth: 7144 gaps > 5 ms; 7044 while armed (6287 airborne)
- vehicle_angular_velocity_groundtruth: 7144 gaps > 5 ms; 7044 while armed (6287 airborne)
- EKF-truth max abs z residual while armed: 0.1045 m
- sensor_gyro first t=30.011 s, last t=101.457 s
