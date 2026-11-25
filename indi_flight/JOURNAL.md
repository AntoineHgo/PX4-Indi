# Journal (append-only, not read at launch)

- 2026-11-15 S1 (launch 20261115-164208): stage 0. Committed workspace and review (df144c0c4b). Wrote STATE, DECISIONS, ANOMALIES.
- 2026-11-15 S1: T1 reference-airframe data table (sonnet). D-1, D-2 recorded. GATES.md G1 draft. Session ended at budget.
- 2026-11-15 S2 (launch 20261115-170222): D-3 recorded. Launched T3 (gz model quad5in + SITL airframe + PID hover/step check, output design/ref_airframe_model.md) and T4 (outer-loop requirements from mc_pos_control source, output design/outer_loop_requirements.md), both sonnet.
- 2026-11-15 S3: reference airframe quad5in model + SITL airframe committed, flies with stock PID (design/ref_airframe_model.md).
- 2026-11-15 S3: outer-loop requirements R1-R36 written (design/outer_loop_requirements.md); review pending.
- 2026-11-15 S4: requirements review T5 (15 new items, 4 blocking); outer-loop candidates r1 (A preferred); local-position rate 125 Hz in SITL.
- 2026-11-15 S5: outer-loop review r1 (fable): A recommended with 5 conditions, B deferred, C rejected (F10).
- 2026-11-15 S6: route check 05 (balance too design-heavy, bench/G1 next); outer-loop candidates r2 (A amended for F1-F17).
- 2026-11-15 S7: metrics.py ported with analytic trajectory reference (T9), self-test passes; review r2 deferred to a >= $3 session.
- 2026-11-15 S8: T10 metrics time base verified (no t0/origin correction), timebase_check.py added.
- 2026-11-15 S8: T11 second key confirms metrics.py trajectory error (3 digits, 3 runs).
- 2026-11-15 S11: route check 10; outer-loop review r2 (1 blocking, N1) and candidates r3; determinism pre-study reproduces A-7 (arm time spread 2.2 s sim).
- 2026-11-15 S14: moved finished S12/S13 next-action blocks out of STATE: 0'. S12 (done/partly): (a) runner: arm and offboard at fixed sim times, and call metrics.py at the end (sonnet, ~12 calls, two keys: haiku re-checks sends.csv vs run.json); re-fly 3 same-seed hovers (haiku, as T18 brief); if spread persists, the cause is below the runner (gz/PX4 threading), bisect with speed factor. (b) outer-loop review r3, opus, narrow. (c) then final GATES.md G1 and remaining second keys (route check 10). 0. S13: (a) determinism: spreads stay 10-25 % with windows aligned to 0.33 s: (i) why arm lands 0.28-0.61 s after 30 s and why arm_late_s is missing; (ii) cause below the runner (gz/PX4 threading): bisect with speed factor and compare gz ground truth vs PX4 timestamps on r1..r3; then define the G1.6 tolerance in GATES.md.(b) DONE S13 (r4 + Q1). (c) final GATES.md G1 and remaining second keys.

## Status history S4-S13 moved from STATE.md in S15
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

- 2026-11-15 S16: Q1 (outer-loop architecture) closed: owner confirmed A; flatness studied as A18, optional stage-5 increment after base A (`design/flatness_r2.md`).
- 2026-11-15 S17: A-11 closed (effort rate dependent), G1.6 verdict recorded, gate_g1.sh for G1.1/3/4/6, A-12/A-13 opened.
- S18: A-12 closed (dynamic_pose/info, truth 800 Hz at speed 4), second key T37 agrees.
- S19: T38 pre-test: attitude/rate truth 800 Hz confirmed; g1.1 FAIL only on esc_status (A-10) and local_position rate; A-14 opened (take-off EKF z residual 2.2 m).
- 2026-11-16 S20: g1.1 rates fixed (00591b4e10); A-14 intermittent take-off EKF z offset; A-15 truth stream misses ~13 % of sim steps (gz_bridge).
- 2026-11-16 S20: A-15 cause = logger overwrite of queue-1 topics (confirmed by log-poll flight, 0c94faa5ba); T41 'not logger' withdrawn: logger dropouts != logger_status.message_gaps. Lesson candidate: check message_gaps before blaming a publisher.
- S21: A-15 fix sim_ground_truth (queue 16) built, pretested, committed; A-16 opened; A-14 6 runs, EKF height 2.26 m high on ground in 1/6.
- S21 moved from STATE (S15/S17 next actions, done): 0000000. S17 (launch 20261115-233009, cap $2.16): A-11 CLOSED (`results/a11_effort_rate.md`, effort rate dependent, G4 at fixed bandwidth); G1.6 verdict in GATES.md ((a) NOT met, (c) met; remedy: lockstep gz or in-PX4 scheduled mode switch, decide before G3). T35 DONE: `bench/gate_g1.sh g1.1|g1.3|g1.4|g1.6` (`design/gate_g1_cmd_s17.md`): g1.1 FAIL (A-12 groundtruth 14.8 Hz vs 50, A-13 gyro gaps, esc_status A-10), g1.3 35/35 agree but most metrics lack a second key, g1.4 tests pass, 7 scripts lack self-tests, g1.6(a) FAIL as recorded. A-12 cause found S17: truth = gz world pose topic at ~60 Hz 
- S22 moved from STATE (S14/S15/S19 next actions, done): 000000000. S19 (launch 20261115-234854, cap $1.08): T38 DONE (`results/a12_fix_s18/pretest_truth_topics/README.md`): attitude/rate/position truth 800 Hz confirmed; g1.1 FAIL only esc_status (A-10) + local_position 88.9 Hz; A-14 opened. S20 NEXT: (1) small fixes (sonnet or haiku, one agent): `g1_checks.py` add attitude/angular-velocity truth rows; `check_truth_s18.py` output path argument (it overwrites `results/a12_fix_s18/second_key.md`); (2) A-14 closing test (haiku); (3) then items (2)-(5) of the S19 list below. Launch pattern: `bench/pretest_simstep_s16.sh` docker line. 00000000. S19 NEXT: (1) pre-test 1 flight at speed 4 (T38, NOT run S18: on host run_scenario.py fails, WORLDS_DIR -> ../../indi_flight/sim/worlds; launch it the way T32/T36 did, inside Docker, see `results/pretest_simstep_s16/README.md` and `design/a12_fix_s18.md`; out dir `results/a12_fix_s18/pretest_truth_topics`): confirm attitude/angular-velocity truth now logged at 800 Hz (added to LOG_TOPICS S18) and g1.1 truth rows pass; (2) second keys for rate/attitude/hover/steps metrics (sonnet, one family per session); (3) self-tests for the 7 scripts (g1.4); (4) A-13 gyro gaps, A-10; (5) decide gz lockstep vs in-PX4 scheduled mode switch (G1.6a). vehicle_local_position 88.9 vs 125 Hz still open (g1.1). 000. S15: A18 r5 verdict BLOCKING (`design/outer_loop_review_r5.md`): F1 yaw-rate double count (also live bug A-9), F2-F4 MAJOR (no stamp in vehicle_rates_setpoint, accumulation into held _rates_setpoint, frame desired vs estimated body). A18 stays OUT of base A; `design/flatness_r2.md` DONE S15 (F1-F9 accepted, A18 = review's minimal spec, optional stage-5 increment after base A, 3-part acceptance), no new review until stage 5 base A works. Stage 5 starts with base A only (Q1 confirmed). 00. S14: (a) review r5 (opus, narrow, <=10 calls): `design/flatness_r1.md` vs arXiv 1809.04048 (source check of the table in section 1) + `src/modules/mc_indi_rate_control` ff entry point; output `design/outer_loop_review_r5.md`. (b) G1.6 run: 5 same-seed runs x (hover, one step, one trajectory) at speed 1 -> spreads vs thresholds (haiku). (c) G1.1-G1.5 commands (`bench/gate_g1.sh`), remaining second keys. Determinism cause found S13 (gz no lockstep).
- 2026-11-16 S22: route check 22 (off path, park anomalies); A-14 parked, runner logs from boot by default; A-16 closed (late-publish pairing).
- S24 moved from STATE (S20-S22 next actions and stage-1 items 1-4, done): 000000000000. S22 (launch 20261116-020843, cap $1.35): route checks 15/20 were missed -> T44 route check 22 (sonnet, `design/route_check_22.md`); T45 A-16 closing test (haiku, `results/a16_s22/README.md`). A-14: the two runner paths differ ONLY by logger `-f` (run_scenario.py:594). DONE: route check 22 (off path: park, go to G1.6a/G1.5/keys); A-14 PARKED with bound, runner default now `--log-from-start` (fdf28977ac); A-16 CLOSED (late-publish pairing, use timestamp_sample; esc_status deficit -> A-10). S23 NEXT = route check 22 items: (1) park A-10/A-13 with bounds, check metrics use timestamp_sample; (2) decide G1.6(a) lockstep vs in-PX4 scheduled switch, re-fly 5 runs; (3) second keys + self-tests; (4) G1.5 injectors (payload, param step); (5) G1 verdict. Stage 2 linear models can start in parallel (no sim needed). 00000000000. S21 (launch 20261116-015246, cap $1.8): A-15 fix decided: uORB queue depth comes only from the .msg (no runtime queue API), and raising it on VehicleAngularVelocity/VehicleAttitude would change the stock control topics. So: new sim-only queued topic `sim_ground_truth` (queue 16) published by gz_bridge in the same pose callback as the *_groundtruth topics, logged, read by the analysis. T43 (sonnet) implements + 1 speed-4 pretest, writes `results/a15_s21/README.md`. DONE: 56578/56586 samples, gaps = gyro gaps, values equal (commits pushed). A-16 opened (actuator_motors 777 zero-dt pairs). A-14: 6 flights (`results/a14_s21/`), 1 reproduced; EKF height itself 2.26 m high on ground. S22 NEXT: (1) g1.1 rows + metrics.py read `sim_ground_truth` (sonnet, plus a haiku second key); (2) A-14: 0/9 boot-logged vs 3/6 not (p=0.044): sonnet reads run_scenario.py paths with/without `--log-from-start`, then a pair test changing only the suspected step; (3) A-16 closing test (haiku); (4) S19 items (2)-(5). 0000000000. S20 (launch 20261116-014126, cap $2.61) DONE: T39 g1.1 declared rates fixed (truth at controller rate, EKF 88 Hz = 800/9 explained, GATES.md log), check_truth output path; T40 A-14 intermittent, not a reset/baro, pre-arm unseen; T41 A-15 truth stream misses ~13 % of sim steps at speed 4 (gz_bridge pose, not logger), controller topics only jitter. S21 NEXT: (1) A-15 cause (sonnet, read-only ~12 calls): gz_bridge dynamic_pose/info subscription vs IMU path, transport queue/pacing at speed 4, propose fix (truth from the same step callback as IMU?); one speed-1 flight to compare. T42 DONE (`design/a15_cause_s20.md`): cause likely LOGGER overwrite (message_gaps 24553 = sum of gaps), not gz; Logger cause CONFIRMED by flight (`results/a15_s20/logpoll_truth/`). S21 (1): fix so truth AND controller topics log every sample (sonnet: F2 queue 8 on truth advertise in gz_bridge, check logger drains queues; A-10 esc_status too?), re-run g1.1. (2) A-14 test: 3 runs logging from boot (SDLOG_MODE 1), EKF z vs truth pre-arm (haiku). (3) S19 items (2)-(5) below. 1. Reference airframe model DONE (session 3): `design/ref_airframe_model.md`, flies with stock PID (hover u 0.1367, eRPM 998.7 rad/s, steps settle). Its open items 1-4 (reaction-torque scaling test, gyro log rate, run1 esc_rpm 0, run-to-run spread) are folded into the simulator work of item 4. 2. Outer-loop study: r2 DONE S6 (`design/outer_loop_candidates_r2.md`: A amended A1-A9 closing F1-F17, requirement amendments R1a-R52, 3 open questions). NEXT (S7 start, ~$1.2): review round 2, fable, narrow brief: candidates_r2 vs review_r1 findings + the 3 open questions + source; output `design/outer_loop_review_r2.md`. r2 DONE S11 (1 BLOCKING). NEXT: round 3, opus, NARROW (A10-A12 of candidates_r3 vs review_r2 + source, <=8 calls, ~$0.6); if no BLOCKING, then the owner question below (not blocking). If no BLOCKING: fold R1a-R52 into requirements, write owner question (one-page summary) in QUESTIONS.md, do NOT block (continue stage 1). Module rename decision (A1: rewrite mc_indi_pos_control in place) goes to DECISIONS.md with the owner answer. 3. Write GATES.md for G1 before its first test (draft exists). 4. Port plan DONE S6 (`design/bench_port_plan.md`, headers only, UNVERIFIED bodies). Port 1a first (sonnet, one script family per agent, ~$0.8 each: metrics.py fix M:51 + self-test, then run_scenario.py sim-time fixes). S7: metrics.py trajectory fix DONE (T9, `design/port_1a_metrics.md`, self-test passes, I re-ran it). NOT yet usable for a verdict: needs (a) second key (sonnet, independent re-implementation of the analytic trajectory error from raw ULog, compare on 3 archive set-O runs, ~$0.5), (b) groundtruth origin offset vs estimator hold_pos (3 cm seen, review used mean-offset removal), (c) lag-scan check. (a), (b), (c) DONE S8 (T10, T11). Remaining: window rule must accept nav_state 23 (external INDI mode), not only 14. Runner port DONE S9 (T12). NEXT: (i) applied_timing.py DONE S10 (T14); its blockers: logging DONE S10 (T15); NEXT session: a moving-payload scenario (steps) and a mid-flight param send; 8 unmatched send_pos rows after 68.3 s unexplained (ANOMALIES); (ii) pre-test flight DONE S9; (iii) two identical-seed flights -> jitter bound for G1; (iv) sag as sim-time ramp in gz bridge (simulator hook, two keys). Then run_scenario.py sim-time fixes (sim_review.md:14,19). Port bench runner/metrics into `indi_flight/bench/` with the review fixes (5 Hz held reference, decimated effort, ground-truth stamp, sim-time injections); self-test + second key per script. Errata re-score of set-O/T5.

- 2026-11-16 S23/S24 next-action entries moved from STATE (S26):
  0000000000000. S23 (launch 20261116-024209, cap $3): T46 (sonnet) truth/timestamp_sample in metrics; DONE: A-10/A-13 PARKED with bounds; D-SCHED decided (sim-time scenario player, sim-only module). T46 DONE (a6820c2e60, `design/t46_truth_metrics_s23.md`): metrics on sim_ground_truth + timestamp_sample, hover re-score <1 %. Open from T46: (i) g1.1 still FAILS on max gap (5.0-6.3 ms vs 3.75 ms) for gyro, ang vel, motors, torque sp, esc, truth: the source (sensor_gyro) has the holes (A-13 parked), so the gap rule tests the sim, not the logger -> either fix the sim step holes or ask the owner to amend g1.1 to a bound (gate change after first test = owner question); decide in S24 after looking at the 6.3 ms gaps; (ii) rate/attitude tracking still scored vs estimator, G1.2 wants truth: add truth-based rate/attitude tracking (sonnet, with player work or after). T48 second key AGREE (`results/second_key_t46_s23/README.md`). S24 NEXT: sonnet implements the player (arm, mode, offboard setpoints first) + runner writer + 1 pretest; S25 second key + re-fly 5-run G1.6 set.
  00000000000000. S24 (launch 20261116-025001, cap $3): T49 DONE (b2dab14759 module, 1fdd07bd2f runner, 9b0e66d0e5 results,
     `design/t49_player_s24.md`): player arms/switches/streams in sim time; 2 hovers: applied-sched 0 us, arm and offboard
     instants identical (spread 0 us vs 7.5-11 ms before). T50 second key AGREE (`results/player_s24/second_key/`).
     Commander adds a fixed 6.25 ms (arm) / 16.25 ms (offboard) after the applied row: deterministic, its 10 ms loop;
     G1.6(a) is the across-run spread, so not a defect. Q2 (G1.1 gap rule) asked, not blocking.
     5 hovers `--sched` (`results/g16_sched_s24/README.md`): arm/offboard spread 5.0/6.25 ms, still > 2.5 ms -> A-17
     (Commander 10 ms loop phase). A-17 CONFIRMED 4/5 (`results/a17_s24/`). S25 NEXT: (1) decide A-17 fix without touching
     Commander (O-11): why its phase varies at SITL start (read-only sonnet ~10 calls), else ask owner to restate
     G1.6(a) as 'trigger within 1 period + Commander phase bound 10 ms'; (2) sonnet: takeoff/land kinds in the
     player + capture hold position (yaw hard-coded 1.585 today), then re-fly the full 5-run G1.6 set (hover, step, traj)
     with --sched at speeds 1 and 4 (host bash) and a G1.6(a) verdict; (3) G1.5 injectors via player kinds.

- S25-S26 next-action entries moved from STATE in S28 (T52-T56: paused gz rejected for A-17, player kinds and setpoint rows, B26 launched):
  000000000000000. S25 (launch 20261116-030636, cap $3): T52 DONE (7a8ad4786a runner, e7e7dc95b0 results): gz paused start
  does not fix A-17 (spread 8.75/6.25 ms); cause = Commander skips/relative sleep + free-running gz. D-A17 overturned,
  A-17 PARKED with bound, Q3 asked (restate G1.6a, or lockstep gz), not blocking. T53 DONE (sp_hold, anchor nav_state=N, takeoff/land
  kinds; `design/t53_player_kinds_s25.md`; pretest: anchor = logged nav_state change, rows after it 0 us error).
  T54 second key (haiku, `results/second_key_t53_s25/`): anchor and post-anchor rows AGREE (0 us); row-1 sp_hold
  1.5 cm off, likely Hold-mode publisher on trajectory_setpoint: re-check with sim_schedule_applied.sp (S26).
  S26 NEXT: (1) that re-check, runner rows for takeoff/land kinds and one flight; untested: anchor never reached (no timeout), sp_hold with invalid position.
  (2) re-fly 5-run G1.6 set (hover, step, traj) --sched at speeds 1 and 4 for G1.6(b); (4) G1.5 injectors via player.
  0000000000000000. S26 (launch 20261116-032411, cap $3): T55 DONE (dbf8425ef0 player att/pva/sp_back rows, 71d13d8a02 runner
  --sched for attitude + trajectory scenarios, run.json times now based on logged anchor_us; `design/t55_player_setpoints_s26.md`).
  Pretest step_roll + traj_lemniscate: all rows on time (0 us; anchor wait 15-19 ms), setpoints = analytic ref (0.000 m).
  T56 second key AGREE 4/4 (`results/second_key_t55_s26/`). Row-1 1.5 cm: Hold mode publishes trajectory_setpoint until
  offboard is accepted (FlightModeManager.cpp:364); not a player defect. Note: pre-T55 runner segment times were up to
  0.7 s late vs the player -> any pre-T55 --sched metric is suspect (only hover was --sched, hold metric, small effect).
  B26 launched detached: G1.6 set (hover, step_roll, traj_lemniscate x5) --sched --sched-anchor, speed 4 then 1.
  S27 NEXT: (1) route check 27 (sonnet, due: last S22); (2) B26: check status.txt, mode instants (second_key_player.py)
  and same-seed spread per metric (g16_spread.py) -> G1.6(b)/(c) table, two keys on the spread; (3) G1.5 injectors via
  player kinds (--sched refuses disturbance/motor_fault/erpm_loss/thrust_sag hooks today); (4) land row instead of MAVLink.
  Unverified from T55: pva propagation never exercised (rows hit own tick); step_pitch/yaw, circle not flown; 4/861 rows
  1-2 ticks late in the first lemniscate run (A-13 holes likely, not checked).
- 2026-11-16 S27: route check 27 (off path, act on G1 keys); B26 speed 4 analysed; A-14 reopened, mechanism T58 (baro fusion of a 13-15 m mismatch).
- 2026-11-16 S29: A-14 SDF fix shown impossible (gz-sensors ignores reference_altitude), bridge fix chosen; metric defects fixed (truth tracking, D-EFFORT-BW); A-19 opened.

- S30: agent ledger rows of sessions 1-13 moved from STATE:
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
- 2026-11-16 S31: A-14 bridge fix flown (B31): step gone, 0.1 m closing bound missed 9/15 (max 0.144 m), parked at 0.15 m; A-20 bridge race opened.
- S28-S30 next-action block moved from STATE in S32 (A-14 root cause, reference_altitude dead end, bridge fix, metric truth/effort fixes, ZOH key, route check 30); full text:
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
     S30 (launch 20261116-042504, cap $1.62): ZOH second key DONE (7320b3d257): rate 15/15 AGREE. T63 DONE: gz_bridge baro
     at world elevation (4443079c0b, builds in docker, make format clean, ISA self-test `bench/tests/test_baro_elev.py`;
     elevation = first raw navsat altitude, so spawn z0 counted twice, ~11 Pa/m, unverified). T64 route check 30 DONE
     (`design/route_check_30.md`): NOT on shortest path; A-14 over its 2-session cap. Acting on it:
     S31 PLAN (hard stop): (i) haiku second key of the bridge diff + pretest 1-3 hovers speed 4 (check CAL_OFF ~0 Pa,
     baro vs GNSS height, no step after EKF2 start); if it fails -> EKF2_BARO_CTRL 0, no more A-14 work. (ii) one haiku
     task: attitude 15 % gap + A-19 closing test, bound if unexplained. (iii) re-fly G1.6 set once, write G1 FINAL with
     anomalies as evidence limits, start stage 2 (loop-gain injection) in parallel. Simulator items of 1-5 below are
     DEFERRED to G3/G5 (route check 30 item 4). Escalate to owner if G1 not frozen by end of S31.
     (Old S30 list, kept for reference:)
     S30 NEXT: (a) gz_bridge baro fix (sonnet) + haiku second key, then a14_close pretest; (b) haiku second keys of the
     new truth/effort metrics over >= 5 logs (G1.3 set) and A-19 closing test; (c) step_metrics still on the estimate;
     (d) route check 30 due (sonnet), freeze G1, start stage 2. T62 DONE (`results/second_key_s29.md`, `bench/second_key_s29.py`): effort 5/5 AGREE (0.03 %); rate
     DISAGREE 8/15 by 1.6-2.9 % only because the key used linear interpolation of the setpoint, primary ZOH (ZOH key matches
     to 7 digits, run inline: add a --zoh option and re-run); attitude AGREE on step/traj, hover r1/r2 only via the 0.1 deg
     floor (~17 % rel) and the primary total is ~15 % below sqrt-sum of its per-axis values: OPEN, check with A-19 in S30.
- S32 (2026-11-16): A-20 atomic ref fix 4297ba9869 keyed; quat_angle metric fix; A-19 closed then reopened; B32 speed 4 analysed (A-14 effect gone).
- S33 (2026-11-16): arccos fixed in second key; T68 A-19 mechanism candidate (declination/mag bias); B32 speed 1 done, spreads = speed 4; A-20 not closed (bias0 0.72 m 2/30); G1 status draft in GATES.md.
- S34 (2026-11-16): A-19/A-20 bench-param pre-test (3 runs): A-20 PASS with SENS_BAR_AUTOCAL 0, A-19 declination candidate refuted (+0.36..+0.78 deg).
- S35 (2026-11-16): A-20 closed (15/15 with SENS_BAR_AUTOCAL 0); A-19 parked by mechanism (1.6 deg, yaw on estimate); route check 35 accepted (stage 2 starts S36); stage-2 margins design note; D-RATE267.
- S36 2026-11-16: G1 FINAL frozen with evidence limits (provisional under Q4-A); stage 2 started; B26 row retired (superseded by B32).
- S36 2026-11-16: stage-2 note review r1 BLOCKING (gyro break misses INDI paths) -> D-G2-BREAK (M3a); r2 CLOSED.
- S37 (2026-11-16): stage-2 note stale text patched; margins estimator + self-tests 1-3 (T75), second key AGREE 5/5 (T76).
- S38 (2026-11-16): linear rate-loop models + self-test 4 (T78, ALL PASS, break-checked), second key AGREE (T79); model predicts INDI model-only defaults PM 42.7 deg < 45 (tau_m 0.02 vs plant 0.033).
- S35 (2026-11-16): A-20 closed 15/15; A-19 parked by mechanism (1.6 deg); A-14 hold bound +-0.15 m; route check 35 accepted; stage-2 note written (T72).
- S39 (2026-11-16): M3a bench injection in mc_indi_rate_control (D-G2-INJ), build OK, pre-test hover u = c + d exact; unit test not run.

## Stage-1 agent ledger rows moved from STATE.md (S39)
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
| 30 | T63 | sonnet | gz_bridge baro elevation fix | done, 6 calls, ~$0.25, built by me |
| 30 | T64 | sonnet | route check 30 | done, 7 calls, ~$0.2 |
| 31 | B31 | host bash | A-14 bridge pretest + 15 hovers | 16/16 flew, ~11 min, $0; 9/15 FAIL 0.1 m bound |
| 31 | T65 | haiku | second key bridge diff | done, 5 calls, ~$0.1, AGREE-WITH-ISSUES (race) |
| 32 | T66 | haiku | second key A-20 diff | done, 4 calls, ~$0.1, AGREE-WITH-ISSUES |
| 32 | T67 | haiku | A-19 + attitude gap | done, 8 calls, ~$0.2, found the arccos metric defect |
| 32 | B32 | host bash | G1.6 re-fly 2x15 + pretest | done, 30/30 flew, $0 |
| 35 | B35 | host bash | A-20 15 hovers + A-19 2 hovers | 17/17 flew, $0 |
| 35 | T70 | haiku | second key bias-median column | done, 7 calls, ~$0.1, AGREE 7/7 |
| 35 | T71 | sonnet | route check 35 | done, 6 calls, ~$0.15 |
| 35 | T72 | sonnet | stage-2 margins design note | done, 11 calls, ~$0.7 (168 lines) |
- S40 (2026-11-16): INDI unit tests run (67 pass, injection gating break-checked); route check 40; G2 written in GATES.md; M3a pre-test both paths READY (hover_long); preliminary roll margins measured 61 deg/12 dB, model-only 25 deg/4.3 dB -> A-21.

- S43 (moved from STATE): S37 (launch 20261116-080552, cap $3): (1) DONE note body patched, section 7 item 7 answers r2 residuals (fault path    unreachable by finite d; M3b store point to be read in S38 plumbing). (2) DONE T75 sonnet: `bench/margins_est.py` +    `bench/tests/test_margins_selftest.py` self-tests 1-3 ALL PASS (re-run by me), 7 break checks recorded (commit    a2884f4cc9). T76 haiku second key: independent analytic GM/PM/DM, AGREE 5/5 (`results/stage2_s37/second_key_margins.md`,    `python3 bench/second_key_margins_s37.py <out.md>`); its case B is unstable with 1 crossing, multi-crossing covered by    self-test 1b only. Estimator not yet run on bench logs (CSV t,d,x,y; sign y = -L x from spec). T77 haiku: PID rate gains VERIFIED (`results/stage2_s37/pid_rate_gains.md`, units and MC_GC_EN=0 checked by me). S38 (launch 20261116-082041, cap $3) DONE: T78 sonnet `bench/margins_models.py` (sampled-data + continuous L_indi,    L_pid, time-domain sim, A-1 table) + self-test 4 ALL PASS (re-run by me; break-checked: dropping t_f fails 4a).    T79 haiku second key, independent continuous model: AGREE (INDI model-only 6.5 dB/43.6 deg vs 6.1/42.7 sampled;    PID 26.0/67.9 vs 25.8/67.9). Tables `results/stage2_s38/`. Note 7.4 reduction corrected (needs A_m = eta A_r; O(T) skew).    FINDING (model, unflown): roll INDI model-only at code defaults PM 42.7/41.6/40.6 deg at 800/400/267 Hz < 45, limited    by tau_m 0.02 vs plant tau_r 0.033 (lesson 8: ACT_TC must be identified, stage 3/4); measured path Tb 0 PM 54, blend    Tb 0.1 PM 48. Self-test 4a is coding consistency only (same equations both sides); firmware match comes from flights.
- S43: A-22 chain trace: analytic G1 878 rejected, measured static roll G1 ~340, links a (allocator) and b (output map) unexplained; `results/stage2_s43/`.

- 2026-11-16 S44: moved from STATE: - Session 16 (launch 20261115-231016, cap $3): D-SIM-STEP implemented (T31, commit 72598e3159) and pre-tested (`results/pretest_simstep_s16/README.md`): 1.25 ms step, IMU 800 Hz, RATEMAX 800/400 applied, PID flies, speed 4 ~38 s wall/run. Logger fixed: `-p actuator_motors -b 200` logs all controller-rate topics at 800 Hz, 0 dropouts. A-10.
- 2026-11-16 S44: A-22 closed as artefact; A-23 opened: 17 Hz pitch limit cycle in all INDI M3a flights S39-S41, stage-2 INDI margins void.
- 2026-11-16 S44: moved from STATE: S40 route check 40 (`design/route_check_40.md`): R1 G2 written in GATES.md (DONE S40) then rate-loop flights (S41-42); R2 stage-3 slice incl. ACT_TC identification + G2 outer-break note (S43-45); R3 G3/G4 harness tasks in parallel; stage 5 from ~S46. Projection ~25 more sessions: tell owner in the Q4 entry.
- 2026-11-16 S44: A-23 test: PID hover clean; INDI with derived G1 (1756/1599) rate RMS 32x lower, motors still pinned 46 % (chatter).

## Moved from STATE.md in S45
S36 DONE: G1 FINAL; T73 r1 BLOCKING answered (note section 7, D-G2-BREAK).
S36 T74 r2 CLOSED (`design/stage2_note_review_r2.md`): M3a cuts every in-flight path; S38 must log c (pre-injection),
   d and u at cycle rate.
S37-S38: margins estimator, models and second keys done (JOURNAL.md); tables `results/stage2_s38/`.
S39 (launch 20261116-084309, cap $3) DONE: D-G2-INJ; T81 sonnet M3a plumbing (commit feat(mc_indi_rate_control)),
   SITL build OK, 1 pre-test hover flew (`design/t81_m3a_inject_s39.md`, `results/stage2_s39/pretest_m3a/`): u = c + d
   exact (max err 0), indi_rate_status 800 Hz, no fault, generator = margins_est multisine on 15849/15998 samples (rest
   = timestamp-join artefact). Added by me: indi_rate_status.timestamp_sample, MC_INDI_INJ_DLY (default 5 s).
S40 (launch 20261116-090818, cap $2.7): (1) DONE unit tests in build/px4_sitl_o11 with -DCMAKE_TESTING=ON: rate lib
   40/40, IndiInjection 4/4, IndiAccelControl 19/19, IndiMeasuredTorque 4/4 PASS; break-check (landed gate removed)
   fails Gating, restored (`results/stage2_s40/unit_tests*.txt`). Earlier S40 plan items:
   (2) DONE in S39: haiku second key code vs D-G2-BREAK/D-G2-INJ AGREE-WITH-ISSUES (`results/stage2_s39/second_key_inject.md`):
   only -0.0 -> +0.0 at AX 0 (accepted, no effect); S41 analysis must assert fault == 0 and landed == 0 over the window,
   params set before arming. Still to do: generator check on timestamp_sample from a new flight;
   (3) route check 40 (sonnet). M3b store points partial in the T81 notes (library `_thrust_prev` unread).
S40 pre-test DONE (`results/stage2_s40/pretest_inj/README.md`): both paths READY with scenario hover_long, DLY 20,
   NP 3, TP 10, AMP 0.005 (window 52-82 s at 5 m); u=c+d, generator on timestamp_sample, fault/landed all pass.
   Preliminary roll 800 Hz: measured PM 61/GM 12.2 dB; model-only PM 25/GM 4.3 dB vs linear model 42.7 -> A-21 OPEN.
S40 also: A-21 linearity AMP 0.01 vs 0.005 PASS (PM 26.3 vs 25.3 deg, GM 5.0 vs 4.3 dB): gap to model is real.
S41 (launch 20261116-092054, cap $1.98): (1) DONE seed 2 model-only AMP 0.005 (`results/stage2_s41/`): checks pass,
   PM 24.0 deg / GM 6.0 dB / DM 14 ms -> A-21 closing test 1 PASS (PM 25.3/26.3/24.0). (2) DONE T84 haiku second key
   (`results/stage2_s41/second_key_m3a.md`): AGREE when periods 2-3 are used as the primary does (all bins <=20 Hz
   within 0.5 dB/3 deg, PM within 0.25 deg); full window incl. period 1 DISAGREES (transient). m3a_csv/m3a_margins
   second-keyed. (3) DONE T85 sonnet closing test 2 (`results/stage2_s41/a21_model_vs_measured.md`, UNKEYED):
   firmware matches margins_models.py element by element; the gap is the MODEL: it omits the attitude P loop
   (MC_ROLL_P 8 closes around the M3a break, alone gives PM 23.5/GM 4.6) and G1 fits 1.30x the default (~417 vs 320,
   unverified), plus ~1 step (1.26 ms) delay/lag (gz command latency suspected).
S42 (launch 20261116-093138, cap $1.26): (b) DONE T86 haiku + my LPF-matched re-fit
   (`results/stage2_s42/g1_regression_lpf.md`, `bench/g1_regress_lpf_s42.py LOG OUT`): G1/tau/delay ridge, not separable
   in 2-10 Hz; G1 377-385 if tau 0.033 and delay <=2 samples, 320 if tau 0.02 + 15 ms latency. (c) decides. UNKEYED.
   T87 haiku analytic G1 = 878 (`results/stage2_s42/g1_analytic.md`, UNKEYED), 2-2.7x the ridge -> A-22 opened.
OLD S44 PLAN: (1) A-22 rest, one sonnet task <=15 calls: why allocator gives 0.23/motor (source says 0.354 or 0.707) and
   why a 0.221 hover maps to w ~990 (sqrt map gives 1269): check actuator_outputs instances/topic multiplicity,
   MixingOutput thrust-model code path for gz ESC, effectiveness scaling (CA_ROTOR CT 6.5 vs physical 10.9);
   haiku second key on esc_status (not actuator_outputs). Matters for stage-4 decision 3 (G1 from CA_* derivation).
   (2) Working G1 for margins = 340 (static, end-to-end, regression-consistent) until A-22 closes. (3) (c) motor step
   in sim to separate tau and latency; (a) add attitude loop to margins_models.py (sonnet) + haiku second key.
- S43 (moved from STATE in S48): S43 (launch 20261116-114133, cap $2.79) DONE: T88 sonnet A-22 chain (`results/stage2_s43/a22_chain.md`, `bench/a22_chain.py`): static roll G1 ~340 = link a (torque_sp -> actuator_motors roll diff 0.92, 0.23/motor) x link b (actuator_motors -> (w/wmax)^2, 0.59 at hover, a 0.221 -> w ~976-999) x link c (626 meas vs 621 analytic, on truth). Product reproduces end-to-end u->alpha at 2.5/5/7.9 Hz; tau_eff 35-44 ms. 878 analytic REJECTED. T89 haiku second key (`results/stage2_s43/a22_second_key.md`): link a AGREE (0.222-0.236); link b DISAGREE but its own map is suspect (actuator_outputs zero-filled on 36 % of rows, max 1897 rad/s, R2 0.2): link b UNSETTLED. Log commit 32500e0 vs HEAD: no diff in allocator/mixer/gz_bridge/INDI module/airframe; params as assumed (THR_MDL_FAC 1, EC_MIN 0, EC_MAX 2700, CT 6.5). A-22 narrowed, still open (see ANOMALIES).
- S48: roll M3a low PM explained (attitude P loop + motor lag; model vs 2 flights within 3 deg PM); A-21 closed; D-RATE-LEAD proposed; A-26 opened.

- S49: stage-2 agent ledger rows S36-S43 moved from STATE.md:
  | 36 | T74 | sonnet | r2 check of section 7 | done, 7 calls, ~$0.35, CLOSED |
  | 36 | T73 | opus | review r1 stage-2 note | done, 11 calls, ~$0.8, BLOCKING, answered |
  | 37 | T75 | sonnet | margins estimator + self-tests 1-3 | done, 9 calls, ~$0.9, ALL PASS re-run by me |
  | 37 | T76 | haiku | second key margins (analytic) | done, 3 calls, ~$0.06, AGREE 5/5 |
  | 43 | T88 | sonnet | A-22 chain trace + link gains | done, 17 calls, ~$0.87, G1 ~340, links a,b unexplained |
  | 43 | T89 | haiku | second key links a,b | done, 10 calls, ~$0.13, a AGREE, b DISAGREE (suspect map) |
  | 42 | T87 | haiku | analytic G1 from allocator | done, 8 calls, ~$0.07, 878 vs 320-435, A-22 |
  | 42 | T86 | haiku | G1 regression | done, 7 calls, ~$0.08, missed D-filter on u, superseded by my re-fit |
  | 37 | T77 | haiku | PID rate gains read | done, 6 calls, ~$0.06, units fixed by me |
  | 38 | T78 | sonnet | margins_models.py + self-test 4 | done, 15 calls, ~$1.0, ALL PASS re-run by me |
  | 38 | T79 | haiku | second key continuous models | done, 4 calls, ~$0.1, AGREE |
  | 38 | T80 | haiku | GM jump check | done, 5 calls, ~$0.06, explained (phase plateau) |
  | 40 | T83 | haiku | M3a pre-test flights + checks | done, 12 calls, ~$0.3, (b) blocked by runner, fixed by me |
  | 40 | T82 | sonnet | route check 40 | done, 5 calls, ~$0.15 |
  | 41 | T85 | sonnet | A-21 model vs measured | done, 15 calls, ~$0.6, model omits attitude loop |
  | 41 | T84 | haiku | second key m3a FRF (2 rounds) | done, 13 calls, ~$0.3, AGREE on periods 2-3 |
  | 39 | T81 | sonnet | M3a plumbing + build + 1 hover | done, 27 calls, ~$0.93, test not linked, fixed by me |

- S50 (2026-11-17): owner answered Q2 (A amended: two hole kinds), Q3 (A, S27 wording), Q4 (A + new G1.7 provenance); GATES.md updated, entries moved below.

## Q2 (2026-11-16, session 24): G1.1 gap rule fails on holes in the simulator, not in the log. Amend? — CLOSED S50 (owner answered 2026-11-16)

**Question.** May I change the G1.1 gap rule after its first test, as below?

**Context.**
- G1.1 says: every declared topic logged at >= its rate, "max gap < 3 declared periods outside the start-up second".
- After the logger fixes of S16-S23, every controller-rate topic is logged at full rate (sim_ground_truth 56578 samples
  vs 56586 gyro samples, hover at speed 4).
- The rule still fails: max gap 5.0-6.3 ms (4-5 periods of 1.25 ms) on gyro, angular velocity, motors, torque setpoint,
  ESC, truth. All topics share the same few instants (7 gaps in 56586 samples, 0.016 %), and the gaps are already in
  `sensor_gyro` and in the truth stream published by gz_bridge: the simulator skipped those steps (A-13, parked S23).
- So the rule measures the simulator, while G1.1 is about logging what the analysis needs. I count this as a defect
  in the test. But the mission says any gate change after its first test goes to you.

**Options.**
- A (recommended): split the rule. (i) Logger completeness: every sample the source published is in the log, checked
  against the source count (gyro/truth), at most 0.1 % missing. (ii) Simulator holes get their own row with a bound:
  <= 0.05 % of steps, single holes <= 10 ms. Every analysis that needs a continuous signal (G2 frequency response,
  spectral detector) must leave out windows that contain a hole, or show its result does not change when they are
  left out (already the A-13 reopen trigger).
- B: keep the rule and remove the simulator holes first (cause in gz at speed 4 not found yet; 1-3 sessions of
  simulator work with no gate gain).
- C: keep the rule as it is. G1 stays failed until B is done.

**Meanwhile.** I continue with the scenario player (G1.6a) and G1.5. Not blocked. I will not mark G1.1 as passed
before you answer.

**Owner answer (2026-11-16): A, amended.**
- (i) Logger completeness as proposed: every sample the source published is in the log (checked against gyro/truth
  counts), at most 0.1 % missing.
- (ii) No global bound on holes: the proposed 0.05 % / 10 ms bound came from one hover and is already exceeded by
  S47 `measured_g2` (truth single hole 11.25 ms, gyro 10.0 ms, controller output 0.054 % missing). Holes also occur
  at speed 1 (2/5 S32 hovers), so running slower does not remove them.
- Two hole kinds, both reported per gate-bearing run: sim holes (gaps in `sensor_gyro`/`sim_ground_truth`) and
  controller holes (gaps in `vehicle_angular_velocity`/`actuator_motors` where `sensor_gyro` is continuous: PX4 skipped
  a rate-loop cycle, e.g. S32 speed1 hover r3 at 41.341 s, S47 measured_g2 19 controller vs 8 gyro holes; logger
  dropouts 0). Option A as written did not cover the second kind.
- Every frequency-response or spectral window excludes both kinds, or shows its result unchanged without them.
- More than ~0.1 % holes in a run triggers a re-fly of that run, not a gate failure.


## Q3 (2026-11-16, session 25): G1.6(a) mode instants cannot meet 2.5 ms without lockstep gz. Restate? — CLOSED S50 (owner answered 2026-11-16)

**Question.** May I restate G1.6(a) after its first test, as below, or do you want lockstep gz first?

**Context.**
- G1.6(a): PX4 mode transitions within 2 IMU periods (2.5 ms) across same-seed runs.
- The sim-time player (S24) applies arm/offboard triggers at the exact same sim time in every run (spread 0 us, two keys).
- PX4's response still spreads 5-9 ms: Commander (zero diff, O-11) acts on its next 10 ms tick, skips its sleep
  while a command is pending, and sleeps relative to the end of its own work. gz runs free of PX4, so that work's
  wall time becomes a random sim-time shift (1.25 ms steps). Starting gz paused (S25) did not change it.
- Only a gz-PX4 lockstep (gz waits for PX4 each step) removes it: new sim plugin, est. 1-3 sessions, no gate gain
  except G1.6(a); it would also tighten G1.6(b).

**Options.**
- A (recommended): (a) becomes (a1) triggers applied at the same sim time across runs, within 1 IMU period; (a2)
  PX4's response within one Commander period (10 ms) of the trigger, logged; plus the player anchors every
  scenario row after a mode change on the logged transition, so the controller sees the same scenario. (b)-(d)
  unchanged: any spread the residual causes still counts against verdicts.
- B: build lockstep gz first, keep (a) as written.
- C: keep (a); G1.6 stays failed.

**Addendum S27 (B26 speed 4, 15 runs):** triggers exact (0 or +1 IMU tick). PX4 response spread 6.25-8.75 ms, but the
offboard latency is 11.25-20 ms (1-2 Commander ticks), so option A's (a2) would read "response spread within one
Commander period, latency within two". Provisional verdicts under A are in GATES.md (not marked passed).

**Meanwhile.** I continue with the player (take-off/land kinds, anchoring on the logged transition) and G1.5.
Not blocked. G1.6 is not marked passed before you answer.

**Owner answer (2026-11-16): A, with the S27 wording.** (a1) triggers at the same sim time across runs within 1 IMU
period; (a2) PX4 response spread within one Commander period (10 ms), latency within two (20 ms); every analysis
window anchors on the logged transition. Reason: the 10 ms tick is real flight-stack behaviour (Commander.cpp sleep
rule, zero diff), so a lockstep sim would hide jitter the vehicle has. Owner check on the 30 S32 runs: triggers at
30.000/52.000 s in 29/30 (one +1.25 ms), arm latency 1.25-10.0 ms, offboard 11.25-20.0 ms, at the mechanism bound.


## Q4 (2026-11-16, session 32): G1 not frozen after 32 sessions. Freeze it with stated evidence limits and start stage 2? — CLOSED S50 (owner answered 2026-11-16)

**Question.** May I freeze G1 now with the limits below written into GATES.md as evidence limits, and start stage 2
(loop-gain injection, margins), or must G1 pass in full before any stage-2 result is used?

**Context.**
- Done with two keys: logging at full controller rate (G1.1 except Q2), truth topic stamped in sim time (G1.2),
  metrics on truth with second keys (G1.3), self-tests break-checked (G1.4), sim-time scenario player (G1.6a1).
- A-14 (baro step, 2.3 m wrong take-off height in 2/15 same-seed runs) fixed in the simulator: spread 2.3 -> 0.13 m.
- Open limits: Q2 (sim step holes), Q3 (Commander 10 ms tick), A-14 parked at 0.15 m EKF-truth z, A-19 EKF heading
  error 0.6-1.5 deg varying under one seed (yaw on truth carries it), G1.5 injectors/variants not built yet (route
  check 30 deferred them to G3/G5, where they are first needed).
- Every further stage-1 session has gone into simulator anomalies with no gate progress (route check 30).

**Options.**
- A (recommended): freeze G1 with these limits listed; G1.5 is re-opened per injector when G3/G5 builds it (each
  injector gets its G1.5 check before its first campaign); yaw verdicts quote the estimate-based yaw plus the EKF
  heading error separately until A-19 is explained. Start stage 2 in S33.
- B: keep stage 1 until G1.5 and A-19 pass (estimate 3-5 sessions), then stage 2.

**Meanwhile.** S33 analyses the speed-1 re-fly, A-19's mechanism (one haiku task), and prepares the stage-2
injection design without using its results for a verdict. Not blocked.

**Update S35 (2026-11-16).** A-20 closed (15/15). A-19 parked with a 1.6 deg bound, and yaw verdicts are stated on the estimate. Route check 35 (`design/route_check_35.md`) recommends option A. Meanwhile, from S36 I write G1 FINAL with the stated limits and start stage 2, with every stage-2 result marked "provisional under Q4-A". If you answer B, those results are re-run after G1 passes in full.

**Update S36 (2026-11-16).** G1 FINAL written in GATES.md (frozen, 5 evidence limits listed, not marked passed). Stage 2 has started; its results are marked "provisional under Q4-A".

**Update S40 (2026-11-16).** Route check 40 (`design/route_check_40.md`): no gate passed yet; G2 tests now written in
GATES.md, first G2 rate-loop flights S41-S42. Projection at the current pace (~$3/session, one agent task each): G2
rate loops ~S45, stage 5 (outer loop) ~S46-S56, validation ~S62, packaging ~S66, i.e. about 25 more sessions. Your
answers to Q2-Q4 remove the "provisional" mark from every stage-2 result; a larger per-session cap would shorten this.

**Owner answer (2026-11-16): A, plus a new item G1.7 provenance.** G1 stays frozen with its evidence limits (as
amended by Q2 and Q3). Add G1.7 before any G2 result counts: a gate-bearing run needs a clean tree, a binary built
from the recorded commit (binary hash recorded in run.json), and sim model and param file hashes recorded; the runner
refuses otherwise. Reason: the S45 clean hover used as the stage-2 reference ran on a dirty tree, the SITL binary was
rebuilt later, and S47 cannot reproduce it (hover thrust estimate 0.137 vs 0.194). Stage-2 numbers so far are void
anyway, so nothing needs re-running under this answer.

- S50: stage-2 ledger rows moved from STATE:
  | 45 | T93 | sonnet | route check 45 | done, 7 calls, ~$0.15 |
  | 44 | T90 | sonnet | A-22 links a,b trace | done, 15 calls, ~$1.0, found limit cycle |
  | 44 | T92 | haiku | A-23 PID + INDI-derived-G1 hovers | done, 11 calls, ~$0.1, PID clean, INDI chatter |
  | 44 | T91 | haiku | second key limit cycle, 3 logs | done, 7 calls, ~$0.1, CONFIRMED |

- S44-S46 (moved from STATE in S51): S44 (launch 20261116-212207, cap $3) DONE: T90 sonnet A-22 trace (`results/stage2_s44/a22_links.md`) + T91 haiku second key (`results/stage2_s44/limit_cycle_second_key.md`): every INDI M3a flight S39-S41 is in a 17 Hz pitch LIMIT CYCLE with motors pinned at 0 on 38 % of samples -> stage-2 INDI margins S40-S43 VOID; A-22 closed as artefact, A-23 opened. Plant G1_roll derived 1756 (CT/KM cancel; needs Ixx and hover thrust, not in CA_*) vs default 320. S44 also: A-23 test flown (`results/stage2_s44/a23_test/`): PID clean; INDI derived G1 cuts rate RMS 32x but motors still pinned at 0 on 46 % (motor-command chatter, 2nd mechanism). See A-23 note. S45 (launch 20261116-214129, cap $3) DONE: A-23 CLOSED. Cause: G1 defaults 5-8x low (yaw 7x: derived G1_Y 205-222, `results/stage2_s45/g1y_derivation.md`). Hover with G1 R/P/Y 1756/1599/215 (`results/stage2_s45/a23_yaw/`): motor pin 0 %, rate RMS 0.0068/0.0056/0.0017, achieved 1.0. A-24 opened (45.7 Hz motor tone, std 0.00085). Route check 45 (`design/route_check_45.md`): stage 2 margins wait for derived defaults; old margin numbers void, method kept. S45 also: T96 `bench/derive_g1.py` + `bench/tests/test_derive_g1.py` written (ALL PASS, re-run by me), UNKEYED: quad5in G1 R/P/Y 1759/1602/221 (`results/stage2_s45/derive_g1.md`). Roll and pitch share PX4's normalisation scale, so torque per unit command is equal and G1_P = G1_R Ixx/Iyy for any arm layout (my reading: B pinv(B) = I). D-G1-DERIVE written. S46 (launch 20261116-215112, cap $3): `bench/pretest_gate.py` + self-test (break-checked) committed: hover window from first airborne +15 s, rate RMS < 0.02 rad/s, motor pin < 1 %, torque achieved > 90 %, exit 0/1/2. On logs: PID and S45 INDI pass, S44 chatter and S41 limit cycle fail (`results/stage2_s46/pretest_gate_check/`). T97 sonnet second key of G1 derivation running -> `results/stage2_s46/g1_second_key.md` (also: which inertia, 1.396e-3 or 1.022e-3, is the plant's). S46 also: T97 second key AGREE on roll/pitch with TOTAL inertia; bench G1 1757/1640/205 in `bench/params/quad5in_indi_g1.params`.
- S52 (2026-11-17): MC_INDI_LEAD implemented and second-keyed; roll M3a lead 1 (ACT_TC 0.033, P8) PM 59/GM 14 dB on 2 seeds vs 26/10.7 without lead; runner appends derived airframe params.
S53 move: S47 (launch 20261116-221436, cap $3): first roll M3a flight with derived G1 invalid: 41 Hz yaw LIMIT CYCLE (pin 37-52 %)
  on model-only and measured paths, S45 clean hover not reproducible (same binary/model/params: bistable). Cause: G2_Y 0
  while the rotor spin-up torque dominates yaw above 1.2 Hz. Derived G2_Y 27 (D-G2Y-DERIVE): 4/4 hovers (2 seeds x 2
  paths) pin 0, rate std <= 0.018, pretest_gate PASS. A-25 opened+closed. `results/stage2_s47/roll_m3a/README.md`.
  M3a margins at AMP 0.005 measured on a saturating plant: VOID. With G1 5x higher, AMP must drop ~5x (0.001).
  T100 second key G2_Y AGREE 27.0. First valid roll M3a (model-only s1, AMP 0.001, no pin, 18/18 bins): PM 22 deg
  @3.5 Hz, GM 4.1 dB, DM 18 ms -- below G2; phase -169 deg at 1 Hz = attitude loop over a slow rate loop (suspect).
  Hypothesis (S47, by hand): matched INDI gives L ~ K_R (1 + P_att/s)/s x A(s) x F(s); MC_INDI_K_R 20 rad/s, airframe
  MC_ROLL_P 8 -> at w_c 22 rad/s: -90 -20 (atan 8/22) -36 (motor 33 ms) = -146 deg + filters/delay ~ measured -158.
  I.e. K_R/P_att = 2.5 and K_R ~ 0.7 x motor bandwidth (30 rad/s): margins limited by the gain defaults, not G1.
  S48 (launch 20261116-223404, cap $3): low roll PM EXPLAINED (`results/stage2_s48/README.md`): model + attitude P loop
  matches S47 (PM 23.6 vs 22.3, f_c 3.48 both, GM 4.7 vs 4.1). Matched INDI: L ~ K A(s)(1+P/s)/s, motor lag caps K_R;
  filters irrelevant; ACT_TC 0.02 vs plant 0.033 costs 5 deg/9.5 dB; G2 by gains alone needs P_att <= 2.5. Remedy
  proposed D-RATE-LEAD (nu -= K tau_c a_f): model PM 56-61, GM 11-16 dB at K 20-40. A-26 opened (1 Hz phase).
  Flight checks (model-only, s1): ACT_TC 0.033 P8 -> PM 25.9/GM 10.7 (model 28.6/14.2); P3 -> 42.9/13.4 (model
  43.8/15.7). A-21 CLOSED. T101 second key: PM/f_c/DM AGREE, GM DISAGREE (flights side with the first key; model GM
  2-3.5 dB optimistic, unmodelled delay).
