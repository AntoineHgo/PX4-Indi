# G3 re-fly prep (S212): ACT_TC per run, critical-first order, halt flag

Files: bench/g3_sample.py (`refly`), bench/g3_run.py (`--samples`, `--require-actc`, actc override), bench/g3_chain.sh
(`--samples`, `--halt-on-fail`, test hook G3_CHAIN_TEST_SCORE_CMD), bench/tests/test_g3_refly_s212.py (13 tests, all pass).

Sample set: `samples/` (300 run JSONs + index.json), made by
`python3 indi_flight/bench/g3_sample.py refly 173 --scores indi_flight/results/g3_campaign_f10/SCORES.tsv --out indi_flight/results/g3_refly_actc_s212/samples --expect-block1 50`
- Draws are the freeze-10 draws unchanged (all 300 compared field by field with g3_campaign_f10/run_NNN/g3_draw.json: 0 differences).
  New fields: `actc` {actc_ratio, tau_mean, mc_indi_act_tc}, `source_run`, `block`; run_index renumbered.
- Block 1 = 110 runs: run_000-059 the corners (source 240-299), run_060-109 the 50 LHS draws below. Block 2 = 190 LHS (run_110-299).
- 50 critical LHS = SCORES.tsv rows of LHS draws (source 0-239) with outcome not ok (aborted/void), or key 1 FAIL, or key 2 FAIL
  (the failing columns list items 1-3 only): 49 scored runs with a FAIL on either key + the one LHS abort (039). The aborts
  245 and 264 are corners, already in block 1. Count is 50 as expected (--expect-block1 50 stops otherwise).
  Source indices: 2 3 8 20 23 24 25 29 31 39 42 45 46 52 54 59 62 67 77 86 90 94 98 107 109 112 115 120 133 137 139 147 153
  160 167 174 175 182 189 195 200 204 205 206 209 220 221 225 230 239.
- r = random.Random(int from sha256 of "master:actc_r:source").uniform(0.88, 1.02); ACT_TC = round(r x (tau_up+tau_down)/2 x 0.033, 6).
  r min 0.8804 max 1.0198 mean 0.9519; ACT_TC min 0.014625 max 0.096939 s; firmware range 0.001-0.2: no clipping.
  corr(r, tau_mean) = 0.022, corr(r, tau_scale) = 0.018.
- Runner: MC_INDI_ACT_TC from the draw replaces the params-file 0.033 (g3_params.txt, checked by run_validity against the
  ulog), and is recorded as `g3_actc_applied` in run.json and `applied.actc` in g3_draw.json. A draw without `actc` is
  unchanged unless --require-actc (the chain passes it with --samples). The block is re-derived from the drawn tau; a stale one is refused.
- Chain: samples dir pinned in DIR/chain_samples and hashed into chain_freeze.sha256; --halt-on-fail pinned in DIR/chain_halt_on_fail.
  Halt = item1 or item2 FAIL on both keys (key1_failing and key2_failing both contain it), after both keys score the run:
  CHAIN_HALTED ("HALT_ON_FAIL run_NNN (source run S): itemX ..."), HALT_ON_FAIL.json, state halted. Resume: remove CHAIN_HALTED and
  HALT_ON_FAIL.json, then start again (the failed run is kept, not re-halted).

Launch (not run):
`bash indi_flight/bench/g3_chain.sh start indi_flight/results/g3_refly_actc_s212 --samples indi_flight/results/g3_refly_actc_s212/samples --speed 4 --halt-on-fail`

Binary: pins build/px4_sitl_default/bin/px4, sha256 d220e193...d46076 = FREEZE_BINARY_SHA = freeze-10 chain pin; the current build
matches, no --allow-binary needed. The docker image id also equals the freeze-10 pin.

Open points: an aborted run (watchdog tilt/height) is UNSCORED and does not trigger the halt (spec: FAIL on both keys); the existing
3-void / 10-other circuit breakers still apply. The chain self-test uses a fake docker on PATH; nothing was flown.

Update (coordinator): with --halt-on-fail the chain also halts on an aborted run that is a flight result (chain class "flight", O-12 watchdog, or "other"); infra aborts are unchanged (retried, then CHAIN_FAILED). HALT_ON_FAIL.json then has reason "abort_flight" and the run index. This replaces the earlier open point. Self-test cases added (watchdog abort halts, infra abort does not); all tests pass.

Update (review check 5): --halt-on-fail now also judges a run scored on restart (skip_done; an already scored halting run is not judged again) and halts with reason "score_pending" (run index) when scoring leaves no score.
Self-test cases e (skip_done halt, then clean resume) and f (score_pending) added; the new test (about 2.5 min) and the existing g3 tests, bash -n and shellcheck pass.
