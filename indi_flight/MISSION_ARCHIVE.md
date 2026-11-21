# Mission archive: finished parts of MISSION.md (owner file, not read at launch)

Moved verbatim out of `MISSION.md` on 2026-11-17 to shorten the prompt every session pays for. These steps are
done; their outcomes are in `STATE.md`, `DECISIONS.md` and `JOURNAL.md`.

## From "What exists"

Read that review once, at Stage 0: `indi_project/review/external_review_s59.md` (section 0 holds the owner's decisions) and
the notes in `indi_project/review/external_review_s59_notes/`. After Stage 0 you work from `STATE.md` and
`LESSONS.md` and open the review only for a specific item.

## The outer-loop architecture, steps 1-5 (done: study finished, base A confirmed by the owner, Q1 closed)

1. **Study.** Map what `mc_pos_control` does today, from the source: its inputs (`trajectory_setpoint`,
   `vehicle_constraints`, land detector, hover-thrust estimate, control mode flags), its outputs
   (`vehicle_attitude_setpoint`, thrust, status topics) and who consumes them, take-off ramp and landing logic,
   failsafe behaviour, EKF reset handling, manual altitude and position modes, and what `mc_att_control` adds.
   Output: `design/outer_loop_requirements.md`, a checklist every candidate must satisfy.
2. **Candidates.** At least two architectures written to the same template (interfaces, what is reused from the
   stock libraries, what is duplicated, how each mode and transition is served, where the INDI law sits, what
   happens without telemetry, cost in code and flash, upstream acceptability under O-11).
3. **Independent review.** A `fable` (or `opus`) agent that has not seen your reasoning reviews the candidates
   against the requirements file and the source, and is asked to find the mode or transition each one breaks.
4. **Iterate** steps 2-3 until a review round finds no blocking issue: at least two rounds. Record each round in
   `design/outer_loop_review_rN.md`.
5. **Ask the owner** to confirm the chosen architecture before implementation (a major decision, see below), with
   a one-page summary of the candidates and the review outcome.

## Stage 0, first launch only (one session) (done S1)

Commit the files of `indi_flight/` that are not yet tracked, and the untracked review files under
`indi_project/review/` (adding them to git does not modify them). Read the
review and its notes. Write `STATE.md` (format below), `DECISIONS.md` (owner decisions F-1..F-5 first) and an
`ANOMALIES.md` seeded with the open anomalies of review section 3.4. Then start stage 1.

## Former "State on disk" and "Budget" rules (replaced by "Token economy" in MISSION.md)

- **State on disk.** `indi_flight/STATE.md` has at most 150 lines: status in ten lines (stage, gate status table,
  blocker), next actions, tasks and batches in flight with their output files and the command that resumes them,
  open problems, the agent ledger of the current stage, lessons proposed. Finished history moves to
  `indi_flight/JOURNAL.md` (one line per milestone, append-only), which you do not read at launch. Update `STATE.md`
  before any long operation.
- **Budget.** Usage is the scarcest resource. Each launch has a spend cap given at the end of this prompt; the
  session is cut when it is reached, with its subagents. Keep bulky material in files. Do not re-read what
  `indi_flight/` already summarises. On a usage-limit error, save state and end the session.

## Former "Token economy" preamble (removed 2026-11-21)

In the first 57 sessions the orchestrator's own context was 78 % of the spend, and half of what it added came from
re-reading `STATE.md`, `LESSONS.md` and `QUESTIONS.md` (`STATE.md` was touched 4-15 times per session) and from
unbounded shell output.
