# S41 second-key check of M3a loop margins

Independent script: `indi_flight/bench/second_key_m3a_s41.py` (direct Fourier sums on actual sample times, L = -Y/X, X = torque_sp[0], Y = torque_sp_pre_inject[0]).

**Verdict: DISAGREE.** Phase margin agrees within 2 deg on both logs (0.09 and 0.06 deg). The per-bin criterion (|L| within 0.5 dB and arg within 3 deg for bins up to 20 Hz) fails on both logs, so the gate is not met.

## Second-key runs

## Run: `indi_flight/results/stage2_s41/model_long_s2/flight.ulg`

- Window start: 52.017 s, end: 82.016 s, duration 29.999 s
- Samples in window (first to last inject != 0, inclusive): 23992
- Of which inject == 0: 0
- Downward 0 dB crossings: 1

| f (Hz) | abs(L) (dB) | arg L (deg) | arg L unwrapped (deg) |
|---:|---:|---:|---:|
| 1.0 | 20.90 | -155.8 | -155.8 |
| 1.3 | 12.07 | -157.8 | -157.8 |
| 1.6 | 9.73 | -152.1 | -152.1 |
| 2.0 | 6.89 | -145.1 | -145.1 |
| 2.5 | 6.51 | -128.9 | -128.9 |
| 3.2 | 2.91 | -141.3 | -141.3 |
| 4.0 | 1.46 | -150.9 | -150.9 |
| 5.0 | -0.67 | -158.4 | -158.4 |
| 6.3 | -3.48 | -171.1 | -171.1 |
| 7.9 | -6.17 | 176.8 | -183.2 |
| 10.0 | -8.77 | 156.5 | -203.5 |
| 12.6 | -12.00 | 139.0 | -221.0 |
| 15.8 | -15.46 | 144.9 | -215.1 |
| 20.0 | -15.69 | 125.1 | -234.9 |
| 25.1 | -16.17 | 101.5 | -258.5 |
| 31.6 | -21.96 | -30.4 | -390.4 |
| 39.8 | -20.26 | -143.3 | -503.3 |
| 50.1 | -25.46 | 7.1 | -352.9 |

- Crossover freq (|L| = 0 dB): 4.661 Hz
- Phase margin: 23.96 deg
- Gain-margin frequency (arg L = -180 deg): 7.440 Hz
- Gain margin: 5.46 dB

## Run: `indi_flight/results/stage2_s40/pretest_inj/model_long/flight.ulg`

- Window start: 52.030 s, end: 82.029 s, duration 29.999 s
- Samples in window (first to last inject != 0, inclusive): 23995
- Of which inject == 0: 0
- Downward 0 dB crossings: 1

| f (Hz) | abs(L) (dB) | arg L (deg) | arg L unwrapped (deg) |
|---:|---:|---:|---:|
| 1.0 | 16.17 | -162.5 | -162.5 |
| 1.3 | 12.50 | -151.1 | -151.1 |
| 1.6 | 10.53 | -158.9 | -158.9 |
| 2.0 | 6.23 | -143.3 | -143.3 |
| 2.5 | 5.32 | -137.9 | -137.9 |
| 3.2 | 2.83 | -144.8 | -144.8 |
| 4.0 | 1.28 | -149.4 | -149.4 |
| 5.0 | -0.95 | -158.7 | -158.7 |
| 6.3 | -3.06 | -170.9 | -170.9 |
| 7.9 | -4.94 | 176.1 | -183.9 |
| 10.0 | -8.31 | 152.3 | -207.7 |
| 12.6 | -12.37 | 129.9 | -230.1 |
| 15.8 | -11.45 | 126.5 | -233.5 |
| 20.0 | -24.54 | 148.5 | -211.5 |
| 25.1 | -16.64 | 109.3 | -250.7 |
| 31.6 | -20.96 | -16.1 | -376.1 |
| 39.8 | -21.82 | -140.4 | -500.4 |
| 50.1 | -26.65 | -57.0 | -417.0 |

