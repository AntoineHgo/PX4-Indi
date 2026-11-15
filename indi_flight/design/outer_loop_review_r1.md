# Outer-loop candidates, review round 1 (independent, 2026-11-15)

Reviewed: `outer_loop_candidates_r1.md` against `outer_loop_requirements.md` (R1-R51) and the source on
`feat/indi-flight`. Abbreviations as in the requirements file; LIB = `src/lib/indi_accel_control/indi_accel_control`;
ARCH = `src/modules/mc_indi_pos_control/McIndiPosControl`. Stock modules confirmed at zero diff vs `main`
(`git diff --stat main -- src/modules/{mc_pos_control,mc_att_control,mc_rate_control,control_allocator,commander} src/lib/control_allocation` is empty).

## 1. Verdict per candidate

- **A (shell copy, stock PositionControl, single rate):** implementable, but not "identical to stock by construction":
  the I = 0 claim is false because `updateHoverThrust` writes the z integrator (F1), the modelled-actuator seed at every
  bypass->INDI or PC-off->PC-on edge is undefined (F3), and the thrust scale between stock bypass and INDI is unresolved (F4).
  0 BLOCKING, 5 MAJOR, 5 MINOR specific to or shared by A.
- **B (dual rate):** everything in A plus a fast stage that keeps publishing after the slow stage stops (R41) and a filter
  mismatch on `vehicle_acceleration` (F8). 0 BLOCKING, 7 MAJOR, 6 MINOR. Not for round 1.
- **C (own position law):** no inherited validity/limit/ramp semantics; the take-off ramp depends on the stock thrust mapping
  (F10), so C must prove R14, R18, R27, R28 from scratch. 1 BLOCKING (as written: ramp), 4 MAJOR, 3 MINOR.

Shared by all three: the module name and start script collide with the archive (F2), and no candidate lists
`vehicle_thrust_setpoint` as an input although the modelled-actuator path needs it (F3).

## 2. Findings

