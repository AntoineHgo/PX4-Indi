# Route check 247 (2026-11-26, read-only short form, no sim/build run)

Read: STATE, GATE_STATUS, GATES.md section 7 and 8 (lines 512-527), last JOURNAL lines, DECISIONS tail, F10_PLAN head, report/ list. Skimmed only: ANOMALIES.

1. Shortest path? Partly. G8 is on the path. G7 (f) unit 9 (public renames) and the whole STATE item 3 "older list" are not: GATES G7 (f) is a reviewer checklist, and unit 9 renames are firmware-touching work under FREEZE-10 with no gate failure to justify them.
2. Difficulty is a consequence of: D-OWNER-Q34-Q35 lifting the cuts (RC208/221/226) so every deferred G7/G8 item came back at once, plus D-FREEZE-10 (no behaviour fix allowed), so each defect found (dead K_pos/K_vel path, ID_OK call site K128, R1 not enforced) can only be justified, not fixed.
3. Fresh start would: write the G7 and G8 verdict texts first, with each open item as a one-line justification, then do only the scripted checks GATES names. Missing: bench/gate_g8.sh does not exist (only gate_g1.sh, gate_g4.sh in bench/), and G8 names it as the command.
4. Blockers per GATES.md:
   - G7 REQUIRED: (a) zero diff (S195 PASS, rerun on final branch); (b) tests pass + break-check (done S195, 9 survivors killed; "injection helpers not break-checked" is a justify item); (c) default-params hash (done, ID_OK 0 stated in verdict, D-ID-OK-LIMIT); (d) make format/check_format (S195 clean on 46 files; must re-run after F-10 commits S196-S246); (e) flash/RAM of one board (done, fmu-v5x; v6x overflow 23.5 kB goes in report); (f) reviewer checklist: .github/instructions + navigation terminology, one whole-branch F-10 review; (g) branch has no indi_flight/ path AND builds (build check via make_fw_branch.sh --force-recreate, needed after S246). Last sentence: opus review items S58-S63 closed-or-justified list (not yet confirmed as written).
   - G7 NICE: unit 9 renames, harness extraction (D-G7-HARNESS), dead-path removal, ACT_TC/W_MAX vs bench, guard params evidence, pos module esc_status instance 0 / 100 ms age.
   - G8 REQUIRED: every gate section has an existing evidence path; G1 evidence limits and G3 excluded corners (beyond-range list) listed; bring-up checklist present (06 exists); errata/history appendix present (A exists); `git diff main -- docs/ko docs/zh docs/uk` empty; page in docs/en only (draft exists); markdown lint if a make target exists (unverified); `bench/gate_g8.sh` written and run.
   - G8 NICE: Q36 R1 wording (STATE says G8 R1 text waits, but it is not a GATES item), prettier/link check, closing every "Unverified" line in 03/04/UNVERIFIED_S217, ch.2 polish.
5. Moved since RC241: G3 final NOT PASSED (S243), G6 NOT PASSED (S244), D-ID-OK-LIMIT closes STATE action 4 (S246), F-10 id grep done (7 ids removed, S246), ch.3 G3/G6 sections and ch.4 limits drafted (S245). G7 and G8 rows unchanged (open); GATE_STATUS last changed S244.
6. Cut list (STATE "Next actions"): 
   - CUT, justify in G7 verdict: unit 9 renames (list them under "not renamed"); dead K_pos/K_vel path (document; removal is behaviour-adjacent); harness extraction D-G7-HARNESS; K128 ID_OK call site, D-JFF-SOURCE, D-OFFB-POSVEL wiring test, omega_ff step; g510 LOC one-sample vs 0.2 s; ACT_TC/W_MAX vs bench; guard params; pos esc_status/100 ms; MC_INDI_ACT_TC yaml wording (yaml text only, behaviour-neutral, do if cheap).
   - CUT: Q36 as a blocker (reword R1 in the report as "required for validated operation", state not enforced); G6 item 2 ID-window rescore; STOP list and Open problems/Deferred anomalies (list in limits).
   - CUT from STATE: item -1/0/2 trap text, stale supervisor line, G3 tooling notes.
   Ordered plan:
   1. Write bench/gate_g8.sh from the GATES text, run it, list failures (G8 checks; 1 session, sonnet).
   2. Re-run make_fw_branch.sh --force-recreate, check (a), (d), (g) incl. branch build and v6x size note (1 session, sonnet; docker, not during flights).
   3. Whole-branch F-10 review + navigation/.github/instructions checklist, fold in unit 8 MINORs as a neutral commit (1 session, opus review, sonnet coder).
   4. Write the G7 verdict in GATES.md with the cut-list justifications and the S58-S63 closed-or-justified table (1 session, opus).
   5. Close G8 gaps from step 1, Unverified items that are evidence-path or limit checks only, G8 verdict (1-2 sessions, sonnet; opus for the final read).
   Total about 5-6 sessions.
Unverified by me: whether (a)/(d) still pass after F-10 commits; whether S58-S63 justified list exists; whether a docs lint make target exists; ANOMALIES not read beyond its tail; the 8000-byte STATE rule (STATE.md appears over budget).
