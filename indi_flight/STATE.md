# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written; G1.6 first tested S14 ((a) not met, see next actions).
- Blocker: none. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- Session 15 (launch 20261115-230225, cap $3): flatness_r2 written; window anchored (T28, T29 2nd key);
  D-SIM-STEP decided (1.25 ms world, IMU 800 Hz), implementation next session.
- Session 16 (launch 20261115-231016, cap $3): D-SIM-STEP implemented (T31, commit 72598e3159) and pre-tested
  (`results/pretest_simstep_s16/README.md`): 1.25 ms step, IMU 800 Hz, RATEMAX 800/400 applied, PID flies, speed 4
  ~38 s wall/run. Logger fixed: `-p actuator_motors -b 200` logs all controller-rate topics at 800 Hz, 0 dropouts. A-10.

## Next actions (in order)
0000000. S17 (launch 20261115-233009, cap $2.16): A-11 CLOSED (`results/a11_effort_rate.md`, effort rate dependent,
   G4 at fixed bandwidth); G1.6 verdict in GATES.md ((a) NOT met, (c) met; remedy: lockstep gz or in-PX4 scheduled
   mode switch, decide before G3). T35 (sonnet) writing `bench/gate_g1.sh` G1.1/G1.3/G1.4/G1.6 + `design/gate_g1_cmd_s17.md`.
000000. NEXT (S17): (a) DONE S16: G1.6 repeat on 1.25 ms world 15/15 (`results/det_g16_w125/README.md`): tracking
   matches 4 ms world within spread; G1.6(a) NOT MET (7.5-11 ms vs 2.5 ms), cause (c) unchanged -> record in GATES.md
   G1.6 verdict. Effort doubled in manoeuvres: A-11 (haiku: recompute effort decimated to 285/250 Hz, close it).
   (b) A-10 partly explained S16 (`design/anomaly_a10_s16.md`); closing test: esc_status publish vs logged count.
   (c) G1.1-G1.5 commands (`bench/gate_g1.sh`), remaining second keys. Stage-3 item: cycle-count params
   (MC_INDI_DELAY, MC_INDI_ERPM_DLY, MC_INDI_DT_MAX) to time units. eRPM latency counts ESC output frames
   (= controller cycles; SIM_GZ_ERPM_LAT default 0 -> 1 frame), `design/sim_step_impl_s16.md`.
0000. G1.6 window anchor DONE S15 (T28 + my end fix, `design/window_anchor_s15.md`, commits 988c2ff59a, 593a8b4fad):
   start spread 4-16 ms, fixed duration; same-seed spreads unchanged (<30 %) -> spread is flight non-determinism
   (gz not lockstepped), G1.6(c) cause stated. Second key T29 AGREE 30/30 (`results/second_key_window_s15.md`).
   G1.6 verdict: (a) NOT met (16 ms vs 8 ms), (b) pending gate thresholds of G3/G5, (c) done, (d) = rule in force.
   Next G1 work: G1.1-G1.5 commands (`bench/gate_g1.sh`), remaining second keys; IMU 1 kHz (item above).
000. S15: A18 r5 verdict BLOCKING (`design/outer_loop_review_r5.md`): F1 yaw-rate double count (also live bug A-9),
   F2-F4 MAJOR (no stamp in vehicle_rates_setpoint, accumulation into held _rates_setpoint, frame desired vs
   estimated body). A18 stays OUT of base A; `design/flatness_r2.md` DONE S15 (F1-F9 accepted, A18 = review's minimal spec,
   optional stage-5 increment after base A, 3-part acceptance), no new review until stage 5 base A works. Stage 5 starts with base A only (Q1 confirmed).
00. S14: (a) review r5 (opus, narrow, <=10 calls): `design/flatness_r1.md` vs arXiv 1809.04048 (source check of the
   table in section 1) + `src/modules/mc_indi_rate_control` ff entry point; output `design/outer_loop_review_r5.md`.
   (b) G1.6 run: 5 same-seed runs x (hover, one step, one trajectory) at speed 1 -> spreads vs thresholds (haiku).
   (c) G1.1-G1.5 commands (`bench/gate_g1.sh`), remaining second keys. Determinism cause found S13 (gz no lockstep).
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
| T35 | gate_g1.sh items 1,3,4,6 | sonnet | `bench/gate_g1.sh`, `design/gate_g1_cmd_s17.md` | relaunch brief from the design file |

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
| 14 | T24 | host bash | G1.6 speed 1, 15 runs | done, 15/15 first attempt, 26 min wall, $0 |
| 14 | T26 | host bash | G1.6 speed 4, 15 runs | done, 15/15 first attempt, ~11 min wall, $0 |
| 14 | T27 | haiku | G1.6 ULog checks | done, 6 calls, ~$0.05 |
| 14 | T25 | opus | review r5 of A18 | done, 10 calls, ~$0.7, BLOCKING (yaw-rate double count) |
| 15 | T28 | sonnet | metrics window anchor + re-score 30 | done, 13 calls, ~$0.35 |
| 15 | T30 | sonnet | plan SITL IMU rate, read-only | done, 9 calls, ~$0.3 -> D-SIM-STEP |
| 15 | T29 | haiku | second key window bounds | done, 2 calls, ~$0.05, AGREE 30/30 (<1 ms) |
| 16 | T31 | sonnet | implement D-SIM-STEP | done, 11 calls, ~$0.45 |
| 16 | T32 | host bash | pre-test 5 flights (rates, logger poll) | done, 5/5 flew, ~5 min wall, $0 |
| 16 | T34 | host bash | G1.6 repeat, 1.25 ms world, 15 runs | done, 15/15 first attempt, ~10 min wall, $0 |
| 16 | T33 | haiku | A-10 esc_status stamps | done, 10 calls, ~$0.05, one wrong claim corrected by me |

## Lessons proposed
- Haiku handles a well-specified log check (10 calls) for ~$0.06: use it for every bounded log/metric check.
- At a $1.6 cap: one sonnet agent of ~15 calls (~$0.5) plus state and commit; no fable work.
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- A fable review of ~1 KLOC of design + source costs ~$2.5: give it a whole session.
- Opus with a narrow brief (one interface, <=12 calls, early skeleton write) reviews ~200 lines of design + source
  for ~$0.6: use opus, not fable, for design review rounds.
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
- PX4 logger default timer (3.5 ms) silently decimates topics above 285 Hz; poll on the last topic of the control
  cycle (`-p actuator_motors`) and check logged rates (`bench/check_rates.py`) before any high-rate analysis (S16).
- Anchor every analysis window on an event in the log, never on the runner's view of it: the 1 Hz HEARTBEAT view moved the window start by up to 0.95 s (S15).
