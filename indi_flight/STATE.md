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
NEXT S102:
   (i) DONE S101 (b9d6cf3285): K101 12/12 agree, all 24 INDI v2 rate cells (measured + model-only) PASS.
   (ii) PID M1 reference rate cells (reference only, F-5; 800 Hz x3 axes, 1 seed is enough).
   (iii) linear-model cross-check for the v2 path (margins_models.py, T78 UNVERIFIED list below) -> G2 verdict note.
   (iv) next hook: shared sim-time delay line (design/delay_line_hook_s94.md), needed by G3.
   (v) G5 pre-test s5_gap085 POSCTL + stick ALTCTL gap + EN/AT_EN start check (RC98 order (a)).
   (vi) attitude-break margin with the new setpoint path (G2) when the G2 table is resumed.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   Old: log a z-only active flag in indi_pos_status when next touching the module (P98 could not see it).
Notes: pretest_gate only on stationary scenarios, or end its window at the fault (S98). S99 hooks SIM_GZ_SEED +
   SIM_GZ_IMU_NSC done (accel scale UNVERIFIED, needs full-rate accel log before G4). D-G7-HARNESS decided, impl
   stage 7. M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36.
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
| V102 | S102: delay-hook pre-test, 2 hover flights (0/0 and 5/5 ms), IMU age + actuator lag | haiku | results/delay_pretest_s102/README.md | if cut: rerun results/delay_pretest_s102/fly.sh |
S102 finding: (ii) PID M1 has NO recipe: the gyro-break hook (`sim_inject`, design/stage2_margins_s35.md l.21) was never built.
  PID reference is F-5 reference only -> deferred behind (iv); build the M1 hook later in gz_bridge IMU callback beside A2.

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list): AlphaFilter coefficient formula, LPF2p coefficients from
  memory, gz/ESC latency 0, measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
