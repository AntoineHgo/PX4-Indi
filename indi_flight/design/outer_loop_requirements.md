# Outer-loop requirements: replacement of mc_pos_control

Purpose: checklist for any module that replaces `mc_pos_control` (started instead of it by a
parameter, serving every multicopter mode). Source-derived only; no design, no judgement of INDI.
Branch `feat/indi-flight`, code read 2026-11-15.

Path abbreviations (all under `src/modules/` unless absolute):
MPC = `mc_pos_control/MulticopterPositionControl.cpp` (.hpp = MPCh);
PC = `mc_pos_control/PositionControl/PositionControl.cpp`; CMath = `.../PositionControl/ControlMath.cpp`;
TO = `mc_pos_control/Takeoff/Takeoff.cpp`; FMM = `flight_mode_manager/FlightModeManager.cpp`;
LD = `land_detector/MulticopterLandDetector.cpp`; ATT = `mc_att_control/mc_att_control_main.cpp`;
CM = `commander/ModeUtil/control_mode.cpp`; SPT = `commander/ModeUtil/setpoint_types.cpp`;
HTE = `mc_hover_thrust_estimator/MulticopterHoverThrustEstimator.cpp`.
UNVERIFIED = not confirmed in code during this pass.

## 1. Inputs (every uORB topic mc_pos_control subscribes, MPCh:106-114)

| Topic | Fields used | Publisher(s) | Notes |
|---|---|---|---|
| vehicle_local_position (callback, sets run rate) | x,y,z, vx,vy,vz, xy_valid, z_valid, v_xy_valid, v_z_valid, heading, z_deriv, vxy_max, timestamp, timestamp_sample, xy/z/vxy/vz/heading_reset_counter, delta_xy, delta_z, delta_vxy, delta_vz, delta_heading (MPC:305-370, 388-392, 585-591, 718-780) | EKF2 (UNVERIFIED, not grepped) | Run() does nothing unless a new sample arrived (MPC:388); 100 ms backup wake only (MPC:382). dt = clamp(timestamp_sample delta, 2 ms, 40 ms) (MPC:390-391). |
| trajectory_setpoint | position[3], velocity[3], acceleration[3], yaw, yawspeed, timestamp (jerk is log-only) (msg/versioned/TrajectorySetpoint.msg) | FlightModeManager (FMM:364, every local-position update while a task is active); GotoControl inside mc_pos_control itself (GotoControl.hpp:128); mavlink offboard (mavlink/mavlink_receiver.h:407) | NaN = "not controlled" per axis. Read at MPC:444. |
| vehicle_constraints | speed_up, speed_down, want_takeoff, timestamp (msg/VehicleConstraints.msg) | FMM (FMM:367); GotoControl (GotoControl.hpp:129) | Read only while position control is enabled and a valid setpoint exists (MPC:462). |
| vehicle_control_mode | flag_multicopter_position_control_enabled, flag_control_velocity_enabled, flag_control_climb_rate_enabled, flag_control_offboard_enabled, flag_armed, timestamp (MPC:396-418, 437, 448, 471) | Commander::updateControlMode (commander/Commander.cpp:2816-2830) | Enabled flag = rotary wing AND (altitude OR climb_rate OR position OR velocity). |
| vehicle_land_detected | landed, ground_contact (MPC:421, 502, 508) | land_detector (LD) | maybe_landed, freefall, in_ground_effect are NOT read. |
| hover_thrust_estimate | valid, hover_thrust (MPC:423-431) | mc_hover_thrust_estimator (HTE) | Applied only when valid. |
| parameter_update (1 s interval) | triggers parameters_update() (MPC:55-301, 384) | param system | Params listed in section 3, B21. |
| goto_setpoint | consumed by GotoControl (GotoControl.hpp:127; MPC:437-442) | UNVERIFIED (not traced) | Used only when no fresh trajectory_setpoint and pos-ctrl enabled (MPC:437-438). |

NOT subscribed: vehicle_attitude (yaw comes from local_position.heading, MPC:368), vehicle_status,
manual_control_setpoint, vehicle_thrust_setpoint, actuator/allocator feedback. Any replacement that
needs these (e.g. specific force, attitude, thrust feedback) adds new inputs.

## 2. Outputs (every topic published)

