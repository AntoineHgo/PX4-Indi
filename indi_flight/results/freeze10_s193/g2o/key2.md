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
| pt0_ax1_r400_s1 | 17/17 | 51.67 | 13.53 | 12.95 | 12.95 | 391.5 | 1.308 |
| pt0_ax1_r400_s2 | 17/17 | 50.01 | 13.63 | 13.04 | 13.04 | 370.0 | 1.305 |
| pt0_ax1_r800_s1 | 17/17 | 52.22 | 14.04 | 13.35 | 13.35 | 395.8 | 1.299 |
| pt0_ax1_r800_s2 | 17/17 | 55.25 | 14.00 | 13.30 | 13.30 | 385.5 | 1.291 |
| pt0_ax2_r400_s1 | 17/17 | 50.14 | 13.54 | 12.88 | 12.88 | 373.3 | 1.303 |
| pt0_ax2_r400_s2 | 17/17 | 49.36 | 13.56 | 12.96 | 12.96 | 369.8 | 1.302 |
| pt0_ax2_r800_s1 | 17/17 | 51.68 | 13.98 | 13.26 | 13.26 | 386.0 | 1.291 |
| pt0_ax2_r800_s2 | 17/17 | 53.23 | 14.03 | 13.23 | 13.23 | 406.4 | 1.288 |
| pt0_ax3_r400_s1 | 15/16 | 65.65 | NaN | 27.99 | 27.99 | 268.2 | 1.190 |
| pt0_ax3_r400_s2 | 15/16 | 68.52 | NaN | 28.03 | 28.03 | 283.3 | 1.204 |
| pt0_ax3_r800_s1 | 16/16 | 67.41 | NaN | 28.03 | 28.03 | 261.9 | 1.187 |
| pt0_ax3_r800_s2 | 14/16 | 66.05 | NaN | 28.03 | 28.03 | 252.4 | 1.185 |
| pt1_ax1_r400_s1 | 16/17 | 52.61 | 13.93 | 13.27 | 13.27 | 466.7 | 1.278 |
| pt1_ax1_r400_s2 | 17/17 | 57.44 | 14.06 | 13.44 | 13.44 | 464.3 | 1.279 |
| pt1_ax1_r800_s1 | 17/17 | 67.81 | 14.51 | NaN | 14.51 | 562.9 | 1.266 |
| pt1_ax1_r800_s2 | 16/17 | 55.91 | 14.38 | NaN | 14.38 | 486.0 | 1.266 |
| pt1_ax2_r400_s1 | 15/17 | 54.19 | 13.99 | 13.20 | 13.20 | 472.9 | 1.278 |
| pt1_ax2_r400_s2 | 16/17 | 57.76 | 14.02 | NaN | 14.02 | 488.7 | 1.276 |
| pt1_ax2_r800_s1 | 15/17 | 56.22 | 14.60 | NaN | 14.60 | 477.5 | 1.260 |
| pt1_ax2_r800_s2 | 15/17 | 54.93 | 14.47 | NaN | 14.47 | 464.9 | 1.265 |
| pt1_ax3_r400_s1 | 11/16 | 63.28 | NaN | NaN | NaN | 278.7 | 1.253 |
| pt1_ax3_r400_s2 | 16/16 | 58.15 | 16.28 | NaN | 16.28 | 255.5 | 1.272 |
| pt1_ax3_r800_s1 | 14/16 | 58.92 | NaN | NaN | NaN | 230.5 | 1.268 |
| pt1_ax3_r800_s2 | 15/16 | 64.72 | 17.80 | NaN | 17.80 | 284.9 | 1.254 |

## Comparison with primary (*_margins.json)

| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |
|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 51.67/50.17/1.49 | 13.53/13.49/0.03 | 391.5/387.5 | 1.308/1.307 | agree |
| pt0_ax1_r400_s2 | 50.01/49.71/0.31 | 13.63/13.61/0.03 | 370.0/366.5 | 1.305/1.304 | agree |
| pt0_ax1_r800_s1 | 52.22/52.40/-0.17 | 14.04/14.02/0.02 | 395.8/398.7 | 1.299/1.299 | agree |
| pt0_ax1_r800_s2 | 55.25/55.33/-0.07 | 14.00/13.95/0.05 | 385.5/385.6 | 1.291/1.289 | agree |
| pt0_ax2_r400_s1 | 50.14/50.47/-0.34 | 13.54/13.46/0.07 | 373.3/377.2 | 1.303/1.302 | agree |
| pt0_ax2_r400_s2 | 49.36/49.08/0.28 | 13.56/13.52/0.04 | 369.8/366.8 | 1.302/1.301 | agree |
| pt0_ax2_r800_s1 | 51.68/51.28/0.40 | 13.98/13.94/0.04 | 386.0/383.5 | 1.291/1.291 | agree |
| pt0_ax2_r800_s2 | 53.23/53.03/0.20 | 14.03/13.97/0.06 | 406.4/404.8 | 1.288/1.286 | agree |
| pt0_ax3_r400_s1 | 65.65/66.25/-0.61 | NaN/NaN/NaN | 268.2/267.1 | 1.190/1.192 | agree |
| pt0_ax3_r400_s2 | 68.52/68.21/0.31 | NaN/NaN/NaN | 283.3/283.2 | 1.204/1.205 | agree |
| pt0_ax3_r800_s1 | 67.41/67.20/0.21 | NaN/NaN/NaN | 261.9/263.0 | 1.187/1.188 | agree |
| pt0_ax3_r800_s2 | 66.05/65.36/0.69 | NaN/NaN/NaN | 252.4/246.2 | 1.185/1.186 | agree |
| pt1_ax1_r400_s1 | 52.61/52.51/0.09 | 13.93/13.83/0.10 | 466.7/469.9 | 1.278/1.276 | agree |
| pt1_ax1_r400_s2 | 57.44/57.53/-0.10 | 14.06/14.00/0.06 | 464.3/466.1 | 1.279/1.277 | agree |
| pt1_ax1_r800_s1 | 67.81/71.28/-3.48 | 14.51/14.40/0.11 | 562.9/590.5 | 1.266/1.264 | BLOCKED |
| pt1_ax1_r800_s2 | 55.91/55.73/0.18 | 14.38/14.28/0.10 | 486.0/489.6 | 1.266/1.265 | agree |
| pt1_ax2_r400_s1 | 54.19/54.09/0.11 | 13.99/13.86/0.13 | 472.9/476.4 | 1.278/1.278 | agree |
| pt1_ax2_r400_s2 | 57.76/56.86/0.89 | 14.02/13.90/0.12 | 488.7/485.0 | 1.276/1.275 | agree |
| pt1_ax2_r800_s1 | 56.22/56.86/-0.64 | 14.60/14.60/-0.01 | 477.5/482.8 | 1.260/1.260 | agree |
| pt1_ax2_r800_s2 | 54.93/52.94/1.99 | 14.47/14.34/0.12 | 464.9/460.8 | 1.265/1.265 | agree |
| pt1_ax3_r400_s1 | 63.28/64.50/-1.22 | NaN/NaN/NaN | 278.7/288.3 | 1.253/1.239 | agree |
| pt1_ax3_r400_s2 | 58.15/58.70/-0.55 | 16.28/NaN/NaN | 255.5/243.0 | 1.272/1.258 | BLOCKED |
| pt1_ax3_r800_s1 | 58.92/59.33/-0.41 | NaN/NaN/NaN | 230.5/228.7 | 1.268/1.256 | agree |
| pt1_ax3_r800_s2 | 64.72/66.17/-1.45 | 17.80/22.37/-4.57 | 284.9/287.1 | 1.254/1.232 | BLOCKED |

BLOCKED cells (3): pt1_ax1_r800_s1, pt1_ax3_r400_s2, pt1_ax3_r800_s2
