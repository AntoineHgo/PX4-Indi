# A-24 check: is the ~46 Hz tone present with MC_INDI_G2_Y = 27?

Script: `indi_flight/results/stage2_s51/a24_psd.py` (pyulog + numpy; scipy not installed on the host, so detrend, Welch and the 40-50 Hz band std are numpy implementations; band std is the square root of the Welch PSD integrated over 40-50 Hz).

Window per log: first `vehicle_land_detected.landed == 0` + 15 s, to min(last log sample - 15 s, first landed == 1 after takeoff). Welch: 2 s Hann segments, 50 % overlap, linear detrend. Frequency bins are 0.5 Hz.

Logged rate: `actuator_motors` 800 Hz (half = 400 Hz), `vehicle_angular_velocity` 800 Hz. Everything up to 100 Hz is inside the valid band.

## actuator_motors, control[0..3]

Peak/median is the largest 20-100 Hz PSD bin over the median PSD in 20-100 Hz. P is the peak PSD value (control units^2/Hz).

| log | motor | mean | std (detrended) | peak Hz | peak P | peak/median | band std 40-50 Hz |
|---|---|---|---|---|---|---|---|
| REF s45 indi_g1y (G2_Y 0) | 0 | 0.13667 | 7.08e-4 | 44.5 | 1.96e-7 | 1461 | 6.41e-4 |
| REF s45 indi_g1y (G2_Y 0) | 1 | 0.13667 | 7.07e-4 | 44.5 | 1.94e-7 | 1492 | 6.40e-4 |
| REF s45 indi_g1y (G2_Y 0) | 2 | 0.13667 | 7.06e-4 | 44.5 | 1.95e-7 | 1471 | 6.40e-4 |
| REF s45 indi_g1y (G2_Y 0) | 3 | 0.13667 | 7.06e-4 | 44.5 | 1.95e-7 | 1468 | 6.40e-4 |
| measured_g2 seed1 (G2_Y 27) | 0 | 0.13667 | 2.51e-4 | 20.5 | 1.50e-11 | 7.7 | 6.74e-6 |
| measured_g2 seed1 (G2_Y 27) | 1 | 0.13667 | 2.52e-4 | 20.0 | 1.83e-11 | 10.3 | 6.71e-6 |
| measured_g2 seed1 (G2_Y 27) | 2 | 0.13667 | 2.79e-4 | 21.0 | 1.75e-11 | 8.5 | 6.63e-6 |
| measured_g2 seed1 (G2_Y 27) | 3 | 0.13667 | 2.77e-4 | 20.5 | 1.72e-11 | 8.6 | 6.54e-6 |
| measured_g2_s2 seed2 (G2_Y 27) | 0 | 0.13667 | 2.58e-4 | 20.0 | 1.80e-11 | 10.1 | 6.69e-6 |
| measured_g2_s2 seed2 (G2_Y 27) | 1 | 0.13667 | 2.56e-4 | 21.0 | 1.71e-11 | 9.4 | 6.71e-6 |
| measured_g2_s2 seed2 (G2_Y 27) | 2 | 0.13667 | 2.35e-4 | 20.0 | 1.72e-11 | 8.9 | 6.87e-6 |
| measured_g2_s2 seed2 (G2_Y 27) | 3 | 0.13667 | 2.37e-4 | 21.5 | 1.84e-11 | 9.6 | 6.85e-6 |
| model_g2 seed1 (G2_Y 27) | 0 | 0.13668 | 4.64e-4 | 24.5 | 7.59e-12 | 3.9 | 6.59e-6 |
| model_g2 seed1 (G2_Y 27) | 1 | 0.13668 | 4.65e-4 | 26.5 | 7.46e-12 | 3.8 | 6.54e-6 |
| model_g2 seed1 (G2_Y 27) | 2 | 0.13665 | 5.14e-4 | 29.0 | 7.32e-12 | 3.9 | 6.48e-6 |
| model_g2 seed1 (G2_Y 27) | 3 | 0.13666 | 5.16e-4 | 29.0 | 7.24e-12 | 3.9 | 6.50e-6 |
| model_g2_s2 seed2 (G2_Y 27) | 0 | 0.13665 | 1.00e-3 | 24.0 | 7.69e-12 | 4.4 | 6.35e-6 |
| model_g2_s2 seed2 (G2_Y 27) | 1 | 0.13665 | 1.00e-3 | 24.0 | 7.44e-12 | 4.1 | 6.36e-6 |
| model_g2_s2 seed2 (G2_Y 27) | 2 | 0.13670 | 1.00e-3 | 36.0 | 7.44e-12 | 4.0 | 6.55e-6 |
| model_g2_s2 seed2 (G2_Y 27) | 3 | 0.13670 | 1.00e-3 | 29.0 | 7.25e-12 | 4.3 | 6.52e-6 |
| model_g2_a001 seed1 (SINE, reported separately) | 0 | 0.13664 | 2.65e-3 | 50.0 | 1.29e-7 | 6516 | 3.63e-4 |
| model_g2_a001 seed1 (SINE, reported separately) | 1 | 0.13664 | 2.65e-3 | 50.0 | 1.29e-7 | 6419 | 3.63e-4 |
| model_g2_a001 seed1 (SINE, reported separately) | 2 | 0.13673 | 2.63e-3 | 50.0 | 1.29e-7 | 6409 | 3.63e-4 |
| model_g2_a001 seed1 (SINE, reported separately) | 3 | 0.13673 | 2.63e-3 | 50.0 | 1.29e-7 | 6438 | 3.63e-4 |

