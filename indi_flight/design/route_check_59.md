# Route check 59 (sonnet, S59-S60 boundary, 2026-11-17)
Read: STATE, DECISIONS (headings, D-S3-*, D-G2-OUTER-DEFER, D-outer-arch), ANOMALIES (open), JOURNAL tail, GATES headings, route_check_57. No source read, nothing flown.

## 1) Still on the shortest path?
Mostly yes, with one drift. Route check 57 recs 1-2 are done (G2 table stopped S57, items 1-4 coded S58-S59, hover PASS x2).
After 59 sessions 0 of 8 gates are passed, and stage 5 (the largest work, every mode) still has no line of code. That is the
real risk, not the safety items. The next action drifts: an opus review ($1.1, ~1/3 session) of ~4 small, already
break-checked, unit-tested, haiku-keyed items, whose triggering paths cannot be exercised before stage 5/G5 anyway (STATE: "Triggering
paths of items 2/3 in SITL: G5"). GATES.md lists only G1 FINAL and G2 in detail; G3-G8 have no written test yet, so stage 5 has no
acceptance target to code against: that is the other gap.

## 2) Which decision is the difficulty a consequence of?
D-outer-arch plus the S57/S58 deferrals (D-G2-DEFER, D-G2-OUTER-DEFER): the project froze architecture A (A1-A17 + optional A18) in
S13 but wrote no stage-5 code, so every outer-loop-dependent item (A-6, A-26, M3b breaks, thrust-gap, G3/G5 evidence for items 2/3) is
blocked behind it. The deferrals were correct (do not buy evidence before the law is frozen) but they make stage 5 the single
critical path, and S58-S59 spent two sessions on stage-3 items that only G5 can validate. Secondary: D-S3-SPTO/D-S3-LANDED choose
behaviours (hold thrust, no slew in flight) whose failure cases are G5 scenarios, so review now can only check the code against
the text of the decision, not the decision.

## 3) What a fresh start would do differently
Stage 3: derive G1/G2_Y/tau first and write D-YAW-INV and lead from day one (as route check 57 said); land safety items with the
module build in the brief (S58 lesson); no per-rate flown tables. Stage 5: start it BEFORE finishing stage 3, as a thin hover slice
over the frozen rate law, because the outer loop decides what the inner loop needs (flatness feed-forward, setpoint timeout
semantics, landed handling). Write G3-G8 test definitions at the same time as the architecture, so each stage-5 slice has a pass
test; run the safety items' triggering tests (false maybe_landed, stale setpoint, frozen rpm injection) as G5 scenarios from the
first outer-loop flight instead of as separate reviews.

## 4) Recommendations (ordered)
1. S60: commit the working tree, rebuild SITL at HEAD (G1.7 provenance), skip the opus review; start the stage-5 hover slice
   (architecture A pos/vel/acc loop publishing to the rate module, hover + thrust-gap flight). Cost ~$2.5 (sonnet code ~$1.0,
   build/flights host-side ~$0.3, haiku key ~$0.1, state ~$0.3). Pays: first real outer-loop path, unblocks A-6, A-26, M3b.
2. S60 or S61 (haiku/sonnet, ~$0.2): write G3-G8 pass tests in GATES.md from MISSION (one session slice), including the item
   2/3/1/4 triggering scenarios (false maybe_landed, 2 Hz offboard stream, frozen rpm, stop/start within 0.5 s), so stage 5 has an
   acceptance target and the safety items get tested where their risk lives.
3. S62+: review the safety diff once, together with the stage-5 slice diff, at the first G5 pass or before the stage-6 freeze,
   by sonnet at ~$0.5 (opus only if G5 finds a miss). Expected cost ~$0.5, replaces the $1.1 now.

## Is the opus review of small safety items worth $1.1 versus stage 5?
No, not now. The items are small, tested to the break, keyed by haiku (AGREE, 5 minor, none blocking) and flown (hover x2 clean).
The residual risk (thrust hold never exercised, 0.5 s stop/start refusal) is a behaviour question that G5 answers, which an
opus read cannot. $1.1 is about 40 % of a session that could buy the first stage-5 flight. Cheaper substitute: one haiku
read-check ($0.06) of the two unverified points listed by T120, inside rec 1.
