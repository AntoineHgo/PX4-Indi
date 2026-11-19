# G5 build list: INDI outer loop serves every mc_pos_control mode (S129)

Architecture: base A (D-outer-arch, DECISIONS.md:76-83): stock position/velocity cascade, then an acceleration INDI
stage; A18 flatness feed-forward only after base A. Requirements: `design/outer_loop_requirements.md` (REQ, cited by
section/B-item). Code read at HEAD 10d3a0e8ac. No build, no flight in this session.

Abbreviations: IPC = `src/modules/mc_indi_pos_control/McIndiPosControl.cpp`, IPCh = `.hpp`, MPC =
`src/modules/mc_pos_control/MulticopterPositionControl.cpp`, RCA = `ROMFS/px4fmu_common/init.d/rc.mc_apps`.

## 0. Structural fact (changes the shape of the work)

IPC is a fork of MPC with the INDI stage inserted after `PositionControl::update` (IPC:858-888). It links the stock
`GotoControl PositionControl Takeoff` libraries (CMakeLists.txt, target_link_libraries) and runs the same
sequence as MPC: control-mode gating (IPC:628-655), takeoff state machine (IPC:737-739), idle setpoint
(IPC:757-765), limits (IPC:768-812), failure cascade (IPC:858-881), EKF-reset handling (IPC:682, 978-1041),
failsafe setpoint (IPC:927-976), takeoff_status (IPC:912-921). Every mode that reaches the module through
`trajectory_setpoint` + `vehicle_control_mode` therefore already gets stock behaviour; the open question per mode is
only what the INDI stage does on top (`want_indi`, IPC:836-840, and `can_run`, IPC:200) and whether that has been
flown. Started instead of MPC by `MC_INDI_POS_EN` (RCA:57-62; yaml MC_INDI_POS_EN default 0, reboot_required).
Built only in `boards/px4/sitl/default.px4board:44`; no hardware board enables it (grep of boards/, only that hit).

INDI stage activation (IPC:836-840): armed AND (position OR velocity OR climb_rate control flag) AND takeoff state
== flight AND not ground-contact. `z_only` (IPC:232) when neither position nor velocity flag: thrust direction stays
stock, collective from INDI (D-ALTCTL-Z, DECISIONS.md:550-562). Else full 3-axis stage on `a_ref` = stock commanded
acceleration `local_pos_sp.acceleration` (IPC:197, 227). Bypass = stock PID attitude setpoint published unchanged
(IPC:287-295).

## 1. Mode table

Flags: REQ section 5 (CM = commander/ModeUtil/control_mode.cpp, FMM = flight_mode_manager). "PC" =
`flag_multicopter_position_control_enabled`. Status words: SERVED = code path exists and no change needed to be
correct; FLOWN = a result set exists that used this mode with INDI pos (only OFFBOARD position setpoints are
known flown: the bench runner arms and enters offboard, run_scenario.py:100-115; others UNVERIFIED, see section 4).

