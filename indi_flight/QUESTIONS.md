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

## Q17 (S178, 2026-11-21): G5.10 stabilized full-scale part, recovery criterion. BLOCKING for G5.10.
Context: Q9 (b) says the full-scale part is flown in stabilized (full throttle + full roll stick for 1 s) with "same
limits": no LOC, alt loss <= 2.0 m, tilt <= MPC_TILTMAX_AIR + 5 deg, no windup = back within 0.3 m in <= 5 s.
Stabilized has no position or altitude setpoint, so "back within 0.3 m" has no reference, and at full roll stick the
tilt is commanded up to MPC_MAN_TILT_MAX, not MPC_TILTMAX_AIR. Pre-test flights (INDI + PID, seed 1) are queued
(results/g5_10_freeze7_s178, new scenario g510_stab_full; SAT part per Q9 (c) at SIM_GZ_THR_SC 0.136, hover needs
1.007 command). PID flies the same flight as reference.
Options: A [recommended] in stabilized: no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg; no windup = attitude error to the
stick-commanded attitude <= 5 deg within 1 s after the sticks return to centre (rate/attitude integrators are the
only wind-up there); alt loss not applied (full throttle climbs). B: keep the literal text, measuring altitude
change from stick release to +5 s against 0.3 m (no reference, likely fails for PID too). C: drop the recovery clause
for the stabilized part.
Meanwhile: the pre-test flights fly (data only); the stabilized part is not scored until answered. SAT part, G2, G4
cause search, G5.3/G5.4 continue.
