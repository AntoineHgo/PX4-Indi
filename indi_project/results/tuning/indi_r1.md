# INDI tuning round 1 (session 8, 2026-11-14)

Command: `python3 bench/tune.py --family indi --round-name r1 --n-candidates
24 --seeds 1 2 --jobs 6 --sampler-seed 0 --base-params
bench/params/indi_v1.params --center bench/params/indi_r1_center.json`
(D-indi-r1). Same scenarios, seeds, cost and reference as PID round 1
(`pid_r1.md`). 240 flights, 0 failures. Data: `indi/r1/summary.csv`.

## Result (ratios to `pid_default`, lower is better)

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| PID best (c00 = defaults) | **0.946** | 0.752 | 0.992 | 1.002 | 0.995 | 0.987 |
| INDI best (c07) | 1.167 | **0.674** | **0.828** | **0.910** | **0.850** | **0.975** |
| INDI center (c00) | 1.463 | 1.129 | 1.040 | 1.026 | 0.862 | 1.071 |
| INDI median of 24 | 1.437 | | | | | |

INDI c07: K_R 37.5, K_P 20.3, K_Y 7.1, ACT_TC 0.0122 s, YAW_CUT 5.4 Hz,
ROLL_P 6.16, PITCH_P 6.56, YAW_P 3.71 (G1 241/241/7.4 from indi_v1).

## Reading (tuning set only; not a held-out or multi-seed result)

- **Tracking:** the best INDI candidate has a lower primary-metric ratio
  than the best PID candidate on all five tuning scenarios (yaw step -15 %,
  roll step -17 %, pitch step -9 %, hover position -10 % relative to PID
  c00). Two seeds per scenario: no statistics yet.
- **Effort:** its J is still worse (1.17 vs 0.95) because the cost charges
  motor-rate RMS above 1.25x the PID reference. The mean tracking ratio of
  c07 is 0.85, so about 0.32 of J is effort penalty. INDI buys its tracking
  with several times PID's actuator activity. Under the frozen cost, PID
  wins round 1. Both statements belong in the report.
- **Direction for round 2:** the best candidates sit at the low edge of the
  yaw cutoff box (5.0-7.1 Hz for the top 3) and at short actuator time
  constants (0.012-0.022 s, gz motor tc 0.0125 s up / 0.025 s down). Round 2
  should extend MC_INDI_YAW_CUT below 5 Hz and first find where the
  remaining hover effort comes from (`check_sync.py` per axis), before
  spending flights on gains. That is a design change (filtering), so it is
  allowed under the procedure, but the PID family must get the same round-2
  budget.
- The hover ratio bias noted in `pid_r1.md` applies here too (common
  reference), so compare INDI and PID hover ratios with each other, not
  with 1.