- Crossover freq (|L| = 0 dB): 4.547 Hz
- Phase margin: 25.29 deg
- Gain-margin frequency (arg L = -180 deg): 7.384 Hz
- Gain margin: 4.38 dB

## Comparison with primary (`margins_model_long_s2.txt`, `margins_model_long.txt`)

Delta = second-key minus primary. Bins up to 20 Hz only (14 bins). The primary reports 14 accepted bins for s2 and 13 for s40; this script does no coherence rejection, so it cannot say which bins the primary dropped.

### stage2_s41/model_long_s2

| f (Hz) | primary abs(L) dB | 2nd abs(L) dB | delta dB | primary arg deg | 2nd arg deg | delta deg |
|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 18.4 | 20.90 | +2.50 | -168.5 | -155.8 | +12.7 |
| 1.3 | 11.3 | 12.07 | +0.77 | -165.3 | -157.8 | +7.5 |
| 1.6 | 9.2 | 9.73 | +0.53 | -151.6 | -152.1 | -0.5 |
| 2.0 | 7.8 | 6.89 | -0.91 | -145.6 | -145.1 | +0.5 |
| 2.5 | 7.0 | 6.51 | -0.49 | -127.8 | -128.9 | -1.1 |
| 3.2 | 2.4 | 2.91 | +0.51 | -137.0 | -141.3 | -4.3 |
| 4.0 | 1.5 | 1.46 | -0.04 | -150.4 | -150.9 | -0.5 |
| 5.0 | -0.6 | -0.67 | -0.07 | -157.8 | -158.4 | -0.6 |
| 6.3 | -3.4 | -3.48 | -0.08 | -170.8 | -171.1 | -0.3 |
| 7.9 | -6.4 | -6.17 | +0.23 | 177.7 | 176.8 | -0.9 |
| 10.0 | -9.3 | -8.77 | +0.53 | 151.9 | 156.5 | +4.6 |
| 12.6 | -12.7 | -12.00 | +0.70 | 137.5 | 139.0 | +1.5 |
| 15.8 | -11.7 | -15.46 | -3.76 | 155.2 | 144.9 | -10.3 |
| 20.0 | -15.4 | -15.69 | -0.29 | 143.6 | 125.1 | -18.5 |

Out of tolerance: |L| at 1.0, 1.3, 1.6, 2.0, 3.2, 10.0, 12.6, 15.8 Hz; arg at 1.0, 1.3, 3.2, 10.0, 15.8, 20.0 Hz.
PM: 23.96 vs 24.05 deg (delta -0.09). Crossover: 4.661 vs 4.752 Hz. GM: 5.46 vs 6.02 dB (delta -0.56). GM frequency: 7.440 vs 7.656 Hz.

### stage2_s40/pretest_inj/model_long

| f (Hz) | primary abs(L) dB | 2nd abs(L) dB | delta dB | primary arg deg | 2nd arg deg | delta deg |
|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 16.9 | 16.17 | -0.73 | -163.7 | -162.5 | +1.2 |
| 1.3 | 12.4 | 12.50 | +0.10 | -163.5 | -151.1 | +12.4 |
| 1.6 | 10.6 | 10.53 | -0.07 | -163.0 | -158.9 | +4.1 |
| 2.0 | 6.9 | 6.23 | -0.67 | -143.5 | -143.3 | +0.2 |
| 2.5 | 6.0 | 5.32 | -0.68 | -138.0 | -137.9 | +0.1 |
| 3.2 | 2.9 | 2.83 | -0.07 | -142.4 | -144.8 | -2.4 |
| 4.0 | 1.2 | 1.28 | +0.08 | -151.0 | -149.4 | +1.6 |
| 5.0 | -1.2 | -0.95 | +0.25 | -158.6 | -158.7 | -0.1 |
| 6.3 | -2.8 | -3.06 | -0.26 | -170.0 | -170.9 | -0.9 |
| 7.9 | -4.9 | -4.94 | -0.04 | 175.6 | 176.1 | +0.5 |
| 10.0 | -8.6 | -8.31 | +0.29 | 154.4 | 152.3 | -2.1 |
| 12.6 | -12.3 | -12.37 | -0.07 | 134.9 | 129.9 | -5.0 |
| 15.8 | -10.0 | -11.45 | -1.45 | 128.3 | 126.5 | -1.8 |
| 20.0 | -23.3 | -24.54 | -1.24 | 173.7 | 148.5 | -25.2 |

