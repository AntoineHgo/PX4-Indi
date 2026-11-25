# Route check 228 (S228, 2026-11-25, independent; GATE_STATUS.tsv unchanged 10 sessions)

Read: STATE, GATE_STATUS, GATES "Owner amendment Q33", D-OWNER-Q33, JOURNAL tail, RC226. ANOMALIES skipped (nothing on the blocker).

1. **Shortest path?** Yes in direction, but the tooling queue grew. Q33 B adds a scenario change (event hover, +23 s/run)
   in front of the baselines, so the solver run (c) is now 3 serial steps further away than at RC226. It still ends:
   build -> 2 re-flies -> 2 baselines -> solver -> review -> pass or route B.
2. **Decision behind the difficulty.** D-RATE-BLD (ACT_BLD 1.0 s, FREEZE-10 decision 2), unchanged from RC226. New second
   layer: the G3 test text (items 4/5) was written without a static pre-event reference (S214 "events at main start"),
   so Q30, Q33 are test-definition debts, not controller problems. D-FREEZE-10 (one binary) still forces a re-fly of G2-G6.
3. **Fresh start would:** fix the scenario (event hover, static reference, item 2 skip rule, both keys) in the gate text
   before the first campaign, and require rate-loop disturbance rejection as a freeze requirement.
4. **Blocks the next G3 verdict (smallest first).**
   a. Build event hover in g3_lemniscate + g3_stick_zsine (length derived from disturbance.py), item 5 refs, gust in item 5
      and item 2 skip windows, break-checked self-tests in both keys (no flights, one commit).
   b. Re-fly draw 0 INDI + PID on 903eae63, both keys (2 runs). If PID fails item 5: owner question (only branch that adds a wait).
   c. FREEZE-10 baselines 262 / 283 (+264/joint) on the new scenario, scored both keys.
   d. Solver run (opus, high) (i)/(ii)/(iii), values fixed first. e. One independent review.
   f. Pass -> freeze-11 + re-fly list; fail -> route B (fixed corner) + G3 300 on 903eae63.
5. **Moved since RC226:** no gate row. Evidence: S227 pre-test flies end to end, keys agree, INDI items 1-4, 6 pass,
   item 5 FAIL 0.576 m (PID 1.210 m, item 4 FAIL 0.764 m); Q33 answered B, GATES amendment text fixed. Item 5 definition
   settled, items 1-4, 6 on draw 0 are the only G3 numbers produced.
6. **Cut / simplify (no threshold lowered).**
   - Do (a) as one commit for both scenarios; flight (b) as one docker job (INDI+PID) and chain (c) behind it, no review between.
   - Skip "re-score S227 pre-test": Q33 states it is evidence for items 1-3, 6 only. Do not rescore it.
   - Keep the S227 note-free rule: no more route checks until the solver verdict (RC226 item 6, next slot S235).
   - Baselines 264/joint on the new scenario only if the pass line lists them; do not add draws.
   - **Independent of G3 firmware:** G7 checks not touching firmware (format, zero-diff re-run, DEFAULTS_DIFF text,
     docs link/prettier check) and G8 chapters for passed gates G1, G2, G4, G5 (ch.1, 2, 4 numbers, history errata) can
     proceed on CPU idle in parallel with flights (not in docker during gate flights). They will NOT change GATE_STATUS sooner:
     G7 and G8 both depend on the final firmware (freeze-11 or route B), so they can only reach "ready for final numbers".
     Items already CUT (G6 item 7, F-10 unit 9) stay cut. Only G3 moves a row.
