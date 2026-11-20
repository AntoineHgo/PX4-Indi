# G5.5 probe with A18 jerk feed-forward (S141), seed 1, PROBE

Same stack, params and matched GNSS (110/110 ms) as `../g5_g55_s140_gnss`; only change: A18 on (firmware commit
"feat(indi): jerk feed-forward side channel", flown before the gate-flip lead-reset fix, which does not act in
steady tracking). `run_batch.sh "<rows>" "<seeds>"`, scored by `bench/g55_check.py`.

| row | S140 (A18 off) | S141 (A18 on) | verdict (limit h 0.5 m) |
|---|---|---|---|
| o1_lemniscate | h 0.776 / v 0.034 | h 0.590 / v 0.045 | FAIL |
| o2_circle_z | h 0.933 / v 0.053 | h 0.793 / v 0.096 | FAIL |

o1 lag split (`../g5_g55_s140_gnss/lag_split.py`): est vs truth 0.05 m; setpoint vs truth best shift 140 ms
(S140: 160 ms), RMS at best shift 0.29 m. omega_ff valid 75 % of samples, |omega_ff| p95 roll 0.31 / pitch
1.08 rad/s. Gain 0.19 m (o1) and 0.14 m (o2) > 0.1 m: D-A18-REOPEN overturn test not met, A18 kept.
Remaining error is still mostly a 140 ms lag: cause not yet split (setpoint transport vs attitude/rate lag).
