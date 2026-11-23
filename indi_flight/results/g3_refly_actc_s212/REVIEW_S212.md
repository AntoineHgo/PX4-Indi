# REVIEW S212: bench code -> gate spec (GATES.md 784-807), independent

1. tau_mean: OK. g3_sample.py actc_block (l.416-424) uses factors tau_up/tau_down values (x nominal). Simulator path:
   hooks.model_variant tau=tau_scale, tau_up=f_up/tau_scale (g3_sample l.292-294) -> g3_run build_run --model-variant ->
   model_variant.py l.98-101 factor = tau x own -> timeConstantUp/Down x factor of quad5in model.sdf (0.033/0.033, l.12-13).
   Checked on all 300 samples: tau x tau_up = f_up and tau x tau_down = f_down within 2e-6; mc_indi_act_tc = r x tau_mean x
   0.033 within 3e-6. 28 inverted draws included (formula symmetric). Nominal 0.033 = params file (quad5in_indi_defaults,
   g5_freeze params MC_INDI_ACT_TC 0.033) = sdf. g3_run re-derives the block and refuses a stale one. Range 0.0146-0.0969,
   inside yaml [0.001, 0.2].
2. r: OK. sha256("173:actc_r:<source>") seeded random.uniform(0.88,1.02), deterministic, own stream. 300 values, min 0.88035,
   max 1.01983, mean 0.952 (expected 0.95); corr with tau_up -0.002, tau_down 0.038, mass 0.065. Every sample equals the
   REAL flown freeze-10 results/g3_campaign_f10/run_*/g3_draw.json draw (and campaign(173,300)) except run_index, source_run,
   block, actc: 0 diffs of 300.
3. Block 1: OK. Recomputed from SCORES.tsv (LHS, outcome not ok or key1/key2 != pass) = 50 draws (24 key1-only FAIL, 20 both,
   5 key2-only, 1 abort); equals the 50 chosen exactly. Of the 3 aborts (039, 245, 264) only one is an LHS draw. 60 corners
   all first (indices 0-59), block 1 = 110, block 2 = 190, each sorted by source. source_run, block in every sample and in
   index.json (+ scores_sha256 of SCORES.tsv). Note: selection includes item-3-only and single-key failures (broader than
   "item 1/2 on both keys"), consistent with "failed or aborted" in S211b.
4. Param path: OK. g3_run l.113-123 writes params["MC_INDI_ACT_TC"] -> merged_params -> g3_params.txt (--params); run_scenario
   applies overlay last in {BASE_PARAMS, STICK, overlay} via set_param (l.1088), after the airframe/base overlay; no later
   set_param of ACT_TC (only SIM_GZ_*); firmware reads it in the McIndiRateControl param update only. Applied value recorded in
   g3_draw.json build.applied.actc and run.json g3_actc_applied. Chain passes --samples and --require-actc to every flight
   (l.469-470), samples pinned in chain_samples and hashed into chain_freeze.sha256; g3_run/g3_sample are frozen inputs.
5. Halt logic: MINOR x2 (each is a way to continue past a failure).
   a. Resume gap: halt_on_fail_check is only called in the fly path (l.729). skip_done (l.636-646) scores a finished but
      unscored run (crash, hard stop, stop --now between flight and score) and never calls it: the failing run does not halt
      the chain on restart. Same for the STOP_NOW break at l.728.
   b. Score failure: if scoring leaves SCORE_PENDING (docker error, key 2 missing), `scored_ok || return 0` so the chain
      flies on without a halt; the pending score is only visible in status/SCORES.tsv.
   c. (info) Class 'other' (non-whitelisted exception, e.g. wall timeout in 'land') halts as abort_flight, consistent with
      the orchestrator decision. 'void' (validity) and infra do not halt (breaker applies). Item 1/2 intersect per item
      (jq); item1 on one key and item2 on the other does not halt.
   Item 3 alone does not halt; resumable via rm CHAIN_HALTED HALT_ON_FAIL.json; score runs before the check; halted DIR
   refuses start; flag pinned in chain_halt_on_fail. Fix suggestion: call the check from skip_done and halt on a
   scored-pending run. The new tests do not cover 5a/5b.
6. Tests (python3 file.py; pytest and scipy absent on host): test_g3_refly_s212 13 passed, test_g3_run, test_g3_sample (0
   failures), test_provenance ALL PASS, test_run_validity rc 0, test_g3_excursion_key2, test_g3_harness_abort,
   test_g3_line_trace pass. test_g3_checks, test_g3_excursion_s186, test_g3_checks_key2_q14_q15 not run (no scipy/pytest
   on host; unrelated to the change). shellcheck g3_chain.sh: 0 findings.
