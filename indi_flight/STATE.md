# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params (XY gains at
  firmware defaults 1.2/2.4). Later firmware commits behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL).
- Gates: see GATE_STATUS.tsv. G1, G2, G4, G5 PASSED; G3 NOT PASSED at freeze-10 (S199). No open question.
- Q27 closed S208 (D-OWNER-Q27, GATES "Owner amendments S208"): identify ACT_TC first; G3 controller-ACT_TC box written
  from the measured ident error bound, then Q28 to the owner with bound + box, then G3 re-fly (300) and G6 item 7.
  FREEZE-10 stays; a firmware change needed by the identification is asked first. S53 round-up rule overturned.
- RC208 (design/route_check_208.md): long pole = ACT_TC ident + error table; offline error grid first, few
  confirmation flights; reuse ident chain, new code = sweep driver only. G7 (g), F-10 unit 9/review, harness
  extraction, dead-path removal stay deferred (firmware may change). Only G7 unit 8 and G8 text may run alongside.
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
CUT RC208: next actions 3 (f) unit 9, (g), harness extraction, dead path, older G7 list stay deferred until the ACT_TC
  ident decides whether firmware changes. G8 drafting only after the Q28 answer.
1. G3/G6 ACT_TC identification (Q27 item 1): survey design/actc_ident_survey_s208.md -> one-page design note ->
   estimator + synthetic self-test (asym tau, delay, closed loop) -> second key -> offline error grid -> few SITL
   confirmation flights -> bound -> capped/two-sided ACT_TC rule with model margins on corners -> GATES G3 box
   draft -> Q28. Next: FRD fix (sub-sample delay bias) checked against key-2 indep*.py -> 2-flight pre-test ->
   30-flight grid (g3_run/run_scenario hooks, ID_OK 0, injector roll then pitch). Synthetic: tau_sym = 0.61 x
   tau_slow, 0.92 x tau_mean at asym 3 (input to the ACT_TC rule). rpm_max only scales y (gain), not tau.
   Quality thresholds set on synthetic noise: check against SITL residuals in the pre-test before the grid.
   Next G3 scoring also: re-fly the 15 freeze-10 item-3 misses at speed 1; table class C skipped lines both stacks.
   g3_campaign_f10 chain: committed, verdict written S199 (GATES "G3 verdict at freeze-10"); nothing to rescore.
2. G5 trap: key2 rows script writes results/g5_events_s145/key2_rows.md (fixed path): `git checkout` it after use.
3. G7 open items: (f) F-10 clean-up per results/g7_s198/F10_PLAN.md (build dir build/f10_sitl, unit tests in
   build/px4_sitl_test). Next unit 8 (yaml/msg/ROMFS/Kconfig, param-metadata diff check; yaml text fixes LND_SLEW unit, PINJ_* long text from
   report/DOCS_DRAFT_S201.md), then unit 9 (public renames listed in F10_UNIT2..7 "not renamed"), then the
   independent F-10 review over the whole branch + id grep. Never during gate flights.
   (g) build check of indi-fw-pr with the worktree OUTSIDE the repo (re-run make_fw_branch.sh --force-recreate after
   any firmware commit; quad5in model lives in indi_flight/sim, not in the branch). v6x flash overflow 23.5 kB ->
   report/upstream note. Tests build in px4-indi-sim (px4-dev fails protobuf).
   Dead path: IndiAccelControl K_pos/K_vel cascade unused (module always accel_only, McIndiPosControl.cpp:315):
   remove after Q26 (behaviour change review) or justify.
   Harness extraction (D-G7-HARNESS, firmware refactor) after Q26, with its re-fly named. Older list (justify in
   writing): MC_INDI_ID_OK call site (K128 MAJOR, fix after Q26), D-JFF-SOURCE case, D-OFFB-POSVEL wiring test,
   omega_ff step on offboard entry; checker defects in bench/tests/SELFTEST_G7_S194.md (no verdict, no LOC check in
   offb_vel_check, IndexError on empty topic); g511_check.py:184; g510_check.py:115-119; ACT_TC/W_MAX firmware vs
   bench (lesson 12); guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
4. G6: runs (GATES section 6) wait on the ACT_TC ident and Q28. ID_OK 0 waits for G6 (D-G7-DEFAULTS).
5. G8 (paused until Q28): drafts report/02_outer_loop_design.md and docs/en/config_mc/indi_control.md; open items in
   report/DOCS_DRAFT_S201.md (arming refusal without eRPM: check code or reword; identification user steps = G6).
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence, never a docker build during gate flights; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC:
  S218 (RC203).
STOP list (+RC194: A-53/A-54/A-58 bound-only, A-50/A-51 model x-check, G5.5 margin): A-39 / yaw measured-path chase,
  PID M1 hook, hooks without a consumer, stand-alone anomaly chases, --sched-anchor and set_param fixes, EdgeState
  design, more PID G5.10 runs.

## Notes
- Nominal plant: matched GNSS --gps-dly 110 --gnss-delay 110. G4 typical noise: --vib-acc 10 --vib-gyr 0
  --imu-noise-scale 4.0 (D-NOISE-PROF).
- G3 tooling: g3_run.py, quad5in variants, overrides/wind/motor_fault/timed eRPM loss. eRPM-loss lateness 36-122 ms:
  take effective time from the log. Weak+sat unflown. Acro G3-unprobed (G5 carries it). altctl/posctl not in MODE_MIX.
- pretest_gate only on stationary scenarios, or end its window at the fault (S98). SIM_GZ_SEED + SIM_GZ_IMU_NSC hooks.
- Stabilized stick centre = HTE; runner thr0 honours HTE valid flag, fallback MPC_THR_HOVER.
- Runner traps: pid_default + params with MC_INDI_EN 1 flies INDI (s148). MC_INDI_EN 1 in a params file does not start
  the module, only MC_RATE_CTL_TYPE 1 does. Pilot sticks kept after LAND -> RC override to POSCTL. margins_of hangs
  if ts_true=0.
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); MC_INDI_ID_OK 0 halves K.
- Guard blocks long `git commit -m`: use `-F <file>`. Guard denies a segment naming indi_project with rm/tee/git
  apply; run each run.sh call alone, redirect only into indi_flight/.
- chatter_cruise_s176.py without RAW= overwrites tracked results/g4_gate_s169/chatter_cruise_s176_raw.txt: brief
  agents to set RAW to their own folder; `git checkout` it if dirty.
- Detached chains: list every waiter pid in Tasks in flight.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
- Worktrees and big builds go OUTSIDE the repo (S196 OOM: VS Code indexed an in-repo worktree to 23 GB).

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| FRD | fractional-delay fix of ident_actc.py (KEY2 item 2 + MINORs) | sonnet | bench/tests/SELFTEST_IDENT_ACTC_S208.md "Fix S208" | S209: code edits left uncommitted, no section; FRD2 agent verifies + writes section, then commit |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