- S54 (2026-11-17): A-27 explained (yaw M3a L -> -1 at DC: static G1+G2/dt yaw denominator, dead-beat spin-up); D-YAW-INV option (c) proposed, model UNKEYED.
- S56 (2026-11-17): D-YAW-INV option (c) coded (23e9d30cc0, 296766019a after second key), yaw M3a PM 88 / Ms 1.6 dB on 2 seeds, A-27 closed.
## S49-S53 detail moved from STATE.md (S56)
S49 (launch 20261116-224459, cap $2.28): T102 stage-2 summary table (`results/stage2_s49/summary_table.md`): only valid
   measured margins are INDI roll torque break at 800 Hz (best PM 42.9 at P3); no measured PID, no 400/250 Hz, no other
   break point. T103 D-RATE-LEAD note draft (`design/rate_lead_note.md`): new param MC_INDI_LEAD scale 0..1 (default 1,
   0 = current law), insertion at indi_rate_control.cpp step 8 (l.378-382), c_i = lead K_i ACT_TC, 0 when landed; noise
   x1.4-2.3 on the a_f term (G4); filter H is in the model (checked). Stage 3 OPEN.
S49 also: lead falsification sweep (`results/stage2_s49/lead_delay_README.md`, UNKEYED): unmodelled delay calibrated
   ~2.5 ms on tc33_p8; lead K20 at 400 Hz PM 57.0/GM 10.5, K30 52.8/8.1, K40 fails -> stop rule not triggered, K_R 20.
S50 (launch 20261117-011145, cap $2.02): owner answers applied (GATES.md G1 FINAL block, evidence limit 1 = two hole
   kinds, >0.1 % -> re-fly). G1.7 implemented: `bench/provenance.py` + `run_scenario.py --gate` + self-test (ALL PASS,
   break-checked), D-G1.7. Current SITL binary is from 32500e0276, not HEAD: rebuild after the LAST commit before a --gate batch
   (any commit, even docs, moves HEAD and makes the binary stale; build = `indi_project/docker/run.sh -n build -t 3600 'make px4_sitl_default'`). TODO: a hole
   reporter per run (sim vs controller holes, extend `bench/a15_gaps.py`?) for evidence limit 1; G1 passes once G1.7 in use.
S50 also: T104 sonnet second key of the lead sweep (`results/stage2_s50/lead_sweep_second_key.md`): AGREE on the
   decision at K_R 20 (PM within 1.4 deg); GM key 2 0.6-2.7 dB higher, K30-40 PM 5-7 deg higher (filter choice). Item (1) next is DONE.
S51 (launch 20261117-021217, cap $3): T105 opus review r1 of the lead note vs code: NOT BLOCKING (`design/rate_lead_review_r1.md`,
   dispositions there, D-RATE-LEAD addendum). Majors: lead is feedback-only (setpoint path keeps actuator lag); GM falls
   12-18 dB in model, ACT_TC overestimated +40 % is the dangerous side (K40: ~5 dB); yaw lead leaves the G2 path lag.
S52 (launch 20261117-022149, cap $3): MC_INDI_LEAD implemented (T107 sonnet, 6e82b66300; reset fix after T108 haiku
   second key AGREE on law, `results/stage3_s52/lead_second_key.md`); 13 unit tests, break-checked (sign flip -> 7 fail);
   closed-loop test PM 34 -> 66, ACT_TC x0.6 PM 45/GM 9.5, x1.4 PM 83/GM 13 (under-estimated tau_c is the weak side, not
   over as review F2 guessed). Flight roll M3a tc33 P8 lead 1, 2 seeds: PM 59.1/59.1, GM 13.9/14.3, DM 57 ms
   (S48 lead 0: 25.9/10.7/25) -> `results/stage3_s52/m3a_lead/README.md`. Runner now appends quad5in_indi_g1.params
   (7c8b8d1661). pretest_gate "end-time option" not needed: use --delay 4 --length 15 to end before the injection.
S53 (launch 20261117-023518, cap $3): ACT_TC sweep with lead 1 (`results/stage3_s53/act_tc_sweep/README.md`): x0.5 PM 36/
   GM 5.1, x1.5 86/11.3, x2 75/10.0 (2 seeds, f_c 7 Hz): tolerance one-sided [x1, x2]. D-RATE-LEAD addendum 2: defaults
   LEAD 1, ACT_TC 0.05 (apply with item 6 of the stage-3 note), stage-4 ident reports an upper bound of tau_c.
   T109 sonnet drafted `design/stage3_items_note.md` (6 items, UNREVIEWED; 9 UNVERIFIED points listed in it).
S53 also: route check 53 (`design/route_check_53.md`), acted on: defaults applied (7522625b0f, ACT_TC 0.05; LEAD already
   1); opus review of the items note DEFERRED (items 1-3 parked as a post-G2 safety package, reviewed before they are
   coded). Pitch M3a ACT_TC 0.05: PM 86.9/86.8, GM 11.9/12.0 (2 seeds, = roll). Yaw M3a pre-test (AMP 0.008):
   no crossover in 1-50 Hz (|L| -0.7 dB at 1 Hz), Ms 8.2 dB at 1 Hz -> A-27 opened. SITL rebuilt at 7522625b0f
   (later commits docs/results only; --gate still needs a rebuild at HEAD).
- S56 (2026-11-17): yaw M3a GM 18.4 dB at 22 Hz; roll M3a at 400 Hz PM 84 / GM 10.5 / DM 58 ms (2 seeds).
- S57: roll M3a 800/3 Hz re-flown with TP 7.5 (PM 83.4, GM 10.1); route check 57 acted on: rate-loop table deferred to stage 6, measured-rotor anchor flown; T116 outer break note launched.
- S57: T116 G2 outer break note written (UNKEYED); measured-rotor roll anchor 800 Hz PM 77 GM 16.5 (D-G2-DEFER).
- S58 (2026-11-17): D-G2-OUTER-DEFER; stage-3 items 1 (landed split, t_fb ramp) and 4 (frozen rpm) coded 65356c4250, second key AGREE.
## S54-S56 detail moved from STATE.md (S58)
S54 (launch 20261117-024822, cap $3): A-27 EXPLAINED. Yaw M3a re-flown 0.1-20 Hz (`results/stage3_s54/yaw_m3a_lf/`):
   L -> -1 at DC. Cause: step 8 yaw denominator G1 + G2/dt (~105 G1 at 800 Hz, dead-beat spin-up) -> law extrapolates t_f,
   M3a reads -H A_m, yaw gain set by G2 and dt, not K_Y. Model `bench/yaw_break_model_s54.py` matches flight to 1 Hz, keyed by T111 (AGREE after a key-2 fix);
   proposed fix D-YAW-INV option (c) (increment low-passed by G2/G1, dt-independent): yaw loop = K A/s, Ms 1.6-8.1 dB
   under G2 x0.5-2, tau x1-2. m3a_margins_pretest.py takes fmin fmax Tp args; checks.py hard-codes the S40 multisine.
S55 (launch 20261117-025824, cap $1.48): yaw model extended (`results/stage3_s55/yaw_model/README.md`, UNKEYED, ae715f427d):
   option (c) dt-independent; tau_m >= plant tau and G2 x0.5..2 -> M3a Ms <= 5.9 dB, GM >= 8.2; weak side tau_m < plant
   and law G2 > plant (GM 0.6). T112 opus review r1 note vs code: NOT BLOCKING (`design/yaw_inv_review_r1.md`, opus ~$0.7
   in 7 calls). Majors: store applied yaw increment after step 9 clamp (replaces _t_f_prev), zero it when landed and in
   resetStates, rewrite G2_Y param/header text; lead acts fully on yaw (x105) -> yaw depends on ACT_TC/LEAD as roll.
S56 (launch 20261117-061159, cap $2.83): D-YAW-INV IMPLEMENTED (T113 sonnet 23e9d30cc0; T114 haiku second key AGREE-WITH-ISSUES:
   first landed cycle read the flight increment -> 296766019a, new test break-checked). 58/58 unit tests. A-27 CLOSED: yaw M3a
   2 seeds f_c 1.24 Hz, PM 88, DM 197 ms, Ms 1.6 dB (model 1.4 Hz/1.3 dB), `results/stage3_s56/yaw_m3a/README.md`. Yaw GM
   unread (band ends 20 Hz at arg -170): extend bins to ~40 Hz for the G2 table. No bench script reads torque_increment.
   SITL binary at 23e9d30cc0: rebuild before any further flight or --gate batch.
   Yaw GM read DONE (`results/stage3_s57_pre/yaw_m3a_hf/README.md`): GM 18.5/18.3 dB at 22 Hz, 2 seeds. Yaw 800 Hz:
   PM 88, DM 197 ms, GM 18.4, Ms 1.6 dB. SITL binary at 296766019a firmware.
   Roll M3a 400 Hz DONE (`results/stage3_s57_pre/roll_m3a_400/README.md`): PM 84.4, GM 10.5, DM 58 ms, Ms 3.9, f_c 4 Hz,
   2 seeds, logged at 400 Hz. pretest_gate over a whole M3a flight FAILs by design: always pass --delay 4 --length 15.
- S59: stage-3 items 2+3 coded (eafb26b623^), hover x2 with items 1-4 PASS, no false flag.
- S57 (launch 20261117-071301, cap $3): roll M3a 800/3 Hz re-flown with TP 7.5 (`results/stage3_s57/roll_m3a_267b/README.md`):    PM 83.2/83.6, GM 10.2/10.0, DM 57 ms, Ms 4.0/4.1, 2 seeds; S56 seed 1 had taken the LS (non-uniform t) path, not a rounding    hole; LS and FFT paths agree on flight data. Route check 57 (`design/route_check_57.md`) ACTED ON: rate-loop table stops    here (roll 800/400/267, yaw 800); remaining rates and the measured-rotor table move to stage 6, except ONE measured-rotor    anchor (roll 800 Hz, sim v2, CA_R_W_MAX 2700, B-S57b) because the flight configuration had no anchor under the current law.    Measured-rotor anchor DONE (`results/stage3_s57/roll_m3a_meas800/README.md`): roll 800 Hz PM 77.5/77.0, GM 16.6/16.3,    DM 70/72 ms, Ms 2.1, f_c 3.0 Hz, measured torque in use 100 % of window; linear-model cross-check of this path: stage 6.    T116 DONE: `design/g2_outer_breaks_note.md` (59 lines, UNKEYED). PID breaks under O-11 via additive trajectory_setpoint    velocity/acceleration feed-forward (PositionControl.cpp:133/:153), position/attitude as reference breaks (L = T/(1-T));    INDI M3b: d into t_c after indi_accel_control.cpp:273 (_thrust_prev inherits d); A-26 model form; Tp 9.000 s; 6-9 sessions.
- S60: stage-5 hover slice coded (T122), flew with INDI stage active 34-98 s, gate PASS; telemetry path off in params; freshness flicker found; commits 97317663c1, instrument.
- Ledger rows S45-S48 moved from STATE (S60):
  | 48 | T101 | sonnet | second key lead/att-loop margins | done, 3 calls, ~$0.1, PM AGREE, GM DISAGREE (flights side with key 1) |
  | 47 | T98 | sonnet | roll M3a + yaw follow-up F5-F9 | done, 15 calls, ~$0.6, found yaw limit cycle; wrong guess on cause (code change) |
  | 47 | T100 | haiku | G2_Y second key | done, 5 calls, ~$0.1, AGREE 27.0 |
  | 45 | T96 | haiku | derive_g1.py + self-test | done, 7 calls, ~$0.1, ALL PASS, UNKEYED |
  | 45 | T95 | haiku | second key A-23 numbers | done, 7 calls, ~$0.06, AGREE (RMS 0.0068/0.0056/0.0017, pin 0 %) |
  | 45 | T94 | haiku | A-23 hover G1_Y 215 + checks | done, 6 calls, ~$0.1, clean hover |
- Ledger rows S49-S50 moved from STATE (S60):
  | 50 | T104 | sonnet | second key lead delay sweep | done, 5 calls, ~$0.25, AGREE at K20, GM 1-3 dB optimistic |
  | 49 | T102 | haiku | stage-2 summary table | done, 7 calls, ~$0.2, PID GM values negative (not used) |
  | 49 | T103 | sonnet | D-RATE-LEAD note draft | done, 6 calls, ~$0.3, UNREVIEWED |

- S61: STATE detail S58-S59 moved here:
S58 (launch 20261117-073027, cap $3): D-G2-OUTER-DEFER (outer break note keyed against stage-5 code, not now);
   D-S3-LANDED, D-S3-FROZEN, D-S3-SPTO written. Items 1 (landed split + t_fb ramp) and 4 (frozen rpm) CODED 65356c4250:
   tests 4/4 targets pass, break-checked (`design/t117_s3_items_s58.md`), SITL build rc 0, format clean; haiku second key
   AGREE (`design/t118_second_key_s58.md`, its one issue unreachable). Not flown yet. REBUILD SITL before flying (binary
   built mid-edit). Flight command template: `design/t81_m3a_inject_s39.md` (run_scenario.py --scenario hover --controller
   indi_m3a --model quad5in --params ...); S57 READMEs do not record the command: record it in every new README.
S59 (launch 20261117-074704, cap $3): items 2 (start-up refusal + foreign torque publisher flag) and 3 (D-S3-SPTO
   timeout, rates zeroed, thrust held) CODED (T119 sonnet, `design/t119_s3_items_s59.md`): 6/6 test targets, break-checked,
   format clean; haiku second key AGREE-WITH-ISSUES (`design/t120_second_key_s59.md`, 5 minor, none blocking: thrust hold
   checked by reading only; stop/start within 0.5 s refused). Hover with take-off + landing, 2 seeds, items 1-4 live:
   gate PASS, rate RMS <= 0.006 rad/s, no stale/foreign/frozen flag (`results/stage3_s59/hover_items23/README.md`).
   G1.7 provenance needs a clean tree AND a binary rebuilt at HEAD: commit, rebuild, then fly.
Route check 59 (`design/route_check_59.md`, sonnet) ACTED ON: opus review of the stage-3 safety diff DEFERRED to one
   combined review with the stage-5 hover-slice diff, before any freeze (lesson 19 kept: nothing frozen until then);
   G3-G8 test text is the gap: write G5 tests (incl. item 2/3 trigger scenarios) before the first G5 flight.

- S61: owner note N1 CLOSED (B.1 confirmed on 3 seeds, B.2 G2-STEP written, B.3 decided D-S3-ATT-STEP, code next; C1 fixed d7c637cb20; C2, C3 open in STATE). Text:
## N1 (2026-11-17, owner note written between S60 and S61): off-loop work, step criterion, bench defects. Not blocking.

Act on this entry first in S61, before the S61 plan in STATE.md (item B changes its order). Then mark it closed and
move it to JOURNAL.md.

**A. What happened while the orchestrator was stopped (08:37-18:20).** Three owner commits, not yet in STATE.md:
- d48766751a: `run_scenario.py` started `disturbance.py` without `--model`, so the injector always pushed on `x500_0`;
  on quad5in every disturbance scenario applied no wrench. Fixed (`--model <model>_0`). New scenario `torque_steps`
  (2 s body-torque steps: roll 100, pitch 100, yaw 30 mN m, position hold). No earlier `indi_flight/results` run used a
  disturbance scenario on quad5in (checked), so no committed result is invalidated.
- 002b4d2df0: a relative `--out` made the injector resolve its trigger file under itself and apply nothing, silently.
  The runner now makes `--out` absolute.
- 018e37683e: ad hoc INDI vs PID comparison, `results/indi_vs_pid/` (quad5in, sim v2, 800 Hz, seed 1, speed 4, same
  attitude P and stock position loop, `indi.params` = S59 hover.params, K_R/K_P/K_Y default). NOT gate-bearing: one seed,
  dirty tree (injector fix uncommitted at flight time). Findings (`metrics.md`):
  - roll/pitch 15 deg steps: INDI overshoot 13.8 / 12.6 % (PID 0 %), 2 % settle 659 / 664 ms (PID 380 / 389 ms),
    rate-tracking RMS 14.5 deg/s (PID 9.3); rise time equal (~180 ms).
  - yaw 45 deg step: INDI overshoot 3.4 % (PID 0.2), settle 1303 ms (PID 1233), rise 476 ms (PID 660).
  - torque steps: INDI rejects better, yaw markedly (peak 4.8 deg vs 14.5), roll/pitch peak ~10 % lower.
  The overshoot is not explained yet: D-RATE-LEAD found PM 29 deg at the torque break without the lead, but this
  comparison flew with MC_INDI_LEAD 1 (M3a PM 59-87 deg). The M3a break does not show the attitude step response:
  find the mechanism (rate setpoint lag, attitude P on a slower inner loop, ...) before choosing the fix.

**B. Owner decision: attitude step criterion, fixed before the thrust-gap work.**
1. Confirm first. Re-fly step_roll, step_pitch, step_yaw with INDI and PID on at least 2 more seeds (gate-bearing if
   G1.7 allows: clean tree, binary rebuilt at HEAD; use `results/indi_vs_pid/fly.sh` as the command template). If the
   INDI overshoot/settle gap holds on >= 2 seeds, go to 2; if it does not, record why seed 1 differed and resume S61.
2. Write an attitude step criterion into GATES.md (the inner-loop gate, before its first test): ABSOLUTE thresholds
   (overshoot, 2 % settle time, per axis) derived from the PID reference numbers measured in step 1 and justified in
   DECISIONS.md. F-5 stands: no gate is a ratio to PID; PID only informs the threshold values. Owner's starting point:
   roll/pitch overshoot <= 5 %, settle no more than ~10 % above PID's measured value; tighten or justify a change.
3. Fix the default INDI tuning to pass it BEFORE the S61 thrust-gap flights. The fix is yours to choose (attitude P
   under INDI, K_R and lead limits, reference model, ...) within F-1 and F-3: generic, robust defaults, no per-airframe
   hand tuning, margins (G2) not traded away. Check the fix keeps the torque-step rejection of item A.

**C. Bench defects to fix (found by the owner, not fixed).**
- `bench/run_scenario.py:285` queries `gz model -m x500_0`: `gz_model_info.txt` is empty on every quad5in run. Use
  `<model>_0`.
- `bench/disturbance.py`: `payload_add` and `com_shift` size their force from `X500_MASS_KG`, `gust_x`/`gust_diag` use
  the x500 drag area `CD_A`. On quad5in these disturbances are mis-sized. Take mass and drag from the flown model.
  `torque_steps` is not affected. Give each profile its G1.5 check before its first campaign (GATES.md G1.5 row).
- The S61 thrust-gap flights use `motor_fault` / `thrust_sag` (SIM_GZ_* params), which are not affected by the injector
  bug, but every scenario using them is attitude-mode (`_ATT`). A hover on the stage-5 slice with a thrust gap needs a
  new scenario.

**D. Untracked results.** About 283 files (~39 MB, `results/` of S10-S32: metrics.json, run.json, csv, sched.txt, ...)
were never committed. Leave them as they are: do not commit, move or delete them. From now on, at the end of the
session that produced a run, commit its metrics and run metadata (metrics.json, run.json, README) as MISSION.md says;
raw logs stay untracked. `git status` should show no untracked file you created.

- S61: lessons moved out of STATE (still valid): S45 derive every physical parameter from the model/airframe before the
  first closed-loop measurement and log it in run metadata; S44 every pre-test runs a spectral oscillation check on body
  rates and motor saturation fractions.
- S62 (2026-11-17): D-S3-ATT-STEP setpoint lead coded (da64bc26b3, b8866cd4b1), keyed (T126), flown seeds 1-3: INDI step OS 13 % -> <=1 %, settle 655-870 -> 358-394 ms.
- S60 detail (moved S62):
  S60 (launch 20261117-075815, cap $3): stage-5 HOVER SLICE CODED (T122 sonnet, `design/t122_hover_slice_s60.md`;
     D-S5-SLICE): mc_indi_pos_control rewritten in place (shell copy of MPC + stock PositionControl/Takeoff/GotoControl libs,
     INDI stage entered at a_ref, bypass/tracking outside FLIGHT), MC_INDI_POS_EN, rc.mc_apps start || mc_pos_control.
     Unit tests pass (new a_ref-entry test break-checked), format clean, SITL rc 0. NOT second-keyed yet.
     Diagnostic hover (`results/stage5_s60/hover_diag/README.md`): module ran, stage ACTIVE 34.0-98.0 s, take-off/land OK,
     gate PASS on first hover. BUT telemetry path never valid (hover.params lacks MC_INDI_W_MAX -> modelled state only), and
     attitude freshness flickers when sample is newer than `now` (fix: clamp age at 0). Residual check cannot separate INDI
     from stock in a gap-free hover (ht/g = 0.014 scale).
     Second key T123 (`design/t123_second_key_s60.md`): AGREE, 3 deviations to act on in S61: (1) setFilter re-config while
     active does not reset filter states (call _indi.reset on re-config); (2) A3 stale fallback uses this cycle's stock thrust,
     fix code or amend A3 text; (3) ESC staleness 100 ms not in spec, record in A5.
     Freshness fix DONE + flown (`results/stage5_s60/hover_fix/README.md`: no flicker, gate PASS).

