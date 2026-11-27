# Text updates for the INDI rpm arming check (S259)
- report/01_inner_loop_design.md, section 4 (R1 paragraph): rewritten to "R1 is enforced in firmware", present tense, limits pointer.
- report/04_limits.md, 4.4 (R1 bullet): enforced; limits (2) ungated windows, (3) rpm while disarmed, (4) frozen not detected disarmed; (1), (5) not listed (chapter states current behaviour).
- report/06_bringup_checklist.md, 6.3: new item B3a (rpm published while disarmed >= ~50 Hz per motor, arming refused with one motor unplugged).
- report/06_bringup_checklist.md, 6.6 (R1 bullet): enforced, SITL only, depends on B3a.
- docs/en/config_mc/indi_control.md: Requirements bullet (arming refused), new "Arming Requirements" subsection, W_MAX text (line ~108) and table row (~172) corrected to "0: arming refused", Limitations bullet, bench check "Rotor speed while disarmed".
- GATES.md, G8 verdict: R1-pending text replaced; dated note (S259) added with q36_s258 and q37_s259 evidence.
- GATES.md, G7 verdict: note on cherry-pick to firmware-only branch and G7 re-check (see G7_RECHECK.md).
- Not changed: A_history_errata.md Q36 row, DOCS_DRAFT_S201.md (historical), 01 wording "no blend" kept from before.

bench/gate_g8.sh (read-only text check, run after the edits):
PASS 1 evidence paths exist
PASS 2 G1 limits and G3 excluded corners listed
PASS 3 bring-up checklist
PASS 4 errata and history appendix
PASS 5 docs/ko zh uk diff vs main empty
PASS 6 user page in docs/en only
PASS 7 markdown lint: not applicable: no docs target (only msg_docs generator)
