# G2 phase-plateau GM, second key (S175, key2)

Script `indi_flight/bench/g2_plateau_key2_s175.py` (host python3, numpy only), self-test `indi_flight/bench/tests/test_g2_plateau_key2_s175.py`
(clean crossover, plateau bin below 1, bin above 1 near -180, phase wrap: all pass). Written and run before opening
`g2_plateau_s164.md` / `g2_plateau_gm_s164.py` (key1).

## Rule implemented (GATES G2 Pass + owner Q13 A)
Per run: classic GM = -20log10|L| at each arg L = -180 (mod 360) crossing (linear interpolation in log f on the unwrapped phase);
plateau GM = min of -20log10|L| over stored bins with |L| < 1 and |arg L + 180| <= 10 deg (wrapped); bins and crossings with
|L| >= 1 near -180 give a gain-reduction margin +20log10|L|. Cell pass: min(classic, plateau) >= 6 dB and every reduction margin >= 6 dB.
Cell value = worst seed. PM and DM not re-done.

## Data source per cell
- Rate cells (14 cells, 32 runs): `results/g2_freeze_s160/<cell>_s<N>/margins.txt`, lines 2-4 (f, |L| dB, arg deg of the accepted
  bins; stored at 0.1 dB / 0.1 deg resolution; 18/18 bins accepted). INVALID_* flight dirs excluded. No higher-resolution FRF is
  stored for rate cells except key2.md 2-decimal tables on 33 runs, not used. Cells: roll/pitch 800 and 400 (3 seeds), roll800_fwdef (3),
  model-only (`_mo`) roll/pitch/yaw 800/400 (2), yaw 800/400 (2), roll267 (1 seed, reported cell).
- Attitude cells (6 cells = ax1/2/3 x 400/800, 2 seeds = the "12 cells" of S162): `results/g2_att_freeze_s162/ax?_r???_s?_att.csv`
  (f_hz, L_db, arg_L_deg, accepted; 9 significant digits), accepted bins only (19-20 of 20).
- Outer cells (S163) are out of scope of this request; not examined.