| Topic | Fields set | Consumers | Source |
|---|---|---|---|
| vehicle_attitude_setpoint (`mc_virtual_attitude_setpoint` when started as `mc_pos_control start vtol`) | q_d (from thrust vector + yaw_sp), thrust_body[2] = -|thr_sp| (x,y = 0), yaw_sp_move_rate = yawspeed_sp, timestamp. Euler fields absent in this message version. | mc_att_control (mc_att_control.hpp:107, read at ATT:327-341); FlightModeManager.hpp:141; lib/weather_vane/WeatherVane.hpp:69; vtol_att_control (mc_virtual_attitude_setpoint, vtol_att_control_main.h:172); logger | MPC:49-50, 641-643; PC:269-273; CMath:48-51, 62-115. Published ONLY while position control enabled and a valid/failsafe setpoint was processed (MPC:458-643). |
| vehicle_local_position_setpoint | x,y,z (pos sp, NaN if none), vx,vy,vz (velocity sp after position P and limits), acceleration[3] (after PID), thrust[3] (NED, normalized), yaw, yawspeed, timestamp | FlightTask.cpp:193 (velocity_setpoint_feedback, used to initialise the velocity setpoint at position unlock; ignored if older than _timeout); commander FailureDetector.cpp:166 (altitude-loss check); vtol_att_control_main.h:170; logger/mavlink (UNVERIFIED) | MPC:631-637; PC:255-267. MPC:632 comment claims land detector uses it; LD does not (LD.h:93-98 subscribes trajectory_setpoint, vehicle_thrust_setpoint, takeoff_status). |
| takeoff_status | takeoff_state (0..5 enum, msg/TakeoffStatus.msg), tilt_limit (slewed, rad), timestamp | land_detector (LD.cpp:118-119); FMM (FMM:349-360, reactivates task when state < RAMPUP); FlightTaskAuto.hpp:132; ManualAccelerationSlow.hpp:77; StickAccelerationXY.hpp:80; navigator.h:383 | Published on change of state or tilt_limit only, including when position control is disabled (MPC:652-660). Advertised in ctor (MPC:54). |
| trajectory_setpoint + vehicle_constraints (via GotoControl) | position/velocity/acceleration/yaw from goto_setpoint | MPC itself (and everything else subscribed to trajectory_setpoint: land_detector LD.h:95, mc_nn_control, mc_raptor, mc_indi_pos_control) | GotoControl.hpp:128-129; MPC:437-442. |
| mavlink_log_critical + events | parameter clamp warnings | GCS | MPC:170-290. |

Not published by mc_pos_control: vehicle_rates_setpoint, vehicle_thrust_setpoint, actuator_*
(those come from mc_att_control ATT:382-389 and the rate controller).

## 3. Behaviours (one item each, with source)

B1 Scheduling. Work item on `nav_and_controllers` WQ, woken by vehicle_local_position callback, 100 ms
   fallback. dt clamp [2, 40] ms; initial sample interval 10 ms (MPC:51, 64, 382, 390-391).
B2 Control-mode gating. `flag_multicopter_position_control_enabled` rising edge stores
   `_time_position_control_enabled`; falling edge clears the stored setpoint (MPC:400-406).
   Enabled branch MPC:458; else-branch (MPC:645-649) runs takeoff state machine with skip=true,
   want_takeoff=false and resets integrators, publishes no attitude/lpos setpoint.
B3 Restart of decaying velocity limits when position_control_enabled, velocity_enabled or
   climb_rate_enabled changes (MPC:410-417, 547-577).
B4 Take-off state machine (disarmed, spoolup, ready_for_takeoff, rampup, flight): armed -> spoolup;
   COM_SPOOLUP_TIME hysteresis -> ready; want_takeoff -> rampup; ramp progress >= 1 -> flight;
   landed in flight -> ready_for_takeoff; COM_THROW_EN (skip_takeoff) forces flight when armed;
   !armed -> disarmed (TO:48-110; MPC:498-503).
B5 Take-off ramp: upward speed limit starts at -g / MPC_Z_VEL_P_ACC and ramps linearly to the
   constraint speed_up over MPC_TKO_RAMP_T (TO:42-46, 112-134; MPC:575). During rampup, the
   acceleration feed-forward in z is NaN-ed when a z velocity setpoint exists (MPC:517-520).
B6 want_takeoff source: from `vehicle_constraints.want_takeoff` (tasks); in OFFBOARD it is derived
   from the setpoint (position z above current, vz < 0, or az < 0), armed and setpoint < 1 s old;
   OFFBOARD also overrides speed_up/down with MPC_Z_VEL_MAX_UP/DN (MPC:470-497). speed_up NaN or
   > MPC_Z_VEL_MAX_UP is clamped to MPC_Z_VEL_MAX_UP (MPC:464-468).
B7 Pre-flight / ground-contact idle: if state < rampup OR (state >= flight AND ground_contact) the
   setpoint is replaced by all-NaN with acceleration = (0,0,100) (thrust to minimum, level attitude),
   integrators reset, horizontal/vertical acceleration decoupled (MPC:508-529).
   Result in PC:207-225: thrust magnitude = lim_thr_min (1e-3 floor, PC:63-68), body_z straight down.
B8 Landing / land-detector interaction. mc_pos_control consumes only `landed` (B4) and `ground_contact`
   (B7). Land detector consumes trajectory_setpoint.velocity[2] >= 1.1*LNDMC_Z_VEL_MAX as "in_descend"
   (LD.cpp:244-253), vehicle_thrust_setpoint throttle (low-thrust test at 30%/60% of [min, hover]
   range, LD.cpp:231-240; maybe_landed threshold 10% LD.cpp:283-297), takeoff_status.takeoff_state
   (LD.cpp:118) and control_mode.flag_control_climb_rate_enabled (LD.cpp:101-103). So a replacement must
   keep (a) trajectory_setpoint.velocity[2] meaningful (it is an input here), (b) thrust_body scale
   consistent with the hover-thrust definition, (c) takeoff_status published.
B9 Setpoint validity (PC:227-253): every axis needs pos OR vel OR acc finite; x/y finite-ness must pair for
   pos, vel and acc; a finite pos sp needs a finite pos state; a finite vel sp needs finite vel and
   acceleration (derivative) states. update() additionally requires finite acc_sp and thr_sp (PC:111-125).
B10 State validity (MPC:305-370): invalid xy/z position or velocity -> NaN states (so setpoints on that
   axis become invalid, B9); on lost velocity the velocity LP/notch/derivative filters are reset.
