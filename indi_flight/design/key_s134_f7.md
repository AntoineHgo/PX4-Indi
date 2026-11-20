# Key review S134 F-7 (code vs D-F7-GROUND). Paths relative to src/.

## BLOCKING
none

## MAJOR
- modules/mc_indi_pos_control/McIndiPosControl.cpp:~191 (`_indi.setLimits(..., _param_mpc_thr_min)`) with lib/indi_accel_control/indi_accel_control.cpp:~330 (`c < c_min` clamp, `t_c(2) = -max(c_min,kMinUpThrust)`):
  the INDI floor is MPC_THR_MIN on the ground and in rampup. Stock used minimum_thrust = 0 when not flying (Run(): `minimum_thrust = flying ? thr_min : 0`).
  Result: +100 m/s^2 gives a finite, non-NaN collective of MPC_THR_MIN (not zero), and the rampup collective starts at MPC_THR_MIN, not "rising from 0" (D-F7-GROUND text). Props spin at thr_min armed on ground.
  Pass thr_min = 0 to setLimits while takeoff state < flight (or model_force); c_min = 0 is handled (kMinUpThrust still keeps t_c finite).
- McIndiPosControl.cpp:531 / lib indi_accel_control.cpp:~109,~134 (`reset()` "A16: b is held, never reset"): gap-remover blend `_b` is never cleared on disarm/re-arm
  (only when tb <= 0). Same for `_acc_stale_latched`, `_held_valid`/held setpoint, `_last_thrust`, `_filter_hz`. A b learned in the previous flight is the first
  u_f = u_meas + b of the next arm. Also, with the stage gated on position-control flags, the Bypass reset may not run while disarmed. Add an explicit disarm-edge reset
  (b = 0, held_valid = false, reset()) next to `_injection.reset()` at ~742.

## MINOR
- McIndiPosControl.cpp:~1005 ground tilt: on ground t_c xy = stock xy a_ref (P on velocity noise, setpoint NAN -> 0) while |t_c,z| = c_min = G*thr_min; tilt is angle based
  (h_max = |z| tan(tilt_max_lnd)), so a floor of thr_min allows up to tilt_max_lnd of attitude command on the ground; stock at thrust 0 gave no tilt. Disappears if the floor is 0 only partly
  (kMinUpThrust = 0.1 still allows h_max = 0.1*tan). Consider zeroing xy a_ref (or tilt limit 0) while takeoff state < rampup.
- McIndiPosControl.cpp:~955,~1010: stock integrator still integrates one step inside PositionControl::update (PositionControl.cpp:204) and setHoverThrust(ht) can shift _vel_int (PositionControl.cpp:88);
  the pre-update resetIntegral() zeroes it before use, so it is never in a_ref (OK) and is zeroed again after the stage when `_indi_active`. Verified, no action.
- McIndiPosControl.cpp:~243 reset-pending path during model_force passes `fresh_acc ? _f_b` (measured, with ground reaction) to `_indi.reset` -> filter seed holds ground reaction; use modelled f when model_force.
- IndiStageModeTest.cpp: no test of the lib on the ground path (blend frozen, +100 setpoint). Add an IndiAccelControlTest for a_ref z = +100, f_b_valid = false.

## Checked OK
1. want_indi = armed && (pos||vel||climb), any takeoff state; Bypass (stock thrust) only when !want. Stock integrator reset before update and after stage. Hold also sets `_indi_active`.
2. model_force -> selectStageMode IndiModelAccel -> in.f_b_valid = false, mean_u_valid = false -> lib `u_valid` false -> `blend_frozen` true (b not updated); blend_hold also set via model_acc. The measured f_b is not used (f_in = modelled). Hold mode (att stale) runs no update.
3. +100 down: t_c,z = 100 - g > -kMinUpThrust -> clamped to -max(c_min,0.1); c > 0 so body_z_d = -t_c/c finite, no NaN. (Floor value: see MAJOR 1.)
5. Removed HandoverBlend / HoverThrustSync / _control_ht: no remaining references in src, msg, docs/en. Handover loss: the first stage cycle no longer continues the bypass a_ref, only relevant at disarmed -> armed (stock +100 setpoint), so no step. trackDegraded masking via model_force is intended.
6. git diff is empty for mc_pos_control, mc_rate_control, mc_att_control, control_allocator, commander.
