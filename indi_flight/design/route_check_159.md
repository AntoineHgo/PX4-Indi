# Route check 159 (written for S159)

Read: STATE.md, DECISIONS (headers, D-GAP-G510, D-PREFREEZE-R1..R3, D-FREEZE-6, D-VIB-HOOK, D-NOISE-PROF), ANOMALIES.md
(open: A-1, A-4, A-6, A-34-A-39 deferred; none new), QUESTIONS Q8-Q11, JOURNAL tail 8, route_check_149.md.
Not read: GATES.md (G2/G3/G4 cell counts are taken from STATE; verify before sizing).

## 1. Still on the shortest path?
Yes for G5, no longer for the whole project. Since RC149 the pre-freeze reviews, noise profiles and the 54-flight
re-fly were done; that was needed. But 5 of 8 gates (G2, G3, G4, G6, G7, G8 = 6) have no freeze evidence and G5 is
at "pending second key". The risk now is polishing G5 (a 3rd and 4th key on rows that pass 3/3) while G2-G4, the
gates most likely to move firmware defaults, are unflown. A firmware change after them re-flies G5 again (D-FREEZE-6).

## 2. Which decision is the main difficulty a consequence of?
- G5.5 o1-o4/o7 FAIL 3/3 (Q11): D-outer-arch base A (stock PositionControl feeds a_c; ~100 ms lag). PID also fails.
- G5.10 INVALID / tilt (Q9): gate text (20 deg vs MPC_TILTMAX_AIR) plus a SAT part that does not saturate; not a decision.
- G5.2 s1 (Q10): D-NOISE-PROF typical profile + stock EKF height; INDI holds the estimate, PID does not.
- G5.9a: stock commander latency (Q8 add.2). None of the open G5 FAILs is a controller defect we can fix cheaply.

## 3. Fresh start on this stage
(a) Order gates by what can still change firmware: G2/G4 (margins, noise) and G3 (disturbance) before G5, so the
freeze re-fly is flown once. (b) Settle Q8-Q11 text with the owner BEFORE the freeze, not "option A assumed".
(c) One scripted all-gates batch with a single second-key pass over the whole set, not per-gate key sessions.

## 4. Blocking?
Nothing hard. Soft: Q8-Q11 answers (4 rows can change verdict: G5.5, G5.9a, G5.10, G5.2). Unverified batch2 o5-o7 args
(batch2_notes.md) should be checked in the key2 pass since o5/o6 count as PASS evidence. fwdef G5.1 cell 0.5x K gate
is "reported", not a verdict: needs an owner line.

## 5. Gate items moved since RC149
G5.1 6/6, G5.3 3/3, G5.4 6/6 PASS (3 seeds); G5.5 offb/o5/o6 3/3 PASS, o1-o4/o7 FAIL 3/3 (PID o1 FAIL too); G5.7 3/3;
G5.2 5/6 (PID ref passes s1); G5.10 re-flown INVALID/tilt (was PASS alt/back at TB 0.3, S151); G4 typical profile fixed
(A-49 closed); G1.5 events scored at option A. G2, G3, G4 verdicts, G6, G7, G8: unmoved.

## 6. Drop or simplify
1. Drop key2 session S159c for rows with no verdict risk beyond checker arithmetic (G5.7 3/3, o5/o6): key one
   representative seed per row, full 3 seeds only where the verdict is FAIL or borderline (G5.2 s1, G5.5 o1-o4/o7).
2. Drop further G5.5 / G5.10 work (Q11, Q9): FAIL recorded with PID reference; wait for the owner.
3. Drop the G5.9a/G5.8 3 m/s re-fly until Q8 is answered.
4. G2: do not fly new cells; use the freeze cells already named (fwdef rate roll 800 at ID_OK 0, ID_OK 1 outer cell, pitch/400 Hz).
5. G3: fly only the INDI-outer MC_INDI_POS_EN=1 minimum, skip weak+sat and altctl/posctl (RC118: G5 carries them).

## Order check for G2 / G3 / G4
Current order (G5 -> G2/G3/G4) is wrong for firmware risk; right for cost. Proposed: G2 offline+few flights first (cheap,
mostly analysis), G4 second (noise run with the typical profile already calibrated), G3 last of the three.
- G2 minimum: 800 Hz rate roll at ID_OK 1 and ID_OK 0 (fwdef), rate pitch/400 Hz, attitude yaw (ax3 r800), plus the offline
  items (outer-cell margin key, A-34/A-39 bound, 267 Hz analytic). About 4-6 flights + analysis, one session.
- G4 minimum: hover + one step + one auto_tour under typical noise, 3 seeds, and quiet/harsh single seeds; closes A-6 (<30 Hz
  excess) via the ablation; about 8-12 flights. Reuses freeze G5 typical-profile data where the scenario matches (check
  the profile args are identical before citing).
- G3 minimum: gust_x, one motor fault, one eRPM loss, one weak+sat if cheap, each 3 seeds on 23acbdef67; cite G5.10-type
  runs as probes only. About 12-15 flights. Needs g3_checks.py/gate_g3.sh (still DEFERRED: write them first, one session).

## Next actions (ordered)
1. G5 (all rows, closes the freeze evidence): key2 pass as D-FREEZE-6 requires, sized per item 6.1; commit verdict table with Q8-Q11 rows marked "FAIL at option A". S159.
2. G2 (G2 rate roll fwdef + ID_OK 1, attitude yaw, offline margin items): fly the freeze set and write the verdict. S160.
3. G4 (typical profile, A-6 ablation): one batch and checker; build G4 checks only for the scenarios flown. S161.
4. G3 (gust, motor fault, eRPM loss): write g3_checks.py + gate_g3.sh, then one serial batch. S162-S163.
5. Owner: ask Q8-Q11 in one message after step 1 (no waiting); if any answer B changes firmware, re-fly only the affected G5 rows.