B11 Failure cascade (MPC:603-626): update fails -> reuse `_last_valid_setpoint` if < 200 ms old (re-expressed in
   the current EKF frame) -> else generateFailsafeSetpoint(warn) with constraints reset and default
   velocity limits (MPC:622-625).
B12 Failsafe setpoint (MPC:667-713): xy velocity finite -> vxy=0 ("stop and wait"); else acc_xy=0 and
   vz=MPC_LAND_SPEED ("blind land"); z velocity finite -> vz=0 unless set; else acc_z=0.3 m/s^2
   ("blind descent"). Warnings rate-limited to 2 s.
  Corrected (review S4): when vz state is also invalid, `velocity[2] = NAN` and `acceleration[2] = 0.3` replace the blind-land vz = MPC_LAND_SPEED set earlier (MPC:699-709). Blind land only survives when vz is finite. The xy test uses states.velocity (filtered, NaN if invalid).
B13 Stale-setpoint failsafe: if pos-ctrl enabled and no trajectory_setpoint newer than the enable time
   arrived, a failsafe setpoint is generated (MPC:448-456); no output at all until a setpoint with
   timestamp >= enable time exists (MPC:458-459). There is NO timeout on setpoint age once running
   (only the OFFBOARD want_takeoff 1 s test, MPC:473).
  Corrected (review S4): "no output until a setpoint with timestamp >= enable time" holds only for the first cycle(s) (see R42, review Rnew-6). The failsafe setpoint's timestamp is timestamp_sample (MPC:454, 667-679), so output starts the next cycle.
B14 EKF resets (MPC:718-780): when counters differ from latched values, deltas are added to the current and
   fallback setpoints (xy pos, z pos, vxy vel, vz vel, heading wrap_pi) only if setpoint.timestamp is
   nonzero and older than local_position.timestamp; velocity LP filters are shifted by delta_vxy/delta_vz
   and notch filters reset; GotoControl reset handlers called. Integrators are NOT reset.
B15 Hover thrust: starts from MPC_THR_HOVER (clamped to [MPC_THR_MIN, MPC_THR_MAX], MPC:277-286, 292);
   forced back to the parameter whenever not flying (MPC:513-515); in flight, valid estimates call
   updateHoverThrust, which also shifts the z integrator so commanded thrust is continuous
   (PC:75-92; MPC:423-431). Thrust mapping: T = a_z*Th/g - Th (PC:219-221).
B16 Tilt limit: MPC_TILTMAX_LND until state >= flight, then MPC_TILTMAX_AIR; slew-limited to 0.2 rad/s
   (MPC:53, 533-535); MPC_TILTMAX_AIR clamped to MAX_SAFE_TILT_DEG (value UNVERIFIED, in MPCh) and
   MPC_TILTMAX_LND <= AIR (MPC:170-190); limit applied to body_z (CMath limitTilt, PC:217-218).
   Published as takeoff_status.tilt_limit.
  Corrected (review S4): the MAX_SAFE_TILT_DEG value is 89 (MPCh:228), as R26 already states; the UNVERIFIED tag does not apply (internal inconsistency only).
B17 Thrust limits: min = MPC_THR_MIN in flight, 0 (floored 1e-3) before; max MPC_THR_MAX (MPC:540-542; PC:63-68).
   Vertical prioritised with a horizontal margin MPC_THR_XY_MARG; horizontal saturated to remaining
   thrust budget (PC:163-186). Collective thrust = min(thrust_z/cos(tilt), -thr_min) (PC:223).
B18 Velocity limits: xy = MPC_XY_VEL_MAX (min with local_position.vxy_max), up = min(constraint speed_up,
   MPC_Z_VEL_MAX_UP), down = max(constraint speed_down, 0); each is raised to a decaying limit
   (starts at measured speed, held 1 s, then -5 m/s per s) so that mode changes do not saturate
   (MPC:544-577); takeoff ramp applied last to up-limit (MPC:575). Velocity setpoint clamped
   in PC:127-141 (xy prioritises position part over feed-forward).
B19 Position/velocity/acceleration cascade: P position (MPC_XY_P, MPC_Z_P) adds to feed-forward velocity;
   PID velocity (MPC_*_VEL_P/I/D_ACC) adds to feed-forward acceleration; NaN setpoints/states contribute
   nothing (PC:127-205). z integral clamp +-g, z anti-windup on thrust limits, xy tracking anti-windup,
   integrators reset when xy not controlled (MPC:594-599) or not flying (MPC:529). Vertical velocity state
   blended with z_deriv when only vz is commanded (weight |vz_sp|/MPC_LAND_SPEED, MPC:581-591).
B20 Acceleration-to-attitude: specific force = (a_xy, g + a_z) unless decoupled (MPC_ACC_DECOUPLE or
   B7), body_z = -normalise(force), yaw from yaw_sp; NaN yaw_sp -> current heading, NaN yawspeed -> 0
   (PC:119-120, 207-225; CMath:62-115). Near-horizontal thrust: body_x defaulted, yaw ignored (CMath:~85-95).
B21 Velocity filtering: optional notch (MPC_VEL_NF_FRQ/BW), LP (MPC_VEL_LP), derivative LP (MPC_VELD_LP) built
   from measured sample rate (MPC:88-115).
B22 Yaw: no yaw control in this module; yaw and yawspeed pass from trajectory_setpoint to attitude
   setpoint (yaw_sp, yaw_sp_move_rate); heading reset delta added to yaw sp (MPC:742).
B23 Manual altitude / position modes: not implemented here; FMM tasks turn sticks into trajectory_setpoint
   (B-table 5). This module cannot tell manual from auto except flag_control_offboard_enabled (B6).
