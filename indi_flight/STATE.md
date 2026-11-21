# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 5 (outer loop, every mode) opened S129. Stage 4 ident frozen (D-IDENT-STOP, RC126), defaults D-DEFAULTS-FW (S128).
  Stage 3 inner loop time-boxed (RC64/RC74). Stage 1 frozen S36. Started S1 (2026-11-15).
- Gates: G1 PASSED S84 | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open, FINAL text S134 (GATES 5b) |
  G6 open | G7 open | G8 open.
- Blocker: none. Q7 closed S140 (rule A, GATES 5b G5.7). F-7/F-8/F-9 acted on S134 (D-F7-GROUND).
## Next actions (in order; each names its gate item)
History: JOURNAL.md. Agent ledger: LEDGER.md. LESSONS_PROPOSED.md (cost calibrations: read before sizing a brief).
0b. Nominal plant: matched GNSS --gps-dly 110 --gnss-delay 110 (S140 set-up fault fixed). G5.1-G5.4 re-fly at freeze.
0c. G5.5 o1 0.59 / o2 0.79 m FAIL after A18 (S141). S143: lag builds in a_c (lag_chain_s143.md); drag-FF probe
   REJECTED (o1 1.11 m, g5_g55_s143_drag; D-A18-SOURCE outcome). Lag chase STOPPED (RC143): o1-o4/o7 FAIL recorded,
   cause = stock PositionControl feedback producing a_c (D-outer-arch base A). Re-fly at freeze; if still FAIL, owner Q.
   S146 (results/g5_events_s145/README.md, fix_s1-3, key2 AGREES): G5.8 hover PASS 3/3; G5.9 b/c/d PASS 3/3;
   G5.9a FAIL 3/3 = stock commander latency switch->actuator_armed.kill 3.75-10 ms, outputs 0 at the flag (Q8 add. 2).
   G5.8 3 m/s pre-test S146 (results/g5_events_s146_move): entry PASS, excursion metric undefined at 3 m/s and
   link_loss receiver window 2.25 s -> Q8 addendum 3 (not blocking). Key2 B1/M1 FIXED S147 (6b623d589e, fc8a16f58d;
   the 1-line fc8a fix is unflown, self-test OK), re-fly s1 valid (results/g5_events_s147_move): entry 510/1/21 ms PASS,
   excursion FAIL by definition. 3 m/s 3 seeds once Q8 add. 3 (i) answered; meanwhile G5.6/G5.11 probes.
0d. G5.10 probe S147 (results/g5_g510_s147, 0f41810f90): INDI s1 alt 2.15 m FAIL, tilt 48.9 FAIL, back 4.3 s PASS;
   PID 3.22 m/44.7 deg. Q9 open (20 deg unreachable with the row's step; full-scale part). s2/s3: tilt 65 deg
   0.3 s after thrust returns (PID 33), LOC by checker, alt 2.21 m. S148: A-48 CLOSED = injector artefact (8 seq.
   per-motor EC sets); uniform faults now via atomic SIM_GZ_THR_SC (run_scenario.py, UNKEYED). Re-fly s148 s2: tilt
   45.3 deg = MPC_TILTMAX_AIR, no LOC; s1-s3 alt 2.67-2.74 m FAIL (2.0), back 3.3-3.5 s; PID s2 watchdog abort >3 m.
   NEXT: key2 of THR_SC change + g510_check; why alt loss grew vs S147 (2.15-2.21); alt-loss = open G5.10 item
   (1 session cause search, then re-open outer-law saturation handling). Q9 a/b still open. S147 s1-s3 superseded.
   Runner trap: --controller pid_default with a params file holding MC_INDI_EN 1 flies INDI (s148 indi_s2_rep).
1. G5.4 probe PASS 9/9 S135 (g5_probe_s135; auto_smoke_check.py, g54_key2.py). Re-fly at freeze.
2. G5.1 DONE as probe S137: 6/6 PASS at K_Y 20 (acro + stabilized x3). Re-fly at freeze.
3. G5.2 DONE as probe S138: 6/6 PASS altctl/posctl (results/g5_g52_s138, g52_check keyed AGREE). Re-fly at freeze.
3b. G5.3 hold PASS 3/3 (S139). G5.7 leaveP: S139 s2/s3 FAIL (5.17-5.25 deg) were the GNSS set-up fault: S143 matched
   re-fly s2 3.62, s3 3.55 deg PASS, thrust step 3.0 % (results/g5_g57_s143_gnss); s1 PASS S139. G5.7 PASS 3/3 as probe;
   PID compare DROPPED (cause found). Re-fly at freeze. G5.9/G5.11 event probes now unblocked (after item 4 fixes).
3c. G5.5 probe committed S140 (results/g5_g55_s139/README.md); G5.3 mission PASS 3/3. G5.3 complete as probe.
4. G5.6/5.8/5.9/5.11 injector KEYED S144 (fixes fee02b59b2, 3944e8e367; key2 results/g5_events_s144/key2.md):
   all events take effect; applied time from firmware log; command events 1.75-4.25 ms late (G1.5 1.25 ms) and
   stream-stop G1.5 lines FAIL by construction -> Q8 + addendum OPEN (not blocking). maybe_landed / EKF z not
   injectable firmware-free (Q8 b). A-47 closed: G5.8 timeout from firmware time (GATES S144 note). G5.10 uses G3 hooks.
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
Route check next: S149, first action (skipped S148 for budget; RC143 filed: design/route_check_143.md; cuts: 3b G5.7 PID compare deferred behind event rows, 4b/4c/5 stay deferred).
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

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