| Mode / failsafe | Setpoint producer | Flags (PC, other) | IPC today | Gap | Smallest change |
|---|---|---|---|---|---|
| Manual, Stabilized | none from pos ctl; mc_att_control makes the attitude sp from sticks (REQ A5) | PC off, attitude type (CM:52-68) | IPC does nothing: else-branch IPC:905-910 only runs takeoff state with skip=true and resets integral. No INDI stage (want_indi needs a flag, IPC:836). Rate loop is mc_indi_rate_control, independent | none in IPC. Hover-thrust scaling lives in mc_att_control (REQ A9) | none; smoke flight only (G5 cell) |
| Acro | none; rate controller reads sticks (REQ section 5, UNVERIFIED) | PC off, rates type (CM:95-98) | same else-branch IPC:905-910 | none in IPC | smoke flight only |
| Altitude (ALTCTL), altitude cruise | FMM ManualAltitude(SmoothVel) / AltitudeCruise (FMM:236-260) -> trajectory_setpoint z only, xy NaN; vehicle_constraints | PC on, climb_rate on, velocity/position off | z-only INDI stage (IPC:232, D-ALTCTL-Z); xy stock thrust dir; tilt/limits IPC:187-188 | G5 flight of ALTCTL with z transient at the switch is the stated overturn (DECISIONS.md:558); UNVERIFIED flown (scenario `s5_gap085_altctl`, scenarios.py:186) | none in code; fly it (S131 probe) |
| Position (POSCTL), slow | FMM ManualAcceleration / ManualPosition (FMM:203-229) -> trajectory_setpoint (acc/vel/pos mix) | PC on, velocity+position on | full stage (IPC:836-851, 229-241), a_ref = stock acc | S129 POSCTL smoke pending (STATE.md:57). Pos-hold with centred sticks unflown. Hold needs `want_takeoff` from FMM for stick takeoff (REQ B6) | fly `s5_gap085_posctl` (scenarios.py:190) |
| Hold/Loiter | Navigator triplet -> FMM Auto task (FMM:192-200) -> trajectory_setpoint | PC on, position type (CM:84-93) | full stage | none in code; unflown (UNVERIFIED) | smoke: arm, offboard-free HOLD via `commander mode auto:loiter` |
| Mission | Navigator -> FMM Auto | as Hold | full stage, trajectory acc/jerk feed-forward in `a_ref` | unflown; mission corner speed/accel limits come from stock MPC_* (IPC:195-243) not from INDI | smoke: 4-waypoint square mission |
| Return (RTL) | Navigator RTL -> FMM Auto | as Hold | full stage | unflown. Land phase at the end uses vz sp, see Land | smoke: trigger RTL at 20 m |
| Take-off (AUTO) | Navigator takeoff -> FMM Auto, `vehicle_constraints.want_takeoff` | as Hold | rampup uses stock PID with bypass (IPC:836-840 requires state == flight; ramp IPC:810). Stage engages at state flight: first-cycle handover resets integral (IPC:851-853) and reseeds filters via `_indi.reset` during bypass (IPC:293) | handover thrust step at rampup -> flight not measured (UNVERIFIED); no test | S130 task T3 |
| Land | Navigator land -> FMM Auto; vz = MPC_LAND_SPEED with altitude-dependent speed | as Hold | full stage until `ground_contact` then bypass + idle setpoint (IPC:743, 757-765). Blend frozen when landed/maybe_landed (IPC:246) | touchdown to disarm: INDI stage bypass edge unflown; `_indi.reset` keeps blend (IPC:287-293). UNVERIFIED | S130 task T4 |
| Precision land, Orbit, Follow target, Guided course | Navigator / FMM tasks (REQ section 5) | PC on | full stage | none expected; not in the owner's list, no smoke | skip, note in G5 list |
| Descend (failsafe) | FMM Descend task (FMM:266-274) | climb_rate only (CM:100-106) | z-only stage (DECISIONS.md:560-562, "G5 flies it") | xy handling of the Descend task UNVERIFIED (REQ section 5); unflown | S130 task T5 |
| RC loss / data-link loss | Commander picks nav_state (RTL, Land, Hold, Descend per COM_*, REQ section 5) | per target row | per target row | no module-level gap; the rows above carry it | smoke: RC loss -> RTL and -> Land via param |
| Task failure / no setpoint | FMM Failsafe task all-NaN setpoint (REQ section 5) or no setpoint after enable | PC on | failsafe setpoint IPC:927-976 (stop and wait / blind land / blind descent, same logic as MPC:667-713) | in the blind-descent branch `a_ref` is acc only (IPC:960-970); stage run on it, effect UNVERIFIED | T5 test |
| Offboard position / velocity / acceleration | MAVLink -> trajectory_setpoint (REQ section 5) | offboard + trajectory type | `want_takeoff` derived from the setpoint, speed limits overridden (IPC:706-733); full stage | FLOWN: it is the bench path (run_scenario.py:100-115). Acceleration offboard has no dedicated flag (velocity true, REQ section 5) UNVERIFIED flown | S131 task T7 |
| Offboard attitude / rates / thrust_and_torque / direct actuators | MAVLink -> respective topics; PC off | CM:131-141 | else-branch IPC:905-910; nothing published | none in IPC; attitude sp consumed by mc_att_control | smoke only, T8 |
| External modes 1-8, goto_setpoint | px4-ros2 / goto (REQ section 5, UNVERIFIED producer) | Trajectory or Goto type | GotoControl hooked (IPC:671-678), params pushed (IPC:430-437), EKF handlers (IPC:1041 region) | none in code; unflown | out of the owner's list; T7 notes only |
| VTOL hover | pos ctl started with `vtol` | PC on | `vtol` arg handled (IPC:49, 1043-1050); rc.vtol_apps not changed | the INDI rate path would also need to serve vtol; UNVERIFIED | out of scope, not on the list |
| Termination | none | all flags false (CM:108-110) | else-branch | none | none |

