# T205 second key: D-ALTCTL-Z z-only stage and T203 integrator-reset gate

Scope: commits de7c598e1e, 52beee60e5, 1d827d62be against DECISIONS.md D-ALTCTL-Z and the T203 minor. Read-only review, no build, no test run.

## Verdict
No BLOCKING. Two MAJOR-level gaps are about test coverage (module-level T203 gate and z_only flag derivation untested; library tests miss state continuity at tilt). Code is correct as read.

## (a) z-only output, signs, limits, state: OK
- indi_accel_control.cpp:358-361: t_c = n_dir * (t_c(2)/n_dir(2)). n_dir(2) <= -0.1 (guard at :243-252) and t_c(2) <= -kMinUpThrust (floor at :351-356), so the scale is positive, t_c(2) is preserved exactly, NED sign correct, no divide by ~0, no NaN (n_norm finite and > eps, t_c finite checked at :346).
- c_max branch (:376-380) scales the whole vector (direction fixed, vertical component shrinks with it): acceptable, matches "limits as usual". c_min branch (:395-400) is shared and scales the whole vector. The vertical floor uses c_min on the z component, so |t_c| >= c_min/|n_z| >= c_min before the min branch: consistent.
- _thrust_prev = thrust = |t_c|/(g_t k_cmd) (:437-438), i.e. the collective norm, the same quantity as the vector the module publishes (thr_vec = t_c_applied/G, McIndiPosControl.cpp ~:290). Blend model path (u_model from _thrust_prev) and measured path (ESC mean u, a collective too) are consistent with the vector output. coll_clamped uses the same clamps.
- MINOR a1 (note, no change): t_f uses the measured z_b, the command uses the stock n_z, so while attitude lags a tilt step the collective is c = t_f_z/n_z (+6 % for a 20 deg step). That is the stock tilt compensation and the fixed point (z_b = n) has no bias. Worth knowing when reading a G5 log, not a defect.
- MINOR a2: output-injection path (MC_INDI_PINJ_PT = 1, McIndiPosControl.cpp t_c_applied += inject) adds an xy term to a z-only vector and tilts it away from the stock direction, and setAppliedThrust receives that norm. Bench-only; fix: skip xy injection when in.z_only (or document).

## (b) zero or near-horizontal stock thrust: OK
- Guard at indi_accel_control.cpp:243-252 returns false before any state is touched (before filters, jerk difference, blend, _thrust_prev), so the module falls to the bypass branch (publishes stock att_sp, reset() keeps the blend, _indi_active = false). No NaN reaches the publication (library returns false on non-finite; module only publishes inside if (_indi.update)).
- The test list covers NaN, zero, horizontal, downward, 0.05 ratio.
- Consequence (see e): in that bypass cycle the stock integrator was already zeroed.

## (c) POSCTL <-> ALTCTL switch inside the active stage: no discontinuity found
- Only z_only changes; filters (_lpf_f, _lpf_u, _lpf_um), _thrust_prev, _b, _j_diff_f are the same objects and are all fed identically in both paths (collective norm, measured f_b, mean u, a_ref).
- a_ref xy is stock in both modes. The jerk difference sees a step in a_ref xy at the switch, but omega_ff is zero in z-only and the first 3-axis cycle uses j from the filtered difference (same behaviour as any a_ref step in POSCTL).
- Thrust vector at the switch: ALTCTL->POSCTL, xy part goes from stock stick tilt to t_f + (a_c - a_f) with measured t_f, so it starts from the measured state (INDI increment form): no step beyond the stock setpoint step. POSCTL->ALTCTL, direction becomes stock; the stock setpoint itself is what changes. Collective is continuous (norm in both).
- MINOR c1: the three-axis path applies the library tilt limit (_tilt_max), the z-only path relies on the stock tilt limit. Stock limitTilt does apply, so equal, but confirm MPC_TILTMAX_AIR == tilt_limit_rad given to setLimits (it is the slewed value there; the stock path uses setTiltLimit with the same slewed value, Run ~:766). OK.
- MINOR c2 (scope): z_only = !(position || velocity) and want_indi now includes climb_rate. NAVIGATION_STATE_DESCEND (control_mode.cpp:100-106, climb_rate only, mc position control enabled by Commander.cpp:2826), ALTITUDE_CRUISE and any external mode with only climb rate also get the z-only stage. D-ALTCTL-Z names ALTCTL only. Failsafe descend is a safety-relevant mode. Fix: state in the decision that DESCEND is included (functionally desirable: gap compensation in failsafe descent) or restrict with flag_control_manual_enabled; either way add it to the G5 list.

