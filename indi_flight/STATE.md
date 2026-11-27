# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 7 (G7, G8). G3 FINAL NOT PASSED (owner Q35 A, GATES "Owner amendment S243"); G6 NOT PASSED (S244).
  FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params. Later firmware commits
  behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL). No gate flights remain.
- Gates: see GATE_STATUS.tsv. Open: G7, G8. Q36 open (R1 wording), blocks only the G8 R1 text.
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
 P6 G7 (b) gaps (results/g7_s249/G7B_TEST_INVENTORY.md, its 7-item ordered list): write the 5 small + 2 medium
    tests, break-check each, sonnet high, one test commit (+ separate neutral helper-extraction commit with objcmp
    where a test needs a helper out of Run(): ERPM_TO freshness, pos esc_status). "Lower mean_u limit" = item 4
    (rpm<0 rejection + lower clamp), orchestrator call. Saturated-motor frozen eRPM: test pins the by-design limit,
    report it in 04_limits. GLUE rows (XY_P/XY_VP wiring, K_pos/K_vel dead path, JFF source): justify via SITL
    rows (g55_gain_probe_s176, G2 outer cells).
 P7 G7 review items: table DONE S249 (results/g7_s249/REVIEW_ITEMS.md: 92 rows, 49 CLOSED, 12 JUSTIFIED,
    23 SUPERSEDED, 8 OPEN). Close the OPEN rows: A-6 hover excess <30 Hz and A-4 speed-factor -> 04_limits lines;
    4.6b notch not mirrored on torque path -> justify + 04_limits; 11.2c gust drag not air-relative -> limit;
    11.3d measured-torque test with hand-computed values -> add to P6; 11.3e = P6; 7.g8 accepted at verdict.
    Re-check the 4 "(weak)" rows (3.5d, 6.3/10, 11.3b, 11.3c). Also MC_INDI_ACT_TC yaml "round up" wording (yaml:123).
 P4 G7 verdict in GATES.md from results/g7_s249/G7_VERDICT_DRAFT.md (draft said NOT PASSED on P6/P7 gaps; its
    "injection helpers not mutation-checked" is wrong: S196 67/0). Re-run make check_format after P6.
 P5 G8 gaps + verdict: re-run bench/gate_g8.sh (results/g8_s247); report drafts 01-06 + A_history_errata
    ("Unverified" lists), docs/en/config_mc/indi_control.md (prettier/link check open, report/DOCS_DRAFT_S201.md).
    R1 text waits Q36.
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
| id | task | agent | output | resume |
|---|---|---|---|---|
| P3/P3b | DONE S248: review results/g7_s248/F10_WHOLE_BRANCH_REVIEW.md, fixes 2292882735 + 104508687b (F10_FIX_S248.md; ~8 MINOR skipped -> G7 verdict) | - | - | - |
| P3b-K2 | DONE S249: PASS with findings, 0 BLOCKER, 1 MAJOR ("no integrator" in McIndiPosControl.cpp help :1300 and comment :971 vs MPC_*_VEL_I_ACC passed + _control.update(dt) runs), 3 MINOR | sonnet | results/g7_s249/P3B_KEY2.md | P3d: verify integrator wording, fix comments + MINORs, one neutral commit (after P3c) |
| P3c | DONE S249: 8423db867b (DT_MAX->INC_MAX, INJ_RAMP->INJ_AMPR, .msg symbol comments; no timestamp_sample existed) + 7eaf225535 (docs/en, report); 13/13 tests, SITL builds; diff read by orchestrator (6 C++ lines, rename only). bench quad5in_indi_defaults.params:31 keeps old DT_MAX name (pinned gate binary): mapping in record; report yaml:NNN refs off by 1-2 lines (G8) | sonnet | results/g7_s249/P3C_PUBLIC_NAMES.md | - |
| P3d | DONE S249: 5987dde746 comments only (integrator reset before every update, :1071-1074) | sonnet | results/g7_s249/P3D_COMMENTS.md | - |
| P2 | DONE S249: indi-fw-pr e5b84f62bf (local); (a) 0 stock diff, 71 files; (d) 46/0; (g) SITL rc=0; 9/9 gtest targets; F-10 grep 0 hits; NuttX not rebuilt (S195 size stands, renames only). Re-run after P6 tests | sonnet | results/g7_s249/README_P2.md | - |
Commit trailer: AGENTS.md wins: use `Assisted-by:` only, no Co-Authored-By naming an AI (S248 commits carry both; not rewritten).
P2 S248 on pre-fix head 4ebf90ad2f: (a)(d)(g) + 9 gtest PASS (results/g7_s248/README.md); re-run after P3d.

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests: justify in the G7 verdict.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
