# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 5 (outer loop, every mode) opened S129. Stage 4 ident frozen (D-IDENT-STOP, RC126), defaults D-DEFAULTS-FW (S128).
  Stage 3 inner loop time-boxed (RC64/RC74). Stage 1 frozen S36. Started S1 (2026-11-15).
- Gates: G1 PASSED S84 | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open, FINAL text S134 (GATES 5b) |
  G6 open | G7 open | G8 open.
- Blocker: none. No open question. Owner directive 2026-11-20 (F-7/F-8/F-9) acted on S134: D-F7-GROUND written,
  D-STAGE-STALE (stock branch) and D-HANDOVER superseded.
## Next actions (in order; each names its gate item)
History: JOURNAL.md. Agent ledger: LEDGER.md. LESSONS_PROPOSED.md (cost calibrations: read before sizing a brief).
1. G5.4 + G5.1-5.5/5.7: post-fix smoke OK (results/f7_smoke_s134_fix: edge 4.7 % hover, dip 0 m, ground collective
   0.001, xy RMS 0.486, land vz 0.70). Next: run the IndiAccelControl lib gtest (resetBlend), then the first 3-seed
   G5 batch (item 3). Edge > 10 % on any seed -> D-F7-GROUND alternative 1, 1 session max.
2. G5 checker: fold the edge/ramp metric of f7_smoke_s134_fix/extra_metrics.py into auto_smoke_check.py (self-test).
3. G5.1-G5.5, G5.7 first 3-seed batch with existing scenarios (GATES 5b row map); checker per row reused
   (auto_smoke_check.py, offb_vel_check.py, passthrough_check.py); write results/g5_probe_s13x/README.md.
   A-46 closed by this batch or superseded by F-7.
4. G5.6/5.8/5.9/5.10/5.11: build the missing injectors one at a time (G1.5 check each), then fly the rows.
5. G7 (deferred, stage 7): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site (K128 MAJOR), checker
   self-tests for passthrough_check/offb_vel_check.
Route check next: S138 (RC133 filed, accepted except PID pass line, F-5).
Rule (RC64/RC74): 1 session per inner-loop law change; no anomaly chase unless a gate test fails.
G3/G5 batches before the stage-6 freeze are PROBES (RC113). G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1.
Offline G2 todo before stage 6: outer-cell margin key, linear outer-loop model, A-36/A-39 bound, 267 Hz rows
  (verdict design/g2_verdict_s108.md).
G3 tooling exists (g3_run.py, quad5in variants, overrides/wind/motor_fault/timed eRPM loss). gust_x results before
  b0486b703e not comparable. eRPM-loss lateness 36-122 ms: take effective time from the log. Weak+sat unflown.
  Acro = G3-unprobed, G5 carries it (RC118). altctl/posctl not in G3 MODE_MIX.
DEFERRED until defaults exist: g3_checks.py, gate_g3.sh, frozen-telemetry hook, G4 profiles.
Deferred to before G6: yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44).
STOP list: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a
  consumer, stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells), --sched-anchor and set_param fixes,
  EdgeState design (RC133 action 3, dropped by owner directive).
Later: combined opus review of stage-3 safety diff + stage-5 slice (incl. T9/T10 keys) before any freeze. Log a
  z-only active flag in indi_pos_status when next touching the module.
## Notes
- pretest_gate only on stationary scenarios, or end its window at the fault (S98). SIM_GZ_SEED + SIM_GZ_IMU_NSC hooks
  (accel scale UNVERIFIED, full-rate accel log before G4). D-G7-HARNESS decided, impl stage 7. M3 PT-change UNVERIFIED.
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39. A-46 (flight-edge thrust step) -> next action 3.
- Stabilized stick centre = HTE; runner thr0 honours HTE valid flag, fallback MPC_THR_HOVER.
- Check script bench/attitude_break_check.py; ratesp_csv.py keyed; run_validity.py (W_MAX check) over cited sets.
- Runner open: MC_INDI_EN 1 in a params file does not start the module, only MC_RATE_CTL_TYPE 1 does (accept
  MC_INDI_EN as alias, keyed). Pilot sticks kept after LAND -> RC override to POSCTL (K118 MINORs). margins_of hangs
  if ts_true=0.
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); firmware ACT_TC 0.05, MC_INDI_ID_OK 0
  halves K.
- Guard: a long inline `git commit -m` is blocked; use `git commit -F <scratch file>`.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
- S133 results: ACRO pass-through and offboard vel-only probes pass (results/s133_passthrough); MANUAL/STABILIZED
  unflown; A133 checkers have no self-test yet.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
S134 F-7 DONE b9fb83c4a0 (keyed K134: 0 BLOCKING, MAJORs floor 0 before flight + arm/disarm state reset FIXED; gtests
  8/8 suites, ArmEdges test break-checked; open MINORs: ground xy tilt, IndiAccelControl lib test not run after
  resetBlend, reset test checks the decision only -> stage-7 harness). Pre-fix smoke (1 seed): edge step 4.7 % hover,
  dip 0 m, ramp max 0.1 s change 7.4 % hover, stage_mode 2 ground/ramp -> 1 flight -> 2 landing.
## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
