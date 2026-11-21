# Offboard pos/vel feedback in the INDI module (G5.5, Q11 B) - design note DRAFT S176

## 1. Today's path and the measured failure
- OFFBOARD uses the stock cascade inside the module: `_control.setInputSetpoint(_setpoint)` and `_control.update(dt)`
  (McIndiPosControl.cpp:1016, ~1055) compute a_sp = a_ff + K_v(v_sp - v) - K_d*vdot, v_sp = K_p(p_sp - p) + v_ff, with
  the MPC_XY_P / MPC_XY_VEL_P_ACC / MPC_*_VEL_D_ACC gains (:599-603). `getLocalPositionSetpoint` (:1083) hands that
  sum to runIndiStage as `a_c_pre_inject` (:198); the library runs `accel_only = true` (:297): a_c = a_ref, so INDI
  only closes the acceleration loop. Library p/v terms (indi_accel_control.cpp:284-321) exist but are unused here.
- Jerk FF: library difference of a_ff (`in.a_ff = _a_ff`, :316, :1090 = raw `_setpoint.acceleration`), omega_ff only in
  offboard (`setFeedforward(offboard)`, :323; D-JFF-SOURCE, D-JFF-OFFB). MAVLink offboard has no jerk field.
- G5.5 result (results/g5_freeze_s157/README.md; JOURNAL Q11): o1-o4/o7 horizontal RMS 0.57-0.81 m (3 seeds, limit
  0.5); vertical, o5/o6, offb_vel_step pass. PID o1 at the freeze plant 0.785 m. Cause as recorded (D-A18-SOURCE,
  results/g5_g55_s141_a18/lag_chain_s143.md): a_c lags the analytic acceleration ~100 ms (setpoint arrives in 3 ms,
  attitude+thrust+plant add 20-40 ms). The truth carries a drag term (a = 1.015 tilt_acc - 0.514 v) that a_ff lacks,
  so the feedback carries it. A drag FF probe made o1 worse (0.59 -> 1.11 m, overshoot).

## 2. Proposed change (OFFBOARD only, flight state only)
  a_c = a_ff + K_v (v_ref - v),  v_ref = v_sp + K_p (p_sp - p)   (library cascade, no D term, no integrator)
- Gains: reuse MPC_XY_P / MPC_Z_P and MPC_*_VEL_P_ACC, passed to `IndiAccelControl::setGains` (never called today;
  library defaults 0.95/1.8 xy, 1/4 z equal the MPC defaults). Zero new params: one tuning surface, same as base A.
  Honest caveat: this is the stock law minus the D term, so the gain over 0.5 m is NOT established by design; it
  comes from removing D (-K_d*vdot, phase lag) and the stock shaping, and from the gains being ours to raise. If the
  pre-test (sec. 5) misses, add MC_INDI_OFB_KP/KV (2 params) and raise them; e ~ drag residual / |K_v K_p - w^2 + j w K_v|.
- Limits: library v_sp limits (setLimits, :188), tilt limit and vertical priority as for every mode; unchanged.
- Valid fields (per axis; the stock validity decision `_control.update` still gates and keeps failsafe fallback):
  pos+vel+acc full law; pos only: v_ref = K_p e; vel only: v_ref = v_sp; accel only: a_c = a_ff, NO velocity term.
  NEW in the library: today NaN p_ref and v_ref give v_ref = 0, i.e. damping toward zero velocity on an accel-only
  axis (the stock cascade skips the term). Add a per-axis feedback mask (finite p_ref or v_ref).
- Reused: library cascade, jerk difference, limits, tilt, injection point, stock `_control` for validity/failsafe/thrust
  limits. New (est. ~60 LOC firmware + ~100 LOC tests): module ~40 (offboard && takeoff state >= flight && not on the
  failsafe fallback: pass in.p, in.v, p_ref/v_ref/a_ref from `_setpoint`, accel_only = false; inject added to a_ref so
  PT 0 still breaks the loop after the feedback; status a_c_pre_inject = a_c - inject; setGains call), library ~12
  (mask), helper `useOwnFeedback()` pure function in a header (pattern of IndiStageMode.hpp) for the unit test.

## 3. Interactions
- Entry/exit: a_ff jumps at offboard entry (stock held a_ff -> external setpoint) and omega_ff steps (key2_jffoffb
  MINOR). Call `_indi.resetJerkHistory()` on the offboard rising edge (3 LOC, existing T10 mechanism). Setpoint
  reset on entry stays stock (:222-234, `_indi_reset_pending`). Takeoff ramp and failsafe setpoint keep today's path.
- Estimator resets: `adjustSetpointForEKFResets` (:871) shifts the setpoint into the new frame; p, v come from the
  same states, so p_sp - p is consistent; `_indi_jerk_reset_pending` (:882) still applies.
