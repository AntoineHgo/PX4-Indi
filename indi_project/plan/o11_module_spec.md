# O-11 refactor: `mc_indi_rate_control` module (spec, session 37)

Owner decision O-11 (`indi_project/OWNER_GUIDANCE.md`). Already done (session 37):
`c1a700e7bb` restores `src/modules/mc_rate_control` and `462eb68990` restores
`src/modules/control_allocator` + `src/lib/control_allocation` to the branch base
(merge-base with main, 7d362c6f38): zero diff. The pre-refactor reference code is commit
**2357bdccb7** (read it with `git show 2357bdccb7:<path>`):

- `src/modules/mc_rate_control/MulticopterRateControl.{cpp,hpp}`: INDI path (`_use_indi`,
  `runIndiRateControl()`, `_torque_measured`, `_unallocated_torque`, params, IMU cutoff lookups).
- `src/modules/mc_rate_control/mc_rate_control_params.yaml`: the `MC_INDI_*` and
  `MC_RATE_CTL_TYPE` definitions.
- `src/modules/control_allocator/ControlAllocator.{cpp,hpp}`: measured torque from ESC rpm
  (`CA_R_W_MAX`, `esc_status` -> normalised thrust (omega/w_max)^2 -> `getControlFromActuators()` ->
  `actuator_torque_measured`), including timeouts/validity rules.
- `src/lib/control_allocation/.../ControlAllocation.hpp`: `getControlFromActuators()`
  = `(effectiveness * (u - trim)).emult(control_allocation_scale)`, NaN -> 0.

## Design (decided, record as D-o11 in DECISIONS.md is done by the orchestrator)

1. **New module** `src/modules/mc_indi_rate_control/` (class e.g. `McIndiRateControl`), Kconfig option
   `MODULES_MC_INDI_RATE_CONTROL` (default n), enabled only in `boards/px4/sitl/default.px4board`.
   It does everything the old `mc_rate_control` did when `_use_indi` was true, and nothing of the PID
   path: same subscriptions (angular velocity + acceleration, rate setpoint, acro/manual handling if the
   old module did it on that path, landed/arming state, control_allocator_status), same publications
   (`vehicle_torque_setpoint`, `vehicle_thrust_setpoint`, `rate_ctrl_status` if published there,
   `indi_rate_status`, battery scaling exactly as before). Behaviour must be identical to 2357bdccb7 with
   `MC_RATE_CTL_TYPE 1`: this is a behaviour-preserving move. The control law stays in
   `src/lib/indi_rate_control/` (do not change it).
2. **Selection** in `ROMFS/px4fmu_common/init.d/rc.mc_apps`:
   `if param compare -s MC_INDI_EN 1 then mc_indi_rate_control start else mc_rate_control start fi`.
   `MC_INDI_EN` (int, 0/1, default 0, `reboot_required: true`) is defined in the new module's yaml, so on
   a board without the module the param does not exist and PID starts. This replaces `MC_RATE_CTL_TYPE`
   (removed) and the old "latched while disarmed" runtime switch. Only one torque publisher can run.
3. **Measured torque in the module**, using the libraries, not a copy of the math in a new place:
   link `ActuatorEffectiveness` (rotor geometry from `CA_ROTOR*`, via `ActuatorEffectivenessRotors` or
   the multirotor effectiveness class the allocator uses) and `ControlAllocation`. Recommended: a small
   class deriving from `ControlAllocationPseudoInverse` that adds `getControlFromActuators()` (protected
   member access), configured exactly as `ControlAllocator` configures its instance
   (`setEffectivenessMatrix(...)` with trim/linearisation point, same normalisation incl. the
   `CA_` normalisation rules), so B, trim and scale match the allocator by construction. Reload on
   `parameter_update`. `CA_R_W_MAX` becomes `MC_INDI_W_MAX` [rad/s] (same semantics, default 0 =
   measured torque disabled -> the law's model-based fallback, as before). Port the ESC timeout /
   validity / eRPM-delay logic from the old allocator code unchanged. Keep publishing
   `actuator_torque_measured` (now from this module) for logging; message unchanged.
4. **Params:** move the `MC_INDI_*` definitions (except nothing new beyond `MC_INDI_EN`, `MC_INDI_W_MAX`)
   to `src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml` (or module.yaml), same names,
   defaults, ranges and text. Reuse `IMU_*`, `CA_*`, `MC_*` where the old code did.
5. **gtest** in the module dir (`px4_add_functional_gtest` or `px4_add_unit_gtest` as fits): for the x500
   geometry (4 rotors, read positions/km from `ROMFS/px4fmu_common/init.d-posix/airframes/4001_gz_x500`),
   build a normal `ControlAllocationPseudoInverse` like the allocator, allocate a few torque/thrust
   setpoints, and check the module's helper maps the allocated actuator vector back to the same control
   (`getAllocatedControl()`), within 1e-5. Also NaN actuator -> treated as zero thrust.
6. **No VTOL / fixed-wing paths.** No dynamic allocation. Follow `.github/instructions/*.instructions.md`
   matching the paths (read only those whose `applyTo` matches).

## Commits (each builds; `git commit -s`; trailer `Assisted-by: Claude:claude-sonnet-5-5`; no Co-Authored-By)

a. `feat(mc_indi_rate_control): add INDI rate controller module` (module, params, Kconfig, gtest).
b. `feat(rc.mc_apps): start mc_indi_rate_control when MC_INDI_EN is set` (ROMFS + sitl board enable).
Format changed C/C++ with `Tools/astyle/fix_code_style.sh <file>` (inside the Docker image if astyle is
missing on the host). A transient `.git/index.lock` error comes from a running batch: retry.

## Build and test constraints

- All builds in Docker via `indi_project/docker/` wrapper (see `indi_project/STATE.md` Conventions).
- **Never** build into or delete `build/px4_sitl_default` (a batch is flying it) or
  `build/px4_sitl_omega2` (old-placement reference binary for the regression check). Build SITL into
  `build/px4_sitl_o11` (same out-of-tree method used for `build/px4_sitl_omega2`: grep STATE.md /
  DECISIONS.md / bench scripts for "px4_sitl_omega2" to find it). Unit tests may use `build/px4_sitl_test`.
- Done = module builds in `build/px4_sitl_o11`, all gtests matching `indi` and the new test pass, and
  `git diff 7d362c6f38 -- src/modules/mc_rate_control src/modules/control_allocator src/lib/control_allocation`
  is empty.

## Not in this task (next)

Bench: `run_scenario.py` must set `MC_INDI_EN` at boot (posix `PX4_PARAM_<NAME>` env mechanism) and fly
both the old binary (old names `MC_RATE_CTL_TYPE`, `CA_R_W_MAX`) and the new one from the same params
files; smoke flights; regression check (O-11 "How").