## (d) stock direction read before overwrite: OK
in.thrust_dir is built from local_pos_sp.thrust at McIndiPosControl.cpp (in the can_run block, before IndiAccelControl::update), and local_pos_sp.thrust is overwritten only after update succeeds. local_pos_sp is re-created each cycle from _control, so no feedback of the INDI vector into the next cycle's direction. In altitude mode the stock thrust comes from _thr_sp = body_z * collective, body_z set by the stick acceleration and tilt-limited, so its direction is the stick tilt (PositionControl.cpp _accelerationControl). With coupled z (MPC_ACC_DECOUPLE = 0) the stock tilt also depends on acc_sp z; still the stock direction, as intended.

## (e) T203 gate
- Poll order: pollStageInputs() then stageInputsFresh(now) before the update (Run ~:837-846); runIndiStage polls again. Correct.
- Freshness: stageInputsFresh uses the same age lambda, kStageMaxAge = kMaxAge (20 ms), same non-zero stamp test as fresh_att/fresh_acc in can_run. Identical definition.
- MINOR e1 (race): if a sample arrives between the pre-poll and the in-stage poll, the pre-gate says stale (no reset, a_ref carries the stock integral) while the stage then runs on the new sample. One cycle with the integral in a_ref; the post-stage resetIntegral clears it. Fix if wanted: remove the second poll in runIndiStage (the first one is enough) so both use the same snapshot.
- MINOR e2 (integrator zeroed, stage does not run), fresh inputs and want_indi true but can_run or the library false:
  - a_c non-finite: stock update() already returns false in that case (needs _acc_sp finite), failsafe path; irrelevant.
  - rate <= 5: unreachable, dt is constrained to [0.002, 0.04] (Run :614), rate in [25, 500]. The library dt check (kMinDt/kMaxDt) is also unreachable.
  - library false for non-finite f_b / q (NaN from a sensor with a fresh timestamp), q norm < 0.5, t_c non-finite, invalid z-only thrust_dir: the integrator is zeroed every cycle and the bypass thrust has no gap compensation. Rare faults; the pre-gate could also require _f_b and _q finite and |q| >= 0.5 (two lines), the thrust_dir case cannot be known before update. Worth the two lines because it is the same class as the T203 fault.
- The first-cycle case where inputs go stale in the middle of the cycle is not a problem.

## (f) Tests: do they fail on breakage?
Library tests (IndiAccelControlTest.cpp, IndiAccelZOnlyTest) are good for direction, vertical match, omega_ff, limits, invalid input. Mutations they would NOT catch:
1. OutputParallelToThrustDir / CollectiveLimits: _thrust_prev set from |t_c(2)| instead of |t_c| (state inconsistent at tilt): no test runs two cycles at a tilted direction; the closed loop test uses a level direction (tilt 0, cos = 1), so any cos factor error (t_c(2)/n_z replaced by t_c(2)) in the stored state or the model path is invisible. MAJOR (coverage): add a tilted closed loop (thrust_dir tilted 30 deg, plant vertical a = g_t u cos(tilt) - g with thrust model scale) and assert convergence plus out.thrust == |t_c|/g_t.
2. InvalidThrustDirReturnsFalse: only checks out.thrust and return. Moving the guard after the filter/blend/_thrust_prev update would still pass (state-before-validation contract, 9. required inputs). Add: call with invalid dir, then valid, compare against a fresh controller.
3. Guard thresholds: replacing 0.1f by 0.06f or deleting the n_norm < FLT_EPSILON test passes (bad list has 0.05 ratio and the zero vector is already caught by the z test).
4. No test of the vertical floor in z-only (t_c(2) > -kMinUpThrust, a_ref z large positive) nor the c_min branch with z_only: removing the floor or mis-signing it passes.
5. VerticalComponentMatchesThreeAxis uses an a_ref where the 3-axis path is not tilt/collective limited; a mutation that makes z-only apply the 3-axis tilt limit on t_c(2) passes (no effect on z).
6. Module level: no test at all for McIndiPosControl (no test file in the module; IndiPosInjectionTest only). T203: removing the stageInputsFresh gate, or using a different age constant, passes everything. z_only derivation (z_only = !(pos || vel)), want_indi with climb_rate, and the read of thrust_dir before overwrite are untested. MAJOR (coverage): the gate and flags are small pure conditions; extract them to a static function (inputs: flags, ages) and unit test, or accept SITL evidence (T204) as the test and record that as the decision.
