# Route check 231 (S231, 2026-11-26), orchestrator question, no code run

Inputs: STATE, GATE_STATUS (unchanged 13 sessions), Q34, D-RATE-BLD-2 / D-OWNER-Q32 / D-OWNER-Q33, RC230.

1. Shortest path: yes, with one trim. Only G3 can move a row. What blocks the next G3 verdict, in order:
   (c) solver run on (i)/(ii)/(iii), (d) one independent review, (e) verdict -> freeze-11 + re-fly, or route B
   (fixed corner) + G3 300 on 903eae63. Q34 blocks only item 5 rows and the final (e) scoring, not (c).
2. Current difficulty is a consequence of D-OWNER-Q33 (event hover, item 5 on a static reference) on top of
   Q32 (bounded re-freeze, item 2 fault windows): each owner amendment re-opened the scenario and keys, and
   Q34 is the next test-definition question on the same item 5.
3. Fresh start: same order. It would pose the item 5 reading together with the scenario change (one question),
   and would run the solver before building the second key. Nothing to redo now.
4. Gate items moved since RC230: none. GATE_STATUS rows unchanged.
5. Cut / simplify:
   - D-RATE-BLD-2 pass line (fixed, never edited) lists items 1-3 as pass criteria and "Items 4-5 reported".
     So the solver does not need item 5 to rank candidates: (i) < (ii) < (iii) by simplicity, first that passes
     items 1-3 plus G2 margins wins. Q34's answer cannot change which candidate wins on this line. It can
     only change how item 5 is reported (A/B/C re-score = no flight, 4 pre-test runs).
     => Start (c) now. Waiting saves nothing; the answer is cheap to apply afterwards.
   - Brief the solver: report item 5 per event as raw max position and max tilt in the event window, so
     any of A/B/C can be scored from its output without a re-flight.
   - Keep the STATE cuts (no tb sweeps, no item2_split, no 2 Hz cause search). No new route check until (c)
     returns or Q34 is answered.
   - G6/G7/G8 work independent of G3 firmware: none that moves a row. G6 item 7 and G7 (f)/(g) change or
     re-fly with firmware; G8 docs need the verdict (ch.3 G3/G6 numbers). G7 (f) unit 9 renames would touch
     firmware that freeze-11 may change; the owner and RC221/RC226 cut it. Cheap non-row prep only: none worth spending on.
6. Recommendation for the ~$3.8 budget: launch (c) now, one opus/high solver run (~$2-3), values fixed
   before review, leave ~$1 for committing the result and STATE; do not wait for Q34.
