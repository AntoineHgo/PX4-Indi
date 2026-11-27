# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Final summary (S257, 2026-11-27; DONE created, removed by owner with Q36 answer B: R1 firmware work open)
- G1, G2, G4, G5, G7, G8 PASSED (G7, G8 with justified limits). G3 NOT PASSED (final, owner Q35 A: draw 3 INDI-only
  2 Hz pitch, draw 264 LOC on saturation + weak motor). G6 NOT PASSED (needs G3; item 7 6/58 failures). All written
  up with data: GATES.md verdict sections, report 03_validation 3.3/3.6, 04_limits 4.1/4.2. Simulation only.
- Q36 answered B: R1 now enforced in firmware (S258, e6af4b6b0d). Open: Q37 (report/GATES/docs/branch update, W_MAX 0
  hole). Clean firmware-only branch exists (G7) without the R1 commit yet; no PR opened.

## Status
- Stage: 7 done. G3 FINAL NOT PASSED (owner Q35 A, GATES "Owner amendment S243"); G6 NOT PASSED (S244).
  FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params. Later firmware commits
  behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL). No gate flights remain.
- Gates: see GATE_STATUS.tsv. G7 PASSED S252. All gates have verdicts. Q37 open (blocking: WAIT_OWNER).
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
RC247 (design/route_check_247.md) cut list, no code work, each becomes one justification line in the G7/G8 verdict:
unit 9 renames (except those the whole-branch F-10 reviewer flags), K_pos/K_vel dead path (module always accel_only,
McIndiPosControl.cpp:315), harness extraction (D-G7-HARNESS), MC_INDI_ID_OK call site (K128), D-JFF-SOURCE,
D-OFFB-POSVEL wiring test, omega_ff step on offboard entry, g510 one-sample LOC (results/g7_checkers_s215),
ACT_TC/W_MAX vs bench (lesson 12), guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced, pos module esc_status
instance 0 / 100 ms age, G6 item 2 ID-window rescore, MC_INDI_ACT_TC yaml "round up" wording (D-OWNER-Q27).
Plan: BLOCKED on Q37 (WAIT_OWNER). Q36 B done S258: rpm arming check e6af4b6b0d, 5/5 tests break-checked, review
 0 BLOCKER (results/q36_s258/). On the Q37 answer: A/B -> cherry-pick onto firmware-only branch + G7 re-checks (one
 sonnet task), (B: W_MAX 0 refusal + 6th test, two keys), then report R1 + 04_limits limits (1)-(5), docs page, GATES
 G8 "pending Q36" dropped, recreate DONE; C -> report text only. Do not touch report/GATES/docs before the answer.
Gate binary = 903eae63 (D-BINARY-GZFIX): do NOT rebuild build/px4_sitl_default from HEAD. G3 chain stopped for good
(Q35 A): the supervisor "g3_campaign_f10 chain finished" line is hardcoded and stale (S199 closed it): ignore it.
Route check: RC256 current (S257 supervisor request answered by RC256, one session old; its cut was acted on).

## Notes
- G5 trap: key2 rows script writes results/g5_events_s145/key2_rows.md (fixed path): `git checkout` it after use.
- chatter_cruise_s176.py without RAW= overwrites tracked results/g4_gate_s169/chatter_cruise_s176_raw.txt.
- Nominal plant: matched GNSS --gps-dly 110 --gnss-delay 110. G4 typical noise: --vib-acc 10 --vib-gyr 0
  --imu-noise-scale 4.0 (D-NOISE-PROF).
- Runner traps: MC_INDI_EN 1 in a params file does not start the module, only MC_RATE_CTL_TYPE 1 does.
  margins_of hangs if ts_true=0. Logger misses the first ~0.2 s of indi_pos_status (late subscription).
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); MC_INDI_ID_OK 0 halves K.
- Guard blocks long `git commit -m`: use `-F <file>`. Guard denies a segment naming indi_project with rm/tee/git
  apply; run each run.sh call alone, redirect only into indi_flight/.
- Worktrees and big builds go OUTSIDE the repo (S196 OOM: VS Code indexed an in-repo worktree to 23 GB).
- Before editing any file under bench/, check no chain pins it (chain_freeze.sha256).

## Tasks in flight
None. Firmware after FREEZE-10: e6af4b6b0d (R1 arming check, owner-lifted freeze, gate rows not invalidated).
Commit trailer: AGENTS.md wins: `Assisted-by:` only.

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests: justify in the G7 verdict.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
