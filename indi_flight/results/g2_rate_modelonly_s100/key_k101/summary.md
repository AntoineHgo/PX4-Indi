# Second key K101: G2 model-only rate cells (S101)

Script `bench/second_key_m3a_s100.py --axis N` (keyed in K100) on raw flight.ulg of P100 (P400, Y800) and B100 cells; runner `key_k101/run_key.sh`. Primary = `<cell>/margins.txt` (m3a_margins_pretest.py). Key = KEY_A line (full window). Per-cell files hold variants B1/B2 and verdicts.

| cell | GM dB primary/key | PM deg primary/key | DM ms primary/key | AGREE verdicts |
|---|---|---|---|---|
| P400 | 10.25 / 10.25 | 72.44 / 71.94 | 41.3 / 41.34 | 2/2 |
| Y800 | 18.43 / 18.43 | 91.01 / 91.10 | 172.0 / 171.66 | 2/2 |
| pitch400_s2 | 10.13 / 10.08 | 70.81 / 70.53 | 39.7 / 39.51 | 2/2 |
| pitch800_s1 | 11.19 / 11.15 | 73.79 / 73.42 | 42.0 / 42.11 | 2/2 |
| pitch800_s2 | 11.20 / 11.18 | 74.11 / 73.55 | 42.7 / 41.85 | 2/2 |
| roll400_s1 | 10.49 / 10.45 | 73.09 / 72.65 | 41.8 / 41.37 | 2/2 |
| roll400_s2 | 10.12 / 10.14 | 71.11 / 70.82 | 40.4 / 40.19 | 2/2 |
| roll800_s1 | 11.23 / 11.22 | 74.13 / 73.82 | 42.0 / 41.89 | 2/2 |
| roll800_s2 | 11.26 / 11.21 | 74.10 / 73.59 | 42.5 / 41.96 | 2/2 |
| yaw400_s1 | 17.84 / 17.89 | 89.63 / 90.48 | 170.1 / 170.69 | 2/2 |
| yaw400_s2 | 17.79 / 17.83 | 90.15 / 90.37 | 170.9 / 171.78 | 2/2 |
| yaw800_s2 | 18.40 / 18.43 | 90.02 / 90.56 | 172.0 / 171.78 | 2/2 |

Result: 12/12 cells agree. Worst over cells (primary): GM 10.12 dB (roll400_s2), PM 70.8 deg (pitch400_s2), DM 39.7 ms; all above G2 thresholds (6 dB, 45 deg, 2 periods + telemetry latency). Limit: same estimator family as the primary (checks indexing/window, not the plant); no synthetic self-test for the s41/s100 key script yet.
