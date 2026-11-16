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
