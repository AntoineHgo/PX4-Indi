# A-22 second-key check (independent, from the ULog only)

Log: indi_flight/results/stage2_s41/model_long_s2/flight.ulg
Log start timestamp: 21.254 s (primary time axis = seconds after this).
Airborne (vehicle_land_detected.landed == 0): 10.76 s to 107.02 s after log start, 76986 motor samples.
actuator_outputs instance: 1118 samples, median rate 10.0 Hz; pairing |dt| for motor 0: median 40.0 ms, max 151.2 ms.
Zero-filled output rows (output[i] < 300 rad/s) excluded per motor, out of 1118 rows: 506, 508, 507, 503.
Airborne output max per motor (rad/s): 1845.2, 1897.1, 1845.2, 1845.4

## 1. Static output map (airborne, all samples)
Motor 0: k_sqrt = 2613.9 rad/s (k/2700 = 0.968), k_lin = 4031.5, affine a = -34.9 b = 1601.4, power exponent p = 0.062
  fit quality: sqrt y=k*sqrt(c) rmse 1072.2 R2 -9.4662; linear y=k*c rmse 1115.6 R2 -10.3290; affine-sqrt y=a*sqrt(c)+b rmse 331.3 R2 0.0010
  best simple map (lowest rmse): affine-sqrt y=a*sqrt(c)+b
  bin 0.05 n=   741 mean_c=0.0503 mean_out=  1576.6 ratio=out/(sqrt(c)*2700)=2.6025
  bin 0.10 n=  1287 mean_c=0.1002 mean_out=  1264.2 ratio=out/(sqrt(c)*2700)=1.4794
  bin 0.15 n=   780 mean_c=0.1501 mean_out=  1531.4 ratio=out/(sqrt(c)*2700)=1.4640
  bin 0.20 n=  1248 mean_c=0.2004 mean_out=  1623.6 ratio=out/(sqrt(c)*2700)=1.3431
  bin 0.25 n=  1823 mean_c=0.2498 mean_out=  1600.3 ratio=out/(sqrt(c)*2700)=1.1858
Motor 1: k_sqrt = 2600.4 rad/s (k/2700 = 0.963), k_lin = 4010.3, affine a = -33.1 b = 1590.6, power exponent p = 0.079
  fit quality: sqrt y=k*sqrt(c) rmse 1069.7 R2 -8.4676; linear y=k*c rmse 1113.0 R2 -9.2496; affine-sqrt y=a*sqrt(c)+b rmse 347.5 R2 0.0008
  best simple map (lowest rmse): affine-sqrt y=a*sqrt(c)+b
  bin 0.05 n=  1106 mean_c=0.0505 mean_out=  1301.5 ratio=out/(sqrt(c)*2700)=2.1442
  bin 0.10 n=  1226 mean_c=0.0991 mean_out=  1250.9 ratio=out/(sqrt(c)*2700)=1.4716
  bin 0.15 n=   854 mean_c=0.1493 mean_out=  1508.7 ratio=out/(sqrt(c)*2700)=1.4459
  bin 0.20 n=  1293 mean_c=0.2005 mean_out=  1597.5 ratio=out/(sqrt(c)*2700)=1.3213
  bin 0.25 n=  1853 mean_c=0.2498 mean_out=  1598.8 ratio=out/(sqrt(c)*2700)=1.1848
Motor 2: k_sqrt = 2576.3 rad/s (k/2700 = 0.954), k_lin = 3969.9, affine a = -30.7 b = 1577.4, power exponent p = 0.046
  fit quality: sqrt y=k*sqrt(c) rmse 1068.5 R2 -7.9160; linear y=k*c rmse 1111.4 R2 -8.6467; affine-sqrt y=a*sqrt(c)+b rmse 357.7 R2 0.0007
  best simple map (lowest rmse): affine-sqrt y=a*sqrt(c)+b
  bin 0.05 n=   808 mean_c=0.0502 mean_out=  1511.2 ratio=out/(sqrt(c)*2700)=2.4973
  bin 0.10 n=  1322 mean_c=0.1000 mean_out=  1242.8 ratio=out/(sqrt(c)*2700)=1.4558
  bin 0.15 n=   744 mean_c=0.1497 mean_out=  1571.4 ratio=out/(sqrt(c)*2700)=1.5044
  bin 0.20 n=  1229 mean_c=0.2004 mean_out=  1610.6 ratio=out/(sqrt(c)*2700)=1.3326
  bin 0.25 n=  1729 mean_c=0.2498 mean_out=  1589.9 ratio=out/(sqrt(c)*2700)=1.1782
