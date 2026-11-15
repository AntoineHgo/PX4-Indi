# Route check 05 (sonnet, 2026-11-15, after session 5)

Read: MISSION.md (outer-loop, gates, order of work), STATE.md, DECISIONS.md, ANOMALIES.md, JOURNAL tail,
`design/outer_loop_review_r1.md`. No source re-read, no test run.

## 1. Still on the shortest path to G1-G8? Is the balance right?

No. The balance is wrong.
- Every gate G1-G8 is measured on a controller in the simulator. After 5 sessions: 0 of 8 gates tested, the bench is
  not ported (STATE.md next action 4), no simulator item of stage 1 beyond the airframe model (action 5), G1 is a
  draft (GATES.md), 7 anomalies all open (ANOMALIES.md A-1..A-7, each closes only with bench or simulator work).
- Outer-loop spend: T4 0.75 + T5 0.5 + T6 2.5 = ~$3.75 of $5.55 recorded agent spend (STATE.md ledger, T3 cost not
  recorded), plus candidates r1 by the orchestrator and all of sessions 4 and 5. Roughly two thirds of the money,
  for a decision MISSION.md ("Outer-loop architecture", step 5; "Stage 5") needs only before stage 5 starts.
  MISSION says "in parallel with stages 1-3", not instead of them.
- Review r1 found 0 BLOCKING for A (`outer_loop_review_r1.md` section 1). The remaining items F1-F5 and the five
  conditions (section 4) are text-level design fixes. More paper rounds have falling value: several answers
  (F4 thrust scale, F15 hardware rate, `normalisedThrustFromRpm` linearity) can only come from code or a prototype.
- Both stage 1 deliverables the later gates need (bench with ground-truth stamp, determinism A-2/A-7) are CPU work,
  not token work; MISSION says "prefer work that spends CPU over work that spends tokens". The project did the opposite.
- Bookkeeping drift: JOURNAL.md has no S5 line; STATE.md next-action 2 is a stale 10-line run-on.

## 2. Which decision is the main difficulty a consequence of?

F-6 (outer loop replaces `mc_pos_control`) combined with O-11 (stock modules at zero diff, separate modules) and
F-2 (every mode). Together they force the new module to re-implement or wrap everything `mc_pos_control` does
(R1-R51) without editing it. That is why a 51-item requirements file, 17 review findings and a shell-copy
architecture exist. The F2 name collision is the "fresh start preserving the archive" owner direction (MEMORY.md)
meeting the archive's `mc_indi_pos_control` module and `MC_INDIP_EN`. F1/F4 come from copying stock
PositionControl into a different thrust scale. Nothing here is an error; it is the price of F-6+O-11, and the
price was not weighed against its place in the schedule.

## 3. What would a fresh start on this stage do differently?

- Order by what gates consume: bench port + G1 test first (stock PID on `quad5in`), because it unlocks G1, A-2, A-7,
  A-4 and every later measurement. Outer loop in the background with a hard cap of 1 session of effort.
- Decide architecture A in one DECISIONS.md entry with the five review conditions as acceptance items, ask the owner
  at once (QUESTIONS.md), and let the owner answer while CPU work runs. Do not wait for a second paper review round.
- Use a prototype as the second review (MISSION step 6): shell copy of `mc_pos_control` with the INDI stage behind a
  flag, then fly take-off/mode switches in SITL. A prototype finds F3/F4-type faults for ~$1 of sonnet, a fable
  paper review costs ~$2.5 and still missed what only running shows.
- Reserve fable for decisions a prototype cannot settle (pre-stage-5 owner summary, stage 3 design).

## 4. Recommendations for the next 3 sessions (ranked)

1. **Port the bench (STATE next action 4) with self-tests and second keys; include the logging profile fix
   (vehicle_acceleration at controller rate).** One sonnet agent, brief at <=25 calls. Cost: medium (~$1-1.5).
2. **Finalise GATES.md G1 and run its first test: same seed, same plant, N repeats on `quad5in` with stock PID, CPU
   only; closes or bounds A-2/A-7 (and A-4 with a speed-factor pair).** Mostly shell time. Cost: cheap-medium (<$1).
3. **Close outer-loop design at r2 by the orchestrator, no fable:** one DECISIONS.md entry (decision 1: A, B
   deferred, C rejected F10), F1-F5 + R1/R14/R24/R25/R33/R41/R47 fixes folded in as text, rename plan for F2, one
   owner question in QUESTIONS.md. Check `normalisedThrustFromRpm` and thrust scale by reading code (2-3 greps).
   Cost: cheap (~$0.5). Log the deviation from MISSION "at least two rounds" in DECISIONS.md with the reason.
4. **Simulator items in G1 order, not list order:** simulation-time injection and ground-truth stamp first, then seeded
   telemetry drops and delayed GNSS. One sonnet agent per session. Cost: medium each (~$1).
5. **Tidy state:** add the S5 JOURNAL line, collapse STATE next-action 2, record this route check. Cost: cheap
   (<$0.2). Then no fable review until the A prototype exists (expected S8-S9); one stage-1 close-out review is the
   only fable spend worth ~$2.5 before then.

Rule for the next route check (after S8): if stage 1 is still open or G1 untested, outer-loop work stops until it is.
