# PID tuning round 1 (session 7-8, 2026-11-14)

Command: `python3 bench/tune.py --family pid --round-name r1 --n-candidates 24
--seeds 1 2 --jobs 6 --sampler-seed 0` (center = YAML defaults, span 2,
Latin hypercube in log space). Scenarios hover (x1), step_roll, step_pitch,
step_yaw, rate_step_roll (x4); seeds 1, 2. 240 flights, 0 failures.
Data: `results/tuning/pid/r1/summary.csv` (J = mean of metric ratios to the
`pid_default` reference flights, plus effort penalty; lower is better).

## Result

| | J | hover | step_roll | step_pitch | step_yaw | rate_step_roll |
|---|---|---|---|---|---|---|
| c00 (center = YAML defaults) | **0.946** | 0.752 | 0.992 | 1.002 | 0.995 | 0.987 |
| c12 (2nd) | 0.978 | 0.741 | 1.087 | 0.999 | 1.013 | 1.049 |
| median of 24 | 1.060 | 0.817 | 0.982 | 0.995 | 1.072 | 0.997 |

- **No sampled candidate beats the default gains.** Within a factor-2 box the
  default PX4 rate/attitude gains are the best of 24 points for this cost.
  Some candidates improve one axis (step_roll down to 0.78) at the expense
  of others; none improves the aggregate.
- **The hover ratio is biased:** its median over all 24 candidates is 0.82,
  including c00, which should be ~1 if c00 equals the reference. Either the
  reference `pid_default` hover flights differ in setup from the tuning
  flights (flown in an earlier session, possibly with another runner
  version), or hover position RMS has large run-to-run noise. The airframe
  hypothesis is ruled out: `4001_gz_x500` sets no rate/attitude gains, so
  c00 has the same gains as `pid_default`. **Unresolved; check before round 2.** The
  bias is common to all candidates, so the ranking inside the PID family is
  unaffected, but J < 1 must not be read as "better than PX4 defaults".
- Step metrics re-fly at ~1.00 for c00, consistent with the ~2 % run-to-run
  noise seen in the smoke round.

## Consequence for the baseline

The retuned-PID baseline is, for now, the default gains, with this round as
the documented tuning effort. A narrower round (span 1.3, more seeds on
hover) around c00 is the next PID step, once the hover reference bias is
explained. INDI round 1 uses the same budget, scenarios and cost (D-indi-r1).

## Follow-up (session 8): hover re-fly

`pid_default` hover re-flown with the same seeds 1-3 (`results/refly_s8/`,
log `results/refly_s8.log`): position RMS 0.036 / 0.037 / 0.046 m vs the
reference 0.033 / 0.027 / 0.021 m (ratios 1.08, 1.38, 2.19). Same gains,
same seed, up to 2x apart: **hover position RMS is not repeatable per
seed**, so the "bias" is run-to-run noise in a short hover, not a setup
difference. Consequence: the hover term of J is noise-dominated with 2
seeds. Before round 2, either fly hover with many more seeds (>= 8), or use
a longer hover window, and find the source of the non-determinism (seeded
gz sensor noise should make a run reproducible; lockstep timing or wind
model state may not be seeded).
