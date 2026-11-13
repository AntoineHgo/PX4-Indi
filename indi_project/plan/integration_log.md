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