- S61 (launch 20261117-182940, cap $3): owner note N1 acted on and closed (JOURNAL). C1 fixed (d7c637cb20, gz model info uses the flown model). B.1: INDI step overshoot CONFIRMED on seeds 2-3 (12.8-14.2 %, settle 655-870 ms; PID 0 %, 380-412) `results/stage3_s61/README.md`. Mechanism: D-RATE-LEAD feedback-only -> closed rate loop dominant pole 12.6 rad/s (flight fit 80 ms + 22 ms, a_f = 0.48 nu); linear model `bench/att_step_model.py lead` reproduces flight (15.4 %). B.2: G2-STEP written in GATES.md (roll/pitch OS <= 5 %, settle <= 450 ms; yaw OS <= 5 %, settle <= 1350 ms). B.3: D-S3-ATT-STEP = setpoint lead nu += c r_dot_f (c = lead_scale K tau_c), model 0.6 % / 388 ms; feedback loop (rate G2) unchanged. Model second key T124 AGREE (overshoot, poles; settle differs at the 2 % band edge, both pass), README item 5.
- S64 (2026-11-17): route check 64; G2-STEP first formal test 9/9 PASS at 800 Hz (results/g2_step_s64); r_dot_f hover pre-look clean; G3-G8 draft + review amendments in GATES.md.
- S62-S63 STATE detail moved (S64):
  S62 (launch 20261117-183951, cap $3): D-S3-ATT-STEP CODED da64bc26b3 (T125; model test OS 0.51 % vs 11.1 % without,
     break-checked), second key T126 AGREE-WITH-ISSUES (yaw-filter toggle spike -> fixed b8866cd4b1 + test, break-checked;
     rest minor, `design/t126_second_key_att_step_s62.md`). Flown 12 INDI flights seeds 1-3 (`results/stage3_s62/README.md`):
     OS 0.2-1.0 %, roll/pitch settle 358-394 ms, yaw 920-936 ms, all within G2-STEP; torque rejection kept (roll 11.8 vs 12.9).
     T127 metric key AGREE (27/27 values, `design/t127_second_key_metrics_s62.md`), but truth != estimate on 2 flights: A-28.
  S63 (launch 20261117-185813, cap $3): A-28 CLOSED (`results/stage3_s63/README.md`): r/p est-truth grows 0 -> +0.22 deg
     0.6-1.5 s after the step (stock EKF tilt while accelerating sideways), same under PID; yaw standing bias 0.5-1 deg.
     G2-STEP measurement definition written in GATES.md (t_on on setpoint crossing, window ends 50 ms before return step,
     pass on estimate + truth overshoot, est error reported apart). T127 key updated: S62 est OS 0.25-0.97 %, r/p settle
     339-371 ms, yaw 899-914 ms, truth OS <= 0.85 %. A-29 parked (0.14 deg in-band dip, seed3 roll). T128 primary script.
     T128 primary `bench/g2_step_metrics.py` (+7 tests) AGREES with the key 9/9 (`design/t128_g2_step_metrics_s63.md`).

## S44-S64 history stubs moved from STATE.md (2026-11-17, owner token-economy restructure)

S44-S46 detail moved to JOURNAL.md (S51). Derived G1 1757/1640/205 in `bench/params/quad5in_indi_g1.params`; `bench/pretest_gate.py` in use. S47-S48 detail moved to JOURNAL.md (S53): yaw limit cycle fixed by derived G2_Y 27; low roll PM explained by K_R/P_att + motor lag.
S49-S53 detail moved to JOURNAL.md (S56): lead MC_INDI_LEAD 1, ACT_TC 0.05 defaults; roll/pitch M3a PM 59-87.
S54-S56 detail moved to JOURNAL.md (S58): D-YAW-INV coded, yaw M3a 800 Hz PM 88 / GM 18.4 / Ms 1.6; roll 400 Hz PM 84.
S57 detail moved to JOURNAL.md (S60): roll M3a anchors 800/400/267 + measured-rotor anchor PM 77.5; G2 table deferred.
S58-S59 + route check 59 detail moved to JOURNAL.md (S61): stage-3 items 1-4 coded, second-keyed, flown (hover gate PASS);
   opus review of the stage-3 safety diff deferred to one combined review with the stage-5 slice, before any freeze.
S60 detail moved to JOURNAL.md (S62): stage-5 hover slice coded (T122), flew, gate PASS; T123 deviations in `design/t123_second_key_s60.md`.
S61 detail moved to JOURNAL.md (S63): step overshoot mechanism, G2-STEP thresholds, D-S3-ATT-STEP designed + keyed.
S62-S63 detail moved to JOURNAL.md (S64): D-S3-ATT-STEP coded+flown (OS 0.2-1.0 %), A-28 closed, G2-STEP measurement
   definition, primary `bench/g2_step_metrics.py` + key `bench/t127_step_metrics_key.py` AGREE.
S64 (launch 20261117-190447, cap $3): route check 64 (T129, `design/route_check_64.md`): drift = no G3-G8 test text,
   inner-loop work not time-boxed; acted. G2-STEP FIRST FORMAL TEST 9/9 PASS at 800 Hz, HEAD 360c9ae453 clean, key AGREES
   (`results/g2_step_s64/README.md`, GATES.md). r_dot_f pre-look (`results/stage3_s64/README.md`): no hover effect
   (motor HF RMS 2.7e-4 lead on/off); acro needs a stick-noise model (G4 build item). G3-G8 draft T130
   (`design/gates_g3_g8_draft_s64.md`) reviewed, amendments in GATES.md (T/W 7.3: saturation corners sized on hover).
- S66 (2026-11-17): T132 second key AGREE; N2-A triage applied; G1.5 pre-test of 5 disturbance profiles on quad5in found the wrench acting 2x (A-31 open, blocks disturbance results).
- S67 (2026-11-17): A-31 closed: server.config already loaded ApplyLinkWrench, injector added a 2nd (fix fc8905cf90, second key AGREE, 5 profiles re-flown 1x); errata.md E-1 created.
- S67: A-30 re-fly: identical 400 Hz INDI runs differ, S64 seed1 not reproduced -> Q5 (non-blocking). A-9: no path in new module (read), archive-only candidate.
- S67: INDI 400 Hz same-seed spread (11 runs): rise 4 / settle 15 ms / OS 0.7 pts, same at speed 1 and 4; S64 seed1 not reproduced (A-30 open, Q5 addendum).
- S68 (2026-11-17): clean-HEAD re-fly of G2-STEP (`results/g2_clean_s68`): 400 Hz 9/9, 800 Hz same-seed spread 14.5/39 ms/1 pt; dirty-tree lead not needed; A-30 bounded.
- S68: A-9 CLOSED archive-only: second key AGREE, guard gtest OmegaFfIndependentOfYawRate break-checked (35b313d2a5).
- S68: G2-STEP batches since S62 flown without --sched (G1.6 flags): T147 re-measures the same-seed spread with them.
- S68: A-30 traced to a determinism regression since S32 (A-32): G1.6 cmd same-seed rise spread 0.8 -> 11.5 ms, not INDI-specific, not sim v2.
- S69: route check 69 (`design/route_check_69.md`): 0/8 gates; stop anomaly chasing, slice 2 in S70, 2nd mode + combined review S71.
- S69: A-32 PARKED: no regression; same-seed spread comes from parallel host load (seq 1.5 ms = S32, 5-parallel 11 ms). G1.6 protocol note (sequential) in GATES.md.
- S69: A-30 PARKED: INDI 400 Hz sequential same-seed spread rise <= 4.3 ms / settle 7.5 ms / OS 0.53 pt.
- S69: N2 closed (A done S66, B = A-9 closed S68, C = Q5 + A-30/A-32 resolved S69). Slice-2 plan `design/slice2_plan_s69.md`.
- S69: STATE.md S65-S68 session notes moved here:
   S65 (launch 20261117-192006, cap $1.5): item (3) DONE T131 (`design/g3_hooks_check_s65.md`): loop delay ABSENT;
   vibration PARTIAL (rotor sinusoid only, no wideband IMU scale); GNSS latency PARTIAL (param SENS_GNSS0_DELAY only,
   no sample delay; draft says EKF2_GPS_DELAY: fix GATES text); eRPM latency EXISTS; drop RNG seed FIXED (hpp:131),
   must become per-run. Item (2) CODED T132 (`design/t132_disturbance_c2_s65.md`, self-test OK, re-run S65): profiles
   sized from SDF (quad5in 0.610 kg, payload 25 % W, gust 10 % W); quad5in CdA 0.012 / CoP 0.02 UNVERIFIED; UNKEYED.
   S66 (launch 20261117-231245, cap $3): T133 second key of T132 AGREE (note errata appended). N2-A triage DONE
   (`design/n2a_triage_s66.md`; A-2/A-15 closed, A-5 archive-only, A-1/A-3/A-7 parked, A-4/A-6 open). T134 G1.5
   pre-test 5 profiles (`results/g15_dist_s66/`): airframe line and wrench peaks OK; open: payload_add thrust +50 %
   vs 25 % force, com_shift roll excursion +79 deg at onset+26 s, torque_steps pitch/yaw sign (FLU vs FRD?).
   T136 (`results/g15_dist_s66/investigation.md`): wrench acts 2x on the vehicle (force and torque) and com_shift
   loses it once at +26 s -> A-31 OPEN, blocks every disturbance result. torque_steps pitch/yaw sign explained
   (world ENU = body FLU at spawn yaw; PX4 FRD flips y, z): document in disturbance.py, not a defect.
   T137 read gz-sim 8.15.0 ApplyLinkWrench (`design/a31_wrench_source_s66.md`): one-step msgs summed per step, no
   mechanism for 2x found. NEXT S67: (a) A-31 first: the 4 tests at the end of that note (payload_add alone first); fix + second key + re-run g15_dist_s66/fly.sh; N2-B (A-9 unit test on new module) and N2-C (A-30 identical 400 Hz re-fly,
   share with A-4 speed 1/4 test); then item (1) slice 2; build hooks (loop delay, GNSS sample delay, per-run drop
   seed, IMU noise scale) as one simulator task with second key.
   Results rule (N1 D): commit metrics/run.json/README of every run in the session that produced it. Next route check: S69.
Standing rule (S35): bench param sets carry SENS_BAR_AUTOCAL 0.
   S67 (launch 20261117-232529, cap $3): A-31 lead: `src/modules/simulation/gz_bridge/server.config:14` already
   loads ApplyLinkWrench (default.sdf has no plugins, gz_env.sh sets GZ_SIM_SERVER_CONFIG_PATH); disturbance.py adds a
   2nd instance at runtime -> 2x. DONE: fix fc8905cf90, second key AGREE, A-31 CLOSED, 5 profiles re-flown 1x
   (`results/a31_fix_s67/`), errata.md E-1 created. A-30 re-fly (`results/a30_refly_s67`): identical runs DIFFER
   -> Q5 open (non-blocking, rec. G1.6 protocol on INDI). A-9: no path in new module by reading
   (`design/a9_new_module_s67.md`); module publishes no jerk ff (omega_ff unused): trajectory lag, stage-5 item.
   T143 (`results/g16_indi_s67`): INDI 400 Hz same-seed spread rise 4 / settle 15 ms / OS 0.7 pts, equal at speed
   1 and 4; arm instant varies 0.76 s (wall clock); S64 seed1 outside all 11 runs (Q5 addendum).
   T144 log diff: params identical, S64 binary from a DIRTY tree (f183dad) = leading cause of the outlier.
   S68 (launch 20261117-234230, cap $3): T145 clean-HEAD re-fly (`results/g2_clean_s68`): 400 Hz table 9/9, seed1 roll
   rise 192.5 (dirty tree not needed as cause); 800 Hz same-seed spread 14.5/39 ms/1 pt, < 1/2 limit margin; A-30
   bounded, Q5 addendum 3. T146: A-9 CLOSED (2nd key AGREE, guard gtest break-checked, 35b313d2a5).
   T147-T150: same-seed spread persists with --sched, PID, v2true, eRPM-lost, and on the EXACT G1.6 cmd (sim v1):
   rise 11.5 ms at HEAD vs 0.8 ms at S32 under both metrics -> A-32 OPEN, G1.6 FINAL regressed (Q5 addendum 5);
   on v2 the spread sits mostly in the first step.
- S70: Q5 closed (A-30/A-32 parked: same-seed spread from parallel host load; G1.6 runs sequential, GATES note s69). Moved from QUESTIONS.md.
- S70: T156 thrust-gap pre-test (7 flights): INDI outer loop z 0.31/0.37 m at 4x0.85 (A11 confirmed), stock 0.01 m; second key T157 agrees <= 0.006 m. D-GAP proposed (blend on collective); review brief written.
- S71: D-GAP opus r1 BLOCKING (edge semantics) -> amended; sonnet r2 wording fixed; D-GAP ACCEPTED; implementation brief design/dgap_impl_brief_s71.md.
- S72: D-GAP implemented (T160 sonnet, 3481bdcf9e firmware, 41d44d461a tests incl. 8 + 1 break-checked); orchestrator fixed reset() model-path init (u + b). gap085_indi_htoff standing dz 0.025 m (was 0.372), loss08_indi 0.056 m; haiku second key 0.020 / 0.053; A-33 opened (loss08 held a_c-a_f 0.158 m/s2, control error 0.040 m). Land/re-take-off scenario missing in runner.
- S72: A-33 explained: loss08 standing 10.4 deg inner-loop attitude error (sp vs actual), outer loop masks it; vertical leak g(1-cos). HTE ruled out. Moves to stage 3 (rate-loop gap under a weak motor).
- S73 (launch 20261118-005601, cap $1.98): A-33 CLOSED: cause = rate-loop blend MC_INDI_ACT_BLD default 0 (no integral action, lesson 9); loss08 with blend 0.3/1.0 removes the standing 10.4 deg attitude error (sp-vs-actual 0.05/0.06 deg), dz last10 +0.037/+0.024 m, max dev 0.107/0.046 m. New script bench/a33_tilt_split.py (reproduces T162 split, second key). D-RATE-BLD proposed.
- S74 (launch 20261118-010057, cap $1.51): route check 74 (sonnet, design/route_check_74.md): root = decision 2 (integral path per measured-state loop); merge rate-blend and D-GAP margins into one campaign; RC stick path + PVA slice before land/re-take-off; default change deferred until margins (lesson 10). No escalation.
- S75 (2026-11-18): D-RATE-BLD-EDGE decided from code read: rate blend keeps snap-to-gap on inactive edges, D-GAP keeps freeze; D-RATE-BLD precondition 2 settled, unit tests remain. No agent (cap $1.16).
- S77 (2026-11-18): A-34 traced (blend and host load ruled out; setpoint lead da64bc26b3 likely, closing test open). D-RATE-BLD preconditions 2-3 met: edge + weak-motor closed-loop tests committed 499e1df991. 400 Hz rate M3a flown (results/stage3_s77_400).
- S77: 400 Hz rate M3a PM 70 / GM 13.3 dB / DM 51 ms at tb 0 and 1.0 (results/stage3_s77_400); outer-loop injector missing, next S78 item.
- S78 (2026-11-18): A-34 model test (T166): setpoint lead reproduces the PM/f_c shift within 1.3 deg/0.07 Hz, bin criterion fails on a common model offset -> A-35 opened; A-34 still needs the da64bc26b3^ flight.
- S78: second key of the margin-model lead (T167) OK; self-test now pins the firmware Tc literally, break-checked.
- S79 (2026-11-18): route check 79 (design/route_check_79.md): A-34/A-35 were a detour under the RC74 rule, parked; D-RATE-BLD accepted, default MC_INDI_ACT_BLD 1.0 s committed a94d5c181a.
- S80 (2026-11-18): pending run metrics committed (194109b460); RC/manual stick-path stub briefed (design/brief_rc_stub_s80.md), not launched (cap $1.05).
- S82 (2026-11-18): T169 stick-path stub finished by orchestrator: expo inverted, 50 Hz grid pacing; altctl/posctl flown PID and INDI (results/stage5_s81_stick/README.md). T170 outer-loop accel-break injector launched (design/brief_velbreak_s82.md).
- S82: T170 outer-loop break injector (D-G2-PINJ) committed; z pre-test PM 54.4 deg at 0.60 Hz (results/stage5_s82_velbreak/README.md).
- S83 (20261118-043259): T171 injector second key AGREE WITH MINOR; T173 minors fixed (a38533428f, 907f57510d); velbreak re-fly DLY 20 NP 5: z PM 57.3 deg tb 1.0, 59.1 deg tb 0.33, D-GAP velocity-break overturn not met (cdc5f03713); T172 stick second key DISAGREE (3 rows at 33 Hz before grid pacing, README overclaim), 4 rows re-flown in results/stage5_s83_stick.
- S84 (20261118-044520): route check 84 (design/route_check_84.md); G1 marked PASSED under the owner's S50 rule (G1.7 self-test re-run ALL PASS); G2 cell table in GATES.md; T174 stage-output accel break briefed (design/brief_accbreak_s84.md) and launched.
- S84: T174 stage-output break committed (20b1c9c48b, 292b71c333), z pre-test PM 58.7 deg at 0.62 Hz (outer loops dominate, as predicted by INDI cancellation; HF bins incoherent); D-G2-PINJ-OUT addendum; T175 second key launched.
- S84: T175 second key AGREE WITH MINOR; param texts fixed, PT 1 bench limits recorded in results/stage5_s84_accbreak/README.md.
- S84: HF output-break re-fly 1.5-10 Hz: abs(L) <= -10 dB, no -180 crossing (unkeyed); pinj_csv --margins crashes without crossover in band (to fix). Session end ~$2.6.
- S85 (launch 20261118-045636): HF FRF second key AGREE; margins_est DC-term defect fixed, S84 pt1 re-scored 61.3 deg; hole_report.py built (evidence limit 1); injector AX=0 identity flights within same-seed spread.
- S86 (2026-11-18): hole_report fixes T179 (98e977a9f0); G2 outer runner + z cells PM 62.8-63.7 deg serial; parallel flights break evidence (holes); xy no-crossover = top_db misread (T181); attitude-break note T180; count check defect at 800 Hz queued (edc562526a).
- S82-S85 notes moved from STATE.md in S86:
  S82 (launch 20261118-042344, cap $3): T169 stick stub DONE (a1f2b3b124, 53b38dd54e; results/stage5_s81_stick/
  README.md): altctl/posctl fly on both stacks, 50 Hz grid pacing; PID = INDI gain 0.86 (stock setpoint shaping).
  T170 DONE (3b7af1282f fw, 37f3ab90a5, 9278260a9d): MC_INDI_PINJ_* injects at the INDI stage INPUT = velocity/
  position break (INDI accel loop closed), z PM 54.4 deg at 0.60 Hz, tb 1.0, pre-test only (results/stage5_s82_
  velbreak/README.md lists open items). The G2 accel-loop break (d at stage output) is still missing.
  NEXT S83 (cheap first): (1) haiku second keys: stick stub (to brief_rc_stub_s80.md) and injector (to
  brief_velbreak_s82.md); (2) re-fly velbreak with DLY >= 15 s / NP 5 at tb 1.0 and tb/3 (D-GAP overturn test);
  (3) G5 stick metric vs vehicle_local_position_setpoint; then (e) or PVA slice.
  S83 (launch 20261118-043259, cap $3): injector second key AGREE WITH MINOR, minors fixed (a38533428f fw,
  907f57510d pinj_csv self-test); velbreak re-fly z PM 57.3 (tb 1.0) / 59.1 deg (tb 0.33): D-GAP PM overturn NOT
  met (cdc5f03713); stick second key DISAGREE (33 Hz rows pre-grid, README overclaim) -> 4 rows re-flown (B83b).
  S84: RC84 done (design/route_check_84.md), G1 PASSED, G2 cell table in GATES.md, T174 launched.
  S84 HF output-break re-fly (1.5-10 Hz): abs(L) <= -10 dB, no -180 crossing (UNKEYED, results/stage5_s84_accbreak/
  README.md); pinj_csv --margins raises when no crossover in band (fix).
  S85 (launch 20261118-045636, cap $3): HF FRF second key AGREE; margins_est LS-phasor DC-term defect fixed
  (5444196ab4): velbreak margins unchanged, S84 pt1 re-scored PM 61.3 deg/0.64 Hz (was 58.7, 7/16 bins);
  pinj_csv reports no-crossover; bench/hole_report.py (evidence limit 1) built, hf + posctl PASS, second key T178;
  AX=0 identity flights: no change beyond same-seed spread (results/stage5_s85_identity/README.md).
- S87: STATE trimmed; S83-S85 task rows (B83 velbreak PM 57.3/59.1, T173, B83b stick 50 Hz, RC84, T174 accel break pt1 z PM 58.7, T175-T178 keys and hole reporter) are DONE, details in their result READMEs.
- S87 (20261118-051310): T182 hole_report count fix (c5b5a897e9) + T184 key AGREE WITH MINOR; T183 key of T181 AGREE; B87 xy G2 cells serial AMP 0.08 TP 20: PM 49.7-64.8 deg, GM ~18-19 dB (30c012bc7c); T185 review of attitude-break note: 0 blocking, 2 major test gaps.
- S88 (2026-11-18, cap $1.75): hole_report D-HOLE-EXCESS (dd9dd0705e, keyed T188, slow-topic fix 688f198ab2); last_bin_db rename 5243e845b9; re-fly of two G2 cells, both holes PASS (e73e39e9ec).
- S89: RC89 filed (stop tooling, freeze hole_report); T189 re-run: all serial G2 cells PASS, 3 FAIL = parallel pre-test only; D-HOLE-FREEZE.
- S89 STATE trim: task rows T179-T184, T186-T188, B86, B86z, B88 done (outputs listed in LEDGER.md and the S86-S88 entries).
- S90 (2026-11-18): G2 attitude break at the rate setpoint implemented (b41dd6ec81, T190) and keyed (T191, 3 MAJOR on gating/restart fixed 2bed1ae95a, test checked by breaking it); not flown yet.
- S91 (2026-11-18): attitude-break pre-test PASS at RAMP 0.06 (roll 400 Hz PM 56.6 deg, GM 22.0 dB, f_c 1.32 Hz); ratesp_csv.py extractor + key T193 (bbb52f0982, 5da12a76d8); cells batch B91c launched.
- S91: attitude-break G2 cells roll/pitch/yaw x 400/800 Hz all above thresholds (PM >= 56.6 deg, GM >= 21.9 dB), 9d28ea5b0a.
- S92 (2026-11-18): G2 attitude-break reported cell roll 267 Hz (D-RATE267): PM 55.5 deg, GM 21.8 dB, DM 0.113 s; hole_report count-disagree flag only (2 jittered intervals, 0 missing), 259cb251d0. A first attempt at 250 Hz was rejected by the runner (choices 800/400/267) and discarded.
- S93 (2026-11-18): STATE.md trimmed; moved S86-S92 status lines and done task rows here:
  S86 (launch 20261118-050243, cap $3): T179 hole_report fixes DONE 98e977a9f0; G2 outer runner
  results/stage5_s86_g2outer/fly.sh (README: findings 1-3); z cells PM 62.8-63.7 deg; G2 cells fly ONE AT A TIME
  (parallel -> holes); xy no-crossover = top_db misread (T181 UNKEYED); attitude-break note design/attitude_break_s86.md
  (T180, unreviewed; check its L_att identity: L_att = A L_rate/(1+L_rate) expected).
  S87 (launch 20261118-051310): T182 count fix c5b5a897e9 + T184 key AGREE WITH MINOR; T183 key of T181 AGREE;
  xy re-fly B87 (stage5_s87_xy, hover_xlong 150 s, AMP 0.08 TP 20).
  S88 (launch 20261118-053836, cap $1.75): (1)(3) done (T186, T187, D-HOLE-EXCESS); (2) B88 done; T188 key closed.
  S89 (launch 20261118-054540, cap $1.05): B88 metrics committed 51a0a42817; T189 all serial G2 outer cells PASS
  hole_report (3 FAIL = S86 parallel pre-test, not evidence); D-HOLE-FREEZE; RC89 (design/route_check_89.md): STOP
  tooling, cosmetic re-flies, anomaly chases.
  S90 (launch 20261118-081145, cap $3): attitude break (MC_INDI_INJ_PT 1, amp MC_INDI_INJ_RAMP) implemented
  b41dd6ec81 + fix 2bed1ae95a (T191 key: 3 MAJOR resolved, design/attitude_break_s90_key.md); 7/7 Indi suites pass,
  SITL builds. Check script bench/attitude_break_check.py (self-test 6/6, never run on a real ULog).
  S91 (launch 20261118-082350, cap $1.98): attitude-break pre-test PASS (RAMP 0.06; roll 400 Hz PM 56.6 GM 22.0
  f_c 1.32, delay margin 0.119 s); extractor bbb52f0982 keyed; B91c 6 cells DONE 9d28ea5b0a: PM 56.6-73.8,
  GM 21.9-34.3 dB, all checks/holes PASS (table in stage5_s91_attbreak/README.md).
  S92 (launch 20261118-083617, cap $1.28): 267 Hz reported roll cell DONE 259cb251d0 (PM 55.5, GM 21.8; holes
  count-disagree flag only, not re-flown). No agent launched (cap below 2x sonnet cost).
  | B87 | xy cells AMP 0.08 TP 20 hover_xlong, serial | host | results/stage5_s87_xy/ (fly.sh PT AX RATE SEED) | DONE 30c012bc7c: 16 cells PM 49.7-64.8, GM 18.2-19.3 dB, f_c 0.27-0.34 Hz; holes 15/16 after re-fly 66589220a9 (pt0_ax2_r400_s1: count check + 89 Hz limit, tool fix S88) |
  | T185 | review attitude-break note vs code | sonnet | design/attitude_break_s86_review.md | DONE: 0 BLOCKING, 2 MAJOR (add call-site test at McIndiRateControl.cpp:231; replace circular x-y-d check by logged rate_sp_dot vs derivative of logged x), 10 MINOR (gate off in ACRO; use hover_xlong; outer loop closed below ~0.3 Hz). Amend note, then implement |
  | T189 | S89 hole_report re-run | haiku | results/stage5_s85_holes/rerun_s89.md | DONE: serial cells all PASS |
  | RC89 | route check 89 | sonnet | design/route_check_89.md | DONE |
  | T190 | S90: amend attitude-break note (sec 8) + implement PT=1 rate-sp break | sonnet | design/t190_impl_log.md | DONE b41dd6ec81 fw, d7bb0e7bd9 check script, 947d510823 note; 7/7 Indi test suites pass (Docker, re-run by orchestrator). UNVERIFIED: check script on real ULog, AX=0 real-log bit-identity |
  | T191 | second key of b41dd6ec81 vs note | sonnet | design/attitude_break_s90_key.md | DONE: 0 BLOCKING, 3 MAJOR fixed 2bed1ae95a |
  | B91 | S91 attitude-break pre-test, roll 400 Hz, RAMP 0.03/0.06 | host | results/stage5_s91_attbreak/README.md | DONE 5da12a76d8: PASS for RAMP 0.06, PM 56.6 GM 22.0 f_c 1.32 |
  | T192/T193 | ratesp_csv.py extractor + key | sonnet | design/t193_ratesp_key.md | DONE bbb52f0982, AGREE WITH MINOR (interior d==0 gaps not counted) |
  | B91c | attitude cells ax2/3 r400, ax1-3 r800, RAMP 0.06, serial | host | results/stage5_s91_attbreak/README.md | DONE 9d28ea5b0a |
  | B92 | S92 (launch 20261118-083617, cap $1.28): 267 Hz reported roll cell (D-RATE267), RAMP 0.06 | host | results/stage5_s91_attbreak/README.md | DONE 259cb251d0 |
- S93 (2026-11-18): attitude-break linear model L_att_indi/L_att_pid (85fb907177, T194); model PM 15 deg high -> A-36; closed outer loop O(s) derived independently (T195) and added (9df899212c): PM within 0.3 deg of all roll cells, GM residue 1.6-4.6 dB (model conservative) kept open; PID model-only reference at the break recorded (7b328f45a4 and following).
- S93: route check 93 (design/route_check_93.md): report G2 next, then G3-G8/G5 text + opus review, then identification slice early; stop model refinement.
- S94 (2026-11-18, launch 20261118-092623, cap $3): G2 report section report/g2_margins.md (T196, preliminary, gate not passed); G3-G8 FINAL text in GATES.md with D-GATES-G3G8 (T197): no accuracy quota, owner ranges kept, hooks MISSING: loop delay, GNSS latency, G5 event injectors, per-run sampler.
- S94: design/delay_line_hook_s94.md (T198, sonnet): loop-delay/GNSS-latency hook design for S96; unverified: GNSS path, world step.
- S95 (20261118-093647): combined opus review T198 (stage-3 safety, NOT BLOCKING, item 5 autotune never coded) + T199 (stage-5 D-GAP slice, BLOCKING edge thrust step, 4 MAJOR; BLOCKING to adjudicate S96). design/review_s95_*.md.
- S96 (20261118-094323): T199 BLOCKING confirmed (commanded collective passed as measured mean_u); D-GAP findings 1-5 fixed bf44ece093 with 5 break-checked tests; autotune not started with INDI b7a171b4b5; watchdog receipt time 4385e8f56a; second key T202.
- S96 moved finished task rows from STATE.md:
  | T194 | S93 (launch 20261118-091231, cap $3): attitude-break linear model L_att_indi/L_att_pid + identity self-test + model-vs-measured table (note sec 5) | sonnet | design/t194_att_model_log.md, results/stage5_s91_attbreak/model_vs_measured.md | DONE 85fb907177 f38ecf5ba3: tests 5/5; model PM ~15 deg above measured -> A-36; S93 outer-loop factor O(s) brings delta to 2-3 deg (unkeyed) |
  | T196 | S94: G2 report section draft | sonnet | report/g2_margins.md | DONE 4542ca1d83 (2 numbers spot-checked) |
  | T197 | S94: G3-G8 final test-text proposal + hook check | sonnet | design/gates_g3_g8_final_s94.md | DONE 18af6e3a66 (8 decisions in GATES.md) |
  | T198 | S95 (launch 20261118-093647): opus review stage-3 safety items code vs design/stage3_items_note.md + D-S3-* | opus | design/review_s95_stage3_safety.md | DONE: NOT BLOCKING; MAJOR item 5 autotune start never coded (rc.mc_apps starts autotune with INDI on); MINOR: watchdog uses publisher stamp (use receipt time), PID-after-INDI start not refused, no start-refusal test |
  | T199 | S95: opus review D-GAP + landed/take-off handling in mc_indi_pos_control/indi_accel_control vs DECISIONS D-GAP | opus | design/review_s95_stage5_slice.md | DONE: BLOCKING (bypass->active edge thrust step of b, :252-255), 4 MAJOR (step on telemetry return :291 accel lib; gap not removed in altitude mode; anti-windup ignores mean_u limit; T123 filter-reset bug unfixed), MINOR tb=0 erases b; no tests. Orchestrator spot-check S95: :252 passes _coll_meas when fresh_thr, so BLOCKING may be misread -> adjudicate first in S96 |
  | T201 | S96: stage-3 item 5 autotune not started with MC_INDI_EN=1 (rc.mc_apps) + rate watchdog on receipt time | sonnet | design/t201_autotune_watchdog_log.md | DONE b7a171b4b5 4385e8f56a (diff read by orchestrator; SITL start test MC_INDI_EN=1 MC_AT_EN=1 not run; start-refusal test needs SITL shell, open) |
  | T195 | key of A-36: independent outer-loop factor from firmware source + flown params | sonnet | design/t195_att_outer_key.md | DONE: agrees; O(s) in margins_models 9df899212c; PM within 0.3 deg, GM residue open (A-36) |
- S96: T202 key found 2 MAJOR in bf44ece093 (vacuous telemetry-continuity test; stock integral in first INDI cycle); fixed 25e420b155, dff2b7a805.
- S97 (launch 20261118-095515): T203 minor fixed de7c598e1e (reset gated on fresh inputs); D-ALTCTL-Z decided (ALTCTL served by a z-only INDI stage, stock tilt kept) and implemented (T204) 52beee60e5; second key T205.
- S97: T205 key: no BLOCKING; double poll removed; DESCEND included in z-only scope (DECISIONS); coverage MAJORs carried to S98.
- S97 STATE trim: moved from STATE.md:
  S93 (launch 20261118-091231, cap $3): attitude-break model + outer-loop factor (T194, T195): PM matches measured
  within 0.3 deg; GM model 1.6-4.6 dB conservative (A-36 residue, linked A-35); PID model-only ref in
  results/stage5_s91_attbreak/model_vs_measured.md.
  RC93 (design/route_check_93.md, accepted): stop model refinement, tooling keys, cosmetic re-flies; A-36 residue
  accepted as conservative and bounded. S94 DONE: G2 report section (report/g2_margins.md, 4542ca1d83; empty cells:
  PID measured, model-only at HEAD, yaw/pitch v2, 267 Hz outer, telemetry latency value, 2nd key S86/S87/S91);
  G3-G8 FINAL text in GATES.md + D-GATES-G3G8 (18af6e3a66). NEXT S95: combined opus review of stage-3 safety diff +
  stage-5 slice (~$1.1, launch first, cap >= $2.5). S96: sim hooks MISSING per design/gates_g3_g8_final_s94.md sec 1
  (shared sim-time delay line for loop delay + GNSS latency; G5 event injectors; per-run sampler g3_sample.py;
  telemetry-drop seed per run), each with G1.5 check + second key. Delay line designed: design/delay_line_hook_s94.md
  (check world step and GNSS path first). S97: yaw cell + first identification slice.
