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

## Q26 (S199, 2026-11-22): G3 NOT PASSED at freeze-10, step back or close as a limit?
Context. The 300-run campaign finished (results/g3_campaign_f10, FAILS_S199.md; re-fly results/g3_refly_s199/SUMMARY.md).
Two losses of control, both reproduced at speed 1, both INDI-specific (PID flies the same draws without LOC): 245
(corner C1: controller G1 x2, motor tau x3, delay 10 ms) diverges in a growing 2 Hz pitch oscillation; 264 (corner C3:
saturation 0.351 plus weak motor 0.709) tilts past 60 deg at the fault. Item 2 fails on 79 runs: real lines class A
(11 Hz pitch, high delay + fast motor + controller G1 below plant, 8 runs) and class B (2 Hz, high delay + slow motor,
37 runs; C1 and C6 fail every run); 283 (A) and 239 (B) reproduce and PID passes them. Item 3 94.95 %. Verdict written
(GATES "G3 verdict at freeze-10"). G2 margins were measured on the nominal plant only; the failures sit where delay and
actuator-model error combine (fixed ACT_TC 0.033 s against plant tau 0.017-0.1 s, no delay in the modelled state), plus
saturation handling with a weak motor. A fix is an inner-loop law change: FREEZE-11 re-opens G2, G4, G5 and the whole
G3 campaign (about 5-7 sessions and 8 h CPU), more than three sessions of finished work.
Options.
- A (recommended): one session of cause search on 245, 239, 283, 264 (logs, linear margin model with the drawn plant);
  if a fix probe removes the failure on a log, FREEZE-11 with the re-flies named above.
- B: close G3 as NOT PASSED with the explanation; state the envelope (delay, tau and G1 mismatch, saturation with a
  weak motor) as a limit and a bring-up requirement in the report; go on to G6-G8.
Meanwhile: the cause search (needed under A and B, every failure must be explained); no firmware change until you
answer. Blocked: only for the firmware change and the re-flies.