| id | cand. | class | req. | finding | evidence | suggested fix |
|---|---|---|---|---|---|---|
| F1 | A, B | MAJOR | R25, R47 | "PositionControl with I = 0 does not alter a_ref" (open fact 2, CLOSED) is wrong. `updateHoverThrust` adds `(a_sp-g)*Th_old/Th_new + g - a_sp` to `_vel_int(2)` on every valid HTE message, independent of the I gain; `_vel_int` is then summed into `_acc_sp` (a_ref). With I = 0 nothing ever bleeds it back, so a_ref(z) accumulates a bias with each HTE update, while the INDI stage already compensates the hover thrust from T_meas: double correction. | PC:75-92 (`_vel_int(2) +=`), PC:146-153 (`_vel_int` in `acc_sp_velocity`), MPC:423-431 (called on every valid HTE) | In the shell call `setHoverThrust` (no integrator shift) or never push the HTE into PositionControl; state explicitly that `_vel_int` is a don't-care and `resetIntegral()` is called each cycle. Add a unit test: 100 HTE updates with I = 0 leave a_ref unchanged. |
| F2 | all | MAJOR | R1, R51, O-11 | The new module is called `mc_indi_pos_control`, the archive module's name. The archive has Kconfig `MODULES_MC_INDI_POS_CONTROL` (`depends on MODULES_MC_POS_CONTROL`), parameter `MC_INDIP_EN` and a start block that runs it IN ADDITION to `mc_pos_control start` (unconditional). "Fresh start preserving the archive" cannot coexist with reusing the name, param and start block. No candidate states the new parameter, the removal/renaming of the archive block, or the `rc.vtol_apps:20` `vtol` variant. | rc.mc_apps:49 (unconditional), rc.mc_apps:67-71 (MC_INDIP_EN block), `src/modules/mc_indi_pos_control/Kconfig`, rc.vtol_apps:18-20 | Decide: new module name (e.g. `mc_indi_flight` or move the archive to `mc_indi_pos_control_ext`), new param (`MC_INDIF_EN`), replace rc.mc_apps:49 by an if/else like :17-23, same in rc.vtol_apps (R12/R51), keep the archive out of the default build. |
| F3 | all | MAJOR | R33, R37, R14 | Modelled actuator without telemetry (O-5) needs a seed for T_meas at every INDI (re)entry: end of RAMPUP, `flying_but_ground_contact` clearing (bounce during landing), PC-off->PC-on in air (Manual/Stabilized -> Position, R37), stale-ESC fallback. The candidates say "INDI starts from T_meas" only for the telemetry case. The archive seeds `_last_thrust = MPC_THR_HOVER` on reset, i.e. a thrust step equal to (actual throttle - hover) at a mode switch from stick throttle. `vehicle_thrust_setpoint` (rate-controller output, the signal LD and HTE read) is not in the input list. | ARCH:52, :222 (`_last_thrust = _param_mpc_thr_hover`); MPC:505-507, 522-530 (bypass conditions, toggle with `ground_contact`); TO:102-104 (armed+skip -> FLIGHT in PC-off, so no ramp on re-entry in air); LIB `reset(f_b, mean_u)` (hpp:143-150) | Add `vehicle_thrust_setpoint` as an input (with staleness rule, R33) and seed the modelled actuator and `IndiAccelControl::reset()` from it at every bypass->INDI edge; list the edges in the design. Test: Stabilized at 0.7 throttle -> Position mode in air, no thrust step. |
| F4 | A, B | MAJOR | R24, R25, R16, R46 | Thrust scale consistency (open fact 3) is still open and it is load-bearing: the bypass publishes stock `thrust = a_z*Th/g - Th` (Th = MPC_THR_HOVER, forced while not flying); INDI publishes `thrust = c/(g_t*k_cmd)` with `g_t`, `k_cmd` independent parameters and T_meas from rpm via `normalisedThrustFromRpm(rpm, rotor_w_max)`. Unless `g_t*k_cmd == g/Th` the hand-over at end of RAMPUP is a thrust step (with telemetry INDI removes it in a few cycles, with the modelled actuator it does not), and the HTE/LD thresholds (fraction of [THR_MIN, hover]) are evaluated on a scale the INDI stage does not know. | PC:219-223; MPC:513-515; LIB.cpp:276-277, :322 (`c_min = g_t*k_cmd*thr_min`, `thrust = c/(g_t*k_cmd)`); ARCH:300-328; LD:231-240, :283-288; HTE:165-190 | Define one scale: either `g_t = g/hover_thrust` (HTE-driven, MPC_THR_HOVER fallback, matching MPC:423-431) with `k_cmd = 1`, or keep `g_t` as a model constant and prove `g_t*k_cmd = g/MPC_THR_HOVER` by a preflight check. Record where hover thrust enters (R25). |
| F5 | A, B | MAJOR | R27, R26 | "Vertical priority + XY margin must be re-done on the INDI thrust vector" is listed but not designed. LIB has tilt and collective clamps (`kMinUpThrust`, `h_max = -t_c(2)*tan(tilt)`, `c_min/c_max`) but no MPC_THR_XY_MARG and no vertical-first saturation order; at `thr_max` saturation the LIB replaces the vector by `(0,0,-c_max)` (lose all xy). Stock keeps a horizontal margin. This changes Position-mode behaviour under heavy climb/wind. | LIB.cpp:276-322 (saturation), :311 (`t_c = (0,0,-c_max)`); PC:163-186 | Port PC:163-186 into the INDI stage operating on t_c (specific thrust units), parameter MPC_THR_XY_MARG scaled by g_t. Test: commanded climb at `thr_max` with xy setpoint keeps the margin. |
| F6 | A, B | MINOR | R4, R50 | `vehicle_local_position_setpoint.thrust[3]` and `acceleration[3]` are filled from the discarded stock `_thr_sp`, not from what is published, so logs/GCS show a thrust that was never commanded. | PC:255-267; MPC:634-637 | Overwrite `thrust` with the INDI thrust vector (NED) and `acceleration` with a_c before publishing. |
| F7 | A | MINOR | R14 | Ramp is run by the stock law with I = 0 (bypass), i.e. a P-only velocity law from 0 thrust (ramp init `-g/MPC_Z_VEL_P_ACC` maps to exactly 0 thrust through PC:220). Stock builds integral action during the ramp; with I = 0 and a wrong MPC_THR_HOVER the vehicle lifts later/earlier than stock and the FLIGHT hand-over (time-based, `progress >= 1`) may happen before lift-off. Not a safety issue (INDI then corrects) but "identical to stock" is not true. | TO:42-46, :112-134; PC:146-150, :220; MPC:575 | State the behaviour and test both hover-thrust errors (+-20 %) for lift-off time and thrust continuity at hand-over, or run INDI from RAMPUP on with the ramp acting on a_ref (it does: `_vel_sp(2)` clamp PC:140 is upstream of a_ref). |
| F8 | B | MAJOR | R33, decision 6 | `vehicle_acceleration` is the sensors-module output after `IMU_ACCEL_CUTOFF` low-pass; `esc_status` is not filtered. "Same filter on a_meas and T_meas" (decision 6) then holds only if the extra lag on a_meas is modelled, otherwise the increment `(a_ref - a_meas)/G` sees a lagged a_meas against a fresh T_meas and over-corrects. The archive avoids this by reading `sensor_combined` plus `estimator_sensor_bias`. Applies to A too, but A's lower rate makes it less visible. | `src/modules/sensors/vehicle_acceleration/VehicleAcceleration.hpp:98-101`; ARCH.hpp:140-143; LIB `setFilter` (hpp:126-131) | Either consume `sensor_combined` + bias as the archive does, or add an explicit delay/filter on mean_u matching the IMU_ACCEL_CUTOFF filter (LIB has `setMeasurementDelay`, max 4 cycles). |
| F9 | B | MAJOR | R41 | The fast stage publishes `vehicle_attitude_setpoint` on every IMU sample. When `vehicle_local_position` stops, the slow stage is silent (inherited, R41) but the fast stage keeps extrapolating a frozen a_ref with jerk feed-forward; mc_att_control has no staleness check and executes it. Stock at least freezes. The candidate only lists "stale slow part" as a test item. | MPC:382, 389 (no else); ATT:327-344 | Fast stage holds the last output (no extrapolation) and stops publishing after N slow cycles missed; define N. |
| F10 | C | BLOCKING | R14, R15 | The take-off ramp is not a velocity-limit feature alone: its initial value `-g/MPC_Z_VEL_P_ACC` yields zero thrust only through the stock chain `a_sp = P*(vz_sp - vz)` -> `T = a_sp*Th/g - Th`. An INDI-native law with its own velocity gain and no Th mapping does not start the ramp at zero thrust: thrust step at RAMPUP entry. C does not say how the ramp is reproduced. | TO:45, :116-130; PC:140, :150, :220; MPC:575 | C must keep the stock bypass law for states < FLIGHT (then it is A with a different in-flight law) or define its own ramp (thrust ramp, not velocity-limit ramp) and justify it against LD in_ground_effect (R44). |
| F11 | C | MAJOR | R18, R9, R28, R31 | Re-implementing validity (`_inputValid`, xy pairing), `constrainXY` priority of position over feed-forward, the z_deriv blend and the decaying limits is listed as cost but no parity test plan exists. Each of these is a mode-transition behaviour (position unlock, altitude->position switch at speed). | PC:127-141, :227-253; MPC:553-577, :581-591 | Keep stock PositionControl for pos/vel (A) and restrict C to the acceleration stage; otherwise list a parity test per item. |
| F12 | all | MINOR | R23, R33 | "vehicle_attitude (or q from local position)": `vehicle_local_position` carries no quaternion, only `heading`/`unaided_heading`. The INDI stage needs the full q to rotate f_b. | `msg/VehicleLocalPosition.msg:42-44` | Subscribe `vehicle_attitude` (as the archive does), staleness rule < 20 ms (HTE precedent, HTE:168). |
| F13 | all | MINOR | R35 | Using `vehicle_attitude.q` for a_meas means a quaternion reset rotates a_meas (xy) by delta_psi in one cycle while a_ref is in the local-position frame that was shifted by `delta_heading`; the two counters (`quat_reset_counter`, `heading_reset_counter`) are published by the same EKF but the candidate handles only the second. One-cycle transient only. | ATT:346-363; MPC:742 | Note it; no action unless the jerk feed-forward amplifies it (F14). |
| F14 | A, B | MINOR | R19, R22 | LIB `j_ref` NaN -> backward difference of a_ref (`_j_diff_f`), clamped to 50 m/s^3. Every step in a_ref (failsafe setpoint, idle (0,0,100) -> flight, fallback re-expression after a reset) produces a jerk pulse. It feeds `omega_ff` only, which `vehicle_attitude_setpoint` cannot carry, so it is wasted CPU, not a hazard; but if a later design maps omega_ff into q_d it becomes one. | LIB.cpp:229-237, :332-337; hpp:65-68 | `setFeedforward(false)` in the attitude-setpoint design, or reset the jerk history on every a_ref discontinuity (mode edge, failsafe entry). |
| F15 | A, B | MINOR | R36 | "125 Hz lockstep SITL" is the only rate measured; on hardware IMU_INTEG_RATE default is 200 Hz and EKF2 timing differs. The preference A vs B is decided on an unmeasured number. | candidates :113-119 | Bring-up checklist item with a go/no-go (phase at the design bandwidth). Acceptable as is. |
| F16 | all | MINOR | R10, R9 | Claim "C must reproduce PC:231-234 exactly" and "A/B inherit": verified; PositionControl returns a_ref untouched by saturation (PC:150-153 before :157-199). Correct. No action. | PC:143-205 | none |
| F17 | A, B | MINOR | R41, R5 | During PC-off the shell publishes `takeoff_status` on change (inherited). But the INDI stage also needs to run `reset()` on the PC-off edge so that the PC-on edge in air starts from measured values rather than the last flight. Not stated. | MPC:403-407 | Add "reset INDI state on PC-off edge" to the shell copy. |

