# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Session 4 (launch 20261115-175831): requirements reviewed, candidates r1 drafted, fact 1 closed.
- Session 5: review r1 DONE (T6): A recommended w/ 5 conditions, B deferred, C rejected.
- Session 6 (launch 20261115-181651): route check 05 DONE (`design/route_check_05.md`): balance wrong, too much
  spend on paper design, no gate tested. Acted on: candidates_r2 written by me (cheap); round 2 = one NARROW
  fable review (deltas only, <=15 calls) because MISSION requires >=2 rounds; then owner question; from S7 on,
  stage-1 bench/G1 work has priority over design.
- Session 7 (launch 20261115-182252, cap $1.6): review r2 NOT launched (fable ~$1.2-2.5 > half the cap, rule 21);
  deferred to the first session with cap >= $3. Did port 1a step 1 instead (T9, metrics.py trajectory fix).
- Session 9 (launch 20261115-204121, cap $1.89): T12 DONE: runner ported to `bench/run_scenario.py` with `sends.csv`
  (intended sim time of every setpoint/param/sag send), metrics window accepts nav_state 23 (`design/port_1a_runner.md`).
  Runner got `--model` (default quad5in). T13 pre-test: quad5in PID hover flies (airframe 4040), sends.csv OK
  (1600 send_pos, monotonic), metrics.py runs (`design/pretest_runner_s9.md`). No unit case for nav_state 23 (lesson 20).
- Session 8 (launch 20261115-182725, cap $1.06): T10 closed items 4b/4c (`design/port_1a_timebase_check.md`):
  no t0 correction (setpoint lag +2..4 ms), no origin correction (estimator bias 2-5 cm reported separately). T11 second key CONFIRMED the
  trajectory metric (`results/second_key_traj.md`, 3 digits on 3 runs). Item 4 metrics.py trajectory part closed.
- Session 10 (launch 20261115-204950, cap $1.44): T14 DONE: `bench/applied_timing.py` + self-test (passes, I re-ran it),
  note `design/port_1a_applied_timing.md`. On the s9 hover it measures log decimation only: trajectory_setpoint logged
  at 5 Hz and constant payload; params sent pre-log. NOT a jitter bound yet; no second key yet.
  T15 DONE: runner writes fs/etc/logging/logger_topics.txt (21 topics, interval 0, instance 0); hover pre-test
  `results/pretest_logging_s10`: 250 Hz IMU/actuator/rates, 125 Hz local pos, 50 Hz trajectory_setpoint and ground
  truth; 27 MB/65 s; metrics + applied_timing run (`design/logging_profile.md`). Closes the open problem below.
  applied_timing on s10: send_pos p50=p95=4 ms (1 step), 0 unmatched (A-8 closed, not reproduced); one changed-payload
  row at 1032 ms = pre-offboard flight-task output, not latency. Payload constant, so still no jitter bound.
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written (not tested).
- Blocker: none. No owner question open.
- Outer-loop architecture study (MISSION section) runs in parallel with stages 1-3: not started.

## Next actions (in order)
1. Reference airframe model DONE (session 3): `design/ref_airframe_model.md`, flies with stock PID (hover u 0.1367,
   eRPM 998.7 rad/s, steps settle). Its open items 1-4 (reaction-torque scaling test, gyro log rate, run1 esc_rpm 0,
   run-to-run spread) are folded into the simulator work of item 4.
2. Outer-loop study: r2 DONE S6 (`design/outer_loop_candidates_r2.md`: A amended A1-A9 closing F1-F17,
   requirement amendments R1a-R52, 3 open questions). NEXT (S7 start, ~$1.2): review round 2, fable, narrow brief:
   candidates_r2 vs review_r1 findings + the 3 open questions + source; output `design/outer_loop_review_r2.md`.
   If no BLOCKING: fold R1a-R52 into requirements, write owner question (one-page summary) in QUESTIONS.md, do
   NOT block (continue stage 1). Module rename decision (A1: rewrite mc_indi_pos_control in place) goes to
   DECISIONS.md with the owner answer.
