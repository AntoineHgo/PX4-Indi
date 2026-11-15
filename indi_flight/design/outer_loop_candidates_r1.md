# Outer-loop architecture candidates, round 1 (session 4, 2026-11-15)

Checked against `outer_loop_requirements.md` (R1-R36). The review of that file
(`outer_loop_requirements_review.md`) may add items; candidates are re-checked against it before review round 1.
F-6 fixes the placement: one module started *instead of* `mc_pos_control` by parameter.

## Constraints common to every candidate (derived, not chosen)

- **Output interface is `vehicle_attitude_setpoint`** (q_d + thrust_body + yaw_sp_move_rate). In every PC-on mode
  the commander also sets `flag_control_attitude_enabled`, so `mc_att_control` publishes `vehicle_rates_setpoint`
  (ATT:304-310). A position module that publishes rates itself (the archive's external-mode design,
  `McIndiPosControl.hpp:152`) would fight `mc_att_control` in stock modes, and silencing it needs a commander or
  `mc_att_control` change, which O-11 forbids. Rejected: candidate R-a below.
- **Input contract unchanged:** `trajectory_setpoint`, `vehicle_constraints`, `goto_setpoint`, land detector,
  HTE, `vehicle_control_mode` (R6, R7). FlightModeManager, Navigator, mavlink and commander stay untouched; that is
  what makes F-2 (every mode) reachable: each mode is served by serving the contract.
- **Thrust scale unchanged:** thrust_body in normalised units with hover = hover thrust (R24), so the land detector
  and the hover-thrust estimator keep working unmodified.
- **Stock libraries linked, not modified:** `Takeoff`, `GotoControl`, `PositionControl`/`ControlMath` are
  `px4_add_library` targets under `src/modules/mc_pos_control/`; a new module can link them (zero diff, O-11).
- **INDI acceleration law** (`src/lib/indi_accel_control`, kept): thrust vector command
  T_cmd = T_meas + (a_ref - a_meas) / G, with a_meas = specific force from `vehicle_acceleration` rotated to NED
  plus gravity, T_meas from measured rotor speed (modelled actuator when telemetry is missing, O-5), both filtered
  by the same filter (decision 6). Then thrust vector -> (tilt-limited) attitude and collective via
  `ControlMath::limitTilt` / `thrustToAttitude`. Remedy for a steady command/output gap (decision 2) plugs in at
  T_meas; not decided here.
- **New inputs** (R33): `vehicle_attitude` (or q from local position), `vehicle_acceleration`, `esc_status`.
  Each gets a staleness rule: stale IMU -> modelled a_meas = T_cmd*G (degenerates to a non-INDI P-on-velocity law,
  logged); stale ESC -> modelled actuator (O-5).

## Candidate A: shell copy, stock kinematics, single rate

- **Structure.** `mc_indi_pos_control` = copy of the `MulticopterPositionControl` shell (~800 lines: subscriptions,
  takeoff state machine driver, constraints, offboard want_takeoff, failsafe setpoint, EKF reset handling,
  tilt-limit slew, GotoControl hosting, publications). Inside the cycle, stock `PositionControl` computes the
  position P / velocity P (I = 0, D as stock) and feed-forward, giving a_ref via `getLocalPositionSetpoint()
  .acceleration`; its own thrust output is discarded. The INDI stage turns a_ref into thrust vector and attitude.
- **Rate.** One work item on the `vehicle_local_position` callback (R2), INDI stage at the same rate.
- **Reused:** PositionControl (validity rules R18, NaN axes R9, velocity limits R28), ControlMath, Takeoff,
  GotoControl, all MPC_* kinematic and limit parameters (same meaning, same values work).
- **Duplicated:** the shell. Every future upstream fix to `MulticopterPositionControl.cpp` must be ported.
- **Modes and transitions:** identical to stock by construction, since the shell and the kinematic layer are
  stock. Ground/idle (R15), ramp (R14), disarmed (R32): the INDI stage is bypassed and the stock thrust/attitude
  of PositionControl is published (ground handling is open-loop by design, INDI is meaningless on the ground).
  Hand-over ground -> INDI at end of RAMPUP: INDI starts from T_meas, so no thrust step (to prove: R14).
- **Without telemetry:** modelled actuator; with modelled state INDI has implicit integral action, behaves like a
  PI on acceleration.
- **Cost:** shell ~800 lines duplicated, INDI lib ~350 lines; one work item. Flash: estimate later.
- **Upstream:** acceptable pattern (as `mc_indi_rate_control` vs `mc_rate_control`), the duplicated shell is
  the main objection. Mitigation (later, optional, upstream PR of its own): factor the shell.
- **Weak point:** INDI bandwidth limited by the local-position rate (R36, rate UNVERIFIED: if EKF2 publishes
  local position at 100+ Hz this is acceptable for an acceleration loop of 3-5 Hz; at 50 Hz it costs phase).
  PositionControl's anti-windup/thrust-saturation logic is inert with I = 0, and the vertical-priority saturation
  (R27) must be re-done in the INDI stage.

## Candidate B: shell copy, stock kinematics, dual rate

