# A-9 second key (T146, S68): can yaw rate be counted twice in the roll/pitch rate setpoint?

Written before reading a9_new_module_s67.md.

## Paths by which yaw rate reaches the roll/pitch body-rate setpoint (current code)
1. Single path, stock mc_att_control: AttitudeControl.cpp:105 `_omega_command = yaw_axis_body * yawspeed_setpoint`
   (world yaw axis expressed in q_ref body frame), added at AttitudeControl.cpp:197
   `rate_setpoint += q_rel.rotateVector(_omega_command)`. When tilted this projects onto body x/y, which is the wanted
   coordinated-turn roll/pitch rate. Unity gain, bypasses the reference model gain/limit.
2. AttitudeControl.cpp:200-208 has a local `omega_ff` (= _ff_gain * rotated _omega_correction of the reference model). Same name,
   unrelated to IndiAccelControl::Output::omega_ff, and it is the model-error term, not the commanded yaw rate.

## IndiAccelControl::Output::omega_ff
indi_accel_control.cpp:336-337: omega_ff(0) = clamp(j_used.y_b / c), omega_ff(1) = clamp(-j_used.x_b / c), z = 0 (cpp:330,
hpp:46,105). Inputs: j_used (jerk), c (collective), R_d from q_d. yawspeed_ref is NOT used there: it is only copied to
out.yawspeed_ff at cpp:348. x_b, y_b depend on yaw_ref (heading), not on its rate. So no psi_dot*(e3.x_b, e3.y_b) term.
(A jerk of a real circle with yaw locked does produce body-rate content through j, but that is the path-curvature rate, a
function of the reference jerk, not a second addition of psi_dot; it is only an issue if something consumes it.)

## Consumers of omega_ff / yawspeed_ff
grep src/: only indi_accel_control.{cpp,hpp}, IndiAccelControlTest.cpp, and the unrelated local in AttitudeControl.cpp.
mc_indi_pos_control (McIndiPosControl.cpp:~175-200) runs the lib with accel_only=true, passes yaw_ref = yaw from att_sp.q_d,
and only uses out.t_c and out.thrust (thrustToAttitude(thr_vec, yaw_sp, att_sp), local_pos_sp.thrust). It does not read
omega_ff, yawspeed_ff, and sets no yaw_sp_move_rate or rates setpoint; the stock att_sp.yaw_sp_move_rate passes through
untouched and reaches AttitudeControl (path 1). mc_indi_rate_control does not reference them either.

## Verdict
Double count NOT possible in the current stack: yaw rate enters the roll/pitch rate setpoint only via AttitudeControl:105/197,
and omega_ff is neither yaw-rate dependent nor consumed. It would become possible only if a future consumer adds
Output.omega_ff to the rate setpoint AND omega_ff gained a yaw term (or the jerk-ff of a yawing reference duplicated it).

## Guard test
IndiAccelControlTest.OmegaFfIndependentOfYawRate in src/lib/indi_accel_control/IndiAccelControlTest.cpp: tilt 0/15/30 deg,
a_ref=(g tan(tilt),0,0), j_ref=(0.4,0.7,0), yawspeed_ref 0 vs 1 rad/s, asserts omega_ff x/y equal to 1e-6 and non-vacuous
(norm > 0.01). Run in Docker (build/px4_sitl_test, target unit-IndiAccelControl): 21/21 PASS.

## Break-check (NOT run; lib must not be modified while the flight batch builds)
File src/lib/indi_accel_control/indi_accel_control.cpp, after line 337 (inside the `if (_jerk_ff ...)` block) add:
    omega_ff(1) += in.yawspeed_ref * x_b(2);
Expected: new test fails at tilt 15 and 30 (x_b(2) = -sin(tilt) for a_ref along +x; at tilt 0 x_b(2)=0 so it passes there; y_b(2) would be 0 for this tilt axis, so do not use it). Revert with
`git checkout src/lib/indi_accel_control/indi_accel_control.cpp`. Rebuild: in Docker
`cd build/px4_sitl_test && ninja unit-IndiAccelControl && ./unit-IndiAccelControl`.

## Comparison with a9_new_module_s67.md (first key)
- Path 1 (module publishes q_d/thrust, yaw_sp_move_rate stock passthrough): AGREE.
- Path 2 (AttitudeControl.cpp:105 projection, once): AGREE (I also cite :197 where it is added).
- Path 3 (omega_ff never consumed, yawspeed_ref not set by module, only lib+test use it): AGREE. Nuance: first key says
  yawspeed_ref is NaN from the module; I confirm module sets only accel_only, q, f_b, mean_u, a_ref, yaw_ref, dt, so default NaN, yes.
  I add that AttitudeControl.cpp:200 has an unrelated local named omega_ff (name collision for greps).
- Path 4 (mc_indi_rate_control takes vehicle_rates_setpoint, no yaw term): AGREE for the grep of omega_ff/yawspeed_ff (none); I did not re-read McIndiRateControl.cpp:353.
- Verdict NO PATH / not possible: AGREE.
- "Unit test: not written, lib-only test tests nothing about A-9": DISAGREE in part. A lib test cannot prove the total, but it
  does guard the one precondition that matters (omega_ff stays yaw-rate free), and it was cheap: written and passing.
  The first key's AttitudeControl-level design is a complementary, not replacement, test.
- "Archive magnitude 0.45 rad/s": not checked by me.