## Key2 table (cell value = worst seed)
| kind | cell | seeds | classic GM | plateau GM | reduction | pass | plateau bins (all seeds) | per-seed classic/plateau | source |
|---|---|---|---|---|---|---|---|---|---|
| att | ax1_r400 | 1,2 | 19.57 | 15.99 | - | PASS | 4 | 1:19.84/15.99 2:19.57/16.05 | g2_att_freeze_s162/ax1_r400_s1_att.csv |
| att | ax1_r800 | 1,2 | 20.16 | 19.12 | - | PASS | 4 | 1:20.16/19.28 2:20.21/19.12 | g2_att_freeze_s162/ax1_r800_s1_att.csv |
| att | ax2_r400 | 1,2 | 19.17 | 16.07 | - | PASS | 4 | 1:19.17/16.22 2:19.71/16.07 | g2_att_freeze_s162/ax2_r400_s1_att.csv |
| att | ax2_r800 | 1,2 | 20.09 | 19.03 | 18.52 | PASS | 4 | 1:20.68/19.38 2:20.09/19.03 | g2_att_freeze_s162/ax2_r800_s1_att.csv |
| att | ax3_r400 | 1,2 | 30.87 | 28.55 | - | PASS | 4 | 1:30.87/28.57 2:30.91/28.55 | g2_att_freeze_s162/ax3_r400_s1_att.csv |
| att | ax3_r800 | 1,2 | 30.50 | 27.80 | - | PASS | 4 | 1:30.50/27.81 2:30.50/27.80 | g2_att_freeze_s162/ax3_r800_s1_att.csv |
| rate | pitch400 | 1,2,3 | 15.17 | 15.00 | - | PASS | 3 | 1:15.17/15.00 2:15.55/15.30 3:15.46/15.20 | g2_freeze_s160/pitch400_s1/margins.txt |
| rate | pitch400_mo | 1,2 | 12.00 | 10.70 | - | PASS | 4 | 1:12.02/10.80 2:12.00/10.70 | g2_freeze_s160/pitch400_mo_s1/margins.txt |
| rate | pitch800 | 1,2,3 | 18.66 | 18.50 | - | PASS | 3 | 1:18.87/18.50 2:18.66/18.50 3:18.91/18.80 | g2_freeze_s160/pitch800_s1/margins.txt |
| rate | pitch800_mo | 1,2 | 13.66 | 13.70 | - | PASS | 2 | 1:13.66/13.70 2:13.83/13.80 | g2_freeze_s160/pitch800_mo_s1/margins.txt |
| rate | roll267 | 1 | 11.55 | - | - | PASS | 0 | 1:11.55/- | g2_freeze_s160/roll267_s1/margins.txt |
| rate | roll400 | 1,2,3 | 14.24 | 14.20 | - | PASS | 3 | 1:15.37/15.00 2:15.48/15.20 3:14.24/14.20 | g2_freeze_s160/roll400_s1/margins.txt |
| rate | roll400_mo | 1,2 | 11.87 | 10.70 | - | PASS | 4 | 1:11.87/10.70 2:11.94/10.80 | g2_freeze_s160/roll400_mo_s1/margins.txt |
| rate | roll800 | 1,2,3 | 18.73 | 18.40 | - | PASS | 3 | 1:19.25/18.80 2:18.75/18.40 3:18.73/18.70 | g2_freeze_s160/roll800_s1/margins.txt |
| rate | roll800_fwdef | 1,2,3 | 15.84 | 16.70 | - | PASS | 3 | 1:15.84/16.70 2:16.24/17.00 3:16.23/16.80 | g2_freeze_s160/roll800_fwdef_s1/margins.txt |
| rate | roll800_mo | 1,2 | 13.78 | 13.70 | - | PASS | 2 | 1:13.86/13.70 2:13.78/13.80 | g2_freeze_s160/roll800_mo_s1/margins.txt |
| rate | yaw400 | 1,2 | 15.27 | - | - | PASS | 0 | 1:15.33/- 2:15.27/- | g2_freeze_s160/yaw400_s1/margins.txt |
| rate | yaw400_mo | 1,2 | 16.97 | 17.70 | - | PASS | 2 | 1:17.07/17.80 2:16.97/17.70 | g2_freeze_s160/yaw400_mo_s1/margins.txt |
| rate | yaw800 | 1,2 | 19.85 | 20.20 | - | PASS | 2 | 1:19.88/20.20 2:19.85/20.20 | g2_freeze_s160/yaw800_s1/margins.txt |
| rate | yaw800_mo | 1,2 | 17.97 | 17.70 | - | PASS | 2 | 1:17.97/17.70 2:17.98/17.70 | g2_freeze_s160/yaw800_mo_s1/margins.txt |

Notes: "-" = no such bin (no plateau bin below 1 / no reduction bin). Only att ax2_r800 has a reduction margin (seed 2, bin at
0.2 Hz, |L| = +18.5 dB, arg -170.9 deg; 18.52 dB >= 6). roll267 and yaw400 have no bin within 10 deg of -180 below unity, so their
value is the classic GM. roll800_fwdef plateau (16.7) > classic (15.8): the plateau minimum is the 20 Hz bin, the crossing sits
beyond it with higher |L|.

**Result: 20 cells, all 20 PASS** (14 rate + 6 attitude). Lowest cell values: roll400_mo 10.70 (rate; the plateau at 12.6 Hz),
pitch400_mo 10.70, ax1_r400 15.99 (att).

