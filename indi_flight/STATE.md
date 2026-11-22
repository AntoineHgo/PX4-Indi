# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params (XY gains at
  firmware defaults 1.2/2.4). Later firmware commits behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL).
- Gates: see GATE_STATUS.tsv. G1, G2, G4, G5 PASSED; G3 NOT PASSED at freeze-10 (S199). Q26 open (A / B / C).
- Q26 closed S207: items 1-4 done (results/q26_actc_s207, q26_kscale_s207, q26_264_s207); Q27 asked (box C1/C2/B,
  K fixed, 264 K probe, pre-ID G6 item). No box, gate text or firmware change before its answer. G3, G6, G7, G8
  verdicts wait on Q27: WAIT_OWNER set S207. On answer: act per Q27 (C1 = G3 campaign re-fly with controller ACT_TC
  drawn in U[1,1.5] x tau_slow, g3_chain.sh G3_PARAMS / g3_run tooling; class C rule into GATES if accepted).
- CUT RC207 (design/route_check_207.md): until Q27 is answered only Q26 items 1-5; next action 3 (f)(g) and the
  older G7 list, next action 5 (G8 drafting) and the g3_score key-1 fix stay deferred.
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
CUT RC202 (design/route_check_202.md): no further 283/264 modelling; G8 report/docs drafting paused until Q26;
  G7 older list justified in writing (not fixed) except MC_INDI_ID_OK call site (firmware: after Q26) and the
  offb_vel_check checker defects; F-10 units merged in pairs. No firmware law change, no G3 re-fly before Q26.
CUT RC203 (design/route_check_203.md): F-10 unit 9 and the whole-branch F-10 review deferred until after Q26 (one
  batch after the freeze decision); no new work after YAW-FIT and F10-U8: then WAIT_OWNER. Not taken: the RC203
  proposal of a default answer B to Q26 by S206 (Q26 decides a gate verdict: blocking, owner's call only).
1. G3 NOT PASSED (GATES "G3 verdict at freeze-10"; FAILS_S199.md, g3_refly_s199/SUMMARY.md, CAUSE_S199.md,
   MARGINS_S200.md). Cause search closed. Under A/C: FREEZE-11 re-flies G2, G4, G5, G3 (tooling: bench/g3_chain.sh,
   README in results/g3_campaign_f10, speed-1 rule in its speed_check/README.md; refly list with PID twins:
   results/g3_refly_s199/refly_all.sh). Side defect: key 1 (g3_score.sh) scores landing windows that key 2 skips
   (class C, 25 runs): fix before any G3 re-score.
2. G5 PASSED at freeze-10 (S198). A firmware change after the freeze re-opens the rows it touches.
   Trap: key2 rows script writes results/g5_events_s145/key2_rows.md (fixed path): `git checkout` it after use.
3. G7 open items: (f) F-10 clean-up per results/g7_s198/F10_PLAN.md; units 1-7 done (F10_UNIT1..7.md: build dir
   build/f10_sitl, unit tests in build/px4_sitl_test, objdump identical; two "INDI stage" log strings left). Next
   unit 8 (yaml/msg/ROMFS/Kconfig, param-metadata diff check; yaml text fixes LND_SLEW unit, PINJ_* long text from
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
4. G6: yaw fit keyed (57e80feac8 + test fix c7ec0740be), A-44 closed (207.5/208.1 vs 205.3,
   results/ident_yaw_a44_s205). G6 runs (GATES section 6) wait on Q26 (ACT_TC identified or not). ID_OK 0 waits for
   G6 (D-G7-DEFAULTS).
CUT RC204 (design/route_check_204.md): after the yaw fit is keyed, nothing advances a gate without Q26: WAIT_OWNER.
CUT RC205 (design/route_check_205.md): same; only G6 yaw key 2 then A-44 closing run (existing logs
  results/ident_m3a_s123/{axyaw,half_ax3}, commands in fit_yaw_s125.md, no flights) before WAIT_OWNER. F-10 unit 9,
  F-10 review, G8 drafting, g3_score key-1 fix stay deferred.
5. G8 (paused until Q26): drafts report/02_outer_loop_design.md and docs/en/config_mc/indi_control.md; open items in
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
| - | none | - | - | - |

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
