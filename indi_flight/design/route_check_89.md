# Route check 89 (S89 start, 2026-11-18)
Read: STATE, GATES (G2 section), DECISIONS (headings, D-G2-PINJ, D-HOLE-EXCESS), ANOMALIES, JOURNAL S84-S88 lines, route_check_84, git log. Nothing flown, no code opened.
Gates: 1 of 8 passed (G1, S84). G2 still open after 88 sessions.

## 1) Still on the shortest path?
Half. The 28 G2 outer cells (z and xy velocity/position break, PM 50-66 deg, GM 18-19 dB, 800/400 Hz) are real G2 evidence. But the
last three sessions bent toward tooling: of S85-S88, S85 and S88 were mostly hole_report work (build, count fix, raw-gap, D-HOLE-EXCESS,
slow-topic fix, three second keys, one rename, two re-flies of cells that had already measured PM). S86 and S87 were mixed (about half
cells, half hole_report fixes and keys). Count since S84: about 13 of ~30 commits are hole_report/rename/state, 0 gate lines changed.
The hole checker was fixed four times in a row (S86, S87, S88 x2), each time after the previous key found a minor. That is polishing a
checker whose result on the 28 cells was already PASS or explained. Re-flying two cells only to clear a hole flag, when PM was
measured and unaffected, bought no gate item. RC84 asked for the G2 report at S86; it is not started. The G2 runner name is still
"to be named" in GATES.md. Missing for G2: attitude break (note unreviewed-then-reviewed, not implemented), yaw, 267 Hz reported run, model-only
vs v2 split, stage-output break at 800/400 across axes, worst-of-2 seeds per cell, model cross-check (A-26/A-34/A-35 still sit under it),
the G2 report. G3-G8 text is still "NOT final" (S64): 25 sessions old.

## 2) Which decision is the difficulty a consequence of?
Decision 2 (measured actuator state, no PID fallback; D-GAP/D-RATE-BLD for it) combined with the G1.6/G1 evidence-integrity rule
(sim holes invalidate a run, D-G2-PINJ one-break-per-loop, serial flights only because parallel load causes holes, A-32). Every cell
needs its own break, injector and key, and every flight is only trusted after a hole check. The hole checker became the work item because
G2 validity requires "no gap" and the spec was written before the sim's real behaviour was known (D-HOLE-EXCESS is a spec change).

## 3) Fresh start on this stage
- Write the hole rule once from a measured gap distribution of a few idle-host flights, as an evidence limit with a stated tolerance,
  and report holes beside the margin, not as a gate on re-flying. Stop at the first tool that gives the answer.
- One runner and one config table (loop, break, rate, path, seed) named in GATES.md before the first cell; the G2 report is generated from it.
- Fix G3-G8 text and the flight matrix first; choose slices by gate coverage.
- Do the attitude break and yaw (new loops) before re-scoring or re-flying old cells.

## 4) Next 3 actions
1. S89: run T189 (hole_report on the 28 cells) as already launched, accept the result whatever it says, record in README, then FREEZE
   hole_report. Closes: G2 validity item "holes" and D-HOLE-EXCESS. Do not open a new key or fix unless a cell flips a PM verdict.
2. S90: implement the attitude break (T185 amendments: call-site test at McIndiRateControl.cpp:231, logged rate_sp_dot check, hover_xlong), fly
   it at 800/400 serial, one seed pair. Closes: G2 attitude row; may close A-26 (low-frequency phase) and inform A-34/A-35.
3. S91: write the G2 report from the existing cells (rate, z, xy, attitude, accel-break) with an explicit "not covered" list (267 Hz, yaw,
   model-only), name the runner command in GATES.md, and write the final G3-G8/G5 text. Closes: G2 pass/fail verdict on 800/400 and the
   "one command per item" line; unblocks G5.
Stop: new hole_report fixes or second keys on tooling; re-flying cells with passing margins for log cosmetics; per-session new NEXT lists
(use this list); anomaly chases without a failing gate test (RC74 rule still holds: A-4, A-6, A-30, A-32, A-34, A-35 parked).
Budget: if G2 has no verdict by S92, owner decides whether to narrow G2 to rate+z+xy and push attitude/yaw to stage 6.
