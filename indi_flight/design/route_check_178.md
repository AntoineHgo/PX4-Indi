# Route check 178 (S178, 2026-11-21)
Read: STATE, GATE_STATUS, DECISIONS (D-FREEZE-7, D-OWNER-Q8-Q15), ANOMALIES, JOURNAL tail, QUESTIONS (Q16 answer), MISSION Gates, RC98.
Nothing flown or run. Gates: 1 of 8 passed (G1, S84), same as RC98 (80 sessions ago).

## 1) Shortest path?
Mostly yes, with one caveat. Since the owner process changes (S175) every session produces keyed gate evidence: Q8-Q15 fixes,
re-scores, D-OFFB-POSVEL (G5.5 24/24 PASS at freeze-7), a serial detached re-fly queue. The G2 verdict is now only a freeze-7 re-fly
away. Off path: the G4 89 Hz cause search (1.4-1.5x the floor, offboard path replaced), STATE action 3 MINORs, and G3 sub-items
(b)/(d) beyond the PID reference, which cost sessions without moving a verdict. The G3 set-up has been "not fixed" for 3 sessions.

## 2) Decision behind the difficulty
D-FREEZE-6/7 re-fly discipline, caused upstream by D-JFF-SOURCE/D-JFF-OFFB (S171-172, hypothesis falsified, kept by D-JFF-KEEP) and
Q11 B (D-OFFB-POSVEL): each firmware change invalidates rows, so G2/G4/G5 verdicts all wait on one serial queue (Q7 then G2Q).
Secondary: D-G3-SAMPLER chain (tel_frozen hook, noise not applied) keeps G3 un-runnable. Root as RC98: INDI logic in the module
without a harness (G7 deferred).

## 3) Fresh start on this stage
Freeze the outer-loop gain ownership (INDI xy gains, offboard path) before any G2/G4/G5 flight, so each row is flown once.
Build the G3 hooks (tel_frozen, noise applied check) in the same session as the G1 hook work, not after G4/G5. Run the G4 chatter
detector on the first flight of each freeze, not three freezes later.

## 5) Gate items moved since RC98 (JOURNAL Gate progress lines)
- G2: 67/67 cells keyed PASS incl. plateau (key2 20/20); x-check 3/15 unexplained = evidence limit; Q16 answered A (verdict pending
  freeze-7 outer cells + 2 spot checks). No verdict written.
- G3: set-up faults (a) noise not applied, (c) Docker scoring closed; 20-run pre-test flown+scored; still not fixed (tel_frozen, run 17).
- G4: metric rows 18/18 PASS both keys, item 2 PASS (Q15 A); chatter FAIL (hover 6/9, cruise 9/9) localised INDI-specific; freeze-7 flown, unscored.
- G5: G5.2, G5.9a, G5.11 scored and keyed; G5.5 failure cause shown, fixed in firmware, freeze-7 24/24 PASS; G5.10 invalid (needs new flights).
- G6/G7/G8: nothing. No gate verdict changed in RC98..RC178 except none (GATE_STATUS unchanged 2 sessions).

## 6) Drop or simplify (STATE.md next actions)
- Action 1: nothing to do until action 7 queue ends; then write G2 PASSED. Do not add model work (owner A).
- Merge action 7 into 2/4: it duplicates the queue; run one scoring pass (SC7, SG2) then stop.
- Action 3 MINORs and action 8 (G7 harness): do not start before G2/G4/G5 verdicts; they are stage 7.
- Action 2: cap the 89 Hz search at one session and only if the line is >2x floor at freeze-7; else record as bound (A-xx) and ask owner.
- Action 6: do (b) and the tel_frozen hook; for (d) explain run 17 with the PID reference only, treat the 4 oscillating runs by
  re-fly after the set-up fix, no separate chase.
- Action 4: the model switch to MC_INDI_XY_* must land before SG2 scoring (the only unscheduled item on the G2 critical path).
Blockers: G2 = freeze-7 outer 24 cells + 2 rate/att spot checks flown and scored (G2Q queued; spot-check cells not in a queue yet).
G3 = tel_frozen hook + run 17 loss of control unexplained (set-up not fixed, no re-fly).
G4 = chatter item: cruise 89 Hz and AUTO_LAND 20-22 Hz lines, decided by scoring the freeze-7 18 runs (SC7).
G5 = G5.10 re-definition flights (SAT motors >= 0.99, full-scale stabilized), plus scoring of freeze-7 G5.3/G5.4 rows.

## Orchestrator response (S178)
- Acted on (6): action 7 merged into the G4/G5 items; G5 MINORs and G7 harness moved behind the G2/G4/G5 verdicts; G3 osc runs re-flown after the set-up fix, not chased; G2 spot cells queued (results/g2_spot_freeze7_s178).
- Not acted on: "switch models to MC_INDI_XY_*" was already done in 190b80ce3a. The "2x floor" condition for the 89 Hz search is not adopted: the keyed chatter detector decides, no new threshold.
