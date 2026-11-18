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
   S96 DONE: T199 BLOCKING confirmed + all 5 findings fixed (T200), autotune/watchdog (T201); second key T202
   (design/t202_dgap_fix_key.md): its 2 MAJORs fixed by orchestrator 25e420b155 (vacuous test, break-checked) and
   dff2b7a805 (integral hoist, compile-only). Open MINORs: lower mean_u limit untested; lagging mean_u at reset untested;
   permanently saturated motor freezes b (no gap tracking): state in report limits.
   NEXT S97: (a) haiku/sonnet key on dff2b7a805 (10 lines); (b) F-2: INDI serves ALTCTL by adding
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
   S93 (launch 20261118-091231, cap $3): attitude-break model + outer-loop factor (T194, T195): PM matches measured
   within 0.3 deg; GM model 1.6-4.6 dB conservative (A-36 residue, linked A-35); PID model-only ref in
   results/stage5_s91_attbreak/model_vs_measured.md.
   RC93 (design/route_check_93.md, accepted): stop model refinement, tooling keys, cosmetic re-flies; A-36 residue
   accepted as conservative and bounded. S94 DONE: G2 report section (report/g2_margins.md, 4542ca1d83; empty cells:
   PID measured, model-only at HEAD, yaw/pitch v2, 267 Hz outer, telemetry latency value, 2nd key S86/S87/S91);
   G3-G8 FINAL text in GATES.md + D-GATES-G3G8 (18af6e3a66). NEXT S95: combined opus review of stage-3 safety diff +
   stage-5 slice (~$1.1, launch first, cap >= $2.5). S96: sim hooks MISSING per design/gates_g3_g8_final_s94.md sec 1
   (shared sim-time delay line for loop delay + GNSS latency; G5 event injectors; per-run sampler g3_sample.py;
   telemetry-drop seed per run), each with G1.5 check + second key. Delay line designed: design/delay_line_hook_s94.md
   (check world step and GNSS path first). S97: yaw cell + first identification slice.
   M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36. Next route check S98.
   Guard note: a long inline `git commit -m` with this kind of text was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(S72-S78 rows done, details in JOURNAL.md; A-34/A-35 rows and S76 D-RATE-BLD line are recorded.)
(S93-S95 rows T194-T199 and S96 T201: JOURNAL.md. S86-S92 rows B87, T185, T189, RC89, T190, T191, B91, T192/T193, B91c, B92 all DONE: JOURNAL.md S93 entry.)
| T200 | S96 (launch 20261118-094323): T199 BLOCKING CONFIRMED by orchestrator (_coll_meas = vehicle_thrust_setpoint, commanded, passed as mean_u). Fix findings 1,2,4,5 + 3 (integrator reset only when INDI ran) in indi_accel_control + mc_indi_pos_control, tests first with break-checks | sonnet | design/t200_dgap_fixes_log.md | DONE bf44ece093 (diff read; 5 new tests fail-before/pass-after; module side F3-F5 compile-only; residue: stock integral in a_ref on the 1st active cycle after bypass; ALTCTL not served by INDI: F-2 open item, note in log) |
| T202 | S96: second key on bf44ece093 vs review findings 1-5 | sonnet | design/t202_dgap_fix_key.md | DONE: no BLOCKING, 2 MAJOR fixed 25e420b155 dff2b7a805 |

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
