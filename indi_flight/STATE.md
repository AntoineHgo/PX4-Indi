# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36, provisional under Q4-A; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open. G1 FROZEN with evidence limits (GATES.md G1 FINAL), not passed until Q2-Q4 answered.
- Blocker: none. S50: owner answered Q2 (A amended), Q3 (A), Q4 (A + G1.7 provenance); GATES.md updated, provisional mark lifted; QUESTIONS.md empty. Q1 closed: A confirmed by owner; flatness A18 reviewed (r5 BLOCKING), answered in
  `design/flatness_r2.md` (S15): optional increment after base A. Outer-loop study finished; stage 5 = base A.
- S36: G1 FINAL written in GATES.md (frozen with 5 evidence limits, provisional under Q4-A, not marked passed);
  stage 2 started provisionally; opus review T73 r1 BLOCKING (gyro break misses INDI's model and rotor-speed
  paths) answered by D-G2-BREAK (M3a torque-setpoint break) and note section 7; r2 CLOSED.
## Next actions (in order)
S44-S67 history: JOURNAL.md. Agent ledger: LEDGER.md. Lessons proposed: LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief).
NEXT (S65), per route check 64 (inner loop time-boxed: 1 session per law change from now on):
   (1) stage-5 slice 2: thrust-gap hover in position mode (NEW scenario, N1 C3; MC_INDI_W_MAX 2700) + one
   velocity/acceleration mode (altitude or position stick) + T123 deviations A3/A5/reset; haiku second key.
   (2) Bench defect N1 C2 (disturbance.py payload_add/com_shift/gust sized for x500): take mass/drag from the flown
   model, G1.5 check per profile. (3) Check the 'NOT FOUND' hooks of the draft (loop delay, GNSS latency, vibration)
   against stage-1 sim work before building. (4) G2-STEP 400 Hz reported run DONE S64 (9/9 within limits, A-30 seed spread parked).
   inputs zeroes the stock integrator every cycle (no gap compensation in that fault): gate pre-update reset on
   S98 (0) EXPLAINED: pretest_gate window [airborne+15, +45 s) = 47-77 s contains the 0.85 fault at ~71 s, the step
   transient inflates rate RMS (S70 hover_gap had no step in window: 0.0037); key +10..20 s after fault: 0.001-0.006.
   Use pretest_gate only on stationary scenarios, or end its window at the fault.
   S99 DONE: hooks SIM_GZ_SEED + SIM_GZ_IMU_NSC (results/t207_hooks/README.md; accel scale UNVERIFIED, needs full-rate
   accel log before G4). G2 rate table compiled (results/g2_rate_table_s99.md): 7 required cells missing at HEAD.
   NEXT S100: (i) read P99 pre-test; if OK, haiku serial batch of the missing rate cells at HEAD, 2 seeds each
   (pitch/yaw v2 800+400, roll v2 400, pitch/yaw model-only 400, + re-fly S57-era model-only cells at HEAD) and PID
   M1 reference cells; second key on margins; (ii) next hook: shared sim-time delay line (design/delay_line_hook_s94.md);
   (iii) S101 deadline rule (c) below still holds. Old: log a z-only
   active flag in indi_pos_status when next touching the module (P98 could not see it).
   S98: RC98 DONE (design/route_check_98.md): STOP coverage after T206; D-G7-HARNESS decided, impl deferred to
   stage 7. Order now: (a) G5 pre-test s5_gap085 POSCTL + stick ALTCTL gap + EN/AT_EN start check; (b) S99 sim
   hooks per design/gates_g3_g8_final_s94.md sec 1 (drop seed, shared delay line, IMU noise scale) + G2 verdict
   (yaw, model-only "not covered"); (c) if hooks/G2 verdict not done by S101, ask owner to narrow G2. Dropped:
   anomaly chases A-4/6/30/32/34-36, tooling keys. Then the 2-3 flight pre-test below (s5_gap085 regression + new stick altctl gap scenario).
   S97: (a) DONE de7c598e1e (compile-only); (b) decided D-ALTCTL-Z (e92a576e01), impl T204. Pre-test recipe: s5_gap085
   (offboard pos) exists; ALTCTL needs a new mode="stick" scenario with motor_fault (allowed without --sched), flown with
   --stick-mode altctl; command in results/stage5_s70/README.md line 17; metric bench/s5_gap_check.py. Was: (b) F-2: INDI serves ALTCTL by adding
   flag_control_climb_rate_enabled to want_indi (T200 log sec F3: the stage only needs finite a_c); (c) 2-flight SITL pre-test: thrust-gap hover 0.85 in POSCTL and ALTCTL + MC_INDI_EN=1
   MC_AT_EN=1 start check; then the sim hooks (old S96 plan below), yaw cell, identification slice.
   (5) attitude-break margin with the new setpoint path (G2) when the G2 table is resumed.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   S65-S68 session notes: JOURNAL.md (S69 entry).
   S69-S71: JOURNAL.md. Route checks 64-79 in design/; next: S84.
   S72-S80 (D-GAP, D-RATE-BLD accepted, A-34/A-35 parked, RC74/RC79): JOURNAL.md. Rule (RC74): no new anomaly
   chase unless a gate test fails, one session cap each. Flights no longer need MC_INDI_ACT_BLD 1.0 (default).
   S82-S85 session notes: JOURNAL.md (moved S86). Guard note: use `git commit -F <scratch file>` for long messages.
   S86-S92 (G2 outer z/xy cells, attitude-break fw + cells 267/400/800 Hz all PASS, RC89: STOP tooling,
   cosmetic re-flies, anomaly chases): JOURNAL.md. Check script bench/attitude_break_check.py; ratesp_csv.py keyed.
   S93-S96 notes (attitude-break model, RC93, G2 report section, G3-G8 FINAL, sim hooks MISSING list in
   design/gates_g3_g8_final_s94.md sec 1, delay line design/delay_line_hook_s94.md): JOURNAL.md S97 entry.
   M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36. Next route check S98.
   Guard note: a long inline `git commit -m` with this kind of text was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(S72-S78 rows done, details in JOURNAL.md; A-34/A-35 rows and S76 D-RATE-BLD line are recorded.)
