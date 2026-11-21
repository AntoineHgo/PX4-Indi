# G2 outer-loop margins: independent second key (S164)

## Method

- Window: periods 2..5 (first period discarded), time-based non-uniform DFT at m/Tp (trapezoid weights) per period; Tp=10 s (ax3), 20 s (ax1/2).
- Excited bins: |D| > 0.1 max over m/Tp in [0.2, 8] Hz, found from the period-averaged DFT of d.
- FRF: cross-spectral G_xd, G_yd over the 4 periods; L = -G_yd/G_xd. Coherence per bin of x and y vs periodic d across the 4 periods; keep bins with both >= 0.8.
- Margins: linear interpolation of log|L| and unwrapped phase vs log f between consecutive KEPT bins. Crossovers |L|=1 -> PM = 180+arg L (wrapped), DM = PM/wc (min over crossovers). GM = min over -180 (mod 360) crossings of -20log10|L|. Plateau GM = min over kept bins with |arg L + 180| <= 10 deg of -20log10|L|. Ms = max 1/|1+L| on the interpolated fine grid (kept-bin span).
- 'GM' = NaN means no -180 crossing between kept bins in band.

## Self-test: PASS

Synthetic discrete loop L(z)=K Ts(1-a)z^-m/((1-z^-1)(1-a z^-1)) at 88.9 Hz, d injected at summing point, process + measurement noise, 400 Hz timestamp quantisation as in the logs; tolerances 1 deg / 0.5 dB / 5 %. Analytic reference = dense-grid margins of exact L(e^jwTs).

- A finite GM/PM (delay): PASS (kept 29/29 bins)
    PM est 69.394 ana 69.463 err 0.069 deg; GM est 15.052 ana 15.021 err 0.031 dB; DM est 0.205 ana 0.204 err 0.004; plateauGM est 14.707 ana 14.669; min(GM,pl) est 14.707 ana 14.669
- B no -180 crossing in band: PASS (kept 29/29 bins)
    PM est 88.419 ana 88.770 err 0.351 deg; GM none/none dB; DM est 0.516 ana 0.516 err 0.000; plateauGM none/none; min(GM,pl) est nan ana nan
- C phase plateau near -180: PASS (kept 24/25 bins)
    PM est 22.566 ana 22.396 err 0.170 deg; GM est 34.364956348442526 vs ana nan (spurious noise crossing at tiny |L|, accepted if >= 20 dB; gate value is min(GM, plateau GM) below) dB; DM est 0.103 ana 0.103 err 0.007; plateauGM est 15.344 ana 15.159; min(GM,pl) est 15.344 ana 15.159
- D z-axis Tp=10: PASS (kept 25/25 bins)
    PM est 65.962 ana 65.943 err 0.019 deg; GM est 15.673 ana 15.516 err 0.157 dB; DM est 0.149 ana 0.148 err 0.004; plateauGM est 14.414 ana 14.280; min(GM,pl) est 14.414 ana 14.280

## Own results (written before the primary values are read)

| cell | kept/exc | PM deg | GM dB | plateau GM dB | min(GM,pl) dB | DM ms | Ms |
|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 15/17 | 40.59 | 11.31 | 11.52 | 11.31 | 215.5 | 1.586 |
| pt0_ax1_r400_s2 | 15/17 | 40.31 | 11.73 | 11.88 | 11.73 | 206.7 | 1.536 |
| pt0_ax1_r800_s1 | 17/17 | 39.79 | 12.04 | 12.19 | 12.04 | 202.8 | 1.513 |
| pt0_ax1_r800_s2 | 16/17 | 41.70 | 12.01 | -10.86 | -10.86 | 212.8 | 1.549 |
| pt0_ax2_r400_s1 | 16/17 | 38.60 | 11.55 | 11.87 | 11.55 | 190.2 | 1.538 |
| pt0_ax2_r400_s2 | 16/17 | 43.81 | 11.70 | 11.91 | 11.70 | 221.7 | 1.525 |
| pt0_ax2_r800_s1 | 16/17 | 42.60 | 12.19 | 12.46 | 12.19 | 216.5 | 1.664 |
| pt0_ax2_r800_s2 | 16/17 | 42.63 | 11.71 | 11.95 | 11.71 | 204.6 | 1.557 |
| pt0_ax3_r400_s1 | 16/16 | 65.98 | NaN | NaN | NaN | 253.3 | 1.200 |
| pt0_ax3_r400_s2 | 15/16 | 67.83 | NaN | NaN | NaN | 255.5 | 1.189 |
| pt0_ax3_r800_s1 | 15/16 | 68.93 | NaN | NaN | NaN | 282.5 | 1.186 |
| pt0_ax3_r800_s2 | 15/16 | 67.78 | NaN | 28.73 | 28.73 | 277.0 | 1.187 |
| pt1_ax1_r400_s1 | 15/17 | 47.06 | 12.36 | 12.33 | 12.33 | 247.2 | 1.461 |
| pt1_ax1_r400_s2 | 15/17 | 42.32 | 12.25 | 12.33 | 12.25 | 223.9 | 1.500 |
| pt1_ax1_r800_s1 | 16/17 | 42.43 | 12.54 | 12.48 | 12.48 | 225.2 | 1.484 |
| pt1_ax1_r800_s2 | 16/17 | 46.92 | 12.58 | 12.61 | 12.58 | 235.7 | 1.457 |
| pt1_ax2_r400_s1 | 15/17 | 44.85 | 12.18 | 12.13 | 12.13 | 234.5 | 1.453 |
| pt1_ax2_r400_s2 | 15/17 | 44.02 | 12.28 | 12.21 | 12.21 | 226.7 | 1.445 |
| pt1_ax2_r800_s1 | 15/17 | 44.54 | 12.81 | 12.51 | 12.51 | 234.0 | 1.472 |
| pt1_ax2_r800_s2 | 15/17 | 44.27 | 12.51 | 12.55 | 12.51 | 229.7 | 1.455 |
| pt1_ax3_r400_s1 | 7/16 | 63.33 | NaN | NaN | NaN | 256.1 | 1.280 |
| pt1_ax3_r400_s2 | 16/16 | 61.01 | 17.86 | NaN | 17.86 | 243.6 | 1.249 |
| pt1_ax3_r800_s1 | 0/16 | NaN | NaN | NaN | NaN | NaN | NaN |
| pt1_ax3_r800_s2 | 2/16 | 62.42 | NaN | NaN | NaN | 256.3 | 1.044 |