- Other modes: AUTO/manual unchanged (branch on flag_control_offboard_enabled; D-JFF-OFFB already splits there).
  mc_pos_control, control_allocator, commander stay at zero diff (O-11).

## 4. Alternatives
- Raise stock gains only (no code): shortens the lag, no structural change; owner chose design change. Overturn if
  the offline check (sec. 5) shows gains alone reach 0.5 m with margins kept.
- Drag FF (D-A18-SOURCE): probed, worse (1.11 m); rejected on data.
- Higher-order/predictive FF (differentiate a_ff twice): needs jerk-level data MAVLink lacks; more code (F-9).
- Overturn the choice if: offline check says D term is <10 % of the a_c lag; or pre-test RMS > 0.5 m at 2x gains.

## 5. Tests and re-fly
- Unit (fail when broken): library test: (a) accel-only axis, v != 0 -> a_c = a_ff (fails without the mask); (b) pos-only,
  vel-only, full; (c) double-integrator closed loop on a sinusoid, lag < 50 ms; module helper: offboard x flight x
  failsafe truth table; resetJerkHistory on entry gives omega_ff 0 on the first cycle after a_ff step.
- Offline first (0 flights): from freeze o1 logs compute the D-term share of a_c and the predicted lag without it.
- G5.5 pre-test: o1_lemniscate seed 1, freeze plant (--gps-dly 110 --gnss-delay 110): pass 0.5 m horizontal RMS.
- Offboard evidence needing a re-fly at freeze-7 (every bench scenario starts as an offboard position hold):
  G2 outer (results/g2_outer_freeze_s163, 26 runs hover_long/hover_xlong; PT 0 cells measure the loop that changes;
  PT 1 output-break cells expected unchanged, re-fly cheap subset to confirm); G2 attitude/rate cells (g2_freeze_s160, 35
  runs hover_long): outer loop outside the break, spot-check 2; G4 (g4_gate_s169, 20 runs: 10 traj_lemniscate cruise
  incl. 1 pid, 10 hover_long incl. 1 pid) all re-flown per D-JFF-KEEP; G5.5 o1-o7 + offb_vel_step.

## Draft DECISIONS entry
## D-OFFB-POSVEL (S176, 2026-11-21): offboard trajectories use the INDI module's own pos/vel feedback (G5.5, Q11 B)
- Fact: G5.5 o1-o4/o7 FAIL 0.57-0.81 m (limit 0.5) for both stacks; a_c from the stock cascade lags the analytic
  acceleration ~100 ms (D-A18-SOURCE, results/g5_g55_s141_a18/lag_chain_s143.md). Owner Q11 B / GATES amendments S175.
- Choice: in OFFBOARD at flight state the library computes a_c = a_ff + K_v (v_ref - v), v_ref = v_sp + K_p (p_sp - p),
  gains MPC_XY_P / MPC_Z_P / MPC_*_VEL_P_ACC (no new param), no D term, per-axis NaN mask, jerk FF as D-JFF-KEEP.
  Stock `_control` stays for validity and failsafe; other modes unchanged; ~60 LOC firmware, ~100 LOC tests.
- Alternatives: stock gains raised (no structural gain); drag FF (probed worse, D-A18-SOURCE); own offboard params
  (kept as fallback if the pre-test misses); change the limit (owner: unchanged).
- Reason: smallest change that moves the feedback law into the stage that already has the library cascade (F-9),
  keeps O-11, removes the stock D-term lag, gives gains we can tune per mode.
- Checks: unit tests of sec. 5; o1 s1 pre-test <= 0.5 m; then G5.5 x3 seeds, G2 outer PT 0 cells, G4 at freeze-7.
- Overturn: offline D-share < 10 % of the lag, or pre-test > 0.5 m at 2x gains (then the 100 ms is plant/drag, and
  the owner is asked about the limit again).

## Orchestrator note (S176)
Steady error on the lemniscate ~ drag/|K_v K_p - w^2 + j w K_v|: with MPC defaults (K_v K_p = 1.71) and drag ~1.5 m/s2
this is ~0.9 m, the measured order (0.57-0.81). Removing D changes little; the lever is the pos/vel bandwidth the fast
INDI acceleration loop allows (K_p 1.9 / K_v 3.6 predicts ~0.25 m). In the INDI configuration the MPC_* gains are read
only by the INDI module (mc_pos_control not running). Before code: one HEAD probe o1 s1 with MPC_XY_P and
MPC_XY_VEL_P_ACC x2 (results/g55_gain_probe_s176). Open for the review: the INDI accel loop should reject drag itself
(accelerometer sees aero force), so why does a_c carry it - is the 100 ms the accel-loop filter lag (then it bounds
the gains)?
