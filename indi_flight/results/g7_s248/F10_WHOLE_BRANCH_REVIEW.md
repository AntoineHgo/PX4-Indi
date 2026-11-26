# F-10 whole-branch review (G7 f), feat/indi-flight at 0b1c6a26d1

Independent review, read-only. Scope: class A of indi_flight/bench/make_fw_branch.sh (A_PATHS) against `main`
(merge-base = main = 7d362c6f38); class B only for the id/path grep. Size: `git diff --stat main -- <A>` = 58 files,
12810 insertions, 4 deletions; `<B>` = 13 files, 1778 insertions, 19 deletions. Grep ran on added lines only
(`git diff -U0 main -- <paths>`, file:line of the new file).

## Grep commands and hit counts

| pattern (on added lines) | A hits | B hits | true violations |
|---|---|---|---|
| `\b(D-[A-Z0-9-]+\|A-?[0-9]{1,3}\|S[0-9]{2,3}\|K[0-9]{2,3}\|Q[0-9]{1,2}\|RC[0-9]{2,3}\|G[1-8]\([a-z]\))\b` | 0 | 5 | B: 5 |
| `indi_flight` | 0 | 1 | B: 1 |
| `indi_project` | 0 | 0 | - |
| `owner` (case-insensitive) | 35 | 3 | 0 (all BSD licence "COPYRIGHT OWNER") |
| `freeze` (case-insensitive) | 3 | 0 | 0 (physical anti-windup / filter freeze) |
| `\bgate\b` | 0 | 0 | - |
| extra: `_[sgkq][0-9]{2,3}\b\|\.md\b\|\.py\b\|design note\|np\.` | 4 | 3 | A: 2 (.md paths), A: 2 MINOR (np.unique); B: 2 (run_scenario.py) |
| extra: `\bG[0-9]\b` / `G1`,`G2` | 9 | 0 | 0 (INDI effectiveness symbols) |
| extra: `TODO\|FIXME` | 1 | - | 0 (copied stock TODO, McIndiPosControl.cpp:923) |
| extra: `stage\|session\|finding\|campaign\|candidate\|draw\|route` | 16 | - | 0 ("INDI stage" = control stage; "candidates" = frequency bins) |

Class B hits (all BLOCKER for the B commit, fixes are comment-only):

| file:line | hit | suggested replacement |
|---|---|---|
| ROMFS/px4fmu_common/init.d-posix/rcS:397 | `(D-SCHED)` | `# SITL scenario player: plays arm, mode and offboard setpoints from a schedule file in simulation time` |
| src/modules/simulation/gz_bridge/GZBridge.cpp:606 | `A-14:` | `// gz-sensors never applies <reference_altitude>, so the sensor reports sea-level pressure at the local` |
| src/modules/simulation/gz_bridge/GZBridge.cpp:1024 | `(A-14)` | `// written once, before the flag that airPressureCallback reads` |
| src/modules/simulation/gz_bridge/GZBridge.hpp:256 | `A-20:` | `// publishes _alt_ref to the baro callback (other gz thread)` |
| src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp:171 | `(A-37 closing test)` | `// Release-age statistics over a window of releases, printed at the end of each window` |
| src/modules/simulation/sim_scenario_player/SimScenarioPlayer.hpp:109 | `indi_flight/bench/run_scenario.py` | `// altitude PD gains of the auto thrust` |
| src/modules/simulation/sim_scenario_player/SimScenarioPlayer.hpp:71 | `(as run_scenario.py thr_cmd)` | drop the parenthesis |
| src/modules/simulation/sim_scenario_player/SimScenarioPlayer.cpp:317 | `as run_scenario.py thr_cmd` | `// auto: hover thrust / tilt + altitude PD` |

## Findings, class A

Severity: BLOCKER = id/path/bookkeeping reference or misleading name; MAJOR = unclear public name/param/field or
style violation of the instructions files; MINOR = wording. All fixes below are behaviour-neutral (comments,
private/local renames, file headers, yaml text) unless marked in the next section.

