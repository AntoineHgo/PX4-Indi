# K99 second-key check of T207 simulator hooks (raw ULog only)

Inputs: `indi_flight/results/t207_hooks/F1/run/flight.ulg` (seed 1, IMU scale 3, drop 0.1) and `F2/run/flight.ulg` (seed 2, IMU scale 1, drop 0.1). Parsed with pyulog. The script is `/tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/c9ff20b2-e1e1-4e9d-a28b-a9a18b8b2a99/scratchpad/k99_check.py`. The analysis did not use the existing `an.py` or the design log.

Windows: armed = first to last `vehicle_status.arming_state == 2` (F1 30.0-100.2 s, F2 30.0-100.1 s). Airborne = armed and `vehicle_land_detected.landed == 0` (F1 32.0-98.3 s, F2 32.0-98.2 s). Middle 50 % of airborne: F1 48.6-81.7 s, F2 48.6-81.7 s.

Estimators: (a) diff: std(diff(x))/sqrt(2). (b) ma9: std(x - centred 9-sample moving average) * sqrt(9/8), the 9/8 factor correcting for the white-noise variance removed by the MA.

## 1. Gyro (sensor_gyro, instance 0, about 800 Hz, rad/s)

| axis | F1 diff | F1 ma9 | F2 diff | F2 ma9 | ratio diff | ratio ma9 |
|---|---|---|---|---|---|---|
| x | 2.620e-3 | 2.623e-3 | 8.720e-4 | 8.711e-4 | 3.01 | 3.01 |
| y | 2.602e-3 | 2.611e-3 | 8.843e-4 | 8.824e-4 | 2.94 | 2.96 |
| z | 2.626e-3 | 2.628e-3 | 8.698e-4 | 8.722e-4 | 3.02 | 3.01 |

F2 sigma is about 8.7e-4 rad/s, as expected. The two estimators agree to within 0.5 %, so there is no sign of unmodelled low-frequency content in the window.

**Verdict: AGREE.**

## 2. Accel (sensor_accel, instance 0, m/s^2)

The logs only contain `sensor_accel` at about 1 Hz (81 samples per flight, 33-34 in the middle window). There is no `sensor_accel_fifo` topic in either log, so a high-rate white-noise estimate is not possible from these files. At 1 Hz, sample-to-sample differences include real vehicle motion, so these numbers are not white-noise estimates:

| axis | F1 diff | F1 ma9 | F2 diff | F2 ma9 | ratio diff | ratio ma9 |
|---|---|---|---|---|---|---|
| x | 1.22e-2 | 1.34e-2 | 8.25e-3 | 1.12e-2 | 1.47 | 1.20 |
| y | 1.53e-2 | 1.72e-2 | 7.49e-3 | 9.22e-3 | 2.05 | 1.87 |
| z | 2.12e-2 | 2.41e-2 | 1.91e-2 | 1.82e-2 | 1.11 | 1.32 |

The F2 values (about 0.008 x/y, 0.019 z) do not reproduce the expected 0.0064 / 0.0069. The vibration question cannot be answered from these logs.

**Verdict: INCONCLUSIVE, does not AGREE.** The expected ratio of about 3 is not reproduced, but the data cannot test it. Rerun with a high-rate accel topic logged (for example `sensor_accel_fifo`, or a logging profile at full rate).

## 3. Telemetry dropouts (esc_status, esc[i].esc_errorcount)

Denominator is the number of `esc_status` samples while armed: F1 53763, F2 53721. Rate = number of samples with a count increase / armed samples. The total-increment count is also given.

| motor | F1 rate (events / total inc) | F2 rate (events / total inc) |
|---|---|---|
| 0 | 0.1036 (5572 / 5597) | 0.1030 (5535 / 5549) |
| 1 | 0.1060 (5698 / 5727) | 0.1050 (5639 / 5661) |
| 2 | 0.1015 (5459 / 5475) | 0.1037 (5569 / 5598) |
| 3 | 0.1028 (5526 / 5551) | 0.1037 (5573 / 5594) |

Motors 4-11 have zero increments in both flights.

Motor 0, first 10 armed-sample indices with an increment:
- F1: [13, 20, 32, 35, 40, 41, 115, 121, 125, 131]
- F2: [13, 25, 48, 50, 55, 61, 84, 100, 102, 107]

The lists agree at index 13 and differ from index 20 onward, so the dropout patterns are not identical between the two seeds.

**Verdict: AGREE** (all four active motors are about 0.10-0.106).

## Summary

1. Gyro white noise: F1 about 2.6e-3, F2 about 8.7e-4 rad/s per axis; F1/F2 ratio about 3.0 by both estimators. AGREE.
2. Accel: logs only have sensor_accel at 1 Hz, so white noise cannot be estimated. The 1 Hz ratios are 1.1-2.1 and F2 sigma is not 0.0064/0.0069. INCONCLUSIVE, not an AGREE.
3. Dropouts: 4 active motors at 0.101-0.106 per armed sample in both flights (expected 0.10). AGREE.
4. Motor 0 dropout indices differ between F1 and F2 from index 20 onward (first index 13 coincides).
5. Totals including multi-count jumps are about 0.5 % higher than event counts; no other anomalies found.
6. Nothing committed; this file is the only artifact written to the repo.