Motor 3: k_sqrt = 2576.4 rad/s (k/2700 = 0.954), k_lin = 3972.3, affine a = -40.9 b = 1581.7, power exponent p = 0.063
  fit quality: sqrt y=k*sqrt(c) rmse 1068.4 R2 -7.8676; linear y=k*c rmse 1111.2 R2 -8.5919; affine-sqrt y=a*sqrt(c)+b rmse 358.6 R2 0.0011
  best simple map (lowest rmse): affine-sqrt y=a*sqrt(c)+b
  bin 0.05 n=   861 mean_c=0.0504 mean_out=  1502.8 ratio=out/(sqrt(c)*2700)=2.4780
  bin 0.10 n=  1386 mean_c=0.0998 mean_out=  1202.7 ratio=out/(sqrt(c)*2700)=1.4103
  bin 0.15 n=   755 mean_c=0.1504 mean_out=  1573.6 ratio=out/(sqrt(c)*2700)=1.5028
  bin 0.20 n=  1247 mean_c=0.2002 mean_out=  1592.8 ratio=out/(sqrt(c)*2700)=1.3183
  bin 0.25 n=  1683 mean_c=0.2499 mean_out=  1598.0 ratio=out/(sqrt(c)*2700)=1.1838

## 1b. Hover window means and output ratio
mode rel: window 52.00 s to 82.00 s on airborne samples, n=23993 (span 52.00 to 82.00 s)
  motor 0: mean control 0.2213, mean output 1617.1 rad/s, ratio 1.2731
  motor 1: mean control 0.2209, mean output 1624.6 rad/s, ratio 1.2801
  motor 2: mean control 0.2213, mean output 1546.8 rad/s, ratio 1.2178
  motor 3: mean control 0.2210, mean output 1554.3 rad/s, ratio 1.2246
  mean of per-motor ratios 1.2489; pooled ratio of means 1.2489; per-sample mean-of-sqrt ratio 1.6252
mode abs: window 52.00 s to 82.00 s on airborne samples, n=23993 (span 30.75 to 60.75 s)
  motor 0: mean control 0.2211, mean output 1617.5 rad/s, ratio 1.2740
  motor 1: mean control 0.2212, mean output 1591.8 rad/s, ratio 1.2536
  motor 2: mean control 0.2210, mean output 1593.8 rad/s, ratio 1.2557
  motor 3: mean control 0.2212, mean output 1612.8 rad/s, ratio 1.2699
  mean of per-motor ratios 1.2633; pooled ratio of means 1.2633; per-sample mean-of-sqrt ratio 1.6440

## 1c. Quasi-static map: control averaged over 0.5 s, evaluated at output timestamps
Motor 0 (n=601): k_sqrt/2700 = 1.241, k_lin/2700 = 2.632, affine a = 5464.6 b = -994.0, best rmse map: linear y=k*c
  fit quality: sqrt y=k*sqrt(c) rmse 306.7 R2 0.2173; linear y=k*c rmse 295.3 R2 0.2744; affine-sqrt y=a*sqrt(c)+b rmse 299.1 R2 0.2558
  bin 0.05 n=1 ratio=1.081; bin 0.10 n=9 ratio=0.974; bin 0.15 n=4 ratio=1.343; bin 0.20 n=13 ratio=1.011; bin 0.25 n=7 ratio=1.381
Motor 1 (n=600): k_sqrt/2700 = 1.231, k_lin/2700 = 2.611, affine a = 5571.3 b = -1056.9, best rmse map: linear y=k*c
  fit quality: sqrt y=k*sqrt(c) rmse 324.7 R2 0.2180; linear y=k*c rmse 311.0 R2 0.2824; affine-sqrt y=a*sqrt(c)+b rmse 315.7 R2 0.2606
  bin 0.05 n=2 ratio=0.982; bin 0.10 n=8 ratio=1.018; bin 0.15 n=4 ratio=1.132; bin 0.20 n=11 ratio=1.110; bin 0.25 n=5 ratio=1.390
Motor 2 (n=601): k_sqrt/2700 = 1.224, k_lin/2700 = 2.595, affine a = 5512.1 b = -1038.9, best rmse map: linear y=k*c
  fit quality: sqrt y=k*sqrt(c) rmse 334.3 R2 0.1686; linear y=k*c rmse 323.9 R2 0.2196; affine-sqrt y=a*sqrt(c)+b rmse 327.7 R2 0.2009
  bin 0.05 n=1 ratio=1.008; bin 0.10 n=8 ratio=1.073; bin 0.15 n=5 ratio=1.146; bin 0.20 n=14 ratio=1.168; bin 0.25 n=5 ratio=1.385
