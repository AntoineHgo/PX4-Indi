# O-11 agent log (module mc_indi_rate_control)

- Step 1: read spec, old code (2357bdccb7). Wrote src/modules/mc_indi_rate_control/{McIndiRateControl.{cpp,hpp},
  IndiMeasuredTorque.{cpp,hpp},IndiMeasuredTorqueTest.cpp,CMakeLists.txt,Kconfig,mc_indi_rate_control_params.yaml}.
  Decisions: (a) torque helper is a uORB-free library `IndiMeasuredTorque` (+ `IndiControlAllocation` deriving
  ControlAllocationPseudoInverse, adds getControlFromActuators); module feeds it esc samples. (b) Rotor geometry from
  ActuatorEffectivenessMultirotor (VehicleActuatorEffectiveness lib, defined in control_allocator dir, so Kconfig
  `depends on MODULES_CONTROL_ALLOCATOR`), config via getEffectivenessMatrix(CONFIGURATION_UPDATE) on every
  parameters_updated(), weak-row zeroing + normalize flag as ControlAllocator does. (c) Measured torque is computed
  at the END of the rates-enabled branch (after publishing torque setpoint), mimicking the allocator running after
  the setpoint; used by the next cycle, so timing equals old placement. (d) Non-fresh rotors are evaluated at trim
  (old code used allocator setpoint) - only affects the torque value while valid=false, which INDI ignores.
  (e) Not ported: failed-motor column zeroing (_handled_motor_failure_bitmask), allocator-side stopped motors
  (NaN): MC multirotor INDI only; with a failed motor ESC goes offline -> measured torque invalid -> model fallback.
  (f) MC_ACRO_* params still come from mc_rate_control yaml (reused, as spec). No battery scaling, no PID, no
  gain compression, no vtol, no rate_ctrl_status (INDI path never published them... rate_ctrl_status was PID-only).
- Step 2: build/px4_sitl_o11 builds (exit 0, 1896 targets) with module enabled in sitl board. Fixed: license comment close, EffectivenessMatrix type, actuator_motors include.
- Step 3: gtest first failed: ControlAllocationPseudoInverse normalises lazily in allocate() -> helper runs one allocate() with zero setpoint after setEffectiveness (fix).
- Step 4 (done): gtests in build/px4_sitl_test: functional-IndiMeasuredTorque 4/4, unit-indi_rate_control_test 35/35,
  unit-ControlAllocationPseudoInverse 5/5, functional-ControlAllocationSequentialDesaturation 20/20,
  functional-ActuatorEffectivenessRotors 4/4. build/px4_sitl_o11 builds (ninja exit 0), parameters.xml has MC_INDI_EN /
  MC_INDI_W_MAX, rc.mc_apps in the build has the selection. Zero diff vs 7d362c6f38 for mc_rate_control,
  control_allocator, control_allocation (empty); indi_rate_control lib unchanged vs HEAD.
  Commits: d2c1f06ad8 (module), 299a55e2fa (rc.mc_apps + sitl board). This log is left uncommitted.
  Unverified: no SITL flight/start of the module (px4 not run); measured-torque equivalence with the old allocator
  is by construction + gtest only; MC_ACRO_* params still defined by mc_rate_control yaml (module needs mc_rate_control
  built in for acro params); board test.px4board inherits the module via default.
