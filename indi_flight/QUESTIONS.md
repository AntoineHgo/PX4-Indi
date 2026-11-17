# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

## N2 (2026-11-17, owner note written after S65): anomaly list cleanup, A-9 on the new outer loop, A-30 escalation. Not blocking.

Act on this at the next route check or the next session that has room, after the work in STATE.md; do not interrupt a
task in flight. Then mark it closed and move it to JOURNAL.md.

**A. [DONE S66: `design/n2a_triage_s66.md`, applied to ANOMALIES; A-7 parked until C, not closed] Triage the old anomalies, one line each.** `ANOMALIES.md` still carries open entries from stage 1 (A-1 to A-7,
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

## Q5 (2026-11-17, S67): INDI same-seed runs differ at 400 Hz (A-30, your N2-C rule). Not blocking.

Context: `results/a30_refly_s67/README.md`. step_roll, INDI, 400 Hz, seed 1, same binary as S64 (no src change since
360c9ae453). Rise / settle / OS: A (speed 4) 210.0 / 356.3 / 0.54 %; B (speed 4, parallel to A) 205.6 / 360.0 / 1.18 %;
C (speed 1) 208.8 / 356.3 / 0.41 %; S64 seed 1 188.7 / 312.5 / 1.78 %. Raw A vs B: arm instant differs by 131 ms
(arming is wall-clock driven in the runner), sample counts 5600 vs 5607. So identical runs are not identical, and the
S64 outlier is reproduced by none of the three. G1.6 measured same-seed spread on PID only (settle <= 1 IMU period);
A vs B here exceeds that on settle (3.75 ms) and OS. Every INDI G2-STEP result is at speed 4 (A-4). All values remain
inside the G2-STEP limits.
Options: (A, recommended) run the G1.6 protocol on INDI (step_roll, 5 runs speed 4 + 5 speed 1, at 400 and 800 Hz,
~20 flights, CPU only), use the measured INDI spread as the rule-(d) spread, and look for the cause, starting with the
wall-clock arm (the noise phase at the step then differs). Fix it in the runner if it is the cause. (B) Require
sim-time arming and bit-identical runs before any further G2 claim (runner work first). (C) Keep parking A-30 until
the G2 table resumes.
Meanwhile: I do (A) as CPU work when there is room; nothing frozen depends on it. Blocking: no.
