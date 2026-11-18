# T183 second key: x-axis pinj loop FRF (independent check)

Script: `indi_flight/bench/t183_xy_frf_key.py` (run: `python3 -I indi_flight/bench/t183_xy_frf_key.py`).
Inputs: `pt0_ax1_r400_s1_pinj.csv`, `pt1_ax1_r400_s1_pinj.csv` (this directory).

## Method

- Samples are not uniform (dt 7.5-21 ms, median 11.25 ms, ~88.9 Hz). No resampling: for each whole
  Tp = 10 s period, a least-squares fit of DC plus cos/sin at k/Tp (k = 1..80, i.e. 0.1-8 Hz) on the
  true timestamps gives the complex harmonic coefficients.
- Record span 49.99 s = 5 periods; period 0 dropped (transient); periods 1-4 averaged.
- Cross/auto spectra averaged over the 4 periods. Coherence uses the same 4 realisations, so it is
  noisy and biased upward for small averages (expected bias about 1/4 for unrelated signals).
- Excited bins: the 16 multisine bins (k = 2,3,4,5,6,8,10,13,16,20,25,32,40,50,63,80, i.e. 0.2-8 Hz,
  log-spaced). Only these bins are reported.

## Column choice

- `d` = excitation r. It is the only periodic channel: corr(d(t), d(t+Tp)) = 1.000 for both files.
  `x` gives 0.95/0.97 and `y` gives 0.81/0.86 at lag Tp, so both carry non-periodic content.
- `x` = loop input e (signal entering the break, |x/r| ~ 1 at high frequency).
- `y` = loop output / returning signal.
- Identity check: x - r - y has relative residual 5e-8 (both files), i.e. x = r + y holds sample-wise.

## Sign choice

- With x = r + y and Y = G X (G = Y/X the forward path), X = R/(1 - G). The measured sensitivity
  x/r therefore equals 1/(1 + L) with **L = -Y/X = -G**. The sign is fixed by this identity, not by
  convention: the data give x/r = 1/(1-G) at the excited bins (checked at 1 Hz: |x/r| = 1.18, arg 14 deg
  from the data; 1/(1-G) gives the same).
- Phase margin PM = 180 + arg(L) (deg, unwrapped) with L = -G. Using +G would shift the phase by 180 deg
  and is not the sensitivity the data measure.
- Estimator: primary is r-referenced, L = Srr/Srx - 1 (from S = x/r = Srx/Srr, with r the clean
  reference). The H1 estimate (-Sxy/Sxx) is also reported. It is biased low at low frequency by output
  noise (|L| 1.07 vs 1.26 at 0.2 Hz, pt0; ratio H1/r-ref 0.84-1.00 over the excited bins).

## Results

Excited bins at the claim frequencies (r-referenced |L|, arg(L) deg, coherences; H1 |L| in brackets):

| CSV | f [Hz] | abs(L) | arg(L) [deg] | coh(r,x) | coh(r,y) | coh(x,y) |
|---|---|---|---|---|---|---|
| pt0 | 0.20 | 1.261 (1.065) | -112.3 | 0.747 | 0.825 | 0.786 |
| pt0 | 0.30 | 1.193 (1.068) | -123.3 | 0.782 | 0.836 | 0.857 |
| pt0 | 0.40 | 0.737 (0.729) | -125.8 | 0.939 | 0.893 | 0.932 |
| pt0 | 0.50 | 0.690 (0.689) | -130.3 | 0.992 | 0.984 | 0.991 |
| pt0 | 1.00 | 0.272 (0.272) | -131.1 | 0.999 | 0.982 | 0.987 |
| pt0 | 2.00 | 0.160 (0.160) | -165.0 | 1.000 | 0.992 | 0.995 |
| pt1 | 0.20 | 1.246 (1.085) | -119.6 | 0.758 | 0.830 | 0.829 |
| pt1 | 0.30 | 0.919 (0.898) | -128.4 | 0.920 | 0.907 | 0.940 |
| pt1 | 0.40 | 0.776 (0.767) | -121.9 | 0.961 | 0.937 | 0.953 |
| pt1 | 0.50 | 0.427 (0.429) | -123.9 | 0.982 | 0.911 | 0.938 |
| pt1 | 1.00 | 0.265 (0.266) | -119.5 | 0.999 | 0.984 | 0.987 |
| pt1 | 2.00 | 0.151 (0.151) | -160.2 | 1.000 | 0.981 | 0.986 |

Crossover |L| = 1 (log interpolation between excited bins) and PM:

- pt0: fc = 0.333 Hz (between 0.30 and 0.40 Hz), arg(L) = -124.2 deg, **PM = 55.8 deg**.
- pt1: fc = 0.268 Hz (between 0.20 and 0.30 Hz), arg(L) = -126.0 deg, **PM = 54.0 deg**.

The bin grid is coarse near crossover (0.1 Hz steps), so fc is resolved only to about +/-0.05 Hz.

## Claims

1. **|L| about 1.26 / 0.74 / 0.27 at 0.2 / 0.4 / 1 Hz: AGREE.** r-referenced: pt0 1.261 / 0.737 / 0.272;
   pt1 1.246 / 0.776 / 0.265. The 0.2 Hz value depends on estimator (H1 gives 1.07-1.09), so the
   claimed 1.26 is the r-referenced number.
2. **Crossover about 0.35 Hz: DISAGREE as a single value.** pt0 gives 0.33 Hz (close), pt1 gives 0.27 Hz.
3. **PM about 55 deg: AGREE.** pt0 55.8 deg, pt1 54.0 deg.
4. **Bins below 0.5 Hz have low coherence: DISAGREE as stated.** Coherence is reduced only at 0.2-0.3 Hz
   (coh(r,x) 0.75-0.78 in pt0, 0.76-0.92 in pt1, with 4 averages). At 0.4 Hz it is 0.94-0.96
   and at 0.5 Hz 0.98-0.99.
