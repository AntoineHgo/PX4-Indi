# S64: G2-STEP 400 Hz reported run (not a pass condition)

Same binary as `../g2_step_s64` (HEAD 360c9ae453, clean tree), same params, `--rate-hz 400`, seeds 1-3, 9 flights rc 0
(`fly.sh`, `done.txt`). Primary `g2_step_primary.json` (`bench/g2_step_metrics.py`), key `key_all.md` (AGREE on OS and
settle on all 9).

| seed | roll OS % / settle ms / rise ms | pitch | yaw |
|---|---|---|---|
| 1 | 1.78 / 312 / 189 | 1.10 / 328 / 196 | 0.16 / 919 / 545 |
| 2 | 0.40 / 360 / 206 | 0.69 / 360 / 201 | 0.38 / 906 / 545 |
| 3 | 0.74 / 336 / 199 | 0.68 / 354 / 207 | 0.24 / 926 / 545 |

All 9 within the 800 Hz limits (truth OS <= 1.86 %). Seed spread larger than at 800 Hz (seed 1 roll faster): A-30.
