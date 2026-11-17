# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

## N2 (2026-11-17, owner note written after S65): anomaly list cleanup, A-9 on the new outer loop, A-30 escalation. Not blocking.

Act on this at the next route check or the next session that has room, after the work in STATE.md; do not interrupt a
task in flight. Then mark it closed and move it to JOURNAL.md.

**A. Triage the old anomalies, one line each.** `ANOMALIES.md` still carries open entries from stage 1 (A-1 to A-7,
A-9, A-17, and the other pre-S36 rows without a CLOSED or PARKED mark). A long open list weakens the rule "nothing is
frozen with an open anomaly that touches it": it becomes noise. For every anomaly older than S36, decide and write one
of: CLOSED (with the evidence that answers it, including later work that answered it without anyone saying so), PARKED
(a written bound by mechanism and a reopen trigger), ARCHIVE-ONLY (concerns code or a result that no longer exists, say
which), or OPEN with the stage and gate it blocks. A-7/A-2 (determinism) must be checked against G1.6 and the sim-time
player before being closed. Cap: one session, haiku or sonnet for the evidence reads, one commit.

**B. A-9 on the new code.** A-9 (yaw-rate feed-forward double count on roll/pitch when tilted) was found in the old
`McIndiPosControl`, which `mc_indi_pos_control` replaced in S60. Check by reading and by a unit test whether the new
module can double count (a circle with yaw locked to the path, several tilts, total rate setpoint against flatness
truth). If the new code has no such path, close A-9 as ARCHIVE-ONLY. A-6 (hover command excess below 30 Hz): keep its
signal-substitution ablation in the stage-5 plan, and name it in the combined review brief. Both must be closed or
bounded before any stage-5 freeze.

**C. A-30 escalation (400 Hz seed spread).** If the planned re-flight of seed 1 step_roll at 400 Hz gives DIFFERENT
results between two identical runs, that is run-to-run nondeterminism at 400 Hz and touches A-7 and every G2-STEP
claim at 400 Hz: stop parking, open a question to me (QUESTIONS.md, blocking only if a G2 freeze depends on it). If
the two runs are identical, the seed-driven reading stands: bound it with 5 more seeds as already planned.
