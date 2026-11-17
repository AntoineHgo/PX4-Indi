# A-9 on the new module (s67): code check

Verdict: NO PATH. A-9 is ARCHIVE-ONLY (source-read, no test run).

## Paths by which yaw rate reaches the body-rate setpoint
1. McIndiPosControl publishes vehicle_attitude_setpoint: q_d via ControlMath::thrustToAttitude (McIndiPosControl.cpp:193)
   and thrust. yaw_sp_move_rate is the stock PositionControl value (PositionControl.cpp:108,272), untouched by the INDI stage.
2. mc_att_control (zero diff vs main) passes q_d and yaw_sp_move_rate to AttitudeControl::setAttitudeSetpoint
   (mc_att_control_main.cpp:339). AttitudeControl.cpp:105 forms _omega_command = qzaxis(q_ref^-1) * yawspeed,
   i.e. psi_dot * (R^T e3). This is the exact world-yaw-rate projection on body axes, counted once.
3. The only other roll/pitch rate feed-forward is IndiAccelControl::Output.omega_ff = (j.y_b, -j.x_b, 0)/c
   (indi_accel_control.cpp:330-337), the term A-9 added on top. McIndiPosControl.cpp does not read out.omega_ff
   or yawspeed_ff, and nothing else in src/ outside the lib and its test uses omega_ff (grep). It is never published.
   The library's yawspeed_ref input is not set by the module either (NaN, so 0).
4. mc_indi_rate_control consumes vehicle_rates_setpoint from mc_att_control (McIndiRateControl.cpp:353); no yaw term is added.

## Consequence
- No double count at any tilt: total = psi_dot*(R^T e3) + P/reference-model term. Magnitude of an error for r=5 m, v=5 m/s,
  psi_dot=1 rad/s, tilt ~27 deg would have been psi_dot*(sin27) ~ 0.45 rad/s on one axis in the archive; here 0.
- Opposite risk, not A-9: with no jerk feed-forward published, the roll/pitch rate of a circle is only the reference-model
  and P response. That is a lag, not a double count, and is a separate topic.
- If someone later publishes omega_ff in rates_setpoint, the A-9 rule applies: omega_ff is already in the
  tilt-axes (x_b, y_b) and the yaw part is from mc_att_control, so omega_ff must not contain psi_dot*(e3.x_b, e3.y_b).

## Unit test: not written (path is not in callable code)
The total is only formed in mc_att_control + the rate module, and no code in IndiAccelControl combines the two,
so a gtest on the lib alone tests nothing about A-9. Design if wanted (AttitudeControl test, existing gtest in mc_att_control):
- Inputs: circle r=5, v=5 (omega_c=1 rad/s, a=5 m/s^2), yaw locked to path (psi_dot=1), tilt 0/15/30 deg via q_d at the
  hover-equilibrium attitude, yawspeed=1, reference model settled.
- Expected: update(q)+_omega_command body rates equal R^T*omega_world, omega_world = (tilt rate of q_d history) + psi_dot e3,
  tolerance 1e-3 rad/s, only for the yaw part (omega_command == psi_dot*R^T e3 to 1e-5).
- Run: indi_project/docker/run.sh (usage header not read), make tests TESTFILTER=... (unverified).
