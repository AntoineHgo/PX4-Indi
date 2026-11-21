# G2 phase-plateau GM at the stage-6 freeze cells (S164)

Script: `indi_flight/bench/g2_plateau_gm_s164.py` (no args). Rule (GATES G2 Pass): pass = PM >= 45 deg and min(GM, plateau GM) >= 6 dB; plateau GM = -20 log10(max |L|) over coherent kept bins with arg L within 10 deg of -180 deg.

## Method

- Estimator: `margins_est.frf_periodic` + `margins_from_frf` (primary), called as each cell's CSV script did (rate: m3a_margins_pretest.py, Tp 10, 1-60 Hz, fs 800/400 from the cell name; outer: pinj_csv.estimate, z Tp 10 s, xy Tp 20 s, 0.2-8 Hz; both discard 1).
- Attitude: window CSVs were not kept (ulg only); the stored FRF table `*_att.csv` (f, |L| dB, unwrapped arg, accepted, %.9g) is rebuilt into L and passed to `margins_est.margins` as `margins_from_frf` does (Tp 10, 0.2-20 Hz).
- Bins used: the estimator's `accepted` bins (coherence >= 0.8, >= 0.9 within a decade of each crossover).
- Phase wrapping: `unwrap(angle(L))` ascending over accepted bins (same as margins_est), distance to -180 deg mod 360 = |((arg + 360) mod 360) - 180| <= 10 deg (equivalently any -180 + 360 k).
- Plateau GM on measured bins (gate value); a dense check on the margins_est cubic-spline curve (20000 pts) is listed as 'dense'. 'f_plat' = frequency of the plateau minimum (largest |L| inside the plateau).
- Pass: PM >= 45 and min(GM, plateau) >= 6 dB; NaN ignored; both NaN -> 'PASS(n/a GM)' (no -180 +-10 deg anywhere in the coherent band).

## Self-test

- plateau -175 deg, |L| = -8 dB, no crossing: classic GM = nan, plateau GM = 8.00 dB (expect NaN / 8.00): OK
- clean crossing (exact GM 14.38 dB): classic GM 14.38, plateau GM 14.38 dB over 2 bins at 5.00 Hz, dense 13.36 dB (need plateau >= GM - 1 dB): OK

Self-test: PASS

## Reproduction of existing margins

- rate: 31 cells, max |dPM| 3.98e-13 deg, max |dGM| 3.93e-13 dB, NaN mismatches none, outside 0.01: none
- att: 12 cells, max |dPM| 5.17e-07 deg, max |dGM| 1.77e-07 dB, NaN mismatches none, outside 0.01: none
- outer: 24 cells, max |dPM| 4.93e-07 deg, max |dGM| 5.92e-09 dB, NaN mismatches none, outside 0.01: none

Reproduction: ALL cells within 0.01 deg / 0.01 dB

## Table