## vehicle_angular_velocity.xyz (per axis)

| log | axis | std (rad/s) | peak Hz | peak/median | band std 40-50 Hz (rad/s) |
|---|---|---|---|---|---|
| REF s45 indi_g1y | x | 6.48e-3 | 23.5 | 7.4 | 8.8e-5 |
| REF s45 indi_g1y | y | 6.99e-3 | 20.0 | 11.7 | 8.8e-5 |
| REF s45 indi_g1y | z | 1.45e-3 | 44.5 | 1250 | 1.15e-3 |
| measured_g2 seed1 | x / y / z | 5.8e-3 / 5.5e-3 / 1.6e-2 | 21.5 / 20.0 / 25.5 | 9.8 / 10.6 / 7.1 | 8.8e-5 / 8.6e-5 / 9.0e-5 |
| measured_g2_s2 seed2 | x / y / z | 5.5e-3 / 6.5e-3 / 1.2e-2 | 20.0 / 20.0 / 23.5 | 12.2 / 10.5 / 6.8 | 9.2e-5 / 8.4e-5 / 9.2e-5 |
| model_g2 seed1 | x / y / z | 4.6e-3 / 4.1e-3 / 3.8e-2 | 22.5 / 21.5 / 22.5 | 8.6 / 8.2 / 7.1 | 9.0e-5 / 8.6e-5 / 8.8e-5 |
| model_g2_s2 seed2 | x / y / z | 4.4e-3 / 4.7e-3 / 8.6e-2 | 21.5 / 20.0 / 23.0 | 10.3 / 9.7 / 5.9 | 8.8e-5 / 8.8e-5 / 8.8e-5 |
| model_g2_a001 seed1 (SINE) | x / y / z | 1.7e-1 / 4.6e-3 / 1.3e-1 | 20.0 / 20.0 / 20.0 | 1187 / 9.2 / 6.0 | 2.8e-4 / 8.9e-5 / 9.0e-5 |

Observations: the reference angular-velocity z axis shows the 44.5 Hz line (peak/median 1250, band std 1.15e-3 rad/s). None of the G2_Y 27 plain hovers shows it on any axis; their 40-50 Hz band std is at the same level as the 20-100 Hz background.

## Conclusion

1. With MC_INDI_G2_Y 27 the ~45 Hz tone is gone from actuator_motors: in all four plain hovers (2 seeds x measured/model) the peak/median falls from about 1470 to 3.8-10 (the background level), and no 40-50 Hz peak stands out.
2. The 40-50 Hz band std drops from 6.4e-4 (reference) to 6.4e-6 to 6.9e-6 (plain hovers), a reduction of about 95-100x on all four motors.
3. Sine run model_g2_a001 (reported separately): its 50 Hz peak is the injected sine (AMP 0.001, not checked against params), not a residual tone, so it does not show the 46 Hz tone either; its 40-50 Hz band std (3.6e-4) is dominated by the injection, so it should not be read as tone evidence.

## Unverified / flags

- The reference peak is at 44.5 Hz (0.5 Hz bins), not 45.7 Hz as quoted in A-24; the reference std is 7.1e-4, not 8.5e-4, and its window is 71 s. The quoted A-24 figures were probably computed on a different window or method; not reconciled here.
- The reference log is G2_Y 0 (`MC_INDI_G1_Y` 215), the comparison logs are G1_Y 205 with G2_Y 27. The G1_Y change is confounded with G2_Y in this comparison.
- Background angular-velocity peaks sit at 20-25 Hz in the plain hovers; these are not interpreted here.
- Band std uses PSD integration (numpy, no bandpass filter), so it is not identical to a filtered-signal std; the Welch window is a periodic Hann with 2 s segments, and the logs are linearly interpolated onto a uniform 800 Hz grid.
- The `model_g2_a001` injection frequency (50 Hz) was read from the spectrum, not from its params file.
- Only 2 seeds per configuration; the model runs are simulator-only and the measured runs are the `--sim v2` set.
