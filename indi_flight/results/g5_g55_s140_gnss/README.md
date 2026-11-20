# G5.5 re-fly with matched GNSS (S140), PROBE, seed 1 only

Same stack and params as `../g5_g55_s139` plus nominal GNSS latency 110 ms with matched EKF compensation
(`--gps-dly 110 --gnss-delay 110`, GATES 5b G5.5 SET-UP FIX S140). `run_batch.sh "<rows>" "<seeds>"`; scored by
`bench/g55_check.py` into `<run>.json`. Lag split: `lag_split.py RUN_DIR` (scratch analysis, no self-test: probe only).

| row | S139 (mismatched) | S140 matched | verdict |
|---|---|---|---|
| o1_lemniscate | h 0.662 / v 0.079 m | h 0.776 / v 0.034 m | FAIL (h > 0.5) |
| o2_circle_z | h 1.336 / v 0.051 m | h 0.933 / v 0.053 m | FAIL (h > 0.5) |
| o5_zsine_com_shift | h 0.041 / v 0.062 m | h 0.048 / v 0.027 m | PASS |
| o6_zsine_mass | (s1 not flown) | h 0.043 / v 0.030 m | PASS |
| offb_vel_step | vx rms 0.102, end 0.079, dz 0.026 | vx rms 0.026, end 0.012, dz 0.019 | PASS |

o1 s1 lag split: estimate vs truth 0.05 m (S139: 0.53 m, estimate leading by 105 ms); setpoint vs truth 0.83 m at
zero shift, 0.50 m at the best shift of +160 ms. The remaining error is controller lag: jerk feed-forward disabled
(`McIndiPosControl.cpp:57`, omega_ff = 0; offboard jerk arrives as finite 0). DECISIONS D-A18-REOPEN.
