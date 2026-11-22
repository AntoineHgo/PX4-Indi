# Route check RC202 (S202)
Read: STATE, GATE_STATUS, Q26, DECISIONS (D-G7-NUTTX-BUILD .. D-F10-NEUTRAL, last 8 headings), ANOMALIES tail, JOURNAL S198-S201, RC194,
MISSION Gates and Reviews. Nothing run. Gates: 4 of 8 passed (G1, G2, G4, G5); was 1 of 8 at RC194 (G2/G4 re-passed at freeze-10, G5 new).

## 1) Shortest path?
Partly. S200 (linear-model cause search, closed) was needed under every Q26 answer. S201 spent its session on F-10 unit 2, a docs page draft and an
outer-loop chapter draft: no gate verdict moved, and the drafts rest on firmware that Q26 may change (limits, inner-loop chapter, ACT_TC text).
The critical path is one owner answer (Q26). Nothing the agent can do alone shortens it; the work done meanwhile should be only what survives
both A/C and B.

## 2) Decision behind the difficulty
G3 failing at freeze-10 comes from D-FREEZE-10 + D-G7-DEFAULTS style fixed physical parameter: MC_INDI_ACT_TC is one fixed actuator model (0.033 s)
against the G3 tau box x[0.5, 3] (MISSION G3, owner wording) while G2 margins were measured on the nominal plant only (G2 scope, RC194 item 3 "fresh
start": G3 pre-test per build). Wait is owner-caused: Q26 asked S199, unanswered for 3 sessions. Root: the owner gate (tau x0.5-3) vs D-IDENT
(ACT_TC identified at bring-up, F-3) were never reconciled before freeze-10; Q22 did it for G1 only.

## 3) Fresh start would do differently
- Ask the Q22-style question for tau at G3 set-up (S186-S198), not after 300 runs; a 20-draw pre-test per corner (C1, C6) would have shown 2 Hz.
- Hold documentation drafts (docs page, report chapters) until the last freeze; write only the design skeleton.
- Treat F-10 clean-up as one batch review after the firmware freeze decision, not nine units across sessions.

## 4) What blocks the next verdict
- G3: Q26 answer. A: probe on 264 (weak-motor recovery) + FREEZE-11 + re-fly G2, G4, G5, G3 (5-7 sessions). B: nothing, verdict stays NOT PASSED
  with limits text. C: narrowed tau box written as owner amendment in GATES.md BEFORE any re-score (Q25 rule), then FREEZE-11.
- G6: cannot give a verdict before Q26 (needs G2/G3/G5 on defaults + wrong-start identification; under C ACT_TC joins the identified set, so
  the identification scope, wrong-start grid and G3 box all change). Can start WITHOUT Q26: yaw fit fix (A-44 probe V3, r regressor + matched
  grid, K126 MAJORs) and the written identification sequence skeleton, both independent of ACT_TC. ACT_TC identification step waits.
- G7: no verdict before Q26 (FREEZE-11 changes firmware: re-opens (c) defaults, (e) flash, (g) branch must equal tested code, F-10 review over
  final files). Under B a verdict is reachable on freeze-10 code. Reachable now without Q26: F-10 units (behaviour-neutral), text-only items,
  checker self-test defects, written justifications.
- G8: no final verdict before G3/G6/G7 (limits, bring-up list, validation chapters). Reachable: design chapters (outer loop done as draft).

## 5) Moved since RC194
- G2: re-flown at freeze-10, PASSED (outer 24/24, STEP 9/9). G4: PASSED 18/18, guard clean. G5: PASSED S198 (events seeds 2-3, G5.8 9/9; Q25 B limit).
- G3: 300/300 flown, verdict NOT PASSED (245, 264 LOC; item 2 79 runs; item 3 94.95 %); cause shown on linear model for 245/239 (S200).
- G7: (a)(c)(d)(e) measured S195, NuttX fix, text edits S196; F-10 units 1-2 of 9. G6: nothing. G8: docs page + outer-loop chapter drafted (not verdicts).

## 6) Cut list against STATE "Next actions"
- Item 1: no more cause work on 283 (outside the linear model) or 264 modelling; key-1 landing-window defect and 02 quota miss stay recorded, not chased.
  Put the Q26 decision options and a one-line deadline in the next owner message; do not start the 264 fix probe before the answer (it is free under A/C only).
- Item 3 G7 older list: justify in writing, do not fix: unevidenced guard params (ERPM_TO/FRZ, SP_TO, DT_MAX), g510 log-read branch,
  g511 p95 test, D-JFF-SOURCE case, dead IndiAccelControl K cascade (remove after the freeze decision). Fix only MC_INDI_ID_OK call site (K128 MAJOR)
  and offb_vel_check no-verdict/IndexError, since both can hide a failure.
- F-10: merge units 3-9 into at most 3 sessions (accel control+hpp, rest of module, yaml/params/msgs); the per-unit objdump check stays.
  Do unit 3 only if no Q26-dependent firmware edit is expected in those files; otherwise defer to after the freeze decision.
- Item 4/5: stop report and docs drafting until Q26; no inner-loop chapter, no docs prettier/link pass.
- Drop: D-G7-HARNESS extraction before verdicts (already ordered after), v6x flash overflow beyond one report line.

## Recommended next 3 actions
1. G3 (Q26): send the owner a short reminder naming the cost of each option (A/C 5-7 sessions, B 0) and that G6/G7/G8 verdicts wait on it; ask for A, B or C.
2. G6 (prerequisite): fix the yaw fit (A-44 probe V3, r regressor + matched grid) and write the identification sequence skeleton, ACT_TC step left open.
3. G7 (items a-g open ones): close MC_INDI_ID_OK call site + checker defects, write justifications for the rest of the older list; F-10 unit 3 merged with 4.
