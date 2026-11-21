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
| pt0_ax1_r400_s1 | 16/17 | 51.55 | 13.66 | 13.07 | 13.07 | 408.2 | 1.306 |
| pt0_ax1_r400_s2 | 17/17 | 52.84 | 13.49 | 12.95 | 12.95 | 390.0 | 1.306 |
| pt0_ax1_r800_s1 | 17/17 | 49.58 | 14.01 | 13.27 | 13.27 | 359.7 | 1.289 |
| pt0_ax1_r800_s2 | 16/17 | 49.39 | 14.05 | 13.29 | 13.29 | 365.8 | 1.290 |
| pt0_ax2_r400_s1 | 17/17 | 51.64 | 13.54 | 12.93 | 12.93 | 401.3 | 1.303 |
| pt0_ax2_r400_s2 | 17/17 | 55.53 | 13.64 | 13.01 | 13.01 | 388.6 | 1.304 |
| pt0_ax2_r800_s1 | 17/17 | 49.94 | 14.08 | 13.33 | 13.33 | 373.4 | 1.290 |
| pt0_ax2_r800_s2 | 17/17 | 50.85 | 14.00 | 13.28 | 13.28 | 377.4 | 1.292 |
| pt0_ax3_r400_s1 | 15/16 | 69.48 | NaN | NaN | NaN | 262.0 | 1.191 |
| pt0_ax3_r400_s2 | 14/16 | 68.20 | NaN | NaN | NaN | 273.6 | 1.195 |
| pt0_ax3_r800_s1 | 14/16 | 69.72 | NaN | NaN | NaN | 290.7 | 1.190 |
| pt0_ax3_r800_s2 | 14/16 | 66.51 | NaN | NaN | NaN | 252.6 | 1.188 |
| pt1_ax1_r400_s1 | 16/17 | 58.32 | 14.13 | 13.45 | 13.45 | 482.1 | 1.274 |
| pt1_ax1_r400_s2 | 16/17 | 56.93 | 13.93 | 13.35 | 13.35 | 504.2 | 1.283 |
| pt1_ax1_r800_s1 | 17/17 | 54.50 | 14.59 | NaN | 14.59 | 467.0 | 1.263 |
| pt1_ax1_r800_s2 | 17/17 | 57.48 | 14.56 | NaN | 14.56 | 483.7 | 1.265 |
| pt1_ax2_r400_s1 | 15/17 | 54.22 | 13.96 | 13.19 | 13.19 | 477.2 | 1.278 |
| pt1_ax2_r400_s2 | 15/17 | 60.75 | 13.95 | 13.19 | 13.19 | 530.4 | 1.279 |
| pt1_ax2_r800_s1 | 16/17 | 56.51 | 14.56 | NaN | 14.56 | 457.6 | 1.264 |
| pt1_ax2_r800_s2 | 16/17 | 60.88 | 14.55 | NaN | 14.55 | 535.6 | 1.264 |
| pt1_ax3_r400_s1 | 14/16 | 60.54 | NaN | NaN | NaN | 272.0 | 1.290 |
| pt1_ax3_r400_s2 | 14/16 | 61.22 | NaN | NaN | NaN | 257.2 | 1.284 |
| pt1_ax3_r800_s1 | 13/16 | 60.85 | NaN | NaN | NaN | 237.3 | 1.271 |
| pt1_ax3_r800_s2 | 7/16 | 66.07 | NaN | NaN | NaN | 266.8 | 1.198 |

## Comparison with primary (*_margins.json)

| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |
|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 51.55/51.18/0.37 | 13.66/13.66/0.01 | 408.2/411.5 | 1.306/1.305 | agree |
| pt0_ax1_r400_s2 | 52.84/51.57/1.26 | 13.49/13.43/0.06 | 390.0/383.7 | 1.306/1.307 | agree |
| pt0_ax1_r800_s1 | 49.58/48.96/0.62 | 14.01/13.96/0.05 | 359.7/354.0 | 1.289/1.288 | agree |
| pt0_ax1_r800_s2 | 49.39/48.53/0.86 | 14.05/13.99/0.06 | 365.8/357.8 | 1.290/1.288 | agree |
| pt0_ax2_r400_s1 | 51.64/51.63/0.01 | 13.54/13.48/0.06 | 401.3/405.8 | 1.303/1.302 | agree |
| pt0_ax2_r400_s2 | 55.53/55.67/-0.14 | 13.64/13.60/0.04 | 388.6/388.5 | 1.304/1.303 | agree |
| pt0_ax2_r800_s1 | 49.94/49.87/0.07 | 14.08/14.06/0.02 | 373.4/373.9 | 1.290/1.289 | agree |
| pt0_ax2_r800_s2 | 50.85/51.04/-0.19 | 14.00/13.98/0.03 | 377.4/378.3 | 1.292/1.292 | agree |
| pt0_ax3_r400_s1 | 69.48/70.42/-0.93 | NaN/NaN/NaN | 262.0/262.2 | 1.191/1.190 | agree |
| pt0_ax3_r400_s2 | 68.20/68.69/-0.49 | NaN/NaN/NaN | 273.6/270.8 | 1.195/1.195 | agree |
| pt0_ax3_r800_s1 | 69.72/71.71/-1.99 | NaN/NaN/NaN | 290.7/313.0 | 1.190/1.191 | agree |
| pt0_ax3_r800_s2 | 66.51/65.47/1.04 | NaN/NaN/NaN | 252.6/245.7 | 1.188/1.189 | agree |
| pt1_ax1_r400_s1 | 58.32/58.88/-0.56 | 14.13/14.07/0.06 | 482.1/491.0 | 1.274/1.272 | agree |
| pt1_ax1_r400_s2 | 56.93/57.61/-0.68 | 13.93/13.88/0.04 | 504.2/512.5 | 1.283/1.282 | agree |
| pt1_ax1_r800_s1 | 54.50/53.24/1.25 | 14.59/14.52/0.07 | 467.0/452.3 | 1.263/1.262 | agree |
| pt1_ax1_r800_s2 | 57.48/55.34/2.14 | 14.56/14.50/0.06 | 483.7/475.5 | 1.265/1.265 | agree |
| pt1_ax2_r400_s1 | 54.22/54.19/0.03 | 13.96/13.82/0.14 | 477.2/482.5 | 1.278/1.279 | agree |
| pt1_ax2_r400_s2 | 60.75/60.50/0.25 | 13.95/13.87/0.09 | 530.4/533.8 | 1.279/1.280 | agree |
| pt1_ax2_r800_s1 | 56.51/56.64/-0.13 | 14.56/14.44/0.12 | 457.6/464.7 | 1.264/1.262 | agree |
| pt1_ax2_r800_s2 | 60.88/62.46/-1.58 | 14.55/14.50/0.05 | 535.6/558.1 | 1.264/1.263 | agree |
| pt1_ax3_r400_s1 | 60.54/63.88/-3.34 | NaN/NaN/NaN | 272.0/273.5 | 1.290/1.253 | BLOCKED |
| pt1_ax3_r400_s2 | 61.22/64.49/-3.27 | NaN/NaN/NaN | 257.2/271.8 | 1.284/1.245 | BLOCKED |
| pt1_ax3_r800_s1 | 60.85/63.13/-2.28 | NaN/NaN/NaN | 237.3/256.3 | 1.271/1.248 | agree |
| pt1_ax3_r800_s2 | 66.07/65.36/0.71 | NaN/NaN/NaN | 266.8/262.5 | 1.198/1.247 | agree |

BLOCKED cells (2): pt1_ax3_r400_s1, pt1_ax3_r400_s2
