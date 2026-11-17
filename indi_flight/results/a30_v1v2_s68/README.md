# T149: does the v2 simulator break same-seed determinism? (a30_v1v2_s68)

Question: is the same-seed spread seen in T148 (PID v2 rise span 12.3 ms, settle span 46.25 ms) caused by `--sim v2`?
Compare G1.6 (`--sim` default v1) with the same command plus `--sim v2`.

Command (copied from `bench/g16_sched_set.sh` line 11, scenario step_roll, speed 4):
`indi_project/docker/run.sh -n s68v_<label> -t 600 -- python3 indi_flight/bench/run_scenario.py --scenario step_roll --controller pid_default --model quad5in --seed 1 --speed 4 --sched --sched-anchor --out <dir>`
G-v2 adds `--sim v2`. No `--rate-hz` (default 800 Hz), no `--params`, seed 1 for all.

Script `fly.sh` (pre: r1 of each group; rest: r2..r5, 5 in parallel, nohup). Done log `done.txt`: 10 lines, all `rc=0`, then ALLDONE.
Metric: `bench/g2_step_metrics.py` (run from `indi_flight/`), scores in `score_all.json` (also `score_pre.json` for the pre-test pair).
Pre-test: both r1 runs rc 0, metric ran, `run.json` sim = v1 / v2 as intended, controller pid_default, sched true.
All 10 flights pass the metric's own gates.

## Per-flight (est = the metric's estimator; overshoot is 0.00 % for all runs)

| group | run | rise ms | est settle ms |
|---|---|---|---|
| G-v1 | r1 | 186.50 | 387.50 |
| G-v1 | r2 | 184.74 | 391.25 |
| G-v1 | r3 | 174.94 | 360.00 |
| G-v1 | r4 | 175.44 | 357.50 |
| G-v1 | r5 | 185.01 | 393.75 |
| G-v2 | r1 | 185.88 | 387.50 |
| G-v2 | r2 | 176.29 | 361.25 |
| G-v2 | r3 | 186.44 | 390.00 |
| G-v2 | r4 | 186.85 | 391.25 |
| G-v2 | r5 | 186.00 | 388.75 |

## Spread per group (min to max, n=5)

| group | rise ms | est settle ms | est OS % |
|---|---|---|---|
| G-v1 (G1.6 command, sim v1) | 174.94-186.50 (span 11.55) | 357.50-393.75 (span 36.25) | 0.00 (span 0) |
| G-v2 (same + `--sim v2`) | 176.29-186.85 (span 10.56) | 361.25-391.25 (span 30.00) | 0.00 (span 0) |
| Reference: T148 G-pid (`--sim v2`, 400 Hz) | span 12.3 | span 46.25 | 0 |
| Reference: G1.6 s32 speed 4 step_roll (`results/g16_set_s32/speed4/README.md`) | not in rise ms; delay span 0.9-1.1 ms, settle 0.4-1.2 %, effort 2.5 % | | |

## Verdict

- Sentence: G-v1 is NOT near-identical (rise span 11.55 ms, well above the 2.5 ms bound), and G-v2 is not near-identical either (10.56 ms).
- So the v2 simulator is not what breaks determinism: the same-seed spread is already present with the default v1 model, at the same magnitude as v2.

## Caveats (not verified)

- The G1.6 s32 README reports a different quantity (delay spread 0.9-1.1 ms, settle as a percent), so its "near-identical" statement and this rise-ms span are not directly comparable. It was not re-scored here with its metric (`bench/metrics.py`).
- T148 used 400 Hz; this batch runs at the default 800 Hz, so the reference span is not like-for-like in rate.
- Not checked: whether the spread comes from the sim-time player, wall-clock scheduling, or PX4 timing; the ULog placement (`sched.txt`, `t_on_us`) was not compared across runs.
