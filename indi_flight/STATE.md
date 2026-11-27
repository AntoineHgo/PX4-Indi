# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 7 (G7, G8). G3 FINAL NOT PASSED (owner Q35 A, GATES "Owner amendment S243"); G6 NOT PASSED (S244).
  FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params. Later firmware commits
  behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL). No gate flights remain.
- Gates: see GATE_STATUS.tsv. G7 PASSED S252. Open: G8. Q36 open (R1 wording), blocks only the G8 R1 text.
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
RC247 (design/route_check_247.md) cut list, no code work, each becomes one justification line in the G7/G8 verdict:
unit 9 renames (except those the whole-branch F-10 reviewer flags), K_pos/K_vel dead path (module always accel_only,
McIndiPosControl.cpp:315), harness extraction (D-G7-HARNESS), MC_INDI_ID_OK call site (K128), D-JFF-SOURCE,
D-OFFB-POSVEL wiring test, omega_ff step on offboard entry, g510 one-sample LOC (results/g7_checkers_s215),
ACT_TC/W_MAX vs bench (lesson 12), guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced, pos module esc_status
instance 0 / 100 ms age, G6 item 2 ID-window rescore, MC_INDI_ACT_TC yaml "round up" wording (D-OWNER-Q27).
Plan (order):
 P5 NEXT: G8 gaps + verdict: bench/gate_g8.sh all 7 PASS S253 (results/g8_s253); report drafts 01-06 + A_history_errata
    ("Unverified" lists), docs/en/config_mc/indi_control.md (prettier/link check open, report/DOCS_DRAFT_S201.md).
    R1 text waits Q36. S254 check of report "Unverified" items: results/g8_s254/UNVERIFIED_CHECK.md (49 items:
    17 VERIFIED, 2 WRONG fixed (stale Q31 tags), 30 UNCHECKED). S255 (haiku) first 10 UNCHECKED: 4 VERIFIED
    (02:347,348,350,351), 6 still unchecked; items 11-20: 2 VERIFIED (15 scoped, 16), 8 still unchecked
    (results/g8_s254/UNVERIFIED_CHECK_S255.md, flags on 12/15/19/20). Next: a sonnet agent clears
    the remaining 24 (and report/UNVERIFIED_S217.md lists), removes verified items from the chapters, fixes report
    02:349 "not confirmed" (yaml answers it) and GATES.md:321 bench/gate_g3.sh (absent; G3 scorers are
    bench/g3_score.sh, g3_checks.py, g3_checks_key2.py).
Gate binary = 903eae63 (D-BINARY-GZFIX): do NOT rebuild build/px4_sitl_default from HEAD. G3 chain stopped for good
(Q35 A): the supervisor "g3_campaign_f10 chain finished" line is hardcoded and stale (S199 closed it): ignore it.
Route check: RC247 current; next RC S262.

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
None. (S248-S252 G7 task rows moved to JOURNAL.md S256.)
Commit trailer: AGENTS.md wins: `Assisted-by:` only.

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests: justify in the G7 verdict.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