Motor 3 (n=605): k_sqrt/2700 = 1.225, k_lin/2700 = 2.598, affine a = 5430.4 b = -998.0, best rmse map: linear y=k*c
  fit quality: sqrt y=k*sqrt(c) rmse 333.5 R2 0.1990; linear y=k*c rmse 321.8 R2 0.2542; affine-sqrt y=a*sqrt(c)+b rmse 325.9 R2 0.2351
  bin 0.10 n=10 ratio=0.984; bin 0.15 n=4 ratio=1.213; bin 0.20 n=11 ratio=1.145; bin 0.25 n=5 ratio=1.387

## 2. Allocator roll gain (least squares, 2-10 Hz zero-phase Butterworth order 4)
Joint fit: control_i ~ b0*xyz[0] + b1*xyz[1] + b2*xyz[2]; single fit: control_i ~ s*xyz[0].
mode rel:
  motor 0: b_roll(xyz0) = -0.2361 | b_pitch(xyz1) = +0.3832 | b_yaw(xyz2) = -0.0019 | joint R2 0.9520 | single-axis roll -0.2037
  motor 1: b_roll(xyz0) = +0.2277 | b_pitch(xyz1) = -0.3891 | b_yaw(xyz2) = -0.0073 | joint R2 0.9594 | single-axis roll +0.1946
  motor 2: b_roll(xyz0) = +0.2288 | b_pitch(xyz1) = +0.3862 | b_yaw(xyz2) = +0.0090 | joint R2 0.9621 | single-axis roll +0.2616
  motor 3: b_roll(xyz0) = -0.2217 | b_pitch(xyz1) = -0.3812 | b_yaw(xyz2) = +0.0011 | joint R2 0.9536 | single-axis roll -0.2539
mode abs:
  motor 0: b_roll(xyz0) = -0.2338 | b_pitch(xyz1) = +0.3839 | b_yaw(xyz2) = -0.0136 | joint R2 0.8254 | single-axis roll -0.1964
  motor 1: b_roll(xyz0) = +0.2573 | b_pitch(xyz1) = -0.6061 | b_yaw(xyz2) = +0.0052 | joint R2 0.7450 | single-axis roll +0.1989
  motor 2: b_roll(xyz0) = +0.1999 | b_pitch(xyz1) = +0.5555 | b_yaw(xyz2) = -0.0031 | joint R2 0.7966 | single-axis roll +0.2534
  motor 3: b_roll(xyz0) = -0.2241 | b_pitch(xyz1) = -0.3331 | b_yaw(xyz2) = +0.0148 | joint R2 0.8203 | single-axis roll -0.2566

## 3. Summary and comparison (primary convention: seconds after log start)
Per-motor roll coefficient magnitudes: 0.2361, 0.2277, 0.2288, 0.2217
Per-motor roll coefficient signs: -1, +1, +1, -1
Coefficient vs 0.23: relative diffs +2.6%, -1.0%, -0.5%, -3.6%; all within 10 %: True
Output-map ratio at hover (mean of per-motor ratios of means): 1.2489 vs 0.769, relative diff +62.4 %; within 10 %: False
VERDICT: DISAGREE

## 4. Reviewer notes on the numbers above

- Zero-filled output rows: actuator_outputs output[i] is 0 (below 300 rad/s) on 506-508 of the 1118 rows per motor over the log, about 36 % of the 963 airborne rows. The numbers in sections 1, 1b and 1c exclude those rows per motor. An earlier run that kept them gave a hover ratio of 0.7695 (the reference 0.769); that agreement comes from the zero rows pulling the mean down, not from a valid map, so it is not used here.
- With the zero rows excluded, the hover output ratio out/(sqrt(c)*2700) is about 1.25 (ratio of means) and 1.63 for the per-sample mean of sqrt(c). The instantaneous sqrt map has R2 near -9 and the affine fit R2 near 0, so 10 Hz nearest-timestamp pairing does not identify a static map on this log. The 0.5 s quasi-static map gives k/2700 of about 1.22-1.24 with R2 about 0.2.
- The maximum rotor speed in the log is 1897 rad/s, not the 2700 nominal scale.
- Time convention: the primary window is 52-82 s after the ULog start timestamp. Read on the raw PX4 timestamp axis, the same window is 30.75-60.75 s after log start. The roll coefficients for motors 1 and 2 change by 0.02-0.05 between the two conventions, so the roll check is sensitive to the convention.
- Verdict: roll coefficients AGREE with 0.23 (primary convention, all within 4 %). The hover output ratio DISAGREES with 0.769 (measured 1.25).
