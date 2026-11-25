# Route check 226 (S226, 2026-11-25, independent; GATE_STATUS.tsv unchanged 8 sessions)

Read: STATE, GATE_STATUS, ANOMALIES (size only, nothing on the blocker), Q32 + owner Answer, JOURNAL tail 5,
D-OWNER-Q31, D-RATE-BLD-2, RC224.

1. **Shortest path?** Yes, now. RC224 asked for a table decision and an owner ruling instead of more probes; both
   happened (ref264_s224 scored, Q32 answered A bounded in one session). The bounded route (one solver, one review, then
   B with a fixed corner) has a hard end, so it converges. Risk: the unchanged pace of the sequence before the solver
   (Q30 tooling, two baselines) is a serial CPU queue that nothing else needs to wait on.
2. **Decision behind the difficulty.** D-RATE-BLD (ACT_BLD 1.0 s, decision 2 of FREEZE-10), frozen on S76/S77 margin
   evidence that never exercised a weak motor with a collective-dependent torque bias. Second: D-FREEZE-10 binding all
   gate rows to one binary, so any fix re-flies G2-G6.
3. **Fresh start would:** state rate-loop disturbance rejection (bounded integrator or per-motor gain estimate) as a
   requirement before freezing, and fly the sag + weak-motor corner in G2/G3 pre-freeze. It would also write the
   item 2 window rule (skip fault-straddling windows) together with the test, not after PID failed it.
4. **What blocks G3 (ordered, from Q32 points 2-7).**
   a. Q30 tooling: S214 window for items 4-6 in both keys + item 2 skip rule (point 7) with self-test in both keys
      (straddling sine not flagged, post-fault sine flagged, break-checked) and skipped-window table.
      Deliverable: scorer commit + self-test log; rescore of the valid 903eae63 runs (4 draws, PID refs).
   b. FREEZE-10 baselines of 262 (C212 idx 22) and 283 (C5) on 903eae63, scored by (a).
      Deliverable: two scored rows (pass or "not worse" G3 risk).
   c. Pass line committed in D-RATE-BLD-2 (draws joint/264/262/283, speed 1, seeds, both keys, G2 rate cells, unit-test
      list) before any candidate flight. Deliverable: one commit, text only.
   d. One solver run (opus, high): (i)/(ii)/(iii), values fixed before review. Deliverable: candidate commit + table
      of the four draws + G2 rate cells + break-checked unit tests.
   e. One independent review. Deliverable: verdict; BLOCKING = no pass, go to B (point 5), no new question.
   f. Winner: re-fly 264 + joint; build freeze-11; G3 300 fail-fast (then G2/G4/G5/G6 item 7 re-fly per point 6).
      Deliverable: G3 verdict row. On B: amended G3 text with the fixed excluded corner + same 300 re-fly.
5. **Moved since RC224:** no GATE_STATUS row. Evidence: tb 1.0 on 903eae63 LOC (baseline now on the gate binary);
   PID ref on 264 passes items 1 and 3, item 2 fails only on straddling windows; Q32 answered A bounded with item 2
   rule; pass-line content now fixed by the owner (points 3-7). G3 stays NOT PASSED.
6. **Cuts (no threshold lowered, Q32 points 1-7 kept).**
   - Write the pass line (c) in parallel with (a)/(b): it needs no flights, only the owner text. Order of flying stays.
   - Run (a) and (b) as one CPU job in docker (baselines need only the (a) scorer at scoring time, not at flight time).
   - Do not run a route check per session during (a)-(e); next RC after the solver verdict (S235 slot is fine).
   - Trim STATE: delete the "Deferred" wording on Q30 tooling (it is now step 1), and collapse items 3-5 (G7/G8
     lists) into one CUT line pointing at their files. Frees STATE budget and agent reading time.
   - Solver brief: forbid tb probe sweeps, item2_split work and post-fault 2 Hz cause search (already in STATE),
     one tuning grid per candidate with the value list fixed before flying.
   - Unit tests are owner point 3 (not cut). Only sequencing: write them after the winner is chosen, for the winner.
