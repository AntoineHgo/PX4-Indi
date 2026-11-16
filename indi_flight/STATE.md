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
S35 (launch 20261116-074242, cap $3): Q4 still unanswered. S34 pre-test read: A-20 PASS 2/2, A-19 candidate refuted 3/3.
   IN FLIGHT (detached, started ~07:50, ~17 runs x ~50 s): `bench/a20a19_s35.sh` -> `results/a20a19_s35/` :
   (a) A-20 closing set, 15 hovers, `bench/a20_close_s35.params` (SENS_BAR_AUTOCAL 0 alone) -> `a20/a14_check.md`;
   (b) A-19 pre-test, 2 hovers, `bench/a19_magtype_s35.params` (EKF2_MAG_TYPE 1 heading-only, decl 2.62) -> `a19/`.
   Resume: wait for ALL_DONE in status.txt; A-20 closes if CAL_OFF 0/0, baro_fault 0, bias med arm-5..arm < 0.5 m
   in 15/15 (new column in `bench/a14_close_check.py`, S35, second key T70); A-19: `python3 results/a19a20_s34/a19_mech.py`
   style check on a19/hover_r*; if not < 0.3 deg -> PARK A-19 by mechanism (EKF 3-axis earth-field/bias states).
   Agents: T70 haiku second key of the bias-median column: AGREE 7/7 (`results/a20a19_s35/second_key_t70.md`).
   T71 route check 35 (`design/route_check_35.md`): stage 1 off the shortest path since S31; park A-19 by mechanism
   now; start stage 2 at S36 in parallel, results marked provisional under Q4-A; escalate Q4 if G1 FINAL not written
   by end of S36. ACCEPTED. T72 sonnet stage-2 design note `design/stage2_margins_s35.md` (gyro injection in
   gz_bridge as primary break for PID and INDI, multisine, L=-S_yd/S_xd, blend-mode model for A-1; 267 Hz -> D-RATE267;
   UNVERIFIED items listed in the note). Needs an opus review (one interface: note vs source) before S37 code.
S34 (launch 20261116-072614, cap $1.35, no agent): Q4 still unanswered. Combined A-19/A-20 pre-test detached:
   `bench/a19a20_pretest_s34.sh` (params `bench/a19a20_pretest_s34.params`: SENS_BAR_AUTOCAL 0, EKF2_DECL_TYPE 0,
   EKF2_MAG_DECL 2.62 (sensor-field value from T68 logs; gz source not read), EKF2_MAG_B_NOISE 0) -> 
   `results/a19a20_s34/` (2 hover + 1 step_roll, speed 4); resume: wait for ALL_DONE in status.txt, then
   `python3 results/a19a20_s34/a19_mech.py` (copy, writes next to itself) and read `a14_check.md`.
   Closing criteria (ANOMALIES): A-19 |err| align+1 s < 0.2 deg, hover window < 0.3 deg, magB_x < 0.5 mG;
   A-20 CAL_BARO0_OFF 0 and median pre-arm bias < 0.5 m. If pass: 15-run set + two keys (S35); route check 35 due.
   S34 ended with the batch still flying (started 07:27, ~4 min); results unread. S35 FIRST: check status.txt, run
   the two checks above, check params_applied in each run's meta (SENS_BAR_AUTOCAL, EKF2_*), write README.md there.
   No stage-2 note this session (budget). hover_r1 read: A-20 PASS, A-19 NOT fixed (EKF decl 3.67, err +0.52 deg,
   magB_x -5.8 mG). ALL 3 runs read at end of S34: A-20 PASS 2/2 hovers, A-19 refuted 3/3 (+0.36..+0.78 deg).
   `results/a19a20_s34/README.md` has the S35 plan (skip re-reading the runs).
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
- S34: a background-wait notification can arrive before the command really ends; check the condition itself
  (status file) before concluding the wait failed.
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
