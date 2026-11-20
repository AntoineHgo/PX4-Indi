# S138 G2 rate-roll probe at the current pair (defaults audit S138)

Probe (1 seed, not gate evidence). Why: design/defaults_audit_s138.md found no G2 margin cell at the current
default pair (ACT_TC 0.033, ID_OK 1, K_R/K_P 20, K_Y 20); all earlier cells were at ACT_TC 0.05, K_Y 10.
Recipe: g2_yaw_ky20_s137/batch.sh (= g2_rate_pretest_s99 recipe), axis roll (MC_INDI_INJ_AX 1, the only param
difference from params_yaw.params), hover_long, quad5in, 800 Hz, seed 1. Command: `bash batch.sh` (resumable).

| cell | GM dB | PM deg | DM ms | crossover rad/s | pretest gate | logged rates |
|---|---|---|---|---|---|---|
| roll800_s1 | 18.8 | 56.2 | 47.7 | 20.6 | PASS | gyro/motors 800 Hz |

Gate G2 thresholds (GM >= 6 dB, PM >= 45 deg, DM >= 2 periods + telemetry latency) met with margin at this probe.
Crossover matches K_R 20. Open: pitch, 400 Hz and 3 seeds at the stage-6 freeze; attitude-yaw cell at K_Y 20;
firmware-default cell (ID_OK 0, W_MAX 0, ACT_TC 0.05). Source: roll800_s1/margins.txt, gate.md, rates.txt.
