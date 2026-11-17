# A-30 re-fly: is S64 seed 1 noise realisation or non-determinism at 400 Hz?

Scenario step_roll, seed 1, 400 Hz, indi, quad5in, params `results/g2_step_s64_400/indi.params`.
`fly.sh` runs A and B in parallel at --speed 4, then C at --speed 1 (-t 2400). done.txt: A, B, C rc=0.
Metrics: `bench/g2_step_metrics.py` -> `g2_step_primary.json` (est_* columns, truth in the same file).

| run | speed | rise ms | settle ms | OS % | truth OS % | t_window_start us |
|---|---|---|---|---|---|---|
| A | 4 | 210.0 | 356.25 | 0.54 | 0.27 | 55551000 |
| B | 4 | 205.6 | 360.0 | 1.18 | 1.14 | 55420000 |
| C | 1 | 208.8 | 356.25 | 0.41 | 0.29 | 55515000 |
| S64 seed 1 | 4 | 188.7 | 312.5 | 1.78 | 1.86 | 55546000 |

Raw comparison (ULG, window t_window_start..t_window_end, linear interp of B/C/S64 onto A timestamps because
the sample timelines differ): noise_seed {gz_sim_seed 1, px4_baro_srand 1234} identical in all runs.
- vehicle_angular_velocity xyz[0]: A vs B max abs 1.42 rad/s; A vs C 0.95; A vs S64 seed 1 0.27.
- actuator_motors control[0]: A vs B max abs 0.048; A vs C 0.037; A vs S64 seed 1 0.030.
- Window start differs between runs by up to 131 ms (B earlier than A) because arm/offboard times are wall-clock driven,
  so the raw diff mixes timing shift with real divergence. Not separated here.

Verdict
- A vs B: DIFFERENT (same seed, same params, same speed; sample counts 5600 vs 5607; metrics differ).
- A vs S64 seed 1: not the same (rise, settle and OS all differ; S64 seed 1 is not reproduced by A, B or C).
- C (speed 1) vs A: DIFFERENT (metrics differ within the same band as A vs B).
