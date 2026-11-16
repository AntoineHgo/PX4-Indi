# STATE (max 150 lines)

## Status
- Stage: 1 (evidence and simulator), started session 1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. GATES.md: G1 draft written; G1.6 first tested S14 ((a) not met, see next actions).
- Blocker: none. Q2, Q3 open (G1.1 gap rule, G1.6a wording), Q4 open (freeze G1 with limits, S32), not blocking. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- Session 18 (launch 20261115-233746, cap $1.62): A-12 CLOSED (T36 fix dbb1a62e29, T37 second key).
- Session 16 (launch 20261115-231016, cap $3): D-SIM-STEP implemented (T31, commit 72598e3159) and pre-tested
  (`results/pretest_simstep_s16/README.md`): 1.25 ms step, IMU 800 Hz, RATEMAX 800/400 applied, PID flies, speed 4
  ~38 s wall/run. Logger fixed: `-p actuator_motors -b 200` logs all controller-rate topics at 800 Hz, 0 dropouts. A-10.

## Next actions (in order)
S32 (launch 20261116-064202, cap $2.70): A-20 fix 4297ba9869 (atomic once-set _alt_ref, built, format clean). B32 G1.6
   re-fly detached (`bench/g16_set_s32.sh` -> `results/g16_set_s32/`, pretest gate then 2x15 runs, then A-20 check).
   T66 haiku second key A-20 diff -> `results/g16_set_s32/second_key_a20.md`; T67 haiku A-19 + attitude 15 % gap ->
   `results/a19_s32/README.md`.
   S32 OUTCOMES: A-20 fix keyed AGREE-WITH-ISSUES (residuals unreachable on quad5in, ANOMALIES). Metric defect found
   by T67 and fixed (b3: quat_angle atan2, self-test break-checked): attitude 15 % gap closed. B32 speed 4 DONE and
   analysed (`results/g16_set_s32/speed4/README.md`): A-14 effect gone (ref z spread 2.3 -> 0.13 m); A-19 closed then
   REOPENED (EKF yaw error up to 1.54 deg, varies under one seed). B32 speed 1 still running detached.
   S33 NEXT: (1) when `results/g16_set_s32/status.txt` shows ALL_DONE: recompute metrics for speed1 with current
   metrics.py (loop as in speed4 README), g16_spread, a20_check.md (bias0 < 0.5, baro_fault 0 in all 30 -> close A-20);
   (2) A-19 mechanism (haiku, NEXT line in ANOMALIES); also fix `bench/second_key_s29.py:130` arccos; (3) write G1
   status: G1.6 verdict with Q2/Q3 provisional wording, anomalies as evidence limits; G1.5 deferred (route check 30)
   -> ask the owner whether G1 can freeze with G1.5 deferred to G3/G5 and Q2/Q3 open (escalation due: G1 not frozen
   by end of S32); then stage 2.
S31 (launch 20261116-042839, cap $1.08): A-14 bridge fix: pretest PASS, B31 15/15 flew; mechanism gone (bias0 <0.5 m,
   baro_fault 0/15, hold 4.94-5.05 m) but closing test FAILS 9/15 on 0.1 m (max 0.144 m): A-14 PARKED with bound
   0.15 m (ANOMALIES). T65 second key AGREE-WITH-ISSUES: thread race on `_alt_ref` -> new A-20; test constant fixed.
   S32 NEXT: (a) A-20 fix (sonnet, small: atomic/once-set ref in gz_bridge) + haiku key, folded into the G1.6 re-fly;
   (b) S31 plan (ii) attitude 15 % gap + A-19 (haiku); (iii) re-fly G1.6 set with the fixed baro, write G1 FINAL
   with anomalies as evidence limits, start stage 2. Escalate to owner if G1 not frozen by end of S32.
1-4. Stage-1 items still pending from the old list (rest done, history in JOURNAL): errata re-score of archived set-O/T5;
   window rule must accept nav_state 23; sag as sim-time ramp in gz bridge (two keys); run_scenario sim-time fixes
   (`sim_review.md`:14,19) now folded into the player; outer-loop A-requirements folded at stage 5.
5. Simulator items of stage 1 (delayed GNSS, rotor inertia check, battery model, injectors, seeded drops, vibration,
   variants, noise profiles, determinism). Source web re-check of J_rotor (ASSUMED) still pending.

## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| B32 | G1.6 re-fly, fixed baro, s4 (done, analysed) + s1 (running) | host bash (detached) | `results/g16_set_s32/status.txt` | delete partial dir, `setsid nohup indi_flight/bench/g16_set_s32.sh` |
| B26 | G1.6 set --sched --sched-anchor, 3 scen x 5, speed 4 (done, analysed S27) then 1 (DONE S28, not analysed) | host bash (detached) | `results/g16_sched_set_s26/speed{4,1}/status.txt` | `setsid nohup indi_flight/bench/g16_sched_set.sh` (delete partial speed dir first) |

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

## Agent ledger (stage 1)
| session | id | model | task | outcome |
|---|---|---|---|---|
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
| 32 | B32 | host bash | G1.6 re-fly 2x15 + pretest | s4 15/15 flew, $0; s1 running |

## Lessons proposed
- An anomaly bound taken from the range of 10 runs was exceeded by the next 5 (A-19, S32): bound by mechanism.
- A metric changed during a running batch: re-compute the whole set with one version before comparing (S32).
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
