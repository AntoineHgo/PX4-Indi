# INDI integration log (session 6)

## Step 1: message (commit d66f114963)
- Added `msg/IndiRateStatus.msg` (topic `indi_rate_status`: timestamp, nu[3],
  angular_accel_filtered[3], torque_filtered[3], torque_increment[3], fault),
  registered in `msg/CMakeLists.txt`, logged by default in
  `logged_topics.cpp` with `add_optional_topic("indi_rate_status")` (interval 0, full
  rate; only published when INDI is active).
- Decision: no `# TOPICS` line (single topic, name derived from file name).
- Build: covered by the combined build in step 3 (purely additive change).

## Step 2: module and parameters
- Params in `mc_rate_control_params.yaml`: MC_RATE_CTL_TYPE (enum 0 PID, 1 INDI),
  MC_INDI_G1_R/P/Y (320/210/30, yaw marked unidentified), MC_INDI_G2_Y (0),
  MC_INDI_K_R/P/Y (20/20/10), MC_INDI_ACT_TC (0.02), MC_INDI_DELAY (0..4, 0),
  MC_INDI_DT_MAX (1.0). Names as in architecture.md section 6/7.
- `MulticopterRateControl.{hpp,cpp}`: `IndiRateControl _indi`; selection `_use_indi`
  latched in the existing disarm block, which also calls `_indi.reset()` and zeroes
  the previous torque (so first run, change of selection and disarm all reset).
  IMU_GYRO_CUTOFF / IMU_DGYRO_CUTOFF read via param_find/param_get in
  `parameters_updated()`. New private `runIndiRateControl()` builds
  torque_allocated_prev (previous published torque minus stored
  `unallocated_torque` only if the allocator status timestamp is newer than the
  previous torque publication), calls `update()`, publishes `indi_rate_status`.
- PID branch is now the `else` branch of `if (_use_indi)` with unchanged code
  (re-indented). `rate_ctrl_status` is published on the PID branch only (its
  integrator fields are meaningless for INDI). Battery scaling skipped on INDI
  (`!_use_indi &&`), yaw LPF only on PID. Thrust unchanged.
- Decision: `angular_accel_filtered` in the status is the input `xyz_derivative`.
- Decision: the allocator status copy in the saturation block now also stores
  `unallocated_torque` and its timestamp (no effect on the PID path).
- CMake: `IndiRateControl` added to DEPENDS of the module.

## Step 3: build, format, test
- `indi_project/docker/run.sh -n build -t 3000 'make px4_sitl_default'`: PASS, no warnings
  (built with both changes; the msg commit is purely additive). parameters.xml contains
  MC_RATE_CTL_TYPE and the MC_INDI_* parameters.
- `Tools/astyle/fix_code_style.sh` on the 3 changed C++ files: Unchanged.
- `make tests TESTFILTER=indi_rate_control`: PASS (1/1).
- Commits: d66f114963 (msg), d6182aea41 (module + params).
- Not verified: SITL flight with INDI; that each commit builds alone (msg commit not built separately).
- This log is left uncommitted.

## Yaw cutoff (session 8)

### Step 1: library (commit 68ef4eaa0b)
- `IndiRateControl::setYawCutoff()` (<=0 or non-finite -> 0 = off), two `LowPassFilter2p`
  instances (`_yaw_lpf_accel`, `_yaw_lpf_torque`) with identical coefficients on the yaw
  component of a_f (after the caller's chain) and t_f (after H). Increment law unchanged,
  uses the filtered pair (G2 term uses the filtered t_f too). New getter
  `getFilteredAngularAccel()` and member `_a_f` for logging.
- Disabled = filter bypassed (not pass-through), so outputs are bit-identical to before.
- Enabled flag set in `designFilters()`: cutoff > 0 and < 0.45 x sample rate, otherwise off
  (explicit 0.45 guard; LowPassFilter2p itself only disables at >= 0.5 x rate).
- Redesign trigger extended with a yaw cutoff change; a pending flag makes update() reset both
  filters to the current unfiltered a_f,yaw and t_f,yaw (no transient). `resetStates()` resets
  both to 0 (so on ground each cycle the a_f,yaw filter is reset: output is b0 x input, near 0).
- Deviation from the brief: test 2 injects the noise on the yaw angular acceleration input
  (the path the filter acts on) rather than on the yaw rate; noise on the rate only enters via
  nu and is not filtered. Tests use 250 Hz (dt 4 ms) as specified. Test 1 compares against a
  controller where setYawCutoff() is never called (cannot compare against the old binary).
- 4 new gtests (14 total): YawCutoffZeroLeavesOutputsUnchanged, YawCutoffReducesYawNoiseOnly
  (std < 0.7 x, roll/pitch equal), YawCutoffEnableHasNoTransient, YawCutoffInvalidValuesDisableFilter
  (NaN, inf, -5, 120 Hz).
- `make format`: passed, only my files changed.
- `indi_project/docker/run.sh -n unittest -t 2400 'make tests TESTFILTER=indi_rate_control'`:
  PASS, 14/14 gtests (1/1 ctest).

### Step 2: parameter and wiring (commit 7da2dc5456)
- `MC_INDI_YAW_CUT` (float, Hz, default 0, 0..100, decimal 1, increment 1) in
  mc_rate_control_params.yaml after MC_INDI_DT_MAX; short description kept brief per
  parameters.instructions.md; `setYawCutoff()` called in `parameters_updated()`.
- `indi_rate_status.angular_accel_filtered` now from `getFilteredAngularAccel()`
  (post-yaw-filter value), torque_filtered already post-filter.
- Same test command: PASS 1/1 (the test build also compiles mc_rate_control, no warnings seen).
- Not verified: px4_sitl_default build (forbidden while PID batch runs), SITL flight.
- Log left uncommitted.
