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
0e. Pre-freeze reviews r1-r3 dispositioned (S152-S155, D-PREFREEZE-R1..R3). STAGE-6 FREEZE: D-FREEZE-6, firmware
   23acbdef67, bench defaults + ID_OK 1, fwdef cells (G5.1 acro + G2 rate roll 800 at ID_OK 0), G4 typical noise
   (--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0, D-NOISE-PROF). Re-fly: results/g5_freeze_s157 (chain.sh:
   batch.sh 18 + batch2.sh 36 flights, status batch_status.txt, DONE2/CHAIN_END). History: JOURNAL S152-S157.
   S158-S164 (JOURNAL): G5 freeze rows scored + KEYED; G5.11 T10 fix d1b65d0f09 (yaw 2/3 PASS, xy FAIL Q12);
   G2 rate + att + outer 67/67 cells PASS + KEYED at freeze (plateau GM per Q13 A), outer model x-check done (A-50).
   S165: rate + att yaw model x-check DONE (xcheck_rate.md, 12/15 agree, A-51, verdict independent).
   267 Hz reported cells flown S165 (GATES G2 freeze status). NEXT: G4 (RC159 order G2 -> G4 -> G3). Next RC: S168.
   S166-S172 (JOURNAL): G4 tooling keyed; G4 batch results/g4_gate_s169 rows PASS 18/18, chatter FAIL (A-54, Q14),
   item 2 FAIL 1/3 harsh (A-56). D-JFF-SOURCE 20b4a41b22, D-JFF-OFFB aa4fd2654a (FF not the cause). RC173 acted on.
   S173 DONE: G4 verdict written (NOT PASSED: A-56 + Q14 chatter). A-56 probe results/a56_probe_s173: oscillation
   persists with stock mc_pos_control and with accel LPF 4 Hz -> outer loop NOT the cause; inner rate loop remains.
   G2 freeze data at 1.5-3 Hz: no lightly damped mode (design/a56_g2_2hz_s173.md; no PID margins exist).
   NEXT S174: (1) G4 item 2 / A-56: PID clean 3/3 harsh (results/a56_pid_s173) -> INDI rate loop is the cause. One
   rate-loop probe at harsh s3 (candidates: measured/modelled blend, frozen-eRPM path, rate LPF) -> re-open the
   inner-loop decision it names (RC64/74: 1 session per law change). (2) G3 pre-test idx 0-19 FLOWN 20/20 ok (results/g3_pretest_s173,
   README): score with g3_checks.py (per-scenario windows), check draws applied, check scenario mix (17/20 o1). Then fold G5.3/G5.4 re-fly (D-JFF-OFFB overturn
   check) and one offboard trajectory (FF still on in offboard, unverified) into the next chain. Deferred to G7: omega_ff step on offboard entry (key2_jffoffb MINOR,
   resetJerkHistory on rising edge). Dropped: typ/quiet G4 re-flights. Next RC: S178.
   G5.2 posctl z settle s1 4.15 s FAIL (EKF2 height error, Q10; PID ref PASS).
4. G5.6/5.8/5.9/5.11 injector KEYED S144 (results/g5_events_s144/key2.md); G1.5 timing of command/stream-stop
   events and maybe_landed / EKF z injectability -> Q8 (scored at option A, not blocking).
4a. Flying: parallel docker streams ONLY for tolerance-insensitive probes (G5.5, G5.10 sat); G5.7 and event rows serial
   or max 2 streams with sim-hole figure recorded (LESSONS_PROPOSED S86); parallel runs are never gate evidence.
4b. G7: align firmware ACT_TC/W_MAX with bench or keep the fwdef cell (lesson 12). Guard params (ERPM_TO/FRZ, SP_TO,
   DT_MAX) unevidenced.
5. G7 (deferred, stage 7): module harness (D-G7-HARNESS) incl. MC_INDI_ID_OK call site (K128 MAJOR), D-JFF-SOURCE case, checker
   self-tests for passthrough_check/offb_vel_check.
RC149 (design/route_check_149.md) cuts: no more PID G5.10 runs; no 3 m/s 3-seed flying before Q8 add.3(i); runner
  MC_INDI_EN alias deferred to stage 7. Next RC: S159.
Rule (RC64/74): 1 session per inner-loop law change; no anomaly chase unless a gate test fails.
G3/G5 batches before the stage-6 freeze are PROBES (RC113). G3 evidence for INDI outer loop needs MC_INDI_POS_EN=1.
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

## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
