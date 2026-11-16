# STATE (max 150 lines)

## Status
- Stage: 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. Q2, Q3 open (G1.1 gap rule, G1.6a wording), Q4 open (freeze G1 with limits, S32), not blocking. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
- Session 16 (launch 20261115-231016, cap $3): D-SIM-STEP implemented (T31, commit 72598e3159) and pre-tested
  (`results/pretest_simstep_s16/README.md`): 1.25 ms step, IMU 800 Hz, RATEMAX 800/400 applied, PID flies, speed 4
  ~38 s wall/run. Logger fixed: `-p actuator_motors -b 200` logs all controller-rate topics at 800 Hz, 0 dropouts. A-10.

## Next actions (in order)
S36 DONE: G1 FINAL; T73 r1 BLOCKING answered (note section 7, D-G2-BREAK).
S36 T74 r2 CLOSED (`design/stage2_note_review_r2.md`): M3a cuts every in-flight path; S38 must log c (pre-injection),
   d and u at cycle rate.
S37 (launch 20261116-080552, cap $3): (1) DONE note body patched, section 7 item 7 answers r2 residuals (fault path
   unreachable by finite d; M3b store point to be read in S38 plumbing). (2) DONE T75 sonnet: `bench/margins_est.py` +
   `bench/tests/test_margins_selftest.py` self-tests 1-3 ALL PASS (re-run by me), 7 break checks recorded (commit
   a2884f4cc9). T76 haiku second key: independent analytic GM/PM/DM, AGREE 5/5 (`results/stage2_s37/second_key_margins.md`,
   `python3 bench/second_key_margins_s37.py <out.md>`); its case B is unstable with 1 crossing, multi-crossing covered by
   self-test 1b only. Estimator not yet run on bench logs (CSV t,d,x,y; sign y = -L x from spec).
T77 haiku: PID rate gains VERIFIED (`results/stage2_s37/pid_rate_gains.md`, units and MC_GC_EN=0 checked by me).
S38 (launch 20261116-082041, cap $3) DONE: T78 sonnet `bench/margins_models.py` (sampled-data + continuous L_indi,
   L_pid, time-domain sim, A-1 table) + self-test 4 ALL PASS (re-run by me; break-checked: dropping t_f fails 4a).
   T79 haiku second key, independent continuous model: AGREE (INDI model-only 6.5 dB/43.6 deg vs 6.1/42.7 sampled;
   PID 26.0/67.9 vs 25.8/67.9). Tables `results/stage2_s38/`. Note 7.4 reduction corrected (needs A_m = eta A_r; O(T) skew).
   FINDING (model, unflown): roll INDI model-only at code defaults PM 42.7/41.6/40.6 deg at 800/400/267 Hz < 45, limited
   by tau_m 0.02 vs plant tau_r 0.033 (lesson 8: ACT_TC must be identified, stage 3/4); measured path Tb 0 PM 54, blend
   Tb 0.1 PM 48. Self-test 4a is coding consistency only (same equations both sides); firmware match comes from flights.
S39 (launch 20261116-084309, cap $3) DONE: D-G2-INJ; T81 sonnet M3a plumbing (commit feat(mc_indi_rate_control)),
   SITL build OK, 1 pre-test hover flew (`design/t81_m3a_inject_s39.md`, `results/stage2_s39/pretest_m3a/`): u = c + d
   exact (max err 0), indi_rate_status 800 Hz, no fault, generator = margins_est multisine on 15849/15998 samples (rest
   = timestamp-join artefact). Added by me: indi_rate_status.timestamp_sample, MC_INDI_INJ_DLY (default 5 s).
S40 NEXT (in order): (1) build `px4_sitl_test`, run Indi* unit tests incl. new IndiInjectionTest (NOT RUN yet);
   (2) haiku second key of the injection diff vs D-G2-BREAK/D-G2-INJ and of the generator on timestamp_sample;
   (3) route check 40 (sonnet). M3b store points partial in the T81 notes (library `_thrust_prev` unread).
S41 flights: pre-test AMP 0.005, DLY 5, model-only AND measured (`CA_R_W_MAX` + `--sim v2`), then matrix.
Standing rule (S35): bench param sets carry SENS_BAR_AUTOCAL 0.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|

## Open problems
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

- S38 GM jump explained (T80, `results/stage2_s38/gm_jump_check.md`): INDI measured Tb 0 phase grazes -180 deg on a
  plateau 12-27 Hz; at 800 Hz it crosses at 11.9 Hz (21.1 dB), at 400 Hz only at 27 Hz (34.8 dB) though |L| at 11.9 Hz
  is -22 dB. Model GM is phase-shape sensitive there: in S41 compare measured |L| over the plateau, and report GM
  together with the minimum |L|^-1 where phase is within 10 deg of -180 (decide in GATES.md before the first G2 test).
- Unmodelled in margins_models.py (T78 UNVERIFIED list): AlphaFilter coefficient formula, LPF2p coefficients from
  memory, gz/ESC latency 0, measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.

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
| 32 | B32 | host bash | G1.6 re-fly 2x15 + pretest | done, 30/30 flew, $0 |
| 35 | B35 | host bash | A-20 15 hovers + A-19 2 hovers | 17/17 flew, $0 |
| 35 | T70 | haiku | second key bias-median column | done, 7 calls, ~$0.1, AGREE 7/7 |
| 35 | T71 | sonnet | route check 35 | done, 6 calls, ~$0.15 |
| 36 | T74 | sonnet | r2 check of section 7 | done, 7 calls, ~$0.35, CLOSED |
| 36 | T73 | opus | review r1 stage-2 note | done, 11 calls, ~$0.8, BLOCKING, answered |
| 35 | T72 | sonnet | stage-2 margins design note | done, 11 calls, ~$0.7 (168 lines) |
| 37 | T75 | sonnet | margins estimator + self-tests 1-3 | done, 9 calls, ~$0.9, ALL PASS re-run by me |
| 37 | T76 | haiku | second key margins (analytic) | done, 3 calls, ~$0.06, AGREE 5/5 |
| 37 | T77 | haiku | PID rate gains read | done, 6 calls, ~$0.06, units fixed by me |
| 38 | T78 | sonnet | margins_models.py + self-test 4 | done, 15 calls, ~$1.0, ALL PASS re-run by me |
| 38 | T79 | haiku | second key continuous models | done, 4 calls, ~$0.1, AGREE |
| 38 | T80 | haiku | GM jump check | done, 5 calls, ~$0.06, explained (phase plateau) |
| 39 | T81 | sonnet | M3a plumbing + build + 1 hover | done, 27 calls, ~$0.93, test not linked, fixed by me |

## Lessons proposed
- S39: a sonnet implement+build+fly task asked to add a unit test spent its last calls on a link error; tell it the
  gtest kind (unit = pure code) and the test build dir, or leave the test run to a separate step.
- S37: a sonnet task writing ~600 lines of numerical code + tests costs ~$0.9 in 9 calls (long writes); the session
  takes one such task plus a haiku second key.
- S36: a design note on a loop with several feedback paths must name every path a break point cuts; the gyro break
  looked complete for PID and was not for INDI (review r1).
- S35: a sonnet design note of ~11 calls over several source files costs ~$0.7; brief it at <=10 calls at a $3 cap.
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
