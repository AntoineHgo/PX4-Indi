# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. Q6 CLOSED S120 (B: INDI flies its own ident; conditions (i)-(v) in D-IDENT). No open question. Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S100-S115 entries hold the recent moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S129 (RC126 filed).
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
S121/S122 findings (stock rate loop, W_MAX missing -> run_validity.py): JOURNAL S122.
RC122 (design/route_check_122.md, ACCEPTED): S123 = M3a ident hover (POS_EN 0 and 1 once each), estimator offline
  from x0.5/x1/x2; S124 = estimator verdict on D-IDENT (i)-(iii), draft defaults file, G5 list. Also run
  run_validity over past result sets that are cited as evidence (G2 s107, stage-5) once keyed.
Stage 4 next (history S119-S120 in JOURNAL): ident pretest hover with M3a injection on quad5in (roll, AMP ~0.01,
  NP >= 6, settle delay, halved gains; design/h120_m3a_signals.md), estimator bench/ident_iv.py offline (K120 keyed;
  size arrays, ulimit -v 4000000), compare to derived G1; then G2 cells at G1 x0.5/x2 (ident config).
  Runner open: MC_INDI_EN 1 in a params file does not start the module, only MC_RATE_CTL_TYPE 1 does (S128 smoke; accept
  MC_INDI_EN as alias, keyed). Pilot sticks kept after LAND -> RC override to POSCTL (K118 MINORs). margins_of hangs if ts_true=0.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S127 | K127 key (design/key_k127_defaults.md): 0 BLOCKING; MAJ1 G1_Y 205 = D-IDENT-STOP stance (fit is the biased one), no action; MAJ2 ACT_TC 0.033 unflown -> 1-flight pretest before adopting; MAJ3 = gate gap below. |
| S128 | DONE impl D-DEFAULTS-FW (MC_INDI_ID_OK halves K, G1 fw defaults quad5in, airframe W_MAX 2700, bench ID_OK 1); 70 lib tests pass, break-check ok, SITL builds | sonnet | design/impl_s128_id_ok.md | - |
| S128 | DONE K128: 0 B, 1 MAJ (call site untested -> stage-7 harness), MINOR comment fixed | sonnet | design/key_k128_id_ok.md | - |
| S128 | DONE smoke hover ID_OK 0 (fw halving, defaults file): ok, z std 0.015 m, xy 0.05 m, p max 0.028 rad/s | haiku | results/smoke_s128_idok0/README.md | - |
Next S129: route check RC129 (due); ACT_TC 0.033 1-flight pretest (K127 MAJ2); then stage-5 build list (RC126).
| S127 | DONE defaults draft (keyed K127). Gaps: no ident-status param / halving in firmware; W_MAX fw default 0 (measured path off), G1 fw defaults 5-8x low; ACT_TC 0.033 proposed | sonnet | design/defaults_s127.md, bench/params/quad5in_indi_defaults.params | S128: key it, then firmware: ident-status param + halved gains + defaults |
S124/S125 ident results (roll 1755-1768, pitch 1649, halved-gain 1757.9 PASS): JOURNAL S124-S125, fit_s124.md.
  RC126 (design/route_check_126.md, ACCEPTED): ident frozen as is (D-IDENT-STOP). S127: conditions (iv)/(v) OFFLINE
  on existing logs, defaults file from derived values (ident checks it), module reads it. S128-S129: stage-5 build
  list, base-A outer loop for every mode, one smoke flight per mode, first G5 probe. Deferred to before G6: yaw fit
  fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44). Next route check S129 (owner question if no
  multi-mode code by then). A-42 closed: one -n and one --out dir per run.

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
