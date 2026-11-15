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
- Session 11 (launch 20261115-214208, cap $3): launched T16 review r2 (opus, narrow, <=12 calls) and T17 route
  check 10 (sonnet, DONE: `design/route_check_10.md`, on path but slow; next = determinism G1.6, final GATES G1,
  second keys, sim-time injection hook; r2 noted as against check-05 rule: accepted, it is the one narrow round
  MISSION requires, already planned S6). T16 review r2 DONE (`design/outer_loop_review_r2.md`): 1 BLOCKING (N1 acceleration-only axes lose drag damping
  under INDI: descend failsafe, blind land, Altitude xy), 2 MAJOR, 4 MINOR. I wrote `design/outer_loop_candidates_r3.md`
  (A10 per-axis-group open loop for acceleration-only setpoints, A11 thrust gap = decision 2, A12 minors).
  T18 determinism pre-study DONE (`design/determinism_s11.md`): A-7 reproduced, arm time spreads 2.2 s in sim time
  with the same seed, roll attitude RMS spread 37 %. run_scenario.py does not write metrics.json (agent ran metrics.py).
  Review r3 not launched (budget < 2x its cost). Untracked `results/pretest_logging_s10_try1/` = T15's failed first try (raw, keep untracked).
- Session 12 (launch 20261115-215107, cap $3): T19 DONE (runner arms at sim 20 s, hold 39 s, offboard 40 s,
  runs metrics.py; `design/runner_fixed_times_s12.md`, I read the diff). T20 review r3 DONE (`design/outer_loop_review_r3.md`):
  NO BLOCKING; 4 MAJOR (R3-1 per-group reset impossible, run lib on all axes and override open group; R3-2 lib
  rejects NaN pos/vel so z cannot keep INDI in blind/no-GPS states; R3-3 open->INDI entry step, needs decaying
  offset + dwell; R3-8 `||` start fallback contradicts F-1), 4 MINOR. R3-8 decided by F-1: no fallback, start
  failure refuses arming (to DECISIONS.md). Try 1 of 3 hovers failed: arm denied 20-25 s (height estimate not
  stable), climb > 8.8 s; constants moved to arm 30 s / offboard 52 s (committed 84b61e5c75). T21 Try 2 DONE (`design/determinism_s12.md`): 3 ok runs,
  arm 30.28-30.61 s (0.33 s spread, ack latency?), well-conditioned spreads down but still 10-25 % (roll RMS 11.6 %,
  rotation 17.7 %, max_dev_h 24.9 %, rms_3d 4.7 %). arm_late_s absent although arm > 30.1 s: check the flag.
- Session 13 (launch 20261115-220341, cap $3): arm/offboard 0.28-0.61 s "latency" = runner observes mode via
  1 Hz HEARTBEAT (same per-run offset on arm and offboard); arm_late_s correctly absent (tests send time). T22 checks
  it in the ULogs: DONE (`design/determinism_s13.md`): PX4 offboard at 52.024-52.032 s, re-aligned window leaves the
  spread (max_dev_h 24.9 %), gyro differs from +28 ms after arm: real SITL non-determinism, log needed from boot. Wrote `design/outer_loop_candidates_r4.md`
  (A13-A17 answer R3-1..R3-8, no interface change, no new round) and owner question Q1 (confirm A, not blocking).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written (not tested).
- Blocker: none. Q1 answered: A confirmed, owner asks to consider differential flatness -> `design/flatness_r1.md`
  (A18 jerk->omega_ff side channel); narrow review r5 (opus) of A18 is the last step before stage 5.
- Outer-loop architecture study: 3 review rounds + r4 deltas done; owner confirmation pending (Q1).

## Next actions (in order)
00. S14: (a) review r5 (opus, narrow, <=10 calls): `design/flatness_r1.md` vs arXiv 1809.04048 (source check of the
   table in section 1) + `src/modules/mc_indi_rate_control` ff entry point; output `design/outer_loop_review_r5.md`.
   (b) G1.6 run: 5 same-seed runs x (hover, one step, one trajectory) at speed 1 -> spreads vs thresholds (haiku).
   (c) G1.1-G1.5 commands (`bench/gate_g1.sh`), remaining second keys. Determinism cause found S13 (gz no lockstep).
