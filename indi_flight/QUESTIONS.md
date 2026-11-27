# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

Q7 closed S140 (owner answer A: G5.7 validity at the 4 edges leaving posctl; written into GATES 5b; text in JOURNAL.md).

Q8-Q15 and the owner note of 2026-11-21 closed S175 (answers acted on: GATES.md "Owner amendments S175",
DECISIONS D-OWNER-Q8-Q15 and D-JFF-KEEP; full text in JOURNAL.md S175).

Q16 closed S178 (owner answer A: G2 PASSED once the freeze-7 outer cells and 2 rate/att spot-check cells pass;
3 rate x-check groups reported as evidence limit, A-51 open; full text in JOURNAL.md S178).

Q17 and Q18 closed S180 (owner answers A; GATES "Owner amendments S180", D-OWNER-Q17-Q18; text in JOURNAL.md).

## Owner note (2026-11-21, after Q17): stay inside INDI scope
1. Scope line. A behaviour that the PID reference shows too (same scenario and seed, same signature in the gate
   metric) is a PX4 fact, not INDI work: report both stacks' values and, if it blocks a gate row, write the owner
   question. Do not chase or fix stock PX4 code (EKF2, mc_pos_control, land detector, commander) or simulator
   plumbing beyond the injectors that the gate factor tables require. No new hook without a gate row that consumes it.
2. G3 tel_frozen hook. Keep it, since the G3 factor table and C5 list frozen telemetry, but build the simplest injector
   (one session, two keys). If it does not fly after that session, stop and write an owner question proposing to drop
   the frozen factor from G3 instead of continuing the plumbing.
3. G4 chatter keys. Before any F2 firmware work, reconcile key 1 (88.5 Hz) and key 2 (33.5 Hz) on the same
   cruise_typ_s1 lemniscate window (results/g55_gain_probe_s179). F2 targets only a line that both keys agree on.
   One sonnet task, existing scripts.
4. G4 item 3 in the XY_P 1.2 probe (altitude_mean 0.29 m, limit 0.1). Look up the freeze-7 value and fly the PID
   reference before any cause search (point 1 applies).

S180: points 3 and 4 acted on (results/g55_gain_probe_s179/RECONCILE_S180.md: keys agree on 33.5 and 89.25 Hz;
cruise item 3 offset equals PID, not a G4 row). Points 1-2 stand as rules (point 2 in STATE next action 4).

Q19 closed S183 (owner answer A with PID guard; GATES "Owner amendment S183", D-OWNER-Q19; text in JOURNAL.md S183).

Q20, Q21, Q22 closed S187 (owner answers acted on: GATES "Owner amendments S187", DECISIONS D-OWNER-Q20-Q22; full
text in JOURNAL.md S187).

Q23 closed S191 (owner answer B: full revert of aa4fd2654a, D-JFF-KEEP overturned for it; DECISIONS
D-OWNER-Q23; full text in JOURNAL.md S191).

Q24 and Q25 closed S197 (owner answers B and B: GATES "Owner amendments S197", D-OWNER-Q24, D-OWNER-Q25,
design/airframe_requirements.md; full text in JOURNAL.md S197).

Q26 closed S207 (owner answer: check first, C not chosen; items 1-4 done, results and recommendation in Q27;
full text in JOURNAL.md S207).

Q27 closed S208 (owner answer: identify ACT_TC first, no box change now; acted on in GATES "Owner amendments S208",
DECISIONS D-OWNER-Q27; full text in JOURNAL.md S208).

Q28 closed S211 (owner answer A, box r [0.88, 1.02] x tau_mean; GATES "Owner amendment S211", DECISIONS
D-OWNER-Q28; full text in JOURNAL.md S211).

Q29 closed S211 (owner answer A + both cuts: G3 300 fail-fast, G6 item 7 corners only; GATES "Owner amendment
S211b", DECISIONS D-OWNER-Q29; full text in JOURNAL.md S211).

Q30 closed S214 (owner answer B with review changes; GATES "Owner amendment S214", DECISIONS D-OWNER-Q30;
full text in JOURNAL.md S214).

Q31 closed S218 (owner answer B + escalation route, binary 903eae63; GATES "Owner amendment S218", DECISIONS
D-OWNER-Q31; full text in JOURNAL.md S218).

Q32 closed S226 (owner answer A bounded + item 2 sub-question yes; GATES "Owner amendment S225", DECISIONS
D-OWNER-Q32; full text in JOURNAL.md S226).

Q33 closed S228 (owner answer B with amendments, event hover; GATES "Owner amendment Q33", DECISIONS
D-OWNER-Q33; full text in JOURNAL.md S228).

Q34 and Q35 closed S243 (owner answers: Q34 "A and B" for item 5; Q35 A, G3 final NOT PASSED, C yes with guard;
GATES "Owner amendment S243", DECISIONS D-OWNER-Q34-Q35; full text in JOURNAL.md S243).


Q36 closed S258 (owner answer B: R1 enforced in INDI firmware, D-OWNER-Q36, commit e6af4b6b0d; full text in
JOURNAL.md S258).

## Q37 (S258, 2026-11-27): report, GATES, docs and firmware-only branch after the R1 arming check
Context: as Q36 B asked, `mc_indi_rate_control` now registers as a commander external arming check and refuses
arming while any motor's rpm telemetry is missing or stale (fixed 20 ms sample age, MC_INDI_ERPM_TO on the oldest
sample). While armed it always replies "can arm", so flight behaviour is unchanged (O-5 fallback). Commander zero diff.
Tests: 4 unit (fresh / missing motor / stale / armed) + 1 SITL hover that arms with telemetry, each break-checked
(results/q36_s258/IMPL.md). Independent review: 0 BLOCKER, 1 MAJOR (param text, fixed), 8 MINOR (REVIEW.md).
No gate row invalidated: every gate flight had telemetry. Limits found:
 (1) the check is off when MC_INDI_W_MAX = 0 (firmware default; the measured path is then off too);
 (2) ungated windows: ~1-1.5 s at boot before the first reply, ~1-2 s after commander drops a silent registration,
     and silently none if commander has no free external-check slot;
 (3) the ESC driver must publish rpm while disarmed at >= ~50 Hz per motor, else arming is refused (unverified on
     hardware: bring-up checklist item); (4) frozen values are not detected while disarmed (motors at rest).
 (5) refusal in running SITL was not flown (it would have been a 6th test).
Options:
- A (recommended): one sonnet task cherry-picks e6af4b6b0d onto the firmware-only branch and re-runs the G7 checks
  on it (stock zero diff, format, gtest, F-10 grep, NuttX flash); I then update the report R1 text and 04_limits with
  limits (1)-(5), the docs page (arming requirement + checklist line for (3)), GATES G8 (drop "pending Q36", add one
  G7 note), then recreate DONE. No re-fly.
- B: A, plus close limit (1): INDI also refuses arming while the measured path is disabled (W_MAX 0 or no rotor
  geometry), so an unconfigured airframe cannot arm. One more break-checked test (6th, needs your OK).
- C: keep the change on feat/indi-flight only; the report states R1 is enforced there but not on the PR branch.
Meanwhile: nothing (no gate work left). Blocked: yes, WAIT_OWNER created.
