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
   G5.8 3 m/s (results/g5_events_s147_move, key2 fixes S147): s1 entry PASS, excursion undefined -> Q8 add. 3;
   3 seeds once answered; meanwhile G5.6/G5.11 probes.
0d. G5.10 probe S147 (results/g5_g510_s147, 0f41810f90): INDI s1 alt 2.15 m FAIL, tilt 48.9 FAIL, back 4.3 s PASS;
   PID 3.22 m/44.7 deg. Q9 open (20 deg unreachable with the row's step; full-scale part). s2/s3: tilt 65 deg
   0.3 s after thrust returns (PID 33), LOC by checker, alt 2.21 m. S148: A-48 CLOSED = injector artefact (8 seq.
   per-motor EC sets); uniform faults now via atomic SIM_GZ_THR_SC (run_scenario.py, UNKEYED). Re-fly s148 s2: tilt
   45.3 deg = MPC_TILTMAX_AIR, no LOC; s1-s3 alt 2.67-2.74 m FAIL (2.0), back 3.3-3.5 s; PID s2 watchdog abort >3 m.
   S149 split: SAT part never saturates (cmd max 0.71) -> Q9 note 2. S150 CAUSE (D-GAP-G510): THR_SC scales omega;
   blend b (TB 1.0, clamp kMaxBlend 0.3 < gap 0.36) too slow. Probe TB 0.3 s1 (results/g5_g510_s150): 1.95 m, back
   1.44 s, b still clamped. kMaxBlend 0.5 DONE S150 (003e25c6d4, key2 MINOR); probe s1 TB 0.3+0.5: 1.77 m, back 1.87 s
   (README_b05.md). S151: margin at TB 0.3 PM 62.7/67.3 deg (g2_outer_tb03_s151); 3 seeds alt 1.74-1.76 m PASS,
   back ~1.9 s PASS (g5_g510_s151); TB default -> 0.3 (D-GAP-G510 ACCEPTED). Row waits on Q9 (tilt, AGG, (c)).
1-3. Probes PASS, re-fly at freeze: G5.4 9/9 (S135), G5.1 6/6 K_Y 20 (S137), G5.2 6/6 (S138, g52_check keyed).
3b. G5.3 hold PASS 3/3 (S139). G5.7 leaveP: S139 s2/s3 FAIL (5.17-5.25 deg) were the GNSS set-up fault: S143 matched
   re-fly s2 3.62, s3 3.55 deg PASS, thrust step 3.0 % (results/g5_g57_s143_gnss); s1 PASS S139. G5.7 PASS 3/3 as probe;
   Re-fly at freeze.
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
RC149 (design/route_check_149.md) cuts: no more PID G5.10 runs; no 3 m/s 3-seed flying before Q8 add.3(i); runner
  MC_INDI_EN alias deferred to stage 7. Next RC: S154.
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
- Runner traps: pid_default + params with MC_INDI_EN 1 flies INDI (s148). MC_INDI_EN 1 in a params file does not start the module, only MC_RATE_CTL_TYPE 1 does (accept
  MC_INDI_EN as alias, keyed). Pilot sticks kept after LAND -> RC override to POSCTL (K118 MINORs). margins_of hangs
  if ts_true=0.
- quad5in defaults: bench/params/quad5in_indi_defaults.params (ACT_TC 0.033); firmware ACT_TC 0.05, MC_INDI_ID_OK 0
  halves K.
- Guard: long inline `git commit -m` blocked; use `git commit -F <file>`.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S151 | key2 of MC_INDI_POS_TB default 1.0->0.3 (uncommitted yaml + bench defaults) | sonnet | results/g5_g510_s151/key2_tb_default.md | re-brief from D-GAP-G510 |

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
