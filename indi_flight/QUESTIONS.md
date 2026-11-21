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

## Q19 (S182, 2026-11-21): does the Q15 A nav_state skip apply to the command-chatter check? BLOCKING for G4
Context: freeze-8 G4 (results/freeze8_s181/G4_SCORES.md, both keys, Q18 skip applied): R20/C20/R4/clip 18/18 in
limits; hover 9/9 clean (freeze-7 hover_harsh_s1 20 Hz gone); cruise 33.5/89 Hz lines gone (89 Hz residue 4.2e-4 <
5e-4). One row splits the keys: cruise_harsh_s2, motor m2, 20.0 Hz, RMS 6.0e-4 (ratio 472), at the hold-to-land
switch (~58-65 s, still airborne, so the Q18 touchdown skip does not cover it). Key 1 scores chatter inside item 2 and
applies the Q15 A 3 s skip after a nav_state change: no flag. Key 2 scores chatter separately without that skip: flag.
With the skip both keys clear it; without it both flag it. GATES line 362 defines the command check as "the G3
detector, also on the command"; Q15 A says "the sustained-oscillation detector skips windows that overlap the 3 s
after a nav_state change; mode transitions are judged by the G5 transient limits". PID: S180 reported land windows
20-26 Hz 1.1-1.5e-3 in PID too (same land-entry signature, larger). If the skip applies, G4 PASSES at freeze-8.
Options: A (recommended) the Q15 A skip applies to the command check too (same detector, line 362), key 2 gets the
skip, G4 PASSED; B the skip is for the rate detector only: G4 NOT PASSED on cruise_harsh_s2.
Meanwhile: no re-fly, re-score or note on G4; work continues on G2 spot probes and G5 scoring. Not blocked overall.