Counts. A: 0 BLOCKING / 5 MAJOR (F1 F2 F3 F4 F5) / 7 MINOR (F6 F7 F12 F13 F14 F15 F17). B: 0 / 7 (A + F8 F9) / 7.
C: 1 BLOCKING (F10) / 4 MAJOR (F2 F3 F5 F11) / 3 MINOR (F12 F13 F15).

## 3. Requirement defects

- **R33 incomplete:** the input list must include `vehicle_thrust_setpoint` for the modelled-actuator seed (F3) and
  `vehicle_attitude` with a staleness rule (F12). "No dependence on inputs mc_pos_control does not have" should be
  reworded as "every new input has a staleness rule and a fallback".
- **R25/R47 as written allow F1:** add "a hover-thrust update must not move the integrator of a loop whose I gain is
  zero" or, better, "hover thrust enters the replacement at exactly one place (named)".
- **R24 is too weak:** it says "consistent" but gives no acceptance test. Add: thrust published at the bypass->INDI
  edge equals the last bypass thrust within x %, with and without telemetry.
- **R1 does not name the archive collision:** add "the archive module `mc_indi_pos_control`, `MC_INDIP_EN` and
  rc.mc_apps:67-71 are renamed or removed; a board builds at most one of them".
- **R14 should say** "ramp starts at zero thrust" explicitly (TO:45 + PC:220), since a replacement law can satisfy the
  velocity-limit wording and still step the thrust (F10).