- Same as A for the slow part (shell, kinematics, take-off, failsafe, resets, goto at the local-position rate).
- **Fast INDI stage** on a second callback (`vehicle_acceleration`, or `vehicle_attitude`), at a configured rate
  (e.g. 250 Hz, decimated from IMU), holds a_ref from the slow part with jerk feed-forward extrapolation, and
  publishes `vehicle_attitude_setpoint` at the fast rate. The slow part passes a mode word (bypass/ground,
  INDI active, failsafe) and the limits (tilt, thrust) to the fast part.
- **Gain over A:** INDI delay is the IMU/ESC path, not the EKF publish interval; a_meas and T_meas are sampled
  together at the same rate, which makes filter matching (decision 6) clean.
- **Costs over A:** two work items in one module (shared state, lock-free hand-over), 2-5x the attitude-setpoint
  publication rate (mc_att_control accepts any newer timestamp, R34), more CPU, more to test (the hand-over,
  stale slow part). R2/R36 apply to the slow part only.
- Everything else as A.

## Candidate C: own position law, no stock PositionControl

- Shell as A or B, but pos/vel/acc in an INDI-native class (position P, velocity P, acceleration INDI), with its
  own validity rules, NaN-axis handling and limits.
- **Gain:** a law designed for INDI (e.g. velocity loop shaped against the INDI acceleration loop, saturation
  handled in acceleration space once). **Cost:** re-implements R9, R18, R27, R28 and their tests; parity with
  stock behaviour must be proven instead of inherited.

## Rejected at this round

- **R-a: publish `vehicle_rates_setpoint` directly** (archive design). Conflicts with mc_att_control in every
  stock PC-on mode; needs commander or mc_att_control changes (O-11). Serves only external/offboard modes (F-2).
- **R-b: acceleration setpoint consumed by the INDI rate module.** Needs a new interface between position and
  rate modules bypassing mc_att_control's ownership of attitude; same objection as R-a.
- **R-c: patch mc_pos_control with an INDI option.** Violates zero diff (O-11), F-6.

## Preliminary preference and what would overturn it

Preference: **A first, with the INDI stage written as a rate-independent class** so that B is a later change of
the trigger only. Overturned if (1) the measured `vehicle_local_position` rate is below ~100 Hz or its latency
makes the acceleration-loop delay margin fail G2 at the target bandwidth, or (2) the A-prototype's take-off/landing
hand-over needs a second fix. C only if PositionControl's internals (saturation, anti-windup inert with I = 0)
turn out to fight the INDI stage.

## Open facts to settle before review round 1

1. `vehicle_local_position` publish rate and latency vs IMU in SITL (`uorb top`, timestamp_sample deltas).
2. CLOSED (S4): PositionControl with I = 0 does not alter a_ref. `_velocityControl` adds the velocity P/D to
   `_acc_sp` (PC:150-153); every saturation and the horizontal ARW act on `_thr_sp` or `vel_error` afterwards
   (PC:157-198), and `_vel_int` stays 0 with zero I gain (PC:201). So a_ref = ff + P/D is unsaturated, and the
   vertical priority + XY margin (R27, PC:163-186) and tilt limit must be re-done on the INDI thrust vector. INDI
   increments from the measured thrust, so it needs no integrator anti-windup (to show in the prototype).
3. Where the hover thrust enters a_ref -> thrust in INDI (only through T_meas scale: check R24/R25 consistency).

## Re-check against the requirements review (T5, `outer_loop_requirements_review.md`)

- Rnew-1 (take-off machine runs with PC off, skip=true, so a manual -> altitude switch in air does not re-enter
  spool-up), Rnew-2 (SYS_VEHICLE_RESP / MPC_*_VEL_ALL remapping lives in mc_pos_control), Rnew-4 (want_takeoff
  as the only take-off trigger), Rnew-5 (silent when vehicle_local_position stops): A and B inherit all four by
  copying the shell; C must keep the shell too. Any candidate that rewrites the shell must list them explicitly.
- R9 correction (an all-NaN axis invalidates the whole setpoint; altitude and descend modes carry an xy
  acceleration setpoint): A and B inherit stock validity rules; the INDI stage receives a finite xy a_ref in
  those modes. C must reproduce PC:231-234 exactly.
- Fact 1 CLOSED (S4, from `results/t3_ref_airframe/run2/flight.ulg`, quad5in, stock PID, SITL lockstep):
  vehicle_local_position 125.0 Hz (dt 8.00 ms median and p95), vehicle_attitude and sensor_combined 250 Hz
  (IMU_INTEG_RATE 250), vehicle_attitude_setpoint 125 Hz one-to-one with local position, timestamp -
  timestamp_sample = 0 (lockstep). At 125 Hz one period costs 14 deg of phase at 5 Hz, 4 deg at 1.5 Hz: adequate
  for an acceleration loop under a 1-2 Hz velocity loop. **A stays preferred**; B is the fallback if G2's delay
  margin fails on A. Not known: the rate and latency on hardware (IMU_INTEG_RATE default 200 Hz, EKF2 timing):
  goes to the bring-up checklist (G8).
