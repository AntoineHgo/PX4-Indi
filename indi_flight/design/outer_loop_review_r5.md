# Review r5: flatness feed-forward side channel (A18), `flatness_r1.md`

Reviewer: independent, opus, session 13. Scope: `indi_flight/design/flatness_r1.md` against Tal & Karaman
(arXiv 1809.04048) and the rate-setpoint entry point of `src/modules/mc_indi_rate_control/McIndiRateControl.cpp`.

Paper source: arXiv HTML v2. Eqs. 1-15 (Sec. II) were read verbatim. The HTML fetch was truncated, so anything from
Sec. III on is marked **[S]** (secondary summary, not verified against the text). Re-check those before relying on them.

Verdict: BLOCKING. Finding 1 is a design-level double count in the mode the note names as its main target (Orbit). It
can be fixed by defining the message content precisely. Findings 2-4 are MAJOR.

## Findings

1. **BLOCKING: the xy body-rate component of the yaw rate is counted twice whenever the yaw rate is nonzero at tilt
   (Orbit is the clearest case).**
   - In the paper, Eq. 14 inverts `[j; psi_dot] = [[tau R [i_z]x^T, b_z], [S, 0]] [Omega; tau_dot]`. The jerk row has
     `[i_z]x^T`, which removes Omega_z. So Omega_x and Omega_y are fully determined by the jerk, and psi_dot only sets
     Omega_z through `psi_dot = S Omega` (Eq. 12).
   - The LIB matches the jerk part: `omega_ff = (j.y_b/c, -j.x_b/c, 0)` (`src/lib/indi_accel_control/indi_accel_control.cpp:330-337`).
   - mc_att_control, at zero diff, also adds the yaw rate at unity along the world z axis expressed in body:
     `_omega_command = yaw_axis_body * yawspeed_setpoint` (`AttitudeControl.cpp:105`) and
     `rate_setpoint += q_rel.rotateVector(_omega_command)` (`AttitudeControl.cpp:197`). At tilt this term has x and y
     components `psi_dot * (e3.x_b, e3.y_b)`.
   - Take a rigid rotation about world z at psi_dot, for example Orbit with the nose to the centre. Then
     `j = psi_dot e3 x t`, and the LIB gives `p = psi_dot e3.x_b` and `q = psi_dot e3.y_b`, which is already the full
     true xy rate. mc_att_control adds the same amount again, so the xy rates are doubled.
   - Orbit does set the yaw rate: `_yawspeed_setpoint = _orbit_velocity / _orbit_radius` (`FlightTaskOrbit.cpp:378`),
     and it reaches mc_att_control through `attitude_setpoint.yaw_sp_move_rate = _yawspeed_sp` (`PositionControl.cpp:272`).
   - Size: the extra rate is `psi_dot * sin(tilt)`. At 10 m/s on a 10 m radius (psi_dot = 1 rad/s, tilt about 45 deg)
     that is about 0.7 rad/s of spurious roll/pitch rate. The attitude P loop has to fight it, so it shows up as
     tracking error and could make A18 look worse than F-a.
   - The same double count already exists in the INDI POS path: `setAttitudeSetpoint(out.q_d, out.yawspeed_ff)` followed
     by `+ out.omega_ff` (`McIndiPosControl.cpp:564-571`). That path is out of scope here, but it is evidence that the bug
     is in the design, not in a typo.
   - The note's unit test ("analytic omega for a constant-speed circle", §4) would not catch this. It checks A18's term
     on its own, not the sum with mc_att_control's term.
   - Fix: the message must carry `Omega_flat - (what mc_att_control already adds)`. In the xy plane, that means
     subtracting `psi_dot * (e3 . x_b, e3 . y_b)` with psi_dot = the `yaw_sp_move_rate` of the same setpoint. The
     simpler equivalent is to project out the part already produced by the yaw rate and keep only the jerk part
     orthogonal to it.

2. **MAJOR: the freshness condition "attitude-setpoint stamp matches the setpoint currently used" cannot be checked
   in the rate module as written.**
   - The rate module consumes only `vehicle_rates_setpoint` (`McIndiRateControl.cpp:287-291`). That message has no
     attitude-setpoint stamp (`msg/VehicleRatesSetpoint.msg`: timestamp, roll, pitch, yaw, thrust_body, reset_integral).
   - mc_att_control publishes a new rate setpoint every attitude cycle from the latest accepted q_sp. It also drops
     non-increasing or invalid setpoints (`mc_att_control_main.cpp:327-341`), so even "latest published" is not always
     "used".
   - To check the condition, the rate module must also subscribe to `vehicle_attitude_setpoint` and compare its
     timestamp with the stamp in the feed-forward message. This also catches the switch to Stabilized, where
     mc_att_control publishes its own setpoint (`mc_att_control_main.cpp:212,317`), which then carries a newer stamp.
   - There is one remaining race: in the cycle where a new setpoint is published, the rate module can see it before
     mc_att_control has consumed it. The cost is one attitude cycle of feed-forward against the previous q_sp, which is
     acceptable, but say so in the design.

