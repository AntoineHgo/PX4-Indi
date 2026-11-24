# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 6 (validation). FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params (XY gains at
  firmware defaults 1.2/2.4). Later firmware commits behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL).
- Gates: see GATE_STATUS.tsv. G3 NOT PASSED twice (S199, S213 C3 LOC draw 264). Q31 answered S218 (route B+).
  Controller ACT_TC box r [0.88, 1.02] x tau_mean (D-OWNER-Q28). FREEZE-10 stays; firmware change only per Q31.
- RC208 (design/route_check_208.md): G7 (g), F-10 unit 9/review, harness extraction, dead-path removal deferred
  (firmware may change). Only G8 text may run alongside.
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
-1. Gate binary = 903eae63 (D-BINARY-GZFIX; FREEZE-10 + GZBridge fix f110361a33; old px4.freeze10_d220e193;
   g3_chain.sh pins it). Do NOT rebuild build/px4_sitl_default from HEAD. Pre-S214 C3 runs: GATES 2 invalid.
0. G3 item 1 (D-OWNER-Q31 escalation): minimal case = results/g3_refly_actc_s212/restore264 joint variant (sat 0.351
   + weak 0.709, rest nominal): INDI LOC at fault+1.1 s, PID survives (pid_joint). Investigators DONE S221
   (restore264/INVESTIGATION_A.md, _B.md agree): no saturation before LOC; weak motor = torque bias growing with
   collective; measured-torque anchor leaks (eff 0.351), only integral left is the 1 s blend (MC_INDI_ACT_BLD,
   indi_rate_control.cpp:336-357) -> INDI P 0.011 vs PID 0.03 + integrator. Re-opens decision 2 (gap remover).
   NEXT: param-only falsifier probes on joint (sonnet, existing runner): ACT_BLD 0.15; measured feedback off.
   Survive -> opus/high solver + independent reviewer (pre-approved): fix design (commanded-torque anchor or fast
   gap fold-in; outer demand capped to available thrust), fix probe on joint, then draw 264; names re-flown rows.
   Still LOC -> owner question (continue / stop, incl. "264 = documented feasibility limit", RC220 item 6).
   Before the next G3 campaign: Q30 tooling (GATES "Owner amendment S214"). Class C skipped lines both stacks.
1. G6 item 7 chain (60 corners, results/g6_item7_s212/PREP.md): CUT RC221 until the Q31 route ends (a firmware
   fix would invalidate it). MAX_STRUCTURE 0.08 vs norm residual > 0.05 (actc_grid_s209 PRETEST.md) revisited then.
S222 route check (supervisor, GATE_STATUS unchanged 4 sessions): RC221 (S221) still current, no new RC filed.
  Only blocker of the next verdict change = G3 item 1 Q31 route (action 0). g3_campaign_f10 committed, verdict
  written (GATES 725). Extra cut: G8 drafting paused until the Q31 route decides firmware (budget to action 0 only).
CUT RC208/RC221: action 3 (f) unit 9, (g), harness extraction, dead path, older G7 list deferred until the Q31
  route decides whether firmware changes. Saturation sweep only if an investigator asks. G8 drafting continues.
2. G5 trap: key2 rows script writes results/g5_events_s145/key2_rows.md (fixed path): `git checkout` it after use.
3. G7 open items: (f) F-10 clean-up per results/g7_s198/F10_PLAN.md (build dir build/f10_sitl, unit tests in
   build/px4_sitl_test). Units 1-8 done; unit 8 review MINORs (wording, F10_UNIT8_REVIEW.md) go into the
   whole-branch pass. Then unit 9 (public renames listed in F10_UNIT2..7 "not renamed"), then the
   independent F-10 review over the whole branch + id grep. Never during gate flights.
   (g) build check of indi-fw-pr with the worktree OUTSIDE the repo (re-run make_fw_branch.sh --force-recreate after
   any firmware commit; quad5in model lives in indi_flight/sim, not in the branch). v6x flash overflow 23.5 kB ->
   report/upstream note. Tests build in px4-indi-sim (px4-dev fails protobuf).
   Dead path: IndiAccelControl K_pos/K_vel cascade unused (module always accel_only, McIndiPosControl.cpp:315):
   remove after Q26 (behaviour change review) or justify.
   Harness extraction (D-G7-HARNESS, firmware refactor) after Q26, with its re-fly named. Older list (justify in
   writing): MC_INDI_ID_OK call site (K128 MAJOR, fix after Q26), D-JFF-SOURCE case, D-OFFB-POSVEL wiring test,
   omega_ff step on offboard entry; g510 LOC on one sample (stricter than GATES 0.2 s,
   results/g7_checkers_s215/README.md: justify or align); ACT_TC/W_MAX firmware vs
   bench (lesson 12); guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
4. G6: item 7 runs in the action-0 chain. ID_OK 0 waits for G6 (D-G7-DEFAULTS).
5. G8: drafts report/02_outer_loop_design.md and docs/en/config_mc/indi_control.md; open items in
   report/DOCS_DRAFT_S201.md (S213: code items resolved; identification user steps = G6; prettier/link check open).
   S213 finding: airframe requirement R1 (refuse to arm without eRPM) is not enforced by code (modelled fallback
   only): G7/G8 decide enforce (firmware, after Q31) or reword R1. S215 drafts: report/01_inner_loop_design.md,
   06_bringup_checklist.md, S216 A_history_errata.md (their "Unverified" sections are open G8 items). Missing: ch.3 G3/G6
   sections and limits (after Q31); numbers in ch.3 follow any re-fly a Q31 fix causes. G7 parameter pass: MC_INDI_ACT_TC yaml still says "round up" (overturned, D-OWNER-Q27);
   pos module reads esc_status instance 0 only, no frozen/error-count check, 100 ms ESC age vs 20 ms in rate module.
Rules: 1 session per inner-loop law change; parallel docker streams only for tolerance-insensitive probes, never gate
  evidence, never a docker build during gate flights; G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1. Next RC:
  S235 (last RC220).
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
| S222-P | Q31 falsifier probes P1 ACT_BLD 0.15, P2 measured feedback off (joint) | sonnet | results/g3_refly_actc_s212/restore264/falsifier_s222/README.md | re-brief from next action 0 if README missing |
## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): `module_parity.md` for stage 5.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
