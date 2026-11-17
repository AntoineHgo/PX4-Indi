# STATE (max 150 lines)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. S50: owner answered Q2 (A amended), Q3 (A), Q4 (A + G1.7 provenance); GATES.md updated, provisional mark lifted; QUESTIONS.md empty. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
- S44: stage-2 INDI margins VOID (A-23 limit cycle, see Next actions).
## Next actions (in order)
S36-S42 detail moved to JOURNAL.md (S45).
S44-S46 detail moved to JOURNAL.md (S51). Derived G1 1757/1640/205 in `bench/params/quad5in_indi_g1.params`; `bench/pretest_gate.py` in use.
S47-S48 detail moved to JOURNAL.md (S53): yaw limit cycle fixed by derived G2_Y 27; low roll PM explained by K_R/P_att + motor lag.
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
   coded); pitch M3a at ACT_TC 0.05 flown (B2, see results/stage3_s53/pitch_m3a/).
NEXT (S54): (1) finish one G2 inner table at 800 Hz: yaw M3a with lead (INJ_AX 3, csv axis 2; check AMP vs G2_Y
   first with a pre-test) and the measured-rotor path (--sim v2) for roll; then 400 Hz roll/pitch/yaw (GATES.md G2
   "Configurations"). (2) write the attitude/velocity/position break notes on the host and second-key them (route
   check 49 item never done). (3) stage-3 items note: opus review before coding items 1-5; own doubts: item 3 thrust
   decay diverges from stock (stock holds), item 2 runtime foreign-publisher detection fragile. (4) hole reporter per
   run only when the frozen --gate batch is scheduled. Next route check S58.
Standing rule (S35): bench param sets carry SENS_BAR_AUTOCAL 0.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S53-B2 | pitch M3a ACT_TC 0.05 lead 1, 2 seeds, then SITL rebuild at 7522625b0f | - | `results/stage3_s53/pitch_m3a/` (done.txt ALLDONE) | `bash results/stage3_s53/pitch_m3a/run_all.sh` |

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
| 53 | T109 | sonnet | stage-3 items design note | done, 5 calls, ~$0.2, 168 lines, UNREVIEWED |
| 52 | T107 | sonnet | code MC_INDI_LEAD + tests | done, 14 calls, ~$0.75, all pass, break-checked |
| 52 | T108 | haiku | second key lead diff vs note | done, 6 calls, ~$0.08, AGREE, 1 logging finding fixed |
| 51 | T106 | haiku | A-24 PSD re-check with G2_Y 27 | done, 5 calls, ~$0.1, tone gone ~100x |
| 51 | T105 | opus | review r1 lead note vs code | done, 9 calls, ~$1.1 (2x estimate), NOT BLOCKING, 3 MAJOR |
| 50 | T104 | sonnet | second key lead delay sweep | done, 5 calls, ~$0.25, AGREE at K20, GM 1-3 dB optimistic |
| 49 | T102 | haiku | stage-2 summary table | done, 7 calls, ~$0.2, PID GM values negative (not used) |
| 49 | T103 | sonnet | D-RATE-LEAD note draft | done, 6 calls, ~$0.3, UNREVIEWED |
| 48 | T101 | sonnet | second key lead/att-loop margins | done, 3 calls, ~$0.1, PM AGREE, GM DISAGREE (flights side with key 1) |
| 47 | T98 | sonnet | roll M3a + yaw follow-up F5-F9 | done, 15 calls, ~$0.6, found yaw limit cycle; wrong guess on cause (code change) |
| 47 | T100 | haiku | G2_Y second key | done, 5 calls, ~$0.1, AGREE 27.0 |
| 45 | T96 | haiku | derive_g1.py + self-test | done, 7 calls, ~$0.1, ALL PASS, UNKEYED |
| 45 | T95 | haiku | second key A-23 numbers | done, 7 calls, ~$0.06, AGREE (RMS 0.0068/0.0056/0.0017, pin 0 %) |
| 45 | T94 | haiku | A-23 hover G1_Y 215 + checks | done, 6 calls, ~$0.1, clean hover |

## Lessons proposed
- S53: four M3a flights on two parallel docker streams took ~5 min wall and ~$0.05 of context: run small sweeps
  from host bash in the background while one agent drafts, instead of delegating the flights.
- S52: review F2 named the over-estimated ACT_TC as the dangerous side of the lead; test and flight show the opposite
  (x0.6: PM 42, x1.4: PM 83). Compute both sides of a parameter error before planning defaults around one.
- S51: an opus review of a ~180-line note plus ~400 lines of law code cost ~$1.1 in 9 calls (2x the S35 estimate); budget opus reviews at ~$1.1 and launch them first in a session.
- S50: break-checks by sed on a .py must run with PYTHONDONTWRITEBYTECODE=1 (or clear __pycache__): a same-size
  mutation in the same second left a stale .pyc that made the restored file fail.
- S49: calibrate the unmodelled delay of a loop model on one existing flight before using the model to accept or
  reject a candidate; the lead's verdict at 400 Hz flips between 2.5 and 5 ms of delay.
- S48: before reading a low margin as a plant or gain problem, put every loop the break closes around into the model
  and test it by predicting a parameter change in flight (two flights, ~$0.1 of CPU, settled what 7 sessions had not).
- S47: a single clean flight does not prove stability: S45 hovered clean, the same config limit-cycled on replay (bistable
  lightly damped mode). Accept a configuration change on >= 2 seeds, and derive every term of the law (G2 too) before flying.
- S45: a default effectiveness never derived for the airframe (G1_Y 30 vs plant 215) cost 5 sessions of margins; derive every
  physical parameter from the model/airframe before the first closed-loop measurement, and log it in run metadata.
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
