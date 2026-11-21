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
| pt0_ax1_r400_s1 | 17/17 | 51.45 | 16.45 | NaN | 16.45 | 531.4 | 1.213 |
| pt0_ax1_r400_s2 | 17/17 | 52.11 | 16.47 | NaN | 16.47 | 546.2 | 1.214 |
| pt0_ax1_r800_s1 | 17/17 | 54.19 | 16.88 | 17.80 | 16.88 | 491.0 | 1.207 |
| pt0_ax1_r800_s2 | 17/17 | 56.63 | 16.93 | 17.86 | 16.93 | 558.9 | 1.209 |
| pt0_ax2_r400_s1 | 17/17 | 57.42 | 16.37 | NaN | 16.37 | 576.0 | 1.214 |
| pt0_ax2_r400_s2 | 17/17 | 55.76 | 16.41 | NaN | 16.41 | 576.6 | 1.214 |
| pt0_ax2_r800_s1 | 17/17 | 55.39 | 16.87 | 17.77 | 16.87 | 548.5 | 1.208 |
| pt0_ax2_r800_s2 | 17/17 | 53.04 | 16.87 | 17.83 | 16.87 | 526.5 | 1.207 |
| pt0_ax3_r400_s1 | 15/16 | 69.39 | NaN | NaN | NaN | 269.1 | 1.191 |
| pt0_ax3_r400_s2 | 15/16 | 68.66 | NaN | 28.19 | 28.19 | 260.4 | 1.197 |
| pt0_ax3_r800_s1 | 16/16 | 70.70 | NaN | NaN | NaN | 276.5 | 1.185 |
| pt0_ax3_r800_s2 | 15/16 | 67.64 | NaN | NaN | NaN | 267.6 | 1.187 |
| pt1_ax1_r400_s1 | 15/17 | 55.18 | 16.73 | NaN | 16.73 | 677.3 | 1.188 |
| pt1_ax1_r400_s2 | 16/17 | 62.33 | 16.81 | NaN | 16.81 | 758.9 | 1.193 |
| pt1_ax1_r800_s1 | 16/17 | 60.34 | 17.38 | 17.98 | 17.38 | 722.6 | 1.185 |
| pt1_ax1_r800_s2 | 16/17 | 66.17 | 17.31 | 17.91 | 17.31 | 802.5 | 1.182 |
| pt1_ax2_r400_s1 | 16/17 | 67.05 | 16.90 | 17.64 | 16.90 | 800.2 | 1.193 |
| pt1_ax2_r400_s2 | 16/17 | 62.56 | 16.86 | 17.76 | 16.86 | 742.6 | 1.198 |
| pt1_ax2_r800_s1 | 16/17 | 61.44 | 17.04 | 17.88 | 17.04 | 735.1 | 1.194 |
| pt1_ax2_r800_s2 | 16/17 | 62.71 | 17.39 | 18.08 | 17.39 | 765.4 | 1.189 |
| pt1_ax3_r400_s1 | 13/16 | 61.97 | NaN | NaN | NaN | 248.8 | 1.279 |
| pt1_ax3_r400_s2 | 13/16 | 63.16 | NaN | NaN | NaN | 245.2 | 1.246 |
| pt1_ax3_r800_s1 | 15/16 | 61.48 | 21.58 | NaN | 21.58 | 257.8 | 1.265 |
| pt1_ax3_r800_s2 | 15/16 | 61.47 | 19.65 | NaN | 19.65 | 249.1 | 1.256 |

## Comparison with primary (*_margins.json)

| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |
|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 51.45/50.98/0.47 | 16.45/16.41/0.04 | 531.4/530.0 | 1.213/1.212 | agree |
| pt0_ax1_r400_s2 | 52.11/52.22/-0.11 | 16.47/16.45/0.03 | 546.2/549.5 | 1.214/1.214 | agree |
| pt0_ax1_r800_s1 | 54.19/54.14/0.05 | 16.88/16.82/0.07 | 491.0/488.8 | 1.207/1.207 | agree |
| pt0_ax1_r800_s2 | 56.63/56.81/-0.18 | 16.93/16.86/0.07 | 558.9/560.1 | 1.209/1.209 | agree |
| pt0_ax2_r400_s1 | 57.42/57.46/-0.04 | 16.37/16.32/0.05 | 576.0/576.5 | 1.214/1.215 | agree |
| pt0_ax2_r400_s2 | 55.76/55.17/0.59 | 16.41/16.35/0.06 | 576.6/579.7 | 1.214/1.214 | agree |
| pt0_ax2_r800_s1 | 55.39/55.77/-0.38 | 16.87/16.82/0.05 | 548.5/553.9 | 1.208/1.207 | agree |
| pt0_ax2_r800_s2 | 53.04/52.37/0.66 | 16.87/16.81/0.06 | 526.5/521.4 | 1.207/1.207 | agree |
| pt0_ax3_r400_s1 | 69.39/70.86/-1.47 | NaN/NaN/NaN | 269.1/277.8 | 1.191/1.191 | agree |
| pt0_ax3_r400_s2 | 68.66/67.95/0.71 | NaN/NaN/NaN | 260.4/260.1 | 1.197/1.198 | agree |
| pt0_ax3_r800_s1 | 70.70/70.51/0.19 | NaN/NaN/NaN | 276.5/268.5 | 1.185/1.186 | agree |
| pt0_ax3_r800_s2 | 67.64/66.13/1.52 | NaN/NaN/NaN | 267.6/259.6 | 1.187/1.184 | agree |
| pt1_ax1_r400_s1 | 55.18/54.02/1.17 | 16.73/16.59/0.14 | 677.3/665.4 | 1.188/1.186 | agree |
| pt1_ax1_r400_s2 | 62.33/63.02/-0.70 | 16.81/16.71/0.10 | 758.9/768.3 | 1.193/1.192 | agree |
| pt1_ax1_r800_s1 | 60.34/59.67/0.67 | 17.38/17.33/0.06 | 722.6/715.5 | 1.185/1.185 | agree |
| pt1_ax1_r800_s2 | 66.17/67.09/-0.92 | 17.31/17.20/0.11 | 802.5/819.6 | 1.182/1.181 | agree |
| pt1_ax2_r400_s1 | 67.05/67.67/-0.62 | 16.90/16.81/0.09 | 800.2/823.2 | 1.193/1.193 | agree |
| pt1_ax2_r400_s2 | 62.56/62.76/-0.21 | 16.86/16.74/0.12 | 742.6/748.0 | 1.198/1.199 | agree |
| pt1_ax2_r800_s1 | 61.44/61.00/0.44 | 17.04/16.75/0.28 | 735.1/715.4 | 1.194/1.197 | agree |
| pt1_ax2_r800_s2 | 62.71/63.84/-1.13 | 17.39/17.26/0.12 | 765.4/774.5 | 1.189/1.190 | agree |
| pt1_ax3_r400_s1 | 61.97/64.17/-2.20 | NaN/NaN/NaN | 248.8/258.0 | 1.279/1.237 | agree |
| pt1_ax3_r400_s2 | 63.16/63.83/-0.67 | NaN/NaN/NaN | 245.2/247.3 | 1.246/1.228 | agree |
| pt1_ax3_r800_s1 | 61.48/64.19/-2.71 | 21.58/NaN/NaN | 257.8/261.6 | 1.265/1.237 | BLOCKED |
| pt1_ax3_r800_s2 | 61.47/62.26/-0.79 | 19.65/NaN/NaN | 249.1/261.0 | 1.256/1.252 | BLOCKED |

BLOCKED cells (2): pt1_ax3_r800_s1, pt1_ax3_r800_s2

## Disposition (orchestrator, S164)
22/24 cells agree within 3 deg / 1 dB (worst dPM 2.2 deg, dGM 0.28 dB). pt1_ax3_r800_s1/s2: the only difference is
whether a -180 deg crossing exists: key2 interpolates the phase through the 3.2 Hz bin of a -27 dB notch (phase
ill-defined there, ~320 deg flip) and finds GM 21.6/19.7 dB; the primary reports no crossing. PM agrees (dPM 2.7/0.8
deg). Resolution: the cells report the conservative value (GM 19.7 dB, the smaller of both keys); the verdict (>= 6 dB)
does not depend on the estimator choice. Outer cells: KEYED (S164).
