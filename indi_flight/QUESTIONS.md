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

## Q20 (S184, 2026-11-21): which RMS does the Q19 PID guard compare? BLOCKING for G4 (guard rows)
Context: the S183 amendment says a G4 row FAILS "if the INDI line RMS in a skipped window exceeds the PID reference at
the same transition". The second key (`results/freeze9_s183/g4/Q19_KEY2_REVIEW.md`, F1) finds the metric undefined:
which windows, which line, any floor or tolerance. Freeze-9 G4 is NOT PASSED under both readings (GATES "G4 verdict at
freeze-9"), so this question does not change today's verdict; it sets the target of the fix and of the re-score.
- Reading A (flagged line): compare only lines above the chatter floor 5e-4 (the G3 detector's own flag). INDI fails
  where it is flagged and PID is not, or both are flagged and INDI > PID. Freeze-9: 5 of 16 transitions fail (INDI
  20.0-20.8 Hz 5.0-5.3e-4, PID 2.7-4.4e-4).
- Reading B (any window): max line RMS over all overlapping windows, strict INDI > PID, no floor. Freeze-9: 9 of 12
  fail, several at levels far below the 5e-4 floor, i.e. noise-level comparisons between two stacks (lesson 6).
Recommendation: A (absolute floor, then the PID comparison only where the floor is crossed).
Meanwhile: one session of cause search on the INDI 20 Hz transition line (log analysis, no firmware change), which
both readings require. Not blocked on other gates (G5.10 set-up continues). No re-score of guard rows until answered.
Added S184 after the cause search (`results/g4_20hz_cause_s184/README.md`, script line20.py with self-test):
- 17->4 (take-off -> loiter): a physical 20 Hz roll/pitch transient (truth body rate 1.5e-3 rad/s, torque x/y, all 4
  motors differential), onset at the end of the take-off setpoint stream, decays ~5x within 10 s. PID shows the same
  onset and shape at 0.5-0.65x the INDI amplitude (PID motor line 2.8-4.1e-4, INDI up to 5.3e-4). The 1.5-1.9x INDI
  amplification is shown; its cause (rate-loop gain near 20 Hz) is a hypothesis.
- 14->18 (offboard -> land): no tone in 19.5-21 Hz in either stack (both at floor); the guard's 5e-4 flag there comes
  from its +-2 Hz integration on broadband descent energy, i.e. a guard artefact under both readings.
So this is partly a PX4 fact (owner note point 1): the transient exists in both stacks, INDI amplifies it ~1.7x at a
level 0.05 % of full motor command. Options: A strict (Reading A; 17->4 fails; next = identify the 20 Hz amplification
from the G2 rate-loop data, then a firmware change that re-opens G2/G4/G5); C (Reading A, and a transition transient
that PID also shows is reported with both values, failing only above an absolute bound you set). Recommendation: A with
a narrow-band (+-0.5 Hz) line measure that removes the 14->18 artefact; I will not propose a tolerance myself.