B24 Disarmed: takeoff state forced disarmed (TO:107); with pos-ctrl enabled the B7 idle setpoint is still
   published as attitude setpoint (level, thrust ~1e-3); with it disabled nothing is published (B2).
B25 Parameter updates: all gains, limits, filters re-read at runtime incl. SYS_VEHICLE_RESP and MPC_XY_VEL_ALL /
   MPC_Z_VEL_ALL which overwrite many MPC_* values (MPC:118-166); invalid combinations are clamped back
   and written to storage with a user message (MPC:170-290); takeoff params refreshed (MPC:299-301).
B26 Goto support: GotoControl turns goto_setpoint into trajectory_setpoint/vehicle_constraints while pos-ctrl
   enabled and no external trajectory_setpoint is updating (MPC:437-442).
B27 VTOL variant: `mc_pos_control start vtol` publishes mc_virtual_attitude_setpoint (MPC:49-50;
   ROMFS rc.vtol_apps:20). UNVERIFIED whether any other module checks that mc_pos_control is running.
B28 Not done by this module (do not infer): navigation, stick mapping, yaw-rate integration, mode
   selection, arming, rate/thrust allocation, land-state computation.

## 4. What mc_att_control adds downstream (ATT)

A1 Consumes vehicle_attitude_setpoint (q_d, yaw_sp_move_rate, thrust_body) only when
   flag_control_attitude_enabled AND hovering multicopter (not VTOL transition) (ATT:304-310, 327-341).
   Messages with timestamp not newer than the last one are ignored; a message with invalid q_d is dropped
   whole, thrust included (ATT:331, 337-341).
A2 Attitude P controller (attitude error -> body rate setpoint) with MC_ROLL_P/PITCH_P/YAW_P, rate limits,
   and MC_YAW_WEIGHT (reduces yaw priority when tilt error is large) (ATT:~90-96, `_attitude_control.update`
   ATT:366). yaw_sp_move_rate is used as yaw-rate feed-forward. Gains/algorithm internals UNVERIFIED
   (AttitudeControl library not read).
A3 Heading reset: when vehicle_attitude.quat_reset_counter changes, the stored setpoint is rotated by
   delta_q_reset (ATT:346-363). So an outer loop must NOT also compensate quaternion resets twice.
A4 Thrust: passes thrust_body (3 floats, only z set by mc_pos_control) unchanged into
   vehicle_rates_setpoint.thrust_body (ATT:386); no hover-thrust scaling in the auto path. The rate
   controller turns it into vehicle_thrust_setpoint (consumed by land detector and HTE). Its scale is
   "normalised thrust, hover = hover_thrust" (PC:219-221).
A5 Stabilized / manual bypass: when flag_control_manual_enabled and altitude, velocity and position flags are
   all false, mc_att_control generates the attitude setpoint itself from sticks (tilt MPC_MAN_TILT_MAX, yaw
   stick via StickYaw, throttle curve MPC_THR_CURVE/MPC_MANTHR_MIN, hover thrust from the estimator clamped
   to [0.05, 0.9]) and publishes vehicle_attitude_setpoint itself (ATT:119-141, 145-212, 236-246,
   312-317). Mode STAB maps to Attitude type, so flag_multicopter_position_control_enabled is false and
   mc_pos_control is silent (CM:65-68; Commander.cpp:2826). Two publishers, mutually exclusive by flags.
A6 When attitude control is disabled (e.g. Acro, offboard rates) stick filters/yaw reset (ATT:391-396).
A7 Landed handling: manual throttle minimum goes to 0 when landed (ATT:398-403); spooled-up gating of manual
   max throttle (ATT:405-409).
A8 Autotune offsets added to the rate setpoint (ATT:370-379), only while autotune active.
A9 Hover thrust estimate is used here for manual stick scaling only (ATT:236-246), not in the auto path.

## 5. Mode table

Flags: CM/SPT. "PC on" = flag_multicopter_position_control_enabled (Commander.cpp:2826). Trajectory type
= allocation, rates, attitude, altitude, velocity, position, climb_rate all true (SPT:75-83).