## Comparison with primary (*_margins.json)

| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |
|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 40.59/40.03/0.56 | 11.31/11.34/-0.04 | 215.5/214.5 | 1.586/1.602 | agree |
| pt0_ax1_r400_s2 | 40.31/41.73/-1.42 | 11.73/11.75/-0.02 | 206.7/221.2 | 1.536/1.525 | agree |
| pt0_ax1_r800_s1 | 39.79/39.51/0.29 | 12.04/12.05/-0.01 | 202.8/205.2 | 1.513/1.510 | agree |
| pt0_ax1_r800_s2 | 41.70/41.97/-0.27 | 12.01/12.11/-0.10 | 212.8/216.9 | 1.549/1.567 | agree |
| pt0_ax2_r400_s1 | 38.60/38.42/0.18 | 11.55/11.40/0.15 | 190.2/189.1 | 1.538/1.541 | agree |
| pt0_ax2_r400_s2 | 43.81/45.95/-2.14 | 11.70/11.62/0.07 | 221.7/234.7 | 1.525/1.561 | agree |
| pt0_ax2_r800_s1 | 42.60/39.97/2.63 | 12.19/12.37/-0.18 | 216.5/208.5 | 1.664/1.639 | agree |
| pt0_ax2_r800_s2 | 42.63/43.73/-1.10 | 11.71/11.59/0.12 | 204.6/207.6 | 1.557/1.561 | agree |
| pt0_ax3_r400_s1 | 65.98/71.13/-5.15 | NaN/NaN/NaN | 253.3/282.0 | 1.200/1.200 | BLOCKED |
| pt0_ax3_r400_s2 | 67.83/68.55/-0.72 | NaN/NaN/NaN | 255.5/257.5 | 1.189/1.188 | agree |
| pt0_ax3_r800_s1 | 68.93/68.32/0.62 | NaN/NaN/NaN | 282.5/280.9 | 1.186/1.187 | agree |
| pt0_ax3_r800_s2 | 67.78/64.24/3.54 | NaN/NaN/NaN | 277.0/270.4 | 1.187/1.189 | BLOCKED |
| pt1_ax1_r400_s1 | 47.06/47.21/-0.15 | 12.36/12.35/0.01 | 247.2/247.6 | 1.461/1.458 | agree |
| pt1_ax1_r400_s2 | 42.32/42.57/-0.24 | 12.25/12.24/0.01 | 223.9/225.8 | 1.500/1.502 | agree |
| pt1_ax1_r800_s1 | 42.43/42.97/-0.54 | 12.54/12.57/-0.03 | 225.2/227.7 | 1.484/1.477 | agree |
| pt1_ax1_r800_s2 | 46.92/47.39/-0.47 | 12.58/12.59/-0.01 | 235.7/237.2 | 1.457/1.460 | agree |
| pt1_ax2_r400_s1 | 44.85/44.70/0.15 | 12.18/12.18/-0.00 | 234.5/234.0 | 1.453/1.455 | agree |
| pt1_ax2_r400_s2 | 44.02/43.75/0.27 | 12.28/12.28/0.00 | 226.7/223.4 | 1.445/1.446 | agree |
| pt1_ax2_r800_s1 | 44.54/44.77/-0.22 | 12.81/12.86/-0.05 | 234.0/236.1 | 1.472/1.472 | agree |
| pt1_ax2_r800_s2 | 44.27/44.81/-0.54 | 12.51/12.51/-0.00 | 229.7/232.6 | 1.455/1.450 | agree |
| pt1_ax3_r400_s1 | 63.33/64.22/-0.89 | NaN/NaN/NaN | 256.1/262.5 | 1.280/1.252 | agree |
| pt1_ax3_r400_s2 | 61.01/61.48/-0.46 | 17.86/NaN/NaN | 243.6/240.4 | 1.249/1.222 | BLOCKED |
| pt1_ax3_r800_s1 | NaN/NaN/NaN | NaN/NaN/NaN | NaN/NaN | NaN/NaN | agree |
| pt1_ax3_r800_s2 | 62.42/62.96/-0.54 | NaN/NaN/NaN | 256.3/274.2 | 1.044/1.241 | agree |

BLOCKED cells (3): pt0_ax3_r400_s1, pt0_ax3_r800_s2, pt1_ax3_r400_s2