Out of tolerance: |L| at 1.0, 2.0, 2.5, 15.8, 20.0 Hz; arg at 1.3, 1.6, 12.6, 20.0 Hz.
PM: 25.29 vs 25.35 deg (delta -0.06). Crossover: 4.547 vs 4.469 Hz. GM: 4.38 vs 4.28 dB (delta +0.10). GM frequency: 7.384 vs 7.437 Hz.

### Notes

- The disagreement is concentrated at the low-frequency end (1.0 to 2.0 Hz, where |L| and arg differ by up to 2.5 dB and 12 deg) and at isolated bins (15.8 and 20.0 Hz). The script and the primary may differ in windowing, detrending or bin acceptance; this check did not inspect the primary code, as instructed.
- PM is the only quantity inside the gate. Gain margin differs by 0.56 dB on s2.

## Variant B

Two options were added to `indi_flight/bench/second_key_m3a_s41.py` (optional third argument: primary margins file). Variant A above is unchanged.

- **B1, periods 2-3 only** (window start + 10 s to end), direct sums, L = -Y/X. Verdict **AGREE** on both logs: all bins up to 20 Hz within 0.5 dB and 3 deg, PM within 0.25 deg (s2: 24.28 vs 24.05 deg; s40: 25.13 vs 25.35 deg).
- **B2, per-period coefficients averaged** over the three 10 s periods (local time reference), then L = -(Y_avg/D_avg)/(X_avg/D_avg). D cancels in the ratio, so this equals -Y_avg/X_avg. It reproduces Variant A to within 0.01 dB, so its verdict is **DISAGREE** on both logs, as before.

Reading: the disagreement with the primary comes from the first 10 s period (the transient). Dropping it (B1) brings every bin up to 20 Hz inside tolerance on both logs. B2 is not an independent estimate of Variant A.

Signal levels: the excitation amplitude |D| is a uniform 0.005 per bin, so |X|/|D| shows how strongly the plant input responds to each bin. The lowest bins are the weakest responders: |X|/|D| at 1.0 Hz is 0.135 (s2) and 0.166 (s40) in B1, and 0.098 and 0.182 in Variant A. These are the bins where the estimate is least well conditioned.

### Run `indi_flight/results/stage2_s41/model_long_s2/flight.ulg`

- Full window 52.017 to 82.016 s, 23992 samples

#### Variant A signal levels (full window, current method)

Full window, 23992 samples. Margins as in the main table.

| f (Hz) | abs(L) dB | arg L deg | abs(D) | abs(X)/abs(D) |
|---:|---:|---:|---:|---:|
| 1.0 | 20.90 | -155.8 | 0.005 | 0.0981 |
| 1.3 | 12.07 | -157.8 | 0.005 | 0.321 |
| 1.6 | 9.73 | -152.1 | 0.00501 | 0.448 |
| 2.0 | 6.89 | -145.1 | 0.005 | 0.665 |
| 2.5 | 6.51 | -128.9 | 0.00501 | 0.596 |
| 3.2 | 2.91 | -141.3 | 0.005 | 1.14 |
| 4.0 | 1.46 | -150.9 | 0.005 | 1.73 |
| 5.0 | -0.67 | -158.4 | 0.005 | 2.72 |
| 6.3 | -3.48 | -171.1 | 0.005 | 2.83 |
| 7.9 | -6.17 | 176.8 | 0.005 | 1.96 |
| 10.0 | -8.77 | 156.5 | 0.005 | 1.47 |
| 12.6 | -12.00 | 139.0 | 0.005 | 1.21 |
| 15.8 | -15.46 | 144.9 | 0.005 | 1.15 |
| 20.0 | -15.69 | 125.1 | 0.005 | 1.09 |
| 25.1 | -16.17 | 101.5 | 0.005 | 1.02 |
| 31.6 | -21.96 | -30.4 | 0.005 | 0.935 |
| 39.8 | -20.26 | -143.3 | 0.005 | 1.08 |
| 50.1 | -25.46 | 7.1 | 0.005 | 0.95 |

