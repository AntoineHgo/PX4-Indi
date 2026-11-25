# Route check 224 (S224, 2026-11-25, independent; GATE_STATUS.tsv unchanged 6 sessions)

Read: STATE, GATE_STATUS, ANOMALIES (not relevant to the blocker), D-OWNER-Q31, D-RATE-BLD-2, JOURNAL tail, RC221, RC223,
GATES "Owner amendment S218" + G3 pass items. Not waiting for S224-F (draw 264 on 903eae63, tb 1.0 + PID ref).

1. **Shortest path?** The target is right (G3 is the only row that gates G6/G7/G8 content), the pace is not. Since S218 seven
   sessions went into one draw (264) and produced probes, no scored evidence. Q31 step 1 allowed "one fix probe"; we ran
   falsifiers S222, blend probes S223 (joint and full plant) and now a baseline re-fly on the gate binary. The route is on
   the right branch but has stopped converging: fix (i) removes LOC yet fails G3 items 2 (post-fault 2 Hz) and 3 (0.37 m
   vs 0.30), so a pass is not in sight on this option alone.
2. **Decision behind the difficulty.** D-RATE-BLD (blend time constant 1.0 s, "decision 2"), frozen in FREEZE-10 on
   margin evidence (S76/S77) that never exercised a weak motor whose torque bias grows with collective. Secondary:
   D-FREEZE-10 itself (all gate rows are bound to one firmware, so any fix re-flies G2-G6), and the G3 draw design (sat +
   weak joint corner) that is the first test to reach this regime.
3. **Fresh start would:** treat the rate loop's disturbance rejection as a stated requirement from day one (an explicit
   bounded integrator, option (iii), or a per-motor command-to-torque estimate, option (ii)) instead of relying on a
   blend that is only an anchor below 1/(2 pi tb); and run the saturation + weak-motor corner in G2/G3 pre-freeze, before
   gates were bound to one binary.
4. **What blocks the next verdict change.** GATE_STATUS row **G3** (NOT PASSED). Missing: a firmware/default candidate that
   gives draw 264 on 903eae63 item 1 pass AND items 2 and 3 pass (or an owner ruling that 2/3 on this draw follow PID,
   if PID fails them too: the ref264_s224 result decides this), and then a fresh G3 campaign on that candidate (300 runs
   fail-fast). No G3 pass can be recorded before that campaign; G6/G7/G8 rows cannot change before the firmware is
   decided. Also unresolved: the S213 LOC baseline flew d220e193, so "INDI LOC on the gate binary at tb 1.0" is still
   not shown (S224-F answers it).
5. **Items moved since RC221:** none in any row. Moved in evidence only: G3 item 1 cause shown (two investigators,
   falsifiers S222); candidate (i) removes LOC on joint and draw 264 (S223, probes); items 2/3 on draw 264 show
   INDI-only failures at tb 0.10/0.05 (PID reference pending).
6. **Drop or simplify (STATE items).**
   - Action 0: stop widening the tb sweep; after S224-F no more tb probes. Decide by table: tb 1.0 LOC? PID items 2/3?
   - Drop "one session of cause search on post-fault 2 Hz / candidate (iv)" unless S224-F shows PID passes 2/3; take it
     straight to the owner as part of the question.
   - Merge the pre-approved solver + reviewer into a single task that compares (i) / (ii) / (iii) on the 4 draws
     already flown (joint, 264, 262, 283) with a written pass line, instead of more orchestrator probes.
   - Keep CUT as is: action 1 (G6 item 7), items 2 and 3 (G5 trap note is housekeeping), G7 (f)/(g)/harness/dead path,
     G8 drafting. Also defer "Before the next G3 campaign: Q30 tooling" until the firmware candidate exists (tooling does
     not depend on it, but nothing consumes it before).
   - Drop the item2_split detail work: pre-fault clean is settled; only the post-fault limit cycle matters.

## Is the Q31 route past its bound, and is an owner question due now?
Yes on the rule, partly on the route. The rule "one session of cause search before the decision is re-opened" was
exceeded: cause shown S221-S222, decision 2 effectively re-opened S222-S223 (D-RATE-BLD-2 PROPOSED), and S224 is the
7th session on this draw. Q31 step 2 (investigators) is done; the pre-approved solver + reviewer were not run, so step 3
(owner continue/stop) is not literally triggered. But D-RATE-BLD-2 option (i) changes a FREEZE-10 default and
invalidates G2, G3, G4, G5, G6 evidence; the owner's Q31 answer covers investigating and fixing the LOC, not a re-freeze
with a full re-fly. That needs an owner decision now (draft it once S224-F reports, same session).

Suggested question (A/B/C):
- **A.** Re-open FREEZE-10: change the rate-loop gap remover (first (i) MC_INDI_ACT_BLD default; if items 2/3 on 264 still
  fail, (iii) bounded rate integrator), re-fly G2 (rate/att, spot), G3, G4, G5, G6 rows on the new binary.
- **B.** Keep FREEZE-10, declare draw 264 (saturation 0.351 + weak 0.709 joint) outside the INDI claim: amend G3 (and the
  report limits) to exclude that joint corner, with PID as documented fallback; G3 then re-flies on 903eae63 without it.
- **C.** Stop the G3 route and report G3 NOT PASSED with the limit.
Include in the question: the PID reference on draw 264 (items 1-3), tb 0.10/0.05 numbers (item 2 fail, item 3 0.37 m),
the re-fly cost list of A, and my recommendation (A with (i) first, bounded to one solver session, B as fallback).
Note the memory rule "no PID fallback" in the owner direction: B must be worded as a stated limit, not a PID fallback.
