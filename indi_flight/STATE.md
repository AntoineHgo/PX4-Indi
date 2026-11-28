# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Final summary (S259, 2026-11-27; DONE recreated after Q36 B and Q37 B)
- G1, G2, G4, G5, G7, G8 PASSED (G7, G8 with justified limits). G3 NOT PASSED (final, owner Q35 A: draw 3 INDI-only
  2 Hz pitch, draw 264 LOC on saturation + weak motor). G6 NOT PASSED (needs G3; item 7 6/58 failures). All written
  up with data: GATES.md verdict sections, report 03_validation 3.3/3.6, 04_limits 4.1/4.2. Simulation only.
- R1 enforced in firmware: INDI refuses arming without fresh rpm on every motor (e6af4b6b0d) or with W_MAX 0 / no
  rotor geometry (ac744d360e); 6 break-checked tests (results/q36_s258, q37_s259). Limits in report 04_limits 4.4.
- Firmware-only branch indi-fw-pr head fcd212f228 (local, no upstream), G7 re-checked S259; no PR opened.

## Status
- Stage: 7 done. G3 FINAL NOT PASSED (owner Q35 A, GATES "Owner amendment S243"); G6 NOT PASSED (S244).
  FREEZE-10 (D-FREEZE-10): firmware 7fe6206fcc, config g5_freeze_s157 params. Later firmware commits
  behaviour-neutral (D-G7-NUTTX-BUILD, D-F10-NEUTRAL). No gate flights remain.
- Gates: see GATE_STATUS.tsv. All gates have verdicts. No open question. DONE exists (S259).
- Owner rule F-10 (2026-11-22): brief every coder with F-10. Clean-up = separate behaviour-neutral commits,
  independent review.

## Next actions (each names its gate item)
RC247 (design/route_check_247.md) cut list, no code work, each becomes one justification line in the G7/G8 verdict:
unit 9 renames (except those the whole-branch F-10 reviewer flags), K_pos/K_vel dead path (module always accel_only,
McIndiPosControl.cpp:315), harness extraction (D-G7-HARNESS), MC_INDI_ID_OK call site (K128), D-JFF-SOURCE,
D-OFFB-POSVEL wiring test, omega_ff step on offboard entry, g510 one-sample LOC (results/g7_checkers_s215),
ACT_TC/W_MAX vs bench (lesson 12), guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced, pos module esc_status
instance 0 / 100 ms age, G6 item 2 ID-window rescore, MC_INDI_ACT_TC yaml "round up" wording (D-OWNER-Q27).
Plan: owner directive 2026-11-28 (QUESTIONS.md, D-OWNER-PDF): G8 professional PDF `report/pdf/indi_report.pdf`.
DONE removed until it is met. Steps: (1) S260 skeleton+front chapters, TikZ diagrams, figure scripts; (2) chapters
inner, outer, analysis; (3) validation, limits, bring-up, conclusion, traceability appendix; (4) fresh-eyes review
agent (no project context) + fixes; (5) orchestrator renders every page (pdftoppm) and checks it; (6) DONE.
Untracked `report/indi_report.pdf` (09:22, origin unknown): left untouched, not committed.
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
S260: A skeleton DONE, committed 1258f61ac1 (23 pages, `report/pdf/build.sh [--no-figs]`; chapters 03-09, A, B
stubs; NOTES_A.md lists unverified airframe-table units). C diagrams DONE d9277c0ec2 (architecture, inner, outer,
ground_logic; CAPTIONS.md: notation u = per-axis normalised torque, bold T specific thrust; one 4.8 pt overfull;
stock-mode routing unverified). Full build with figs+diagrams not yet run. B figures DONE b8f50cae60 (7 figs, 12 tests; FIGURES.md
lists not-possible figs). B flagged source discrepancies to settle before the chapters copy them: ch02 z outer cells
"4 of 8" no -180 crossing vs 7/8 in scores; ch03 "item 2 fails 79 of 297" vs 79 failing runs, item 2 on 73; figure
font DejaVu (Libertinus OTF is in texmf, point matplotlib at it); PID step trace from older indi_vs_pid flights. Next: chapters 03-05 agent (inner, outer, analysis) from report/*.md, using
CAPTIONS.md/FIGURES.md. Cost: S260 three sonnet-high agents ~ $1+ each: run at most 2 per session.
S261: ch03 written 26a5a6a340 (NOTES_D.md 11 items); 7a review reviews/ch03_section_review.md: 0 BLOCKER, 2 MAJOR
(R1 crossover 4 Hz vs 1.72 Hz -> blend corner 0.16 Hz vs 1.7 Hz; R2 ch07 stub must cover sat+weak motor,
telemetry-loss fallback, yaw G1 disagreement, assumed rotor inertia behind G2_Y), 14 MINOR. Next: (1) sonnet-medium
fix agent for R1 + MINORs (R2 carried to ch07 brief), re-review fixed parts; (2) 7a reviews of ch01/02 (addendum 7
applies retroactively); (3) ch04, ch05, one chapter + its review per session (~$0.45 write, ~$0.5 review). Firmware after FREEZE-10: e6af4b6b0d, ac744d360e (R1 arming check, owner-lifted freeze, no gate row
invalidated). Commit trailer: AGENTS.md wins: `Assisted-by:` only.

## Open problems
- Deferred to stage 7 (RC98): MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit
  untested, DESCEND failsafe tests: justify in the G7 verdict.
- Unmodelled in margins_models.py: measured path = eta x motor state, yaw structure (A-51), attitude loop; 267 Hz
  analytic only. Motor latency optional (lat_s, S175).
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
