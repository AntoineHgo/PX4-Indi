# G6 item 7 tally, runs 240-299 (S244)

Command: `bash indi_flight/bench/g3_chain.sh rescore indi_flight/results/g6_item7_s212 > indi_flight/results/g6_item7_s212/rescore_s244.log 2>&1`
Result: log says "rescored 0 run(s)". Every run already has a valid chain_score.json, so `scored_ok` skips it and no checker ran. Re-scoring would need `score()` (docker), which was out of scope. The tally below uses the existing scores from the earlier checkers, not recomputed ones.

Validity: 54 valid (chain_class ok), 6 invalid.
- 262: flight watchdog, > 3.0 m below hold altitude for 1.0 s
- 264: flight watchdog, height < 0.3 m
- 269: flight watchdog, tilt > 60 deg for 0.5 s
- 274: other, wall timeout (103 s) in phase scenario:traj
- 284: void, indi_rate_status median rate None Hz; MC_INDI_POS_EN 1 without indi_pos_status samples
- 292: flight watchdog, tilt > 60 deg for 0.5 s

Tally over the 54 valid runs (fails = pass false; missing = 0 in all cases):

| item | key 1 fails | key 2 fails | runs differing K1 vs K2 |
|---|---|---|---|
| 1 loss of control (item1_loc) | 2 | 2 | 0 |
| 2 sustained oscillation (item2_oscillation) | 21 | 22 | 1 (run 276) |
| 3 steady state | 2 | 2 | 0 |
| 4 tracking | 18 | 18 | 0 |
| 5 recovery | 30 | 30 | 0 |
| 6 rate hold | 0 | 0 | 0 |

Overall pass: key 1 12/54, key 2 12/54. Overall SCORES key1 and key2 agree on all 54 valid runs.

Item 1 failing runs (both keys): 278, 295
Item 2 failing runs, key 1 (21): 241-249, 257, 260, 270, 272, 277, 278, 290, 293-297
Item 2 failing runs, key 2 (22): same as key 1 plus 276

Item 2 disagreement: run 276 fails item 2 in key 2 only.

Corner mapping: PREP.md gives C1-C6 as corner ids for the 60 runs but no per-run mapping. No file in the results directory maps runs to corners, so per-corner failures are not reported.

Unverified: the checkers were not re-run. Item 2 in key 2 and key 1 were compared only on the stored pass fields.
