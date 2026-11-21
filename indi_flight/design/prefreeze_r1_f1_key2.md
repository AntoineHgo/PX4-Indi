# Pre-freeze r1 F1, second-key review

Verdict: ACCEPT (no BLOCKING, no MAJOR; two MINOR).

## (a) Collective with direction (0,0,-1), z_only, on ground
indi_accel_control.cpp:371-373 keeps the vertical component of t_c and replaces only the direction. The collective
does not come from the thrust direction. t_c = t_f + (a_c - a_f) (:337); the call site feeds a_ref from the stock
a_z setpoint, which on ground is +100 m/s^2 down (McIndiPosControl.cpp:907-911), so t_c,z > -kMinUpThrust and is
forced to -max(c_min, 0.1) (:367-369). c_min = 0 on ground (call site :185, flying ? thr_min : 0).
Result: c = 0.1 m/s^2, thrust = 0.1/(g_t*k_cmd) ~ 0.005 at ht 0.5. Tilt zero. Not hover, no unbounded path.
- MINOR M1 (indi_accel_control.cpp:368): landed z_only output is ~0.005, not exactly 0 like stock. Harmless
  (below any idle), but the "minimum/zero thrust" claim in the design note should read "kMinUpThrust floor".
  Fix: word the note accordingly; optionally clamp thrust to 0 at the call site when !flying.
- Ramp to flight edge: no new step. At the edge thr_min goes 0 -> MPC_THR_MIN and a_ref leaves the +100 setpoint; both
  existed before the change. The substitution only affects direction, which is vertical in both cases.

## (b) flying flag
Correct. McIndiPosControl.cpp:891 flying = takeoff state >= flight, passed to runIndiStage (:1045) and used the same
way for thr_min at :185 and the stock minimum_thrust at :926. Consistent with the rest of the stage.

## (c) Substitution in flight
Only fires on a finite, exactly zero vector (norm^2 < 1e-12). In flight stock minimum thrust is MPC_THR_MIN > 0, so
the vector is nonzero. With MPC_THR_MIN = 0 and a stock command of zero, INDI commanding the kMinUpThrust floor
equals the stock intent. NaN is excluded (isfinite) and still goes to Hold. Non-z_only paths untouched. No harm found.

## (d) Tests
IndiStageModeTest.cpp:84-98 assert the two helpers (isZeroThrustDir, holdFallbackThrust) only.
- MINOR M2 (IndiStageModeTest.cpp / IndiAccelControlTest.cpp:564): the call-site wiring (substitution actually
  applied, Hold fallback using `flying`) is not asserted. Library test :564 covers the floor with a_ref but not
  z_only with direction (0,0,-1). Fix: add a library test z_only, thrust_dir (0,0,-1), a_ref z = +100 expecting
  thrust ~ 0.1/(g_t*k_cmd) and finite q_d level.
