# Lessons from stage 1 (59 sessions, $156, archive in `indi_project/`)

Read this at every launch, after `STATE.md`. Each lesson is a rule with the stage-1 event that produced it. The
evidence is in `indi_project/review/external_review_s59.md` and its notes folder. The owner maintains this file; the
orchestrator proposes additions in `LESSONS_PROPOSED.md`.

## Evidence

1. **A number that decides anything is computed twice, by code written independently, from raw logs.**
   Stage 1: `bench/metrics.py` scored trajectories against a reference logged at 5 Hz and held between samples. All
   outer-loop results were wrong (reported ratio 0.69, real 0.23) and three reviews did not see it, because they
   compared report text with result files.
2. **Check the logged rate and time base of every signal before using it.** No zero-order hold of a decimated
   topic, no derivative of an irregularly sampled signal, no mixing of `timestamp` and `timestamp_sample`, no
   spectrum above half the logged rate. Log what the analysis needs at the rate it needs.
3. **Tracking is measured against simulator ground truth**, stamped with simulation time, not against the estimator.
   Estimator error is reported separately.
4. **Every analysis and identification script has a self-test on synthetic data with a known answer**, including a
   closed-loop case. Stage 1: the G1 identification gave 321 and 211 on a symmetric vehicle; the thrust-constant fit
   was a one-point ratio (g divided by mean thrust) with a meaningless R^2.
5. **Seeds that change only sensor noise are one sample.** Generalisation comes from varying the plant, the scenario
   and the airframe. A p-value over noise seeds is not reported as evidence.
6. **A criterion is an absolute, physical quantity with a threshold that matters on a vehicle.** Stage 1 failed
   INDI on a 2x ratio of motor-command derivative that was 0.1 % against 0.2 % of full scale, against a baseline
   whose own value varied 3.5x between identical flights.
7. **A scenario is flown once with the reference controller before it enters a validation set** (O-13). Stage 1
   spent 80 flights on entries no controller could fly.

## Design

8. **Identified, never tuned.** Effectiveness, time constants, delays and thrust constants come from identification.
   Stage 1: a tuner chose an actuator time constant faster than the plant and produced the H5 limit cycle.
9. **Measured actuator state removes the implicit integral action** against any gap between command and output.
   Stage 1: v2 held 13 deg of tilt on a weak motor. The same structure sits in the outer-loop thrust channel and is
   untested there. Every loop that feeds back a measured actuator needs a stated answer to "what removes a steady
   command/output gap".
10. **No design is frozen without a measured stability margin and an explanation of every failure near it.**
    Stage 1 froze a blend time constant of 0.3 s while 0.1 s crashed unexplained, and never measured a loop gain.
11. **An unexplained anomaly is an open item with a closing test, not a footnote.** Stage 1 left six open (blend
    crash, PID hover spread, vertical excursions, speed-factor sensitivity, a failed tuning candidate, outer-loop
    hover noise).
12. **Defaults are a validated configuration.** Stage 1 shipped firmware defaults that matched no tested setup and
    parameter files that only the benchmark runner could load.
13. **Validate the final configuration on the whole matrix.** Stage 1 built each held-out set around the previous
    weakness; the final inner loop never flew a gust.
14. **Simulator extensions are code under test.** Stage 1 found by accident a world-frame torque injector and a
    110 ms estimator artefact. Frames, units, timing and determinism of every hook are checked before use.

## Process

15. **The orchestrator decides; subagents do the work.** Stage 1: 72 % of the spend was the orchestrator's own
    context, with about one subagent per session.
16. **State stays small.** `STATE.md` under 8000 bytes (the supervisor checks it). History goes to `JOURNAL.md`,
    the agent ledger to `LEDGER.md`, proposed lessons to `LESSONS_PROPOSED.md`; none of them is read at launch.
    Stage 1 re-read a 131 KB state file 61 times.
17. **Two keys for anything that decides a verdict or flies:** metric code, identification code, simulator hooks and
    control-law changes are reviewed or re-implemented by an agent that has not seen the first one's reasoning,
    before the result is used. Scope (owner, 2026-11-21): firmware changes, identification code, and a new metric
    script before its first use as gate evidence. A re-scoring with an already keyed script, a result note, a probe
    or a decision does not get a second key.
18. **A review brief names one interface:** raw data to result, result to report, or code to specification.
19. **Review before freeze.** Stage 1 found a control-law bug eight sessions after freezing the firmware that
    contained it.
20. **Passing tests prove what they assert, nothing more.** Stage 1: four defects in code with green tests. A new
    behaviour gets a test that fails when the behaviour is broken; check it by breaking it once.
21. **Size long tasks to the budget.** Launch an agent only if the session has twice its expected cost left; agents
    write as they go. Stage 1 lost 24 % of its agents to session ends.
22. **The report describes the final design first** and keeps history in an appendix. No drafting residue, no
    description of removed code in the present tense.
23. **Pre-test before a campaign.** One to three flights that prove the configuration flies and the metric runs,
    before any long batch. Stage 1 flew 200-flight batches for entries and candidates that a single flight would
    have ruled out.
24. **Check the route regularly and step back without hesitation.** Stage 1 never revisited a decision unless the
    owner intervened; v2 was tuned and validated for ten sessions on a structure that could not work. When a fix
    needs a second fix, re-open the decision underneath.
25. **One airframe until the design is right.** Breadth comes last.
26. **Ask the owner for the few decisions that shape everything.** Stage 1's rule "never ask" turned owner reviews
    into the only course corrections, each arriving after the cost was paid.
