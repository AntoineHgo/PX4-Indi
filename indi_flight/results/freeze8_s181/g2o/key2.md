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
| pt0_ax1_r400_s1 | 16/17 | 53.65 | 10.87 | 10.96 | 10.87 | 270.8 | 1.501 |
| pt0_ax1_r400_s2 | 17/17 | 52.47 | 10.80 | 10.88 | 10.80 | 264.1 | 1.503 |
| pt0_ax1_r800_s1 | 17/17 | 53.88 | 11.23 | 11.24 | 11.23 | 290.5 | 1.487 |
| pt0_ax1_r800_s2 | 17/17 | 53.73 | 11.28 | 11.29 | 11.28 | 281.1 | 1.493 |
| pt0_ax2_r400_s1 | 17/17 | 51.10 | 10.85 | 10.89 | 10.85 | 265.7 | 1.489 |
| pt0_ax2_r400_s2 | 17/17 | 54.88 | 10.93 | 10.95 | 10.93 | 285.0 | 1.494 |
| pt0_ax2_r800_s1 | 17/17 | 50.10 | 11.00 | 11.05 | 11.00 | 264.1 | 1.487 |
| pt0_ax2_r800_s2 | 17/17 | 50.19 | 11.20 | 11.15 | 11.15 | 271.2 | 1.489 |
| pt0_ax3_r400_s1 | 15/16 | 67.08 | NaN | 28.25 | 28.25 | 269.8 | 1.189 |
| pt0_ax3_r400_s2 | 16/16 | 66.60 | NaN | 28.08 | 28.08 | 264.4 | 1.200 |
| pt0_ax3_r800_s1 | 15/16 | 68.56 | NaN | NaN | NaN | 276.9 | 1.189 |
| pt0_ax3_r800_s2 | 15/16 | 65.12 | NaN | 28.14 | 28.14 | 248.8 | 1.183 |
| pt1_ax1_r400_s1 | 16/17 | 60.61 | 11.21 | 11.20 | 11.20 | 332.1 | 1.448 |
| pt1_ax1_r400_s2 | 17/17 | 59.37 | 11.39 | 11.31 | 11.31 | 322.1 | 1.451 |
| pt1_ax1_r800_s1 | 16/17 | 63.34 | 11.69 | 11.64 | 11.64 | 349.3 | 1.438 |
| pt1_ax1_r800_s2 | 17/17 | 57.02 | 11.69 | 11.58 | 11.58 | 310.1 | 1.448 |
| pt1_ax2_r400_s1 | 14/17 | 54.74 | 11.05 | 11.00 | 11.00 | 326.1 | 1.453 |
| pt1_ax2_r400_s2 | 15/17 | 56.54 | 11.08 | 11.00 | 11.00 | 316.9 | 1.446 |
| pt1_ax2_r800_s1 | 16/17 | 57.72 | 11.72 | 11.52 | 11.52 | 317.0 | 1.436 |
| pt1_ax2_r800_s2 | 15/17 | 56.37 | 11.60 | 11.40 | 11.40 | 317.3 | 1.436 |
| pt1_ax3_r400_s1 | 5/16 | 63.75 | NaN | NaN | NaN | 259.6 | 1.185 |
| pt1_ax3_r400_s2 | 14/16 | 59.39 | NaN | 13.96 | 13.96 | 275.6 | 1.307 |
| pt1_ax3_r800_s1 | 14/16 | 64.51 | NaN | NaN | NaN | 265.5 | 1.262 |
| pt1_ax3_r800_s2 | 5/16 | 64.16 | NaN | NaN | NaN | 259.8 | 1.288 |

## Comparison with primary (*_margins.json)

| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |
|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 53.65/54.60/-0.95 | 10.87/10.88/-0.01 | 270.8/271.3 | 1.501/1.499 | agree |
| pt0_ax1_r400_s2 | 52.47/52.76/-0.29 | 10.80/10.79/0.00 | 264.1/263.4 | 1.503/1.496 | agree |
| pt0_ax1_r800_s1 | 53.88/53.94/-0.07 | 11.23/11.23/0.01 | 290.5/291.8 | 1.487/1.481 | agree |
| pt0_ax1_r800_s2 | 53.73/54.09/-0.37 | 11.28/11.28/-0.00 | 281.1/285.5 | 1.493/1.488 | agree |
| pt0_ax2_r400_s1 | 51.10/51.41/-0.31 | 10.85/10.84/0.01 | 265.7/267.8 | 1.489/1.483 | agree |
| pt0_ax2_r400_s2 | 54.88/55.31/-0.43 | 10.93/10.92/0.01 | 285.0/286.3 | 1.494/1.491 | agree |
| pt0_ax2_r800_s1 | 50.10/49.88/0.23 | 11.00/10.98/0.02 | 264.1/266.3 | 1.487/1.482 | agree |
| pt0_ax2_r800_s2 | 50.19/50.03/0.16 | 11.20/11.20/-0.00 | 271.2/271.3 | 1.489/1.486 | agree |
| pt0_ax3_r400_s1 | 67.08/67.45/-0.37 | NaN/NaN/NaN | 269.8/276.2 | 1.189/1.189 | agree |
| pt0_ax3_r400_s2 | 66.60/63.13/3.47 | NaN/NaN/NaN | 264.4/240.1 | 1.200/1.200 | BLOCKED |
| pt0_ax3_r800_s1 | 68.56/66.86/1.70 | NaN/NaN/NaN | 276.9/289.6 | 1.189/1.194 | agree |
| pt0_ax3_r800_s2 | 65.12/64.35/0.76 | NaN/NaN/NaN | 248.8/241.1 | 1.183/1.183 | agree |
| pt1_ax1_r400_s1 | 60.61/60.78/-0.17 | 11.21/11.21/0.00 | 332.1/333.1 | 1.448/1.449 | agree |
| pt1_ax1_r400_s2 | 59.37/59.36/0.01 | 11.39/11.38/0.01 | 322.1/319.8 | 1.451/1.451 | agree |
| pt1_ax1_r800_s1 | 63.34/63.69/-0.35 | 11.69/11.69/0.00 | 349.3/351.5 | 1.438/1.436 | agree |
| pt1_ax1_r800_s2 | 57.02/57.13/-0.11 | 11.69/11.70/-0.01 | 310.1/308.8 | 1.448/1.447 | agree |
| pt1_ax2_r400_s1 | 54.74/54.29/0.45 | 11.05/11.06/-0.01 | 326.1/326.6 | 1.453/1.453 | agree |
| pt1_ax2_r400_s2 | 56.54/56.48/0.06 | 11.08/11.09/-0.01 | 316.9/316.0 | 1.446/1.445 | agree |
| pt1_ax2_r800_s1 | 57.72/57.43/0.29 | 11.72/11.69/0.02 | 317.0/314.1 | 1.436/1.434 | agree |
| pt1_ax2_r800_s2 | 56.37/56.39/-0.02 | 11.60/11.60/-0.00 | 317.3/317.1 | 1.436/1.433 | agree |
| pt1_ax3_r400_s1 | 63.75/60.15/3.59 | NaN/NaN/NaN | 259.6/256.3 | 1.185/1.282 | BLOCKED |
| pt1_ax3_r400_s2 | 59.39/61.16/-1.77 | NaN/NaN/NaN | 275.6/259.3 | 1.307/1.256 | agree |
| pt1_ax3_r800_s1 | 64.51/66.58/-2.06 | NaN/NaN/NaN | 265.5/271.6 | 1.262/1.232 | agree |
| pt1_ax3_r800_s2 | 64.16/61.95/2.21 | NaN/NaN/NaN | 259.8/248.8 | 1.288/1.264 | agree |

BLOCKED cells (2): pt0_ax3_r400_s2, pt1_ax3_r400_s1
