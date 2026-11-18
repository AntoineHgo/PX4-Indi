# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. QUESTIONS.md empty (Q1-Q5, N1, N2 closed). Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S101 entry holds the latest moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S103.
Rule (RC64/RC74): inner loop time-boxed, 1 session per law change; no new anomaly chase unless a gate test fails.
NEXT S107 (RC103 done S103; next route check S108). RC103 order: (v) DONE, (iii) DONE S105, hook B DONE S106
   (d52576b02a + fix 99673b62bd; matched = --gnss-delay equal to --gps-dly; results/gnss_delay_key_s106/README.md).
   S107: check K107 note; `make format` check on gz_bridge; then yaw linear model in margins_models.py (8 yaw
   cells lack cross-check, design/g2_verdict_rate_s105.md). G1.5 estimator M-vs-X separation needs a moving
   scenario: do it in the G3 pre-test, not before.
   (0) DONE S103: A-37 closed (DLY_ACT lag d+[0,1.25 ms), results/a37_actlag_s103). Hook B (GNSS, note s.4) after (v),(iii).
   (i) DONE S101 (b9d6cf3285): K101 12/12 agree, all 24 INDI v2 rate cells (measured + model-only) PASS.
   (ii) PID M1 reference rate cells (reference only, F-5; 800 Hz x3 axes, 1 seed is enough).
   (iii) linear-model cross-check for the v2 path (margins_models.py, T78 UNVERIFIED list below) -> G2 verdict note.
   (iv) delay hooks A1+A2 DONE S102 (c6ba02609f, keyed K102); hook B GNSS open.
   (v) DONE S104: A-38 closed (est-sp 0.000 m after gap; -0.07 m is estimator truth-est offset present before
       the event). G5 rows must report truth-sp and truth-est separately (lesson 3).
   (vi) attitude-break margin with the new setpoint path (G2) when the G2 table is resumed.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   Old: log a z-only active flag in indi_pos_status when next touching the module (P98 could not see it).
Notes: pretest_gate only on stationary scenarios, or end its window at the fault (S98). S99 hooks SIM_GZ_SEED +
   SIM_GZ_IMU_NSC done (accel scale UNVERIFIED, needs full-rate accel log before G4). D-G7-HARNESS decided, impl
   stage 7. M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36. PID M1 hook deferred (RC103).
   Flights no longer need MC_INDI_ACT_BLD 1.0 (default). Check script bench/attitude_break_check.py; ratesp_csv.py keyed.
   Guard note: a long inline `git commit -m` was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(Done rows up to K100/P100: JOURNAL.md S100/S101 entries.)
| B100 | S100: model-only batch, 10 flights | haiku | results/g2_rate_modelonly_s100/batch/batch.log | DONE S101: 10/10 PASS, worst GM 10.12 dB, PM 70.8, DM 39.7 ms; torque MODEL_ONLY_VERIFIED |
| K101 | S101: second key of 12 model-only cells (P100+B100) | self (docker) | results/g2_rate_modelonly_s100/key_k101/summary.md | DONE b9d6cf3285: 12/12 agree |
| H102 | S102: delay-line hooks A1+A2 in gz_bridge (uncommitted, builds, 0 warnings, not flown) | sonnet | design/delay_line_impl_s102.md | DONE; orchestrator read diff, OK |
| K102 | S102: second key of H102 | sonnet | design/delay_line_key_s102.md | DONE: 0 BLOCKING, M1+M2 fixed by orchestrator, c6ba02609f |
| V102 | S102: delay-hook pre-test d0/d5 | haiku | results/delay_pretest_s102/README.md | DONE: IMU PASS (age 0/5000 us), actuator UNVERIFIED -> A-37 |
| G104 | S104: scope G2 verdict note (iii), read-only | haiku | design/g2_verdict_scope_s104.md | DONE (haiku, UNVERIFIED): table claim checked: results/g2_rate_table_s99.md "S101 update" holds 24/24 (K100+K101), only its body is pre-S101; A-21 model-vs-measured PM gap ~18 deg (results/stage2_s41/a21_model_vs_measured.md) > 10 deg G2 tolerance: check which loop/version it was before (iii) |
| X105 | S105: G2 model-vs-measured cross-check, offline | sonnet | design/g2_crosscheck_s105.md | DONE: 16 roll/pitch cells within tol (dPM<=4.7, dGM<=1.86); yaw unmodelled; filters verified; A-21 n/a to v2 |
| RC103 | S103: route check | sonnet | design/route_check_103.md | DONE: A-37 time-box $0.5 then park; then G5 pre-tests, G2 verdict note, hook B; defer PID M1 |
| S103 | S103: scope POSCTL stick gap scenario (read-only) | haiku | design/posctl_gap_scope_s103.md | DONE: scenario + --stick-mode posctl, flown |
| H106 | S106: hook B GNSS delay (SIM_GZ_GPS_DLY) impl+build+1 flight | sonnet | design/gnss_delay_impl_s106.md | DONE d52576b02a (fw) bd0aa768f4 (pretest: age 200000 us x110, 1 Hz log) |
| K106 | S106: second key of H106 + L=250 flights | sonnet | results/gnss_delay_key_s106/README.md | DONE: BLOCKING (SENS_GNSS0_DELAY inert) fixed 99673b62bd, M2 verified (EKF time err +4 ms matched) |
| K107 | S106: second key of fix 99673b62bd (read-only) | sonnet | design/gnss_delay_fix_key_s106.md | in flight; resume: re-launch same brief if note missing |
| A103 | S103: A-37 test (a9e5066a55), hover d5/d10 | host bg | results/a37_actlag_s103/README.md | DONE: A-37 closed |
S102 finding: (ii) PID M1 has NO recipe: the gyro-break hook (`sim_inject`, design/stage2_margins_s35.md l.21) was never built.
  PID reference is F-5 reference only -> deferred behind (iv); build the M1 hook later in gz_bridge IMU callback beside A2.

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
