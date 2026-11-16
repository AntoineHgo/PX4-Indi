# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written; G1.6 first tested S14 ((a) not met, see next actions).
- Blocker: none. Q2, Q3 open (G1.1 gap rule, G1.6a wording), not blocking. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- Session 15 (launch 20261115-230225, cap $3): flatness_r2 written; window anchored (T28, T29 2nd key);
  D-SIM-STEP decided (1.25 ms world, IMU 800 Hz), implementation next session.
- Session 18 (launch 20261115-233746, cap $1.62): A-12 CLOSED (T36 fix dbb1a62e29, T37 second key).
- Session 16 (launch 20261115-231016, cap $3): D-SIM-STEP implemented (T31, commit 72598e3159) and pre-tested
  (`results/pretest_simstep_s16/README.md`): 1.25 ms step, IMU 800 Hz, RATEMAX 800/400 applied, PID flies, speed 4
  ~38 s wall/run. Logger fixed: `-p actuator_motors -b 200` logs all controller-rate topics at 800 Hz, 0 dropouts. A-10.

## Next actions (in order)
000000000000000000. S28 (launch 20261116-040120, cap $3): A-14 ROOT CAUSE found from source + logs (D-A14): gz baro has
   no reference_altitude (sea level) vs world 488 m; SENS_BAR_AUTOCAL steps baro ~488 m on the ground after EKF2
   started; baro bias still converging at arm. Fix staged (`sim/staged/quad5in_base_model_a14.sdf`), installed by
   `bench/a14_close.sh` AFTER B26 speed 1 (detached, then pretest + 15 hovers speed 4 -> `results/a14_close_s28/`).
   Check script `bench/a14_close_check.py` (self-test: reproduces old speed4 r2 2.28 m). B26 speed1 traj r1 started
   before the revert but logged 101332 Pa (old model): B26 speed 1 is clean.
   T59 DONE (`design/g13_g14_matrix_s28.md`): 3 analytic self-tests added (rate, attitude, step), break-checked 8x.
   Second key AGREE on 3/7 gate-bearing rows (rate, effort on 1 log only; trajectory); none on attitude, hover
   position, step. DEFECTS (not fixed): rate/attitude tracking use the EKF estimate, not truth (lesson 3);
   effort is an unfiltered first difference, not a fixed bandwidth; no spectral detector exists yet.
   S29 NEXT: (0) fix those two metric defects (sonnet, then haiku second keys over >= 5 logs, G1.3 sample set).
   (1) B28 PRETEST_FAIL (`results/a14_close_s28/pretest_check.md`, batch stopped by design, model restored):
   raw baro still 101324 Pa, bias0 -488, baro_fault -> reference_altitude had NO effect. First check (haiku, cheap):
   is quad5in loaded from `indi_flight/sim/models` at run time or from a copy (image/build dir), and does gz-sensors
   read <air_pressure><reference_altitude>? (S28: run_scenario.py:173 sets PX4_GZ_MODELS to the repo models dir, so
   path is likely fine; suspect gz-sensors version in the image ignores it -> read its AirPressureSensor.cc.) Then retry, or D-A14 alternative (1) EKF2_BARO_CTRL 0. (2) B26 speed 1 analysis
   (as speed 4: `second_key_player.py`, `G16_ROOT=... g16_spread.py`), haiku second key; G1.6 set must be re-flown
   with the fixed baro anyway (A-14 touched hover r2/traj r1). (3) route check 27 items 2-5 (G1.3/G1.4 keys,
   minimum G1.5, freeze G1 by S30, stage 2).
0000000000000000000. S29 (launch 20261116-041436, cap $2.34): T60 DONE (`design/a14_refalt_s29.md`): gz-sensors 8 never
   reads reference_altitude -> SDF fix impossible; D-A14 now = gz_bridge re-expresses pressure at world elevation
   (sim-only, two keys), fallback EKF2_BARO_CTRL 0. T61 DONE (`design/metric_fix_s29.md`, D-EFFORT-BW): rate/attitude
   tracking on sim_ground_truth (estimate kept as *_estimate), effort at 400 Hz grid/50 Hz LP; tests ALL PASS (re-run
   by me), 7 breaks checked. New A-19 (constant truth-EKF yaw offset ~0.4-0.65 deg).
   S30 NEXT: (a) gz_bridge baro fix (sonnet) + haiku second key, then a14_close pretest; (b) haiku second keys of the
   new truth/effort metrics over >= 5 logs (G1.3 set) and A-19 closing test; (c) step_metrics still on the estimate;
   (d) route check 30 due (sonnet), freeze G1, start stage 2.
