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