| file:line | category | severity | finding | suggested fix |
|---|---|---|---|---|
| src/modules/mc_indi_rate_control/IndiInjectionStep.hpp:39 | bookkeeping ref | BLOCKER | `(the call-site tests of design note attitude_break_s86.md, section 8)`: project design note with session id | ` * rate setpoint) and which setpoint the INDI law receives. Kept out of McIndiRateControl so that a unit test runs` / ` * the same code path as the module.` |
| ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:73 | bookkeeping ref | BLOCKER | `(rationale in ref_airframe_model.md)`: project document | `# stock PID rate and attitude gains scaled for the small, fast quadcopter` |
| src/modules/mc_indi_pos_control/McIndiPosControl.hpp:147 | misleading name | BLOCKER | `_coll_meas` holds the commanded collective from vehicle_thrust_setpoint (cpp:129), not a measurement; cpp:441 even has to say "c is the COMMANDED collective (not measured)" | rename to `_collective_command` (hpp:147, cpp:129,244,299,439); comment `///< latest vehicle_thrust_setpoint collective (commanded)` |
| src/modules/mc_indi_pos_control/{EkfResetDetect.hpp, EkfResetDetectTest.cpp, FailsafeSetpoint.hpp, FailsafeSetpointTest.cpp, IndiStageMode.hpp, IndiStageModeTest.cpp, SetpointExtrapolation.hpp, SetpointExtrapolationTest.cpp}:1 | PX4 style | MAJOR | no PX4 BSD licence header (all other 29 new C++ files have the 2026 header) | prepend the standard `Copyright (c) 2026 PX4 Development Team` BSD-3 block used by the sibling files |
| msg/ActuatorTorqueMeasured.msg:6 | wrong reference | MAJOR | names parameter `CA_R_W_MAX`, which does not exist; the parameter is `MC_INDI_W_MAX` | `# each rotor, u_i = (omega_i / MC_INDI_W_MAX)^2, in place of the actuator setpoint. Only published while MC_INDI_W_MAX > 0.` |
| msg/{ActuatorTorqueMeasured,IndiPosStatus,IndiRateFeedforward,IndiRateStatus}.msg | uORB doc standard | MAJOR | not to docs/en/uorb/uorb_documentation.md: no leading description block (timestamp is line 1), units trailing `(m/s^2)` instead of leading `[m/s^2]`, `[-]` missing on normalised fields, enum constants uncommented, no `[@frame]` on NED/FRD vectors, ActuatorTorqueMeasured mixes `[us]` and `(microseconds)` | comment-only rewrite, e.g. IndiPosStatus: first lines `# INDI acceleration loop internals` / `#` / `# Published by mc_indi_pos_control while it runs the INDI loop.`, then `float32[3] a_c # [m/s^2] [@frame NED] Commanded acceleration, INDI loop input, including the excitation`; same pattern for all fields |
| src/modules/mc_indi_pos_control/McIndiPosControl.cpp:1300-1305 | misleading doc | MAJOR | module description copied from mc_pos_control: "a PID loop for velocity error", no word on INDI; the INDI module has no velocity integrator in use (INDI supplies it) | `This implements the multicopter position controller with an acceleration INDI loop.` / `The stock position and velocity loops compute the commanded acceleration (no integrator), an incremental nonlinear dynamic inversion on the measured specific force turns it into the thrust vector and attitude setpoint.` / `It replaces mc_pos_control when MC_INDI_POS_EN is set (see rc.mc_apps).` |
| src/modules/mc_indi_pos_control/McIndiPosControl.hpp:331-333 | misleading comment | MAJOR | `_omega_ff_out` described as "rotor-speed feed-forward"; it is the body-rate feed-forward | `// rate feed-forward the INDI loop produced (valid only on an active INDI cycle), published every cycle` |
| src/modules/mc_indi_pos_control/IndiPosInjection.hpp:73 | misleading comment | MAJOR | `timestamp_sample_us cycle time (gyro sample time)`: the module passes `now` (hrt_absolute_time), not a gyro time | `@param timestamp_us cycle time, microseconds` |
| src/modules/mc_indi_pos_control/IndiPosInjection.hpp:39 (+ .cpp) | design history / duplication | MAJOR | "Copy of mc_indi_rate_control/IndiInjection ..., renamed to avoid a duplicate symbol": a 2nd copy of the same generator (code-review instructions: framework reuse, necessity) | comment: delete the line. Real fix (not neutral, see below): one generator in src/lib |
| src/lib/indi_rate_control/indi_rate_control.hpp:47,48,62,263,383 (+ .cpp) | ambiguous name | MAJOR | torque increment named `dt_cmd` / `_dt_cmd` next to `dt` (time step) in the same formula `(G1 + G2/dt) dt_cmd` | rename member `_dt_cmd` -> `_torque_increment`, formula symbol `dt_cmd` -> `Delta` (already used at line 61) |
| src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:63-71 | prior MINOR 1 | MINOR | still present (G2_Y long: "not the motor time constant", 5-inch history) | as F10_UNIT8_REVIEW finding 1 |
| mc_indi_rate_control_params.yaml:31,42,54-55 | prior MINOR 2 | MINOR | still present ("in rad/s^2" repeats unit; G1_Y default restatement) | `long: Roll angular acceleration per unit of normalised torque.` (P, Y alike; drop G1_Y 2nd sentence) |
| mc_indi_rate_control_params.yaml:17-21 | prior MINOR 3 | MINOR | still present ("(1.0)", "Zero disables" instead of stock phrase) | as unit 8 finding 3 (ends "Set to 0 to disable, INDI then uses its actuator model.") |
| mc_indi_rate_control_params.yaml:126-128 | prior MINOR 4 | MINOR | still present (tuning rationale) | `Time constant of the first order actuator model, also used by the rate lead (MC_INDI_LEAD). When unsure, round up.` |
| mc_indi_rate_control_params.yaml:140-142 | prior MINOR 5 | MINOR | still present (formula sentence) | as unit 8 finding 5 |
| mc_indi_rate_control_params.yaml:79-88 | prior MINOR 6 | MINOR | still present: int32 with options re-listed in `long` via `\|-` block | `type: boolean`, `short: INDI physical parameters identified`, `long: While 0, MC_INDI_K_R, MC_INDI_K_P and MC_INDI_K_Y are applied at half their value.` (metadata type change only; stored value 0/1 unchanged) |
| mc_indi_rate_control_params.yaml:262-358 (+ pos yaml 77-153) | prior MINOR 7 | MINOR | still present (prefix repeated on 9 + 7 entries) | keep the sentence on `_AX` only, others end with `Only used when MC_INDI_INJ_AX is not 0.` |
| mc_indi_rate_control_params.yaml:210 | prior MINOR 8 | MINOR | still present | delete `The torque is ramped instead of stepped.` |
| both params yaml | prior MINOR 9 | MINOR | still present: folded `>-` scalars (instructions: "plain or quoted YAML scalar"); output is one paragraph so QGC is fine | optional: convert to quoted one-line scalars |
| msg/IndiRateFeedforward.msg:6 | prior MINOR 10 | MINOR | still present ("ramp, z only" undefined). IndiPosStatus part is fixed (stage_mode now says "takeoff ramp") | `bool valid # INDI loop active (not bypass, landed, takeoff ramp or altitude only) and omega_ff finite` |
| rate yaml short 260-357, pos yaml 75; IndiPosStatus.msg:4-6; IndiRateStatus.msg:16,21; McIndiRateControl.hpp:119,120,127; .cpp:112,240; McIndiPosControl.hpp:135; .cpp:282,625,842; IndiInjection.hpp:37; IndiPosInjection.hpp:37; IndiInjectionStep.hpp:37,71; indi_accel_control.hpp:185 | wording | MINOR | "bench (loop-break) excitation": the excitation runs in flight, "bench" is project jargon | "system identification excitation" (shorts: `INDI sysid excitation axis`, ...) |
| McIndiRateControl.hpp:120, .cpp:240,253; IndiInjectionStep.hpp:52,59-63,72-73, .cpp:44,64,73; IndiInjection.hpp:38; IndiPosInjection.hpp:38; McIndiPosControl.cpp:282,290-292,349,359 | symbols | MINOR | `u = c + d`, `x = y + d` undefined at use; `u` is also the normalised rotor thrust and `c` the lead gain in the same code | write out: "controller output plus excitation"; e.g. cpp:253 `// published and fed back setpoint = controller output + excitation, so every feedback path sees what was applied` |
| src/modules/mc_indi_pos_control/IndiStageMode.hpp:6 | decision echo | MINOR | `(no PID fallback)` restates a project decision | ` * Mode selection of the INDI outer loop.` |
| src/modules/mc_indi_pos_control/McIndiPosControl.cpp:308-309 | design history | MINOR | `(re-seeding them with one raw sample gave a 1.9 deg tilt spike at a yaw reset)` | `// is not differentiated. The measured force and collective filters are frame independent and kept.` |
| IndiInjection.cpp:75, IndiPosInjection.cpp:75 | external reference | MINOR | `np.unique` refers to a Python reference not in the tree | `// each bin is kept once (k is non-decreasing), then k >= 1 and k * df <= fmax * (1 + 0.5 * df / fmax)` |
| IndiInjectionTest.cpp:55, IndiPosInjectionTest.cpp:54-56 | test provenance | MINOR | expected waveform values have no stated source | add `// expected values: double precision evaluation of the same multisine formula` |
| indi_accel_control.hpp:151; McIndiPosControl.cpp:94 | SITL detail | MINOR | `~267 Hz` is the SITL vehicle_acceleration rate | `(native rate, above the control rate)` / drop the number |
| indi_accel_control.hpp:151,198; indi_accel_control.cpp:381; McIndiPosControl.cpp:441 | wording | MINOR | capitalised emphasis EVERY, MEASURED, SAME, COMMANDED | lower case |
| indi_accel_control.hpp:252-256,277,245,259-263 | private names | MINOR | `_native_f`, `_native_cut`, `_native_hz`, `_native_dev_count`, `_t_a_ff_prev`, `_delay`, `_u_buf`, `_um_buf`, `_lpf_um` | `_force_native_last`, `_force_native_cutoff_hz`, `_force_native_rate_hz`, `_force_native_rate_dev_count`, `_a_ff_prev_time`, `_delay_samples`, `_mean_u_delay_buf`, `_model_u_delay_buf`, `_lpf_model_u` |
| McIndiPosControl.hpp:142,152-153,177-182; .cpp:113 | private names | MINOR | `_q_time`, `_acc_time`, `_esc_time`, `_thr_time`, `_hte`, `_hte_valid`, `_filter_hz`, `_filter_cut`, parameter `ht` | `_attitude_time`, `_accel_time`, `_esc_status_time`, `_thrust_sp_time`, `_hover_thrust_estimate`, `_hover_thrust_estimate_valid`, `_filter_rate_hz`, `_filter_cutoff_hz`, `hover_thrust` |
| McIndiPosControl.hpp:223-237 | PX4 style | MINOR | `_param_indi_*` handles; PX4 convention (and the rate module) is `_param_<full lowercase name>` | `_param_mc_indi_xy_p`, `_param_mc_indi_pos_lpf`, ... |
| McIndiRateControl.hpp:131 | name | MINOR | `IndiMeasuredTorque _measured_torque_model` (measured vs model) | `_measured_torque` |
| indi_rate_control.cpp:52 / .hpp:129; indi_accel_control.hpp:174 | names | MINOR | parameter `tb_s` | `blend_tc_s` |
| TorqueStampTracker.hpp:46; IndiRateFeedforwardGate.hpp:47; RateSetpointWatchdog.hpp; IndiMeasuredTorque.hpp | constant style | MINOR | mixed `kMaxAgeUs` and `RING`/`CLEAR_COUNT`/`MAX_COMPONENTS`; `RING` unclear | `kOwnStampCount`, `kClearCount` (pick one style per module) |
| IndiInjectionStep.hpp:52 | name | MINOR | field `point` | `break_point` |
| indi_accel_control.cpp:110,113; McIndiPosControl.cpp:178,181 | magic numbers | MINOR | `0.2f` (rate deviation) and `5.f` (min rate) | `kRateDevRatio = 0.2f`, `kMinFilterRateHz = 5.f` |
| McIndiPosControl.cpp:275 | log text | MINOR | `INDI stage cond 0x%02x (want att acc aref rate esc active)` cryptic | `INDI run conditions 0x%02x (bits: requested, attitude, accel, accel cmd, rate, esc, active), rate %.0f Hz` |
| indi_rate_control.hpp:50-53,63-64 | long doc | MINOR | design rationale in file header ("so G2/G1 is not the motor time constant", lead explanation) | keep the law table, drop the two rationale sentences |
| McIndiPosControl.hpp:35 | doc | MINOR | `Multicopter position controller.` copied | `Multicopter position controller with an acceleration INDI loop.` |
| indi_accel_control.hpp:110-112; IndiStageMode.hpp:55 | names | MINOR | `z_only` / `deriveZOnly` for the climb-rate-only (collective-only) mode | `collective_only` / `isCollectiveOnly` |
| 4040_gz_quad5in:3,7 | wording | MINOR | "(5-inch reference airframe)"; model quad5in not in Tools/simulation/gz | `# @name Gazebo quad5in (5-inch quadcopter)`; `# Model: quad5in (not in PX4-gazebo-models, set PX4_GZ_MODELS)` |
| src/lib/indi_rate_control/indi_rate_control_test.cpp | file name | MINOR | snake_case test file, all other INDI tests are `*Test.cpp` | `IndiRateControlTest.cpp` |