- S98 (2026-11-18): RC98 (stop coverage, defer harness to stage 7, D-G7-HARNESS); T206 lib mutation tests b6e95f88c4 + module gate c32d022f9e; P98 G5 pre-test gap 0.85: standing z error ~0 in offboard, ALTCTL, EN+AT_EN (S70: 0.33 m), keyed K98 from raw ulg.
- S98 STATE trim, moved: S96 DONE: T199 BLOCKING confirmed + all 5 findings fixed (T200), autotune/watchdog (T201); second key T202 / (design/t202_dgap_fix_key.md): its 2 MAJORs fixed by orchestrator 25e420b155 (vacuous test, break-checked) and / dff2b7a805 (integral hoist, compile-only). Open MINORs: lower mean_u limit untested; lagging mean_u at reset untested; / permanently saturated motor freezes b (no gap tracking): state in report limits. / dff2b7a805 keyed OK (T203, design/t203_integral_hoist_key.md); MINOR: want_indi true + stage bypass on stale / fresh inputs. / | T200 | S96 (launch 20261118-094323): T199 BLOCKING CONFIRMED by orchestrator (_coll_meas = vehicle_thrust_setpoint, commanded, passed as mean_u). Fix findings 1,2,4,5 + 3 (integrator reset only when INDI ran) in indi_accel_control + mc_indi_pos_control, tests first with break-checks | sonnet | des / | T204 | S97: D-ALTCTL-Z implement | sonnet | design/t204_altctl_z_log.md | DONE 52beee60e5 + tests 1d827d62be (diff read; 5/6 fail-before, break-check 3 fail; module compile-only; closed-loop test is regression-only) | / | T205 | S97: second key on 52beee60e5 + de7c598e1e | sonnet | design/t205_altctl_key.md | DONE: no BLOCKING; double poll removed + DESCEND scope noted (S97); OPEN: 2 MAJOR coverage (no module harness for T203 gate / z_only derivation / want_indi; lib mutations at tilt, guard order, 0.1 threshold, m / | T202 | S96: second key on bf44ece093 vs review findings 1-5 | sonnet | design/t202_dgap_fix_key.md | DONE: no BLOCKING, 2 MAJOR fixed 25e420b155 dff2b7a805 |
- S99 (2026-11-18): T207 sim hooks SIM_GZ_SEED/SIM_GZ_IMU_NSC fdcc54ed63 9d48cea369, G1.5 check 93e20fd849 (gyro x3, drops per seed; accel unverified); T208 G2 rate table: 7 of 12 required cells missing at HEAD; P99 rate pre-test launched.
- S99: B99 G2 rate batch v2 at HEAD 10/10 PASS (worst GM 13.1 dB, PM 68.2 deg, DM 46 ms), with P99 all 12 v2 800/400 cells covered x2 seeds; not yet second-keyed; model-only cells and PID M1 reference open.
- S99 STATE trim: dropped S97 ALTCTL recipe (in results/stage5_s70/README.md), T206/P98/K98 rows (S98 entry), S38 GM-jump note (results/stage2_s38/gm_jump_check.md).
- S100 (2026-11-18): K100 second key of B99+P1/P2 rate cells 12/12 agree (9621a25d3d); P100 model-only pre-test PASS (db536a8c01); B100 model-only batch launched.
- S101 STATE trim (moved from STATE): S36 G1 FINAL/T73 lines; S98 D-pretest_gate window note (use pretest_gate only on stationary scenarios or end window at fault; S98 (0) explained); RC98 order (a)-(c); rows T207, T208, P99, B99, K100, P100 (all DONE, commits in rows above). Rule (c) "ask owner to narrow G2 if hooks/G2 verdict not done by S101": resolved without question, all 24 required INDI rate cells (v2 + model-only, 800/400, x3 axes) flown and passing at HEAD; remaining G2 work (PID reference, linear cross-check) is not a narrowing of the gate. Delay-line hook belongs to G3.
- S101: B100 model-only batch 10/10 PASS + P100 2/2: worst GM 10.12 dB (roll400_s2), PM 70.8 deg (pitch400_s2), DM 39.7 ms; torque_check MODEL_ONLY_VERIFIED on cells.
- S102: (ii) PID M1 has no recipe (gyro-break sim_inject hook from design/stage2_margins_s35.md never built); deferred behind G3 delay-line hooks (iv), H102 sonnet implements A1+A2.
- S102: delay-line hooks A1+A2 built (H102), second-keyed (K102: M1 init order, M2 IMU clock fixed), committed c6ba02609f; runner --dly-act/--dly-imu; pre-test V102: IMU delay exact, actuator delay unverified -> A-37.
- S103 (2026-11-18): RC103 (design/route_check_103.md); A-37 closed (a9e5066a55 release-age windows, results/a37_actlag_s103): DLY_ACT lag d+[0,1.25 ms) in flight at 5 and 10 ms, usable in G3.
- S103: G5 POSCTL gap pre-test (results/g5_posctl_s103): -0.09 m standing truth-z error, A-38 opened (setpoint re-latch vs z-path, ulog check next).
- S104 (2026-11-18): A-38 closed (results/g5_posctl_s103 README A-38 section, a38_check.py): setpoint not re-latched, est-sp 0.000 m after the 0.85 gap; -0.07 m truth error is a pre-existing estimator vertical offset. Next: G2 verdict note (iii).
- S105 (2026-11-18): G2 verdict note for the INDI v2 rate loop (design/g2_verdict_rate_s105.md): 16 roll/pitch cells cross-checked against margins_models.py within tolerance (dPM<=4.7 deg, dGM<=1.86 dB); 8 yaw cells open (no yaw model); filter models verified against source; A-21 shown not to apply to v2.
- S106 (2026-11-18): hook B GNSS delivery delay SIM_GZ_GPS_DLY (d52576b02a, H106); second key K106 found SENS_GNSS0_DELAY inert (true timestamp_sample kept by VehicleGPSPosition), fixed 99673b62bd (sample = delivery time at release); M2 flight: true age median 254 ms for 250, EKF time error +4 ms matched (results/gnss_delay_key_s106/README.md). K107 key of the fix.
- S107 (2026-11-18): yaw linear model L_indi_yaw + self-test (b05d07c555); Y107b second key of the law (0 BLOCKING) and yaw cross-check: model-only 4/4 within tolerance, measured-path 400 Hz dGM -9.7/-9.1 dB -> A-39 deferred (gate still passes, GM 15.5 dB); attitude-break cells re-flown at HEAD 6/6 PASS, dPM <= 0.5 deg vs S91 (8ec7d4a95b).
- S108 (20261118-145323, cap $3): D107 draft reviewed: outer-loop G2 cells (S83/S86/S87, 24 cells, PM >= 49.7 deg, GM >= 18.2 dB, unkeyed, no model) had been missed; design/g2_verdict_s108.md + GATES.md G2 table (93f94320d3). Attitude seed 2 not flown (pre-freeze). G108 G3 sampler launched.
- S108: G108 G3 sampler bench/g3_sample.py (238079b24f, self-test 9/9, deterministic); D-G3-SAMPLER; K108 second key launched.
- S108: K108 key of the sampler: 0 BLOCKING, 4 MAJOR (G1-error basis vs drawn inertia, missing gusts, test gaps, saturation share), fixes queued S109.
- S109 (2026-11-18): S108 G2 table edits committed (0e7fa9dd65, left out of 93f94320d3); raw run captures ignored; K108 MAJORs closed (gust floor, G1 error plant-relative k = e / I_scale, mutation guards), keyed; quad5in plant variants (mass, inertia, tau, up/down) with mass x1.3 flight check; K109 key launched.
- S110 (20261118-151204, cap $3): G3 driver bench/g3_run.py (c5acce1b39, self-test 6/6, model_variant mapped: K109 MAJOR closed); found wind, sag, saturation, weak motor, eRPM loss have no runner input -> O110 scenario overrides launched.
- S110: O110 run_scenario.py --scenario-overrides + parametrised gust_x wind, g3_run applies sag/saturation/weak motor/eRPM loss/wind (fc3ef9e626); check flight: wind +y 0.066 N steady, sag command +16 %; K110 key launched.
- S110: K110 key of overrides: 0 BLOCKING, 3 MAJOR (wind drag not air-relative, pre-existing; eRPM loss window too long; weak motor lost when saturation drawn), 3 surviving mutations; fixes queued S111 before the G3 pre-test.
- S111: K110 MAJORs closed b0486b703e (air-relative gust_x drag from gz pose finite diff, timed eRPM loss at drawn offset/duration, motor_fault list so weak+sat both apply, single main-segment anchor, 3 surviving mutations caught). Second key K111 (design/k110_fixes_key_s111.md): 0 BLOCKING, F-1 runner hooks untested -> closed 6e8c4fa474 (erpm_loss_split, fault_apply pinned, 4 mutations caught), F-3 vel-None ticks logged to run.json (unflown), F-5 docs; F-2 pose/clock thread lag 0-1 pose period accepted bounded (wrench logged as applied); F-4 set_param latency between sub-runs MINOR, check in S112 pre-test. Earlier gust_x results not comparable. Nothing flown.
- S112 (20261118-153702, cap $1.75): P112 G3 hook pre-test (2 of 3 flown): wind not air-relative (gz Pose msg class missing), inertia draws invalid ~1/3, eRPM loss starts late (set_param latency), stick draws trip height watchdog; fixes queued S113.
- S113: RC113 filed (single-factor ladder before mixed batches; mass x1.3 stick descent = unattributed probe result; hook stop rule). F113 fixed pose subscriber (late Pose import; positional vel bug), inertia triangle-inequality redraw, aborted-run status (09515cd8ae). Dropped --sched-anchor and set_param-latency work per RC113.
- S113: M113 3 flights: stick_zsine_o6 stabilized falls at the 52 s mode switch for INDI m1.3, INDI m1.0 and PID m1.0 alike (thrust 0.65-0.69 x hover): stick_profile.py hover stick 2*hover_thr-1 ignores the PX4 throttle curve. Set-up fault, not a controller finding; FAULT 3 of P112 explained.
- S114: stick_profile stabilized hover stick fixed from mc_att_control throttle_curve (807fd6a08a; S113 log thrust 0.095 = 0.08 + 0.274*(0.137-0.08) confirms the old map as the cause); K113 MINOR 5, 6 closed 3d8e4b5f29. K114 key + F114 re-fly launched.
- S114: K114 key of 807fd6a08a: 0 BLOCKING, MAJOR thr0 ignores HTE valid flag (fix S115), MINORs (slew, unpinned curve params).
- S114: F114 stabilized stick re-fly: INDI and PID fly through the switch (fix confirmed); A-40 opened (landing 70.3 s inside window).
- S115: K114 MAJOR/MINOR 3-4 fixed 8f57b47f7e (key K115 pending); A-40 closed (no early landing, px4.log time base).
- S116: K115 key of 8f57b47f7e: 0 BLOCKING; MINORs (fallback clamp, run.json source field for all runs, 4 surviving mutations) queued after L116.
- S116: L116 ladder (e97d826b27): 5/9 fly; sag/weak/sat trip height watchdog on stabilized stick (open-loop collective hypothesis); L116b control flights launched.
- S116: L116b controls a7ac9375c0: PID trips the same watchdog on stick sag/weak (scenario: open-loop stabilized collective); INDI holds altitude on o1_lemniscate with sag/weak/sat/wind. K115 fixes dce771f1e6. A-41 opened and closed 4e25b1aa00 (o1 horiz RMS 2.80 m nominal, INDI = PID).
- S116: A116 ca6825db51: stick_zsine_o6 flies in altctl/posctl (+sag 0.7); stick-mode metric window/reference missing for these modes.
- S117: D-G3-STICK-FACTORS (981e94f79e): stick runs draw attitude/rate factors only; C2/C3/C4/C6 forced position. g3_run.py --stop; G3 probe seed 117 n=60 launched (results/g3_probe_s117).
- S117: P117 G3 probe seed 117 n=60: position 45/45, stabilized 8/10, acro 3/5 without abort; all stick failures = open-loop collective (PID controls), D-G3-STICK-PILOT proposed (results/g3_probe_s117).
- S118 (20261118-203643, cap $3): RC118 filed and accepted (stick pilot time-boxed, then stage 4 identification/defaults, then G5 build; G3 scoring deferred until defaults exist). o1 probes ran MC_INDI_POS_EN=0 (stock mc_pos_control outer loop).
- S118: stick pilot 880a83c63b (I118, K118 key 0 BLOCKING/2 MAJOR, F118 fixes: pilot from mode switch, thr0-scaled clamps); v0 pre-test idx 0 tripped in neutral segment (pilot inactive there); v1 pre-test T118 launched (results/g3_pilot_s118).
- S118: T118 v1 INDI pre-test with pilot: idx 0 (acro), 21, 49 (stabilized) all ok (were watchdog trips in P117); PID controls in flight at session end.
- S119 (20261118-205000, cap $3): T118 stick pilot PASSED (INDI+PID), D-G3-STICK-PILOT decided (31c9869179); stage 4 opened: design/ident_concept.md, D-IDENT proposed, Q6 to owner (58ef81cdda); I119 estimator launched.
- Q6 closed S120 (moved from QUESTIONS.md):
  ## Q6 (S119, 2026-11-18) Identification concept: how does INDI fly before identification? ANSWERED (B)
  Context: stage 4 (decision 3). Full note: `design/ident_concept.md`. G1, G2_Y, ACT_TC, telemetry latency, W_MAX and
  the outer-loop thrust model are identified in one ~60 s hover manoeuvre: small injected multisine per axis,
  instrumental-variable regression of gyro/accel-derived acceleration on the measured rotor-speed increment (eRPM), with
  intercept, saturation excluded. That estimator is controller-agnostic. The open choice is what flies the manoeuvre:
  - B (recommended): INDI itself, in a conservative ident configuration (rate and outer gains halved, so a G1 wrong by
    x0.5 still has >= 6 dB / 45 deg, to be proven by G2 cells); full gains unlock when an ident-status parameter is set
    and the values pass plausibility checks. No PID needed (fits F-1 and "any quadcopter").
  - A: the user flies the manoeuvre on the default PID stack, then selects INDI (needs a PID tune first).
  - C: INDI refuses to arm until an offline log identification (same estimator on a PID log) wrote the parameters.
  - D: online adaptive estimation (kept as outlook only).
  Meanwhile: I build and key the estimator and its synthetic closed-loop self-tests (needed by every option), then G2
  cells at G1 x0.5/x2 with halved gains. Not blocked.
  Answer:
  **Owner answer (2026-11-18): B.** INDI flies its own identification manoeuvre in the conservative ident
  configuration; no PID dependency. Concern to close: INDI flying the manoeuvre must not bias the result. Conditions:
  - (i) Start independence (acceptance test): in SITL, ident flights started from G1 x0.5, x1 and x2 must give the same
    estimate (spread within the 10 % convergence tolerance) and each within 10 % of the true quad5in values. An estimate
    that follows its starting value means the closed loop leaks into the fit: B fails.
  - (ii) Excitation strength: INDI rejects the injected signal inside its bandwidth. Choose the multisine band against
    the halved-gain loop bandwidth, and report per axis the instrument strength (correlation of the instrument with
    du_meas, or the first-stage F statistic) and the confidence interval of each estimate. A weak instrument is a
    failed identification, not a value.
  - (iii) Filter alignment: the regressor (du_meas) and the regressand (derived acceleration) pass through the same
    filter and delay; a self-test with a deliberate mismatch must fail.
  - (iv) Identifiability: the excitation spans four independent directions (roll, pitch, yaw, thrust) whatever the
    starting G1; check the conditioning of the regression and report it.
  - (v) Cross-check, once in SITL: the same estimator on a PID-flown manoeuvre gives the same values within tolerance.
  SITL validates the estimator only; unmodelled effects (prop wash, frame flex, ESC non-linearity) stay in G4/G6
  scope.
- S120: Q6 closed (B), D-IDENT decided; ident_iv.py O(n) projection; K120 key: point estimate agrees with independent 2SLS, J mismatch detector + HAC se + rcond added, test_c fixed (seed lottery), 20/20 pass, mutations checked.
- S120 STATE trim, done rows moved verbatim:
  K115 DONE (design/key_k115_hte.md, 0 BLOCKING): fix AFTER L116 ends (same runner file): clamp [0.05,0.9] only on
    valid HTE (mc_att_control_main.cpp:241), meta hover_thr_used + hover_thr_source for every run (not stick only),
    tests that catch the 4 surviving mutations (run.json fields x2, stick_profile guard, main() thr0).
  L116 DONE e97d826b27 (results/g3_ladder_s116/README.md): nominal, mass13, inert13, erpmloss, gnssmis fly; wind5
    flies with 4.6 m horiz RMS (stabilized has no position hold: expected); sag07, weak08, sat(one motor x0.35)
    trip height watchdog 60-63 s. Hypothesis: open-loop stabilized collective, not controller.
  L116b DONE a7ac9375c0: PID trips the same watchdog (sag07 63.10 s, weak08 63.30 s) -> scenario property: stick
    stabilized is for attitude/rate factors only; thrust/wind factors go on position-hold scenarios. INDI on
    o1_lemniscate --sched holds altitude with sag/weak/sat/wind (vert RMS 0.03-0.18 m). A-41 opened (horiz 2.8 m).
  A116 DONE ca6825db51: stick_zsine_o6 flies in altctl, posctl, posctl+sag07 (INDI). metrics.py has no stick-mode
    reference/window for altctl/posctl (vertical = commanded climb): add one before these enter the batch.
  N116 DONE 4e25b1aa00: nominal horiz RMS INDI 2.805 / PID 2.800 m = faulted rows; A-41 closed.
  H116 DONE dce771f1e6 (K115 fixes, 9+3 tests pass, mutations checked; slew-lag m3 not addressed, accepted:
    probes only). Key of a bench-only meta fix not required (no safety path).
- S121: G3 'indi' runs S110-S118 flew the stock rate loop (no MC_RATE_CTL_TYPE 1 in base params); runner fixed and guarded; P117/T118/ladder INDI verdicts void.
- S119 (moved S122 from STATE): T118 PASSED (31c9869179) but its INDI half VOID (S121: stock rate loop). Stage 4 opened: design/ident_concept.md, D-IDENT, Q6. I119 ident_iv killed by OOM (n x n projection; use Zf @ (pinv(Zf) @ X)).
- S120 (moved): K120 key of ident_iv (design/key_k120_ident_iv.md, 20/20 pass; latency_by_xcorr unkeyed, J threshold needs flight data). H120 M3a signal survey (design/h120_m3a_signals.md): 1-axis Schroeder multisine on torque via MC_INDI_INJ_*, starts at first armed non-landed cycle, c/d/u in indi_rate_status at 800 Hz.
- S117 (moved): P117 probe results/g3_probe_s117 (60/60 flown, INDI half VOID per S121). Resume pattern `fly.sh <P> <idx...>`; g3_run.py skips runs with g3_done.json.
- S122: re-fly idx 21 with real INDI ok (a85d58f5ef): z ~5 m under stick z-sine, landed; esc_status 750 Hz in log; actuator_torque_measured absent.
- S122: RC122 filed (accepted). MC_INDI_W_MAX missing from G3 base params -> all G3 INDI runs model-only; fixed 0a49572149 + run_validity.py (void runs). Re-fly T118 idx 0/21/49 INDI+measured: all ok (8cfbc36d85).
- S123: K122 blocking fixed (46b2e2ceb2, fail closed). M3a ident hover pretest pos0/pos1 valid at INJ_AMP 0.003 (f49f8029f8); eRPM path 800 Hz confirmed. Next: ident_iv.py offline.
- S124: ident_fit.py IV driver; M3a roll G1_R 1748 (x1), 1742 (x0.5 start), 1756 (x2 start), pitch 1634, all within
  0.8 % of derived; yaw invalid (G2 term omitted). K124 key: 3 BLOCKING (no failing mismatch test, no F/J gate,
  homoskedastic F), MAJOR: ZOH regressor (actuator_torque_measured changes every ~2.4 samples), J-shift pre-test CI.
- S121/S122 findings (moved from STATE S125): G3 runs S110-S118 flew the STOCK rate loop (no MC_RATE_CTL_TYPE 1;
  fixed g3_run.py + run_scenario guard, P117/T118/ladder INDI verdicts VOID); G3 base params lacked MC_INDI_W_MAX
  -> measured path OFF, s121 re-flies MODEL-ONLY (fixed 0a49572149, run_validity.py). S122 re-fly idx 0/21/49 with
  W_MAX all ok + valid (results/g3_refly_s122, 8cfbc36d85). K122 key 3 BLOCKING (W_MAX alias, check_validity
  exception, missing g3_params.txt) fixed S123.
- S125: STATE trimmed; K125 key of K124 fix (usable w/ caveats) + gap fix (robust-F test, chain gate on data path); D-IDENT-J (J diagnostic only); halved-gain roll ident 1757.9 PASS; yaw two-regressor IV: G2_Y 27.5 ok, G1_Y 165 vs 205 derived (A-43); A-42 empty-dir second launch.
- S126: A-42 closed (sequential run.sh launches with distinct --out both complete, results/a42_s126). A-43: source chain
  SDF/plugin/CA gives G1_Y 205.3 (design/a43_closing_s126.md); K126 key of ident_fit_yaw.py 0 B / 4 MAJ / 6 MIN;
  probe (a43_probe) finds the cause = omitted rotor-drag yaw damping (synthetic 165.8 without r, 204.4 with r; real
  logs 212/220 with r + matched grid). A-43 closed, residual opened as A-44. Yaw ident model needs the D r term.
- S126: RC126 accepted (design/route_check_126.md): D-IDENT-STOP, S127 defaults file, S128-S129 stage 5 every mode.
- S127 (budget $1): defaults draft design/defaults_s127.md + bench/params/quad5in_indi_defaults.params (unkeyed). Found
  firmware gaps for D-IDENT: no ident-status parameter or halved-gain gating; MC_INDI_W_MAX default 0 disables the
  measured path; G1 firmware defaults 320/210/30 vs derived 1757/1640/205. Conditions (iv)/(v) not done (budget).
  K127 key: 0 BLOCKING, ACT_TC 0.033 needs a pretest flight; G1_Y 205 kept per D-IDENT-STOP.
- S128: D-DEFAULTS-FW: MC_INDI_ID_OK gate (0 halves K), G1/G2_Y fw defaults = quad5in, W_MAX 2700 in airframe, bench ID_OK 1 (5b70c50748..); K128 0 B; smoke hover ID_OK 0 ok.
- S128: ACT_TC pretest 0.033 vs 0.05 (hover, step_roll): both fly, 0.033 adopted in quad5in params, firmware 0.05 kept.
- S128: RC129 filed and accepted: stage 5 next (S129 build list + POSCTL smoke, S130 AUTO, S131 OFFBOARD + G5 probe).
- S129: G5 build list (design/g5_build_list.md, unkeyed): module = fork of mc_pos_control + INDI stage; all modes routed by code, only offboard flown; gaps: PID fallback x2 (F-1), no INDI reset on estimator reset, hover-thrust shift not ported, no module tests, no G5 section in GATES.md.
- S129: POSCTL smoke with MC_INDI_POS_EN 1 (results/smoke_s129_posctl): xy hold 0.02 m, tilt 0.26 deg; open: 2 m alt excursion 36-52 s, runner NAV_LAND at 63 s mid-sweep with status ok.
- S130: STATE trimmed: moved to JOURNAL the plans RC113/RC118/RC122/RC126 (all executed or superseded by RC129), the S116-S118 and S124-S128 status lines, the S127/S128 task rows (all done, outputs in design/ and results/).
- S130: rc.mc_apps start-up PID fallback removed (4016a03ec8); D-STAGE-STALE: no in-flight stock bypass, modelled-accel mode via library f_b_valid with delayed model signal, hold otherwise (0adaaa490f); keys K130/K130b 0 BLOCKING; smoke hover/POSCTL ok.
- S131: T5 failsafe pure fn + T10 stage reset on EKF reset (3d6066de89, K131 0 BLOCKING/MAJOR); AUTO harness (auto_tour, auto_land10) flown with INDI pos (166bb5a258): handover thrust step 25 % of hover > PROPOSED 10 %; S130 early-NAV_LAND was a README time-base error.
- S131: PID reference auto_land10 handover step 0.0075 vs INDI 0.035 -> A-45 opened.
- S132: A-45 closed: integrator zeroed at handover; D-HANDOVER bumpless a_ref (HandoverBlend, 9 gtests, break-checked); AUTO land10 step 0.035 -> <= 0.0067 on 3 seeds; key K132 MAJOR (frozen offset) fixed.
- S133: T9 hover-thrust sync in IPC bypass (7770538b55), gtest break-checked; SITL assertion pending.
- S133: T7 offboard vel-only + T8 ACRO pass-through probes pass (1 seed); A-46 flight-edge thrust step 6.1 % in ACRO run.
- S133: RC133 route check filed (accepted except PID-relative pass line, F-5).
- S134: owner directive 2026-11-20 acted on: D-STAGE-STALE stock branch + D-HANDOVER superseded, D-F7-GROUND written, G5 FINAL text (GATES 5b, F-8 rows not tested), STATE next actions gate-tagged; A134 F-7 implementation launched. Gate progress: G5 criteria FINAL (5b) committed before first G5 test.
- S134: F-7 firmware b9fb83c4a0 (INDI from arming, modelled force on ground/ramp, HandoverBlend/HoverThrustSync removed), keyed K134 (2 MAJOR fixed). Pre-fix smoke: take-off edge step 4.7 % hover, dip 0 m. Gate progress: G5.4 take-off edge 4.7 % < 10 % (probe, 1 seed).
- S134: post-fix smoke (f7_smoke_s134_fix): edge 4.7 % hover, dip 0 m, ground collective 0.0011 (was 0.0145). Gate progress: G5.4 take-off edge confirmed on fixed firmware (probe, 1 seed).
- S135: IndiAccelControl gtest PASS after resetBlend; auto_smoke_check.py gains all G5.4 limits (8 self-tests, break-checked, touchdown anchored on truth since ground_contact flags late), keyed by g54_key2.py (AGREE on 3 runs); G5.4 probe batch auto_tour + auto_land10 s1-3 all limits pass (edge step <= 4.4 %, ramp max 7.5 %, touchdown 0.71 m/s, tilt < 0.5 deg). Gate progress: G5.4 take-off and land rows pass on 3 seeds (probe, pre-freeze); RTL-from-20 m row 3/3 pass (auto_rtl20); A-46 left open, closing test moved to G5.1 acro probe.
- S135: A-46 closing test, stick_zsine_o6 acro x3: edge step 4.6/6.0/5.7 % hover < 10 %, A-46 CLOSED (seam not the cause; ramp-end reference change, bounded). G5.1 rate-step row still unflown (z-sine is not the G5.1 test). Gate progress: G5.4 edge confirmed in ACRO (3 seeds); A-46 closed.
- S136 (2026-11-20): G5.1 test defined exactly in GATES 5b, stick_steps scenario + g51_check.py (self-test, blind key AGREE); test defect fixed (hover throttle sank the craft -> pilot throttle-only); pre-identification half gains explain acro 13.6 deg/s. Gate progress: G5.1 tooling done, 3-seed probe batch flying.
- S136 batch: G5.1 probe stabilized PASS 3/3, acro yaw FAIL 3/3 (15-16 deg/s, K_Y 10 bandwidth lead). Gate progress: G5.1 tested as probe, acro yaw failure found.
- S137 (2026-11-20): G5.1 acro yaw cause found on the S136 logs (yaw lag 1/K_Y, K_Y 10 archive default, no saturation; first-order prediction 15.5 vs 15.0-16.0 deg/s). D-KY: default K_Y 20 (firmware 5d1d828af7). Probes: acro PASS 3/3 (yaw 3.15-3.29 deg/s), G2 rate-yaw 800/400 Hz GM 18.8/14.3 dB PM 78/82 deg. Gate progress: G5.1 acro row passes (probe); G2 rate-yaw cells re-measured at the new default.
- S137: G5.1 stabilized re-flown at K_Y 20, PASS 3/3 (tilt <= 0.14 deg, yaw rate <= 0.15 deg/s). Gate progress: G5.1 row PASS 6/6 as probe at the new default.
- S138 (2026-11-20): RC138 filed (cuts: merged G5 probes, one shared event injector, G5.10 on G3 hooks, defaults audit). Defaults audit: no G2 cell at the current pair nor at the firmware-default config (design/defaults_audit_s138.md). G5.2 exact test written, stick_pos_steps + g52_check (self-test), probe altctl/posctl x3 PASS 6/6 (z os <= 0.026 m, x os <= 0.063 m, settle <= 2.98 s), blind key AGREE. Gate progress: G5.2 row PASS 6/6 as probe.
- S138: G2 rate-roll 800 Hz probe at the current pair (ACT_TC 0.033, K_Y 20): GM 18.8 dB, PM 56.2 deg, DM 47.7 ms (1 seed, results/g2_roll_ky20_s138). Gate progress: G2 rate-roll cell measured at the current defaults (probe).
- S139 (2026-11-20): G5.3/G5.5/G5.7 exact tests written (dc4028652c). Runner per-segment mode switch, mode_switch10, hold_wind, g53_hold/g57 checkers (self-tests, break-checked). G5.3 hold PASS 3/3 (RMS 0.036-0.052 m). G5.7 INVALID as written (hold brakes, speed rule unmeetable) -> Q7; under leaveP s1 PASS, s2/s3 FAIL tilt err 5.2 deg at H->P, switch-specific (G5.2 same stick step 1 deg). Gate progress: G5.3 hold row PASS (probe); G5.7 first test flown, failure localised to H->P.

- S140: Q7 closed (answer A), full text:
  ## Q7 (S139, 2026-11-20): G5.7 validity rule, change after first test. Not blocking.
  Context: G5.7 exact test (GATES 5b, S139) flown x3 (results/g5_g57_s139). All 10 switches happen as commanded,
  thrust step <= 3.1 % of hover (limit 20 %), no LOC. Runs are INVALID: the rule "truth speed >= 1.5 m/s at >= 8 of 10
  edges" cannot be met, because HOLD brakes by design (speed at H->P edges 0.0-0.1 m/s; A/S coast to ~1 m/s in 2 s).
  Under any validity rule that admits the runs, tilt error over [edge+0.3, edge+1.0] s is 4.4-5.25 deg at the two H->P
  edges (limit 5 deg): FAIL in 2 of 3 seeds. Being compared with the same measure on G5.2 posctl stick steps from rest
  (no switch) to tell switch transient from normal attitude lag to a stick acceleration.
  Options: (A, recommended) validity = speed >= 1.5 m/s at the 4 edges that leave posctl; all 10 edges stay gated with
  unchanged limits (stricter than dropping edges). (B) re-design the sequence (shorter hold dwell) and re-fly.
  (C) keep as written: G5.7 cannot produce a valid run.
  Meanwhile: runs re-scored under A, marked "pending Q7"; no G5.7 verdict is claimed.
  
  Q7 ANSWER (owner, 2026-11-20): A. G5.7 validity = truth speed >= 1.5 m/s at the 4 edges that leave posctl; all 10 edges
  stay gated with unchanged limits. Next session: write into GATES 5b, re-score results/g5_g57_s139, close Q7.
- S140 (2026-11-20): Q7 closed (rule A in GATES 5b). G5.5 S139 probe scored + committed (o5/o6/offb PASS, o1-o4/o7 horiz FAIL 0.66-1.36 m, PID o1 1.04 m); G5.3 mission PASS 3/3. Cause: GNSS delay mismatch (sim 0 ms vs EKF 110 ms) in all G5 probes; matched re-fly started. Gate progress: G5.3 complete (probe), G5.5 scored and cause found, G5.7 verdict official (FAIL 2/3).
- S140 cont.: matched-GNSS re-fly s1 (results/g5_g55_s140_gnss): estimator fixed, o5/o6/offb PASS, o1 0.78 m / o2 0.93 m FAIL on 160 ms controller lag (jerk FF off); D-A18-REOPEN written; GATES 5b nominal GNSS set-up fix. Gate progress: G5.5 cause isolated to A18 (next: design note + implementation).
- S141 (2026-11-20): A18 design note (design/a18_jerk_ff_s141.md), implementation 7e58bea57c (a_ff-only jerk difference + 0.1 s hold, IndiRateFeedforward msg, rate-module gate, tests break-checked), key2 DISAGREE on one MAJOR (gate flip -> setpoint-lead pulse), fixed (gate bit in sp_source). Probe o1 0.776->0.590 m, o2 0.933->0.793 m, still FAIL; lag 140 ms. Gate progress: G5.5 o1/o2 error -24 %/-15 %, A18 kept (overturn test not met); rows still fail.
- S143 (2026-11-21): S142 injector committed (README written; kill/offboard-loss work, ekf_yaw/rc_loss defects, MAVLink events 3-24 ms late, maybe_landed/z not injectable -> Q8 open). Route check 143 filed. Lag chain split by phase fit: lag builds in a_c; drag-FF probe made o1 worse (0.59 -> 1.11 m), rejected; lag chase stopped per RC143. Gate progress: G5.5 o1-o4/o7 cause narrowed to a_c feedback and FAIL recorded; G5.6/5.8/5.9/5.11 injector pre-tested (Q8).
- S143 cont. (2026-11-21): G5.7 mode_switch10 re-flown with matched GNSS: s2 3.62 deg, s3 3.55 deg PASS (S139 FAILs were the GNSS set-up fault); PID compare dropped. Gate progress: G5.7 PASS 3/3 as probe.
- S144 (2026-11-21): G5 injector defects fixed (ekf_yaw sent id 43002 instead of 620; rcS scales COM_RC_LOSS_T by speed factor -> set 0.5 s), 2 pre-test flights, key2 AGREE on fixes + MAJOR (applied time from runner send) closed (3944e8e367). A-47 opened and closed (stock heartbeat re-stamp + 2 Hz flag log; G5.8 measurement defined in GATES). Q8 addendum. Gate progress: G5.8/G5.9/G5.11 injector keyed, rows unblocked except A-47 on G5.8 link-loss.
- S146 (2026-11-21): A145b finished: checker defects fixed (output[10..12] lexicographic pick, kill window past re-arm; torque_increment algebraic, out of the state set), G5.8/G5.9 hover re-flown 3 seeds with full-rate event logging, key2 AGREE. G5.9a FAIL 3/3 = stock commander latency (Q8 addendum 2). Gate progress: G5.8 hover PASS 3/3, G5.9 b/c/d PASS 3/3, G5.9a FAIL recorded (probe, RC113).
- S146 cont.: G5.8 3 m/s pre-test (--moving, offboard legs): entry PASS 3/3 events; excursion metric undefined at 3 m/s and link_loss flag reference lags last GCS message by 2.25 s -> Q8 addendum 3. Gate progress: G5.8 3 m/s case flown once (probe), definition question open.
- S147: G5.8 --moving key2 B1/M1 fixed (t_cmd from dispatched schedule), s1 re-fly valid: entry 510/1/21 ms PASS, 3 m/s excursion still Q8 add. 3. G5.10 probe built (sat_sustained, g510_check + self-test): INDI s1 alt 2.15 m FAIL, tilt 48.9 deg FAIL, back 4.3 s PASS; PID 3.22 m, 44.7 deg, 5.9 s; 20 deg tilt limit unreachable with the row's 3 m step, full-scale part not saturable in position modes -> Q9; A-48. Gate progress: G5.8 3 m/s s1 valid; G5.10 first probe flown (FAIL recorded, test-defect question Q9).
- S147 cont.: G5.10 INDI s2/s3: tilt spike 65 deg 0.3 s after thrust returns (PID 33 deg), checker LOC; alt 2.21 m. A-48 is a G5.10 gate test failure (saturation exit). Gate progress: G5.10 SAT part 3/3 seeds flown, FAIL (alt, tilt, LOC s2/s3), cause search next.
- S148: A-48 closed = injector artefact (8 sequential per-motor EC sets at the G5.10 saturation release); uniform faults via atomic SIM_GZ_THR_SC (867e10424a). Re-fly s1-s3: no LOC, tilt 45.3 deg (= MPC_TILTMAX_AIR), back 3.3-3.5 s, alt loss 2.67-2.74 m FAIL; PID s2 watchdog abort (> 3 m). Gate progress: G5.10 LOC/tilt-spike failure removed (test defect), alt-loss FAIL remains.
- S149: route check RC149 (design/route_check_149.md): on path; G5.10 cause search offline next (alt-loss split), cuts: PID G5.10 reruns, 3 m/s seeds before Q8, MC_INDI_EN alias. Gate progress: none (route check session, budget $1).
- S149 cont.: G5.10 alt-loss split offline (results/g5_g510_s148/altloss_split.md): SAT never saturates (cmd max 0.71), 2.7 m lost within 1.7 s of the 73 % thrust drop, none after REC -> Q9 note 2. Gate progress: G5.10 failure cause located (test does not saturate; transient of thrust drop).
- S150: G5.10 cause found on the S148 log: D-GAP blend (TB 1.0 s, clamp kMaxBlend 0.3 < gap 0.36) absorbs the 0.274 drop too slowly; D-GAP-G510 re-opens TB and bound. Probe TB 0.3 s seed 1 (results/g5_g510_s150): alt loss 2.71 -> 1.95 m, back 1.44 s, b still clamped. Q9 note 3. Gate progress: G5.10 alt loss 2.71 -> 1.95 m (probe, margin unmeasured).
- S150 cont.: kMaxBlend 0.3 -> 0.5 (003e25c6d4; gap at a 2x-hover thrust drop is 0.5 - u_hover on any airframe), unit test fails at 0.3, tests pass, key2 MINOR. Gate progress: G5.10 standing-error cause removed in firmware (not yet flown).
- S150 end: probe TB 0.3 + bound 0.5 seed 1 (results/g5_g510_s150/README_b05.md): alt loss 1.77 m (limit 2.0), back 1.87 s, b settles 0.367 = predicted gap. Gate progress: G5.10 alt loss 2.71 -> 1.77 m on one seed (probe; margin at TB 0.3 pending).
- S151: D-GAP-G510 accept condition met: outer z accel-break at TB 0.3 PM 62.7/67.3 deg r400/r800 (d65f07cf19, probe). G5.10 3 seeds TB 0.3 + bound 0.5: alt loss 1.74-1.76 m PASS, back 1.9-2.0 s PASS, no LOC; tilt 45.3 deg and AGG invalid wait on Q9 (0303185255). MC_INDI_POS_TB default 0.3. Gate progress: G5.10 alt loss and recovery PASS 3/3 (probe); G2 outer z cell at the new TB measured.
- S151 cont.: TB default 0.3 committed (f3b93704b6, key2 ACCEPT); xy margins at TB 0.3 PM 51.4/65.2 deg, GM 16.8 dB (9f827a2026); G5.4 probe auto_land10/auto_tour s1 at TB 0.3 all limits PASS, edge 4.0/4.4 %. Gate progress: G2 outer xy cells at the new default measured; G5.4 holds at the new default (probe).
- S152: 4c pre-freeze review 1/3 (opus, design/prefreeze_r1_stage5.md): REJECT, BLOCKING F1 ALTCTL arm on ground held at hover thrust; MAJOR F2 blend reset at arm edges, F3 no lib reset on re-entry, F4 dt clamp makes <5 Hz hold dead. F1 fixed 1c838f4801 (2 tests break-checked, key2 ACCEPT, MINORs: 0.005 floor thrust on ground, call-site wiring untested -> G7 harness). Gate progress: G5.2/G5.4 ALTCTL arm-on-ground defect fixed (probe pending S153); G7 review item 1/3 done.
- S153 (STATE trim): detail moved out of STATE 0c/0d: G5.5 o1 0.59/o2 0.79 m FAIL after A18 (S141); drag-FF probe rejected o1 1.11 m (S143); G5.9a switch->kill 3.75-10 ms (S146); G5.8 3 m/s s1 entry PASS, excursion undefined (S147); G5.10 S147 s1 alt 2.15 m tilt 48.9, s2/s3 tilt 65 deg at exit (injector artefact, A-48 closed S148 via SIM_GZ_THR_SC); S148 alt 2.67-2.74 m FAIL; S150 kMaxBlend 0.5 (003e25c6d4); S151 TB 0.3 PM 62.7/67.3 deg.
- S153: STATE trimmed; F1 ground-arm probe PASS altctl/posctl edge 7.2/7.1 % (bb67fc1cff, runner --ground-arm 3da7adf513); D-PREFREEZE-R1 (F2 amendment of D-GAP, F7/F8 deferred); F3/F4 fixed 23acbdef67 (key2 ACCEPT, K1 fixed). Gate progress: G5.2/G5.4 manual ground take-off path probed PASS; G5.7/G5.4 blocking review findings closed in firmware.
- S153 cont.: G5.7 probe s1 on 23acbdef67 PASS (3.71 deg, 2.6 %). Gate progress: G5.7 holds after the F3 firmware fix.
- S154 (20261121-040853): route check 154 (design/route_check_154.md, sonnet): on path; cuts: Q8/Q9 not blocking the freeze (option A assumed in freeze text), review 3/3 shrunk to a checklist with opus key only on gaps, no MINOR fixes before freeze, no re-probes of passing rows. Pre-freeze review 2/3 (design/prefreeze_r2_stage3.md, opus): ACCEPT WITH FIXES, 0 BLOCKING, MAJOR F1 (armable with no controller after a module start failure) accepted as stock-parity residual, MINORs to stage 7 (D-PREFREEZE-R2). Gate progress: G7 pre-freeze review 2/3 done; stage-6 freeze path cleared of inner-loop blockers.
- S155 (20261121-041621): pre-freeze review 3/3 checklist (design/prefreeze_r3_parity.md, sonnet): 0 OPEN, 0 SAFETY, 8 PARTIAL MINOR -> D-PREFREEZE-R3; stage-6 freeze defined D-FREEZE-6 at firmware 23acbdef67. GATES 5b needs the G4 typical profile for the re-fly: design/noise_profiles.md drafted (sonnet, UNKEYED: quiet ICM-42688-P, typical BMI270 + 10 m/s^2 judgement value, harsh 27 m/s^2 second-hand source); vibration hook found to cancel at equal rotor speeds (A-49). Gate progress: G7 pre-freeze reviews 3/3 closed; G5 freeze defined; G4 profile sources drafted.
- S156 (20261121-042420): D-VIB-HOOK implemented (gz_bridge 0f56d56bf1 + NaN guard 56ebc4e009; runner VIB_RPM/NB + full-rate sensor_accel), hover typical pre-test 1P 9.70 / BP 4.80 vs 10 / 5 m/s^2 (results/g4_vib_s156, bench/vib_line_check.py self-test), key2 ACCEPT WITH FIXES -> A-49 closed. Key2 of noise sources: D-NOISE-PROF (quiet 0.5, typical 10, harsh 27 amplitude at IMU). Gate progress: G4 profiles fixed and calibrated in the simulator; G5 re-fly unblocked.
- S157 (20261121-043345): freeze re-fly started (results/g5_freeze_s157): pre-test auto_tour PASS but found set-up fault (defaults file MC_INDI_ID_OK 0 defeats runner overlay; freeze params = defaults + ID_OK 1, D-FREEZE-6 note); batch scripts for all G5 rows (sonnet), 54 serial flights in a detached chain; seed 1 G5.1 acro/stab PASS, G5.2 altctl PASS, posctl z settle 4.15 s FAIL (limit 4.0). Gate progress: G5 freeze re-fly under the typical profile running; G5.1 s1 and G5.2 altctl s1 PASS, G5.2 posctl s1 FAIL recorded.
- S157 note: STATE 'Later: z-only active flag in indi_pos_status when next touching the module' moved here (size).
- S158 (2026-11-21): freeze re-fly batch 1 scored (G5.1 6/6, G5.2 5/6, G5.3 3/3, G5.4 6/6 PASS) and batch 2 seed 1 (G5.5 o1-o4/o7 FAIL -> Q11, G5.7 PASS, G5.10 INVALID Q9, fwdef G5.1 acro FAIL 15 deg/s, cause probe queued). Gate progress: G5.1/G5.3/G5.4 3-seed freeze evidence complete; G5.5/G5.7/G5.10 seed 1.
- S158 later: freeze re-fly complete (54/54), seeds 2-3 + PID refs + fwdef ID_OK 1 probe scored; fwdef excess = 0.5x K gate; Q10/Q11 updated. Gate progress: G5 freeze evidence complete on 3 seeds for every flown row (pending second key); G5.5 o1-o4/o7 FAIL 3/3 -> Q11.
- S159 (2026-11-21): RC159 filed + response (next: G2 freeze cells -> G4 -> G3); second keys run/written for every G5 freeze row: G5.1/G5.2 17/17, G5.4 (+ new land key) and G5.8/G5.9 all agree, G5.5/G5.7 27/27 INDI agree. Gate progress: G5 freeze verdicts now keyed (FAIL rows unchanged: G5.2 s1, G5.5 o1-o4/o7, G5.9a s1, G5.10 invalid; owner Q8-Q11).
- S160 (2026-11-21): G5 verdict table (freeze README); G5.3 hold was missing from the freeze set: re-flown PASS 3/3 (0.044-0.080 m), key2 agrees (key2_g53_hold.txt); G5.11 exact test written (3563613002) + g511_check.py/osc_detector.py (self-tests, break-checked): FAIL 6/6 on tilt command jump (xy 5.7-6.4, yaw 1.8-1.9 deg), UNKEYED, PID ref queued; G2 freeze roll 800 s1 GM 19.3 dB PM 56.4 deg DM 47.9 ms PASS; chain.sh flying remaining G2 cells. Gate progress: G5.3 hold freeze evidence complete + keyed; G5.11 first scoring (FAIL, cause search open); G2 first freeze cell PASS.
- S160 later: PID g5_events_s1 reference: G5.11 xy 7.82 deg FAIL (stack-independent -> Q12), yaw 0.48 deg PASS (INDI yaw spike is INDI-specific, cause search next). Gate progress: G5.11 xy cause found (stock EKF/pos loop), yaw row narrowed to INDI module.
- S160 end: G2 freeze rate cells flown (roll/pitch 400/800 x3, fwdef roll800 x3): GM >= 14.2 dB, PM >= 54.3 deg, DM >= 47.6 ms; 3 cells flag the pretest hover-RMS line under typical noise (open). Gate progress: G2 rate cells at the freeze measured on 3 seeds, all margins pass.
- S161 (2026-11-21): G5.11 INDI yaw-reset spike cause = estimator-reset branch re-seeding the INDI force filter with one raw sample (g511_yaw_cause.md); fixed D-T10-RESET (49568bcaa5, d1b65d0f09 after key2 review MAJORs), 2 unit tests break-checked; s1 probe 1.94 -> 1.08 deg, inside INDI no-event noise floor 0.72-1.10 (PID 0.48-0.86) -> Q12 addendum option D. Re-fly s1-3 at d1b65d0f09 flying. Gate progress: G5.11 yaw reset-specific spike removed (cause found, fixed, probed); row limit now at the noise floor.
- S161 end: G5.11 re-fly at d1b65d0f09 (3 seeds): yaw tilt jump 0.76/1.21/0.83 deg (freeze 1.94/1.78/1.84), xy 5.8-6.7 FAIL (Q12), excursion <= 0.21 m, no osc; row FAIL as written, UNKEYED. Gate progress: G5.11 yaw 0/3 -> 2/3 PASS after a firmware fix.
- S162 (2026-11-21): G5.11 re-fly at d1b65d0f09 KEYED (key2_g511 agrees 6/6): yaw 2/3 PASS, xy 0/3 (Q12), row FAIL as written; G5.8/G5.9 re-scored + key2 at the new firmware: unchanged (G5.8 PASS 3/3, G5.9a commander latency s1/s3, b-d PASS). Gate progress: G5.11 verdict keyed; G5.8/G5.9 confirmed at the post-freeze firmware.
- S162 later: G2 attitude cells at the freeze (results/g2_att_freeze_s162): 12/12 PASS (roll/pitch/yaw x 400/800 x 2 seeds), worst PM 53.4 deg GM 19.2 dB DM 106 ms, KEYED (key2 from raw, dPM 0.1 dGM 0.22 dB); reset-edge sweep: only g5_events flights have airborne resets, other 58 freeze rows unaffected by D-T10-RESET. Gate progress: G2 attitude cells measured at the freeze, 2 seeds, keyed.
- S163 (2026-11-21): G2 at freeze: rate yaw meas + model-only r/p/y 800/400 x2 (16 cells) PASS + KEYED, completing the rate cell set; outer vel/pos + accel x/y/z 800/400 x2 (24 cells) meet thresholds, UNKEYED; S160 pretest_gate RMS FAIL lines ruled not a validity item; 3 cells invalidated by sim holes from my parallel containers and re-flown. Gate progress: G2 rate cells complete+keyed at freeze, outer cells flown at freeze.
- S163: route check 163 (design/route_check_163.md): on path; acted on (6): single plateau-GM and x-check scripts, 267 Hz reported as 1 rate + 1 outer cell, G4 not waiting on 267 Hz. Gate progress: none (planning).
- S164 (2026-11-21): G2 outer cells KEYED (independent FRF from CSVs, 22/24 within 3 deg/1 dB, 2 z-accel 800 Hz cells differ on a -180 crossing inside a -27 dB notch, reported at the smaller GM 19.7 dB); phase-plateau GM over all 67 freeze cells: 66/67 literal, att pitch 800 s2 hit by a |L|>1 bin at 0.2 Hz (gain-reduction margin 18.5 dB) -> Q13 (test-defect fix A, not blocking). Gate progress: G2 outer key2 closed, plateau rule applied to every freeze cell.
- S164: G2 outer linear-model x-check: PM 8/8 within 10 deg, xy GM model ~5 dB conservative (A-50, verdict independent, closing test = attitude FRF in model), z no crossing either side. Gate progress: G2 outer x-check item done (one anomaly bounded).
- S165 (2026-11-21): STATE trimmed; G2 rate + attitude-yaw linear-model x-check at freeze params (bench/g2_rate_model_s165.py, self-test PASS; results/g2_freeze_s160/xcheck_rate.md): 12/15 groups agree, 3 disagreements bounded as A-51 (400 Hz GM drop unmodelled, likely gz/ESC latency), all cells pass either way. Gate progress: G2 model cross-check item done for rate, attitude yaw and outer.
- S165: G2 267 Hz reported cells flown (chain267.sh, s1): rate roll GM 11.5 dB PM 54.3 deg DM 52 ms; outer z PM 62.8/65.6 deg, no phase crossover; rate GM falls with controller rate (A-51 trend). Gate progress: G2 267 Hz reported rows done; G2 freeze set complete except keys of the 267 Hz rows (reported only).
- S166 (2026-11-21): committed G2 outer 267 Hz pinj captures; G4 metric bench/g4_metrics.py (R20/R4/C20/C4/clip, self-test + break-check PASS, UNKEYED), pre-look on g4_vib_s156 hover (proxy R20 0.09 %, C20 0.0015, clip 0); found no true rotor speed logged under SIM_GZ_ESC_FB=2. Gate progress: G4 metric script written, truth-signal gap identified.
- S167 (2026-11-21, $1 cap): gz_bridge true-rpm hook on esc_status instance 1 under FB=2 (10c741af4b), runner logs it (fc7f74e85a); builds, unverified. Gate progress: G4 R20/R4 true-rotor-speed blocker removed in code, flight check pending.
- S168 (2026-11-21, $3 cap): SITL rebuilt; true-rpm hook verified on a hover flight (esc_status inst 1, 800 Hz, 1 rpm, inst 0 lags 1 frame) and KEYED (no blocking), format clean; g4_metrics.py selects inst 1 under FB=2 (truth R20 0.077 % hover typical, probe); route check 168 filed (on path; cuts: no acro stick model now, G3 minimum = g3_checks.py + pretest chain + frozen-telemetry hook); G4 pre-test of 3 started (results/g4_pretest_s168). Gate progress: G4 truth signal available and keyed; G4 pre-test flying.
- S168 (later): G4 pre-test of 3 (quiet/harsh hover_long, typical lemniscate) flies, all values >=30x below proposed limits; S166 window defect fixed (windows from run.json); G4 metric key2 agrees except harsh C20 7 % (A-52). Gate progress: G4 pre-test done, metric keyed with one bounded disagreement; 27-run batch next.
- S169 (2026-11-21): results tree sorted (chain markers ignored). A-52 CLOSED (G4 keys agree <= 0.03 % on raw samples; key2 grid phase). bench/gate_g4.sh, G4 batch 18/18 flown (results/g4_gate_s169): R20/R4/C20/clip PASS all runs >= 10x margin. bench/g3_checks.py built (UNKEYED): harsh hover items 1-3 PASS 3/3, command chatter FAIL 3/3 = 70 Hz line, also in PID ref (A-54, sim alias suspected). A-53 opened (rpm stream gaps, bounded). Gate progress: G4 metric rows flown and PASS 18/18; chatter clause FAIL pending A-54.
- S170 (2026-11-21): A-54 cause search (one session, results/a54_s170): blade-pass 476.5 Hz aliases to 323.5 Hz at the 800 Hz IMU and 56.5 Hz at the 267 Hz decimation (confirmed); 70 Hz motor line in both stacks via the stock chain (1P/EKF2 stage, UNVERIFIED); line 0.5 DShot step; no hook change; owner Q14 (absolute floor for the chatter clause). Gate progress: G4 chatter-clause failure explained, verdict pending Q14 and g3_checks key2.
- S170 (later): blind key2 of g3_checks.py (bench/g3_checks_key2.py): items 1/3 and harsh 70 Hz chatter agree; item-2 span disagreement at landing and quiet-run chatter flags opened as A-55; Q14 addendum. Gate progress: G4 items 1-3 keyed on harsh (2 of 3 items full agreement), chatter verdict pending Q14/A-55.
- S170 (later): A-55 test: key1 on all 9 hover runs agrees with key2 on items 1/3 and chatter (flagged 9/9 incl. quiet); only item-2 landing span open. Gate progress: G4 checker keyed except the item-2 span; chatter clause shown non-discriminating (Q14 add. 2).
- S171 (2026-11-21): A-55 closed: harsh_s2 q flag is in flight (AUTO_LAND descent, not touchdown); D-G3-SPAN (item 2 whole airborne span), key1 g3_checks.py fixed + self-test osc_in_land (fails old code), keys agree on 9 hover runs; A-56 opened (INDI descent body-rate noise under harsh vibration, 10-20x PID). Gate progress: G4 additional clause item 2 now keyed: FAIL 1/3 harsh (was "pass, span open").
- S171 (later): A-56 cause search part 1 (results/a56_s171, log read): in AUTO_LAND the INDI pos module's rate feed-forward omega_ff reaches 7-22 deg/s (0 in offboard hold) and fights the attitude loop (-11 deg/s), no motor saturation. Gate progress: G4 item-2 harsh failure has a cause lead (INDI jerk FF in auto modes).
- S171 (later): A-56 cause: stock auto trajectory jerk (bang-bang +-MPC_JERK_AUTO, not d/dt of the accel setpoint) used as INDI rate FF -> up to 23 deg/s FF fighting the attitude loop; D-JFF-SOURCE decided (always difference a_ff), code next session. Gate progress: G4 item-2 harsh failure explained, fix specified.
- S172 (2026-11-21): D-JFF-SOURCE implemented (20b4a41b22, key2 no BLOCKING/MAJOR) and re-flown G4 hover x9 (results/g4_jff_s172): G4 rows PASS 9/9 but AUTO_LAND omega_ff spike unchanged (24-28 deg/s harsh), item 2 FAIL harsh_s3; source is the stock auto a_ff itself (aff_source.md). Second fix -> D-JFF-OFFB (rate FF offboard only), in test. Gate progress: G4 item 2 cause narrowed (FF scope), fix in flight test.
- S172 (later): D-JFF-OFFB (aa4fd2654a, key2 no BLOCKING; MINOR offboard-entry omega_ff step, deferred) flown harsh hover x3 (results/g4_jffoffb_s172): AUTO_LAND omega_ff 0 (was 24-28), G4 rows PASS, item 2 still FAIL 1/3 (2 Hz p from before land entry): A-56 FF hypothesis falsified, cause-search limit reached. Gate progress: G4 item 2 not moved; FF source removed as a cause.
- S172 (end): RC173 run early (design/route_check_173.md): stop FF work, write G4 verdict with A-56 open FAIL 1/3, one truth-accel probe re-opening the outer-loop measured-accel path, then G3 pre-test. Gate progress: G4 route to verdict set.
- S173: G4 verdict written (metric rows PASS; A-56 item 2 and chatter clause Q14 open -> G4 NOT PASSED). A-56 probe (results/a56_probe_s173, 6 harsh hover flights): oscillation persists with stock mc_pos_control (pos0) and with accel LPF 4 Hz -> INDI outer loop not the cause; inner rate loop remains. G3 pre-test idx 0-19 (seed 173, n 300) launched (results/g3_pretest_s173). Gate progress: G4 verdict recorded; A-56 narrowed to the inner loop; G3 pre-test started.
- S173 (later): G2 freeze data at 1.5-3 Hz show no lightly damped mode (design/a56_g2_2hz_s173.md, sonnet); PID had only 1 harsh flight, so PID harsh s2/s3 queued after the G3 pre-test (results/a56_pid_s173). Gate progress: G4 item 2 closing test defined (stack-dependence).
- S173 (end): G3 pre-test idx 0-19 flown 20/20 ok (results/g3_pretest_s173), unscored. Gate progress: G3 pre-test flown (scoring S174).
- S173 (end2): PID harsh s2/s3 clean (results/a56_pid_s173) -> A-56 INDI-specific, in the rate loop. Gate progress: G4 item 2 cause localised to the INDI rate loop.
- S174 (2026-11-21): results backlog sorted (66 paths; raw captures ignored). A-56 rate probe (results/a56_rate_s174):
  lead 0 keeps the s3 2 Hz line, blend 0.3 s clears s3 but s2 flags at the same window; trace shows the window spans
  AUTO_LAND entry where the stock land setpoint jumps and both stacks transient (PID s3 30.5 vs INDI 25 deg/s q std);
  S173 "INDI rate loop" reading withdrawn, Q15 asked, no firmware change. G3 pre-test scored (sonnet, UNKEYED,
  score_s174.md): 0/20 pass with chatter, 4/20 without; campaign blocked by set-up faults (noise profile not applied,
  tel_frozen hook missing, 5 m excursion rule vs 5 m lemniscate, windows). Gate progress: G4 item 2 failure
  re-attributed to a stack-independent transient (verdict waits Q14/Q15); G3 pre-test scored, set-up faults found.

## S175 (2026-11-21): Q8-Q15 and owner note closed, moved from QUESTIONS.md
## Q8 (S143, 2026-11-20): G5 event injectors, G1.5 timing and two rows not injectable firmware-free. NOT blocking.
Context: S142 built bench/g5_events.py (one flight: EKF yaw/xy reset, RC/link/offboard loss, kill/re-arm), pre-test
in results/g5_events_s142/README.md. (a) Every MAVLink-side event is applied 3-24 ms after its commanded time: the
runner only acts on lockstep ticks of 10-20 ms. G1.5 asks "applied within 1 physics step (1.25 ms) of commanded and
logged as applied". The applied time IS logged by the firmware itself (kill flag, failsafe flags, EKF reset counters).
(b) G5.6 false maybe_landed and G5.11 EKF z reset cannot be produced without firmware: the land detector needs
ground contact, and the external-position reset in ekf2 is horizontal only.
Options (a): A [recommended] for discrete events (stream stop, kill, EKF reset command) the G1.5 timing check becomes
"applied time taken from the firmware's own log flag/counter, every G5 transient metric referenced to it, the
commanded-applied spread reported"; the 1-step rule stays for physics injectors (torque, wind, motor, eRPM). This
fixes a defect of the test (the rule exists so metrics start at the real event), it does not loosen a G5 limit.
B: build a sim-time event scheduler (gz plugin or firmware hook), about 2 sessions.
Options (b): A [recommended] SITL-only test parameter in the two INDI modules (not in stock modules, O-11 holds) that
forces maybe_landed into their own land input for 0.5 s; z reset: try an EKF2_HGT_REF switch in flight (param, no
firmware), else row "not tested" with this reason. B: mark G5.6 false maybe_landed and G5.11 z as not tested.
Meanwhile: fix the ekf_yaw and rc_loss injector defects and continue G5.5 (A18); event rows fly after G5.7/A18.
Q8 addendum (S144): yaw-reset and RC-loss injector defects fixed and keyed (results/g5_events_s144). With applied time
taken from the firmware log, command events are 1.75-4.25 ms after send (ekf_yaw 3.0 ms). For stream-stop events
(rc/link/offboard loss) the firmware has no "applied" instant other than the failsafe flag, which includes the
timeout; the G1.5 1-step check cannot apply there and those G1.5 FAIL lines are by construction, not evidence. The
G5.8 limit (failsafe <= 1 s after timeout) is checked as written. Option (a) A covers this; still not blocking.
Q8 addendum 2 (S146): G5.9 "motors 0 within one command period" referenced to manual_control_switches.kill_switch
measures 5.00 ms (FAIL vs 1.25 ms, fix_s2), all of it stock commander latency switch -> actuator_armed.kill; outputs
are 0 in the same sample as the kill flag (0.00 ms). Options: A [recommended] reference = actuator_armed.kill rise
(the instant the control stack is told; commander latency reported, O-11 forbids changing it); B keep the switch
reference: G5.9a FAIL recorded as a stock limit. Meanwhile: both numbers reported, row counted FAIL. Not blocking.
Q8 addendum 3 (S146): G5.8 definitions, two items, not blocking (results/g5_events_s146_move/README.md).
(i) "excursion <= 1 m" at 3 m/s: measured from the position at loss it includes the flight during the timeout
(4 s offboard timeout = 12 m) and the braking (3.4-3.5 m from 3 m/s, stock hold). Options: A [recommended] excursion
at 3 m/s = max horizontal deviation of ground truth from the position setpoint/trajectory the failsafe action
commands (what the controller controls), <= 1 m; hover keeps the current definition. B: drop the 3 m/s excursion.
(ii) link_loss "timeout": the firmware flags GCS loss COM_DL_LOSS_T after the last telemetry_status heartbeat flag,
which itself stays set about 2.25 s after the last GCS message (fix_s2: last message 75.35 s, entry 80.60 s; stock
mavlink/commander, O-11). Options: A [recommended] timeout reference = firmware's own flag (as now, S144 note), the
receiver window reported; B: reference = last message sent, row FAIL in both stacks (stock limit).
Meanwhile: G5.8 hover counted on the S144 definition with the 2.25 s window reported; 3 m/s rows not counted.
**Owner answer (2026-11-21):** (a) A. (b) B: G5.6 false maybe_landed and G5.11 z are "not tested, owner decision
Q8(b)", with the reason; no SITL test parameter. Addendum 2: A (reference = actuator_armed.kill rise, commander
latency reported). Addendum 3 (i): A (excursion from the failsafe-commanded setpoint/trajectory at 3 m/s; hover
definition unchanged). Addendum 3 (ii): A (firmware flag, receiver window reported).

