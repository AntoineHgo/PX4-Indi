# STATE (max 150 lines)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Sessions 4-13: history in JOURNAL.md (moved S15). S14: G1.6 runs at speed 1 and 4, review r5 BLOCKING (A18).
- Gates: G1 open | G2 open | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. Q2, Q3 open (G1.1 gap rule, G1.6a wording), Q4 open (freeze G1 with limits, S32), not blocking. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
- S44: stage-2 INDI margins VOID (A-23 limit cycle, see Next actions).
## Next actions (in order)
S36-S42 detail moved to JOURNAL.md (S45).
S44 (launch 20261116-212207, cap $3) DONE: T90 sonnet A-22 trace (`results/stage2_s44/a22_links.md`) + T91 haiku
   second key (`results/stage2_s44/limit_cycle_second_key.md`): every INDI M3a flight S39-S41 is in a 17 Hz pitch LIMIT
   CYCLE with motors pinned at 0 on 38 % of samples -> stage-2 INDI margins S40-S43 VOID; A-22 closed as artefact,
   A-23 opened. Plant G1_roll derived 1756 (CT/KM cancel; needs Ixx and hover thrust, not in CA_*) vs default 320.
S44 also: A-23 test flown (`results/stage2_s44/a23_test/`): PID clean; INDI derived G1 cuts rate RMS 32x but motors
   still pinned at 0 on 46 % (motor-command chatter, 2nd mechanism). See A-23 note.
S45 (launch 20261116-214129, cap $3) DONE: A-23 CLOSED. Cause: G1 defaults 5-8x low (yaw 7x: derived G1_Y 205-222,
   `results/stage2_s45/g1y_derivation.md`). Hover with G1 R/P/Y 1756/1599/215 (`results/stage2_s45/a23_yaw/`): motor pin 0 %,
   rate RMS 0.0068/0.0056/0.0017, achieved 1.0. A-24 opened (45.7 Hz motor tone, std 0.00085). Route check 45
   (`design/route_check_45.md`): stage 2 margins wait for derived defaults; old margin numbers void, method kept.
S45 also: T96 `bench/derive_g1.py` + `bench/tests/test_derive_g1.py` written (ALL PASS, re-run by me), UNKEYED: quad5in G1
   R/P/Y 1759/1602/221 (`results/stage2_s45/derive_g1.md`). Roll and pitch share PX4's normalisation scale, so torque per unit
   command is equal and G1_P = G1_R Ixx/Iyy for any arm layout (my reading: B pinv(B) = I). D-G1-DERIVE written.
S46 (launch 20261116-215112, cap $3): `bench/pretest_gate.py` + self-test (break-checked) committed: hover window from first
   airborne +15 s, rate RMS < 0.02 rad/s, motor pin < 1 %, torque achieved > 90 %, exit 0/1/2. On logs: PID and S45 INDI
   pass, S44 chatter and S41 limit cycle fail (`results/stage2_s46/pretest_gate_check/`). T97 sonnet second key of G1
   derivation running -> `results/stage2_s46/g1_second_key.md` (also: which inertia, 1.396e-3 or 1.022e-3, is the plant's).
S46 also: T97 second key AGREE on roll/pitch with TOTAL inertia; bench G1 1757/1640/205 in `bench/params/quad5in_indi_g1.params`.
S47 (launch 20261116-221436, cap $3): first roll M3a flight with derived G1 invalid: 41 Hz yaw LIMIT CYCLE (pin 37-52 %)
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
S49 (launch 20261116-224459, cap $2.28): T102 stage-2 summary table (`results/stage2_s49/summary_table.md`): only valid
   measured margins are INDI roll torque break at 800 Hz (best PM 42.9 at P3); no measured PID, no 400/250 Hz, no other
   break point. T103 D-RATE-LEAD note draft (`design/rate_lead_note.md`): new param MC_INDI_LEAD scale 0..1 (default 1,
   0 = current law), insertion at indi_rate_control.cpp step 8 (l.378-382), c_i = lead K_i ACT_TC, 0 when landed; noise
   x1.4-2.3 on the a_f term (G4); filter H is in the model (checked). Stage 3 OPEN.
NEXT (S50): route check 49 done early (`design/route_check_49.md`), adopted: (1) host-only falsification of the lead
   first: add 3-5 ms delay, ACT_TC 0.033 to `bench/margins_models.py` lead rows at 400/800 Hz; stop D-RATE-LEAD if
   PM < 50 or GM < 8 dB at 400 Hz (model is 2.3-3.5 dB GM optimistic). (2) If it holds: opus review r1 of the note
   vs src/lib/indi_rate_control (one interface, ~$0.6, needs $1.2 left), then code MC_INDI_LEAD + unit test (break-checked),
   one roll M3a flight on 2 seeds. Not adopted: 'review the diff instead of the note' (design-first rule kept; the
   review of the code against the note follows the code). Q2-Q4 already asked, no new question.
   (3) runner appends quad5in_indi_g1.params + provenance in run.json; pretest_gate end-time
   option (window overlaps injection). (4) A-24 PSD re-check with G2.
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
| 49 | T102 | haiku | stage-2 summary table | done, 7 calls, ~$0.2, PID GM values negative (not used) |
| 49 | T103 | sonnet | D-RATE-LEAD note draft | done, 6 calls, ~$0.3, UNREVIEWED |
| 48 | T101 | sonnet | second key lead/att-loop margins | done, 3 calls, ~$0.1, PM AGREE, GM DISAGREE (flights side with key 1) |
| 47 | T98 | sonnet | roll M3a + yaw follow-up F5-F9 | done, 15 calls, ~$0.6, found yaw limit cycle; wrong guess on cause (code change) |
| 47 | T100 | haiku | G2_Y second key | done, 5 calls, ~$0.1, AGREE 27.0 |
| 45 | T93 | sonnet | route check 45 | done, 7 calls, ~$0.15 |
| 45 | T96 | haiku | derive_g1.py + self-test | done, 7 calls, ~$0.1, ALL PASS, UNKEYED |
| 45 | T95 | haiku | second key A-23 numbers | done, 7 calls, ~$0.06, AGREE (RMS 0.0068/0.0056/0.0017, pin 0 %) |
| 45 | T94 | haiku | A-23 hover G1_Y 215 + checks | done, 6 calls, ~$0.1, clean hover |
| 44 | T90 | sonnet | A-22 links a,b trace | done, 15 calls, ~$1.0, found limit cycle |
| 44 | T92 | haiku | A-23 PID + INDI-derived-G1 hovers | done, 11 calls, ~$0.1, PID clean, INDI chatter |
| 44 | T91 | haiku | second key limit cycle, 3 logs | done, 7 calls, ~$0.1, CONFIRMED |

## Lessons proposed
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
