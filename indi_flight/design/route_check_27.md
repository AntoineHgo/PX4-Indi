# Route check 27 (sonnet, 2026-11-16, session 27)
Read: STATE, DECISIONS (G1/sim entries), ANOMALIES, QUESTIONS, JOURNAL tail, GATES G1, route_check_22. No source, no archive.

## 1. Still on the shortest path?
No, and worse than at S22: 4 more sessions (S23-S26), still 0 G1 items formally passed, stages 2-7 still 0 sessions.
G1 count (6 items): passed 0; ready to pass with one command or one note: G1.2 (truth topics 800 Hz, stamps, metrics read
truth since S23, second keys AGREE) ; failing on a gate-wording question: G1.1 (Q2: rule measures sim holes A-13) and
G1.6(a) (Q3: Commander 10 ms phase, 5-9 ms spread; (c) met, (d) in force, (b) data being produced in B26); not started or
mostly open: G1.3 (35/35 agree but most metrics have no second key), G1.4 (7 scripts without self-test as of S17,
nothing since), G1.5 (zero injectors; only the player's applied-time part exists).
Route check 22 said: (1) close A-15/A-16, park A-10/13/14 (DONE S23, good); (2) G1.6(a): build the scheduled switch
"only if <= 1 session, else restate (a)" (the player took S23-S26, 4 sessions, plus the A-17 detour S24-S25 and
take-off/land/attitude/pva row kinds beyond what (a) needed); (3) G1.3/G1.4 batch (0 sessions); (4) G1.5 minimum
injectors (0 sessions, only now reachable via player kinds); (5) freeze G1, start stage 2 in parallel (not done).
The 2-session anomaly cap was respected (A-17 parked at 2). The 1-session cap on item 2 was not, and the start of
stage 2 was not done. The player is real value (G1.5 applied time, anchored scenarios) but it was grown past need.

## 2. Which decision is the difficulty a consequence of?
D-SCHED (S23): chose to build the sim-time player rather than restate G1.6(a) ("rejected, weakens the test"). It
rested on D-G1.6 (no lockstep gz) and D-SIM-STEP. The player made the trigger exact (0 us) but Commander's loop phase
remained, so (a) as written is unreachable without lockstep: the decision bought the part of (a) that no verdict needs.
Amplifier: the rule "a gate change after its first test goes to the owner" turns every wording defect (Q2, Q3) into a
waiting state, and the agent filled the wait with simulator work instead of moving on. The owner is not blocking, so
the agent must proceed under the recommended option, marked provisional.

## 3. A fresh start on stage 1 would
- Write G1 as bounds: each item "pass, or bound written once in GATES" (A-10/13/14/17 are bounds, not anomalies).
- Define G1.6(a) from day 1 as "trigger applied time exact + response within one Commander period, logged", never as
  an across-run spread on a free-running gz; no lockstep, no 4 ms world first (D-SIM-STEP before any G1 pass cost S16-S21).
- Build the player first (it is the one sim-time mechanism for modes, setpoints and injections), then metrics with
  their second key and self-test in the same task (no later 7-script batch).
- Put stage 2 (CPU only) on from session 4 in parallel; budget stage 1 at ~12 sessions, not open-ended.

## 4. Next actions S27-S31 (max 5, one agent per session)
1. S27 (now): read B26, compute G1.6(b)/(c) with `g16_spread.py` and `second_key_player.py` (haiku second key on
   the spread). Write the G1 verdicts as PROVISIONAL under Q2-A and Q3-A (orchestrator note in GATES: "passes under
   the owner's recommended option; reopen if owner picks B or C"): G1.1 (logger completeness <= 0.1 %, sim holes
   <= 0.05 % steps and <= 10 ms, already measured), G1.2 pass, G1.6(a1)/(a2)/(c)/(d) pass, (b) = recorded spreads as
   the noise floor every later verdict must exceed. Stop waiting on Q2/Q3.
2. S28: G1.3/G1.4 in one sonnet task + haiku keys, scoped to gate-bearing metrics only (rate/attitude tracking on
   truth, effort at fixed bandwidth, hover deviation, step settling, trajectory error, spectral detector input):
   second key for each, self-test for each used script. Acceptable with a bound: scripts/metrics not read by any
   G2-G5 verdict are tagged "single key, not gate-bearing" and not ported.
3. S29: G1.5 minimum injectors through player kinds (mass/payload step, param step, force/torque disturbance): frame,
   sign, magnitude 2 %, applied time. Accepted with a stated bound and moved past: sag ramp, delayed GNSS,
   vibration, battery model, noise profiles, rotor-inertia web check, seeded drops, variants; list them in GATES G1.5
   as "built when the gate that consumes them runs" (note as owner Q4, not blocking). Also accept: --sched only for
   hover/step_roll/lemniscate; step_pitch/yaw, circle, land row, pva propagation, row-1 1.5 cm = unverified list.
4. S30: freeze G1 (final) with the parked-anomaly list as evidence limits (A-10, A-13, A-14, A-17, A-7 bound),
   commit, G1 verdict. Same session: kick off stage 2 (linear margins, CPU only, reads A-1 blend question).
5. S31: first stage-3 task (inner-loop code needing only G1.1/1.2/1.6 bounds and the rate/effort keys), and the
   stage 2 follow-up as host/CPU work in parallel. If S28-S29 run over, cut them to the minimum above; do not extend.
Do not: open a new anomaly or read logs for a cause unless it changes a verdict; no lockstep; no player kinds beyond
G1.5 needs; no outer-loop design before G1 is final.
