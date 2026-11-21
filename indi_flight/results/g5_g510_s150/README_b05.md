# G5.10 probe S150b: TB 0.3 s + kMaxBlend 0.5 (firmware 003e25c6d4), probe, not gate evidence

Build: `indi_project/docker/run.sh -n b05build -t 1500 "make px4_sitl_default"` (exit 0)

Fly: `indi_project/docker/run.sh -n g510b05 -t 700 -- python3 indi_flight/bench/run_scenario.py --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --params indi_flight/results/g5_g510_s150/params_tb03.params --scenario sat_sustained --out indi_flight/results/g5_g510_s150/s1_tb03_b05`

| run | alt_loss_m (limit 2.0) | tilt_max_deg | back_s_sat (limit 5) | loc |
|---|---|---|---|---|
| TB 1.0 / bound 0.3 | 2.71 | 45.33 | 3.31 | no |
| TB 0.3 / bound 0.3 | 1.95 | 45.34 | 1.44 | no |
| TB 0.3 / bound 0.5 (this run) | 1.77 | 45.34 | 1.87 | no |

Checker (`g510_check.py`): RESULT INVALID. PASS no_loc, PASS alt_loss, FAIL tilt, PASS back_sat, FAIL back_agg. Invalid reason: "no saturation in AGG part" (last_sat_agg_s None, back_s_agg None, overshoot_x_agg_m 2.00).

SAT = 58.926 s (sends.csv SIM_GZ_THR_SC=0.274 row, intended_sim_time_us 58926000).

Blend timeline, t relative to SAT (s): mean_u / blend
-0.50 0.137/0.000, 0.00 0.137/0.000, +0.25 0.066/0.058, +0.50 0.114/0.168, +0.75 0.155/0.281
+1.00 0.184/0.382, +1.25 0.198/0.456, +1.50 0.194/0.495, +1.75 0.168/0.483, +2.00 0.141/0.436
+3.00 0.117/0.306, +4.00 0.142/0.362, +4.90 0.137/0.367, +5.25 0.177/0.223, +6.00 0.120/0.019

Oddities: b.py printed a field-name list before the timeline. mean_u_valid = 1.000 at all rows. Tilt FAIL is the same 45.3 deg as the earlier rows. Output: indi_flight/results/g5_g510_s150/s1_tb03_b05.out, g510.json in the run dir.

## Reading (orchestrator, S150)
- Bound 0.5 removes the clamp: b settles at 0.367 (predicted gap 0.5 - 0.137 = 0.363). Alt loss 1.95 -> 1.77 m.
- b overshoots to 0.495 at +1.5 s (LP of a gap that itself moves while mean_u recovers); recovery 1.87 s (PASS 5).
- One seed, parallel-free, still a probe: the G2 outer-break margin at TB 0.3 is the accept condition (D-GAP-G510).
