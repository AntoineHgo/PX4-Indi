# STATE (budget 8000 bytes: read at every launch, resume essentials only)

## Status
- Stage: 5 (outer loop, every mode) opened S129. Stage 4 ident frozen (D-IDENT-STOP, RC126), defaults D-DEFAULTS-FW (S128).
  Stage 3 inner loop time-boxed (RC64/RC74). Stage 1 frozen S36. Started S1 (2026-11-15).
- Gates: G1 PASSED S84 | G2 open (cell table in GATES.md) | G3 open | G4 open | G5 open | G6 open | G7 open | G8 open.
- Blocker: none. No open question. Outer-loop architecture = base A (`design/flatness_r2.md`: flatness = optional increment).
## Next actions (in order)
History: JOURNAL.md. Agent ledger: LEDGER.md. LESSONS_PROPOSED.md (cost calibrations: read before sizing a brief).
Route checks in design/; next: S134 (due now) (RC129 filed, ACCEPTED).
RC129 plan: S130 = T1-T6 of design/g5_build_list.md (start with F-1 fallback removal: McIndiPosControl.cpp:287-295
  bypass and rc.mc_apps:59 `||`), AUTO modes; S131 OFFBOARD, pass-through modes, first G5 probe. Owner question at the
  end of S131 if there is no multi-mode code. Write the G5 section of GATES.md before the first G5 test.
G5 build gaps (S129 list): hover-thrust shift not ported (T9); no module tests. Estimator reset done S131.
POSCTL smoke S129 open: 2 m alt excursion 36-52 s (unanalysed). Runner NAV_LAND: not a defect (S131).
Rule (RC64/RC74): 1 session per inner-loop law change; no new anomaly chase unless a gate test fails.
G3/G5 batches before the stage-6 freeze are PROBES (RC113), not gate evidence. G3 evidence for the INDI outer loop
  needs MC_INDI_POS_EN=1 in the base params (S118 probes ran stock mc_pos_control).
Offline G2 todo before stage 6: outer-cell margin key, linear outer-loop model, A-36/A-39 bound, 267 Hz rows
  (verdict design/g2_verdict_s108.md).
G3 tooling exists (g3_run.py, quad5in variants, overrides/wind/motor_fault/timed eRPM loss). gust_x results before
  b0486b703e not comparable. eRPM-loss lateness 36-122 ms: take effective time from the log. Weak+sat unflown.
  Acro = G3-unprobed, G5 carries it (RC118). altctl/posctl not in G3 MODE_MIX.
DEFERRED until defaults exist: g3_checks.py, gate_g3.sh, frozen-telemetry hook, G4 profiles.
Deferred to before G6: yaw fit fix (r regressor + matched grid = probe V3, K126 MAJORs, A-44).
STOP list: A-39 / yaw measured-path chase, more G2 cells at the preliminary pair, PID M1 hook, hooks without a
  consumer, stand-alone anomaly chases (fold A-4, A-6 into G3/G5 side-cells), --sched-anchor and set_param fixes.
Later: combined opus review of stage-3 safety diff + stage-5 slice before any freeze. Log a z-only active flag in
  indi_pos_status when next touching the module.
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
## Tasks in flight
| id | task | agent | output | resume |
|---|---|---|---|---|
S130 DONE (0adaaa490f, keyed K130 + K130b, 0 BLOCKING): D-STAGE-STALE in firmware, rc.mc_apps `||` removed = build list
  T1 + F-1 gap. Open from keys (S131): K130b MAJOR step test too weak (tighten, assert transient); no test of
  valid->invalid->valid switch nor of runIndiStage (Hold on update false, no stock thrust) -> stage-7 harness or
  TestPeer; entry transient of f_b filter history unquantified; mode (a) never flown (no stale-accel hook);
  astyle run on all INDI module/lib files S132 (one fix committed). Smoke S130 (before lib fix): stage_mode 1 throughout, hover = S128; POSCTL
  z std 0.114 vs 0.050 m (1 seed; re-fly once in S131 with T2-T6 smokes); NAV_LAND 16 s early in S128-S130 = runner.
S131 AUTO smoke (166bb5a258, probe, 1 seed): auto_tour + auto_land10 fly with INDI pos, stage_mode 1, land vz 0.71 vs
  0.70, disarm 2.7 s, mission xy 0.49 m RMS. Handover: vehicle_thrust_setpoint step 0.035 = 25 % of hover 0.137 >
  PROPOSED 10 % (dip 0 m); indi_pos_status has no sample before the edge (log it in bypass). S130 "NAV_LAND early" =
  README time-base error (window is 55-85 s), not runner. PID ref (results/auto_smoke_s131_pid): step 0.0075, land
  same -> handover step is INDI-specific = A-45 (fix first in S132: align checker 50 ms -> 0.1 s, log indi_pos_status
  in bypass, find first-cycle collective cause; 1 session max per RC64 rule).
S132 A-45 CLOSED (D-HANDOVER, HandoverBlend tau 0.5 s, keyed K132): handover step 0.035 -> <=0.0067 (3 seeds,
  results/auto_smoke_s132). K132 MINORs open: caller wiring untested (stage-7 harness); status.a_c_pre_inject logs
  the stock value without the offset (ident windows within 2 s of a handover). Logger misses the first ~0.2 s of
  indi_pos_status (late subscription): never read a missing sample as bypass.
S133 = T7-T12 (OFFBOARD rows, pass-through modes, T9 hover-thrust port, first G5 probe, T12 owner Q).
S133 T9 DONE 7770538b55 (syncHoverThrust: updateHoverThrust on ht change, bypass only; gtest break-checked, 152/152;
  key folded into the pre-freeze combined opus review). A133 (a95f3121a5, notes design/impl_s133_offboard_passthrough.md,
  results/s133_passthrough): ACRO pass (no IPC output while PC flags off; method = flag-gated sample count, no
  publisher id), offboard vel-only pass (vx step RMS 0.62, last 3 s 0.092 m/s, z 0.04 m). T9 SITL: flight-edge step
  1.0 % (vel) / 6.1 % (acro) of hover = A-46 (fold into T11). Not flown: accel-only offboard (runner send_pva always
  has position), takeoff on offboard setpoint alone, MANUAL/STABILIZED. New checkers have no self-test yet.
  T12: no owner question (T12a done S130; board enable = G7). S134 = route check (due), G5 section of GATES.md,
  then T11 first G5 probe incl. A-46 3-seed check and the unflown rows above.
S131 done: A131 sonnet runner AUTO harness T2/T3/T4/T6 -> design/impl_s131_auto_harness.md; B131 sonnet
  firmware T5 failsafe pure fn + T10 reset reaction DONE 3d6066de89 (gtests pass, reset reaction unflown, module-side
  call untested); K131 key 0 BLOCKING/MAJOR (MINORs: reset collective from measured thrust = small step, wiring
  untested -> stage-7 harness; G5.11 probe measures the step).
## Open problems
- Deferred to stage 7 (RC98): module harness (D-G7-HARNESS; must cover the MC_INDI_ID_OK call site, K128 MAJOR),
  MINORs frozen-b on saturated motor, lagging mean_u at reset, lower mean_u limit untested, DESCEND failsafe tests.
- Review notes (`indi_project/review/external_review_s59_notes/`): open per item: `module_parity.md` for stage 5.
- Unmodelled in margins_models.py (T78 list): gz/ESC latency 0, measured path = eta x motor state, yaw, attitude
  loop; 267 Hz analytic only.