3. **MAJOR: the entry point holds `_rates_setpoint` between messages, so "adds omega_ff to the rate setpoint" is
   ambiguous and has an accumulation trap.**
   - `_rates_setpoint` is a member that is overwritten only when a new `vehicle_rates_setpoint` arrives (`:287`), while
     `Run()` executes on every gyro sample (`:233`, about 4-8x more often).
   - If the feed-forward is added into `_rates_setpoint` itself, it integrates. If it is added only on message arrival,
     a stale feed-forward is never removed.
   - The feed-forward must go into a local `rates_sp_used = _rates_setpoint + ff_gated` computed every cycle and passed
     to `_indi.update` (`:195`).
   - That sum must be constrained to the rate limits again. mc_att_control limits before publishing
     (`AttitudeControl.cpp:210-212`), and the INDI POS path re-limits after adding its feed-forward (`McIndiPosControl.cpp:571`).
   - The Acro branch (`:262-285`) must never add the feed-forward. The gate should require
     `flag_control_attitude_enabled && flag_control_position_enabled|velocity_enabled`, not only "INDI stage active".

4. **MAJOR: frame not specified.**
   - "omega_ff in FRD" does not say which body. The LIB builds it in the *desired* body (`R_d(q_d)`,
     `indi_accel_control.cpp:333-335`), and the rate module applies it in the *estimated* body.
   - mc_att_control rotates its own feed-forward from the reference body into the current body with `q_rel`
     (`AttitudeControl.cpp:192-197`).
   - The two frames agree at small attitude error. They do not agree during the transients where the feed-forward
     matters most: a fast tilt reversal, recovery after a gust, and the first cycles after a mode switch.
   - Fix: publish the feed-forward together with the q_d it was built in, and rotate it by `q^-1 q_d` in the rate
     module, which then needs `vehicle_attitude`. The alternative is to state the small-error approximation as an
     explicit, tested assumption.

5. **MINOR: double count with the stock reference model when `MC_REF_FF > 0`.**
   - mc_att_control's reference model (`AttitudeControl.cpp:94-130`, `MC_REF_W_N` default 50, `MC_REF_FF` default 0)
     feeds forward the time derivative of q_sp, with a lag, scaled by `MC_REF_FF`.
   - At the default of 0 there is no overlap. With MC_REF_FF = 1, both terms carry d(q_sp)/dt.
   - Note §2 F-a ("lag about 1/MC_ROLL_P") ignores this existing stock path. Either gate A18 to MC_REF_FF == 0 or
     document the conflict. F-a with `MC_REF_FF` tuned is also the zero-new-interface baseline that A18 must beat in
     the acceptance test.

6. **MINOR: §1 mapping is mostly correct, with the following corrections.**
   - Acceleration law: the paper's law is `(tau b_z)_c = (tau b_z)_f + a_c - a_f` (Eq. 20 [S]). This matches LIB:273.
     However, `a_c = K_x e_x + K_v e_v + K_a (a_ref - a_f) + a_ref` (Eq. 17 [S]) has an acceleration-error term that
     stock PositionControl does not have. The row "gap: none" is therefore slightly overstated. This is not a reason
     to add the term.
   - Measured thrust: in the paper the filtered thrust comes from motor-speed encoders (Eq. 5 and the Introduction,
     verbatim), not from ESC `mean_u`.
   - Feed-forward structure: the paper adds the feed-forward at the angular-acceleration level,
     `Omega_dot_c = K_xi xi_e + K_Omega (Omega_ref - Omega_f) + Omega_dot_ref` (Eq. 28 [S]). Adding omega_ff to the rate
     setpoint of a P-on-rate INDI loop gives the same structure with K_xi = K_rate*K_att. The F-c structure is
     therefore sound.
   - Yaw: the paper uses yaw angle psi from the horizontal projection of b_x (Eq. 11). That is the same angle as
     `bodyzToAttitude`. The paper's tilt-first construction also chooses between psi and psi+pi (Eqs. 24-25 [S]),
     which PX4 does not do. That is harmless.
   - The note does not mention that psi_dot enters only Omega_z. That omission is the root of finding 1.
   - Paper evidence on value: the ablation in Table V [S] removes the rate and angular-acceleration feed-forward
     *together* (RMS error 9.0 -> 16.8 cm). The paper does not quantify the jerk-to-rate term alone, and that is the
     only part A18 can provide.

