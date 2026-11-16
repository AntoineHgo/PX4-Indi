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
