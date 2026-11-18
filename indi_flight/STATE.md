# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 3 (inner loop) opened S49; stage 2 (analysis tools, margins) from S36; stage 1 frozen S36 (G1 FINAL). Started S1 (2026-11-15). Stage 0 done. Session 3: ref airframe model done.
- Gates: G1 PASSED S84 (owner S50 rule; G1.5 per injector, evidence limits) | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. QUESTIONS.md empty (Q1-Q5, N1, N2 closed). Outer-loop study finished; stage 5 = base A
  (`design/flatness_r2.md`: flatness = optional increment after base A).
## Next actions (in order)
History: JOURNAL.md (S107 entry holds the latest moves). Agent ledger: LEDGER.md. Lessons proposed:
LESSONS_PROPOSED.md (agent cost calibrations: read before sizing a brief). Route checks in design/; next: S118 (RC113 filed).
Rule (RC64/RC74): inner loop time-boxed, 1 session per law change; no new anomaly chase unless a gate test fails.
NEXT S108 per RC108 (design/route_check_108.md, filed S107; next route check S113). Accepted with one amendment:
   G3/G5 batches before the stage-6 freeze are PROBES of the current stack (find failures early), not gate evidence.
   S108 DONE 93f94320d3: design/g2_verdict_s108.md + GATES.md G2 table (outer cells S83/S86/S87 added; draft had
     missed them). Attitude seed 2 NOT flown (pre-freeze, stage 6 re-flies all). Offline G2 todo before stage 6:
     outer-cell margin key, linear outer-loop model, A-36/A-39 bound, 267 Hz rows.
   S109 DONE: K108 closed (D-G3-SAMPLER-K108, 3a245d1590, keyed e634a78671); quad5in variants bd612779a1 (key K109).
   S110 DONE: G3 driver g3_run.py (c5acce1b39, K109 MAJOR closed) + scenario overrides/wind (fc3ef9e626), key K110.
   S111 DONE: K110 M-1..M-3 closed b0486b703e (air-relative gust_x drag via gz pose finite diff; timed eRPM loss;
     motor_fault list), keyed K111 (0 BLOCKING), K111 F-1/F-3/F-5 closed 6e8c4fa474 (runner hooks pinned, 4 mutations
     caught). F-2 accepted bounded: pose/clock threads, velocity lag 0-1 pose period, applied wrench logged.
     All gust_x results before b0486b703e are not comparable (drag was wind-only).
   S112 order: 3-flight pre-test (haiku runs, serial): o1_lemniscate --sched and stick_zsine_o6, overrides with
     motor_fault list (weak+sat) + timed erpm_loss + wind. Check on logs: pose topic gives velocity (run.json
     disturbance.injector vel_none small), eRPM loss window at drawn offset/duration, timings under --sched /
     --sched-anchor (K110 m-5), sub-run set_param latency (K111 F-4). Then frozen-telemetry hook (two keys);
     g3_checks.py + key; gate_g3.sh consuming run JSON hooks block; then ~20-run pre-test.
   S109: G3 randomised runner (plant draw per run, all G3 axes incl. GNSS hook B: matched = --gnss-delay == --gps-dly)
     + ~20-run pre-test; fold G1.5 estimator M-vs-X separation (moving scenario) into it.
   S110: first G3 probe batch >= 60 runs. S111: G5 mode/transition batch. S112: G4 noise profiles.
   STOP: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a consumer,
     stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells).
   Done history (RC103 list i-vi, hooks A1/A2/B, A-37, A-38, yaw model): JOURNAL.md S101-S107.
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
(Done rows up to K109: JOURNAL.md S100-S109 entries; ledger LEDGER.md. Yaw model tool defect open: margins_of hangs if ts_true=0.)
(R110/O110/K110/F111/K111/G111 done: JOURNAL.md S110-S111.)
(P112 done: results/g3_pretest_s112/README.md, agent-reported, NOT yet verified by orchestrator.)
P112 faults: 1, 2, 4b fixed S113; 3 (eRPM loss 36-122 ms late) accepted, effective time to be taken from the log;
  4a explained (stick fault below); 5 dropped (RC113). Weak+sat together still unflown (ladder covers it).
S113: RC113 filed 140164bc93 (accepted: single-factor ladder S114-S115 before 60-run mixed batch S116; drop
  --sched-anchor + set_param-latency fixes, eRPM-loss lateness logged as applied; stop rule in RC113 sec 5).
  F113 faults 1, 2, 4b fixed 09515cd8ae (40 tests pass, orchestrator ran them). In flight: K113 (sonnet, key of
  09515cd8ae: DONE 95eff712f6, 0 BLOCKING; S114 fix MINOR 5 = g3_run classify() says ok on rc 0 even if run.json
  exit_status failed, MINOR 6 = aborted metrics.json lacks window (a11/g1_checks KeyError)). M113 DONE 9b208ba0a7
  (results/g3_single_s113/README.md): stabilized stick scenarios fall at the 52 s mode switch for INDI m1.3, INDI m1.0
  and PID m1.0 alike -> SET-UP FAULT, not controller: bench/stick_profile.py:54 hover stick = 2*hover_thr-1 ignores
  the PX4 manual throttle curve (MPC_THR_CURVE / MPC_THR_HOVER; mid stick = hover under default curve, UNVERIFIED).
S114 FIRST: (a) fix stick_profile stabilized/acro hover stick from the PX4 source mapping + test + key, re-fly
  stick_zsine_o6 stabilized nominal (O-13 flyability, INDI and PID); also check altctl/posctl stick scenarios fly;
  (b) K113 MINOR 5, 6. Then RC113 ladder (8 single-factor runs, sec 5 order). Next route check S118.

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS), MINORs frozen-b on saturated motor, lagging
  mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests (T202/T205 rows in JOURNAL S98).
- Review notes folder (`indi_project/review/external_review_s59_notes/`) not read in full at stage 0 (budget);
  open per item: `sim_review.md` for simulator work, `module_parity.md` for stage 3/5, `test_review.md` for stage 3,
  `ident_review.md` for stage 4, `remetric.py`/`hover.py` for the errata.
- Unmodelled in margins_models.py (T78 UNVERIFIED list; filters verified S105): gz/ESC latency 0 (likely cause of
  1-2 dB 400 Hz GM residual), measured path = eta x motor state, yaw, attitude loop; 267 Hz analytic only.