Count: of the 10 owner modes (manual/stab, acro, altitude, position, hold, mission, return, land, take-off, offboard)
plus 2 failsafe groups (descend, RC/data-link loss), the module serves by code path: 12 of 12 are routed (all
modes reach either the stock cascade plus stage or the silent else-branch). Flown with INDI pos on in a recorded
result set: offboard only (everything else UNVERIFIED, see section 4).

## 2. Cross-cutting items (mc_pos_control behaviour -> IPC)

| Item | Status | Evidence |
|---|---|---|
| Work item scheduling, dt clamp [2, 40] ms, 100 ms backup (REQ B1) | done | IPC:614, 621-626 |
| Mode-flag edges: stored enable time, clear setpoint on disable, decaying vel limits restart (REQ B2, B3) | done | IPC:628-655 |
| Takeoff state machine, COM_SPOOLUP_TIME, COM_THROW_EN skip (REQ B4) | done | IPC:735-739 (library Takeoff, linked from mc_pos_control) |
| Takeoff ramp on up-speed limit; acceleration ff NaN-ed in rampup (REQ B5) | done (stock), INDI bypassed in rampup | IPC:753-755, 810, 836-840 |
| Offboard want_takeoff, speed limit override (REQ B6) | done | IPC:706-733 |
| Idle setpoint on ground / ground contact, integrator reset (REQ B7) | done | IPC:757-765 |
| Publishes `takeoff_status` (state, tilt_limit) for the land detector (REQ B8) | done | IPC:912-921; publication IPCh:150 |
| Publishes `vehicle_local_position_setpoint` (land detector input) | done, but its `thrust` is overwritten by the INDI thrust vector when the stage runs, `acceleration` stays the stock command | IPC:278-281, 883-899 |
| Land detector inputs that the module must keep meaningful: trajectory_setpoint vz (input, untouched), thrust scale = hover-thrust convention, takeoff_status (REQ B8) | done; thrust scale: stage uses `G = g / ht` (IPC:185-186, 276) so collective = hover thrust at hover. Not verified against the land detector in flight | UNVERIFIED |
| Hover thrust: HTE valid only in flight, else MPC_THR_HOVER (REQ B15) | done for the stage (`ht`, IPC:749-750); the stock integrator shift that MPC does on estimate update (MPC:428 `updateHoverThrust`) is NOT done: IPC calls `setHoverThrust` only (IPC:750). Harmless while the stage runs (integrator zeroed, IPC:852, 891-893); in bypass-in-flight the integrator is not shifted, small thrust step on estimate update | partial; see T9 |
| Estimator resets xy/z/vxy/vz/heading (REQ B14) | done (same function structure as MPC:718-780); no test | IPC:978-1041. Stage state (filters, previous thrust) not touched on a reset: UNVERIFIED effect on `_indi` memory |
| EKF-reset handling inside the INDI stage | missing | `_indi` is only reset on bypass (IPC:293); nothing reacts to reset counters |
| Setpoint invalid -> reuse last valid < 200 ms -> failsafe setpoint (REQ B11-B13) | done | IPC:858-881, 927-976 |
| Failsafe uses PID when the stage cannot run | present, by design of A3 bypass (stock attitude sp published, IPC:287-295). Conflicts with owner direction "no PID fallback" (MEMORY.md, INDI owner direction) | owner decision needed, see 4 |
| Process-level PID fallback: `mc_indi_pos_control start \|\| mc_pos_control start` | present, same conflict | RCA:59 |
| Tilt limit LND/AIR with 0.2 rad/s slew (REQ B16) | done; INDI limits take the slewed value | IPC:767-770, 187-188, 888 |
| Thrust limits min (flight) / max, xy margin (REQ B17) | done in PositionControl; INDI stage clamps again with MPC_THR_MIN/MAX | IPC:775-777, 187-188 |
| Velocity limits xy/up/down, vxy_max, decaying limits (REQ B18) | done; INDI limits also take them | IPC:779-812, 187 |
| Acceleration limits MPC_ACC_*, jerk (feed-forward from tasks, not this module) | n/a here; GotoControl gets them | IPC:430-437 |
| Velocity filters (notch, LP, derivative LP), reset on invalid velocity (REQ B10, B21) | done | IPC:537-604 |
| Vertical velocity from `z_deriv` blend when only vz commanded (REQ B19) | done | IPC:816-827 |
| Yaw / yaw rate passthrough, heading reset delta (REQ B22) | done for stock; INDI stage takes `yaw_sp` from the stock `q_d` (IPC:199) and `thrustToAttitude` rebuilds `q_d` from it (IPC:277; ControlMath.cpp:47-51); `yaw_sp_move_rate` is not written by `thrustToAttitude`, so it stays from the stock getAttitudeSetpoint (PositionControl.cpp:272) | done, UNVERIFIED in a yaw-rate flight |
| Parameter updates at runtime, SYS_VEHICLE_RESP, clamping (REQ B25) | done | IPC:298-536 |
| Disarm: INDI injection window reset, stage not run disarmed | done | IPC:632-634, 836 |
| Unit tests for decision logic (D-G7-HARNESS, DECISIONS.md:564) | missing: CMakeLists.txt registers only `IndiPosInjectionTest.cpp`; the stock MulticopterPositionControlTest.cpp is not mirrored | CMakeLists.txt last line |

