# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. QUESTIONS.md empty (Q1-Q5, N1, N2 closed). Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S100-S115 entries hold the recent moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S118 (RC113 filed).
Rule (RC64/RC74): inner loop time-boxed, 1 session per law change; no new anomaly chase unless a gate test fails.
Plan RC108 (design/route_check_108.md) + RC113 (design/route_check_113.md, accepted):
   G3/G5 batches before the stage-6 freeze are PROBES of the current stack (find failures early), not gate evidence.
   Offline G2 todo before stage 6: outer-cell margin key, linear outer-loop model, A-36/A-39 bound, 267 Hz rows
     (verdict design/g2_verdict_s108.md).
   G3 tooling: g3_run.py driver, quad5in variants, scenario overrides/wind/motor_fault/timed eRPM loss (S109-S111,
     keyed). gust_x results before b0486b703e not comparable. eRPM-loss lateness 36-122 ms: take effective time
     from the log. Weak+sat together still unflown (ladder covers it).
   Stick scenarios: stabilized centre = HTE (807fd6a08a), runner thr0 honours HTE valid flag, fallback
     MPC_THR_HOVER (8f57b47f7e). A-40 closed. Stabilized stick altitude 6.5 m mean vs 5 m hold (open loop, ok).
   NEXT S116: (1) sonnet key K115 of 8f57b47f7e (out design/key_k115_hte.md); (2) RC113 ladder (8 single-factor
     runs, haiku, serial, RC113 sec 5 order; first re-fly stick nominal to confirm hover_thr_used in run.json = HTE
     valid); (3) altctl/posctl stick flyability. Then 60-run mixed G3 probe batch; then frozen-telemetry hook (two
     keys), g3_checks.py + key, gate_g3.sh; G5 mode batch; G4 noise profiles.
   STOP: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a consumer,
     stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells), --sched-anchor and set_param-latency fixes.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   Old: log a z-only active flag in indi_pos_status when next touching the module (P98 could not see it).
Notes: pretest_gate only on stationary scenarios, or end its window at the fault (S98). S99 hooks SIM_GZ_SEED +
   SIM_GZ_IMU_NSC done (accel scale UNVERIFIED, needs full-rate accel log before G4). D-G7-HARNESS decided, impl
   stage 7. M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39. PID M1 hook deferred (RC103).
   Flights no longer need MC_INDI_ACT_BLD 1.0 (default). Check script bench/attitude_break_check.py; ratesp_csv.py keyed.
   Guard note: a long inline `git commit -m` was blocked; use `git commit -F <scratch file>`.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
K115 DONE (design/key_k115_hte.md, 0 BLOCKING): fix AFTER L116 ends (same runner file): clamp [0.05,0.9] only on
  valid HTE (mc_att_control_main.cpp:241), meta hover_thr_used + hover_thr_source for every run (not stick only),
  tests that catch the 4 surviving mutations (run.json fields x2, stick_profile guard, main() thr0).
| L116 | RC113 ladder, stick_zsine_o6 INDI nominal + 8 factors | haiku | results/g3_ladder_s116/README.md | re-run missing rows (fly.sh there) |
(Done rows up to K114/F114: JOURNAL.md S100-S115; ledger LEDGER.md. Yaw model tool defect open: margins_of hangs if ts_true=0.)

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
