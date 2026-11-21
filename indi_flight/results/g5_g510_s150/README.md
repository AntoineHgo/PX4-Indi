# G5.10 probe S150: MC_INDI_POS_TB 0.3 s (probe, not gate evidence)

Command (run from repo root, Docker via wrapper):

```
indi_project/docker/run.sh -n g510tb03 -t 700 -- python3 indi_flight/bench/run_scenario.py --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params indi_flight/results/g5_g510_s150/params_tb03.params --scenario sat_sustained --out indi_flight/results/g5_g510_s150/s1_tb03 > indi_flight/results/g5_g510_s150/s1_tb03.out 2>&1
```

Exit code 0. The `.out` file is empty.

Checker (`g510_check.py`): RESULT INVALID, "no saturation in AGG part" (`sat_frac_agg_part` = 0.0, `last_sat_agg_s` = None).

| Metric | S148 s1 (TB 1.0) | S150 probe (TB 0.3) | Threshold | Check |
|---|---|---|---|---|
| Alt loss (m) | 2.71 | 1.953 | < 2.0 | PASS |
| Tilt max (deg) | 45.33 | 45.34 | (checker) | FAIL |
| Back-within (s) | 3.31 | 1.44 (SAT part) | < 5 | PASS |
| Back-within AGG (s) | n/a | None | - | FAIL |
| LOC | no | no | none | PASS (no LOC) |

Blend timeline (SAT = 58.12 s, from the SIM_GZ_THR_SC=0.274 row in `sends.csv`):

```
time_s  mean_u  blend
-0.50   0.137   -0.000
+0.00   0.137   -0.000
+0.25   0.064    0.053
+0.50   0.114    0.167
+0.75   0.155    0.281
+1.00   0.167    0.300
+1.25   0.178    0.300
+1.50   0.172    0.300
+1.75   0.161    0.300
+2.00   0.151    0.300
+3.00   0.130    0.300
+4.00   0.132    0.300
+4.90   0.135    0.300
+5.25   0.168    0.181
+6.00   0.120    0.016
```

## Reading (orchestrator, S150)
- MC_INDI_POS_TB 0.3 confirmed in the log's initial parameters. Only change vs S148 s1.
- TB explains most of the loss: 2.71 -> 1.95 m (limit 2.0, thin margin, one seed), back 3.31 -> 1.44 s.
- b still clamps at kMaxBlend 0.3 from +1.0 s to REC (gap 0.36 needs more): the bound is the next lever (D-GAP-G510 (2)).
- Tilt 45.3 deg = MPC_TILTMAX_AIR (Q9 a); AGG part never saturates (Q9 b): both open owner items, not this probe.
- Not gate evidence: TB 0.3 has no G2 outer-break margin yet (D-GAP-G510 accept condition).
