# S137 G2 rate-yaw margins at MC_INDI_K_Y 20 (PROBE, 1 seed per rate; full G2 at the stage-6 freeze)

Recipe = results/g2_rate_batch_s99 (hover_long, measured-torque injection MC_INDI_INJ_AX 3, quad5in, sim v2, speed 4,
m3a_margins_pretest.py 1-60 Hz), but the parameter base is the G5 set (results/g5_g51_ky20_s137/params.params:
ID_OK 1, ACT_TC 0.033, POS_EN 1) with K_Y 20, plus the S99 injection lines. Runner batch.sh, log batch.log.
pretest_gate PASS on both cells, 18/18 bins accepted.

| cell | GM dB | PM deg | DM ms | f_c Hz | pass (GM>=6, PM>=45, DM>=2T+L) |
|---|---|---|---|---|---|
| yaw 800 s1, K_Y 20 | 18.82 | 78.4 | 71.8 | 3.03 | yes |
| yaw 400 s1, K_Y 20 | 14.35 | 81.9 | 80.1 | 2.84 | yes |
| ref S99 yaw 800 s1, K_Y 10 | 21.53 | 87.1 | 154.6 | 1.57 | yes |
| ref S99 yaw 400 (worst of 2), K_Y 10 | 15.5 | 86.5 | 161.2 | | yes |

Crossover moved 1.6 -> 3.0 Hz (w_c 19 rad/s, about K_Y). The GM fell less than the 6 dB a pure gain doubling gives:
the base set differs from S99 (ACT_TC 0.033 vs 0.05, ID_OK gate, outer module), so the K_Y 10 rows are context, not
a same-config pair. Not measured: attitude-yaw cell at K_Y 20 (32.1 dB at K_Y 10), 267 Hz.
