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
S40 (launch 20261116-090818, cap $2.7): (1) DONE unit tests in build/px4_sitl_o11 with -DCMAKE_TESTING=ON: rate lib
   40/40, IndiInjection 4/4, IndiAccelControl 19/19, IndiMeasuredTorque 4/4 PASS; break-check (landed gate removed)
   fails Gating, restored (`results/stage2_s40/unit_tests*.txt`). Earlier S40 plan items:
   (2) DONE in S39: haiku second key code vs D-G2-BREAK/D-G2-INJ AGREE-WITH-ISSUES (`results/stage2_s39/second_key_inject.md`):
   only -0.0 -> +0.0 at AX 0 (accepted, no effect); S41 analysis must assert fault == 0 and landed == 0 over the window,
   params set before arming. Still to do: generator check on timestamp_sample from a new flight;
   (3) route check 40 (sonnet). M3b store points partial in the T81 notes (library `_thrust_prev` unread).
S41 flights: pre-test AMP 0.005, DLY 5, model-only AND measured (`CA_R_W_MAX` + `--sim v2`), then matrix.
S40 route check 40 (`design/route_check_40.md`): R1 G2 written in GATES.md (DONE S40) then rate-loop flights
   (S41-42); R2 stage-3 slice incl. ACT_TC identification + G2 outer-break note (S43-45); R3 G3/G4 harness tasks in
   parallel; stage 5 from ~S46. Projection ~25 more sessions: tell owner in the Q4 entry.
Standing rule (S35): bench param sets carry SENS_BAR_AUTOCAL 0.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| T83 | S41 pre-test: 2 hovers AMP 0.005 model-only + measured, checks | haiku | `results/stage2_s40/pretest_inj/README.md` | relaunch same brief |

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

## Agent ledger (stage 2; stage-1 rows in JOURNAL.md)
| session | id | model | task | outcome |
|---|---|---|---|---|

| 36 | T74 | sonnet | r2 check of section 7 | done, 7 calls, ~$0.35, CLOSED |
| 36 | T73 | opus | review r1 stage-2 note | done, 11 calls, ~$0.8, BLOCKING, answered |
| 37 | T75 | sonnet | margins estimator + self-tests 1-3 | done, 9 calls, ~$0.9, ALL PASS re-run by me |
| 37 | T76 | haiku | second key margins (analytic) | done, 3 calls, ~$0.06, AGREE 5/5 |
| 37 | T77 | haiku | PID rate gains read | done, 6 calls, ~$0.06, units fixed by me |
| 38 | T78 | sonnet | margins_models.py + self-test 4 | done, 15 calls, ~$1.0, ALL PASS re-run by me |
| 38 | T79 | haiku | second key continuous models | done, 4 calls, ~$0.1, AGREE |
| 38 | T80 | haiku | GM jump check | done, 5 calls, ~$0.06, explained (phase plateau) |
| 40 | T82 | sonnet | route check 40 | done, 5 calls, ~$0.15 |
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