## Q9 (S147, 2026-11-21): G5.10 row after its first probe. NOT blocking.
Context (results/g5_g510_s147/README.md): scenario sat_sustained = 5 s at thrust scale 0.274 (2x hover) with the
row's 3 m position step, then a "full-scale aggressive manoeuvre". Seed 1: INDI alt loss 2.15 m (<= 2.0 FAIL), tilt
48.9 deg (<= 20 FAIL), back 4.3 s PASS; PID same flight 3.22 m, 44.7 deg, 5.9 s. (a) The 3 m step makes the stock
position loop command up to MPC_TILTMAX_AIR 45 deg, so "tilt <= 20 deg" fails for any controller: defect of the test.
(b) No position-mode manoeuvre saturates at full scale: 20-37 m steps peaked at 0.49 command (velocity/tilt limits).
Options (a): A [recommended] tilt limit = MPC_TILTMAX_AIR + 5 deg (no tilt beyond what the stack commands, overshoot
bounded); alt loss 2.0 m and recovery 5 s unchanged. B: keep 20 deg, drop the position step (saturation in hover only).
Options (b): A [recommended] full-scale part flown in stabilized: full throttle + full roll stick 1 s (inner loop at
full-scale saturation), limits as the row; B: drop the full-scale part.
Meanwhile: 3 seeds of the SAT part as is (counts against the current text), A-48 closing test. Not blocked.
Q9 note (S147, later): seeds 2/3 show the real G5.10 failure is INDI's tilt spike at the saturation EXIT (65 deg,
PID 33 deg), not the 20 deg text; (a) still applies to the SAT part. Cause search first (A-48), no answer needed for it.
Q9 note 2 (S149, results/g5_g510_s148/altloss_split.md, haiku log read, UNKEYED): the SAT part does NOT saturate:
motor command peaks 0.71, 0 % of time >= 0.99 in s1-s3 (THR_SC 0.274 leaves 2x hover thrust available). All 2.7 m alt
loss happens in the first 1.7 s after the thrust drop (collective ramps 0.14 -> 0.71 in ~1.5 s), none after REC.
So the row as flown measures the transient of an instantaneous 73 % thrust-effectiveness loss, not sustained
saturation. Proposal (c) A [recommended]: SAT part = scale chosen so hover needs >= 1.0 command (e.g. THR_SC <= hover
fraction) for 5 s with the limits as written, flown after a one-flight check that motors sit at >= 0.99; the 73 %
drop kept as a G3-type side probe, not a G5.10 pass condition. B: keep as is (row FAIL counted). Not blocking.
Q9 note 3 (S150): the 2.7 m loss is a controller limit, not a test defect: the D-GAP collective blend (TB 1.0 s,
bound 0.3 < the 0.36 gap) absorbs the drop too slowly (DECISIONS D-GAP-G510). Being fixed on the INDI side whatever
the answer to (c); (c) still decides whether the row also needs a truly saturating part.
Q9 note 4 (S151): with TB 0.3 + bound 0.5 the SAT part passes alt loss (1.74-1.76 m) and recovery (1.9-2.0 s) on 3
seeds (results/g5_g510_s151); only (a) tilt 45.3 deg = MPC_TILTMAX_AIR and (b)/(c) the non-saturating AGG/SAT
definition keep the row from PASS. Still not blocking.
**Owner answer (2026-11-21):** (a) A: tilt limit = MPC_TILTMAX_AIR + 5 deg; alt loss 2.0 m and recovery 5 s
unchanged. (b) A: full-scale part flown in stabilized (full throttle + full roll stick 1 s). (c) A: SAT part at a
scale where hover needs >= 1.0 command for 5 s, after a one-flight check that motors sit at >= 0.99; the 73 % drop
stays as a G3-type side probe, not a G5.10 pass condition.

Note S154 (RC154): the stage-6 freeze will proceed with option A assumed for Q8 (a)/(b)/add.2/add.3 and Q9 (a)/(c); an answer
B from the owner changes only the affected G5 rows, re-scored or re-flown after the freeze.

## Q10 (S157, 2026-11-21): G5.2 posctl z settle FAIL at the freeze is estimator height error. NOT blocking.
Update S157: seeds 2-3 posctl settle 0.36/0.35 s PASS; the FAIL is seed 1 only (5/6 runs PASS).
Context (results/g5_freeze_s157/README.md): freeze re-fly, typical noise, seed 1: G5.2 posctl z step settle 4.15 s
(limit 4.0 s, band 2 % of d = 0.039 m); overshoot and the x step pass. Truth vs estimate after release: the controller
holds the estimate on the setpoint within 0.02 m over the whole window, while EKF2 height error (est - truth) is
-0.078 m at release and decays to 0 over ~5 s; the truth "settle" is that decay. Stock ekf2 (O-11), not the INDI law.
At the sim-default noise (S138) the same row settled 1.2-3.0 s. Lesson 3: tracking on truth, estimator error separate.
Options: A [recommended] keep the truth metric and the limit; add a reference PID flight of the same seed (F-5): if PID
also fails, record the row as FAIL with cause "estimator height error > settle band", stack-independent, reported with
the est-truth trace; B (gate change after first test): settle band = max(2 % of d, 0.10 m) for z, justified by the
EKF height accuracy under the typical profile; C: settle measured on the estimate, truth error reported separately.
Meanwhile: the other rows continue; seeds 2-3 and one PID reference flight of this row are flown and scored as written.
Update S158: PID reference of the same seed PASSES (z settle 3.39 s, os 0.004 m). Option A therefore records the INDI
s1 FAIL as FAIL (1/6 runs), not as stack-independent. INDI holds the estimate on the setpoint; PID's slower z
response lets the EKF height error decay inside its own travel. Still not blocking; B or C only on your call.
**Owner answer (2026-11-21):** B: z settle band = max(2 % of d, 0.10 m), justified in GATES by the EKF height
accuracy under the typical profile; logged as a test-defect fix.

## Q11 (S158, 2026-11-21): G5.5 o1-o4/o7 still FAIL at the freeze. Re-open outer-loop base A? NOT blocking.
Context (results/g5_freeze_s157/README.md, seed 1; seeds 2-3 flying): horizontal RMS vs the analytic trajectory
0.58-0.79 m (limit 0.5 m) on o1-o4/o7; vertical, o5/o6 and offb_vel_step PASS. Same as the probes (S139-S143). Cause
(route check 143, D-A18-SOURCE): the acceleration command a_c produced by the stock PositionControl vel/pos feedback in
base A (accel_only) lags the trajectory ~100 ms; the INDI stage and the plant add only 20-40 ms. A drag feed-forward
probe made it worse (rejected). PID on o1 (S139, older plant) 1.04 m: the row fails for both stacks. The fix is in the
architecture you confirmed (base A keeps stock PositionControl for the feedback), so I ask before touching it.
Options: A [recommended] record G5.5 o1-o4/o7 FAIL with data and cause, both stacks; G5 otherwise judged on its rows;
B: re-open base A for offboard trajectories only: INDI module's own pos/vel feedback with full flatness FF (estimated
2-3 sessions + re-freeze of G5); C: owner reviews the 0.5 m limit (gate change after first test, needs your call).
Meanwhile: seeds 2-3 and a PID o1 reference at the freeze plant are flown and scored as written.
Update S158: 3/3 seeds FAIL on each of o1-o4/o7 (0.57-0.81 m), o5/o6/offb_vel_step PASS 3/3; PID o1 s1 at the
freeze plant 0.785 m (also FAIL).
**Owner answer (2026-11-21):** B: re-open base A for offboard trajectories only. The INDI module gets its own
pos/vel feedback with full flatness feed-forward. Other modes keep base A. Design note and DECISIONS entry first
(one page), then code with second key and tests, then a G5.5 pre-test. G5 rows the change touches are re-flown at
a new freeze. The 0.5 m limit is unchanged.

## Q12 (S160, 2026-11-21): G5.11 xy reset tilt limit fails for both stacks. NOT blocking.
Context (results/g5_freeze_s157/README.md, G5.11 row; exact test GATES 5b S160): a 1 m external-position reset
(MAV_CMD_EXTERNAL_POSITION_ESTIMATE) moves the estimate 1 m; EKF2 then fuses GNSS and returns it to truth in ~1 s, so
the position loop sees a 1 m transient error and commands 5.7-6.4 deg tilt (INDI, 3 seeds) and 7.82 deg (PID, seed 1)
against the row's 1 deg. Truth excursion 0.15-0.19 m (<= 0.5) and no oscillation in both stacks. The firmware-free
injector cannot produce a reset that the EKF keeps (stock ekf2, O-11).
Options: A [recommended] record G5.11 xy as FAIL, stack-independent (stock EKF/pos loop), truth excursion reported as
the controller-relevant number; B (gate change after first test): xy part judged on truth excursion and oscillation
only, the 1 deg limit kept for yaw (and z if injectable); C: drop the xy part (injector cannot make a persistent reset).
Meanwhile: yaw part (INDI-specific 1.8 deg spike, PID 0.48 deg) gets its cause search; xy counted FAIL as written.
Q12 addendum (S161): INDI yaw spike cause found and fixed (D-T10-RESET, results/g511_fix_s161/README.md): estimator
reset re-seeded a filter with one raw sample. After the fix the yaw event reads 1.08 deg on s1, inside INDI's own
no-event range of the same metric (0.72-1.10 deg; PID 0.48-0.86): the 1 deg limit is at INDI's hover tilt-command
noise floor under the typical profile. Option D [recommended, gate defect fix]: tilt jump measured as the event value
minus the 95th percentile of the same metric at no-event instants of the same flight (the row then measures the reset,
the noise is judged in G4). Meanwhile scored as written. Not blocking.
**Owner answer (2026-11-21):** B + D. xy is judged on truth excursion (<= 0.5 m) and no oscillation. The 1 deg
tilt limit is kept for yaw. The yaw tilt jump = event value minus the 95th percentile of the same metric at
no-event instants of the same flight.

## Q13 (S164, 2026-11-21): G2 phase-plateau GM formula on bins with |L| > 1. NOT blocking.
Context (results/g2_plateau_s164.md): the G2 pass uses min(GM, plateau GM), plateau GM = min of 1/|L| over bins with
arg L within 10 deg of -180. First applied at the freeze (67 cells): 66 PASS; attitude pitch 800 Hz seed 2 gets
"-18.5 dB" from its 0.2 Hz bin, BELOW crossover, |L| = +18.5 dB, arg -170.9 deg (other seeds -158 to -165 deg there).
There 1/|L| is not a gain margin: the loop is stable with 18.5 dB of gain REDUCTION margin. Classic GM 20.2 dB, PM 54.1.
Options: A [recommended, test-defect fix] plateau GM over bins with |L| < 1; bins with |L| > 1 within 10 deg of -180 are
reported as gain-reduction margin 20log10|L| with the same >= 6 dB pass threshold (no threshold lowered); 67/67 PASS.
B: keep the literal formula: the cell FAILs G2.
Meanwhile: G2 work continues (model x-check, 267 Hz); both readings reported in GATES G2 freeze status.
**Owner answer (2026-11-21):** A.

## Q14 (S170, 2026-11-21): G4 command-chatter clause fails on a sub-DShot-step line in both stacks. NOT blocking.
Context (results/a54_s170/README.md): G4 "Additional" flags a 20-100 Hz line in actuator_motors at peak > 20 x median.
All G4 metric rows PASS 18/18 with >= 10x margin; the clause FAILS 3/3 typical/harsh on a 70 Hz line. Cause (one
session, A-54): the modelled rotor vibration (1P 159 Hz, blade-pass 476.5 Hz) folds through the stock 800 Hz IMU, 267 Hz
accel decimation and EKF2 stages into the command; PID carries the same line (78x) - INDI shows more (768x), probably because it
feeds acceleration back. Line RMS 2.5e-4 of full scale = half of one DShot step (1/2000); C20 23x under its limit. A
real FIFO-mean IMU attenuates the blade-pass alias only ~6 dB, so a hook change would not close the clause honestly.
Options: A [recommended, test-defect fix, lesson 6]: a line counts as chatter when peak > 20 x median AND its RMS
(+-2 Hz) >= one DShot step (5e-4 of full scale); ratio reported. B: keep the clause as written: G4 FAIL recorded,
stack-independent cause. C: change the vibration model (FIFO mean): line ~4x lower in power, still FAIL; not advised.
Meanwhile: G4 verdict written both ways; key2 of g3_checks.py; G3 preparation continues.
Q14 addendum (S170, later): the blind key2 of the checker (results/g4_gate_s169/g3_key2.md) flags the 20 x median rule
on every quiet and typical run too (22-39 Hz, command std 2.5e-4): the ratio alone flags a sloped background, not
only lines. This supports option A (absolute floor); being checked against key1 (A-55) before the G4 verdict.
Q14 addendum 2 (S170): the original checker (key1) run on all 9 runs agrees with key2: the clause flags 9/9 runs, quiet
included (22-39 Hz, windows from take-off), so as written it fails every profile (results/g4_gate_s169/a55_key1_all.md).
**Owner answer (2026-11-21):** A: chatter = peak > 20 x median AND line RMS (+-2 Hz) >= one DShot step (5e-4 of
full scale); ratio reported.

