# T150: G1.6 spread vs g2 rise-settle spread, S32 vs S68 step_roll

Scripts: `bench/g16_spread.py` (G1.6 spread, stdlib, host python) and `bench/g2_step_metrics.py` (run from `indi_flight/`).
Runs: S32 = `results/g16_set_s32/speed4/step_roll/r1..r5`; S68 = `results/a30_v1v2_s68/G-v1/r1..r5` (sim v1) and `G-v2/r1..r5` (sim v2).
No flights, no firmware build, nothing written into `indi_project/`. Outputs: `spread_v1.json`, `spread_v2.json`, `g2_v1.json` here;
S32 g2 output in the scratchpad (`g2_s32.json`); S32 G1.6 spread is the existing `g16_set_s32/speed4/spread.json`, recomputed to the scratchpad (`spread_s32_step.json`) and identical in content.

## Commits

- S32 (`g16_set_s32`): `run.json` git commit `71c194ff26c369d4496cf3334069b35744b55fc0`, dirty true.
- S68 G-v1 and G-v2: commit `5daadda43e873f54feaec7978e80a24c8e7fb3e2`, dirty false (checked r1 and r5 of each).
- Sim: G-v1 = v1, G-v2 = v2 (per `run.json`).

## 2x2 table (abs spread across r1..r5; rel = spread / mean)

| metric | S32 runs | S68 G-v1 (sim v1) | S68 G-v2 (sim v2) |
|---|---|---|---|
| G1.6 spread, rise_10_90 (steps 0..3, ms) | 0.85 / 0.77 / 0.64 / 0.95 (rel 0.5 %) | 11.1 / 10.9 / 11.8 / 11.7 (rel 6.1 %) | 10.6 / 0.9 / 1.2 / 1.4 (rel 5.8 % on step 0, <1 % otherwise) |
| G1.6 spread, delay_10pct (steps 0..3, ms) | 1.1 / 0.9 / 0.9 / 0.9 | 1.7 / 1.1 / 1.3 / 1.2 | 0.8 / 2.8 / 1.0 / 2.3 |
| g2 rise-settle, est_rise_ms | 0.82 ms (rel 0.44 %) | 11.55 ms (rel 6.4 %) | not run |
| g2 rise-settle, est_settle_ms | 3.75 ms (rel 0.96 %) | 36.25 ms (rel 9.6 %) | not run |
| g2 rise-settle, truth_settle_ms | 22.5 ms (rel 5.7 %) | 52.5 ms (rel 13.9 %) | not run |

Mean est_rise_ms: S32 186.2, G-v1 181.3. Mean est_settle_ms: S32 389, G-v1 378.

## Reading

Both metrics give the same ranking: the S68 G-v1 rise spread is about 11 ms (about 13x the S32 spread) under the G1.6 script and under g2. This is not a metric difference. The G1.6 numbers for G-v2 show the 11 ms appears on step 0 only (10.6 ms); steps 1..3 sit near 1 ms, so the v1/v2 split is not clean either.
