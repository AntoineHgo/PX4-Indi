# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

## Owner directive 2026-11-20 (not a question; act on it first, then close it here)

New owner decisions F-7, F-8, F-9 and the rule "Staying on the path" are in MISSION.md. In practice:
1. F-7 overturns the `want_indi` false stock path of D-STAGE-STALE and the "start INDI in rampup" rejection of
   D-HANDOVER (overturn condition "owner classing the takeoff ramp as a PID fallback" is met). Mark both entries
   superseded in DECISIONS.md and write one short decision for the ground/ramp handling (simplest scheme).
2. RC133 is re-ordered: (a) write the G5 section of GATES.md first (absolute limits, 3 seeds, F-8 rows marked
   not tested); (b) implement F-7 in the module and remove the code that only served the old seam; (c) fly one
   3-seed G5 batch of all modes with existing scenarios. The EdgeState design of RC133 action 3 is dropped: with one
   controller there is no stock->INDI edge left. A-46 is closed by (c) or superseded by F-7.
3. Rewrite the STATE.md next actions so each names the gate item it advances, and add `Gate progress:` to the
   JOURNAL line of this session.
