# T204 ALTCTL z-only INDI stage (D-ALTCTL-Z) - log

## Hook points
- Library `indi_accel_control.hpp`: Input gets `z_only`, `thrust_dir`.
- Library `update()`:
  - validation block right after the existing required-input check (before any state is touched): thrust_dir finite,
    norm > eps, thrust_dir(2) < -0.1*norm, else return false; n_dir = normalised.
  - step 6 (saturation), after the finite check and the existing `t_c(2) > -kMinUpThrust` guard on the vertical
    component: if z_only, `t_c = n_dir * (t_c(2)/n_dir(2))` and the tilt limit is skipped. Why here: filters, blend,
    a_c and the INDI vertical increment (steps 1-5) are untouched; the guard keeps the vertical command upward;
    everything downstream (c, collective clamps, `thrust`, `_thrust_prev`, `_coll_clamped`, out.t_c, q_d from
    -t_c/c) then uses the z-only vector, so the blend model path and the previous command follow what is output.
  - collective max: in z_only the whole vector is scaled (direction fixed) instead of shrinking only the horizontal
    part; the min clamp already scales the whole vector.
  - step 8: `omega_ff` stays 0 when z_only (extra `!in.z_only` in the feedforward condition).
- Module `McIndiPosControl.cpp`: want_indi accepts `flag_control_climb_rate_enabled`; in runIndiStage
  `in.z_only = !(position_enabled || velocity_enabled)`, `in.thrust_dir = local_pos_sp.thrust[0..2]` (read before the
  stage overwrites it at its end).

## Tests (IndiAccelControlTest.cpp, fixture IndiAccelZOnlyTest)
Fail-before (header fields added, no implementation): `make tests TESTFILTER=IndiAccelControl` -> 37 passed, 5 FAILED:
OutputParallelToThrustDir, VerticalComponentMatchesThreeAxis, InvalidThrustDirReturnsFalse, OmegaFfZero,
CollectiveLimitsApplyNoTiltLimit. ClosedLoopCollectiveRemovesVerticalError PASSED before (see UNVERIFIED: the plant
is vertical so the old 3-axis path also converges; it is a regression guard for the z_only collective path, not
discriminating).
Pass-after: all 42 tests of the target pass (100% tests passed, 1/1 ctest).
Break-check: replaced the line `t_c = n_dir * (t_c(2) / n_dir(2));` by a comment -> OutputParallelToThrustDir,
VerticalComponentMatchesThreeAxis, CollectiveLimitsApplyNoTiltLimit FAILED (3 tests); line restored (verified, no
marker left), final run 42/42 pass.

## PositionControl in ALTCTL (read only, no change)
- xy: module already calls resetIntegralXY when xy velocity and position setpoints are NaN (ALTCTL case).
  _accelerationControl builds thr_sp from _acc_sp xy (stick acceleration from the flight task, if any) and z, so
  local_pos_sp.thrust is the stock direction used as thrust_dir.
- z: velocity loop acc_sp z = Kp (vz_sp - vz) + vel_int - Kd vel_dot. The module's pre-update
  `_control.resetIntegral()` (want_indi && stageInputsFresh) now also applies in ALTCTL (intended), and
  `resetIntegral` after an active stage cycle as in other modes. No other difference in the z path.

## Build / full test
- `make px4_sitl_default` in docker: OK (module compiled and linked).
- `make tests TESTFILTER=IndiAccelControl`: 42 tests (36 old + 6 new), all pass.
- Format: fix_code_style.sh on the 4 files: unchanged (already clean).

## UNVERIFIED
- Module change has no unit harness; verified by compile only (no SITL flight in ALTCTL, no G5 flight).
- Closed-loop test uses a level, vertical plant (thrust_dir straight up); tilted-dir plant behaviour (model assumes
  t_f along z_b while the stock direction may differ from the body z at the switch) is not covered.
- Behaviour at the mode switch (z transient) is for the G5 flight per the decision's overturn condition.
