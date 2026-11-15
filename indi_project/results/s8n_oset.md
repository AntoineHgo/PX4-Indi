# Stage-8 verdict on set O: pid_tuned (stock pipeline) vs indi_pos_v3 (INDI POS), 10 seeds

Batch `bench/s8n_oset.sh` (140 flights, 2026-11-15 04:14-05:03, v2 sim, SENS_GNSS0_DELAY 0 for both, D-s8-gnss-delay),
frozen config `bench/params/indi_pos_v3.params` (D-s8-freeze), criteria `bench/scenarios.md` sec. 10, fixed before any
INDI POS flight on set O. Glitch scan (`bench/glitch_scan.py results/s8n_oset/runs`): no estimator glitch, no re-fly.
Verdict: `python3 bench/s2_verdict.py results/s8n_oset/runs --b indi_pos_v3 --oset --final --hover-runs results/s8m_smoke_gnss0`.

## Primary metric (trajectory RMS 3D in the window, m), paired by seed, exact two-sided Wilcoxon

| entry | pid_tuned mean | indi_pos_v3 mean | ratio | b<a | med impr | p | effort ratio | fails a/b | verdict |
|---|---|---|---|---|---|---|---|---|---|
| O1 lemniscate | 0.4557 | 0.3158 | 0.69 | 10/10 | 31 % | 0.00195 | 1.10 | 0/0 | better |
| O2 circle + z | 0.585 | 0.4215 | 0.72 | 10/10 | 28 % | 0.00195 | 1.03 | 0/0 | better |
| O3 lemniscate + gust | 0.4088 | 0.2772 | 0.68 | 10/10 | 32 % | 0.00195 | 1.10 | 0/0 | better |
| O4 lemniscate + payload | 0.7827 | 0.217 | 0.28 | 10/10 | 72 % | 0.00195 | 1.41 | 0/0 | better |
| O5 z-sine + CoM shift | 0.1631 | 0.07941 | 0.49 | 10/10 | 51 % | 0.00195 | 1.03 | 0/0 | better |
| O6 z-sine + mass x1.15 | 0.1006 | 0.09671 | 0.96 | 8/10 | 4 % | 0.00977 | 0.91 | 0/0 | better < 10 % |
| O7 lemniscate, tau x2 | 0.4563 | 0.3196 | 0.70 | 10/10 | 30 % | 0.00195 | 1.10 | 0/0 | better |

p = 0.00195 is the smallest exact two-sided p with 10 pairs (all 10 seeds on the same side).

Criteria (sec. 10): 1. no INDI POS failure on O: **met** (0/70). 2. significantly better by >= 10 % on >= 5 of 7:
**met** (6/7). 3. no entry significantly worse by > 10 %: **met** (0). 4. hover effort <= 1.5x pid_tuned:
**not met**: 2.02x on 10 seeds per controller (mean motor-rate RMS 0.088 vs 0.044; pid_tuned per seed 0.021-0.075, INDI POS 0.067-0.118; all 20 runs ok; `bench/s8p_hover_effort.sh`, D-s8-hover10; the 2-seed smoke value was 2.67x).

**Formal outcome (sec. 6 words): INDI POS does not outperform PID on set O**, because criterion 4 fails. Criteria 1-3, the
tracking criteria, are met clearly (6 of 7 entries better, 10/10 seeds on each, no failure, nothing worse). The hover
effort attribution (D-s8-freeze, s8o screen): pid_tuned ~0.03, indi_v3 rate loop under the stock outer loop ~0.05,
INDI POS ~0.08 on seeds 1-2, so about half the excess comes from the INDI rate loop (as in V', D-v3-hover) and half
from the outer loop's specific-force feedback; motor-rate RMS in hover is small in absolute terms (no saturation),
but the criterion was fixed in advance and is reported as failed.


## Secondary metrics (means over 10 seeds; reported, not deciding)

| entry | att RMS pid [deg] | sat pid [%] | max dev pid [m] | vert RMS pid [m] | att RMS INDI [deg] | sat INDI [%] | max dev INDI [m] | vert RMS INDI [m] |
|---|---|---|---|---|---|---|---|---|
| O1 | 8.95 | 0.0 | 1.13 | 0.037 | 4.70 | 0.0 | 1.10 | 0.020 |
| O2 | 6.41 | 0.0 | 1.12 | 0.048 | 3.19 | 0.0 | 1.03 | 0.049 |
| O3 | 7.64 | 0.0 | 1.20 | 0.025 | 4.30 | 0.0 | 1.19 | 0.016 |
| O4 | 6.12 | 33.5 | 2.82 | 0.193 | 2.53 | 22.9 | 0.81 | 0.029 |
| O5 | 0.74 | 0.0 | 0.56 | 0.157 | 0.47 | 0.0 | 0.32 | 0.076 |
| O6 | 0.10 | 0.0 | 0.33 | 0.098 | 0.47 | 0.0 | 0.31 | 0.094 |
| O7 | 8.97 | 0.0 | 1.14 | 0.025 | 4.69 | 0.0 | 1.11 | 0.018 |

Attitude RMS is the error against each pipeline's OWN attitude setpoint, so it compares inner-loop following, not the
two pipelines; saturation is `effort.saturation_frac_motors`; max dev is `trajectory.max_dev_3d_m`.

## Reading

- The gain is consistent (10/10 seeds on six entries) and largest where a disturbance acts on the translational
  dynamics: O4 payload (-72 %, the stock pipeline loses 0.19 m vertical RMS and saturates a third of the window; INDI
  POS reacts through the measured specific force without waiting for an integrator) and O5 CoM shift (-51 %).
- O1/O2/O3/O7 (-28..-32 %) are nominal-path entries: the gain there comes from the jerk/acceleration feedforward and
  the faster acceleration loop. The stock pipeline does not get the flatness feedforward (O-9: the feedforward is part
  of the INDI design); the FF-0 ablation (arm C, one seed on T5, `results/s8j_pos_v3_smoke.md`) was 0.76 m, i.e.
  without feedforward INDI POS was worse than pid_tuned on T5 (0.38 m) under the stock 110 ms GNSS delay; that arm was
  not re-flown with delay 0, so the share of the gain due to feedforward is not measured on set O.
- O6 (mass x1.15, a G_T model error for INDI POS) is the only entry without a 10 % gain: both hold the vertical sine
  to ~0.1 m; INDI is significantly but only 4 % better. The incremental law absorbs the thrust-effectiveness error,
  but this path is easy for both.
- O7 (motor time constants x2) changes neither controller (O1 vs O7 within 1 %): at outer-loop bandwidth the slower
  motors are not visible, so this entry does not probe the expected INDI weakness of stage 1.
- Effort: 0.91-1.10x on six entries, 1.41x on O4 (INDI POS holds the payload with less saturation, 22.9 vs 33.5 %).
