# S151 G2 outer z accel-break cells at MC_INDI_POS_TB 0.3 + kMaxBlend 0.5 (probe, pre-freeze, UNKEYED)

Purpose: the accept condition of D-GAP-G510 (TB 0.3 s must keep the outer acceleration-break PM >= 45 deg).
Runner `fly.sh PT AX RATE SEED` (repo root): base `results/g5_g510_s150/params_tb03.params`, injection as S86
(AMP 0.04, TP 10, NP 5, DLY 20, band 0.2-8 Hz), hover_long, quad5in, sim v2, matched GNSS 110 ms, serial flights.
Firmware 003e25c6d4 (bound 0.5). Margins from `pinj_csv.py --margins --point output`.

| cell | PM [deg] | f_c [Hz] | DM [s] | GM [dB] | Ms | holes |
|---|---|---|---|---|---|---|
| pt1_ax3_r400_s1 | 62.7 | 0.72 | 0.241 | 20.9 (2.92 Hz) | 1.26 | PASS |
| pt1_ax3_r800_s1 | 67.3 | 0.70 | 0.267 | no phase crossing in band | 1.23 | PASS |
| S86 TB 1.0 r400 s1 (reference) | 63.7 | 0.68 | 0.262 | - | 1.18 | PASS |

Reading: TB 1.0 -> 0.3 changes the z accel-break PM by about 1 deg at 400 Hz; all >= 45 deg, DM far above 2
periods + telemetry latency. D-GAP-G510 accept condition met as a probe. Still outstanding for gate use: margin
second key for outer cells (STATE offline G2 todo), 3 seeds at freeze.

## xy cells (key2 MINOR-2, S151): S87 settings AMP 0.08, TP 20, hover_xlong, serial
`AMP=0.08 TP=20 SCN=hover_xlong bash fly.sh PT 1 RATE SEED`. S87 reference flew TB 1.0 without the matched 110 ms
GNSS delay (now nominal), so the comparison mixes two changes.

| cell | PM [deg] | f_c [Hz] | DM [s] | GM [dB] | Ms | min coh | holes | S87 TB 1.0 PM / GM |
|---|---|---|---|---|---|---|---|---|
| pt0_ax1_r800_s2 (vel/pos break, S87 floor) | 51.4 | 0.27 | 0.523 | 16.8 | 1.21 | 0.95 | PASS | 49.7 / 18.8 |
| pt1_ax1_r400_s1 (accel break) | 65.2 | 0.23 | 0.776 | 16.8 | 1.20 | 0.97 | PASS | 62.8 / 18.6 |

Reading: TB 0.3 does not lower the xy PM floor; GM about 2 dB lower, far above 6 dB.
