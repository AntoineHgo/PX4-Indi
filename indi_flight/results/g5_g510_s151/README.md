# S151 G5.10 sat_sustained, 3 seeds, TB 0.3 + kMaxBlend 0.5 (probe, pre-freeze, parallel streams)

Fly: `bash indi_flight/results/g5_g510_s151/fly.sh` (repo root; params `results/g5_g510_s150/params_tb03.params`,
firmware 003e25c6d4, matched GNSS 110 ms, 3 parallel streams = probe only, STATE 4a). Checker `bench/g510_check.py`.

| seed | alt_loss_m (<= 2.0) | back_s_sat (<= 5) | tilt_max_deg (<= 20, Q9 a) | loc | AGG part |
|---|---|---|---|---|---|
| 1 | 1.741 PASS | 1.99 PASS | 45.32 FAIL | no | invalid (no saturation, Q9 b) |
| 2 | 1.736 PASS | 1.88 PASS | 45.34 FAIL | no | invalid |
| 3 | 1.758 PASS | 1.93 PASS | 45.35 FAIL | no | invalid |

Reading: the D-GAP-G510 fix (TB 1.0 -> 0.3, bound 0.3 -> 0.5) brings the alt loss from 2.67-2.74 m (S148) to
1.74-1.76 m on 3 seeds, spread 0.02 m; no 65 deg exit spike (S147) recurs. Tilt equals MPC_TILTMAX_AIR (the row's
3 m step, Q9 a test defect); AGG never saturates (Q9 b). Row stays FAIL/INVALID on the current text until Q9.
Margin at TB 0.3: results/g2_outer_tb03_s151 (PM 62.7 / 67.3 deg).
