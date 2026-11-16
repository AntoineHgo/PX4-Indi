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
- S44: stage-2 INDI margins VOID (A-23 limit cycle, see Next actions).
## Next actions (in order)
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
S43 (launch 20261116-114133, cap $2.79) DONE: T88 sonnet A-22 chain (`results/stage2_s43/a22_chain.md`,
   `bench/a22_chain.py`): static roll G1 ~340 = link a (torque_sp -> actuator_motors roll diff 0.92, 0.23/motor)
   x link b (actuator_motors -> (w/wmax)^2, 0.59 at hover, a 0.221 -> w ~976-999) x link c (626 meas vs 621 analytic,
   on truth). Product reproduces end-to-end u->alpha at 2.5/5/7.9 Hz; tau_eff 35-44 ms. 878 analytic REJECTED.
   T89 haiku second key (`results/stage2_s43/a22_second_key.md`): link a AGREE (0.222-0.236); link b DISAGREE but its
   own map is suspect (actuator_outputs zero-filled on 36 % of rows, max 1897 rad/s, R2 0.2): link b UNSETTLED.
   Log commit 32500e0 vs HEAD: no diff in allocator/mixer/gz_bridge/INDI module/airframe; params as assumed
   (THR_MDL_FAC 1, EC_MIN 0, EC_MAX 2700, CT 6.5). A-22 narrowed, still open (see ANOMALIES).
S44 (launch 20261116-212207, cap $3) DONE: T90 sonnet A-22 trace (`results/stage2_s44/a22_links.md`) + T91 haiku
   second key (`results/stage2_s44/limit_cycle_second_key.md`): every INDI M3a flight S39-S41 is in a 17 Hz pitch LIMIT
   CYCLE with motors pinned at 0 on 38 % of samples -> stage-2 INDI margins S40-S43 VOID; A-22 closed as artefact,
   A-23 opened. Plant G1_roll derived 1756 (CT/KM cancel; needs Ixx and hover thrust, not in CA_*) vs default 320.
S44 also: A-23 test flown (`results/stage2_s44/a23_test/`): PID clean; INDI derived G1 cuts rate RMS 32x but motors
   still pinned at 0 on 46 % (motor-command chatter, 2nd mechanism). See A-23 note.
S45 NEXT (step back, lesson 24): (0) route check 45 (sonnet, due; give it A-23). (1) A-23: chatter is 46 Hz with yaw torque_sp at
   the rails (`a23_test/motor_chatter.md`): derive G1_Y (rotor drag/spin-up, decision 5) and fly; check esc 15 ms 'lead'. (2) pre-test
   checklist gets pitch-rate RMS < 0.02 rad/s and motor pin < 1 %. (3) only then redo M3a margins with derived G1. Old S44 plan kept below for record:
OLD S44 PLAN: (1) A-22 rest, one sonnet task <=15 calls: why allocator gives 0.23/motor (source says 0.354 or 0.707) and
   why a 0.221 hover maps to w ~990 (sqrt map gives 1269): check actuator_outputs instances/topic multiplicity,
   MixingOutput thrust-model code path for gz ESC, effectiveness scaling (CA_ROTOR CT 6.5 vs physical 10.9);
   haiku second key on esc_status (not actuator_outputs). Matters for stage-4 decision 3 (G1 from CA_* derivation).
   (2) Working G1 for margins = 340 (static, end-to-end, regression-consistent) until A-22 closes. (3) (c) motor step
   in sim to separate tau and latency; (a) add attitude loop to margins_models.py (sonnet) + haiku second key.
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

## Agent ledger (stage 2; stage-1 rows in JOURNAL.md)
| session | id | model | task | outcome |
|---|---|---|---|---|

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
| 44 | T90 | sonnet | A-22 links a,b trace | done, 15 calls, ~$1.0, found limit cycle |
| 44 | T92 | haiku | A-23 PID + INDI-derived-G1 hovers | done, 11 calls, ~$0.1, PID clean, INDI chatter |
| 44 | T91 | haiku | second key limit cycle, 3 logs | done, 7 calls, ~$0.1, CONFIRMED |
| 39 | T81 | sonnet | M3a plumbing + build + 1 hover | done, 27 calls, ~$0.93, test not linked, fixed by me |

## Lessons proposed
- S44: five sessions of margin work ran on a vehicle in a 17 Hz limit cycle; the pre-test checked u=c+d, fault and
  landed but not body-rate spectra. Every pre-test runs a spectral oscillation check on body rates and motor saturation fractions.
- S43: a static 'analytic' gain from source reading was 2.6x off in two links; measure each link of a chain on the log before trusting a derived plant gain (and a sonnet chain trace with log analysis costs ~$0.9 in 17 calls).
- Regressing a filtered signal (angular_accel_filtered) on a command: pass the command through the same filter first; T86 missed it and read the LPF2p group delay as a 20 ms plant delay (S42).
- S41: a loop-gain model must contain every loop the break closes around, outer loops included; the M3a model
  lacked the attitude P loop and a 17 deg PM gap was spent on as an anomaly (A-21).
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
