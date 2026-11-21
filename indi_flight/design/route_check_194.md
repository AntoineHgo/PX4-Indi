# Route check RC194 (S194)
Read: STATE, GATE_STATUS, DECISIONS (D-FREEZE-9 .. D-FREEZE-10), ANOMALIES, JOURNAL tail (S188-S193), RC178, freeze10_s193/README.
Nothing flown or run. Queue pid 1308846 is at G3 pre-test draw 13 of 20 (23:22); no row scored at freeze-10 yet. Gates: 1 of 8 passed (G1), same as RC178.

## 1) Shortest path?
Mostly yes now, but the last 16 sessions were not. Three freezes (8, 9, 10) were declared since RC178; each invalidated G2 outer, G4 and G5
outer rows. G2 (S184) and G4 (S187) were PASSED at freeze-9 and are open again, so net verdicts are zero. On path: D-FREEZE-9-GAP (G5.1/5.2/5.7
were never re-flown), cause-shown fixes (D-AF-ALIAS, D-G57-FF), one serial queue. Off path: D-XY-TRADE/D-XY-PICK sweeps (S181-183), the
Q19/Q20 guard re-score rounds, G3 cause chases on 02/05/03/08 (CAUSE_S191, matched-GNSS probe) that cost 3 sessions and may still end in an owner question.

## 2) Decision behind the difficulty
Same root as RC178: the freeze rule combined with outer-loop firmware that kept changing after evidence was flown (D-OFFB-POSVEL, D-JFF-KEEP kept
aa4fd2654a at owner request, then reverted by Q23). Direct trigger now: D-AF-ALIAS (outer a_f built at 88.9 Hz from 267 Hz data) plus D-FREEZE-10 itself,
which re-opened every outer row. Open risk inside it: D-FREEZE-10 leaves G3 02/05 resting on D-OFFB-POSVEL bandwidth vs uncompensated GNSS latency.

## 3) Fresh start on this stage (6 validation, 7 packaging G7/G8, G6)
- Before any outer-loop flight, run a sample-rate audit of every signal the module reads (decimation, aliasing vs 800/267/88.9 Hz): D-AF-ALIAS
  would have been caught before freeze-6, not at freeze-10.
- Fly the G3 pre-test and one G5.7 + one G4 chatter run on each candidate build before declaring a freeze (this was done only at S191, the
  third freeze); fly gate rows once, at the last freeze.
- Write the G7 harness (module unit tests, MC_INDI_ID_OK call site, D-OFFB-POSVEL wiring test) alongside stage 6, since it is a code-only item that
  does not wait for flight verdicts and would have caught the D-AF-ALIAS form with a decimation unit test.
- Decide the G3 GNSS-mismatch range (owner) up front, not after cause search.

## 5) Gate items moved since RC178
- G2: freeze-7 outer 24 cells + spot cells flown, PASSED S184 at freeze-9 (outer 24/24, spot 47.3/47.4, STEP 9/9); invalidated S192, re-fly in queue step 4.
- G3: set-up fixed (tel_frozen, Q22 box); pre-test 10/20 -> 15/20 key1, 16/20 key2 after D-AF-ALIAS; 02/05 cause shown (GNSS +95/+84 ms); 03/08 shared with PID.
  Draws re-flown at freeze-10 (step 1, running). No verdict.
- G4: chatter resolved (Q19/Q20 guard), PASSED S187 at freeze-9, invalidated S192; re-fly step 3.
- G5: G5.1 6/6, G5.2 6/6, G5.10 stab 3/3, G5.5 24/24 (worst 0.499 m); G5.7 FAIL -> cause D-G57-FF -> Q23 -> probe PASS 3/3. Re-fly step 2. SAT dropped (Q21).
- G6/G7/G8: nothing (G7 list in STATE item 5 unchanged).

## 6) Drop or simplify
- Do not read or chase anything until queue_status.tsv shows steps 1-4 done; score once per gate with the existing scripts. No new probes while it runs.
- Stop any further XY gain, D-OFFB-POSVEL or firmware tuning before the queue verdicts; a G3 02/05 failure goes straight to the owner question (mismatch range) with the matched-GNSS probe as evidence, not another cause search.
- Cut G3 draws 03 and 08 (shared with PID) from the chase: report them with PID values and put them in the owner question with the verdict data.
- Cut G5.10 PID reference and G5.5 margin work (0.499 m is a pass; no chase), A-39 / A-44 / A-50 / A-51 model cross-check work (all parked, none gates a verdict).
- Start the G7 harness items (STATE item 5: MC_INDI_ID_OK call site, D-OFFB-POSVEL wiring test, decimation unit test, checker self-tests) in the next
  session in parallel with the queue (code only, no firmware src change, no gate evidence touched); this is the next critical path after the verdicts.
- Cut A-58 (78 Hz line) and A-53/A-54 anomaly work: bound-and-record only.
Rules kept: F-9 direct path; F-*/O-* owner decisions and gate thresholds untouched; firmware change only for a gate failure with cause shown on a log.
