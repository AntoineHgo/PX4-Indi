# S134 F-7 smoke re-fly (fixed firmware): auto_tour, INDI from arming. Pre-fix = `f7_smoke_s134`

Same command, seed 1, quad5in, params as pre-fix. Exit ok, no LOC/failsafe. `run.json` metrics_status failed (no scenario window), same as pre-fix. Metrics: `check.txt` and `extra_metrics.py`.

| Metric | Pre-fix | Fix |
|---|---|---|
| Take-off edge thrust step (50 ms), % of hover | 0.0064 (4.7 %) | 0.0064 (4.7 %) |
| Edge step, 0.1 s means | 4.4 % | 4.5 % |
| Truth altitude dip after edge | 0.000 m | 0.000 m |
| Max abs collective change, 0.1 s means, ramp | 0.0102 (32.10 s) | 0.0103 (31.82 s) |
| Pre-arm ground collective, mean (range), 5 s before rampup | 0.0145 (0.001-0.050) | 0.0011 (0.001-0.0014) |
| Rampup start / take-off edge | 31.40 s / 34.40 s | 31.22 s / 34.22 s |
| stage_mode | 2, 1 at 34.40, 2 at 92.05 | 2, 1 at 34.22, 2 at 91.55 |
| Mission xy RMS (max) | 0.490 m (0.785) | 0.486 m (0.767) |
| Land mean vz | 0.707 m/s | 0.702 m/s |
| Contact to disarm | 2.69 s | 2.68 s |