1-4. Stage-1 items still pending from the old list (rest done, history in JOURNAL): errata re-score of archived set-O/T5;
   window rule must accept nav_state 23; sag as sim-time ramp in gz bridge (two keys); run_scenario sim-time fixes
   (`sim_review.md`:14,19) now folded into the player; outer-loop A-requirements folded at stage 5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia check, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism). Source web re-check of J_rotor (ASSUMED) still pending.

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| B26 | G1.6 set --sched --sched-anchor, 3 scen x 5, speed 4 (done, analysed S27) then 1 (DONE S28, not analysed) | host bash (detached) | `results/g16_sched_set_s26/speed{4,1}/status.txt` | `setsid nohup indi_flight/bench/g16_sched_set.sh` (delete partial speed dir first) |

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
| 18 | T37 | haiku | second key A-12 (truth rate, EKF vs truth) | done, 6 calls, ~$0.06, agrees |
| 18 | T36 | sonnet | A-12 fix (dynamic_pose/info) | done, 18 calls, ~$0.43, commit dbb1a62e29 |
| 17 | T35 | sonnet | gate_g1.sh + g1_checks.py | done, 14 calls, ~$0.52 |
| 19 | T38 | host bash | pre-test hover s4, truth topics | done, 1/1 flew, 40 s wall, $0 |
| 20 | T39 | sonnet | g1.1 rates + check_truth path | done, 17 calls, ~$0.35 |
| 20 | T40 | haiku | A-14 two reruns + a14_check.py | done, 13 calls, ~$0.1 |
| 20 | T41 | haiku | A-15 gap coincidence | done, 6 calls, ~$0.06 (conclusion revised by T42) |
| 20 | T42 | sonnet | A-15 cause, read-only | done, 13 calls, ~$0.45 |
| 21 | T43 | sonnet | sim_ground_truth topic + pretest | done, 11 calls, ~$0.35 |
| 21 | - | host bash | A-14 six hovers | done, 6/6 flew, ~4 min wall, $0 |
| 22 | T44 | sonnet | route check 22 | done, 6 calls, ~$0.15 |
| 22 | T45 | haiku | A-16 closing test | done, 6 calls, ~$0.05 |
| 23 | T46 | sonnet | metrics on sim_ground_truth + timestamp_sample | done, 16 calls, ~$0.45, commit a6820c2e60 |
| 23 | T48 | haiku | second key T46 | done, 12 calls, ~$0.1, AGREE on same window (<0.03 %) |
| 23 | T47 | haiku | D-SCHED interface map | done, 12 calls, ~$0.1, `design/sched_interfaces_s23.md` (4 UNVERIFIED items) |

| 24 | T49 | sonnet | sim-time scenario player + pretest | done, 29 calls, ~$0.75 |
| 24 | T51 | haiku | A-17 Commander phase | done, 5 calls, ~$0.06, confirmed 4/5 |
| 24 | T50 | haiku | second key player instants | done, 8 calls, ~$0.06, AGREE |
| 25 | T52 | sonnet | gz paused start + 5 hovers | done, 18 calls, ~$0.45, hypothesis rejected |
| 25 | T53 | sonnet | player sp_hold/anchor/takeoff/land + pretest | done, 15 calls, ~$0.45, takeoff/land unflown |
| 25 | T54 | haiku | second key T53 | done, 3 calls, ~$0.05, AGREE (row-1 check artefact open) |
| 26 | T55 | sonnet | player att/pva rows + runner + 2 pretests | done, 21 calls, ~$1.0 (2x estimate, 11 min) |
| 26 | T56 | haiku | second key T55 | done, 11 calls, ~$0.2, AGREE 4/4 |
| 27 | T57 | sonnet | route check 27 | done, 10 calls, ~$0.25 |
| 27 | T58 | sonnet | A-14 mechanism from logs | done, 5 calls, ~$0.3, numbers re-read by me |
| 28 | B28 | host bash | A-14 closing test (16 hovers) | pretest FAIL (no effect on baro), stopped, $0 |
| 28 | T59 | sonnet | G1.3/G1.4 matrix + missing self-tests (route check 27 item 2) | done, 16 calls, ~$0.45; tests re-run by me (ALL PASS, metrics.py diff empty) |
| 29 | T60 | haiku | A-14 reference_altitude check | done, 11 calls, ~$0.25, SDF fix impossible |
| 29 | T61 | sonnet | metric defects 1+2 | done, 16 calls, ~$0.6, tests re-run by me |

## Lessons proposed
- A shared sim model is live for every running batch: stage a model change and install it after the batch ends (S28 nearly mixed two baro models into B26).
- A parked anomaly bound from a correlation (A-14: 0/9 vs 3/6 runs, p=0.044, "logger -f") was wrong; park on a mechanism, not on a pair test (S27).
- A sonnet implement+build+2-flight task costs ~$1.0 (21 calls): at a $3 cap it is the session's one big task (S26).
- Read the sleep/wake rule of a loop before building a timing fix around it: S25 spent a session on a start-up
  race while Commander's skip-sleep-on-command line (visible in 20 lines of source) already ruled it out.
- A pre-test check worded "within N periods of the command" measured Commander's fixed latency; state the
  determinism check as across-run spread, and latency separately (S24).
- Give each anomaly at most 2 sessions, then park it with a written bound and reopen trigger (route check 22).
- Haiku handles a well-specified log check (10 calls) for ~$0.06: use it for every bounded log/metric check.
- At a $1.6 cap: one sonnet agent of ~15 calls (~$0.5) plus state and commit; no fable work.
- At a $3 cap launch one agent per session (session 2: two sonnet agents ~$1.4 in 30 min, both cut).
- A fable review of ~1 KLOC of design + source costs ~$2.5: give it a whole session.
- Opus with a narrow brief (one interface, <=12 calls, early skeleton write) reviews ~200 lines of design + source
  for ~$0.6: use opus, not fable, for design review rounds.
- Web-research agents cost about 3x a code-read agent of the same call count; brief them at 20 calls.
- PX4 logger default timer (3.5 ms) silently decimates topics above 285 Hz; poll on the last topic of the control
  cycle (`-p actuator_motors`) and check logged rates (`bench/check_rates.py`) before any high-rate analysis (S16).
- At a ~$1 cap the launch context alone costs ~$0.3: do one host-bash flight + check, no agent (S19).
- Analysis scripts take an output path argument; never a fixed path into a committed result (S19).
- Anchor every analysis window on an event in the log, never on the runner's view of it: the 1 Hz HEARTBEAT view moved the window start by up to 0.95 s (S15).
- Give a second key the primary script's exact window (start, end, anchor); a different window produced a false 2.1 % DISAGREE (S23 T48).
