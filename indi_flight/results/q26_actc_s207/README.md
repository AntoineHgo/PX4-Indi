# Q26 check flight batch (S207)

Purpose: owner Q26 item 1. Re-fly the 8 S199 re-fly draws at speed 1 (same index and seeds, FREEZE-10 binary d220e19315c2, params file overrides only) with MC_INDI_ACT_TC set to the drawn plant motor time constant, to decide whether a correctly identified time constant removes the G3 robustness failures.
- set a: MC_INDI_ACT_TC = tau_slow = max(tau_up, tau_down) (perfect identification)
- set b: MC_INDI_ACT_TC = 1.5 x tau_slow (round-up error)
Everything else as in the campaign. Scored with key 1 and key 2 by g3_chain.sh. No G3 campaign re-fly.

## Draws (draws.tsv)
Plant tau read from results/g3_campaign_f10/run_NNN/model_variant/quad5in/model.sdf (timeConstantUp/Down = 0.033 s x drawn tau_up/tau_down factor).

| idx | tau_up s | tau_down s | tau_slow s | ACT_TC a | ACT_TC b |
|---|---|---|---|---|---|
| 245 | 0.099000 | 0.085848 | 0.099000 | 0.099000 | 0.148500 |
| 264 | 0.016500 | 0.019887 | 0.019887 | 0.019887 | 0.029830 |
| 008 | 0.016500 | 0.019169 | 0.019169 | 0.019169 | 0.028753 |
| 240 | 0.034557 | 0.099000 | 0.099000 | 0.099000 | 0.148500 |
| 283 | 0.016500 | 0.016500 | 0.016500 | 0.016500 | 0.024750 |
| 239 | 0.061163 | 0.084112 | 0.084112 | 0.084112 | 0.126168 |
| 046 | 0.064212 | 0.064938 | 0.064938 | 0.064938 | 0.097407 |
| 039 | 0.081298 | 0.089426 | 0.089426 | 0.089426 | 0.134139 |

Clamp check: MC_INDI_ACT_TC yaml min 0.001, max 0.2; indi_rate_control.cpp:49 constrains to [0.001, 0.2]. Range flown 0.0165 to 0.1485 s: no clamping.

## Tooling change
indi_flight/bench/g3_chain.sh takes the params file from env G3_PARAMS (default unchanged, g5_freeze_s157/params.params). It is pinned per DIR in DIR/chain_params at the first start (also hashed in chain_freeze.sha256 and shown as "params" in chain_status.json); a later start with a different G3_PARAMS is refused; DIRs without chain_params use the default.

## Pre-test (a_245)
Passed. g3_params.txt, merged_params and the ulog initial parameters hold MC_INDI_ACT_TC 0.099 (ulog 0.0989999995). g3_draw.json equals the S199 re-fly draw except output paths and ACT_TC (same seeds, same model-variant args, same tau sdf). Chain accepted the FREEZE-10 binary d220e19315c2 without --allow-binary. Result key1 pass, key2 pass.

## Run / resume
Files: params/{a,b}_NNN.params, refly_q26.sh, progress.txt, chain dirs a_NNN/ b_NNN/, DONE marker at the end.
Resume (skips finished dirs, any cwd):
`setsid nohup bash /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/q26_actc_s207/refly_q26.sh >/dev/null 2>&1 </dev/null &`
A dir with CHAIN_HALTED is skipped until the marker is removed.

## Results
| idx | class | ACT_TC a / b (s) | S199 INDI s1 | PID s1 | set a k1/k2 | set b k1/k2 |
|---|---|---|---|---|---|---|
| 245 | C1, LOC | 0.099000 / 0.148500 | ABORT height < 0.3 m at 65.05 s | ok, no LOC; k1/k2 FAIL item2 p 2.75 Hz 7.5 | PASS / PASS | PASS / PASS |
| 264 | C3, LOC | 0.019887 / 0.029830 | ABORT tilt > 60 deg at 60.91 s | ok, no LOC; k1 PASS, k2 FAIL item2 r 2.5 Hz 9.7 | ABORT tilt > 60 deg at 60.93 s | ABORT tilt > 60 deg at 60.93 s |
| 008 | A | 0.019169 / 0.028753 | k1/k2 FAIL q 10.75 Hz 7.1/8.1 | k1/k2 FAIL p 11.0 Hz 161/207 (r 8 Hz) | k1 FAIL q 2.0 Hz 10.5, k2 PASS | k1/k2 FAIL q 10.75 Hz 6.0/7.0 |
| 240 | C1, class C | 0.099000 / 0.148500 | k1 FAIL p 2.25 Hz 8.6, k2 PASS | k1 FAIL q 3.25 Hz 5.9, k2 PASS | k1 FAIL q 2.0 Hz 5.1, k2 PASS | PASS / PASS |
| 283 | C5, A | 0.016500 / 0.024750 | k1/k2 FAIL q 10.75 Hz 18.2/18.1 | PASS / PASS | PASS / PASS | k1/k2 FAIL q 10.75 Hz 9.2/13.3 |
| 239 | B (LHS, largest) | 0.084112 / 0.126168 | k1/k2 FAIL p 2.0-2.5 Hz 76.6/76.0 | PASS / PASS | PASS / PASS | PASS / PASS |
| 046 | D | 0.064938 / 0.097407 | k1 FAIL p 2.5 Hz 14.3, k2 FAIL p 2.5 Hz 31.5 | PASS / PASS | k1 PASS, k2 FAIL p 2.0 Hz 13.4 | PASS / PASS |
| 039 | harness | 0.089426 / 0.134139 | ABORT land wall timeout; k1/k2 FAIL q 2.0-2.5 Hz 16.9/21.4 | ABORT land wall timeout; PASS / PASS | ABORT land wall timeout; PASS / PASS | ABORT land wall timeout; PASS / PASS |

- LOC (tilt > 60 deg abort): set a 1/8 (264), set b 1/8 (264). 245 has no LOC in either set. 264 has no g3_checks.json and no key2 json in either set (SCORE_PENDING marker); the other 14 runs have both.
- Item-2 fails, set a (7 scored runs): key 1 2 (008 q, 240 q); key 2 1 (046 p). Set b: key 1 2 (008 q, 283 q); key 2 2 (008 q, 283 q). Item 1 and item 3 pass in every scored run.
- 039 aborts in both sets: wall timeout 240 s in phase land (sim t 322.75 in a, 322.74 in b); key 1 and key 2 scored PASS in both.
- Verdict differs from S199 INDI s1 in set a on 245, 008, 240, 283, 239, 046, 039 (only 264 unchanged); in set b on 245, 240, 239, 046, 039.
- Set b keeps the S199 q 10.75 Hz line on 008 and 283 (RMS 6.0/7.0 vs 7.1/8.1 and 9.2/13.3 vs 18.2/18.1).