- PM 23.96 deg, crossover 4.661 Hz, GM 5.46 dB at 7.440 Hz

#### Variant B1: periods 2-3, direct sums, L = -Y/X

Window 62.017 to 82.016 s, 15994 samples

| f (Hz) | prim abs(L) dB | abs(L) dB | delta dB | prim arg deg | arg deg | delta deg | abs(D) | abs(X)/abs(D) | out of tol (<=20 Hz) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| 1.0 | 18.40 | 18.45 | +0.05 | -168.5 | -169.1 | -0.6 | 0.005 | 0.135 |  |
| 1.3 | 11.30 | 11.31 | +0.01 | -165.3 | -165.3 | +0.0 | 0.005 | 0.367 |  |
| 1.6 | 9.20 | 9.24 | +0.04 | -151.6 | -151.6 | +0.0 | 0.005 | 0.482 |  |
| 2.0 | 7.80 | 7.80 | +0.00 | -145.6 | -145.6 | -0.0 | 0.005 | 0.58 |  |
| 2.5 | 7.00 | 7.01 | +0.01 | -127.8 | -127.7 | +0.1 | 0.005 | 0.552 |  |
| 3.2 | 2.40 | 2.41 | +0.01 | -137.0 | -136.9 | +0.1 | 0.005 | 1.11 |  |
| 4.0 | 1.50 | 1.48 | -0.02 | -150.4 | -150.3 | +0.1 | 0.005 | 1.7 |  |
| 5.0 | -0.60 | -0.57 | +0.03 | -157.8 | -157.8 | +0.0 | 0.005 | 2.64 |  |
| 6.3 | -3.40 | -3.41 | -0.01 | -170.8 | -170.8 | +0.0 | 0.005 | 2.85 |  |
| 7.9 | -6.40 | -6.41 | -0.01 | 177.7 | 177.7 | +0.0 | 0.005 | 1.91 |  |
| 10.0 | -9.30 | -9.29 | +0.01 | 151.9 | 151.9 | -0.0 | 0.005 | 1.4 |  |
| 12.6 | -12.70 | -12.71 | -0.01 | 137.5 | 137.4 | -0.1 | 0.005 | 1.18 |  |
| 15.8 | -11.70 | -11.69 | +0.01 | 155.2 | 155.2 | -0.0 | 0.005 | 1.3 |  |
| 20.0 | -15.40 | -15.38 | +0.02 | 143.6 | 143.8 | +0.2 | 0.005 | 1.15 |  |
| 25.1 | -16.00 | -15.97 | +0.03 | 102.5 | 102.5 | +0.0 | 0.005 | 1.02 |  |
| 31.6 | -22.00 | -21.99 | +0.01 | -23.9 | -23.3 | +0.6 | 0.005 | 0.932 |  |
| 39.8 | -20.60 | -20.56 | +0.04 | -146.4 | -146.3 | +0.1 | 0.005 | 1.08 |  |
| 50.1 | -23.50 | -23.46 | +0.04 | -0.2 | -0.6 | -0.4 | 0.005 | 0.937 |  |

- PM: 24.28 vs primary 24.05 deg (delta +0.23)
- Crossover: 4.701 vs primary 4.752 Hz
- GM: 5.82 vs primary 6.02 dB (delta -0.21)
- Bins out of tolerance (<=20 Hz): abs(L) 0, arg 0
- **Verdict: AGREE**

#### Variant B2: per-period coefficients averaged, L = -(Y_avg/D_avg)/(X_avg/D_avg)