| Mode (nav_state) | Flags (summary) | PC on? | Modules producing the command | Topic carrying it |
|---|---|---|---|---|
| Manual (MANUAL, PARKING) | manual; Attitude type if stabilization_required else ThrustAndTorque (CM:52-63; stabilization_required value for MC UNVERIFIED) | no | mc_att_control (stick->att sp) + rate ctrl | vehicle_attitude_setpoint (ATT) |
| Stabilized (STAB) | manual + Attitude (CM:65-68) | no | mc_att_control | vehicle_attitude_setpoint from mc_att_control |
| Acro (ACRO) | manual + Rates (CM:95-98) | no | rate controller reads sticks (UNVERIFIED) | vehicle_rates_setpoint / manual_control_setpoint |
| Altitude (ALTCTL), Altitude cruise | manual + Trajectory with velocity/position off (CM:70-76) | yes (altitude, climb_rate) | FMM task ManualAltitude(SmoothVel) per MPC_POS_MODE (FMM:236-249); AltitudeCruise (FMM:256-260) | trajectory_setpoint (z-only valid, xy NaN), vehicle_constraints |
| Position (POSCTL) | manual + Trajectory (CM:78-82) | yes | FMM task ManualAcceleration (default, MPC_POS_MODE 4) or ManualPosition (0) (FMM:210-229) | trajectory_setpoint (accel/vel/pos mix), vehicle_constraints |
| Position slow | same flags | yes | ManualAccelerationSlow (FMM:203-207) | trajectory_setpoint |
| Hold/Loiter, Mission, RTL, Land, PrecLand, Takeoff, Guided course | PositionTriplet type (CM:84-93; flag set UNVERIFIED, SPT PositionTriplet not read in full; one position_enabled found) ; auto_enabled | yes | Navigator -> FMM Auto task (FMM:192-200) (position_setpoint_triplet publisher UNVERIFIED) | trajectory_setpoint, vehicle_constraints (want_takeoff) |
| Descend (failsafe) | auto + climb_rate + attitude + rates only (CM:100-106) | yes (climb_rate) | FMM Descend task (FMM:266-274) | trajectory_setpoint (xy handling of Descend task UNVERIFIED) |
| Follow target, Orbit | Trajectory, manual off (CM:146-153) | yes | FMM AutoFollowTarget / Orbit (FMM:160-185) | trajectory_setpoint |
| Task failure | any | yes | FMM Failsafe task (FMM:276-279) publishes all-NaN setpoint (FMM:339-347) -> MPC failsafe B12 | trajectory_setpoint (empty) |
| Offboard position | offboard + Trajectory (CM:115-116) | yes | MAVLink receiver -> trajectory_setpoint (mavlink_receiver.h:407); no FMM task matches (FMM:281-283, inferred) | trajectory_setpoint; vehicle_constraints overridden in MPC:470-497 |
| Offboard velocity | Trajectory, position off (CM:118-120) | yes | as above | trajectory_setpoint |
| Offboard acceleration | Trajectory, then velocity=true, position/altitude/climb_rate=false (CM:122-129) | yes (via velocity) | as above | trajectory_setpoint.acceleration (no dedicated flag) |
| Offboard attitude | Attitude type (CM:131-132) | no | MAVLink -> vehicle_attitude_setpoint (mavlink_receiver.h:402; consumption UNVERIFIED) | vehicle_attitude_setpoint |
| Offboard rates / thrust_and_torque / direct_actuator | Rates / ThrustAndTorque / DirectActuators (CM:134-141) | no | MAVLink -> rates / thrust-torque / actuators | respective topics |
| External modes 1-8 | per registered setpoint type (CM:155-157); FMM runs no task (FMM:143-145) | if Trajectory/Goto type | external mode (px4-ros2) UNVERIFIED | trajectory_setpoint or goto_setpoint |
| Termination | all flags false (CM:108-110) | no | none | none |
| VTOL hover | same, pos-ctrl started with `vtol` | yes | as above | mc_virtual_attitude_setpoint -> vtol_att_control |
| RC-loss / data-link-loss failsafes | Commander picks nav_state (RTL, Land, Hold, Descend, Terminate: choice per COM_* params UNVERIFIED) | per row above | per row above | per row above |

Startup precedent: rc.mc_apps:15-19 already chooses `mc_indi_rate_control` vs `mc_rate_control` by param
MC_INDI_EN; `mc_pos_control start` is unconditional at rc.mc_apps:49; MC_INDIP_EN block at rc.mc_apps:68-70
starts an existing `mc_indi_pos_control` (src/modules/mc_indi_pos_control, archive) IN ADDITION to mc_pos_control;
their output arbitration is UNVERIFIED.

## 6. Requirements checklist

Each item is testable by SITL (uORB echo/log) or unit test. "Src" gives the behaviour it mirrors.

Interfaces
- R1 Start: exactly one of {mc_pos_control, replacement} runs, selected by a parameter in rc.mc_apps; the
  other is not started. Test: `ps`/`mc_pos_control status` for both param values. Src: rc.mc_apps:15-19, 49.
- R2 Run trigger: execute on each vehicle_local_position update (callback) with a slow fallback wake; dt
  derived from timestamp_sample and clamped to [2, 40] ms. Src: MPC:64, 382, 390-391.
- R3 Publish vehicle_attitude_setpoint (q_d unit quaternion, thrust_body[2] <= 0 normalised, x,y = 0,
  yaw_sp_move_rate, timestamp) only while PC-on; use mc_virtual_attitude_setpoint under the `vtol`
  argument. Src: MPC:49-50, 641-643; PC:269-273. Test: rate and absence when PC off.
- R4 Publish vehicle_local_position_setpoint with x,y,z (NaN if uncontrolled), vx,vy,vz, acceleration[3],
  thrust[3], yaw, yawspeed at each active cycle; vx,vy,vz must be the velocity setpoint actually tracked
  (FlightTask uses it to seed position unlock) and z/vz finite whenever altitude is controlled
  (FailureDetector alt-loss). Src: MPC:631-637; FlightTask.cpp:193-200; FailureDetector.cpp:160-185.
- R5 Publish takeoff_status (state enum 0-5 with identical semantics, tilt_limit) on change, also when PC
  off; advertise at construction. Consumers LD, FMM, Auto task, navigator depend on it. Src: MPC:54,
  652-660; LD.cpp:118; FMM:349-360.
  Corrected (review S4): published values are 1..5 (disarmed=1, spoolup=2, ready=3, rampup=4, flight=5). 0 is UNINITIALIZED and is never produced by TakeoffState (msg/TakeoffStatus.msg:5-10; Takeoff.hpp:48-54). Consumers compare `< RAMPUP` (=4) (FMM:357).
