# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. Q6 OPEN (ident concept, not blocking). Q1-Q5, N1, N2 closed. Outer-loop study finished; stage 5 = base A
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
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
S119: T118 PASSED (31c9869179): INDI+PID idx 0/21/49 hold ~5 m, acro levelled, vz follows demand (corr 0.99);
  D-G3-STICK-PILOT decided. Open: runner keeps pilot sticks after LAND -> RC override to POSCTL (README; fix in runner
  when next touched, K118 MINORs). STAGE 4 OPENED: design/ident_concept.md + D-IDENT (PROPOSED) + Q6 to owner.
  I119 (sonnet): IV estimator bench/ident_iv.py + self-tests incl. closed loop -> design/i119_ident_iv.md.
  NEXT: key I119 (second sonnet, re-implement), then flight data: hover with M3a injection on quad5in, compare to
  derived G1; G2 cells at G1 x0.5/x2 with halved gains (ident config).
S117 sampler rule DONE 981e94f79e (D-G3-STICK-FACTORS). g3_run.py got --stop.
P117 G3 probe seed 117 n=60 (45 pos/10 stab/5 acro): results/g3_probe_s117/ (fly.sh, progress.txt, run_NNN/g3_done.json).
  Pretest idx 0,1,16: 1 pos + 16 stab ok; 0 ACRO watchdog trip (sank 3.5 m at 59.8 s; collective 0.1 = HTE
  lower bound, mass 0.76; acro held 11 deg tilt, no levelling). PID control on same draw: ctl_pid_run000/.
  P117 DONE: 60/60 flown; pos 45/45, stab 8/10, acro 3/5 no-abort ("ok" = no abort only; nothing scored).
  Non-ok 0,21,25,49 = open-loop stick collective (PID controls 0,21,49 in README; 25 uncontrolled). Resume: `setsid nohup bash indi_flight/results/g3_probe_s117/fly.sh 3 <idx...>`
  (runs with g3_done.json are skipped by g3_run.py; delete a partial run_NNN without it before re-running).
K115 DONE (design/key_k115_hte.md, 0 BLOCKING): fix AFTER L116 ends (same runner file): clamp [0.05,0.9] only on
  valid HTE (mc_att_control_main.cpp:241), meta hover_thr_used + hover_thr_source for every run (not stick only),
  tests that catch the 4 surviving mutations (run.json fields x2, stick_profile guard, main() thr0).
L116 DONE e97d826b27 (results/g3_ladder_s116/README.md): nominal, mass13, inert13, erpmloss, gnssmis fly; wind5
  flies with 4.6 m horiz RMS (stabilized has no position hold: expected); sag07, weak08, sat(one motor x0.35)
  trip height watchdog 60-63 s. Hypothesis: open-loop stabilized collective, not controller.
L116b DONE a7ac9375c0: PID trips the same watchdog (sag07 63.10 s, weak08 63.30 s) -> scenario property: stick
  stabilized is for attitude/rate factors only; thrust/wind factors go on position-hold scenarios. INDI on
  o1_lemniscate --sched holds altitude with sag/weak/sat/wind (vert RMS 0.03-0.18 m). A-41 opened (horiz 2.8 m).
A116 DONE ca6825db51: stick_zsine_o6 flies in altctl, posctl, posctl+sag07 (INDI). metrics.py has no stick-mode
  reference/window for altctl/posctl (vertical = commanded climb): add one before these enter the batch.
N116 DONE 4e25b1aa00: nominal horiz RMS INDI 2.805 / PID 2.800 m = faulted rows; A-41 closed.
H116 DONE dce771f1e6 (K115 fixes, 9+3 tests pass, mutations checked; slew-lag m3 not addressed, accepted:
  probes only). Key of a bench-only meta fix not required (no safety path).
(Done rows up to K114/F114: JOURNAL.md S100-S115; ledger LEDGER.md. Yaw model tool defect open: margins_of hangs if ts_true=0.)

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
