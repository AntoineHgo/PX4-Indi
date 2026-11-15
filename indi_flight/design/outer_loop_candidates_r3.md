# Outer-loop architecture candidates, round 3 (session 11, 2026-11-15)

Deltas to A as amended in `outer_loop_candidates_r2.md`, answering `outer_loop_review_r2.md` (1 BLOCKING, 2 MAJOR,
4 MINOR). Everything not named here stands as in r2.

## A10. Acceleration-only axes run open loop, as stock (N1 BLOCKING, N2, N7)
- Per cycle and per axis group (xy, z), the module classifies the `trajectory_setpoint` after PositionControl's own
  NaN handling: an axis group is *acceleration-only* when its position and velocity setpoints are both NaN and its
  acceleration setpoint is finite. Sources today: FlightTaskDescend z (`FlightTaskDescend.cpp:57-58`), blind
  descent/land in mc_pos_control (`MulticopterPositionControl.cpp:680-712`, reproduced by the module), Altitude mode
  xy (`FlightTaskManualAltitude.cpp:300`), offboard acceleration-only.
- On an acceleration-only group the INDI increment is not applied: that group's share of the thrust vector is the
  stock mapping of a_ref (PositionControl `_accelerationControl` path with `ht`), so drag limits speed exactly as with
  mc_pos_control. The other group keeps INDI. The thrust vector is assembled from the two groups before the tilt
  limit and saturation of A4, so A4 is unchanged.
- Group edges (acceleration-only <-> tracked) are bypass edges and use A3 tracking: the inactive group's INDI state is
  seeded from the published collective/tilt each cycle (adds e7 to the edge list).
- N7: offboard acceleration-only setpoints therefore keep stock meaning; stated in the user docs.
- Tests: descend failsafe from 100 m in SITL, vertical speed bounded (stock value +-10 %); Altitude mode stick
  release, horizontal speed decays as with PID; unit test of the classifier on every flight task's setpoint pattern.
- Overturn: a mode is found whose setpoint pattern the classifier cannot express per group (e.g. velocity on x only).

## A11. Thrust-scale gap (N3 MAJOR) is decision 2, not architecture
- With measured actuator state, a gap k between commanded and measured collective leaves a_ref - a_meas = G (1-k)
  T_cmd standing, the same mechanism as lesson 9 in the rate loop. A2's zero integrators remove nothing.
- The architecture must not preclude the remedy. Candidates (decision 2, chosen in stage 3 with the inner loop):
  (a) slow per-motor correction of the command-to-omega^2 map in the rate stack, which removes the gap for both loops
  at the source; (b) a slow integrator on the INDI acceleration error in the module; (c) re-enabling PositionControl
  velocity integrators (MPC_*_VEL_I_ACC) as in stock. A keeps (c) available: A2 becomes "integrators reset only at
  bypass edges" if (c) is chosen.
- Stage-2 thrust-gap test (thrust scale 0.85, one motor 0.8) is the measurement that decides; acceptance stays R24.

## A12. Minor items
- N4: tracking seed read from the latest `vehicle_thrust_setpoint` in the edge cycle; e6 = position resume after a
  gap > 5 cycles counts as an edge.
- N5: A8 overturn rule replaced: overturn if climb rate exceeds the ramp limit by 20 % or `flying_but_ground_contact`
  is set within 1 s after e1, for ht errors +-20 %.
- N6: parameter renamed `MC_INDIP_EN` -> new name chosen at implementation (archive meaning differs); rc.mc_apps uses
  the stock fallback pattern `mc_indi_pos_control start || mc_pos_control start`, same for the rate pair.

## Open for round 3 (narrow: A10-A12 only)
1. Does per-group open loop (A10) leave any mode or edge with a discontinuity in collective or tilt?
2. Is the classifier unambiguous for every flight task (FlightTaskAuto, Orbit, Manual*, Descend, Offboard)?