- R6 Keep consuming trajectory_setpoint (pos/vel/acc/yaw/yawspeed, any axis NaN) and vehicle_constraints
  unchanged; no change to FlightModeManager, Navigator or mavlink offboard. Src: sec. 1.
- R7 Provide goto_setpoint behaviour (GotoControl) or explicitly record that it is dropped;
  trajectory_setpoint/vehicle_constraints publication by GotoControl is part of the contract. Src: MPC:437-442.

Mode coverage
- R8 Active in every mode where flag_multicopter_position_control_enabled is true (altitude, position,
  auto, descend, orbit, follow, offboard pos/vel/acc, external trajectory/goto) and silent (no
  vehicle_attitude_setpoint) otherwise, so that mc_att_control's stabilized path and offboard attitude
  keep sole ownership. Src: Commander.cpp:2826; CM; ATT:312-317.
- R9 Altitude-only control (xy setpoints NaN, ALTCTL) and climb-rate-only (DESCEND) must be handled: an
  axis with all-NaN setpoint is left uncontrolled with no integrator build-up, while a valid setpoint
  on the remaining axes still yields a valid output. Src: PC:227-253, MPC:594-599; CM:70-76, 100-106.
  Corrected (review S4): an axis with all of pos/vel/acc NaN makes the whole setpoint INVALID (PC:231-234, "every axis x, y, z needs to have some setpoint"). Altitude and Descend modes work because xy carries an ACCELERATION setpoint (Descend: FlightTaskDescend.cpp:64, 72). xy pos/vel NaN with finite acc is the "uncontrolled" case and only resets the xy integrator (MPC:594-599). A candidate must not assume xy can be omitted entirely (ManualAltitude xy output not read; inferred from PC:231-234).
- R10 Offboard acceleration setpoints (xy+z acceleration only, no velocity/position) are executed as an
  acceleration command; pos/vel/acc may be mixed per axis and xy must come in pairs. Src: PC:233-239;
  CM:122-129.
- R11 In OFFBOARD derive want_takeoff from the setpoint (z up, vz<0 or az<0, armed, setpoint < 1 s old) and
  override speed_up/down with maxima. Src: MPC:470-497.
- R12 VTOL start argument supported or explicit non-goal. Src: MPC:49-50; rc.vtol_apps:20.

Take-off, landing, ground
- R13 Reproduce the 6-state take-off machine (disarmed..flight) with COM_SPOOLUP_TIME, want_takeoff,
  landed->ready, COM_THROW_EN, !armed->disarmed. Test: state sequence on arm/take-off/land/disarm.
  Src: TO:48-110.
- R14 Take-off ramp: vertical-speed limit from -g/MPC_Z_VEL_P_ACC to constraint speed_up over MPC_TKO_RAMP_T,
  with z acceleration feed-forward suppressed during ramp; no thrust jump at end of ramp. Src: TO:42-46,
  112-134; MPC:517-520, 575.
- R15 Before RAMPUP and in flight with ground_contact=true: output level attitude, thrust at the minimum
  (>0, 1e-3 floor), integrators zero, no horizontal correction. Src: MPC:508-529; PC:63-68.
- R16 Ground/idle thrust must satisfy the land detector's thrust test (thrust <= min + 10-60% of
  [min, hover]); landing descent must show trajectory_setpoint.velocity[2] semantics unchanged
  (LD reads it, not the output). Src: LD.cpp:231-297, 244-253.
- R17 Respect `landed` and `ground_contact`; do not require maybe_landed. Src: MPC:421, 502, 507.

Validity, failsafe, resets
- R18 Setpoint validity rules identical to PC:227-253 (per-axis coverage, xy pairing, state finite where a
  setpoint is finite). Test: unit tests with NaN patterns.
- R19 On invalid input: reuse last valid setpoint if < 200 ms old, else failsafe setpoint (stop xy / blind
  land / blind descent a_z=0.3), never output NaN to vehicle_attitude_setpoint; warnings rate-limited 2 s.
  Src: MPC:603-626, 667-713; PC:123-124.
  Corrected (review S4): "never output NaN" is a design property, not a guard: the result of the last `_control.update` is not checked (MPC:627). Safety comes from the failsafe setpoint being finite by construction.
- R20 No setpoint after PC enabled -> failsafe setpoint; no output until a setpoint with timestamp >=
  enable time exists; setpoint cleared on PC disable. Src: MPC:400-406, 448-459.
  Corrected (review S4): "no output until a setpoint with timestamp >= enable time" holds only for the first cycle(s) (see R42, review Rnew-6). The failsafe setpoint's timestamp is timestamp_sample (MPC:454, 667-679), so output starts the next cycle.
- R21 NaN/invalid estimate handling: invalid vxy -> NaN state and filter reset, invalid vz likewise; do
  not propagate NaN into the output. Src: MPC:305-370.
- R22 EKF reset handling for xy, z, vxy, vz and heading counters: shift setpoint and stored fallback by the
  deltas (only if setpoint older than the position sample), shift/reset velocity filters, wrap yaw; no
  integrator spike across a reset. Test: inject resets in SITL. Src: MPC:718-780.
- R23 Heading input from vehicle_local_position.heading (no vehicle_attitude subscription needed) and
  yaw/yawspeed passed through: NaN yaw -> hold current heading, NaN yawspeed -> 0. Src: MPC:368;
  PC:119-120.