Periods 1-3 (10 s each), samples per period [7998, 7999, 7995]

| f (Hz) | prim abs(L) dB | abs(L) dB | delta dB | prim arg deg | arg deg | delta deg | abs(D) | abs(X)/abs(D) | out of tol (<=20 Hz) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| 1.0 | 18.40 | 20.90 | +2.50 | -168.5 | -155.8 | +12.7 | 0.005 | 0.0981 | abs(L) arg |
| 1.3 | 11.30 | 12.07 | +0.77 | -165.3 | -157.8 | +7.5 | 0.005 | 0.321 | abs(L) arg |
| 1.6 | 9.20 | 9.73 | +0.53 | -151.6 | -152.1 | -0.5 | 0.00501 | 0.448 | abs(L) |
| 2.0 | 7.80 | 6.89 | -0.91 | -145.6 | -145.1 | +0.5 | 0.005 | 0.665 | abs(L) |
| 2.5 | 7.00 | 6.51 | -0.49 | -127.8 | -128.9 | -1.1 | 0.00501 | 0.596 |  |
| 3.2 | 2.40 | 2.91 | +0.51 | -137.0 | -141.3 | -4.3 | 0.005 | 1.14 | abs(L) arg |
| 4.0 | 1.50 | 1.46 | -0.04 | -150.4 | -150.9 | -0.5 | 0.005 | 1.73 |  |
| 5.0 | -0.60 | -0.67 | -0.07 | -157.8 | -158.4 | -0.6 | 0.005 | 2.72 |  |
| 6.3 | -3.40 | -3.48 | -0.08 | -170.8 | -171.1 | -0.3 | 0.005 | 2.83 |  |
| 7.9 | -6.40 | -6.17 | +0.23 | 177.7 | 176.8 | -0.9 | 0.005 | 1.96 |  |
| 10.0 | -9.30 | -8.77 | +0.53 | 151.9 | 156.5 | +4.6 | 0.005 | 1.47 | abs(L) arg |
| 12.6 | -12.70 | -12.00 | +0.70 | 137.5 | 139.0 | +1.5 | 0.005 | 1.21 | abs(L) |
| 15.8 | -11.70 | -15.46 | -3.76 | 155.2 | 144.9 | -10.3 | 0.005 | 1.15 | abs(L) arg |
| 20.0 | -15.40 | -15.69 | -0.29 | 143.6 | 125.1 | -18.5 | 0.005 | 1.09 | arg |
| 25.1 | -16.00 | -16.17 | -0.17 | 102.5 | 101.5 | -1.0 | 0.005 | 1.02 |  |
| 31.6 | -22.00 | -21.96 | +0.04 | -23.9 | -30.4 | -6.5 | 0.005 | 0.935 |  |
| 39.8 | -20.60 | -20.26 | +0.34 | -146.4 | -143.3 | +3.1 | 0.005 | 1.08 |  |
| 50.1 | -23.50 | -25.46 | -1.96 | -0.2 | 7.1 | +7.3 | 0.005 | 0.95 |  |

- PM: 23.96 vs primary 24.05 deg (delta -0.09)
- Crossover: 4.661 vs primary 4.752 Hz
- GM: 5.46 vs primary 6.02 dB (delta -0.56)
- Bins out of tolerance (<=20 Hz): abs(L) 8, arg 6
- **Verdict: DISAGREE**


### Run `indi_flight/results/stage2_s40/pretest_inj/model_long/flight.ulg`

- Full window 52.030 to 82.029 s, 23995 samples

#### Variant A signal levels (full window, current method)

Full window, 23995 samples. Margins as in the main table.

