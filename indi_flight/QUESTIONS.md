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
**Owner answer (2026-11-21):** A. In the stabilized full-scale part of G5.10: no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg;
no windup = attitude error to the stick-commanded attitude <= 5 deg within 1 s after the sticks return to centre;
the alt-loss limit is not applied (full throttle climbs). Log it in GATES.md 5b and DECISIONS.md as an approved
test-definition fix. PID flies the same flight as the reference.

## Q18 (S179, 2026-11-21): G4 command chatter, windows that contain the touchdown. BLOCKING for G4 (land windows).
Context: G4 asks for limits on motor-command RMS "in hover and cruise"; Q14 A added the 20-100 Hz chatter detector
(4 s windows, peak > 20 x median AND line RMS >= 5e-4) over the whole flight. At freeze-7 the cruise runs fail it in
two places: L1 in the lemniscate (in scope, INDI work continues: setpoint extrapolation probe F2) and L2 in AUTO_LAND.
S179 localised L2 on logs (results/g4_fix_probe_s179/touchdown_s179.md): line RMS >= 5e-4 only in 1 s windows that
contain the ground impact (ground_contact - 0.5 s to landed + 0.7 s); steady descent 1.3e-4 (6e-5 with MPC_VEL_LP 5),
on ground 1e-5. PID shows the same impact signature (26 Hz, 1.2e-3 in the impact window; diffB 5e-4 at 20 Hz), but
its detector did not flag a sustained 20 Hz line; INDI at 20 Hz is 6e-4 vs PID 1e-4 there. Touchdown is judged by
G5.4 (passed at freeze-7: touchdown 0.708 m/s, ramp step 7.5 %). The hover_harsh_s1 flag (20.0 Hz) is likely the
same event (not yet checked).
Options: A [recommended] the G4 chatter detector skips windows overlapping [ground_contact - 1 s, landed + 1 s] in
both stacks; touchdown stays judged by G5.4; the land-window values are reported for both stacks. B: keep the rule;
G4 then needs a touchdown fix (re-open D-F7-GROUND ground handling), likely affecting G5.4/G5.6 too. C: score the
detector on the hover and cruise segments only (gate text), take-off/land reported.
Meanwhile: the land windows are not re-scored or chased. L1 (lemniscate) work, G2 (XY_P 1.2 freeze-8), G5 continue.
