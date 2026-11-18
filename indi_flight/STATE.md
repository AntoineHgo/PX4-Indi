# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. Q6 CLOSED S120 (B: INDI flies its own ident; conditions (i)-(v) in D-IDENT). No open question. Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S100-S115 entries hold the recent moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S122 (RC118 filed).
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
   S116 DONE: K115 key + fixes, RC113 ladder + controls + nominal baseline (results/g3_ladder_s116, JOURNAL S116).
   S117 DONE: D-G3-STICK-FACTORS (981e94f79e); altctl/posctl excluded from batch (not in MODE_MIX); probe P117.
   RC118 (design/route_check_118.md, ACCEPTED): stick pilot time-boxed to S118-S119 (key + re-fly idx 0/21/49
     INDI+PID); if acro still fails for both, acro = G3-unprobed, G5 carries it. Then STAGE 4 (identification
     chain from x2/x0.5 starts, defaults file, minimal G4 profile) S119-S121, then G5 build (base A, every mode)
     S122-S125. DEFERRED until defaults exist: g3_checks.py, gate_g3.sh, frozen-telemetry hook, G4 profiles.
     Next route check S122.
   S118 check: G3/o1 probes ran MC_INDI_POS_EN=0 (ulog param, run_001): INDI rate loop under STOCK mc_pos_control.
     G3 evidence for the INDI outer loop needs MC_INDI_POS_EN=1 in the base params (stage 5).
   STOP: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a consumer,
     stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells), --sched-anchor and set_param-latency fixes.
   Later: G5 build order (draft end), combined opus review of stage-3 safety diff + stage-5 slice before any freeze.
   Old: log a z-only active flag in indi_pos_status when next touching the module (P98 could not see it).
Notes: pretest_gate only on stationary scenarios, or end its window at the fault (S98). S99 hooks SIM_GZ_SEED +
   SIM_GZ_IMU_NSC done (accel scale UNVERIFIED, needs full-rate accel log before G4). D-G7-HARNESS decided, impl
   stage 7. M3 PT-change UNVERIFIED. Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39. PID M1 hook deferred (RC103).
   Flights no longer need MC_INDI_ACT_BLD 1.0 (default). Check script bench/attitude_break_check.py; ratesp_csv.py keyed.
   Guard note: a long inline `git commit -m` was blocked; use `git commit -F <scratch file>`.
S121 FINDING: every "indi" G3 run S110-S118 flew the STOCK rate loop (base params lacked MC_RATE_CTL_TYPE 1).
  Fixed in g3_run.py + run_scenario.py guard; P117/T118/ladder INDI verdicts VOID. TODO test in test_g3_run.py
  asserting the flag (DONE S122). S122: idx 21 re-flown with real INDI: ok (z ~5 m, landed; g3_refly_s121/README.md).
S122 FINDING 2: G3 base params lacked MC_INDI_W_MAX (G2 s107/stage-5 runs had 2700) -> measured path OFF
  (measured_torque_in_use 0, no actuator_torque_measured; design/s122_torque_measured_logging.md). s121 re-flies
  are MODEL-ONLY. Fixed 0a49572149 (+ run_validity.py: g3_done.json "validity", outcome "void"; 23 tests;
  UNKEYED: two-key review before gate use). Re-fly idx 0/21/49 with W_MAX -> results/g3_refly_s122/.
RC122 (design/route_check_122.md, ACCEPTED): S123 = M3a ident hover (POS_EN 0 and 1 once each), estimator offline
  from x0.5/x1/x2; S124 = estimator verdict on D-IDENT (i)-(iii), draft defaults file, G5 list. Also run
  run_validity over past result sets that are cited as evidence (G2 s107, stage-5) once keyed.
Stage 4 next (history S119-S120 in JOURNAL): ident pretest hover with M3a injection on quad5in (roll, AMP ~0.01,
  NP >= 6, settle delay, halved gains; design/h120_m3a_signals.md), estimator bench/ident_iv.py offline (K120 keyed;
  size arrays, ulimit -v 4000000), compare to derived G1; then G2 cells at G1 x0.5/x2 (ident config).
  Runner open: pilot sticks kept after LAND -> RC override to POSCTL (K118 MINORs). margins_of hangs if ts_true=0.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
(none) S123: K122 3 BLOCKING fixed 46b2e2ceb2 (design/fix_k122_s123.md, broken-checked, 26 tests). H123 DONE
  f49f8029f8 (results/ident_m3a_s123/README.md): M3a hover pos0/pos1 valid, MC_INDI_INJ_AMP 0.003 (0.01 = 25 deg,
  void; AMP is per component x18), INJ_DLY 8, NP 6, roll <= 7.3 deg. esc_status/actuator_torque_measured 800 Hz
  (H120 "100 Hz" doubt CLOSED). measured_torque_in_use 84 % of samples (check: ground phase only?).
  NEXT S124: run bench/ident_iv.py on pos0/pos1 (SNR at AMP 0.003 UNVERIFIED), then x0.5/x2 starts, D-IDENT verdict.
S122 DONE: re-fly idx 0/21/49 with W_MAX all ok + valid, measured path in use (results/g3_refly_s122/README.md,
  8cfbc36d85). T118 INDI half restored. Model-only s121 idx 49 aborted: runner pilot sticks -> POSCTL after LAND
  (K118 MINOR: fix in runner before the next stick batch). K122 key DONE (design/key_k122_run_validity.md): 3
  BLOCKING open: CA_R_W_MAX alias not translated (run_validity.py:14,58-64); exception in check_validity loses the
  outcome (g3_run.py:263, wrap and fail closed); ulog without g3_params.txt skips the check (g3_run.py:251).
  NEXT S123: fix those 3 (sonnet ~$0.15, test each by breaking), then RC122 S123 plan (M3a ident hover).

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