## Q15 (S174, 2026-11-21): G4 item 2 (A-56) flags a stack-independent land-entry transient. NOT blocking.
Context (results/a56_rate_s174/README.md): the 2 Hz pitch-rate "sustained oscillation" that fails G4 item 2 on 1/3
harsh runs always sits in the 3 detector windows that span AUTO_LAND entry. There the stock land setpoint jumps
(velocity 0.2-0.54 m/s) and the rate loop tracks its own setpoint for 1-2.5 s, then returns to the hover floor.
PID shows the same transient, the same size (q std peak 30.5 deg/s PID s3 vs 25.0 INDI). Whether the detector calls it
"sustained" depends on window alignment, and the run that gets flagged moves with seed and config (blend 0.3 s moved it
from s3 to s2). The S173 reading "cause in the INDI rate loop" is withdrawn: PID was not flagged, but it is not clean.
Options: A [recommended, test-defect fix]: item 2 runs on windows that do not overlap the 3 s after a nav_state change
(mode transitions are judged by the G5 transient limits); the land-entry transient is reported for both stacks.
B: run the item 2 detector on the rate tracking error (q - q_sp) over the whole flight. C: keep as written: G4 item 2
FAIL recorded, stack-independent cause. Meanwhile: G4 verdict stays NOT PASSED as written; no inner-loop change
(D-RATE-BLD unchanged at 1.0 s); G3 continues.
**Owner answer (2026-11-21):** A: item 2 skips windows that overlap the 3 s after a nav_state change. Mode
transitions are judged by the G5 transient limits. The land-entry transient is reported for both stacks.

## Owner note (2026-11-21): acting on Q8-Q15
All eight questions are answered. These are test-defect fixes the owner approved, so log each in GATES.md and
DECISIONS.md as such. Then re-score the existing gate evidence with the amended definitions; no re-fly is needed
except where a new definition requires new flights (G5.10 SAT/full-scale, Q11 B). Order: (1) re-score G2 (Q13),
then G4 (Q14, Q15); close each gate that passes. (2) G5 re-scoring (Q8, Q10, Q12, Q9a). (3) Q11 B design and code,
then the G5.10 re-definition flights. (4) G3 set-up fix (below). Mark Q8-Q15 closed and move them to JOURNAL.md.
See the process changes in MISSION.md (owner, 2026-11-21): blocking questions, second-key scope, route checks,
hands-off rule, reference flight first, freeze discipline, GATE_STATUS.tsv, no history in STATE next actions.

Also from the owner, 2026-11-21:
- Post-freeze firmware commits 20b4a41b22 (D-JFF-SOURCE) and aa4fd2654a (D-JFF-OFFB) were made on a hypothesis
  that was falsified, but they also fix a real feed-forward defect. Judge them under the new freeze discipline:
  keep (with the G5 rows they invalidate re-flown) or revert, and record the choice in DECISIONS.md.
- G3 set-up before any campaign: (a) the runner aborts when a declared plant/noise factor is listed as
  not_applied (results/g3_pretest_s173: noise profile not applied, tel_frozen hook missing). (b) The excursion rule
  is measured against the setpoint, so it no longer conflicts with the lemniscate. (c) g3_checks.py runs in Docker,
  not with scipy from a scratchpad path. (d) Explain run 17 (129 deg tilt, loss of control) and the four
  oscillating runs, PID reference first. Then re-fly the 20-run pre-test.
- When the re-flown G3 pre-test is clean, create WAIT_OWNER with "G3 set-up fixed, ready for flight chain" in
  STATE.md. The owner then builds a detached flight chain (batches flying between sessions) before the 300-run
  campaign.
- S175 (2026-11-21): acted on Q8-Q15 (GATES "Owner amendments S175", D-OWNER-Q8-Q15, D-JFF-KEEP keep both post-freeze
  FF commits, rows re-fly at freeze-7). G2 plateau key2 20/20 agree (0.22 dB); A-51 closing test rejected latency
  (12/15 -> 5/15) -> Q16 BLOCKING G2. G4 re-score both keys: metric rows 18/18, item 2 PASS (Q15 A); chatter FAIL =
  INDI-only 22 Hz line AUTO_LAND -> touchdown (PID none), probe S175-f on post-JFF firmware. G3 set-up (a)+(c) fixed
  (noise profile applied, abort on not_applied, Docker scoring). Gate progress: G2 evidence complete except x-check
  clause (Q16); G4 item 2 PASS, chatter failure localised as INDI-specific; G3 set-up faults (a)(c) closed.
- S176 (2026-11-21): G4 cruise chatter INDI-specific (PID same seed clean): ~89 Hz offboard-trajectory line 1.4-1.5x
  floor + AUTO_LAND 22 Hz line; cause search deferred to freeze-7 (offboard path changes). G5 checkers on S175 rules,
  re-score keyed (G5.2/G5.9a/G5.11 pass on evidence). G5.5: gain probe shows xy pos/vel bandwidth is the lever
  (o1 0.587 -> 0.289 m; o2-o4/o7 0.27-0.32 m at 2x); D-OFFB-POSVEL replaces the cascade+mask draft. Gate progress:
  G5 rows G5.2/G5.9a/G5.11 scored and keyed; G5.5 failure cause shown and fix probed; G4 cruise chatter localised.
- S176 (cont.): D-OFFB-POSVEL firmware 7dd352bae2 + 08011e92d0 (MC_INDI_XY_P/XY_VP 1.9/3.6), key2 agrees; default
  params o1 s1 0.297 m. Gate progress: G5.5 fix in firmware and keyed, freeze-7 code complete pending declaration.
- S178: Q16 closed. Full text:
  ## Q16 (S175, 2026-11-21): G2 verdict with 3/15 rate model x-check groups unexplained. BLOCKING for G2.
  Context: every G2 cell passes at the freeze, keyed: rate/att/outer 67/67 incl. the Q13 A plateau rule (key2 S175,
  results/g2_plateau_s164_key2.md, max diff 0.22 dB); worst measured GM 10.7 dB (plateau, model-only roll/pitch 400),
  PM 54.3 deg. G2 also says "measured and model PM within 10 deg and GM within 3 dB, or the difference explained in
  ANOMALIES.md before the result is used". Rate x-check (A-51, results/g2_freeze_s160/xcheck_rate.md): 12/15 groups agree;
  roll400 GM 14.2 vs model 17.9, yaw400 GM 15.3 vs 21.5, roll800 fwdef PM 54.3 vs 65.9. The closing test (S175,
  xcheck_rate_a51.md) added the measured cmd->eRPM latency (2.1/4.1 ms): agreement fell to 5/15, hypothesis rejected.
  The residuals are unexplained (likely yaw model structure and filter roll-off; not chased). In every group BOTH the
  measured and the model margins pass (model min 7.9 dB/48 deg with latency), so no pass depends on which one is right.
  Outer x-check: A-50, model conservative, explained.
  Options: A [recommended] G2 PASSED on the keyed measured margins; the 3 unexplained groups are reported as an evidence
  limit (model fidelity, A-51 open). The rule "a margin that passes only because it disagrees with the model is not a
  pass" is met (the model passes too). B: one more session of model structure work (yaw reaction-torque path,
  filter roll-off) before the verdict. C: G2 NOT PASSED on the x-check clause.
  Meanwhile: no G2 work; G4/G5/G3 work continues.
  **Owner answer (2026-11-21):** A. G2 PASSED on the keyed measured margins. Report the 3 unexplained rate x-check
  groups (roll400 GM, yaw400 GM, roll800 fwdef PM) as an evidence limit on model fidelity. A-51 stays open, and no
  further model-structure work is done for G2. D-FREEZE-7 re-flies the G2 outer cells (x-check models on
  MC_INDI_XY_*) and spot-checks 2 rate/att cells. Write the verdict once those freeze-7 cells pass. If one fails,
  re-open G2 under the D-FREEZE-7 overturn rule.
- S178: route check 178 (cuts applied in STATE); Q16 closed (A). Freeze-7 G4 18 runs scored both keys: metric rows
  18/18, items PASS, chatter FAIL hover 1/9 + cruise 9/9 -> G4 NOT PASSED at freeze-7 (GATES). Cause search on logs:
  33 Hz = bench 30 ms setpoint staircase passed 3x PID; 18.7 Hz descent line from EKF velocity via xy vel gain.
  Probes P1 (MPC_VEL_LP 8) and P2 (10 ms sender) both still flagged: no fix, step back next session. G2 spot cells + G5.10 pre-test chained after queue2; Q17 (G5.10 stabilized criterion).
  Gate progress: G4 verdict NOT PASSED (freeze-7, evidence complete); G5.5 24/24, G5.3 mission 3/3, G5.4 6/6 PASS at freeze-7; G2 spot cells queued.
- S179 (2026-11-21): G4 step back (D-G4-STEPBACK): F1 MC_INDI_POS_LPF 5 and F3 MPC_VEL_LP 5 (3 seeds each) do not
  remove the AUTO_LAND flag; logs place it at the touchdown impact (touchdown_s179.md) -> Q18 to owner. G2 freeze-7
  scored: xy PM 38.4-44.8 on 13/16 outer cells, att spot 43.0 -> G2 NOT PASSED at freeze-7 (D-OFFB-POSVEL overturn);
  params probe XY_P 1.2 gives PM 49.5/50.2, G5.5 0.345/0.347 m. G5.10 pre-test flown (unscored).
  Gate progress: G2 verdict NOT PASSED at freeze-7 (evidence complete) and a shown remedy (XY_P 1.2); G4 L2 located.

- S180 closed Q17 and Q18 (owner answers A; acted on: GATES "Owner amendments S180", D-OWNER-Q17-Q18). Text:
## Q17 (S178, 2026-11-21): G5.10 stabilized full-scale part, recovery criterion. BLOCKING for G5.10.
Context: Q9 (b) says the full-scale part is flown in stabilized (full throttle + full roll stick for 1 s) with "same
limits": no LOC, alt loss <= 2.0 m, tilt <= MPC_TILTMAX_AIR + 5 deg, no windup = back within 0.3 m in <= 5 s.
Stabilized has no position or altitude setpoint, so "back within 0.3 m" has no reference, and at full roll stick the
tilt is commanded up to MPC_MAN_TILT_MAX, not MPC_TILTMAX_AIR. Pre-test flights (INDI + PID, seed 1) are queued
(results/g5_10_freeze7_s178, new scenario g510_stab_full; SAT part per Q9 (c) at SIM_GZ_THR_SC 0.136, hover needs
1.007 command). PID flies the same flight as reference.
Options: A [recommended] in stabilized: no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg; no windup = attitude error to the
stick-commanded attitude <= 5 deg within 1 s after the sticks return to centre (rate/attitude integrators are the
only wind-up there); alt loss not applied (full throttle climbs). B: keep the literal text, measuring altitude
change from stick release to +5 s against 0.3 m (no reference, likely fails for PID too). C: drop the recovery clause
for the stabilized part.
Meanwhile: the pre-test flights fly (data only); the stabilized part is not scored until answered. SAT part, G2, G4
cause search, G5.3/G5.4 continue.
**Owner answer (2026-11-21):** A. In the stabilized full-scale part of G5.10: no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg;
no windup = attitude error to the stick-commanded attitude <= 5 deg within 1 s after the sticks return to centre;
the alt-loss limit is not applied (full throttle climbs). Log it in GATES.md 5b and DECISIONS.md as an approved
test-definition fix. PID flies the same flight as the reference.

## Q18 (S179, 2026-11-21): G4 command chatter, windows that contain the touchdown. BLOCKING for G4 (land windows).
Context: G4 asks for limits on motor-command RMS "in hover and cruise"; Q14 A added the 20-100 Hz chatter detector
(4 s windows, peak > 20 x median AND line RMS >= 5e-4) over the whole flight. At freeze-7 the cruise runs fail it in
two places: L1 in the lemniscate (in scope, INDI work continues: setpoint extrapolation probe F2) and L2 in AUTO_LAND.
S179 localised L2 on logs (results/g4_fix_probe_s179/touchdown_s179.md): line RMS >= 5e-4 only in 1 s windows that
contain the ground impact (ground_contact - 0.5 s to landed + 0.7 s); steady descent 1.3e-4 (6e-5 with MPC_VEL_LP 5),
on ground 1e-5. PID shows the same impact signature (26 Hz, 1.2e-3 in the impact window; diffB 5e-4 at 20 Hz), but
its detector did not flag a sustained 20 Hz line; INDI at 20 Hz is 6e-4 vs PID 1e-4 there. Touchdown is judged by
G5.4 (passed at freeze-7: touchdown 0.708 m/s, ramp step 7.5 %). The hover_harsh_s1 flag (20.0 Hz) is likely the
same event (not yet checked).
Options: A [recommended] the G4 chatter detector skips windows overlapping [ground_contact - 1 s, landed + 1 s] in
both stacks; touchdown stays judged by G5.4; the land-window values are reported for both stacks. B: keep the rule;
G4 then needs a touchdown fix (re-open D-F7-GROUND ground handling), likely affecting G5.4/G5.6 too. C: score the
detector on the hover and cruise segments only (gate text), take-off/land reported.
Meanwhile: the land windows are not re-scored or chased. L1 (lemniscate) work, G2 (XY_P 1.2 freeze-8), G5 continue.

**Owner answer to Q18 (2026-11-21):** A. The G4 chatter detector skips windows that overlap [ground_contact - 1 s,
landed + 1 s] in both stacks. Touchdown stays judged by G5.4. Report the land-window values for both stacks. Log it
in GATES.md and DECISIONS.md as an approved test-definition fix, then re-score the freeze-7 G4 runs with keyed
scripts (no re-fly). Check that the hover_harsh_s1 20 Hz flag is the same touchdown event. L1 (lemniscate) stays
in scope.

- S180 (2026-11-21): owner answers Q17/Q18 logged (GATES 'Owner amendments S180'); Q18 skip in both chatter keys, freeze-7 G4 re-score: no window skipped, verdict NOT PASSED unchanged; hover_harsh_s1 flag is take-off/loiter not touchdown; keys reconciled on GP (33.5 + 89.25 Hz); cruise item 3 offset = PID (not a G4 row). F2 probe launched. Gate progress: G4 Q18 re-score row scored (verdict unchanged, evidence q18_rescore_s180).
- S180 (cont.): F2 committed (33.5 Hz gone, 89 Hz stays); 89 Hz located: outer 88.9 Hz staircase x inner setpoint-lead derivative (zero-noise flight unchanged); F4 kSetpointLeadTc 0.03 committed, probe met (89 Hz 4.2e-4). Gate progress: G4 cruise chatter L1 removed on one probe flight (both keys), freeze-8 candidate defined.
- S181 (2026-11-21): MC_INDI_XY_P default 1.2 (d2f3845292) + bench yaml-default test; key2 freeze-8 diff 0 blocking (M1 bench lead Tc 0.01 -> 0.03 fixed, roll model PM 66.4 deg); pre-test cruise s2/s3 89 Hz 3.8-4.2e-4, G2-STEP att 3/3 -> FREEZE-8 declared (D-FREEZE-8); re-fly queue results/freeze8_s181 (87 flights) started. G5.10: score_motors key2 found 4 key1 defects, key1 fixed (bench/g510_score_motors.py), keys agree; SAT pre-test was a set-up fault (thrust step with the position step, both stacks crash) -> D-G510-SAT-SETUP ramp. (The git mv of score_motors landed in commit 210ad05859.) Gate progress: G2/G4/G5 freeze-8 evidence in flight (87 flights queued); G5.10 metric keyed (two keys agree), SAT set-up fault found and decided.
- S182 (2026-11-21): freeze-8 queue 87/87 rc 0, all groups scored by keyed scripts (agents). G2 NOT PASSED at freeze-8: outer 24/24 PASS, spot rate 41.3 / att 42.2 FAIL; G2-STEP 9/9. Cause search: low-f phase loss from xy gains, probe XY 0.95/1.8 -> 49.0/51.4 (D-XY-TRADE, sweep next, offboard-only gains rejected). G4: all rows in limits, 33/89 Hz gone, cruise_harsh_s2 keys split on Q15 skip -> Q19 (blocking G4). G5: every scored row PASS (G5.5 24/24, G5.3 6/6, G5.4 6/6, events 9/9), G5.10 open. G5.10 scorer: saturation fraction is validity only (INVALID). Gate progress: G2 verdict at freeze-8 written + cause shown; G4 scored (Q19 decides); G5 rows re-scored PASS at freeze-8.
- S183 (2026-11-21): xy sweep (results/xy_sweep_s183): XY_VP 2.4 -> spot PM 47.2/48.1, G5.5 0.44-0.45 m; 2.8 -> 45.5/46.4, rate holes FAIL. D-XY-PICK 2.4, firmware default 83976c5099 (key2 AGREE), FREEZE-9 declared (D-FREEZE-9), re-fly queue results/freeze9_s183 started (G4 cruise_harsh_s2 held for Q19). Gate progress: G2 spot cells PM >= 45 on 1 seed at the new default (freeze-9 3 seeds decide).
- S183 Q19 closed (full text follows):
  ## Q19 (S182, 2026-11-21): does the Q15 A nav_state skip apply to the command-chatter check? BLOCKING for G4
  Context: freeze-8 G4 (results/freeze8_s181/G4_SCORES.md, both keys, Q18 skip applied): R20/C20/R4/clip 18/18 in
  limits; hover 9/9 clean (freeze-7 hover_harsh_s1 20 Hz gone); cruise 33.5/89 Hz lines gone (89 Hz residue 4.2e-4 <
  5e-4). One row splits the keys: cruise_harsh_s2, motor m2, 20.0 Hz, RMS 6.0e-4 (ratio 472), at the hold-to-land
  switch (~58-65 s, still airborne, so the Q18 touchdown skip does not cover it). Key 1 scores chatter inside item 2 and
  applies the Q15 A 3 s skip after a nav_state change: no flag. Key 2 scores chatter separately without that skip: flag.
  With the skip both keys clear it; without it both flag it. GATES line 362 defines the command check as "the G3
  detector, also on the command"; Q15 A says "the sustained-oscillation detector skips windows that overlap the 3 s
  after a nav_state change; mode transitions are judged by the G5 transient limits". PID: S180 reported land windows
  20-26 Hz 1.1-1.5e-3 in PID too (same land-entry signature, larger). If the skip applies, G4 PASSES at freeze-8.
  Options: A (recommended) the Q15 A skip applies to the command check too (same detector, line 362), key 2 gets the
  skip, G4 PASSED; B the skip is for the rate detector only: G4 NOT PASSED on cruise_harsh_s2.
  Meanwhile: no re-fly, re-score or note on G4; work continues on G2 spot probes and G5 scoring. Not blocked overall.
  **Owner answer to Q19 (2026-11-21):** A, with a PID guard. The Q15 A 3 s skip after a nav_state change applies to the
  command-chatter check too (same G3 detector, GATES line 362); key 2 gets the skip so both keys score alike. Guard,
  because no G5 transient limit judges command oscillation: chatter lines inside skipped windows are still reported for
  both stacks, and the row FAILS if the INDI line RMS there exceeds the PID reference at the same transition (same
  scenario and seed). Scope confirmed: the item 2 rate detector limit applies to harsh hover; harsh-cruise rate flags
  stay informational (reported). Log it in GATES.md and DECISIONS.md as an approved test-definition fix, re-score
  freeze-8 G4 with keyed scripts (no re-fly), then fly cruise_harsh_s2 in the freeze-9 set and score G4 at freeze-9.
- S184 (2026-11-21): results sorted (freeze-9 committed, rate s1.csv ignored). G2 re-scored after hole re-flies ->
  G2 PASSED at freeze-9 (outer 24/24, spot 47.3/47.4, G2-STEP 9/9; 1 max-gap hole cell counted under evidence limit 1).
  G4 scored (effort 18/18, chatter 0/18 Q19 skip, 2 keys; Q19 key2 review: skip OK, guard comparison not coded) ->
  G4 NOT PASSED on the PID guard; cause search: 17->4 20 Hz transient in both stacks (INDI 1.7x), 14->18 guard
  artefact; Q20 asked (blocking G4). G5.10 set-up: two ramps invalid (sank before window), reverted.
  Gate progress: G2 open -> PASSED; G4 open -> NOT PASSED (guard, Q20); G5.10 set-up 2 attempts invalid (D-G510-SAT-SETUP to re-open).
- S185 (2026-11-21): Q21 asked (G5.10 SAT set-up unreachable as worded, PID sinks too; D-G510-SAT-SETUP re-opened,
  BLOCKING G5.10). G3 tel_frozen hook built (SIM_GZ_ERPM_FRZ in gz_bridge + erpm_frozen override, g3_run wired),
  key2 no blocking, hover probe + trip probe: detector trips and releases (A-57 trip latency, bounded). Run 17 PID ref
  ref: no LOC (tilt 38.6, osc flag in both) -> INDI-specific. Gate progress: G3 set-up item (a) tel_frozen hook done (runs 03/11 no longer abort); G5.10 -> Q21.
- S186 (2026-11-21): G3 set-up. Checker fixes, 2 keys each: item-1 excursion vs time-matched trajectory_setpoint (old fixed
  point measured the lemniscate; keys agree 0.01 m), G4 chatter no longer decides G3 item 2 (GATES 304), run_validity pid_*.
  Run 17 LOC cause (log): 1.8 Hz pitch limit cycle from ~20 s, motors unsaturated, telemetry fine, touchdown inside it.
  Linear model: attitude loop PM<0 in exactly the 4 osc runs (03/07/13/17), boundary e x tau_mult >= ~5; P ~4.7 fixes up to
  e 2 x tau 3, not the down-tau x9 corner. A-58 (77.5 Hz chatter in G3 draws). Q22 written (box vs gains), blocking G3 -> WAIT_OWNER.
  Keys then agree 21/21 on items 1-3 (D-G3-ZREF: truth height zeroed at rest).
  Gate progress: G3 pre-test re-scored with fixed checkers (2 keys agree); osc failures explained (attitude-loop margin), verdict path -> Q22.