(S93-S95 rows T194-T199 and S96 T201: JOURNAL.md. S86-S92 rows B87, T185, T189, RC89, T190, T191, B91, T192/T193, B91c, B92 all DONE: JOURNAL.md S93 entry.)
| T207 | S99: sim hooks SIM_GZ_SEED (drop RNG) + SIM_GZ_IMU_NSC (IMU noise scale), build, 2-flight G1.5 check | sonnet | design/t207_seed_noise_hooks_log.md | DONE fdcc54ed63 9d48cea369 (diff read, astyle clean): drop frac 0.10, seeds differ, gyro sigma ratio 3.0; second key K99 -> results/t207_hooks/key_k99.md |
| T208 | S99: compile G2 rate-cell table | sonnet | results/g2_rate_table_s99.md | DONE: 18 INDI cells, 6 prelim PASS (mostly S57 fw, pre setpoint lead), 0 FAIL, 12 NOT COVERED; 7 of 12 required 800/400 cells missing; no PID rate margins ever; measured-path model cross-check missing |
| P99 | S99: G2 rate pre-test at HEAD: pitch v2 800 Hz, yaw v2 400 Hz | haiku | results/g2_rate_pretest_s99/README.md | if incomplete: relaunch same brief |
| T206 | S98: lib tests T205 (f) 1-5 + pre-gate finite f_b/q | sonnet | design/t206_lib_mutation_tests_log.md | DONE b6e95f88c4 c32d022f9e (diff read; 4/5 break-checked, #5 partly not a bug; module compile-only) |
| P98 | S98: G5 pre-test gap 0.85 | sonnet | results/stage5_s98/README.md | DONE a462b69ad5: offboard standing z err 0.003 m (S70 0.33), ALTCTL 0.035 m, EN+AT_EN 0.027 m no start errors; pretest_gate FAILS rate RMS 0.022-0.024 vs 0.02 (cause open); z-only activity not logged |
| K98 | S98: haiku second key on P98 | haiku | results/stage5_s98/key_p98.md | DONE: gt z mean err +10..20 s = +0.011/-0.001/-0.002 m (A/B/C) agrees with P98 to 0.04 m; body-rate RMS 0.001-0.006 rad/s, so pretest_gate 0.022 'rate RMS' is another quantity (check its definition, 1 call) |

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.

- S38 GM jump explained (T80, `results/stage2_s38/gm_jump_check.md`): INDI measured Tb 0 phase grazes -180 deg on a
  plateau 12-27 Hz; at 800 Hz it crosses at 11.9 Hz (21.1 dB), at 400 Hz only at 27 Hz (34.8 dB) though |L| at 11.9 Hz
  is -22 dB. Model GM is phase-shape sensitive there: in S41 compare measured |L| over the plateau, and report GM
  together with the minimum |L|^-1 where phase is within 10 deg of -180 (decide in GATES.md before the first G2 test).
- Unmodelled in margins_models.py (T78 UNVERIFIED list): AlphaFilter coefficient formula, LPF2p coefficients from
  memory, gz/ESC latency 0, measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