0. S13: (a) determinism: spreads stay 10-25 % with windows aligned to 0.33 s: (i) why arm lands 0.28-0.61 s after
   30 s and why arm_late_s is missing; (ii) cause below the runner (gz/PX4 threading): bisect with speed factor
   and compare gz ground truth vs PX4 timestamps on r1..r3; then define the G1.6 tolerance in GATES.md.(b) DONE S13 (r4 + Q1).
   (c) final GATES.md G1 and remaining second keys.
0'. S12 (done/partly): (a) runner: arm and offboard at fixed sim times, and call metrics.py at the end (sonnet, ~12 calls, two keys:
   haiku re-checks sends.csv vs run.json); re-fly 3 same-seed hovers (haiku, as T18 brief); if spread persists, the
   cause is below the runner (gz/PX4 threading), bisect with speed factor. (b) outer-loop review r3, opus, narrow.
   (c) then final GATES.md G1 and remaining second keys (route check 10).
1. Reference airframe model DONE (session 3): `design/ref_airframe_model.md`, flies with stock PID (hover u 0.1367,
   eRPM 998.7 rad/s, steps settle). Its open items 1-4 (reaction-torque scaling test, gyro log rate, run1 esc_rpm 0,
   run-to-run spread) are folded into the simulator work of item 4.
2. Outer-loop study: r2 DONE S6 (`design/outer_loop_candidates_r2.md`: A amended A1-A9 closing F1-F17,
   requirement amendments R1a-R52, 3 open questions). NEXT (S7 start, ~$1.2): review round 2, fable, narrow brief:
   candidates_r2 vs review_r1 findings + the 3 open questions + source; output `design/outer_loop_review_r2.md`.
   r2 DONE S11 (1 BLOCKING). NEXT: round 3, opus, NARROW (A10-A12 of candidates_r3 vs review_r2 + source, <=8 calls,
   ~$0.6); if no BLOCKING, then the owner question below (not blocking).
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
| T25 | opus | S14: review r5 of A18 (flatness ff), narrow | design/outer_loop_review_r5.md | relaunch same brief if file lacks Verdict |
| T24 | haiku (agent ended S13; its batch survives as host bash) | S13: G1.6 pre-test (step_roll, traj_lemniscate on quad5in) then 5 same-seed runs x hover/step_roll/traj_lemniscate, speed 1 | results/det_g16/, design/g16_s13.md | batch script /tmp/claude-1001/-home-ahugo-Documents-Drotek-Codes-PX4-Indi/52d81939-c2c5-4141-b338-03f1bc8a732b/scratchpad/g16/batch.sh (status.txt, spread.py there); S14 watches it; if lost, re-run missing rN dirs only |

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
| 11 | T16 | opus | outer-loop review r2, narrow | done, 7 calls, ~$0.6 (opus ~1/4 of fable r1) |
| 11 | T17 | sonnet | route check 10 | done, 6 calls, ~$0.2 |
| 11 | T18 | haiku | determinism pre-study, 3 hovers | done, 12 calls, ~$0.05, 6 min wall |
| 12 | T19 | sonnet | runner fixed sim-time arm/offboard + metrics call | done, 9 calls, ~$0.4 |
| 12 | T20 | opus | outer-loop review r3, narrow | done, 8 calls, ~$1.0 |
| 12 | T21a | haiku | 3 hovers try 1 | stopped at run 1 (arm late), 3 calls, ~$0.03 |
| 12 | T21 | haiku | 3 hovers try 2 | done, 11 calls, ~$0.05, 6.5 min wall |

## Lessons proposed
- Haiku handles a well-specified log check (10 calls) for ~$0.06: use it for every bounded log/metric check.
- At a $1.6 cap: one sonnet agent of ~15 calls (~$0.5) plus state and commit; no fable work.
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- A fable review of ~1 KLOC of design + source costs ~$2.5: give it a whole session.
- Opus with a narrow brief (one interface, <=12 calls, early skeleton write) reviews ~200 lines of design + source
  for ~$0.6: use opus, not fable, for design review rounds.
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