7. **MINOR: inconsistency on jerk from differentiation.**
   - §3 says "never differentiate a_ref". The LIB still has a difference path (`indi_accel_control.cpp:230-238`,
     `jerk_from_difference`), and `McIndiPosControl.cpp:544` documents falling back to it when the message jerk is zero.
   - A18 must use only a finite, nonzero message jerk, with `from_diff` forced off for the published feed-forward.
     Otherwise every setpoint step becomes a rate pulse (the r1 F14 class).

8. **MINOR: steps and staleness.**
   - PositionSmoothing jerk is piecewise constant, so the feed-forward steps by up to `MPC_JERK_AUTO/g`, held
     zero-order at the rate-loop rate. A step in the INDI rate setpoint becomes a torque step.
   - A first-order filter or slew limit on the feed-forward in the rate module costs little.
   - "<2 outer cycles": define it in microseconds against `vehicle_local_position` timestamps, not a cycle count. The
     local-position rate is not constant, and the gyro-driven rate loop has no notion of an "outer cycle".
   - Zero the feed-forward when `landed || maybe_landed`, which the rate module already has (`:252-253,312`), and on
     disarm (`:298`).

9. **MINOR: transitions that break, or are untested, if findings 2-3 are not fixed.**
   - Auto -> Stabilized / Acro mid-turn: mc_indi_pos_control stops publishing, and the last feed-forward is applied
     for up to 2 outer cycles against a stick attitude.
   - Offboard where the jerk drops to zero or NaN between messages.
   - Heading or quaternion estimator reset: q_d jumps, but the feed-forward computed in the old desired frame is still
     applied.
   - Land / touchdown.
   - Failsafe to Descend / Land from Orbit at tilt.
   - None of these are in the acceptance set. The note's overturn clause names "A3/e7 edges" but does not list them.

## Acceptance plan (question 4)
The measured on/off figure-8 and Orbit test against ground truth, with the same-seed spread as the bar, is the right
kind of test, but it is not enough. It needs the following additions:
- **Unit tests.**
  - Compute the full rate setpoint as mc_att_control output plus A18, not A18 alone.
  - Check it against the analytic Omega for (i) a constant-speed circle with the yaw locked to the tangent or centre,
    which catches finding 1, and (ii) the same circle with a fixed yaw.
  - Check it at tilts of 10, 30 and 45 degrees.
- **Tests with `MC_REF_FF` = 0 and = 1.** The reference model, with no new interface, is the baseline A18 must beat.
- **A scripted edge set**, run with the feed-forward magnitude logged:
  - Auto -> Stabilized -> Acro during an Orbit;
  - RTL landing;
  - an injected heading reset;
  - offboard with the jerk stream cut.
  - Pass criterion: the feed-forward actually applied in the rate module is exactly 0 within one attitude cycle of
    each edge, and no rate-setpoint step is larger than the A-only run's.
- **Log the applied feed-forward** (after gating) in the rate module's status, not only the computed one in
  `indi_pos_status`. Otherwise gating bugs are invisible.

## Minimal correct A18
- **Message.** mc_indi_pos_control publishes `indi_rate_feedforward` with these fields:
  - `timestamp` (from the local-position sample);
  - `attitude_setpoint_timestamp` (equal to the `vehicle_attitude_setpoint.timestamp` it published in the same cycle);
  - `q_d`;
  - `omega_ff_xy` in the q_d body, computed only from a finite, nonzero `trajectory_setpoint.jerk` (no difference
    path) as `(j.y_b, -j.x_b)/c - psi_dot*(e3.x_b, e3.y_b)` with `psi_dot = yaw_sp_move_rate`, so the
    mc_att_control yaw term is not counted twice;
  - Omega_z = 0, because mc_att_control already carries the yaw rate;
  - no alpha_ff.
- **Gating in the rate module.** Every gyro cycle, the rate module computes
  `rates_sp_used = constrain(_rates_setpoint + g * R(q^-1 q_d) * omega_ff, -rate_max, rate_max)`. The factor g is 1
  only if all of these hold:
  - the message is younger than a fixed time (for example 25 ms);
  - its `attitude_setpoint_timestamp` equals the latest `vehicle_attitude_setpoint.timestamp`;
  - the attitude and velocity/position control flags are set;
  - the vehicle is not Acro, not landed or maybe_landed, and armed;
  - `MC_REF_FF == 0`.

  Otherwise g is 0 immediately. The feed-forward is already step-limited by the slew limit of finding 8, so no
  separate ramp is needed.
- **Not changed.** `_rates_setpoint` itself is never modified, and mc_att_control stays at zero diff.