| f (Hz) | abs(L) dB | arg L deg | abs(D) | abs(X)/abs(D) |
|---:|---:|---:|---:|---:|
| 1.0 | 16.17 | -162.5 | 0.005 | 0.182 |
| 1.3 | 12.50 | -151.1 | 0.005 | 0.296 |
| 1.6 | 10.53 | -158.9 | 0.005 | 0.408 |
| 2.0 | 6.23 | -143.3 | 0.005 | 0.723 |
| 2.5 | 5.32 | -137.9 | 0.005 | 0.775 |
| 3.2 | 2.83 | -144.8 | 0.005 | 1.24 |
| 4.0 | 1.28 | -149.4 | 0.005 | 1.69 |
| 5.0 | -0.95 | -158.7 | 0.005 | 2.74 |
| 6.3 | -3.06 | -170.9 | 0.005 | 3.07 |
| 7.9 | -4.94 | 176.1 | 0.005 | 2.29 |
| 10.0 | -8.31 | 152.3 | 0.005 | 1.46 |
| 12.6 | -12.37 | 129.9 | 0.005 | 1.16 |
| 15.8 | -11.45 | 126.5 | 0.005 | 1.15 |
| 20.0 | -24.54 | 148.5 | 0.005 | 1.05 |
| 25.1 | -16.64 | 109.3 | 0.005 | 1.04 |
| 31.6 | -20.96 | -16.1 | 0.005 | 0.921 |
| 39.8 | -21.82 | -140.4 | 0.005 | 1.06 |
| 50.1 | -26.65 | -57.0 | 0.005 | 0.975 |

- PM 25.29 deg, crossover 4.547 Hz, GM 4.38 dB at 7.384 Hz

#### Variant B1: periods 2-3, direct sums, L = -Y/X

Window 62.030 to 82.029 s, 15996 samples

| f (Hz) | prim abs(L) dB | abs(L) dB | delta dB | prim arg deg | arg deg | delta deg | abs(D) | abs(X)/abs(D) | out of tol (<=20 Hz) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| 1.0 | 16.90 | 16.88 | -0.02 | -163.7 | -164.0 | -0.3 | 0.005 | 0.166 |  |
| 1.3 | 12.40 | 12.39 | -0.01 | -163.5 | -163.5 | +0.0 | 0.005 | 0.311 |  |
| 1.6 | 10.60 | 10.60 | +0.00 | -163.0 | -163.0 | +0.0 | 0.005 | 0.408 |  |
| 2.0 | 6.90 | 6.86 | -0.04 | -143.5 | -143.5 | -0.0 | 0.005 | 0.658 |  |
| 2.5 | 6.00 | 5.99 | -0.01 | -138.0 | -137.9 | +0.1 | 0.005 | 0.705 |  |
| 3.2 | 2.90 | 2.94 | +0.04 | -142.4 | -142.4 | +0.0 | 0.005 | 1.16 |  |
| 4.0 | 1.20 | 1.19 | -0.01 | -151.0 | -151.0 | +0.0 | 0.005 | 1.8 |  |
| 5.0 | -1.20 | -1.16 | +0.04 | -158.6 | -158.6 | -0.0 | 0.005 | 2.71 |  |
| 6.3 | -2.80 | -2.84 | -0.04 | -170.0 | -170.0 | -0.0 | 0.005 | 3.16 |  |
| 7.9 | -4.90 | -4.95 | -0.05 | 175.6 | 175.7 | +0.1 | 0.005 | 2.28 |  |
| 10.0 | -8.60 | -8.63 | -0.03 | 154.4 | 154.3 | -0.1 | 0.005 | 1.46 |  |
| 12.6 | -12.30 | -12.31 | -0.01 | 134.9 | 134.8 | -0.1 | 0.005 | 1.18 |  |
| 15.8 | -10.00 | -10.03 | -0.03 | 128.3 | 128.4 | +0.1 | 0.005 | 1.19 |  |
| 20.0 | -23.30 | -23.23 | +0.07 | 173.7 | 173.7 | -0.0 | 0.005 | 1.07 |  |
| 25.1 | -16.40 | -16.39 | +0.01 | 113.7 | 113.6 | -0.1 | 0.005 | 1.05 |  |
| 31.6 | -20.00 | -19.96 | +0.04 | -5.4 | -5.5 | -0.1 | 0.005 | 0.909 |  |
| 39.8 | -21.90 | -21.92 | -0.02 | -142.6 | -142.6 | -0.0 | 0.005 | 1.07 |  |
| 50.1 | -24.80 | -24.70 | +0.10 | -46.4 | -46.6 | -0.2 | 0.005 | 0.961 |  |

