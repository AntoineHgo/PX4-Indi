# Open anomalies

Each entry: what was seen, where, closing test, status. Nothing is frozen with an open anomaly that touches it.
Seeded from review section 3.4 (archive results, stage 1).

| id | anomaly | source | closing test | status |
|---|---|---|---|---|
| A-1 | Blend at Tb 0.1 s lost altitude and was pruned unexplained (frozen 0.3 s is a factor 3 away) | `indi_project/results/v3_screen.md:22` | linear model of the rate loop with blend predicts the 0.1 s failure; SITL margin at 0.1 and 0.3 s matches (stage 2) | open |
| A-2 | PID hover effort spread 3.5x between identical flights, mostly above 30 Hz | review 2.2 | determinism study (stage 1): same seed/plant reproduce within tolerance, or cause identified | open |
| A-3 | Sporadic vertical excursions in hover | review 3.4 | locate in re-scored hover logs; reproduce with fixed timing hooks | open |
| A-4 | INDI sensitivity to the simulation speed factor | review 3.4 | same scenario at speed factor 1 and max with deterministic injections; difference bounded or explained | open |
| A-5 | Failed v2 tuning candidate c12, unexplained | review 3.4 | archive-only: explain from logs or close as obsolete with reason once v2 law is gone | open |
| A-6 | Outer-loop hover command excess below 30 Hz, cause unknown | review 2.2, 5.3 | signal-substitution ablation (truth accel / unquantised rpm / truth velocity) in stage 5 | open |
| A-7 | Run-to-run non-reproducibility with identical seeds | review 3.1, 11.2 | stage 1 determinism test, G1 | open |
| A-8 | 8 of 1600 send_pos rows unmatched in applied_timing after 68.3 s (s9 hover) | T14, design/port_1a_applied_timing.md | re-run applied_timing on a full-rate log (pretest_logging_s10) and identify the logged trajectory_setpoint at those times; explain or fix the matcher | closed S10, not reproduced: full-rate s10 hover 0/1549 unmatched, p50=p95=4 ms (1 step); s9 cause not identified (likely 5 Hz decimation), reopen if it recurs |
