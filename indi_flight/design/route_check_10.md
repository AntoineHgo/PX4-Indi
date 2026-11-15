# Route check 10 (sonnet, 2026-11-15, session 11)

Read: MISSION Gates and Order of work, STATE, DECISIONS, ANOMALIES, JOURNAL tail, route_check_05. No source or test run.

## 1. Sessions 6-10 on the shortest path to G1?
Mostly yes, but slowly: five sessions closed about one third of G1. Done: logging at analysis rate (T15), ground-truth
stamp and time base (T10), second key on the trajectory metric (T11), self-tests for metrics.py and applied_timing.py,
runner with sends.csv (T12). A-8 closed. The applied-timing detour (T14, A-8) produced a note that "is not yet a jitter
bound" (payload constant), so it is the only item that overshot G1's need.
Remaining G1 items (GATES.md G1 is still a draft, 0 gate tests):
 a. Second independent script for every other primary metric (effort, hover/steady-state, settling, spectral) and a
    self-test for the runner/scenarios.
 b. Determinism: same seed and plant, N identical flights, tolerance stated or cause known (A-2, A-7, A-4). Never run.
 c. Injectors and plant variants verified: sim-time injections with moving payload (steps, mid-flight param), sag ramp
    in the gz bridge, payload frame/units, effect on measured rotor speed. None built (stage 1 simulator list: GNSS delay,
    battery model, seeded drops, vibration, variants, noise profiles).
 d. Finalise GATES.md G1 (exact tests and thresholds) and commit before the first test.
Next cheapest to close: b. CPU only, the logging profile and the pre-test hover already exist; N=5 identical hover
flights (plus one speed-factor pair for A-4) and a spread table from metrics.py. A haiku agent plus ~25 min wall.
It also gives the tolerance that d needs and tells whether c is worth building before or after.

## 2. Which decision is the difficulty a consequence of?
F-4 (archive never modified, fresh start) combined with the G1 wording "every metric a second independent script, every
script a self-test". Each archive script must be re-ported, self-tested and re-keyed, and at $1-1.6 caps each session
closes one sub-item (and each closure raises a new sub-question: A-8, logging rate, origin offset). Secondary: F-6+O-11
(outer loop replaces mc_pos_control at zero diff) still drives the design side; see 3.

## 3. Route check 05 recommendations
Acted on: 1 bench port (S7-S10, with logging fix); 3 partly (candidates_r2 by the orchestrator, no owner-question yet);
timebase, second key, applied timing, pre-test flights.
Not acted on: 2 G1 first test (same-seed repeats) never run, GATES.md still draft; 3 "close at r2, no fable review":
S11 launched an opus review r2 (T16) and no QUESTIONS.md owner summary exists, the rule "outer loop stops until G1 is
tested" was stated in 05 and is now broken in S11; 4 simulator items in G1 order: none started (no sim-time injection
hook, no seeded drops, no GNSS delay); 5 tidy: JOURNAL still has no S5, S9-S11 lines; STATE next-actions 2 and 4 remain
run-ons that mix done and open items.

## 4. A fresh start on stage 1 would
- Write GATES.md G1 first (list of metrics, tolerance form), then derive tasks from it, not from the review defect list.
- Run the determinism flights on the very first working hover (S3), before porting metrics: it sets the noise floor
  every later metric must be read against, and it is CPU only.
- Port only the metrics a gate consumes; skip applied_timing until a moving payload exists.
- One agent per session on a batch of 3-4 related items, not one item per session; fixed-format STATE (task table
  only), no history run-ons.

## 5. Three next actions, ordered
1. G1 determinism study (b): 5 identical-seed hover flights + 1 speed-factor pair on quad5in, spread table, then
   close or bound A-2, A-7, A-4. Haiku, ~20 calls, <$0.3; orchestrator reads the table (~5 calls).
2. Finalise GATES.md G1 with the measured tolerance, plus the remaining second keys (a): effort and hover metric
   independent scripts with self-tests. Sonnet, ~25 calls, ~$0.7; then one haiku re-run of the key (~8 calls).
3. First simulator hook in G1 order (c): sim-time injection/payload step with logged "applied", verified on a step
   scenario with a rotor-speed effect check. Sonnet, ~30 calls, ~$0.9, one session, no design work alongside.
Defer: outer-loop review r2 outcome is read when T16 lands, but no further outer-loop spend and no QUESTIONS.md
polishing before action 1 is finished. Tidy JOURNAL and STATE (~5 orchestrator calls) in the same session.