Limits and thrust model
- R24 Thrust mapping consistent with hover thrust: thrust_body magnitude = a*Th/g - Th scale, used by
  land detector, HTE and rate controller. HTE needs |thrust| and az to be consistent, so changing the
  scale breaks hover_thrust_estimate. Src: PC:219-221; HTE:158-200.
- R25 Use hover_thrust_estimate when valid, MPC_THR_HOVER otherwise and when not flying, clamped to
  [THR_MIN, THR_MAX]; no thrust step on estimate change. Src: MPC:277-292, 423-431, 513-515; PC:75-92.
- R26 Tilt limit: MPC_TILTMAX_LND until flight, MPC_TILTMAX_AIR after, slew 0.2 rad/s, clamped <= 89 deg
  (MAX_SAFE_TILT_DEG), land <= air; the commanded tilt never exceeds the published tilt_limit. Src:
  MPC:53, 170-190, 533-535; MPCh:228.
- R27 Thrust limits MPC_THR_MIN (in flight) / MPC_THR_MAX with vertical priority and MPC_THR_XY_MARG.
  Src: MPC:540-542; PC:163-186.
- R28 Velocity limits MPC_XY_VEL_MAX (and vxy_max), MPC_Z_VEL_MAX_UP/DN, constraints speed_up/down, with the
  decaying limit on mode change (no integrator saturation after switching). Src: MPC:544-577.
- R29 Honour acceleration/jerk-related parameters that remain meaningful (MPC_ACC_DECOUPLE for z/xy
  coupling) or document the replacement parameters. Src: MPC:511; PC:207-225.
- R30 Parameter updates take effect at runtime without restart, including SYS_VEHICLE_RESP /
  MPC_XY_VEL_ALL / MPC_Z_VEL_ALL remapping and the clamping warnings. Src: MPC:55-301.
- R31 Vertical velocity state blended with z_deriv when only vz is commanded. Src: MPC:581-591.

Arming / system
- R32 Disarmed: takeoff state = disarmed, output idle (level, minimum thrust) while PC-on, nothing while
  PC-off. Src: TO:107; MPC:645-649.
- R33 No dependence on inputs mc_pos_control does not have unless added explicitly (attitude, IMU
  specific force, thrust feedback); any such addition needs staleness handling. Src: sec. 1.
- R34 Outputs must be accepted by unmodified mc_att_control: new q_d each cycle, increasing timestamp, valid
  unit quaternion (else the whole message incl. thrust is dropped). Src: ATT:331-341.
- R35 Heading/quaternion reset is handled once, in mc_att_control (ATT:346-363); the outer loop only
  handles local_position resets (R22).
- R36 Run-time cost: stays within the work-queue budget at the local-position rate (typical 50-100 Hz);
  perf counter present. Src: MPC:372-388 (cycle perf). Rate itself UNVERIFIED (EKF publish rate).

