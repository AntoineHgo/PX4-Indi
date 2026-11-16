# Second-key stability margin check (stage 2, S37)

Independent re-implementation of the margin definitions (`margins_est.margins` was only introspected for signature and return keys; its source was not used).

Reference: analytic L on 200000 log points, 0.05-200 Hz; sign changes of |L|-1 (gain crossovers) and of Im(L) with Re(L)<0 (phase crossovers, equivalent to angle = -180 + k*360); roots refined by log-domain bisection on the analytic expression. PM wrapped into (-180, 180]; DM = PM[rad]/w_c; GM = -20 log10|L| at phase crossovers; min over crossings.
Repo: `margins(w, L)` with defaults, fed 100 samples at 40 bins/decade over 0.2-60 Hz.
Tolerances: GM 1 dB, PM 3 deg, DM 0.3 ms, identical gain-crossover count inside 0.2-60 Hz.

## Reference values

| Case | T [s] | GM full [dB] | PM full [deg] | DM full [ms] | N_gc full | N_pc full | GM in-band | PM in-band | DM in-band [ms] | N_gc in-band | N_pc in-band |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 0.001250 | 15.18 | 67.79 | 60.29 | 1 | 2 | 15.18 | 67.79 | 60.29 | 1 | 1 |
| A | 0.002500 | 13.82 | 65.68 | 58.41 | 1 | 3 | 13.82 | 65.68 | 58.41 | 1 | 1 |
| A | 0.003750 | 12.66 | 63.58 | 56.54 | 1 | 3 | 12.66 | 63.58 | 56.54 | 1 | 1 |
| B | n/a | -0.40 | -102.48 | -18.23 | 1 | 1 | -0.40 | -102.48 | -18.23 | 1 | 1 |
| C | n/a | 31.99 | 61.09 | 133.00 | 1 | 1 | 31.99 | 61.09 | 133.00 | 1 | 1 |

## Reference (in-band) vs repo

| Case | T [s] | GM ref / repo [dB] | PM ref / repo [deg] | DM ref / repo [ms] | N_gc ref / repo | Verdict |
|---|---|---|---|---|---|---|
| A | 0.001250 | 15.18 / 15.18 | 67.79 / 67.79 | 60.29 / 60.29 | 1 / 1 | AGREE [out-of-band crossings exist in full range] |
| A | 0.002500 | 13.82 / 13.82 | 65.68 / 65.68 | 58.41 / 58.41 | 1 / 1 | AGREE [out-of-band crossings exist in full range] |
| A | 0.003750 | 12.66 / 12.66 | 63.58 / 63.58 | 56.54 / 56.54 | 1 / 1 | AGREE [out-of-band crossings exist in full range] |
| B | n/a | -0.40 / -0.40 | -102.48 / -102.26 | -18.23 / -18.19 | 1 / 1 | AGREE |
| C | n/a | 31.99 / 31.99 | 61.09 / 61.09 | 133.00 / 133.00 | 1 / 1 | AGREE |

## Crossing detail

- Case A, T=0.001250: ref gain-xover Hz (in-band) [3.1]; repo [3.1]. Ref full-range gain-xover Hz [3.1]. Ref phase-xover Hz (in-band) [13.8]; repo [13.8]. Ref phase-xover Hz (full) [13.8, 103.7].
- Case A, T=0.002500: ref gain-xover Hz (in-band) [3.1]; repo [3.1]. Ref full-range gain-xover Hz [3.1]. Ref phase-xover Hz (in-band) [12.3]; repo [12.3]. Ref phase-xover Hz (full) [12.3, 87.5, 171.5].
- Case A, T=0.003750: ref gain-xover Hz (in-band) [3.1]; repo [3.1]. Ref full-range gain-xover Hz [3.1]. Ref phase-xover Hz (in-band) [11.2]; repo [11.2]. Ref phase-xover Hz (full) [11.2, 75.8, 148.0].
- Case B, T=n/a: ref gain-xover Hz (in-band) [15.6]; repo [15.6]. Ref full-range gain-xover Hz [15.6]. Ref phase-xover Hz (in-band) [11.6]; repo [11.6]. Ref phase-xover Hz (full) [11.6].
- Case C, T=n/a: ref gain-xover Hz (in-band) [1.3]; repo [1.3]. Ref full-range gain-xover Hz [1.3]. Ref phase-xover Hz (in-band) [16.0]; repo [16.0]. Ref phase-xover Hz (full) [16.0].