## S187 (2026-11-21) closed owner questions Q20-Q22 (full text moved from QUESTIONS.md)
## Q20 (S184, 2026-11-21): which RMS does the Q19 PID guard compare? BLOCKING for G4 (guard rows)
Context: the S183 amendment says a G4 row FAILS "if the INDI line RMS in a skipped window exceeds the PID reference at
the same transition". The second key (`results/freeze9_s183/g4/Q19_KEY2_REVIEW.md`, F1) finds the metric undefined:
which windows, which line, any floor or tolerance. Freeze-9 G4 is NOT PASSED under both readings (GATES "G4 verdict at
freeze-9"), so this question does not change today's verdict; it sets the target of the fix and of the re-score.
- Reading A (flagged line): compare only lines above the chatter floor 5e-4 (the G3 detector's own flag). INDI fails
  where it is flagged and PID is not, or both are flagged and INDI > PID. Freeze-9: 5 of 16 transitions fail (INDI
  20.0-20.8 Hz 5.0-5.3e-4, PID 2.7-4.4e-4).
- Reading B (any window): max line RMS over all overlapping windows, strict INDI > PID, no floor. Freeze-9: 9 of 12
  fail, several at levels far below the 5e-4 floor, i.e. noise-level comparisons between two stacks (lesson 6).
Recommendation: A (absolute floor, then the PID comparison only where the floor is crossed).
Meanwhile: one session of cause search on the INDI 20 Hz transition line (log analysis, no firmware change), which
both readings require. Not blocked on other gates (G5.10 set-up continues). No re-score of guard rows until answered.
Added S184 after the cause search (`results/g4_20hz_cause_s184/README.md`, script line20.py with self-test):
- 17->4 (take-off -> loiter): a physical 20 Hz roll/pitch transient (truth body rate 1.5e-3 rad/s, torque x/y, all 4
  motors differential), onset at the end of the take-off setpoint stream, decays ~5x within 10 s. PID shows the same
  onset and shape at 0.5-0.65x the INDI amplitude (PID motor line 2.8-4.1e-4, INDI up to 5.3e-4). The 1.5-1.9x INDI
  amplification is shown; its cause (rate-loop gain near 20 Hz) is a hypothesis.
- 14->18 (offboard -> land): no tone in 19.5-21 Hz in either stack (both at floor); the guard's 5e-4 flag there comes
  from its +-2 Hz integration on broadband descent energy, i.e. a guard artefact under both readings.
So this is partly a PX4 fact (owner note point 1): the transient exists in both stacks, INDI amplifies it ~1.7x at a
level 0.05 % of full motor command. Options: A strict (Reading A; 17->4 fails; next = identify the 20 Hz amplification
from the G2 rate-loop data, then a firmware change that re-opens G2/G4/G5); C (Reading A, and a transition transient
that PID also shows is reported with both values, failing only above an absolute bound you set). Recommendation: A with
a narrow-band (+-0.5 Hz) line measure that removes the 14->18 artefact; I will not propose a tolerance myself.

**Owner answer to Q20 (2026-11-21):** Reading A with a narrow-band line measure in the guard only, plus C for
transients PID shares.
1. Guard metric: key-2 detector `psd_windows(..., rms_hz=0.5)` (4 s Hann, 1 s hop, peak bin in 20-100 Hz, RMS over
   the peak +-2 bins = +-0.5 Hz). Skipped windows as in S183/Q15 (`ta < c+3 and ta+4 > c`). The Q14 detector outside
   skipped windows keeps its +-2 Hz measure.
2. A transition is checked only where an INDI skipped window is flagged (ratio > 20 AND narrow RMS >= 5e-4); otherwise
   both values are reported.
3. When checked: FAIL if PID has no window with ratio > 20 within +-0.5 Hz of the INDI peak at that transition
   (INDI-only line), or if the INDI narrow RMS > 1e-3 (new upper bound set by the owner). Otherwise PASS (transient PID
   shows too, owner note point 1); INDI, PID and ratio reported. Windows from c+3 s on stay with the Q15 detector.
4. Review pre-look (read-only, to be confirmed by both keys): every freeze-9 INDI skipped window is below 5e-4 in the
   narrow band (max 4.84e-4, hover_harsh_s2 17->4); 14->18 drops to 2.3-2.95e-4; INDI/PID at 17->4 on 4 s windows is
   0.74-1.14. Report the 4 s values, not the 1.7x from line20.py 2 s windows. No firmware chase.
5. Code the rule in both keys, re-score freeze-9 G4 (no re-fly): that is the G4 verdict.

## Q21 (S185, 2026-11-21): G5.10 SAT part, the "hover needs >= 1.0 command" set-up cannot be reached. BLOCKING for G5.10 (and so the G5 verdict)
Context: Q9(c) defines the SAT part at a thrust scale where hover needs >= 1.0 command, entered from a pinned hover.
- Step-in 1 -> 0.136 with the 3 m step (S181): an 86 % thrust-loss test, both stacks hit the ground (D-G510-SAT-SETUP).
- Ramped scale-down during hover (S184, results/g510_setup_s184/README.md, 4 ramp shapes, INDI and PID): both stacks
  sink once the scale passes ~0.2 (hover cmd ~0.65-0.8), before the window opens; PID run s1 alt loss 2.39 m, INVALID.
  Log: rotor speed stays at hover (thrust = weight) while the vehicle sinks 0.4-0.5 m/s: a ramp-disturbance velocity
  error, not a plant limit (T/W 1.08 at the final scale was real). `hover_thrust_estimate` stuck at 0.337 while the
  true hover command rises (hypothesis for the low vertical gain, stock PX4, not chased: owner note point 1).
- This meets the overturn rule of D-G510-SAT-SETUP (PID fails too) and the row text needs a change: your call.
Options:
  A. Demand transient at a moderate scale (0.3-0.4, hover cmd ~0.6): 3 m climb step + full-throttle demand saturates
     all motors >= 0.99 for >= 1 s (scored on the motors), limits unchanged (alt loss 2.0 m, tilt, 5 s recovery). The
     "pinned hover" wording is dropped. Recommended: tests windup and saturation handling, reachable by both stacks.
  B. Keep the pinned hover and add the hover-estimate fix to the flight params (MPC_THR_HOVER near the true hover at
     the low scale): changes the stock hover set-up for this row only.
  C. Drop the SAT part; G5.10 = the stabilized full-scale part (Q17 A) only, reported as such.
Meanwhile: no G5.10 flight or score. Work moves to G3 set-up (tel_frozen hook, STATE next action 4). Blocked on G5 verdict.

**Owner answer to Q21 (2026-11-21):** A as a one-flight feasibility check; C if saturation is not reached.
1. Cause recorded: Q9(c) is not physically impossible (scale 0.136: T/W 0.993, ~0.9 m loss in 5 s for an ideal loop).
   The blocker is stock PX4: hover-thrust estimate clamped at MPC_THR_HOVER + HTE_THR_RANGE = 0.337
   (MulticopterHoverThrustEstimator.cpp:91). PX4 fact: reported, not chased.
2. Numbers: T/W = 7.31 x scale, hover command = 0.137 / scale; the estimate stays inside its clamp only for scale >= 0.41.
3. One flight per stack: scale 0.30, a 3 m climb (new z offset) plus the existing 3 m horizontal step
   (scenarios.py:244). Valid only if all 4 motors stay >= 0.99 for >= 1 s in BOTH stacks (validity, not pass).
4. If valid: limits unchanged (no LOC, alt loss <= 2.0 m, tilt <= MPC_TILTMAX_AIR + 5 deg, back within 0.3 m in <= 5 s
   after saturation ends); saturation time and hover-estimate value reported. If not valid: C, G5.10 = stabilized
   full-scale part (Q17 A); sustained saturation under the position loop stays covered by G3 corner C3.
5. Not B (per-row stock hover parameter is a hand tune). Note for G3: C3 (scale 0.27, hover cmd 0.51) is also above
   the hover-estimate clamp; report it with the C3 results.

## Q22 (S186, 2026-11-21): G3 pre-test oscillations sit outside the attitude-loop stability boundary; box or gains? BLOCKING for G3
Context (results/g3_pretest_s173/run_017/LOC_CAUSE_S186.md, results/g3_osc_margin_s186/README.md, results/g3_excursion_s186/RESCORE_V2.md):
- Fixed two G3 checker defects (both keys agree): excursion now vs the time-matched setpoint (old rule measured the 5 m lemniscate),
  and the G4 chatter line no longer decides G3 item 2 (GATES 304). Remaining pre-test failures: sustained 1.6-2 Hz roll/pitch limit
  cycle in runs 03, 07, 13, 17 (17 tumbles at touchdown inside the cycle: LOC); small q 10.75 Hz line in 08; item 3 horizontal in 02/05/09.
- Run 17 log: motors unsaturated (max 0.27), measured torque valid, no telemetry fault: a closed-loop limit cycle from ~20 s.
- Linear model (existing margins_models.py, drawn factors per run): rate loop PM 36-79 deg on every draw; ATTITUDE loop (MC_ROLL_P /
  MC_PITCH_P 8 around the INDI rate loop) PM -16 to -0.6 deg at 1.6-1.8 Hz in exactly those 4 runs; 35 of the other 36 axis-runs OK.
  Boundary: unstable when e x tau_mult >= ~5 (e = controller G1 / plant G1, tau_mult = slow motor tau / 33 ms); PM < 30 deg above ~3.5.
  The G3 box reaches e 2 x tau 3 x asymmetry 3 = 18.
- PID reference on run 17's draw (one flight): also sustained p/q oscillation (2.75-3.25 Hz, 18-29 deg/s RMS), no LOC. So that row fails
  in both stacks on that draw; INDI's is ~10x larger and ends in LOC.
- Attitude P ~4.7 restores PM >= 30 deg at e 2, tau x3 (nominal attitude crossover 1.25 -> 0.7 Hz, PM 69 -> 78). With the slow-down
  corner (tau x3 and asymmetry x3 = down tau x9) even P 2 gives only 19 deg: no single gain covers the whole box.
Options:
  A. Keep the box. Set INDI-configuration attitude P to ~4.7 (stock params, values only, zero code diff), declare freeze-10, re-fly the
     G2/G4/G5 rows it invalidates (about 3-5 sessions). The down-tau x9 corner is then expected to fail and is reported as an explained,
     out-of-reach corner (G3 NOT PASSED there unless you narrow it).
  B. Narrow the box to what identification bounds (G6 flies G3 after identification): e.g. G1 error x[0.67, 1.5] and tau asymmetry
     applied inside x[0.5, 3] (down tau <= x3). Current gains then still fail at e 1.5 x tau 3 = 4.5 (PM < 30), so B alone is not enough.
  C. Attitude P scheduled from the identified motor tau (bandwidth rule, decision 4): a firmware design change (new law parameter,
     two keys, freeze-10). Covers the tau part, not the G1-error part.
  D. Keep gains and box, report G3 NOT PASSED with this boundary as the explanation, and move on to G6-G8.
Recommendation: A (and report the down-tau x9 corner as it falls). It is the smallest change that buys margin, and gives a
re-flyable freeze.
Meanwhile: no G3 flight or score of the oscillation rows. The key-2 item-3 fix (tooling, all options need it) finishes this session.
G4 waits Q20, G5 waits Q21, G7 waits the G4/G5 verdicts: blocked (WAIT_OWNER).
**Owner answer to Q22 (2026-11-21):** no attitude-P change, no freeze-10. Narrow the G1-error factor and fix the
tau box (test definition).
1. Not A: by model scaled to freeze-9, P 4.7 gives G2-STEP settle ~830-890 ms (limit 450) and outer xy PM ~36.5 deg
   (limit 45). No P meets G2 and covers G1 error x2 (P 8: max e 1.2 at att PM >= 30; P 7: 1.35, settle 447-480 ms).
2. G1 error, controller vs plant: x[0.8, 1.2] per axis (was x[0.5, 2]). Basis: identification is accepted only within
   10 %, the gate halves gains before identification (MC_INDI_ID_OK 0), and G6 covers the x0.5/x2 starting errors.
   A payload added after identification (e ~1.3) is a stated G8 limit. Gains unchanged; freeze-9 G2/G4/G5 evidence stands.
3. Tau box, test defect: g3_sample/model_variant multiply tau_down by scale x asymmetry (up to x9). Fix: tau_up and
   tau_down both lie in x[0.5, 3]; slow = scale, fast = max(scale / asym, 0.5). Corners C1-C6 re-stated on the new
   ranges (C1/C2/C4 use e 1.2 / 0.8).
4. Fast-motor corner (missed in Q22): e 0.5, tau x0.5, 10 ms gives rate PM -22 deg at 16.6 Hz. Check the rate loop
   at e 0.8, tau x0.5, 10 ms on the model before the re-fly; run 08's 10.75 Hz q line is a hypothesis for this.
5. Not C (G3's controller tau is nominal, the plant's is drawn), not D (LOC is a safety row).
6. Next: update GATES G3 table + sampler (second key), re-fly the 20-run pre-test; when clean, the flight-chain line
   in STATE.md + WAIT_OWNER as before.
7. Run 17 PID reference (owner review, results/g3_pretest_s173/run_017_pid_s185/flight.ulg, same draw and seeds):
   the PID flight FAILS G3 item 2 in both keys (sustained p 2.75-3.25 Hz, line RMS 18 deg/s; q 2.5-2.75 Hz, 28.8 deg/s),
   no LOC. "PID: no oscillation" in LOC_CAUSE_S186 was wrong (corrected there). The gap is ~25x, not ~10x: q RMS
   0.5-20 Hz over 28-74 s is 272 deg/s INDI vs 10.9 deg/s PID. Not verified: whether the PID line is a limit cycle or
   the gust/wind response (needs a calm-air PID flight; only if the G3 report needs it). Run 17's draw (e 1.52) is
   outside the new box, so it leaves the pre-test set and goes to the report as an out-of-box case with both values.
## S191 (2026-11-21) closed owner question Q23 (full text moved from QUESTIONS.md)
## Q23 (S189, 2026-11-21): G5.7 cause is aa4fd2654a (kept under D-JFF-KEEP at owner request). Which fix? BLOCKING for G5.7
Context: G5.7 fails 3/3 at freeze-9 on attitude tracking lag at hold edges (tilt_err 5.8-10.7 deg, limit 5; freeze-6
2.4-4.2; PID ref 4.50/4.54/7.50, s3 FAIL). Probes (results/freeze9_s183/g5_modes): XY gains back to freeze-6 values:
still FAIL (probe_s189); kSetpointLeadTc 0.01: still FAIL (probe_tc_s189); aa4fd2654a reverted (rate feed-forward in
every mode again): PASS s3 and s1, hold edges 2.5-3.8 deg (probe_ff_s189). aa4fd2654a was kept at your request
(D-JFF-KEEP) because the auto-mode a_ff is the stock smoother state that follows the vehicle: differenced, it fed
24-28 deg/s of rate FF during AUTO_LAND under strong vibration (results/g4_jff_s172). Without FF, INDI tracking lag at
hold edges (~48 ms) equals PID's (~50 ms), and PID also fails s3.
Options:
 A. FF in every mode except AUTO_LAND (and land-like failsafes): smallest change, keeps the S172 fix where it was seen.
    Probe first (G5.7 s3 + the S172 AUTO_LAND vibration case), then into FREEZE-10. Recommended.
 B. Full revert of aa4fd2654a: re-ships the AUTO_LAND FF defect.
 C. Keep aa4fd2654a: G5.7 stays NOT PASSED with this data (PID fails s3 too: your call whether G5.7 is a test defect).
Meanwhile: the G3 fix D-AF-ALIAS (outer-loop acceleration aliasing, INDI-only 7 Hz line) is implemented and probed;
both firmware changes would enter one FREEZE-10, then the invalidated rows are re-flown once. G5.7 work waits.
Blocked: G5.7 only.
**Owner answer to Q23 (2026-11-21):** B, full revert of aa4fd2654a (D-JFF-KEEP overturned for that commit only;
20b4a41b22 stays). Basis (review of the S172 evidence):
1. The AUTO_LAND rate FF has no gate effect. With FF already 0 in AUTO_LAND (results/g4_jffoffb_s172), G4 item 2
   still failed 1/3 near land entry (p 2.0 Hz) and descent q std stayed (13.9 deg/s s2): A-56 FF hypothesis falsified
   (S172). The < 3 deg/s omega_ff target was self-set, not a gate row.
2. The spike is not an entry transient: on harsh it is a sustained slope of the stock land-task a_ff during descent
   (aff_source.md); typ peaks equal harsh (24-28 deg/s). Source is stock FlightTaskAuto: no cause search (owner note
   point 1). Record the 24-28 deg/s landing FF as a known, gate-neutral fact.
3. Not A: a nav_state or land-setpoint switch is a new hook (new vehicle_status subscription) that no gate row
   consumes, and RTL / mission landings (nav_state 5 / 3) would need it too. Not C: the revert probe already PASSES
   G5.7 (s1, s3) and also clears s3 1>2 (10.66 -> 2.45) and 15>2 (6.20 -> 2.38).
4. Before FREEZE-10, one probe on the candidate build (revert + D-AF-ALIAS 2d92dbcf59/4afa7a97b6):
   - G5.7 mode_switch10 seeds 1, 2, 3 (s2 not yet flown with the revert).
   - G5.4 auto_land10 and auto_tour on typ, plus one harsh auto_tour: G5.3/G5.4 rows against freeze-9 under the
     D-JFF-KEEP 10 % rule; record omega_ff peaks in takeoff, loiter, mission (difference FF never flown there).
   - One moving offboard run (G4 cruise) showing omega_ff non-zero (not shown in g4_jffoffb_s172 hover).
5. If any check fails: stop and write a new owner question; no fall-back to A or C.
- S188 (20261121-195641): G5.10 stabilized part 3/3 both keys at freeze-9 (SAT dropped Q21; PID ref also passes).
  D-FREEZE-9-GAP: G5.1/G5.2/G5.7 had not been re-flown since freeze-6; re-flown: G5.1 6/6, G5.2 6/6 PASS, G5.7 FAIL
  3/3 both keys (attitude jump 5.8-10.7 deg at hold edges; freeze-6 PASS). G3 pre-test on Q22 draws: 10/20 FAIL item 2
  both keys (ANALYSIS_S188.md). PID refs of both failures queued detached (T9, T10). Gate progress: G5.10 scored
  PASS; G5.1/G5.2 re-scored PASS at freeze-9; G5.7 and G3 pre-test scored FAIL (PID refs pending).
- S188 (cont.): PID refs flown. G5.7 PID attitude jump 4.50/4.54/7.50 deg (INDI 5.8/9.3/10.7): mostly INDI-specific.
  G3 pre-test PID key 1 fails 03/08/13 (shared); INDI-only 00/02/05/09/10/16/17. Next: one cause-search session for
  both. Gate progress: G3 and G5.7 failures classified INDI-specific vs shared (reference rule).
- S189: one cause-search session for G3 and G5.7. G3 INDI-only 7 Hz p/q line (runs 16/10) = outer a_f aliased: 267 Hz
  f_b sampled at the 88.9 Hz stage before its LPF, 95.73 Hz vibration -> 6.84 Hz (recompute corr 0.99998; D-AF-ALIAS);
  LPF 5 probe passes only under the detector threshold. G5.7 hold-edge lag: XY-gain and Tc 0.01 probes FAIL,
  aa4fd2654a revert PASS s3/s1 (D-G57-FF) -> Q23 (D-JFF-KEEP was owner request). PID key1/key2 on 03: key 1 lacks
  the Q15 A nav-change skip. Gate progress: G3 and G5.7 failure causes shown on logs, fixes named (G3 fix next, G5.7 Q23).
- S192 (2026-11-21): scored D-OWNER-Q23 probe (results/freeze10_cand_s191): G5.7 3/3 PASS, G5.3/5.4 and G4 cruise PASS, G3 02/05 pass with matched GNSS; FREEZE-10 declared at 7fe6206fcc (D-FREEZE-10). Gate progress: G5.7 FAIL->PASS on candidate (probe, re-score at freeze-10 batch); G3 02/05 cause shown.
- S193 (2026-11-21): FREEZE-10 re-fly queue built and launched detached (results/freeze10_s193/, commit 0d6581ac16, pid 1308846); route check deferred to S194 for budget. Gate progress: G2/G3/G4/G5 re-fly at freeze-10 started (no row scored yet).
- S194 (2026-11-22): RC194 filed; FREEZE-10 queue ended (01:14, rc 0); G4 PASSED (18/18 both keys, Q20 guard 0 FAIL), G2 PASSED (outer 24/24 after 1 hole re-fly, spot, G2-STEP 9/9); G5 all rows pass except G5.5 o2_circle_z s1 0.5027 m (PID 1.157 m) -> Q25; G3 pre-test 16/20 both keys (02/05 GNSS mismatch +95/+84 ms, 03, 08 shared with PID) -> Q24; G7 checker self-tests started. Gate progress: G2 open->PASSED, G4 open->PASSED at freeze-10; G3 pre-test and G5 scored, verdicts wait Q24/Q25.
- S195 (2026-11-22): no owner answer to Q24/Q25; G7 work: (a) stock zero diff PASS; (c) defaults diff 0 gain mismatches, ACT_TC 0.033 into 4040, ID_OK 0 kept (D-G7-DEFAULTS); (d) astyle clean; (e) mc_indi_pos_control failed NuttX compile (std::fmin) -> fminf fix e9e85e395d (D-G7-NUTTX-BUILD, behaviour-neutral), fmu-v5x +64.9 kB flash, v6x overflows 23.5 kB; (b) break audit 57/66 killed, all 9 survivors killed by new tests. Gate progress: G7 items a, c, d, e evidence scored; b 66/66 (injection helpers left).
- S196 (2026-11-22): G7(b) injection helpers break-checked (67 mutations, 0 survivors, results/g7_s196/INJECTION_BREAK_CHECK.md); G7(g) bench/make_fw_branch.sh builds local indi-fw-pr (firmware + sim commits); G7(f) checklist -> D-G7-F-TEXT; agents S196c (indi-fw-pr SITL build, failed on pymavlink submodule clone) and S196e (F-TEXT, half done, partial patch results/g7_s196/F_TEXT_PARTIAL_S196e.patch) killed by host OOM 02:51 (worktree inside the repo indexed by VS Code cpptools to 23 GB). Owner answered Q24 B, Q25 B and added F-10. Gate progress: G7(b) injection break-check done, G7(g) branch script.
- S197 (2026-11-22): STATE trimmed under budget; history moved here: G5 freeze-9 every flown row PASS both keys (G5.5 worst 0.499 m), G5.7 FAIL 3/3 at freeze-9 then PASS at freeze-10 (worst 3.98 deg); G3 S191 re-fly after D-AF-ALIAS key1 15/20 key2 16/20, CAUSE_S191 02/05 = 1.45 Hz accel-loop oscillation under uncompensated GNSS +95/+84 ms (S192 matched probe passes), 19 = key-1 land-pulse scope, 03/08 shared with PID; G7 S194 checker self-test defects in bench/tests/SELFTEST_G7_S194.md.
- S197 closed Q24 and Q25 (full text follows, moved from QUESTIONS.md):

### Q24 (S194, 2026-11-21): G3 pre-test at FREEZE-10, four draws fail (BLOCKING for G3 only)
Context. FREEZE-10 pre-test (results/freeze10_s193/g3_pretest/README.md, 20 draws, seed 173): key 1 16/20, key 2
16/20, both keys fail 02, 03, 05, 08 (item 2 = sustained oscillation, item 3 = steady xy error).
- 02/05: GNSS latency uncompensated by +95/+84 ms (GATES l.289 draws latency + U[-100,+100] ms in 50 % of runs).
  q ~1.45 Hz accel-loop oscillation (detector reports its 2.0 Hz band floor), 13-16 dps, xy error ~0.49-0.5 m.
  S192 probe: same draws with matched GNSS pass items 1-3 both keys. PID passes 02/05 (S187 refs). INDI-specific,
  cause shown: the outer loop (D-OFFB-POSVEL, XY gains 1.2/2.4) is less tolerant of a stale position than PID.
- 03 (+20 ms): INDI q 2.0-2.5 Hz, 19-20 dps. PID ref: key 1 FAIL (q 2.5 Hz), key 2 PASS.
- 08 (-63 ms): INDI q 10.75 Hz ~9 dps; PID fails both keys (p 11 Hz, r 8 Hz). Shared with PID.
Options.
 A. Keep the gate. After the queue ends, probe 02/05 (and 03) with lower XY_P/VEL_P (config only). If they pass and
    the G5.5/G5.7 probes hold, declare FREEZE-11 and re-fly G2 outer/G4/G5 outer (~4-5 h CPU, ~2 sessions).
 B. Narrow the mismatch to U[-50,+50] ms and add "EKF2/SENS GNSS delay set within 50 ms of the measured
    latency" to the F-3 requirements and bring-up checklist. Gate change after first test: your call only.
 C. Keep the gate and the gains; G3 NOT PASSED for uncompensated GNSS latency above ~+60 ms, stated as a limit.
 For 08 (and 03 key 1): count as a scenario property shared with PID (reported, not an INDI failure), or count.
Recommendation: A for 02/05/03 (honest fix, config only); 08 reported as shared with PID, not counted against INDI.
Meanwhile: the queue (G5, G4, G2 outer) runs on; no G3 re-fly, re-score or note until answered. Not blocked overall.

**Owner answer to Q24 (2026-11-22):** B for 02/05, and 08 (and 03 key 1) reported as shared with PID.
1. Narrow the EKF GNSS delay mismatch draw to latency + U[-50, +50] ms (min 0); matched/mismatched split stays
   50/50. Add "EKF2/SENS GNSS delay set within 50 ms of the measured GNSS latency" to the F-3 requirements and to
   the bring-up checklist. Record the gate change in GATES.md as an owner amendment (date, Q24 B), with the reason:
   the +-100 ms mismatch exceeds what a correct bring-up leaves, and the S192 matched-GNSS probe shows 02/05 pass.
2. No firmware or config change: FREEZE-10 stands, G2/G4 verdicts stand.
3. 08 and 03 key 1 fail with PID on the same draws: reported in the G3 evidence as scenario properties shared
   with PID, not counted against INDI.
4. How to re-run the pre-test under the new range (re-draw vs. re-fly only the affected draws) is the agent's to
   plan; state the plan in a decision before flying, and keep the earlier 16/20 result in the evidence.

### Q25 (S194, 2026-11-22): G5.5 o2_circle_z s1 fails by 3 mm, PID fails by 0.65 m (BLOCKING for G5 only)
Context. FREEZE-10 G5 re-fly (results/freeze10_s193/G5_SCORES.md): every flown G5 row passes both keys except G5.5
o2_circle_z s1: horizontal RMS truth vs analytic reference 0.5027 m, limit 0.5 m (both keys agree; s2 0.491, s3
0.496; freeze-9 0.488/0.497/0.499 PASS). PID reference, same scenario, seeds and nominal plant
(results/freeze10_s193/g55_pid_ref/README.md): 1.157/1.144/1.146 m, no LOC. The 0.5 m limit is the G3 steady-state
xy limit applied to a moving trajectory (GATES l.462); Q11 B kept it. Coupling: Q24 option A (lower XY gains for the
GNSS-mismatch draws) would most likely raise o2 tracking error further.
Options.
 A. Keep 0.5 m: G5 NOT PASSED on one cell (0.6 % over), all other rows pass; stated as a limit in the report.
 B. Declare the row a test defect (absolute 0.5 m on a circle no reference stack meets) and set a trajectory limit
    sourced from the scenario (e.g. speed x one outer-loop time constant); re-score only, no re-fly.
 C. Keep 0.5 m and accept a tuning change (config) that improves o2 tracking, folded into a FREEZE-11 with Q24.
Recommendation: A (no threshold change after the test to pass a row by 3 mm); B only if you judge the limit wrong
for both stacks. Meanwhile: no G5 re-fly, re-score or note; G2 verdict proceeds. Not blocked overall.

**Owner answer to Q25 (2026-11-22):** B. The absolute 0.5 m horizontal limit is a test defect for moving
offboard trajectories (a steady-state hover limit; no reference stack meets it on o2: PID 1.14-1.16 m).
1. Replace it for the G5.5 trajectory segments with a limit derived from the scenario (e.g. reference speed x one
   outer-loop time constant, or another sourced bound). Write the derivation and its sources in a decision and in
   GATES.md as an owner amendment (date, Q25 B) BEFORE re-scoring; the limit must not be picked from the scores.
2. Apply the same limit to every G5.5 row and to the PID reference; report both stacks against it.
3. Re-score only, no re-fly. Vertical 0.3 m and the offb_vel_step rows are unchanged.

- S198 (2026-11-22): G3 pre-test under Q24 B finished (14 changed draws re-flown, 17/20 both keys, 0 LOC; 03/08 shared
  with PID, 02 item-3 quota miss 0.318 m) -> set-up fixed, WAIT_OWNER for the flight chain. G5 audit gaps closed: events
  seeds 2-3 pass; G5.8 at 3 m/s scorer written with two independent keys, 9/9 PASS; G5 verdict PASSED. G7(f) F-10 plan
  (results/g7_s198/F10_PLAN.md). Gate progress: G5 PASSED (verdict written); G3 pre-test re-scored 16 -> 17/20 under Q24 B.
- S199 (2026-11-22): G3 campaign chain finished (300/300, speed 4), committed. Failure classification (FAILS_S199.md):
  2 LOC (245 C1, 264 C3), item 2 on 79 runs (A 11 Hz, B 2 Hz real; C key-1 landing windows; D borderline), item 3
  94.95 %, 039 harness. Speed-1 re-fly + PID reference of 8 draws (g3_refly_s199): both LOC and A/B lines reproduce,
  PID no LOC and passes 283/239. G3 verdict NOT PASSED at freeze-10; Q26 (step back A vs close as limit B). Gate
  progress: G3 verdict written, NOT PASSED.
- S200 (2026-11-22): G3 chain already committed and verdict written S199 (skipped). Cause search closed on the linear
  model (MARGINS_S200.md): 245/239 2 Hz = rate+attitude cascade at plant tau x3, PM 6/13 deg; 283 GM gap outside the
  model; no fixed ACT_TC covers the G3 tau box. Q26 addendum with option C (tau box = identification error) + A for
  264. D-F10-NEUTRAL written; F-10 unit 1 (McIndiPosControl.cpp) committed, objects identical. Gate progress: G7(f)
  unit 1 of 9 done; G3 failures 245/239 explained on the model (verdict unchanged, Q26 open).
- S201 (2026-11-22): G3 chain item already closed (runs committed 83f98905e5, verdict S199; 3 unscored = explained
  aborts 039/245/264). Q26 still unanswered. F-10 unit 2 committed (21737adf53, objects identical, unit-IndiStageMode
  15/15). docs/en INDI page first draft (fceaa3ebd5, open items report/DOCS_DRAFT_S201.md). Outer-loop report chapter
  draft (report/02_outer_loop_design.md). Gate progress: G7(f) unit 2 of 9 done; G8 docs page and outer-loop chapter
  drafted.
- S202 (2026-11-22): route check RC202 (588efaa409, scope cut: G6/G7/G8 verdicts wait on Q26). F-10 units 3-7
  committed (912f60cc64 .. feb9bf288b, objects identical, unit tests pass). Yaw fit fix (G6 pre-item) started, not
  finished (session cut). Q26 still unanswered. Gate progress: G7(f) units 3-7 of 9 done.
- S203 (2026-11-22): STATE trimmed (S199/S200 cause-search history kept in CAUSE_S199.md, MARGINS_S200.md and the
  S199-S200 journal lines; Q24/Q25 history in S197 line). G3 chain item already closed (runs committed S199/S201).
- S204-S205 (2026-11-22): yaw fit second key (928fe49fc6: code matches spec, CI gate untested MAJOR); route check
  RC205 (710c2cf03f). Gate progress: none (G6 pre-item only; verdicts wait on Q26).
- S206 (2026-11-22): yaw fit test fix verified (14/14, mutants M8/M6/M10 killed; c7ec0740be); A-44 closing run on
  axyaw/half_ax3 G1 207.5/208.1 vs 205.3 (f686875ca7), A-44 closed (V0 597 left unexplained, method removed). RC205
  stands for the supervisor route-check trigger. All work allowed before Q26 done: WAIT_OWNER. Gate progress: none
  (G6 yaw identification pre-item keyed and closed; no gate row scored, G3/G6/G7/G8 verdicts wait on Q26).

## S207 (2026-11-22): Q26 closed, full text
## Q26 (S199, 2026-11-22): G3 NOT PASSED at freeze-10, step back or close as a limit?
Context. The 300-run campaign finished (results/g3_campaign_f10, FAILS_S199.md; re-fly results/g3_refly_s199/SUMMARY.md).
Two losses of control, both reproduced at speed 1, both INDI-specific (PID flies the same draws without LOC): 245
(corner C1: controller G1 x2, motor tau x3, delay 10 ms) diverges in a growing 2 Hz pitch oscillation; 264 (corner C3:
saturation 0.351 plus weak motor 0.709) tilts past 60 deg at the fault. Item 2 fails on 79 runs: real lines class A
(11 Hz pitch, high delay + fast motor + controller G1 below plant, 8 runs) and class B (2 Hz, high delay + slow motor,
37 runs; C1 and C6 fail every run); 283 (A) and 239 (B) reproduce and PID passes them. Item 3 94.95 %. Verdict written
(GATES "G3 verdict at freeze-10"). G2 margins were measured on the nominal plant only; the failures sit where delay and
actuator-model error combine (fixed ACT_TC 0.033 s against plant tau 0.017-0.1 s, no delay in the modelled state), plus
saturation handling with a weak motor. A fix is an inner-loop law change: FREEZE-11 re-opens G2, G4, G5 and the whole
G3 campaign (about 5-7 sessions and 8 h CPU), more than three sessions of finished work.
Options.
- A (recommended): one session of cause search on 245, 239, 283, 264 (logs, linear margin model with the drawn plant);
  if a fix probe removes the failure on a log, FREEZE-11 with the re-flies named above.
- B: close G3 as NOT PASSED with the explanation; state the envelope (delay, tau and G1 mismatch, saturation with a
  weak motor) as a limit and a bring-up requirement in the report; go on to G6-G8.
Meanwhile: the cause search (needed under A and B, every failure must be explained); no firmware change until you
answer. Blocked: only for the firmware change and the re-flies.
S199 cause search, first pass (results/g3_refly_s199/CAUSE_S199.md, describing-function estimates, not yet checked
on the linear model): 245, 239, 283 point to a rate loop with little phase margin when the drawn motor tau departs
from the controller's fixed 0.033 s (x3 slow: 245, 239; x0.5 fast + 10 ms delay: 283); saturation follows the growth.
264: both stacks see the weak-motor yaw collapse; PID recovers, INDI hits its 220 dps rate limit and tilts over.
S200 addendum (linear model with the drawn plants, results/g3_refly_s199/MARGINS_S200.md; model checked against
the nominal G2 roll cell within 1 deg / 1 dB):
- 245 and 239 shown: the rate loop alone keeps PM 44-49 deg, but closing the stock attitude loop around it at plant
  tau x3 (slow) leaves PM 6 deg (245) and 13 deg (239) at 2.1 Hz; model |L| 0.84-0.94 at about -135 deg matches the
  log estimate. The position loop is not needed for the mode. 283 (fast tau, 10 ms delay): model GM 6.2 dB, the log
  shows about 3 dB less; that gap is outside the linear model (vibration x5, dropout). 264 is not modelled.
- No fixed MC_INDI_ACT_TC holds PM 45 deg / GM 6 dB over the G3 box corners (tau x0.5..3, delay 0-10 ms, G1 x0.8-1.2,
  0-3 frames): 0.033 gives worst-case PM 5.7 deg, the best value 0.05 gives 15 deg and lowers 283 to GM 3.6 dB.
  A fixed actuator model cannot cover a x6 tau range; PID flies the same draws without LOC.
- Option C (new): treat the motor time constant like G1 in Q22. MC_INDI_ACT_TC is a physical parameter that the
  procedure identifies (F-3 bring-up item), so the G3 tau factor becomes identification error (for example x[0.7, 1.5],
  up/down asymmetry kept); the x0.5..3 result stays in the report as the unidentified-airframe limit. 264
  (saturation + weak motor, INDI tilts over where PID recovers) is not covered by C and still needs A or B.
- Updated recommendation: C for the tau factor plus A for 264 only (one fix probe on the weak-motor recovery), then
  FREEZE-11 with the re-flies named above if the probe works. Note that C changes a gate after its first test and
  narrows a factor PID passes at full width: your call, not mine.
S202 reminder (route check design/route_check_202.md): G6, G7 and G8 verdicts all wait on Q26 (G6 scope depends on
whether ACT_TC becomes an identified parameter; G7 and G8 depend on whether FREEZE-11 changes firmware). Meanwhile:
G6 yaw fit fix, F-10 clean-up units, no firmware law change, no G3 re-fly. Not blocked yet; blocked once that work is done.
S206: that work is done (yaw fit keyed, A-44 closed; F-10 unit 9 and the F-10 review deferred until after your answer,
since FREEZE-11 may change the code they touch). BLOCKED on Q26 for G3, G6, G7, G8: WAIT_OWNER set.
Owner-session note (2026-11-22, written in the owner's session at the owner's request; NOT an answer: Q26 stays open,
WAIT_OWNER unchanged). Underlying question: should INDI meet the same genericity as PID over airframe and configuration?
INDI replaces the vehicle model (inertia, aerodynamics) by measurement, but keeps a model of the actuator (G1, motor tau,
loop delay): the rate law cancels the motor pole with tau_c = MC_INDI_ACT_TC (D-RATE-LEAD), whose measured safe band is
one-sided, ACT_TC / plant tau in [1, 2] (S53 addendum 2; x0.6 already fails G2). PID has no actuator model to get wrong.
Published multirotor INDI identifies actuator dynamics per vehicle (and adapts G1); none known to us ships one actuator
model for every airframe (from memory, not re-checked). So PID-level genericity is the wrong target for INDI's physical
parameters; it is the right target for its pre-identification state. Points that Option C does not yet state:
1. Box consistency. The G3 run flies the identified quad5in set (ID_OK 1, ACT_TC 0.033) against plant tau x0.5..3,
   i.e. ACT_TC / tau 0.33..2: class B and 245 sit at 0.33-0.45, far below the band the law was designed for. Q22 already
   reduced G1 to identification error on the same reasoning; tau is listed as identified (decision 3, D-RATE-LEAD,
   identification plan) and should follow. G6 is the gate that covers a wrong start through identification.
2. The C box should be one-sided, as the law is: the identification reports an upper bound of tau_c and the procedure
   rounds up (S53 (c)). So the residual error box is ACT_TC / tau about [1, 2] (with the bound's real uncertainty), not a
   symmetric x[0.7, 1.5] around the true value. The quad5in set flies the point estimate 0.033 (S128), which drops the
   round-up rule; S200 also prefers 0.05 on the slow side.
3. Gains as bandwidths (decision 4). K is fixed at 20 rad/s for every tau; with tau x3, K tau reaches the lead cap 2.
   Scaling K with 1/tau_c (identified) is the generic form; worth a model check before FREEZE-11.
4. Pre-identification state (ID_OK 0: gains x0.5, firmware ACT_TC 0.05) is where the full x0.5..3 tau range belongs. It
   has never flown the G3 box. Suggestion: the x0.5..3 campaign result becomes the requirement for that state (a G6
   item), not only a limit sentence in the report.
5. C is untested in flight. The S200 margins are a model; class A (283: fast motor, 10 ms delay, ACT_TC / tau = 2) sits
   inside the band and may survive C (S200: ACT_TC 0.05 lowers its GM to 3.6 dB, so a matched 0.0165 may help; not
   shown). Cheap check, no firmware change: re-fly the 8 S199 re-fly draws (245, 264, 008, 240, 283, 239, 046, 039) at
   speed 1 with ACT_TC = drawn plant tau (slow value), and again with ACT_TC = 1.5 x drawn tau (round-up error). If 245,
   239 (and 283) come out clean, C holds; if not, the cascade needs a law change whatever the box.
6. Not covered by any option: class C (25 runs, key 1 only, touchdown windows, low mass): key 1 runs without the
   nav-change skip that key 2 applies (FAILS_S199.md section 1). This is a scoring-rule mismatch between the keys to settle
   in the verdict, separate from the controller.
264 (saturation plus weak motor) stays under A whatever is chosen for tau. Changing the box after the first test stays
the owner's call; the x0.5..3 result is reported as is in either case.
**Owner answer Q26 (2026-11-22): check first, C not yet chosen.**
1. Re-fly check, no firmware change (FREEZE-10 binary, params file overrides only): the 8 S199 re-fly draws (245, 264,
   008, 240, 283, 239, 046, 039) at speed 1, same index and seeds, in two sets: (a) MC_INDI_ACT_TC = drawn plant tau
   (slow value, max of up/down), standing for a perfect identification; (b) MC_INDI_ACT_TC = 1.5 x drawn plant tau,
   standing for the round-up error. Everything else as in the campaign. Score with both keys, compare per draw with the
   S199 INDI and PID re-flies (one table, like g3_refly_s199/SUMMARY.md). Own results dir; no G3 campaign re-fly.
2. Model check, no flight: K_R/K_P scaled with 1/tau_c (K tau_c held at its quad5in value) against fixed K 20, on the
   drawn plants of 245, 239, 283 and on the G3 box corners (MARGINS_S200 method).
3. 264 stays under A: cause search on the logs only, no fix probe in firmware yet.
4. Class C (key 1 without the nav-change skip): write how the verdict should treat it; settle it in the verdict, not
   in the controller.
5. Then report the results in a new question (Q27) with a recommendation on C (box shape, one-sided as in note point
   2), K scaling, the pre-identification requirement (note point 4) and FREEZE-11. No box change, no gate text change
   and no firmware change before my answer to Q27. G6-G8 stay as they are until then.
- S207 (2026-11-22): Q26 owner answer acted on. RC207 filed (cuts: G7 (f)(g), G8 drafting, key-1 fix stay deferred). Item 1: 16 INDI re-flies (results/q26_actc_s207): ACT_TC = tau clears 245, 239, 283; 1.5 tau clears 245, 239, keeps 283/008 10.75 Hz; 264 LOC in both. Item 2 (q26_kscale_s207): K scaled with 1/tau_c worse than fixed K; matched ACT_TC worst PM 5.7 -> 35.9 deg. Item 3 (q26_264_s207): CW rotor collapse, INDI counter-torque about half of PID (likely). Item 4: class C = Q15 A skip missing from G3 key 1. Q27 asked, WAIT_OWNER. Gate progress: none (G3 check data for Q27; no gate row scored, verdicts wait on Q27).
- S208 (2026-11-22): Q27 closed. Question and owner answer as asked:
  ## Q27 (S207, 2026-11-22): Q26 check results; choose the tau box, K rule, pre-identification item, FREEZE-11
  BLOCKING for G3 (box and test text), and through it for G6, G7, G8. Results: results/q26_actc_s207/README.md (table),
  results/q26_kscale_s207/README.md, results/q26_264_s207/README.md. FREEZE-10 binary throughout, params overrides only.
  1. Re-fly, 8 S199 draws at speed 1 (S199 INDI -> set a ACT_TC = drawn tau_slow -> set b 1.5 x tau_slow), keys k1/k2:
     245 (C1, LOC) ABORT -> PASS/PASS -> PASS/PASS; 239 (B) FAIL 2 Hz 76 dps -> PASS/PASS -> PASS/PASS;
     283 (A: fast motor, 10 ms) FAIL 10.75 Hz 18 dps -> PASS/PASS -> FAIL/FAIL 10.75 Hz 9-13 dps (PID passes);
     008 (A) FAIL 10.75 Hz -> k1 FAIL 2.0 Hz 10.5, k2 PASS -> FAIL/FAIL 10.75 Hz 6-7 (PID fails it harder, 161-207 dps);
     046 (D) FAIL both -> k2 FAIL 2.0 Hz 13.4 -> PASS/PASS; 240 (class C) k1 FAIL -> k1 FAIL -> PASS/PASS;
     039 land wall timeout (harness, both stacks) in every set, scored PASS; 264 ABORT tilt > 60 deg in both sets.
     So an identified ACT_TC removes the slow-motor LOC and the 2 Hz class B; the round-up end (x1.5) keeps the
     fast-motor class A line (lower RMS).
  2. Model (MARGINS_S200 method, worst over the realised G3-box corners, PM deg / GM dB): ACT_TC 0.033 fixed 5.7 / 3.1;
     ACT_TC = tau, K 20: 35.9 / 6.8; ACT_TC = 1.5 tau, K 20: 36.2 / 5.3. K scaled with 1/tau_c: 13.8 / 1.4 (a), 33.3 / 3.1 (b),
     worse in both (K reaches 40 on fast motors; 283 GM 9.5 -> 3.2 dB). No rule gives PM 45 on every corner (binding:
     tau x3 + 10 ms + G1 error 1.2). G2 is measured on the nominal plant and is not affected.
  3. 264 (log only): a 20 ms collapse of both CW rotor speeds (11600 -> 7000 rpm, command flat) hits both stacks; no
     saturation, no unallocated torque. INDI's pitch/roll counter-torque is 55-80 % of PID's for 0.2 s; the rate setpoint
     reaches 220 dps; tilt > 60 deg. Likely (not shown): low rate-loop gain against a large disturbance. Unexplained: why
     the rotors collapse (injector or Gazebo model at speed scale 0.351; not traced).
  4. Class C: Q15 A (skip windows overlapping the 3 s after a nav_state change) is written for G4 only; G3 key 2 applies
     it, key 1 (g3_score.sh) does not. Proposed rule: Q15 A applies to G3 item 2 for both keys (transitions are judged by
     G5); key 1 re-scored with its existing --skip-nav-change. Freeze-10 item 2 drops from 79 to at most 54 runs:
     verdict unchanged (NOT PASSED).
  Options and recommendation:
  - C1 (recommended): tau becomes identification error, one-sided ACT_TC / tau_slow in U[1, 1.5] with up/down asymmetry
    kept; K fixed 20 (no 1/tau_c scaling: the model rejects it); x0.5..3 result reported as the unidentified limit. No
    firmware change, so FREEZE-10 and G2, G4, G5 stand; only the 300-run G3 campaign is re-flown (tooling: draw the
    controller ACT_TC like the controller G1 error, about 8 h CPU), with the class C rule above. Risk, stated now: class A
    draws near the x1.5 end may still fail item 2 (283, 008 set b), and 264 still fails item 1.
  - C2: as C1 with [1, 1.2] (tighter identification claim). Removes 283 at the cost of a stronger bring-up requirement.
  - B: close G3 NOT PASSED as written, report this check as the path; go to G6-G8.
  264 (needs your call whatever the box): (i, recommended) one session: confirm the rotor collapse is the drawn fault,
  then a params-only probe of MC_INDI_K_R/P 30 and 40 on 264 with model margins; if it recovers with margins kept, the
  new default is FREEZE-11 (firmware default change, re-flies G2, G4, G5 and G3); (ii) report 264 as a limit.
  Pre-identification state (ID_OK 0, gains x0.5, ACT_TC 0.05): recommend a G6 item "flies the x0.5..3 tau box without
  LOC" on a reduced set (the 8 draws plus the 16 box corners, item 2 reported, not required), not a second 300-run campaign.
  Meanwhile: nothing (route check 207: every gate item waits on this answer). Blocked: yes, WAIT_OWNER.
  **Owner answer Q27 (2026-11-22, with an independent review in the owner's session): identify first, no box change now.**
  1. tau box: none of C1, C2, B as written. No ACT_TC identification with a measured error exists, so no box can be
     justified yet; C2 ([1, 1.2], chosen because 283 fails at 1.5) is rejected as fitting the test to the result. Next:
     build and validate the ACT_TC identification step (decision 3, G6 work), and measure its error over plant tau
     x0.5..3 (up/down asymmetry kept, and whether it returns tau_slow or a mean), delay 0-10 ms and telemetry frames 0-3.
     Then write the G3 tau box from that measured bound, in GATES.md, before any G3 flight. Plant tau in G3 stays drawn
     x0.5..3 (owner range); only the controller ACT_TC is drawn as identification error. G3 stands NOT PASSED as written
     until then.
  2. S53 rule (D-RATE-LEAD addendum 2, "identification errs high, round up"): record it as overturned. 283 (tau 16.5 ms,
     10 ms delay) fails at ACT_TC x1.5 and x2 and passes at x1, which meets its own overturn clause. Replace it with a
     capped or two-sided rule derived from the identification bound of item 1 and the delay, with model margins on the
     box corners.
  3. K: fixed K 20 stays; no 1/tau_c scaling (rejected by the model with MC_ROLL/PITCH_P 8 held; scaling the attitude
     gain too was not checked and is not asked for now). Report the model margins on the realised box (best rule about
     36 deg PM / 5-7 dB GM, below G2's 45 deg / 6 dB) as a stated limit for G8, with the 3 dB model optimism seen on 283.
  4. 264: report as a limit (option ii). The report states what is shown (both stacks get the CW rotor-speed collapse;
     INDI applies 55-80 % of PID's counter-torque and tilts over, PID recovers) and what is not (origin of the collapse,
     possibly the gz rotor model at speed scale 0.351, untraced). No K change, no FREEZE-11 for 264.
  5. Items 3-6: decision 5 of G3-G8 FINAL S94 (GATES.md line 231, no quota) governs. Correct the contradicting test text
     (GATES.md line 316, "items 3-6 met in >= 95 %") and the campaign README verdict wording. Every item 3-6 miss in a
     valid run is a failure after the speed-1 re-fly rule; the 15 freeze-10 misses are re-flown at speed 1 when the next
     G3 campaign is scored, not now.
  6. Class C: accepted with conditions. Q15 A (skip windows overlapping the 3 s after a nav_state change) applies to G3
     item 2 on both keys, recorded in GATES as a test-definition change after the first test (key 2 applied it without
     the text allowing it). Report the skipped land-entry lines for both stacks, and check PID on the class C draws
     (240 PID also shows a key 1 line). Do not claim that G5 covers these windows: G5 flies the nominal plant only.
  7. Un-identified state (ID_OK 0, gains x0.5, ACT_TC 0.05): a G6 item of about 100 Latin-hypercube runs over the full
     G3 box (tau x0.5..3) plus the box corners, flown at ID_OK 0. LOC required; item 2 required at least during the
     identification manoeuvre (an oscillation there corrupts the fit), reported elsewhere. The freeze-10 x0.5..3 result
     was flown at ID_OK 1 with ACT_TC 0.033: never label it "the unidentified limit".
  8. Harness, before any new campaign: 039 (LAND overridden by the stick re-centre, wall timeout) is an invalid run,
     not a PASS; fix the runner defect and score harness aborts as invalid (re-flown), per the existing failure rule.
  9. Order: items 2-6 and 8 are text and tooling (no flight beyond checks); then item 1 (identification and its error
     measurement) and item 7 inside G6. FREEZE-10 stays; no firmware change unless the identification needs one, and then
     ask first. Come back with a question when the identification bound is measured and the G3 box is proposed.
- S208 (2026-11-22): Q27 acted on (GATES "Owner amendments S208", D-OWNER-Q27, S53 rule overturned); RC208 filed; G3 harness fixed (039 lands, aborts INVALID, key 1 skip-nav-change); ACT_TC ident: survey, design note, GATES 6c, D-ACTC-IDENT, estimator key 1 with self-test (all 6c synthetic limits met; tau_sym 0.61 x tau_slow at asym 3); key 2 launched. Gate progress: G3 test text amended per Q27 and harness ready for the re-fly; G6 6c criteria written, estimator key 1 passed its self-test.
- S208 history moved from STATE (S209 trim): GATES 6c, design note, estimator key 1 78387a01da (all 6c limits met); KEY2 75a333e518 (model/thresholds/real log PASS, pos0 33.9 vs 33 ms; sub-sample delay bias -16 % -> FRD fix); G3 harness 86539dac11 (LAND holds last stick, aborts INVALID both keys, key 1 --skip-nav-change), 039 lands at speed 1 (results/harness_039_s208), PID not re-flown on 039. G7 (f) F-10 units 1-7 done (F10_UNIT1..7.md, objdump identical, two "INDI stage" log strings left). G6 yaw fit keyed 57e80feac8 + c7ec0740be, A-44 closed (results/ident_yaw_a44_s205). CUT RC204/RC205 superseded by RC208.
- S209 (2026-11-23): STATE trimmed; ACT_TC estimator fractional-delay fix (2dd2110a0c, off-grid bias -16 % -> -0.6 % on key-2 plant); grid driver bench/actc_grid.py, 2-flight pre-test, 30-cell grid flown (0/30 failed, tau_up/down <= 3.7 %, tau_sym/tau_mean 0.90-1.00, delay within 0.1 ms); table script + self-test; box model margins (BOX_MARGINS.md); A-59 filed (telemetry-frames hook inert, also in G3 campaign); Q28 written (rule A). Gate progress: G6 6c ACT_TC identification error measured and tabled (GATE_STATUS G6 row); G3 box proposed to owner (Q28).
- S209 addendum: grid first fitted the SITL truth esc_status instance; refit on telemetry instance 0 (fdef565b87, REFIT_INST0.md) gives the same bounds (within 0.003) and shows frames (+3.8 ms); A-59 closed (hook works on both paths, G3 frames factor was applied). Q28 stands. Gate progress: G6 6c bound now on telemetry data.
- S210 (2026-11-23): g3_campaign_f10 re-checked (committed, 297 scored + 3 aborts, verdict S199 stands); STATE corrected (unit 8 was committed b34adf0c95); independent F-10 review of unit 8: PASS with MINORs (wording only, results/g7_s198/F10_UNIT8_REVIEW.md, deferred to whole-branch pass). Q28 open, no unblocked gate work: WAIT_OWNER. Gate progress: G7 (f) unit 8 reviewed.
- S211 (2026-11-23): Q28 closed. Question and owner answer as asked:
  ## Q28 (S209, 2026-11-23): G3 controller-ACT_TC box and ACT_TC rule from the measured identification bound. BLOCKING for G3 (test definition) and for G6 item 7 ordering
  Context (Q27 item 1, GATES 6c):
  - Estimator `bench/ident_actc.py` (two keys; off-grid delay fix 2dd2110a0c) flown on the 30-cell grid of 6c
    (`results/actc_grid_s209/README.md`): plant tau_slow x0.5..3 of 33 ms, asym 1 / 3 down-slow / 3 up-slow, delay 0 / 10 ms.
  - 0/30 failed identifications. Per motor tau_up and tau_down within 3.7 %; delay recovered within 0.1 ms (+1.75 ms offset).
  - The single tau the firmware takes (symmetric fit tau_sym) returns a mean, never tau_slow: tau_sym / tau_mean = 0.996-1.002
    (asym 1), 0.90-0.98 (asym 3); tau_sym / tau_slow = 0.60-0.66 at asym 3. It never exceeds tau_mean by more than 0.2 %.
  - Limits: telemetry frames 0-3 NOT applied (simulator hook inert, A-59; the 10 ms delay cells cover more delay than
    3 frames); one seed except 4 corners; roll injector only; sim speed 4.
  - Model margins at the box corners (`results/actc_grid_s209/BOX_MARGINS.md`, same method as Q27, 800 Hz, worst over
    G1 x0.8/1.2): proposed box rate 30.6 deg / 3.4 dB / 10.4 ms, rate+att 19.9 deg / 3.2 dB (corner tau_mean x3, 10 ms,
    asym 3); fixed 0.033 (freeze-10 campaign) rate+att UNSTABLE at the same corner. Symmetric plants: box rate+att 32 deg
    vs fixed 5.7 deg. Below G2's 45 deg / 6 dB at the slow + 10 ms corners: reported as a limit per Q27 item 3.
  Options:
  - A (recommended). Rule: MC_INDI_ACT_TC = median over motors of the identified tau_sym, no rounding, no cap (the
    estimator never errs high; 283 showed erring high is the harmful side). G3 box: controller ACT_TC = r x plant tau_mean,
    r drawn uniform [0.88, 1.02] (measured 0.90-1.00 plus 2 % estimator error each side), independent of the other draws.
  - B. Same rule, r drawn from the asymmetry-dependent measured relation (r = 1 at asym 1, 0.90-0.98 at asym 3) plus
    +-4 %. Closer to reality, harder to explain; margins nearly the same.
  - C. Rule ACT_TC = identified tau_slow (from tau_up/tau_down). Matches the slow motor but the controller then runs
    above the mean on asymmetric motors, the side 283 failed on.
  Meanwhile (not decided by this question): fix the telemetry-latency hook (A-59, one session, simplest injector, two
  keys; if it does not fly after that session, I ask to drop the frames factor), and G7 unit 8. No G3 or G6 item-7 flight.
  Blocked: G3 re-fly and G6 item 7 only.
  CORRECTION S209 (same session, before any answer): `ident_actc.py:275` reads the highest esc_status instance, which in
  SITL is the simulator's TRUE rotor speed (gz_bridge truth publisher), not the telemetry instance 0 a vehicle has. The
  grid numbers above therefore measure the fit on true rotor speed: they are a best case, not the bound. Do not answer
  from them yet. Next session: fit instance 0 on the same 30 logs (no flight), re-table, re-run box margins, and update
  this question. This also explains A-59 (the delayed telemetry was never fitted).
  RESOLVED S209: refit on telemetry instance 0 (results/actc_grid_s209/REFIT_INST0.md, --esc-instance 0 now default):
  0/30 failed, tau_up/down <= 3.9 %, r_mean 0.898-1.004 (each bound within 0.003 of the truth fit), frames 3 seen
  (+3.8 ms delay). Box r [0.88, 1.02] and BOX_MARGINS unchanged. Q28 stands as written above; A-59 closed (hook works).
  CORRECTION S211 (independent review, results/actc_grid_s209/Q28_REVIEW.md): the box stands, the wording above does not.
  On telemetry instance 0: tau_up/down <= 3.9 % (not 3.7); delay offset +2.9 ms at frames 0 and +6.7 ms at frames 3 (not
  +1.75); tau_sym (median of 4 motors) reaches 1.0039 x tau_mean on symmetric plants, so "never exceeds tau_mean by more
  than 0.2 %" and option A's "never errs high" are false: it errs high by up to 0.4 %. The upper edge 1.02 is the measured
  max + 1.6 %, not + 2 %; the lower edge 0.8983 x 0.98 = 0.880 holds. Limits added: the bound holds for the median of 4
  only (single motors 0.843-1.040, split by diagonal pair on the roll injector); the 2 % allowance equals the largest
  seed spread seen (2.0 %, 4 pairs), no slack; the linear model is flat in r from 1.02 to 1.05
  (box_margins_r_upper.tsv), so the upper edge rests on flight evidence only (283 fails at x1.5); delay_hat on instance 0
  includes telemetry delay and is never fed to a delay parameter. Review verdicts: A agree with these changes, box
  agree, B and C rejected.
  Owner answer (2026-11-23, S211): A, as recommended and confirmed by the independent review
  (results/actc_grid_s209/Q28_REVIEW.md). Rule MC_INDI_ACT_TC = median over the 4 motors of the identified tau_sym, no
  rounding, no cap. G3 box: controller ACT_TC = r x plant tau_mean (tau_mean = (tau_up + tau_down) / 2), r uniform
  [0.88, 1.02], independent of the other draws. Box kept at 1.02 with the S211 wording corrections and limits.
- S211 (2026-11-23): Q28 wording corrected from an independent review (2c94a727ca: telemetry-instance numbers, tau_sym up to 0.4 % high, upper edge = max + 1.6 %, median-of-4 and no-slack limits); owner answer A recorded (GATES "Owner amendment S211", D-OWNER-Q28, D-ACTC-RULE accepted). Gate progress: G3 controller-ACT_TC box written; G3 re-fly and G6 item 7 unblocked (sampler draw of controller ACT_TC not yet built).
- S211 (2026-11-23): Q29 closed. Question and owner answer as asked:
  ## Q29 (S211, 2026-11-23): reduce the G3 re-fly and G6 item 7 to the critical runs? BLOCKING for the G3 / G6 chain size
  Context: Q28 answered (box r [0.88, 1.02] x tau_mean). Planned chain: G3 300 runs (240 LHS + 60 corners C1-C6, owner
  floor, GATES 3), the 15 freeze-10 item-3 misses re-flown at speed 1 (S208), G6 item 7 ~100 LHS + corners at ID_OK 0.
  About 45 s per run at speed 4: G3 ~3.8 h, G6 ~1.3 h, plus scoring (both keys) and classification.
  Where freeze-10 failed (results/g3_campaign_f10/SCORES.tsv, any key or abort, 87/300):
  - Corners: C1 10/10, C6 10/10, C4 8/10, C5 5/10, C3 4/10, C2 0/10. Both LOC were corners (245 C1, 264 C3).
  - LHS 50/240. Item 1-2 fails by quadrant: tau >= 1.5 & delay >= 5 ms 19/52; tau >= 1.5 & < 5 ms 9/41;
    tau < 1.5 & >= 5 ms 14/81; tau < 1.5 & < 5 ms 5/66. Failures are not confined to an obvious critical region.
  - The 300-run floor is what bounds the safety-failure rate below 1 % at 95 % (rule of three, GATES 3 "Campaign pass").
  Options (G3):
  - A (recommended). Keep 300, fly critical first and stop early: corners (60) and the 50 S199 LHS fail/abort draws
    (same seeds, new r draw) first; halt the chain on the first item 1 or 2 failure confirmed on both keys, otherwise
    finish the remaining 190 LHS. Same gate claim (< 1 %); saves ~2.5 h only when it fails, as freeze-10 did.
  - B. 160 runs: 60 corners + 100 fresh LHS, plus the 50 S199 LHS fail draws as targeted evidence (not counted). Bound
    becomes < 3 % at 95 % from the 100 LHS (corners are not distribution samples). Needs the GATES 3 floor changed.
  - C. Critical only: corners + the S199 fail/abort draws (~110 runs). No rate bound: shows the observed failures are
    fixed, not that G3 holds; G3 could not be marked PASSED under the current text.
  Also proposed (all options):
  - Drop the speed-1 re-fly of the 15 freeze-10 item-3 misses: they were flown at the old ACT_TC 0.033; every miss of
    the new campaign goes through the speed-1 rule anyway.
  - G6 item 7: fly the 60 corners only (pass = item 1, no LOC; item 2 inside the ident window). Both freeze-10 LOC were
    corners, and ID_OK 0 (gains x0.5, ACT_TC 0.05) is the conservative state. Cuts ~100 runs to 60. The ~100 LHS
    (Q27 item 7, owner text) is dropped; G8 states the reduced coverage as a limit.
  Not affected: the sampler r draw and its review (needed in every option); no firmware change.
  Owner answer (2026-11-23, S211): A, with the two proposed cuts (no speed-1 re-fly of the 15 freeze-10 item-3
  misses; G6 item 7 = the 60 corners at ID_OK 0). Relaunch the orchestrator with WEEKLY_SHARE 0.9.
- S211: Q29 acted on (GATES "Owner amendment S211b", D-OWNER-Q29); supervisor restarted with WEEKLY_SHARE 0.9. Gate progress: G3 re-fly order and G6 item 7 size fixed; next is the sampler r draw + review, then the chain.
- S212: G3 re-fly tooling (r draw, per-run ACT_TC, critical-first order, --halt-on-fail; 77572243f5) reviewed
  independently (results/g3_refly_actc_s212/REVIEW_S212.md, 2 halt gaps closed); pre-test runs 110-111 OK (ULog ACT_TC
  equals sample); chain C212 (300 runs, speed 4) launched 2026-11-23 19:42. Gate progress: G3 re-fly flying (tooling
  keyed, pre-test passed).
- S213 (2026-11-23): chain C212 halted at run 022 (draw 262, C3) on item 2 both keys; runs 000-022 committed. Speed-1
  re-fly (results/g3_refly_actc_s212/speed1_s213/): INDI item 2 passes both keys, PID fails item 2 (p/q 2.0 Hz) on the
  same draw -> halt not confirmed, chain resumed 20:10. INDI item 3 0.308 m vs 0.30 at speed 1 (PID 0.138):
  ITEM3_DECOMP.md shows settling inside a 3 s window opening 0.5 s after arrival, not a steady gap; the scorer's 3 s
  window deviates from the GATES "last 10 s of a hold >= 20 s" and was never recorded -> Q30 to the owner, blocking
  item 3. Gate progress: G3 run 022 item 2 resolved (not confirmed), item 3 window question Q30.
- S213 (cont.): chain halted again at run 024 (draw 264, C3): INDI LOC (tilt > 60 deg) at 60.8 s speed 4 and 61.0 s
  speed 1 with ACT_TC 0.0177, same as freeze-10 at ACT_TC 0.033; PID no LOC. G3 verdict NOT PASSED written (GATES
  S213 section); Q31 (route A/B/C) to the owner, blocking G3 and G6. Gate progress: G3 re-fly verdict NOT PASSED.
- S214 (2026-11-23, owner interactive session): Q30 closed. Question and owner answer as asked:
  ## Q30 (S213, 2026-11-23): G3 item 3 window. BLOCKING for G3 item 3 (not for items 1, 2, 4-6)
  Question: which window scores G3 item 3 (steady-state horizontal RMS <= 0.30 m with wind)?
  Context:
  - GATES (line ~255) defines it as "last 10 s of a hold >= 20 s after the last transient, truth". The scorer
    `bench/g3_score.sh` (header "DEVIATION, stand-in scenarios have no 20 s hold") scores the final 3 s hold segment,
    which starts about 0.5 s after the arrival from the trajectory. This deviation was never written in GATES or
    DECISIONS. It also scored the freeze-10 campaign (15 item-3 misses, then under a 95 % quota).
  - Chain C212 run 022 (draw 262, corner C3, thrust 0.351, wind 1.7 m/s) item 3: INDI 0.317 m (speed 4), 0.308 m
    (speed 1, both keys) -> a confirmed miss under the S208 no-quota rule. PID, same draw, speed 1: 0.138 m.
  - Decomposition (`results/g3_refly_actc_s212/speed1_s213/ITEM3_DECOMP.md`): mean offset INDI 0.10-0.13 m, PID 0.12 m
    (no steady gap); the excess is INDI settling from 0.6 to 0.15 m in about 2 s inside the window (PID about 0.5 s).
    Over the last 1.5 s of the window: INDI 0.13-0.19 m, PID 0.08 m. Item 3 here measures settling, not steady state.
    Item 5 (recovery <= 5 s) is the row that covers settling.
  - Item 2 at speed 1 passes for INDI on run 022 (PID fails item 2 on the same draw), so the halt was not confirmed and
    the chain resumed on 2026-11-23 at 20:10 for items 1 and 2.
  Options:
  - A. Keep the 3 s window (write the deviation into GATES). Run 022 fails item 3, so G3 is NOT PASSED for this campaign.
  - B. (recommended) Apply the written rule: lengthen the final hold of the G3 scenarios to >= 20 s, score its last
    10 s. Only the scenario timing changes, no threshold changes. The campaign restarts (CPU only, about +5 s wall per
    run at speed 4). The current chain keeps flying meanwhile as early item 1 and 2 evidence. A confirmed item 1 or 2
    failure there still ends G3 as NOT PASSED.
  - C. Keep the flights and score item 3 on the last 1.5 s of the 3 s hold. Not recommended: the window would be
    chosen after seeing the data.
  Meanwhile: chain C212 flies for items 1 and 2, and its item-3 scores are not read or re-flown. G8 drafting continues.
  Blocked: G3 item 3 rows only.
  Owner answer (2026-11-23, S214): B, with the independent review's changes (results/g3_refly_actc_s212/Q30_REVIEW.md):
  dedicated G3 scenarios with a >= 20 s final hold (o1_lemniscate and stick_zsine_o6 left untouched for G5), steady
  wind kept to the end (no wrench clear in the hold), sag ramp fixed at its drawn length, window = last 10 s of the
  hold, item 6 = last 20 s, each key computes its own window; GATES 3 text corrected (events start at the main
  segment, not the hold). C212 stays halted (Q31); the next campaign uses the new scenarios.
- S214: Q30 acted on (GATES "Owner amendment S214", D-OWNER-Q30, review Q30_REVIEW.md; ITEM3_DECOMP gust-timing line corrected there: gust ends ~5 s before the 022 window, mixed time bases). Gate progress: G3 item 3 window fixed for the next campaign; tooling (G3 scenarios, scorer t0, key-2 window, items 5-6) to build after Q31.
- S215 (trim): STATE next action 1 history moved here: ACT_TC identification chain (survey s208 -> estimator, self-test,
  second key, offline grid, confirmation flights, bound) DONE S209 in results/actc_grid_s209 (README, REFIT_INST0,
  BOX_MARGINS); Q28 answered A S211, box in GATES. g3_campaign_f10 chain committed, 297 scored + 3 aborts
  (039/245/264), verdict written S199, re-checked S210 and S215 (nothing uncommitted, no re-score needed).
- S215: Q31 still open (G3, G6 blocked). STATE trimmed. G8 drafts report/01_inner_loop_design.md and
  06_bringup_checklist.md (sonnet; Unverified sections open; ACT_TC yaml "round up" text confirmed stale, G7 param
  pass). G7 checker defects closed: offb_vel/passthrough verdict, LOC, empty-topic INVALID, 8 break-checked tests,
  re-score of G5.5 seeds 1-3 and S133 logs unchanged (results/g7_checkers_s215). Gate progress: G7 open-items list
  (checker defects closed), G8 chapters 1 and 6 drafted.
- S214 (2026-11-23, owner interactive): Q31 cause search. Simulator injector defect found and fixed (GZBridge 1 s param interval split multi-motor EC_MAX writes 1 s apart; f110361a33, owner allowed the stock change); binary 903eae63 (FREEZE-10 sources + fix) built and checked; draw 264 re-flown s1 on it: INDI LOC, PID 37 deg. Evidence results/q31_injector_fix_s214/README.md; Q31 addendum. Gate progress: G3 C3 fault now applied as drawn; pre-S214 C3 runs fail GATES 2 validity; the 264 LOC is real.
- S216 (2026-11-23): supervisor item "G3 chain g3_campaign_f10 finished" was already done (runs committed 83f98905e5, 3 unscored = 039 abort, 245/264 LOC, verdict S199 written); nothing re-scored (Q31 open). G8 drafts: report/A_history_errata.md (appendix A), report/03_validation.md (G1/G2/G4/G5; G3/G6/G7 pending). GATE_STATUS G5 evidence path corrected (freeze10_s193/g5_gaps_s198). Gate progress: G8 appendix A and ch.3 (passed gates) drafted.
- S217 (2026-11-23): supervisor item "G3 chain g3_campaign_f10 finished" already done (S216; verdict S199 written), skipped. STATE trimmed under budget. G8 drafts: Unverified items of report 01/03/06/A checked against sources (report/UNVERIFIED_S217.md): 6 closed, 3 corrected (G5.11 limits in ch.3 now 1 deg / 0.5 m per F10 G5_SCORES.md:160; ACT_TC yaml path; DSHOT_MOT_POL default), 34 open with reasons (flights, Q31, G7 pass). Q31 still open, no unblocked work left: WAIT_OWNER. Gate progress: G8 report drafts, 9 unverified items resolved.
- S218 (2026-11-23, owner interactive): Q31 closed. Question and owner answer as asked:
  ## Q31 (S213, 2026-11-23): G3 halted on an INDI loss of control at corner C3. BLOCKING for G3 and G6
  Question: after the second G3 NOT PASSED, which route do we take?
  Context:
  - Chain C212 (ACT_TC drawn in the S211 box) halted at run 024, draw 264, corner C3: thrust scale 0.351 on all motors,
    motor 3 further x0.709 (ceiling 0.249), mass x1.3. INDI tilts past 60 deg at 60.8 s (speed 4) and 61.0 s (speed 1).
    The same plant at freeze-10 (ACT_TC 0.033) lost control at the same time: identifying ACT_TC did not change it.
    PID flies the draw (tilt max 40 deg). Verdict written: GATES "G3 verdict, re-fly ... (S213)".
  - Mechanism on the S199 logs (`results/g3_refly_s199/CAUSE_S199.md`): at the fault both stacks spin up in yaw (weak CW
    rotors). PID recovers roll/pitch, but INDI's pitch rate runs against its setpoint and every rate setpoint reaches the
    220 dps limit. Motor 3 saturates only after the tilt is lost. Shown on the log: yaw first, then INDI fails to recover.
    Inferred, not tested: why INDI fails to recover (no roll/pitch-over-yaw priority in the increment, or the measured
    torque gap from the unknown weak motor).
  - The GATES failure-explanation rule (restore drawn factors one at a time) has not been run on 264.
  Options:
  - A. Stop G3 here. G3 is NOT PASSED, and the C3 corner (saturation plus weak motor) is a stated limit in G8. G6 item 7
    and G7/G8 go ahead on freeze-10, and G6 is reported as not passable because it requires G3.
  - B. (recommended) One session of factor restoration on 264 (data only, about 10 speed-1 flights). Then, only if a fix
    probe removes the loss of control on the log, one firmware fix (freeze discipline). The rows it invalidates are
    named and re-flown (G2/G4/G5 subsets), then the G3 campaign restarts critical first. If the restoration shows
    beyond-range physics (class b), the result comes back to you.
  - C. Re-open the outer/inner-loop saturation design (yaw priority in the INDI increment) as a design step before any
    probe. That costs more sessions.
  Meanwhile: nothing flies. G8 drafting continues (not decided by Q30/Q31); G6 item 7 waits. Q30 stays open for the next campaign.
  Blocked: G3, G6. Not blocked: G8 drafting, G7 items that do not touch firmware.
  ADDENDUM S214 (owner interactive session, owner allowed a stock-PX4 change for the injector; not an answer):
  results/q31_injector_fix_s214/README.md. (1) The simulator bridge applied SIM_GZ_EC_MAX writes at most once per
  second, so every C3 flight before S214 (freeze-10 264, C212 run 024 and their speed-1 re-flies) got a CCW-only limit
  for 1 s, then a sudden CW limit: GATES 2 run validity fails on them; the "CW rotor-speed collapse" of Q27 item 4 is this
  artefact. Fixed in f110361a33 (sim only); binary 903eae63 = FREEZE-10 sources + fix, only GZBridge symbols differ, the
  other frozen build files match. (2) On the fixed binary draw 264 still loses control for INDI (tilt 60 deg at 59.9 s)
  and PID flies it (37 deg): the LOC is real and INDI-specific. (3) Yaw is no longer involved (yaw torque sp <= 0.06), so
  roll/pitch-over-yaw priority is not the mechanism; INDI's pitch rate overshoots (+194 dps) and the measured torque
  then lags the commanded torque (-0.02..-0.04 vs -0.09) until the tilt is lost. Inferred: the nominal W_MAX
  normalisation of the measured torque after a max-rotor-speed loss. Factor restoration (option B) can now run on a
  valid fault. Open for the owner: which binary G3 uses from now on (g3_chain.sh still pins d220e193).
  Owner answer (2026-11-23, S218): B, with an escalation route; and adopt binary 903eae63.
  1. B: GATES factor restoration on draw 264 at speed 1 on binary 903eae63 (one factor at a time, smallest subset that
     removes the LOC), then one fix probe if a cause is shown on the log; class (b) beyond-range physics comes back to me.
  2. If the issue persists after B: two independent investigation agents in parallel (model opus, effort high), each
     identifies the mechanism and writes its own report; then one solving agent (opus, high) proposes and implements the
     fix from both reports, plus an independent review agent. Pre-approved, no further question needed to launch them.
  3. If the LOC is still there at the end: write an owner question, continue investigating or stop here.
  Binary: 903eae63 (FREEZE-10 sources + GZBridge fix f110361a33) is the gate binary from now on; pre-S214 C3 runs
  (saturation draws) fail GATES 2 validity.
- S218: Q31 acted on (GATES "Owner amendment S218", D-OWNER-Q31, D-BINARY-GZFIX; g3_chain.sh pin -> 903eae63). Gate progress: G3 binary and C3 validity fixed; draw-264 restoration (B) unblocked.
- S219-S220: Q31 route B done (results/g3_refly_actc_s212/restore264/README.md, 14 rows): restoring saturation, weak
  motor or mass alone removes the draw-264 LOC; the other 10 single restorations do not. Joint probe (only saturation
  0.351 + weak motor 0.709 drawn, rest nominal): INDI LOC 1.1 s after the fault, PID survives (38 deg max tilt) ->
  INDI-specific, minimal reproduction. Route check 220 filed (design/route_check_220.md), acted on (sweeps ended).
  Next: Q31 escalation (2 opus investigators). Gate progress: G3 item 1 cause isolated to saturation + weak motor
  (INDI-specific); no GATE_STATUS row changed (no new scored evidence).
- S221 (2026-11-24): STATE trimmed; route check 221 filed (design/route_check_221.md, G6 item 7 chain cut until Q31 route ends). Q31 escalation: 2 independent opus investigators (restore264/INVESTIGATION_A.md, _B.md) agree: draw-264 joint LOC = loss of integral action in the INDI rate loop (weak-motor torque bias, leaky measured anchor at 0.351, 1 s blend only integrator; no saturation before LOC); PID survives on higher P + integrator. Next: param-only falsifier probes, then solver. Gate progress: G3 item 1 cause identified on logs by two independent reports (decision 2 re-opened); no GATE_STATUS row changed (no scored evidence).
- S222 (2026-11-24): supervisor route check: RC221 still current, blocker = G3 item 1 Q31 route, G8 drafting paused (STATE). g3_campaign_f10 already committed and verdict written. Q31 falsifier probes on draw-264 joint (restore264/falsifier_s222): ACT_BLD 0.15 and W_MAX 0 (model only) both survive (no LOC, tilt 53.5/45.3 vs 86.7 deg) but fail item 2 -> lost integral action in the measured-torque path confirmed as LOC cause; next: PID item-2 check on joint, then solver + reviewer for decision 2. Gate progress: G3 item 1 cause confirmed by falsifier probes (fix route open); no GATE_STATUS row changed (probes, not gate evidence).
- S222b: pid_joint scored (g3_chain rescore): item 2 key1 FAIL 2 Hz q rms 2.6, key2 pass; INDI probes fail both keys (rms 11-15), detections start 21-29 s, before the fault. Gate progress: G3 item 1 PID reference scored for the fix comparison; no GATE_STATUS row changed.
- S223 (2026-11-24): STATE trimmed; route check 223 (orchestrator, RC221 current). D-RATE-BLD-2 proposed. Joint probes ACT_BLD 0.10/0.05 no LOC (52.4/45.4 deg), item 2 fail both keys (blend_s223). Item 2 split: pre-fault clean on all 4 runs, flags from fault-straddling windows + post-fault limit cycle (item2_split_s223). Gate progress: G3 item 1 fix candidate (i) supported on joint; no GATE_STATUS row changed.
- S223b: draw 264 full plant (903eae63) tb 0.10/0.05: no LOC (48.5/47.9 deg), item 1 pass, item 2 fail post-fault (2 Hz), item 3 fail 0.37/0.36 m; S213 LOC baseline was on d220e193 -> baseline tb 1.0 and PID draw 264 on 903eae63 next. Gate progress: G3 item 1 removed on draw 264 by fix candidate (i) (probe, not gate evidence); items 2/3 open; no GATE_STATUS row changed.
- S225 (2026-11-25): acted on RC224 (no new route check: RC224 is from S224 and current). Committed S224 draw-264 run: INDI tb 1.0 on gate binary 903eae63 aborts (watchdog, max tilt 66.8 deg), LOC reproduces. PID reference re-flown and scored (ref264_s224/README.md, 4b85049845): items 1 and 3 pass (41 deg, 0.123 m), item 2 fails both keys on fault-straddling windows only, pre/post-fault clean. Q32 to owner (re-freeze A / exclude corner B / stop C, plus item 2 straddle windows), WAIT_OWNER. Gate progress: G3 item 1-3 PID reference on draw 264 scored (INDI-only: LOC at tb 1.0, post-fault 2 Hz, item 3); no GATE_STATUS row changed (verdict waits on Q32).
- S226 (2026-11-25): Q32 closed, full text below.

### Q32 (S225, 2026-11-25): draw 264 needs a firmware change after FREEZE-10. Re-freeze, exclude the corner, or stop? BLOCKING G3

Context (route check design/route_check_224.md; evidence results/g3_refly_actc_s212/restore264/):
- Draw 264 = available thrust 0.351 on all motors (sag) + one motor at 0.709, lemniscate. Q31 route steps 1-2 done.
- INDI on the gate binary 903eae63 at the frozen MC_INDI_ACT_BLD 1.0 loses control (ref264_s224/q0_bld100: watchdog,
  > 3 m below hold altitude). Same on the joint minimal case (falsifier_s222).
- Cause shown on logs (two investigators + falsifiers): the weak motor's torque bias grows with collective; the
  rate loop's only remover of a command/output gap is the 1 s blend of modelled and measured torque, too slow.
  ACT_BLD 0.15/0.10/0.05 or model-only (W_MAX 0) remove the loss of control (max tilt 45-54 deg).
- With tb 0.10/0.05 on draw 264 (blend264_s223) G3 item 1 passes but item 2 fails (post-fault 2 Hz p/q limit
  cycle, pre-fault clean) and item 3 fails (0.37/0.36 m vs 0.30 m).
- PID reference, same draw and binary (ref264_s224/README.md): item 1 pass (max tilt 41 deg), item 3 pass (0.123 m),
  item 2 FAIL both keys on the whole run (2 Hz q, windows straddling the fault; pre- and post-fault clean). So item 2
  fails in both stacks as scored today (a test-window question), while the INDI post-fault 2 Hz line and item 3
  are INDI-only. INDI tb 1.0 max tilt 66.8 deg before the abort.
- Any fix (lower ACT_BLD default, per-motor command-to-omega^2 correction, or a bounded rate integrator) changes
  frozen firmware/defaults: G2 rate/att cells, G3 (300), G4 (18), G5 rows, G6 item 7 are re-flown. Roughly 8-12
  sessions of CPU-heavy re-fly plus 1-2 sessions of design and two-key review.

Options:
- A. Re-open FREEZE-10 for decision 2 (D-RATE-BLD-2): one solver session (opus, high) + independent review compare
  (i) lower ACT_BLD, (ii) per-motor gain correction, (iii) bounded rate integrator on the four draws already flown
  (joint, 264, 262, 283) against a written pass line (items 1-3); pick one, check G2 rate margins, freeze-11, re-fly
  the listed rows.
- B. Keep FREEZE-10 and state the limit: amend G3 so the joint corner "sag below X + one weak motor" is outside the
  INDI claim (reported as a measured limit in the report, not a PID fallback, F-1), re-fly G3 on 903eae63 without it.
- C. Stop the G3 route: G3 NOT PASSED with this limit written up; go to G6/G7/G8 on FREEZE-10.

- Sub-question (any option): item 2 windows that straddle the fault instant also flag PID on this draw. Exclude
  windows straddling a fault from item 2 (score pre-fault and post-fault separately), yes/no? Recommendation: yes.

Recommendation: A, bounded: one solver session; if no option passes items 1-3 on the four draws, fall back to B.
Reason: the cause is a structural gap (no integral action against a growing actuator bias, lesson 9), which a real
weak or damaged motor also produces; B and C ship a known defect.
Meanwhile: nothing. Every open item (G3 campaign, G6 item 7, G7 F-10 clean-up, G8 chapters) depends on which firmware
is frozen. Blocked: yes (WAIT_OWNER).

Answer:
A, bounded; sub-question yes with conditions (owner, 2026-11-25, with an independent review agent's second opinion).
Gate text: GATES "Owner amendment S225".
1. Re-open FREEZE-10 decision 2 (D-RATE-BLD-2), rate loop only (D-GAP unchanged; a candidate that needs it says so
   before flying). Candidates (i) lower ACT_BLD, (ii) per-motor command-to-omega^2 correction, (iii) bounded rate
   integrator with allocator-saturation anti-windup, all judged by one pass line; simplest passing one wins (F-9).
2. First: Q30 tooling (S214 window, items 4-6 in both keys), then FREEZE-10 baselines of 262 (C212 idx 22) and 283
   (C5, sample source named in the pass line) on 903eae63; old flights of 262/283 are d220e193 (262 invalid, S218).
3. Pass line, committed in D-RATE-BLD-2 before the first candidate flight, unchanged after. Draws joint, 264, 262,
   283, speed 1, committed seeds, one flight each; both keys: item 1 pass, item 2 pass as scored in point 7, item 3
   on the S214 window. A cell FREEZE-10 already fails on 262/283 becomes "not worse", reported as a G3 risk. Items
   4-5 reported. Winner re-flown once on 264 and joint: still passes. G2 rate roll/pitch/yaw, 800 and 400 Hz,
   measured and model-only, 2 seeds, at G2 thresholds; G2-STEP 9/9. Unit tests, each break-checked: weak-motor loop,
   allocator-saturation anti-windup, landed, telemetry loss and frozen, arming reset. New code meets F-10.
4. Bound: one solver agent run (opus, high) builds, flies, tunes; values fixed before review. One independent review
   (opus, high) of code and scoring; a BLOCKING finding = no pass. Any missed cell = fail, no partial pass, no second
   solver, no more tb probes. No candidate passes -> B, no new question.
5. B: keep FREEZE-10. Excluded corner fixed now, not fitted: saturation-corner draws (2.0 x hover, outside owner
   ranges, S94 decision 6) with a weak motor on; class (b), a measured INDI limit in G8, not a PID fallback (F-1; as
   Q27 item 4). In-range draws (sag, weak motor >= 0.7) stay counted. G3 re-flies 300 fail-fast on 903eae63.
6. A passes: freeze-11 = FREEZE-10 + the candidate only, built per D-BINARY-GZFIX, sha pinned. Re-fly G2 rate/att
   cells + G2-STEP (outer cells only if the outer loop changed), G3 300 fail-fast, G4, G5 rows, G6 item 7. A failure
   there goes to the owner, not automatically to B.
7. Sub-question yes: G3 item 2 skips 4 s windows containing a fault or gust step start (traj start, read by each key
   from run.json); no line chains across the skip. Telemetry loss/frozen starts are not skipped. Conditions: item 5
   scored in both keys in the same campaign; self-test in both keys (straddling sine not flagged, post-fault sine
   flagged, break-checked); skipped windows tabled for both stacks (as Q15 class C). Applies from now on; rescore
   only valid 903eae63 runs used here (4 draws, PID refs); pre-S214 multi-motor runs stay invalid.
Owner warnings noted: (iii) may cost G2 rate PM (freeze-10 spot 46.9 vs 45 deg); the 2 Hz line is the lowest bin of
the 2-40 Hz band (untested whether a real tone); the mechanism also applies inside owner ranges, so G3 may still fail
on an in-range draw; A costs ~8-12 sessions under the weekly cap.

- S226 (2026-11-25): Q32 closed and acted on (GATES "Owner amendment S225", D-OWNER-Q32, D-RATE-BLD-2 active with pass line fixed before any candidate flight). Route check 226 (on path; cuts: G6 item 7/G7/G8 wait, no RC before solver verdict). g3_campaign_f10 already committed and its verdict written (S199): skipped. Q30 tooling built: g3_lemniscate/g3_stick_zsine (25 s hold) + key 1 items 3-6 + S225 skip (1bf26c88f9), independent key 2 (f3170f4b91), break-checked; not flown; key interpretations of items 5/6 and chain wiring to reconcile. Gate progress: G3 route step (a) Q30 scorer tooling built in both keys (unflown); no GATE_STATUS row changed.