## 3. Ordered build list

Rule: each task is one implementation agent, one commit, pure-helper extraction where possible so a gtest can fail
without SITL (D-G7-HARNESS). SITL smoke = `indi_flight/bench/run_scenario.py` with `--sim v2 --model quad5in`
and `MC_INDI_POS_EN 1` in the params file (S128 note: check `MC_RATE_CTL_TYPE`, STATE.md:46).

### S130: AUTO modes

T1. Extract `computeWantIndi(flags, takeoff_state, ground_contact, armed)` and `deriveZOnly(flags)` from IPC:232,
836-840 into a header-only helper in the module; gtest table over every row of section 1 (manual off, ALTCTL
z-only, POSCTL, auto, descend). Fails if: ALTCTL/DESCEND returns full 3-axis, or POSCTL returns z-only, or a
state < flight returns true.
T2. Smoke harness for AUTO: scenario + runner support for a navigator-driven mission (arm, `commander takeoff`,
`mission start`) beside the offboard path (run_scenario.py:100-115 is offboard only). Result README lists tracking error
per leg. Fails if: no waypoint reached in 120 s sim.
T3. Take-off handover (AUTO takeoff, stick takeoff in POSCTL): add a one-line log of the thrust command at
rampup -> flight (`indi_pos_status`, IPC:258-274 already carries `thrust`) and a runner check that |thrust step| at the
edge < threshold (to be set in GATES.md before the run). Fails if: step exceeds the threshold, or altitude
dips more than 0.3 m at the edge.
T4. Land and touchdown: smoke LAND from 10 m with INDI on; assert vz tracks MPC_LAND_SPEED, stage -> bypass edge at
ground contact, disarm within COM_DISARM_LAND, and `blend` unchanged across the edge (|db| < 1e-6, DECISIONS.md:455).
Fails if: bounce, or disarm timeout, or blend jump.
T5. Failsafes: (a) DESCEND via `COM_RC_LOSS` action / `NAV_RCL_ACT` descend, (b) RTL on RC loss, (c) Land on
data-link loss, (d) empty trajectory_setpoint. gtest for `generateFailsafeSetpoint` (IPC:927-976) extracted as a pure function:
xy velocity finite -> vxy 0; vz invalid -> acc_z 0.3 and vz NaN (REQ B12 correction). Fails if: the extracted
function diverges from MPC:667-713 on any of the four input combinations (test compares with the stock rule table).
T6. Return + mission + loiter smoke (one scenario each, 1 seed), results folder per mode with xy/z error README.

