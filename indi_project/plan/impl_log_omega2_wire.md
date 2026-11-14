# Implementation log: omega2 wiring (D-omega2, D-omega2-wire)

Branch feat/indi-control. One commit per step. Docker only; build/px4_sitl_default untouched (SITL batch running).

## Step 1: messages
- Added msg/ActuatorTorqueMeasured.msg (timestamp, timestamp_sample, float32[3] torque, bool valid, uint8 motor_valid_mask), registered in msg/CMakeLists.txt after ActuatorTest.
- Added `bool measured_torque_in_use` to msg/IndiRateStatus.msg.
- Read .github/instructions/messages.instructions.md (timestamp_sample, no versioning): followed.
- Commit: ddecbb37ce `feat(msg): add actuator_torque_measured and measured_torque_in_use`. Build check deferred to the final SITL compile (step 4 end).

## Step 2: ControlAllocation::getControlFromActuators
- Added const `getControlFromActuators(const ActuatorVector &)` in ControlAllocation.hpp (same expression as getAllocatedControl incl. nanToZero on a copy; getAllocatedControl untouched).
- gtest `ControlAllocationPseudoInverseTest.ControlFromActuatorsMatchesAllocatedControl` in ControlAllocationPseudoInverseTest.cpp (exact equality with setpoint, trim -> zero, linearity, NaN as zero).
- Test: `indi_project/docker/run.sh -t 1500 'make tests TESTFILTER=ControlAllocation'` -> 2/2 ctest passed (unit-ControlAllocationPseudoInverse incl. new case, functional-ControlAllocationSequentialDesaturation). First attempt failed to compile (EXPECT_EQ with a template temporary containing a comma), fixed.
- astyle (Tools/astyle/astylerc, Docker, dry-run) on both files: clean.
- Commit: 2c9ef01a90 `feat(control_allocation): add getControlFromActuators`.

## Step 3: control_allocator
- module.yaml: CA_R_W_MAX (float, rad/s, default 0 = off, min 0, max 5000, after CA_REV_THR_FRAC). ControlAllocator.hpp/.cpp: esc_status subscription, `EscSample _esc_samples[MAX_NUM_MOTORS]` (static), `update_esc_samples()`, `publish_actuator_torque_measured(now)` called after allocation when `do_update`. Msg field comment: motor_valid_mask covers motors 1-8 only (uint8).
- Motor mapping: esc[j].actuator_function - 101 = motor index i; motor indexes come first in the actuator order of the allocator (publish_actuator_controls and effectiveness config iterate motors first), so for matrix 0 column = running count of motors with matrix_selection_index 0 (= i for a multirotor). Motors whose selection index is not 0 are skipped.
- u_i = clamp((omega/CA_R_W_MAX)^2, 0, 1); invalid if non finite, omega < 0 or omega/omega_max > 1.5 (local copy of IndiRateControl::normalisedThrustFromRpm logic, kMaxOmegaRatio 1.5; lib not linked). Other actuators = their setpoint (NaN -> zero inside getControlFromActuators). valid = all rotors of matrix 0 online + sample valid + age < 20 ms (kEscSampleMaxAge); torque finite.
- gz_bridge esc_status (GZMixingInterfaceESC.cpp): per esc: timestamp=now, esc_online_flags bit set for all, actuator_function = mixing output function, esc_rpm from the eRPM model. A dropped telemetry frame (SIM_GZ_ERPM_DRP) is represented by esc_errorcount++ with the LAST GOOD rpm and a FRESH esc timestamp (mimics the DShot driver). Handling: an errorcount change = repeated sample, so the stored sample and its timestamp_good are kept; a run of drops therefore ages the sample out after 20 ms (about 5 frames at the ~250 Hz esc_status rate) and valid goes false; a single drop keeps valid true with a held value (one-frame-old rpm), which avoids dropping INDI out of the measured path (kMeasValidCycles = 20) on every drop. timestamp_sample = oldest timestamp_good among the rotors.
- Deviation/safety: only published when `_effectiveness_source_id == MULTIROTOR` (u=(omega/omega_max)^2 and motor=column only make sense for multirotor rotors; other airframes would mix motor types).
- Commit: fa3d8f2381 `feat(control_allocator): publish torque produced by measured rotor speeds`.

## Step 4: mc_rate_control
- Params MC_INDI_ERPM_DLY (int 0..4, default 1) and MC_INDI_ERPM_TO (float s, default 0.02, min 0.001, max 0.5) in mc_rate_control_params.yaml before MC_INDI_DT_MAX. Subscription actuator_torque_measured (member `_torque_measured`, zero/invalid until received) polled only inside runIndiRateControl (INDI path); valid = msg.valid && now >= timestamp_sample && age < TO && finite; setMeasuredTorque before update(); setMeasurementDelaySamples in parameters_updated(); indi_rate_status.measured_torque_in_use = _indi.measurementInUse(). PID path code untouched (only a param setter on the idle INDI object in parameters_updated).
- Commit: 62c0eb5937 `feat(mc_rate_control): use the measured actuator torque in the INDI path`.

## Verification
- astyle 3.1 (Tools/astyle/astylerc, Docker, dry-run) on ControlAllocator.{cpp,hpp}, MulticopterRateControl.{cpp,hpp}: all Unchanged (clean). make check_format not run (whole tree).
- SITL compile: `indi_project/docker/run.sh -t 2400 'cmake -S . -B build/px4_sitl_omega2 -G Ninja -DCONFIG=px4_sitl_default && ninja -C build/px4_sitl_omega2'` -> exit 0, 1892/1892, no warnings (-Werror), parameters.xml contains the new params. build/px4_sitl_default untouched.
- `make tests TESTFILTER=ControlAllocation` -> 2/2 passed (run after step 2; step 3/4 do not touch the library).
- `make tests TESTFILTER=indi_rate_control` -> 1/1 passed (35 gtests inside, library unchanged).

## Unverified / open
- No SITL flight, no unit test for the allocator (ControlAllocator has no gtest harness) or for the mc_rate_control wiring: the esc_status -> actuator_torque_measured path, its drop handling and the fallback are untested at run time.
- Actuator order assumption (motors first, column = motor index for matrix 0) taken from the code, not asserted at run time; only the MULTIROTOR effectiveness source is supported.
- Without a command-curve fit (THR_MDL_FAC, see D-omega2) the measured u and the allocator setpoint are inconsistent by design; CA_R_W_MAX for gz x500 should be 1000 rad/s (SIM_GZ_EC_MAX).
- Real ESC drivers: errorcount-based drop detection assumes esc_errorcount increments on a failed frame; if a driver does not, a held value looks fresh.
- MC_INDI_ERPM_TO max (0.5 s) and CA_R_W_MAX max (5000 rad/s) were chosen here, not specified.
- Step 1 build check happened in the final SITL compile (messages generate there).