## Comparison with key1 (results/g2_plateau_s164.md, opened after the table)
Per run (31 rate + 12 att = 43 runs, roll267 is not in key1; key1's table also lists 24 outer runs, not compared). Full per-run table at the end.
- Classic GM: key2 (own interpolation of the stored bins) vs key1 GM (estimator spline value): max |d| 0.22 dB (one run), all
  within 1 dB. Differences come from linear-in-log-f interpolation on the 0.1 dB-rounded bins versus the estimator's cubic spline.
- Plateau GM (|L| < 1 only): key2 vs key1 column "plateau, |L|<1 only": max |d| 0.05 dB; the same set of runs has a plateau
  (NaN / "-" agree on all runs: yaw400 s1/s2 and roll267 none).
- Min(classic, plateau) per run: max |d| 0.16 dB, all pass/fail verdicts equal, excluding att ax2_r800_s2.
- att ax2_r800_s2: key1's literal-rule value -18.5 (bin at 0.2 Hz with |L| > 1) is the defect the Q13 A rule removes. Under the
  owner rule key2 gets plateau 19.03 (key1 19.0), reduction 18.52 (key1 18.5), classic 20.09 (key1 20.2, d -0.11): agree.
- Key1's "dense spline plateau" column (up to ~1.5 dB lower than bin values) is not part of the owner rule (bins only); key2 does
  not compute it. Not compared.
- Cell level: worst-seed values agree with key1 to <= 0.2 dB for every cell; key1 verdict 67/67 under Q13 A (outer included),
  key2 20/20 cells on rate+att. Agreement on every cell.

Unverified: rate bins are 0.1 dB / 0.1 deg rounded (no better data), attitude from stored FRF not re-estimated from the ulg (same
as key1); plateau coherence filter is the stored `accepted` flag, not re-derived; outer cells not covered.

## Per-run comparison (key1 vs key2)
| run | key1 GM | key2 classic | key1 plateau(|L|<1) | key2 plateau | key1 min | key2 min(incl. red) | d_classic | d_plateau |
|---|---|---|---|---|---|---|---|---|
| pitch400_mo_s1 | 12.1 | 12.02 | 10.8 | 10.80 | 10.8 | 10.80 | -0.08 | +0.00 |
| pitch400_mo_s2 | 12.1 | 12.00 | 10.7 | 10.70 | 10.7 | 10.70 | -0.10 | +0.00 |
| pitch400_s1 | 15.1 | 15.17 | 15.0 | 15.00 | 15.0 | 15.00 | +0.07 | +0.00 |
| pitch400_s2 | 15.5 | 15.55 | 15.3 | 15.30 | 15.3 | 15.30 | +0.05 | +0.00 |
| pitch400_s3 | 15.4 | 15.46 | 15.2 | 15.20 | 15.2 | 15.20 | +0.06 | +0.00 |
| pitch800_mo_s1 | 13.7 | 13.66 | 13.7 | 13.70 | 13.7 | 13.66 | -0.04 | +0.00 |
| pitch800_mo_s2 | 13.8 | 13.83 | 13.8 | 13.80 | 13.8 | 13.80 | +0.03 | +0.00 |
| pitch800_s1 | 18.8 | 18.87 | 18.5 | 18.50 | 18.5 | 18.50 | +0.07 | +0.00 |
| pitch800_s2 | 18.6 | 18.66 | 18.5 | 18.50 | 18.5 | 18.50 | +0.06 | +0.00 |
| pitch800_s3 | 18.9 | 18.91 | 18.8 | 18.80 | 18.8 | 18.80 | +0.01 | +0.00 |
| roll400_mo_s1 | 11.8 | 11.87 | 10.7 | 10.70 | 10.7 | 10.70 | +0.07 | +0.00 |
| roll400_mo_s2 | 11.9 | 11.94 | 10.8 | 10.80 | 10.8 | 10.80 | +0.04 | +0.00 |
| roll400_s1 | 15.4 | 15.37 | 15.0 | 15.00 | 15.0 | 15.00 | -0.03 | +0.00 |
| roll400_s2 | 15.5 | 15.48 | 15.2 | 15.20 | 15.2 | 15.20 | -0.02 | +0.00 |
| roll400_s3 | 14.2 | 14.24 | 14.2 | 14.20 | 14.2 | 14.20 | +0.04 | +0.00 |
| roll800_fwdef_s1 | 15.9 | 15.84 | 16.7 | 16.70 | 15.9 | 15.84 | -0.06 | +0.00 |
| roll800_fwdef_s2 | 16.4 | 16.24 | 17.0 | 17.00 | 16.4 | 16.24 | -0.16 | +0.00 |
| roll800_fwdef_s3 | 16.3 | 16.23 | 16.8 | 16.80 | 16.3 | 16.23 | -0.07 | +0.00 |
| roll800_mo_s1 | 13.8 | 13.86 | 13.7 | 13.70 | 13.7 | 13.70 | +0.06 | +0.00 |
| roll800_mo_s2 | 13.8 | 13.78 | 13.8 | 13.80 | 13.8 | 13.78 | -0.02 | +0.00 |
| roll800_s1 | 19.3 | 19.25 | 18.8 | 18.80 | 18.8 | 18.80 | -0.05 | +0.00 |
| roll800_s2 | 18.8 | 18.75 | 18.4 | 18.40 | 18.4 | 18.40 | -0.05 | +0.00 |
| roll800_s3 | 18.7 | 18.73 | 18.7 | 18.70 | 18.7 | 18.70 | +0.03 | +0.00 |
| yaw400_mo_s1 | 17.0 | 17.07 | 17.8 | 17.80 | 17.0 | 17.07 | +0.07 | +0.00 |
| yaw400_mo_s2 | 17.0 | 16.97 | 17.7 | 17.70 | 17.0 | 16.97 | -0.03 | +0.00 |
| yaw400_s1 | 15.3 | 15.33 | NaN | - | 15.3 | 15.33 | +0.03 |  |
| yaw400_s2 | 15.3 | 15.27 | NaN | - | 15.3 | 15.27 | -0.03 |  |
| yaw800_mo_s1 | 18.0 | 17.97 | 17.7 | 17.70 | 17.7 | 17.70 | -0.03 | +0.00 |
| yaw800_mo_s2 | 18.0 | 17.98 | 17.7 | 17.70 | 17.7 | 17.70 | -0.02 | +0.00 |
| yaw800_s1 | 19.9 | 19.88 | 20.2 | 20.20 | 19.9 | 19.88 | -0.02 | +0.00 |
| yaw800_s2 | 19.8 | 19.85 | 20.2 | 20.20 | 19.8 | 19.85 | +0.05 | +0.00 |
| ax1_r400_s1 | 19.9 | 19.84 | 16.0 | 15.99 | 16.0 | 15.99 | -0.06 | -0.01 |
| ax1_r400_s2 | 19.6 | 19.57 | 16.0 | 16.05 | 16.0 | 16.05 | -0.03 | +0.05 |
| ax1_r800_s1 | 20.2 | 20.16 | 19.3 | 19.28 | 19.3 | 19.28 | -0.04 | -0.02 |
| ax1_r800_s2 | 20.3 | 20.21 | 19.1 | 19.12 | 19.1 | 19.12 | -0.09 | +0.02 |
| ax2_r400_s1 | 19.2 | 19.17 | 16.2 | 16.22 | 16.2 | 16.22 | -0.03 | +0.02 |
| ax2_r400_s2 | 19.7 | 19.71 | 16.1 | 16.07 | 16.1 | 16.07 | +0.01 | -0.03 |
| ax2_r800_s1 | 20.9 | 20.68 | 19.4 | 19.38 | 19.4 | 19.38 | -0.22 | -0.02 |
| ax2_r800_s2 | 20.2 | 20.09 | 19.0 | 19.03 | -18.5 | 18.52 | -0.11 | +0.03 |
| ax3_r400_s1 | 30.8 | 30.87 | 28.6 | 28.57 | 28.6 | 28.57 | +0.07 | -0.03 |
| ax3_r400_s2 | 30.9 | 30.91 | 28.6 | 28.55 | 28.6 | 28.55 | +0.01 | -0.05 |
| ax3_r800_s1 | 30.5 | 30.50 | 27.8 | 27.81 | 27.8 | 27.81 | -0.00 | +0.01 |
| ax3_r800_s2 | 30.5 | 30.50 | 27.8 | 27.80 | 27.8 | 27.80 | +0.00 | +0.00 |