Navigation terms: no violation. `heading` used only for the estimator heading reset counter (mirrors
`vehicle_local_position.heading_reset_counter`); `yaw`/`yaw_ref`/`yawspeed` follow the heading = yaw rule; "track"
appears only as a verb; no course/bearing/drift use.

## Findings whose fix changes a public name (costly, decide separately)

| item | severity | finding | suggested change |
|---|---|---|---|
| param MC_INDI_DT_MAX | MAJOR | "DT" reads as time step; it is the torque increment limit | `MC_INDI_INC_MAX` |
| param MC_INDI_INJ_RAMP | MAJOR | reads as "ramp"; it is the rate-setpoint excitation amplitude | `MC_INDI_INJ_AMPR` |
| params MC_INDI_XY_P, MC_INDI_XY_VP | MAJOR | same meaning as MPC_XY_P / MPC_XY_VEL_P_ACC (parameters.instructions: no two parameters with the same meaning); prefix also differs from the module's MC_INDI_POS_* | use MPC_XY_P / MPC_XY_VEL_P_ACC, or `MC_INDI_POS_XY_P` / `MC_INDI_POS_XY_VP` with a description of the INDI-specific role |
| uORB IndiPosStatus a_c, a_c_pre_inject, a_f, t_f, t_c, t_c_applied, mean_u, inject; IndiRateStatus nu, inject | MAJOR | math symbols as public field names (only defined by the trailing comment) | e.g. `accel_cmd`, `accel_cmd_pre_excitation`, `accel_filtered`, `thrust_filtered`, `thrust_cmd`, `thrust_cmd_applied`, `mean_rotor_thrust`, `excitation`, `angular_accel_desired`; minimum neutral alternative: full field comments to the uORB standard |
| uORB IndiRateFeedforward.timestamp_sample | MAJOR | documented as "gyro sample time of the cycle" but never written by mc_indi_pos_control (always 0) | set it from vehicle_local_position.timestamp_sample (behaviour change, small) or remove the field |
| IndiPosInjection duplicate of IndiInjection | MAJOR | two copies of one generator | move one `IndiInjection` (units-agnostic) to src/lib and use it in both modules |

## Prior unit 8 review (F10_UNIT8_REVIEW.md) status

Findings 1-9 still present unchanged; finding 10 half fixed (IndiPosStatus stage_mode now says "takeoff ramp";
IndiRateFeedforward.msg:6 still says "ramp, z only").

## Counts (class A)

BLOCKER 3, MAJOR 8 neutral + 6 public-name, MINOR 32 rows (10 of them the open prior unit 8 MINORs).
Class B grep: 8 id/path references (5 ids, 1 indi_flight path, 2 run_scenario.py), all comment-only fixes.

Verdict: does not meet F-10 as is; meets after the listed neutral fixes (3 BLOCKER, 8 MAJOR, plus the class B
comments), with the 6 public-name items left as an explicit decision (keep, or rename before first release).