| loop | cell | bins | PM deg | GM dB | plateau GM dB | f_plat Hz | n_plat | dense plateau dB | plateau, |L|<1 only dB | min dB | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rate | pitch400_mo_s1 | 18/18 | 54.8 | 12.1 | 10.8 | 12.60 | 2 | 10.7 | 10.8 | 10.8 | PASS |
| rate | pitch400_mo_s2 | 18/18 | 54.5 | 12.1 | 10.7 | 12.60 | 2 | 10.7 | 10.7 | 10.7 | PASS |
| rate | pitch400_s1 | 18/18 | 55.9 | 15.1 | 15.0 | 25.10 | 1 | 14.5 | 15.0 | 15.0 | PASS |
| rate | pitch400_s2 | 18/18 | 56.0 | 15.5 | 15.3 | 25.10 | 1 | 14.7 | 15.3 | 15.3 | PASS |
| rate | pitch400_s3 | 18/18 | 55.9 | 15.4 | 15.2 | 25.10 | 1 | 14.5 | 15.2 | 15.2 | PASS |
| rate | pitch800_mo_s1 | 18/18 | 55.8 | 13.7 | 13.7 | 15.80 | 1 | 12.3 | 13.7 | 13.7 | PASS |
| rate | pitch800_mo_s2 | 18/18 | 55.8 | 13.8 | 13.8 | 15.80 | 1 | 12.3 | 13.8 | 13.8 | PASS |
| rate | pitch800_s1 | 18/18 | 56.4 | 18.8 | 18.5 | 25.10 | 1 | 17.6 | 18.5 | 18.5 | PASS |
| rate | pitch800_s2 | 18/18 | 56.0 | 18.6 | 18.5 | 25.10 | 1 | 17.5 | 18.5 | 18.5 | PASS |
| rate | pitch800_s3 | 18/18 | 55.9 | 18.9 | 18.8 | 25.10 | 1 | 17.5 | 18.8 | 18.8 | PASS |
| rate | roll400_mo_s1 | 18/18 | 54.6 | 11.8 | 10.7 | 12.60 | 2 | 10.6 | 10.7 | 10.7 | PASS |
| rate | roll400_mo_s2 | 18/18 | 54.7 | 11.9 | 10.8 | 12.60 | 2 | 10.6 | 10.8 | 10.8 | PASS |
| rate | roll400_s1 | 18/18 | 56.1 | 15.4 | 15.0 | 25.10 | 1 | 14.5 | 15.0 | 15.0 | PASS |
| rate | roll400_s2 | 18/18 | 55.1 | 15.5 | 15.2 | 25.10 | 1 | 14.5 | 15.2 | 15.2 | PASS |
| rate | roll400_s3 | 18/18 | 56.1 | 14.2 | 14.2 | 25.10 | 1 | 13.4 | 14.2 | 14.2 | PASS |
| rate | roll800_fwdef_s1 | 18/18 | 54.4 | 15.9 | 16.7 | 20.00 | 1 | 14.5 | 16.7 | 15.9 | PASS |
| rate | roll800_fwdef_s2 | 18/18 | 54.3 | 16.4 | 17.0 | 20.00 | 1 | 14.7 | 17.0 | 16.4 | PASS |
| rate | roll800_fwdef_s3 | 18/18 | 54.3 | 16.3 | 16.8 | 20.00 | 1 | 14.7 | 16.8 | 16.3 | PASS |
| rate | roll800_mo_s1 | 18/18 | 55.9 | 13.8 | 13.7 | 15.80 | 1 | 12.4 | 13.7 | 13.7 | PASS |
| rate | roll800_mo_s2 | 18/18 | 56.1 | 13.8 | 13.8 | 15.80 | 1 | 12.1 | 13.8 | 13.8 | PASS |
| rate | roll800_s1 | 18/18 | 56.4 | 19.3 | 18.8 | 25.10 | 1 | 17.4 | 18.8 | 18.8 | PASS |
| rate | roll800_s2 | 18/18 | 56.2 | 18.8 | 18.4 | 25.10 | 1 | 17.7 | 18.4 | 18.4 | PASS |
| rate | roll800_s3 | 18/18 | 56.5 | 18.7 | 18.7 | 25.10 | 1 | 17.3 | 18.7 | 18.7 | PASS |
| rate | yaw400_mo_s1 | 18/18 | 75.8 | 17.0 | 17.8 | 20.00 | 1 | 15.4 | 17.8 | 17.0 | PASS |
| rate | yaw400_mo_s2 | 18/18 | 75.4 | 17.0 | 17.7 | 20.00 | 1 | 15.3 | 17.7 | 17.0 | PASS |
| rate | yaw400_s1 | 18/18 | 80.8 | 15.3 | NaN | NaN | 0 | 14.4 | NaN | 15.3 | PASS |
| rate | yaw400_s2 | 18/18 | 81.5 | 15.3 | NaN | NaN | 0 | 14.4 | NaN | 15.3 | PASS |
| rate | yaw800_mo_s1 | 18/18 | 76.1 | 18.0 | 17.7 | 20.00 | 1 | 16.1 | 17.7 | 17.7 | PASS |
| rate | yaw800_mo_s2 | 18/18 | 76.2 | 18.0 | 17.7 | 20.00 | 1 | 16.3 | 17.7 | 17.7 | PASS |
| rate | yaw800_s1 | 18/18 | 79.0 | 19.9 | 20.2 | 31.60 | 1 | 18.7 | 20.2 | 19.9 | PASS |
| rate | yaw800_s2 | 18/18 | 79.2 | 19.8 | 20.2 | 31.60 | 1 | 18.6 | 20.2 | 19.8 | PASS |
| att | ax1_r400_s1 | 19/20 | 54.0 | 19.9 | 16.0 | 5.00 | 2 | 15.5 | 16.0 | 16.0 | PASS |
| att | ax1_r400_s2 | 20/20 | 54.2 | 19.6 | 16.0 | 5.00 | 2 | 15.4 | 16.0 | 16.0 | PASS |
| att | ax1_r800_s1 | 20/20 | 54.7 | 20.2 | 19.3 | 6.30 | 2 | 17.2 | 19.3 | 19.3 | PASS |
| att | ax1_r800_s2 | 19/20 | 54.5 | 20.3 | 19.1 | 6.30 | 2 | 16.6 | 19.1 | 19.1 | PASS |
| att | ax2_r400_s1 | 20/20 | 53.4 | 19.2 | 16.2 | 5.00 | 2 | 15.4 | 16.2 | 16.2 | PASS |
| att | ax2_r400_s2 | 19/20 | 53.9 | 19.7 | 16.1 | 5.00 | 2 | 15.4 | 16.1 | 16.1 | PASS |
| att | ax2_r800_s1 | 20/20 | 54.9 | 20.9 | 19.4 | 6.30 | 2 | 17.1 | 19.4 | 19.4 | PASS |
| att | ax2_r800_s2 | 20/20 | 54.1 | 20.2 | -18.5 | 0.20 | 3 | -18.5 | 19.0 | -18.5 | FAIL |
| att | ax3_r400_s1 | 20/20 | 81.4 | 30.8 | 28.6 | 6.30 | 2 | 27.4 | 28.6 | 28.6 | PASS |
| att | ax3_r400_s2 | 20/20 | 81.4 | 30.9 | 28.6 | 6.30 | 2 | 27.3 | 28.6 | 28.6 | PASS |
| att | ax3_r800_s1 | 20/20 | 81.4 | 30.5 | 27.8 | 6.30 | 2 | 27.6 | 27.8 | 27.8 | PASS |
| att | ax3_r800_s2 | 20/20 | 81.3 | 30.5 | 27.8 | 6.30 | 2 | 27.6 | 27.8 | 27.8 | PASS |
| outer | pt0_ax1_r400_s1 | 17/17 | 51.0 | 16.4 | NaN | NaN | 0 | 15.6 | NaN | 16.4 | PASS |
| outer | pt0_ax1_r400_s2 | 17/17 | 52.2 | 16.4 | NaN | NaN | 0 | 15.5 | NaN | 16.4 | PASS |
| outer | pt0_ax1_r800_s1 | 17/17 | 54.1 | 16.8 | 17.8 | 2.50 | 1 | 15.8 | 17.8 | 16.8 | PASS |
| outer | pt0_ax1_r800_s2 | 17/17 | 56.8 | 16.9 | 17.9 | 2.50 | 1 | 15.8 | 17.9 | 16.9 | PASS |
| outer | pt0_ax2_r400_s1 | 17/17 | 57.5 | 16.3 | NaN | NaN | 0 | 15.4 | NaN | 16.3 | PASS |
| outer | pt0_ax2_r400_s2 | 17/17 | 55.2 | 16.3 | NaN | NaN | 0 | 15.4 | NaN | 16.3 | PASS |
| outer | pt0_ax2_r800_s1 | 17/17 | 55.8 | 16.8 | 17.8 | 2.50 | 1 | 15.8 | 17.8 | 16.8 | PASS |
| outer | pt0_ax2_r800_s2 | 17/17 | 52.4 | 16.8 | 17.8 | 2.50 | 1 | 15.8 | 17.8 | 16.8 | PASS |
| outer | pt0_ax3_r400_s1 | 15/16 | 70.9 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt0_ax3_r400_s2 | 14/16 | 67.9 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt0_ax3_r800_s1 | 14/16 | 70.5 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt0_ax3_r800_s2 | 13/16 | 66.1 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt1_ax1_r400_s1 | 15/17 | 54.0 | 16.6 | NaN | NaN | 0 | 16.2 | NaN | 16.6 | PASS |
| outer | pt1_ax1_r400_s2 | 16/17 | 63.0 | 16.7 | 17.6 | 2.50 | 1 | 16.0 | 17.6 | 16.7 | PASS |
| outer | pt1_ax1_r800_s1 | 16/17 | 59.7 | 17.3 | 18.0 | 2.50 | 1 | 16.5 | 18.0 | 17.3 | PASS |
| outer | pt1_ax1_r800_s2 | 16/17 | 67.1 | 17.2 | 17.9 | 2.50 | 1 | 16.5 | 17.9 | 17.2 | PASS |
| outer | pt1_ax2_r400_s1 | 16/17 | 67.7 | 16.8 | 17.7 | 2.50 | 1 | 16.0 | 17.7 | 16.8 | PASS |
| outer | pt1_ax2_r400_s2 | 16/17 | 62.8 | 16.7 | 17.8 | 2.50 | 1 | 15.8 | 17.8 | 16.7 | PASS |
| outer | pt1_ax2_r800_s1 | 16/17 | 61.0 | 16.8 | 17.8 | 2.50 | 1 | 15.8 | 17.8 | 16.8 | PASS |
| outer | pt1_ax2_r800_s2 | 15/17 | 63.8 | 17.3 | 18.1 | 2.50 | 1 | 16.2 | 18.1 | 17.3 | PASS |
| outer | pt1_ax3_r400_s1 | 12/16 | 64.2 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt1_ax3_r400_s2 | 11/16 | 63.8 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt1_ax3_r800_s1 | 12/16 | 64.2 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |
| outer | pt1_ax3_r800_s2 | 12/16 | 62.3 | NaN | NaN | NaN | 0 | NaN | NaN | NaN | PASS(n/a GM) |