3. Write GATES.md for G1 before its first test (draft exists).
4. Port plan DONE S6 (`design/bench_port_plan.md`, headers only, UNVERIFIED bodies). Port 1a first (sonnet,
   one script family per agent, ~$0.8 each: metrics.py fix M:51 + self-test, then run_scenario.py sim-time fixes).
   S7: metrics.py trajectory fix DONE (T9, `design/port_1a_metrics.md`, self-test passes, I re-ran it). NOT yet
   usable for a verdict: needs (a) second key (sonnet, independent re-implementation of the analytic trajectory error
   from raw ULog, compare on 3 archive set-O runs, ~$0.5), (b) groundtruth origin offset vs estimator hold_pos (3 cm
   seen, review used mean-offset removal), (c) lag-scan check. (a), (b), (c) DONE S8 (T10, T11). Remaining: window rule
   must accept nav_state 23 (external INDI mode), not only 14. Runner port DONE S9 (T12). NEXT: (i) applied_timing.py DONE S10 (T14); its blockers: logging DONE S10 (T15); NEXT session: a moving-payload
   scenario (steps) and a mid-flight param send; 8 unmatched send_pos rows after 68.3 s unexplained (ANOMALIES); (ii) pre-test flight DONE S9; (iii) two identical-seed flights -> jitter bound for G1; (iv) sag as sim-time ramp in gz bridge
   (simulator hook, two keys).
   Then run_scenario.py sim-time fixes (sim_review.md:14,19). Port bench runner/metrics into `indi_flight/bench/` with the review fixes (5 Hz held reference, decimated effort,
   ground-truth stamp, sim-time injections); self-test + second key per script. Errata re-score of set-O/T5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia check, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism). Source web re-check of J_rotor (ASSUMED) still pending.

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| - | none | | | |

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

## Agent ledger (stage 1)
| session | id | model | task | outcome |
|---|---|---|---|---|
| 1 | T1 | sonnet | sourced airframe data | done, 42 calls, ~$1.0 (above 30-call brief) |
| 1 | T2 | sonnet | second key, arithmetic/SDF | done, 14 calls, ~$0.8, 10 WRONG items |
| 2 | T3 | sonnet | gz model + PID check | done (verified and committed in session 3) |
| 2 | T4 | sonnet | outer-loop requirements | cut by cap, nothing written |
| 3 | T4 | sonnet | outer-loop requirements, relaunch | done, 31 calls, ~$0.75, 36 items, 305 lines |
| 4 | T5 | sonnet | requirements review | done, 16 calls, ~$0.5, 15 new items (4 blocking) |
| 5 | T6 | fable | outer-loop review r1 | done, 13 calls, ~$2.5 (2x estimate) |
| 6 | T7 | sonnet | route check 05 | done, 7 calls, ~$0.3 |
| 6 | T8 | haiku | bench inventory + defect map | done, 7 calls, ~$0.15, design/bench_port_plan.md |
| 7 | T9 | sonnet | metrics.py port, M:51 fix, self-test | done, 13 calls, ~$0.47 |
| 8 | T10 | haiku | time-base + origin check | done, 10 calls, ~$0.06, re-run by me |
| 8 | T11 | haiku | second key, trajectory error | done, 5 calls, ~$0.07, matches metrics.py |
| 9 | T12 | sonnet | runner port + sends.csv | done, 12 calls, ~$0.37, compile + metrics tests pass |
| 9 | T13 | haiku | pre-test flight of runner | done, 12 calls, ~$0.1, found x500 hard-code (fixed), then flew |
| 10 | T14 | sonnet | applied_timing.py + self-test | done, 6 calls, ~$0.34 |
| 10 | T15 | haiku | logger topics file + pre-test flight | done, 27 calls, ~$0.1, 21 min wall (one rerun) |

## Lessons proposed
- Haiku handles a well-specified log check (10 calls) for ~$0.06: use it for every bounded log/metric check.
- At a $1.6 cap: one sonnet agent of ~15 calls (~$0.5) plus state and commit; no fable work.
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- A fable review of ~1 KLOC of design + source costs ~$2.5: give it a whole session.
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