From review (S4)
- R37 BLOCKING: The takeoff state machine must also run while PC is disabled, with skip_takeoff=true and want_takeoff=false. Armed therefore forces state FLIGHT (TO:102-104), so Manual/Stabilized to Altitude/Position in air does not re-enter spoolup/ramp or idle thrust. On the ground, landed then drops FLIGHT to ready_for_takeoff on the first PC-on cycle (TO:91-95). R13 and R32 do not state this. (MPC:645-650; TO:102-104)
- R38 BLOCKING: SYS_VEHICLE_RESP, MPC_XY_VEL_ALL and MPC_Z_VEL_ALL are applied by mc_pos_control as writes to params owned by other consumers: MPC_ACC_HOR, MPC_ACC_HOR_MAX, MPC_MAN_Y_MAX, MPC_MAN_Y_TAU, MPC_TILTMAX_AIR (seen) and further ones declared at MPCh:186-197. If the replacement does not perform this remap, the knobs silently stop working for the flight tasks. R30 treats them as the module's own params. Whether the FMM tasks read these params was not grepped. (MPC:118-134, 166-168; MPCh:186-197)
- R39 MINOR: mc_pos_control also enforces cross-module parameter sanity and commits to storage: tilt air <= 89 and land <= air, MPC_XY_CRUISE <= MPC_XY_VEL_MAX, MPC_VEL_MANUAL/BACK/SIDE, MPC_Z_V_AUTO_UP/DN <= MAX_UP/DN, MPC_THR_HOVER within [MIN, MAX]. MPC_TKO_SPEED and MPC_LAND_SPEED are clamped locally only (no commit). Without this, tasks see unvalidated limits. (MPC:170-290, 296-297)
- R40 BLOCKING: Takeoff can start only from want_takeoff in vehicle_constraints (ready_for_takeoff to rampup, TO:72-75). Producers are FlightTaskAuto (FlightTaskAuto.cpp:236, 276: unsmoothed vz < -0.3), ManualAltitude (:316), ManualAcceleration (:93), AutoFollowTarget (:480), and OFFBOARD derived in MPC:470-492. The default is false (FlightTask.cpp:224). R11 covers only offboard; the replacement must keep reading constraints.want_takeoff as the sole trigger. Before rampup the output is idle for every mode (MPC:505, 522-526).
- R41 BLOCKING: Outputs and takeoff_status are produced only inside `if (_local_pos_sub.update(...))` (MPC:389-662) and there is no else. If vehicle_local_position stops, the 100 ms backup wake (MPC:382) publishes nothing: no attitude setpoint, no vehicle_local_position_setpoint, no takeoff_status. ATT then holds the last thrust_body/q_d (ATT:327-344 has no staleness check in the lines read). A replacement needs an explicit decision on a stale local position, since the existing module offers no protection beyond Commander. (ATT staleness handling elsewhere unverified.)
- R42 MINOR: The failsafe setpoint is LATCHED. After the enable edge with no trajectory_setpoint, MPC:451-455 stores a failsafe setpoint stamped with timestamp_sample. From the next cycle `_setpoint.timestamp >= _time_position_control_enabled`, so that frozen setpoint is reused until a real trajectory_setpoint arrives. It is not regenerated each cycle. (MPC:451-459)
- R43 MINOR: In OFFBOARD, constraints.want_takeoff and speed limits are overwritten every cycle after the speed_up clamp. speed_down NaN falls back to MPC_Z_VEL_MAX_DN (MPC:537-538). On the failsafe path constraints are reset to `{0, NAN, NAN, false}` (MPC:622). (R6 and B6 mention only part.)
- R44 MINOR: LD derives in_ground_effect from takeoff_state (RAMPUP always; FLIGHT if below LNDMC_ALT_GND_EFFECT height; also in_descend and no horizontal movement). takeoff_status must therefore stay in RAMPUP for the whole ramp. (LD:329-334, 116-120)
- R45 MINOR: takeoff_status.tilt_limit is consumed by StickAccelerationXY to cap Position-mode stick acceleration at tan(tilt_limit)*g (StickAccelerationXY.cpp:193-200). It must be published, and slewed at 0.2 rad/s from MPC_TILTMAX_LND to AIR. R5/R26 list the field but not this consumer; the default when no message exists was not checked.
- R46 MINOR: LD and HTE depend on parameters and signals the outer loop's thrust scale must match. LD uses MPC_THR_HOVER and MPC_THR_MIN (via `_params`) and hover_thrust_estimate directly in its low-throttle thresholds (LD:105-114, 222-234, 287-288). HTE starts from MPC_THR_HOVER, bounds the estimate by +/-HTE_THR_RANGE (HTE:72, 90-91), only runs when armed and `_in_air` (dist_bottom > 1 m, HTE:128-132, 158), and needs vehicle_thrust_setpoint and vehicle_attitude fresh within 20 ms plus control_allocator_status (HTE:165-172). It fuses -local_pos.az against allocated thrust (HTE:190). Extends R24.
- R47 MINOR: The hover-thrust estimate is pushed into the controller on every valid message (MPC:423-431), but MPC_THR_HOVER overwrites it each cycle until state is FLIGHT (MPC:513-515). The estimate therefore takes effect only once flying. The z integrator is shifted on each update so thrust stays continuous (PC:75-92). R25 states the end result, not this ordering.
- R48 MINOR: z and vz validity are independent (MPC:320, 348; EKF2.cpp:1731 TODO says modules do not always handle v_z_valid != z_valid). The z_deriv blend requires both z_valid and v_z_valid (MPC:582-584). R21/R31 do not state the independence.
- R49 MINOR: GotoControl detail beyond R7. The goto setpoint times out after 500 ms and is cleared when disabled (GotoControl.cpp:51-65). It runs only when no new trajectory_setpoint arrived this cycle (MPC:437-438). Its smoother is reset on invalid position (GotoControl.cpp:79-89) and on EKF resets (MPC:754-778).
- R50 MINOR: vehicle_local_position_setpoint consumers beyond R4: mavlink POSITION_TARGET_LOCAL_NED and POSITION_TARGET_GLOBAL_INT streams, so GCS shows setpoints (streams/*.hpp:58, :62). FlightTask applies a timeout (`_timeout`) and sets the feedback to NaN when stale (FlightTask.cpp:193-201).
- R51 MINOR: Build and start integration: voxl2 start scripts also start mc_pos_control (see (a)-11), and the VTOL script starts it with `vtol` (rc.vtol_apps:20). A replacement must be wired into each, plus board px4board and linker lists (not grepped).

## 7. UNVERIFIED summary
Publisher of vehicle_local_position (assumed EKF2); publisher of goto_setpoint and external-mode
trajectory_setpoint; MAVLink offboard attitude path; PositionTriplet and stabilization_required flag
details (SPT, CM); Descend task xy behaviour; Acro rate path; AttitudeControl internals (yaw weight,
gains); failsafe-to-nav_state mapping (COM_*); arbitration between existing mc_indi_pos_control and
mc_pos_control; whether other modules check that mc_pos_control runs; logger/mavlink consumers.

Resolutions: see outer_loop_requirements_review.md section (a); still unknown: Acro rate path (a-7); AttitudeControl internals (a-8); COM_* failsafe-to-nav_state mapping (a-9); setpoint type registered by mc_indi_pos_control, arbitration partial (a-10); Descend xy selection between FlightTaskDescend.cpp:64 and :72 (a-6); non-VTOL branch of the MAVLink attitude publish (a-3); logger consumers of vehicle_local_position_setpoint (a-12); vehicle_local_position publish rate (R36); whether FMM tasks read the SYS_VEHICLE_RESP-remapped params (R38); ManualAltitude/ManualAcceleration xy outputs and FlightTaskOrbit takeoff (d); FlightModeManager.hpp:141, WeatherVane.hpp:69, vtol_att_control mc_virtual consumption and board CONFIG_MODULES_* lists (d); ATT behaviour on a stale vehicle_attitude_setpoint (d); GotoControl internals beyond lines 50-100 and PositionControl/ControlMath thrustToAttitude near-horizontal behaviour (d).
