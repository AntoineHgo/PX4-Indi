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
S44-S46 detail moved to JOURNAL.md (S51). Derived G1 1757/1640/205 in `bench/params/quad5in_indi_g1.params`; `bench/pretest_gate.py` in use. S47-S48 detail moved to JOURNAL.md (S53): yaw limit cycle fixed by derived G2_Y 27; low roll PM explained by K_R/P_att + motor lag.
S49-S53 detail moved to JOURNAL.md (S56): lead MC_INDI_LEAD 1, ACT_TC 0.05 defaults; roll/pitch M3a PM 59-87.
S54-S56 detail moved to JOURNAL.md (S58): D-YAW-INV coded, yaw M3a 800 Hz PM 88 / GM 18.4 / Ms 1.6; roll 400 Hz PM 84.
S57 (launch 20261117-071301, cap $3): roll M3a 800/3 Hz re-flown with TP 7.5 (`results/stage3_s57/roll_m3a_267b/README.md`):
   PM 83.2/83.6, GM 10.2/10.0, DM 57 ms, Ms 4.0/4.1, 2 seeds; S56 seed 1 had taken the LS (non-uniform t) path, not a rounding
   hole; LS and FFT paths agree on flight data. Route check 57 (`design/route_check_57.md`) ACTED ON: rate-loop table stops
   here (roll 800/400/267, yaw 800); remaining rates and the measured-rotor table move to stage 6, except ONE measured-rotor
   anchor (roll 800 Hz, sim v2, CA_R_W_MAX 2700, B-S57b) because the flight configuration had no anchor under the current law.
   Measured-rotor anchor DONE (`results/stage3_s57/roll_m3a_meas800/README.md`): roll 800 Hz PM 77.5/77.0, GM 16.6/16.3,
   DM 70/72 ms, Ms 2.1, f_c 3.0 Hz, measured torque in use 100 % of window; linear-model cross-check of this path: stage 6.
   T116 DONE: `design/g2_outer_breaks_note.md` (59 lines, UNKEYED). PID breaks under O-11 via additive trajectory_setpoint
   velocity/acceleration feed-forward (PositionControl.cpp:133/:153), position/attitude as reference breaks (L = T/(1-T));
   INDI M3b: d into t_c after indi_accel_control.cpp:273 (_thrust_prev inherits d); A-26 model form; Tp 9.000 s; 6-9 sessions.
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
NEXT (S60): (a) opus review of the whole stage-3 safety DIFF (65356c4250 + eafb26b623^) vs DECISIONS D-S3-*, one
   interface, <=12 calls, budget $1.1, launch FIRST; (b) route check 61 (sonnet, ~$0.2) if budget remains, else S61;
   (c) then stage 5 hover slice + thrust-gap flight (route check 57 rec 3). Triggering paths of items 2/3 in SITL: G5.
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
| 59 | T120 | haiku | second key items 2+3 diff | done, 5 calls, ~$0.06, AGREE-WITH-ISSUES (5 minor) |
| 59 | T119 | sonnet | code items 2+3 + tests | done, 7 calls, ~$0.33, 6/6 pass, break-checked |
| 58 | T118 | haiku | second key items 1+4 diff | done, 6 calls, ~$0.06, AGREE-WITH-ISSUES (issue unreachable) |
| 58 | T117 | sonnet | code items 1+4 + tests | done, 27 calls, ~$0.7, all pass, break-checked, module not compiled by it |
| 57 | T116 | sonnet | G2 outer break note | done, 8 calls, ~$0.7, 59 lines, UNKEYED |
| 57 | T115 | sonnet | route check 57 | done, 6 calls, ~$0.18, acted on |
| 56 | T114 | haiku | second key D-YAW-INV diff | done, 5 calls, ~$0.05, AGREE-WITH-ISSUES, landed-cycle bug found and fixed |
| 56 | T113 | sonnet | code D-YAW-INV + tests | done, 13 calls, ~$0.45, all pass, break-checked, missed first landed cycle |
| 54 | T111 | sonnet | second key yaw break model | done, 6 calls, ~$0.25, coded-law denominator mis-transcribed; AGREE after 1-line fix, option (c) AGREE |
| 53 | T110 | sonnet | route check 53 | done, 6 calls, ~$0.2, acted on (defaults, G2 table first) |
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
- S58: the px4_sitl_test build does not compile the module (only libs and tests); a coding agent's green tests say nothing
  about the module wiring: always add `make px4_sitl_default` to the brief.
- S57: a non-integer fs*Tp did not trip the FFT check on a jittered log because the FRF code switched to its least-squares
  path; know which path a script took before calling a pass a hole. Pick multisine periods that are whole samples at every rate.
- S54: a module-level loop variable shadowed a deleted local in a model script and silently changed its output; re-run
  every model script against its committed output after any edit (diff), as done here.
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