### S131: OFFBOARD, pass-through modes, first G5 probe

T7. Offboard acceleration and velocity-only setpoints (no position): add scenario rows to scenarios.py using the offboard path
(velocity-only, acceleration-only, takeoff via offboard setpoint with `want_takeoff` IPC:706-733). Fails if: no
takeoff from the ground on the setpoint alone, or `speed_up` ignored (override IPC:731).
T8. Pass-through modes: MANUAL, STABILIZED, ACRO with INDI pos on: scenario `stick` mode already maps
altctl/posctl/acro/stabilized (STICK_MAIN_MODE, run_scenario.py:91, per posctl_gap_scope_s103.md section 1);
assert `mc_indi_pos_control` publishes no attitude setpoint in those modes (topic
`vehicle_attitude_setpoint` publisher is mc_att_control) and takeoff_status reports skip state. Fails if: IPC
publishes `vehicle_attitude_setpoint` while PC is off (compare publisher count by timestamp pattern in log).
T9. Hover-thrust interaction: port MPC:423-431 (`updateHoverThrust` with integrator shift) into IPC:659-667 while
keeping the stage's own `ht` (IPC:749). gtest on PositionControl is stock; test is a SITL assertion that the thrust
command is continuous across an HTE update in bypass-in-flight. Fails if: step in commanded thrust at an HTE update
exceeds 2 % of hover.
T10. Estimator reset reaction in the stage: on any reset counter change, call `_indi.reset(...)` (as in the bypass,
IPC:293) so jerk differencing does not see the reset as a step. gtest with a mock stage: reset counter bump ->
`reset()` called once. Fails if: no reset call, or called every cycle.
T11. First G5 probe: run the G5 set from GATES.md (list not read in this session, see 4) in each mode of T2-T8 with 1
seed, INDI pos on, PID reference for comparison only (F-5). Output one table: mode x pass/fail x metric.
T12. Owner questions to raise at the end of S131 if any row of section 1 has no flown code: (a) remove
`|| mc_pos_control start` (RCA:59) and decide the bypass behaviour; (b) enable the module on a hardware board.

## 4. UNVERIFIED

- Whether any mode other than offboard has been flown with `MC_INDI_POS_EN 1`: STATE.md:57 lists the S129 POSCTL
  smoke as pending; I did not open result folders.
- `s5_gap085_posctl` content (scenarios.py:190 shows an alias of the altctl dict; POSCTL xy hold with centred
  sticks is not what the alias proves).
- Navigator-driven mode selection from the bench runner (mission/RTL/land commands): not located in run_scenario.py.
- Producer of `trajectory_setpoint` in the Descend task for xy (REQ section 5), and external-mode producers.
- Land detector reaction to the INDI thrust scale in flight (thrust-low test, LD.cpp:231-240 per REQ B8).
- Behaviour of the stage when the stock failsafe setpoint is fed in (blind descent) and across estimator resets.
- G5 gate content: `GATES.md` G5 section not found by `sed '/^## G5/,/^## G6/p'` (no match); the G5 events list
  (5.10 sag etc.) is only referenced at GATES.md:191-193. T11 must take it from GATES.md before the run.
- Owner direction: MEMORY.md says "no PID fallback"; the bypass (IPC:287-295) and RCA:59 are PID fallbacks. Intent
  for stage 5 (keep as safety bypass or remove) is not settled in files I read.
- The module is not part of any hardware board config; whether another board config references
  `MC_INDI_POS_EN` was only grepped under boards/, ROMFS/ and Tools/.
