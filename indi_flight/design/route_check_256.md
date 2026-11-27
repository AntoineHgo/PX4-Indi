# Route check 256 (2026-11-27, read-only short form, no sim/build/python)

Read: STATE.md, GATE_STATUS.tsv G8 row (line 9), GATES.md:523-527 (G8), JOURNAL tail 5, QUESTIONS.md:81 (Q36), headings of g8_s254 checks, RC247.

1. On the shortest path? No. GATES.md:523-527 requires: evidence paths exist, G1 limits and G3 excluded corners listed, bring-up checklist, errata/history appendix, no diff in docs/ko|zh|uk, page only in docs/en, lint if a make target exists. Nothing says every "Unverified" item must be cleared. bench/gate_g8.sh already passes 1-7 (results/g8_s253). The Unverified work (STATE.md:19-26, 24 items left) is quality polish; the criterion is met if unchecked claims are marked "unverified" or removed. S254/S255 added zero gate movement.
2. The difficulty is a consequence of D-OWNER-Q34-Q35 (G3 chain closed, all deferred items returned as write-ups) plus D-FREEZE-10 (no fix allowed, so everything is justified, not fixed). Q36 (QUESTIONS.md:81) is not the cause: by its own text it blocks "G8 text on R1 only", no verdict. The 49-item check is a self-imposed extension of STATE.md "Plan P5".
3. Fresh start on stage 7: write G7 and G8 verdict texts first, every open point as one justification line, run only the scripted checks named in GATES; mark every unchecked claim "unverified in this report" in one pass instead of verifying each.
4. Blocking the G8 verdict now (hard blockers: none).
   - Q36 R1 wording: QUESTIONS.md:81 (STATE.md:2-3, GATE_STATUS.tsv:9). Soft: can be written as "pending Q36".
   - Report "Unverified" lists, 24 unchecked: results/g8_s254/UNVERIFIED_CHECK.md:59 (counts), UNVERIFIED_CHECK_S255.md:23. Soft: self-imposed.
   - Open fixes: report 02:349 "not confirmed" (yaml answers it); GATES.md:321 refers to absent bench/gate_g3.sh (STATE.md:24-26). Small edits.
   - docs/en page prettier/link check open (STATE.md:19). Check 7 is n/a (no docs make target).
5. Moved since RC247: G7 open -> PASSED (S252, GATE_STATUS). gate_g8.sh written and all PASS (S253; was missing/2 FAIL). D-ID-OK-LIMIT and F-10 delta review done (S246/S252). G3, G6 unchanged (final). G8 row still "open". S254-S255: 19 + 6 Unverified items checked, 2 stale Q31 tags fixed, no gate change.
6. Cut list.
   - STOP the item-by-item Unverified clearing. One pass: for each unchecked item keep it only if it is already marked "Unverified" in the text, otherwise delete the claim. Drop report/UNVERIFIED_S217.md clearing; state the list as a limit in the verdict.
   - Drop the Q36 wait: write R1 as option A wording ("eRPM telemetry on every motor is required for the validated configuration; not enforced by firmware; without it the modelled actuator state runs, not validated"), mark "pending owner Q36, option A recommended". No gate result depends on it.
   - Keep as justification lines only (RC247 list): unit 9 renames, K_pos/K_vel dead path, harness extraction, K128, D-JFF-SOURCE, D-OFFB-POSVEL, omega_ff step, g510 one-sample LOC, ACT_TC/W_MAX vs bench, guard params, esc_status instance, G6 item 2 rescore, ACT_TC yaml wording.
   - Do the two small fixes (02:349, GATES.md:321) and run bench/gate_g8.sh once more.
   - Do not rebuild, do not fly, no new gates.
   RECOMMENDATION: write the G8 verdict now with R1 "pending Q36" (not WAIT_OWNER). Verdict: G8 PASSED on the GATES criterion with listed limits (R1 not enforced, N unverified claims marked). If the owner picks option B for Q36, that is a separate post-verdict change request. Needs about 1 session (sonnet write, opus final read).
