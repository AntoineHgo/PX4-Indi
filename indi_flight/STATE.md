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
0c. G5.5 o1-o4/o7 FAIL recorded (lag chase STOPPED RC143, cause stock PositionControl a_c, base A). Re-fly at
   freeze; if still FAIL, owner Q. G5.8 hover PASS 3/3, G5.9 b/c/d PASS 3/3, G5.9a FAIL = stock commander latency
   (Q8 add. 2). G5.8 3 m/s: 3 seeds once Q8 add. 3 answered. Meanwhile G5.6/G5.11 probes. History: JOURNAL S141-S147.
0d. G5.10 (results/g5_g510_s151): alt 1.74-1.76 m PASS, back ~1.9 s PASS at TB 0.3 (default, f3b93704b6); tilt
   45.3 deg = MPC_TILTMAX_AIR and non-saturating SAT/AGG wait on Q9. A-48 closed (THR_SC injector, UNKEYED).
   G5.4 at TB 0.3 PASS s1. History: JOURNAL S147-S151.
0e. Pre-freeze reviews r1 (S152-S153, F1 BLOCKING fixed, F3/F4 fixed 23acbdef67, D-PREFREEZE-R1), r2 (S154,
   D-PREFREEZE-R2), r3 (S155) all dispositioned. History: JOURNAL S152-S155.
   S155: review 3/3 DONE (design/prefreeze_r3_parity.md): 0 OPEN, 0 SAFETY, 8 PARTIAL MINOR (D-PREFREEZE-R3).
   STAGE-6 FREEZE DEFINED: D-FREEZE-6, firmware 23acbdef67, bench defaults + ID_OK 1 overlay, firmware-default cells
   (G5.1 acro yaw + G2 rate roll 800 at ID_OK 0); re-fly with the G4 typical profile.
   S156: vib hook done, A-49 CLOSED; typical = --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 (D-NOISE-PROF).
   S157: pre-test auto_tour PASS but at ID_OK 0 (defaults file defeats runner overlay = set-up fault, fixed:
   results/g5_freeze_s157/params.params, D-FREEZE-6 note). FREEZE RE-FLY RUNNING detached (chain.sh: batch.sh G5.1-5.4
   18 flights, then batch2.sh G5.5/5.7/5.10/events/fwdef cell 36 flights; status batch_status.txt, CHAIN_END at end).
   S158: batch 1 scored (README table): G5.1 6/6, G5.3 3/3, G5.4 6/6 PASS, G5.2 5/6. o1_lemniscate_s1 FAIL 0.61 m.
   NEXT: if no CHAIN_END and no px4 container running, `setsid nohup bash .../chain.sh &` (resumes). Re-run
   checks.sh after DONE2 (o2/o3 check.txt were taken mid-batch), verdict table, keyed second checker per
   D-FREEZE-6 (g54_key2.py, g5_rows_key2.py exist). Unverified: batch2 o5-o7 args (batch2_notes.md).
   Seed 1: G5.1 acro/stab, G5.2 altctl PASS; G5.2 posctl z settle 4.15 s FAIL (> 4.0): cause
   search DONE: EKF2 height error -0.08 m decaying ~5 s, controller holds estimate (README); Q10 OPEN (not blocking);
   S158: PID reference flight of stick_pos_steps posctl s1 (F-5) for Q10.
1-3. Probes PASS, re-fly at freeze: G5.4 9/9 (S135), G5.1 6/6 K_Y 20 (S137), G5.2 6/6 (S138, g52_check keyed).
3b. G5.3 hold + mission PASS 3/3 (S139-S140). G5.7 PASS 3/3 as probe (S139/S143 matched GNSS, results/g5_g57_s143_gnss).
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
  MC_INDI_EN alias deferred to stage 7. Next RC: S159.
Rule (RC64/74): 1 session per inner-loop law change; no anomaly chase unless a gate test fails.
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
- Guard blocks long `git commit -m`: use `-F <file>`.
- Logger misses the first ~0.2 s of indi_pos_status (late subscription): never read a missing sample as bypass.
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
| S157b | G5 freeze re-fly, 54 flights, detached (batch 1 done+scored S158) | chain.sh (setsid) | results/g5_freeze_s157/batch_status.txt | `setsid nohup bash indi_flight/results/g5_freeze_s157/chain.sh &` (skips done) |
| S158a | Q10 PID ref posctl s1, waits CHAIN_END, serial | pid_ref.sh (setsid) | g5_freeze_s157/stick_pos_steps_s1_posctl_pid, PID_REF_END | `setsid nohup bash indi_flight/results/g5_freeze_s157/pid_ref.sh &` |

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
