# T151 (a32_load_s69): A-32 is host load, not a code regression

Question (A-32): the exact G1.6 command re-flown at HEAD spread 11.5 ms in rise against 0.8 ms at S32
(`results/a30_v1v2_s68/g16_metric.md`). Regression in the code, or a run condition?
Lead: in S68 G-v1 the rise values were bimodal (175 / 186 ms); the 186 mode equals the S32 mean (186.2 ms), and the
175 mode appeared only in runs flown 5 in parallel (`a30_v1v2_s68/fly.sh rest`). S32 was flown strictly
sequentially (`bench/g16_sched_set.sh`).

Command: exact G1.6 command (`bench/g16_sched_set.sh` line 11): step_roll, pid_default, quad5in, sim v1, seed 1,
speed 4, `--sched --sched-anchor`, HEAD 50bb9ef9ff, clean tree, firmware not rebuilt. `fly.sh`: G-seq = 5 runs strictly
sequential, then G-par = 5 runs started together. All 10 rc 0 (`done.txt`; 36 s per sequential run, 41 s in parallel).
Metric: the G1.6 script `bench/g16_spread.py` (`G16_ROOT=results/a32_load_s69`), output `spread.json`, ms extract
`spread_ms.txt`.

| group | rise 10-90 span, steps 0/1/2/3 (ms) | step-0 rise values (ms) | step-0 delay span | step-0 settle span |
|---|---|---|---|---|
| G-seq (sequential) | 1.45 / 1.23 / 0.86 / 0.54 | 185.8 185.8 186.2 186.0 187.3 | 0.90 ms | 5.0 ms |
| G-par (5 in parallel) | 11.97 / 11.34 / 10.81 / 10.15 | 178.7 175.9 184.8 174.9 186.9 | 5.22 ms | 23.75 ms |
| S32 reference (sequential) | 0.85 / 0.77 / 0.64 / 0.95 | mean 186.2 | 0.9-1.1 ms | |

## Verdict

- No regression: run sequentially at HEAD, the G1.6 command gives the S32 numbers (same mean, rise span <= 1.5 ms).
  G1.6 FINAL holds at HEAD under its own protocol (sequential runs).
- Host load breaks same-seed determinism: with 5 concurrent runs the rise spreads ~11 ms and is biased toward a faster
  mode (~175 ms, -6 %). Lockstep does not make the result independent of wall-clock timing under load. The mechanism is
  not identified here (candidates: a PX4 or bridge input that is not sim-time locked, e.g. message arrival relative to
  the lockstep tick).
- Consequence for evidence: same-seed and gate step-response claims are flown sequentially, or the parallel spread
  (rise 12 ms / settle 24 ms on this step, PID) is carried as the noise floor of a parallel batch.