- **R41 should require** a decision for a module that has a second trigger (B), not only for the local-position one.
- **Missing:** a requirement on `vehicle_local_position_setpoint.thrust/acceleration` reflecting the published command
  (F6, R4/R50 only list the fields).
- **Verified correct, keep:** R34 (ATT:331 timestamp test, :337-342 whole-message drop), R37 (TO:102-104, MPC:645-650),
  R9 correction (PC:231-234), R40 (TO:72-75), R44 (LD:329-334), trajectory-type flags (SPT:75-83 set attitude_enabled,
  so the R-a rejection stands).
- **UNVERIFIED by me:** esc_status rate and per-motor staggering vs the fast stage of B (affects F8); whether
  `IndiRateControl::normalisedThrustFromRpm` is rpm^2-linear (affects F4 scale argument); hardware local-position rate (F15).

## 4. Recommendation

Take **A** to the owner, on these conditions before any code:
1. F2 resolved: new module name and parameter, rc.mc_apps:49 replaced by an if/else, rc.vtol_apps handled, archive kept
   out of the default build.
2. F1 and F4 resolved in the design text: hover thrust enters at one named place; `updateHoverThrust` is not called;
   `g_t*k_cmd` tied to g/hover_thrust or proven equal.
3. F3: `vehicle_thrust_setpoint` input and the list of INDI (re)entry edges with the seed at each one.
4. F5: PC:163-186 ported into the INDI stage, with MPC_THR_XY_MARG.
5. The INDI stage stays a rate-independent class (as proposed) so that B remains a trigger change; B is not accepted
   now because of F8/F9.
C is rejected at this round (F10).