## Worst cell per loop (by min(GM, plateau); PM worst listed separately)

- rate: worst min(GM, plateau) = 10.7 dB (roll400_mo_s1; GM 11.8, plateau 10.7); worst PM = 54.3 deg (roll800_fwdef_s2); fails: none
- att: worst min(GM, plateau) = -18.5 dB (ax2_r800_s2; GM 20.2, plateau -18.5); worst PM = 53.4 deg (ax2_r400_s1); fails: ['ax2_r800_s2']
- outer: worst min(GM, plateau) = 16.3 dB (pt0_ax2_r400_s1; GM 16.3, plateau NaN); worst PM = 51.0 deg (pt0_ax1_r400_s1); fails: none

Verdict changes versus classic-GM-only pass (literal gate rule): ax2_r800_s2

Low-frequency artefact check: plateau minima with |L| > 1 (plateau GM < 0 dB, i.e. a bin ABOVE unity gain whose phase is within 10 deg of -180): ax2_r800_s2 (plateau -18.5 dB at 0.20 Hz).
These are not a gain-increase stability margin (|L| > 1 there is the normal low-frequency region of an integrating loop; the Nyquist encirclement count is unchanged unless the phase crosses -180 deg while |L| > 1). The literal gate rule counts them; the column 'plateau, |L|<1 only' restricts the plateau to bins below unity gain. Verdicts with that restriction: ax2_r800_s2 PASS.


## Disposition (orchestrator, S164)
Literal rule: 66/67 cells PASS; att ax2_r800_s2 "FAIL" at 0.2 Hz where |L| = +18.5 dB, arg -170.9 deg. Below
crossover a bin with |L| > 1 near -180 deg is a gain-REDUCTION margin (the loop goes unstable only if the gain drops
by 18.5 dB), not a gain margin; -20log10|L| < 0 there is a defect of the formula, not a margin. Gate fix proposed
(Q13, gate change after first test): plateau GM over bins with |L| < 1; bins with |L| > 1 within 10 deg of -180
reported as gain-reduction margin 20log10|L| with the same >= 6 dB threshold. Under it all 67 cells PASS (ax2_r800_s2:
plateau 19.0 dB, reduction margin 18.5 dB). Outer plateau values keyed by key2 (g2_outer_freeze_s163/key2.md);
rate/attitude plateau values UNKEYED (attitude from the stored FRF table, not re-estimated from the ulg).
