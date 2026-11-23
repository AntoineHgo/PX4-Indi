# Pretest S212 (started 2026-11-23T19:36:12+01:00)
Step 0: lock free (flock), docker ps empty, no chain running.
Step 1 (chain 110-111, speed 4, halt-on-fail; finished 19:37:58, ~1 min per flight):
a. run_110 outcome ok, run_111 outcome ok (both flew to end). Scores: 110 key1 pass key2 pass; 111 key1 FAIL key2 FAIL item3 (a legitimate flight result, not item 1/2, no halt).
b. ulog MC_INDI_ACT_TC: 110 = 0.021177 (sample 0.021177), 111 = 0.023403 (sample 0.023403); g3_actc_applied present in both run.json; run_validity checked ACT_TC want==got.
c. scoring present: SCORES.tsv has both rows, chain_score.json per run, key2 files; items 1-3 scored.
d. binary sha d220e19315c2798aa18a1bab6ce7300cd0f6eff14d43273d5064c06009d46076 = PREP.md pin.
No set-up fault. Launching the real chain.
Step 2: real chain launched 2026-11-23 19:42:07, chain pid 588997 (waiter 588990). At 19:43 run_000 done ok (scored pass/pass), run_001 flying.
