# Route check 64 (sonnet, S64 start, 2026-11-17)
Read: STATE, DECISIONS (headings, D-S3-*, D-outer-arch, D-S5-SLICE), ANOMALIES (open), JOURNAL tail, GATES headings, route_check_59. No source read, nothing flown.

## 1) Still on the shortest path to G1-G8?
No, drift again. 0/8 gates passed after 63 sessions. GATES.md has only G1 FINAL, G2 and G2-STEP written: G3-G8 still have
no test text (route check 59 rec 2 was never done). Stage 5 is one hover slice (S60) and has had no session since.
Drift, concretely:
- S61-S63 (3 sessions, ~$9) went to attitude-step overshoot (D-S3-ATT-STEP, T125-T128, A-28/A-29): an inner-loop item
  that the owner note N1 asked for and that is now closed in model + 12 flights. It was legitimate, but it is stage 3 work
  done a 4th time (S47-S63 on stage 3) while stage 5 holds all remaining modes.
- NEXT list item (1), r_dot_f noise (G4 pre-look) and (2), attitude-break margin: both are D-S3-ATT-STEP "open before freeze"
  items, i.e. more stage-3 closing. G4 has no written test, so (1) measures against no threshold; (2) is an outer-loop
  break that D-G2-OUTER-DEFER says to do against stage-5 code. Only the "first formal G2-STEP test" is on path.
- Position, velocity, acro, offboard, acceleration modes: 0 flown. The N1 C2 bench defect (disturbance.py mis-sized on
  quad5in) blocks every outer-loop disturbance campaign and is still open.
On path: thrust-gap flights on the slice, slice second key, G5 test list.

## 2) Which recorded decision is the difficulty a consequence of?
D-S5-SLICE (S60) read with D-outer-arch: the hover slice deliberately deferred A4, A10/A15 and A11 (thrust-gap remedy),
so every later question (thrust gap, noise limits, outer breaks, A-6, A-26) needs a slice that does not exist, and
meanwhile the inner loop absorbs sessions. Underneath: D-G2-DEFER / D-G2-OUTER-DEFER made correct choices not to buy
evidence early, but with no G3-G8 text nothing pulls the work toward stage 5. The stage-3 overshoot itself follows
D-RATE-LEAD (S48-S53): feedback-only lead, checked on inner-break margins only (S61 lesson).

## 3) What a fresh start would do differently
- Write G3-G8 pass tests first (one haiku/sonnet task), so each stage has a target and r_dot_f noise, thrust gap, modes
  are tested against a number, not explored.
- Build stage 5 as full mode coverage in thin slices (position, velocity, acceleration, acro, offboard) before polishing
  any inner-loop metric; verify inner changes through the outer step response from day one (S61 lesson).
- Fix the bench (N1 C2) before the first disturbance campaign, not after.
- Time-box inner-loop work: one session per law change, then freeze and move on.

## Recommendations (ranked, S64-S66)
1. S64: write G3-G8 test definitions in GATES.md (sonnet ~$0.5, from MISSION; include r_dot_f noise as a G4 row, thrust-gap
   hover, false maybe_landed, 2 Hz-vs-10 Hz offboard stream) and run the formal G2-STEP test on a clean tree (host bash
   ~$0.2). Drop NEXT (1)-(2) as standalone work: fold r_dot_f noise into the G4 row, attitude-break into the stage-5 M3b plan.
2. S65: stage-5 slice 2: thrust-gap hover scenario, MC_INDI_W_MAX 2700, T123 deviations (reset on re-config, A3/A5), plus
   the next mode slice (velocity/acceleration, A10/A15) in the same sonnet task if the budget allows; haiku key ($0.06).
3. S66: bench N1 C2 fix (mass/drag from flown model, G1.5 per profile) then first outer-loop disturbance flights; one
   combined review (safety diff + slice) by sonnet ~$0.5 before any freeze. Stop opening inner-loop items unless a gate fails.