- PM: 25.13 vs primary 25.35 deg (delta -0.22)
- Crossover: 4.480 vs primary 4.469 Hz
- GM: 4.31 vs primary 4.28 dB (delta +0.03)
- Bins out of tolerance (<=20 Hz): abs(L) 0, arg 0
- **Verdict: AGREE**

#### Variant B2: per-period coefficients averaged, L = -(Y_avg/D_avg)/(X_avg/D_avg)

Periods 1-3 (10 s each), samples per period [8000, 7998, 7997]

| f (Hz) | prim abs(L) dB | abs(L) dB | delta dB | prim arg deg | arg deg | delta deg | abs(D) | abs(X)/abs(D) | out of tol (<=20 Hz) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| 1.0 | 16.90 | 16.17 | -0.73 | -163.7 | -162.5 | +1.2 | 0.005 | 0.182 | abs(L) |
| 1.3 | 12.40 | 12.50 | +0.10 | -163.5 | -151.1 | +12.4 | 0.005 | 0.296 | arg |
| 1.6 | 10.60 | 10.53 | -0.07 | -163.0 | -158.9 | +4.1 | 0.005 | 0.408 | arg |
| 2.0 | 6.90 | 6.23 | -0.67 | -143.5 | -143.3 | +0.2 | 0.005 | 0.723 | abs(L) |
| 2.5 | 6.00 | 5.32 | -0.68 | -138.0 | -137.9 | +0.1 | 0.005 | 0.775 | abs(L) |
| 3.2 | 2.90 | 2.83 | -0.07 | -142.4 | -144.8 | -2.4 | 0.005 | 1.24 |  |
| 4.0 | 1.20 | 1.28 | +0.08 | -151.0 | -149.4 | +1.6 | 0.005 | 1.69 |  |
| 5.0 | -1.20 | -0.95 | +0.25 | -158.6 | -158.7 | -0.1 | 0.005 | 2.74 |  |
| 6.3 | -2.80 | -3.06 | -0.26 | -170.0 | -170.9 | -0.9 | 0.005 | 3.07 |  |
| 7.9 | -4.90 | -4.94 | -0.04 | 175.6 | 176.1 | +0.5 | 0.005 | 2.29 |  |
| 10.0 | -8.60 | -8.31 | +0.29 | 154.4 | 152.3 | -2.1 | 0.005 | 1.46 |  |
| 12.6 | -12.30 | -12.37 | -0.07 | 134.9 | 129.9 | -5.0 | 0.005 | 1.16 | arg |
| 15.8 | -10.00 | -11.45 | -1.45 | 128.3 | 126.5 | -1.8 | 0.005 | 1.15 | abs(L) |
| 20.0 | -23.30 | -24.54 | -1.24 | 173.7 | 148.5 | -25.2 | 0.005 | 1.05 | abs(L) arg |
| 25.1 | -16.40 | -16.64 | -0.24 | 113.7 | 109.3 | -4.4 | 0.005 | 1.04 |  |
| 31.6 | -20.00 | -20.96 | -0.96 | -5.4 | -16.1 | -10.7 | 0.005 | 0.921 |  |
| 39.8 | -21.90 | -21.82 | +0.08 | -142.6 | -140.4 | +2.2 | 0.005 | 1.06 |  |
| 50.1 | -24.80 | -26.65 | -1.85 | -46.4 | -57.0 | -10.6 | 0.005 | 0.975 |  |

- PM: 25.29 vs primary 25.35 deg (delta -0.06)
- Crossover: 4.547 vs primary 4.469 Hz
- GM: 4.38 vs primary 4.28 dB (delta +0.10)
- Bins out of tolerance (<=20 Hz): abs(L) 5, arg 4
- **Verdict: DISAGREE**

