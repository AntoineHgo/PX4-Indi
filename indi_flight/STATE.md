# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 5 (outer loop, every mode) opened S129. Stage 4 ident frozen (D-IDENT-STOP, RC126), defaults D-DEFAULTS-FW (S128).
  Stage 3 inner loop time-boxed (RC64/RC74). Stage 1 frozen S36. Started S1 (2026-11-15).
- Gates: G1 PASSED S84 | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open, FINAL text S134 (GATES 5b) |
  G6 open | G7 open | G8 open.
- Blocker: none. Q7 answered (rule A), see item 0. Owner directive 2026-11-20 (F-7/F-8/F-9) acted on S134: D-F7-GROUND written,
  D-STAGE-STALE (stock branch) and D-HANDOVER superseded.
## Next actions (in order; each names its gate item)
History: JOURNAL.md. Agent ledger: LEDGER.md. LESSONS_PROPOSED.md (cost calibrations: read before sizing a brief).
0. S140: Q7 closed (rule A in GATES 5b G5.7 AMENDED S140; g5_g57_s139 official probe verdict FAIL 2/3).
0b. S140 SET-UP FAULT in every G5 probe: sim GNSS latency 0 with EKF SENS_GNSS0_DELAY 110 (estimate leads truth
   ~110 ms, 0.35 m/axis at 3-4 m/s). G5.5 S139: o5/o6/offb_vel_step PASS, o1-o4/o7 FAIL horiz 0.66-1.36 m (limit 0.5;
   PID o1 1.04 m). Nominal plant from now on: --gps-dly 110 --gnss-delay 110 (matched). Matched pre-test
   (results/g5_g55_s140_gnss): estimator fixed (0.05 m) but o1 0.78 m, o2 0.93 m FAIL: truth lags setpoint 160 ms,
   jerk FF off (McIndiPosControl.cpp:57). G5.1-G5.4 re-fly at freeze with matched GNSS.
0c. S141 A18 DONE (7e58bea57c, keyed t208_a18_key2: MAJOR gate-flip lead pulse fixed by me, unkeyed fix -> 4c
   review; MINORs in key2). Probe results/g5_g55_s141_a18: o1 0.590 m, o2 0.793 m, still FAIL (0.5); lag 160->140 ms.
   NEXT (G5.5, 1 session of cause search left, then re-open): lag split (README) says att sp->att 60-90 ms with
   omega_ff, and ~50 ms a_c->att sp. Check omega_ff size vs the analytic need (jerk-difference LPF and 43 Hz hold
   delay; roll p95 only 0.31 rad/s) and the accel-loop filter delay. Then G5.7 x1 matched.
1. G5.4 DONE as probe S135: 9/9 runs (auto_tour, auto_land10, auto_rtl20 x3 seeds) all limits PASS
   (results/g5_probe_s135/README.md; checker auto_smoke_check.py g54_*, keyed g54_key2.py). Re-fly at freeze.
2. G5.1 DONE as probe S137: 6/6 PASS at K_Y 20 (acro + stabilized x3). Re-fly at freeze.
3. G5.2 DONE as probe S138: 6/6 PASS altctl/posctl (results/g5_g52_s138, g52_check keyed AGREE). Re-fly at freeze.
3b. S139: G5.3 hold PASS 3/3 (RMS <= 0.052 m). G5.7 under leaveP: s1 PASS, s2/s3 FAIL tilt err 5.17-5.25 deg at H->P
   edges (limit 5); thrust step <= 3.1 %; switch-specific (G5.2 leaves ~1 deg). NEXT, max 1 session: fly mode_switch10
   once with PID (MC_RATE_CTL_TYPE 0, MC_INDI_POS_EN 0), compare setpoints after H->P (setpoint re-init vs INDI state
   reset on mode change). Tools: g57_check.py, g57_lag_compare.py. G5.9/G5.11 probes are NOT flown before this closes.
3c. G5.5 probe committed S140 (results/g5_g55_s139/README.md); G5.3 mission PASS 3/3. G5.3 complete as probe.
4. G5.6/5.8/5.9/5.11 injector: OWNER ORDER 2026-11-20 = NEXT SESSION, before more A18/G5.7 work, as its own
   sonnet task (firmware-free, parallel to the A18 code + key). ONE script bench/g5_events.py, ONE multi-event flight,
   one G1.5 verdict line PER event (maybe_landed, kill, EKF reset, RC/link/offboard loss; applied time within 1 physics
   step). Fly the rows after G5.7/A18 close. G5.10 uses G3 hooks. Keep G5.6 1 m / G5.8 offboard-loss variants (owner).
4a. Flying: parallel docker streams ONLY for tolerance-insensitive probes (G5.5, G5.10 sat); G5.7 and event rows serial
   or max 2 streams with sim-hole figure recorded (LESSONS_PROPOSED S86); parallel runs are never gate evidence.
4c. Pre-freeze review, standalone session (not beside flying), split into 2-3 single-interface reviews (stage-3 safety
   diff, stage-5 slice + D-KY, module_parity.md): after the probes close, before the freeze.
4b. Audit DONE S138 (design/defaults_audit_s138.md): no G2 cell at the current pair. Rate roll 800 Hz probe DONE S138 (GM 18.8 dB, PM 56 deg). Next: rate roll
   pitch/400 Hz at freeze; attitude yaw (g2_attbreak_s107 ax3 r800).
   Freeze G2 set must add the firmware-default cell (ID_OK 0, W_MAX 0, ACT_TC 0.05; D-DEFAULTS-FW overturn test)
   or align firmware ACT_TC/W_MAX with bench (G7 lesson 12). Guard params (ERPM_TO/FRZ, SP_TO, DT_MAX) unevidenced.
5. G7 (deferred, stage 7): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site (K128 MAJOR), checker
   self-tests for passthrough_check/offb_vel_check.
Route check next: S143 (RC138 filed, cuts accepted: items 3, 4, 4b).
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
- Deferred anomalies: A-4, A-6, A-30, A-32, A-34-A-36, A-39.
- Stabilized stick centre = HTE; runner thr0 honours HTE valid flag, fallback MPC_THR_HOVER.
- Check script bench/attitude_break_check.py; ratesp_csv.py keyed; run_validity.py (W_MAX check) over cited sets.
- Runner open: MC_INDI_EN 1 in a params file does not start the module, only MC_RATE_CTL_TYPE 1 does (accept
  MC_INDI_EN as alias, keyed). Pilot sticks kept after LAND -> RC override to POSCTL (K118 MINORs). margins_of hangs
  if ts_true=0.
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); firmware ACT_TC 0.05, MC_INDI_ID_OK 0
  halves K.
- Guard: a long inline `git commit -m` is blocked; use `git commit -F <scratch file>`.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| - | none (S141 A18 probe done) | - | results/g5_g55_s141_a18/README.md | run_batch.sh "<rows>" "<seeds>" |
| A142 | injector build g5_events.py (item 4) | sonnet | bench/g5_events.py + G1.5 README | not started: owner order |

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
