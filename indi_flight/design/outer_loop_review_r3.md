# Outer-loop candidates, review round 3 (independent, 2026-11-15)

Reviewer: Claude Opus 5.5 (claude-opus-5-5). Scope: `outer_loop_candidates_r3.md` (A10-A12) against
`outer_loop_review_r2.md` and the source on `feat/indi-flight`. No build, no git, no code change.
Abbreviations: MPC = `src/modules/mc_pos_control/MulticopterPositionControl.cpp`, PC = `.../PositionControl/PositionControl.cpp`,
LIB = `src/lib/indi_accel_control/indi_accel_control.cpp`, FTD = `.../tasks/Descend/FlightTaskDescend.cpp`,
FTA = `.../tasks/ManualAltitude/FlightTaskManualAltitude.cpp`, FTT = `.../tasks/Transition/FlightTaskTransition.cpp`,
FTO = `.../tasks/Orbit/FlightTaskOrbit.cpp`, SAXY = `.../tasks/Utility/StickAccelerationXY.cpp`, RC = `ROMFS/px4fmu_common/init.d/rc.mc_apps`.

## 1. Does A10 close N1? Classifier coverage

**N1: CLOSED in substance.** On an acceleration-only group the published thrust is the stock open-loop map, so drag
bounds the speed as with mc_pos_control. This covers Descend z without vz (FTD:55-58), blind descent (MPC:705-708) and
blind land xy (MPC:689-692). N2 (Altitude xy, FTA:300-301) and N7 (offboard) are also CLOSED. In the worst case
(finding R3-2 below) the stage drops to bypass in exactly these states, and bypass is also stock. Safety holds either way.

**Classifier: complete for every pattern that can reach the controller.**
- "Velocity on x only" cannot happen. PC rejects any xy setpoint whose x/y finiteness differs for position, velocity
  or acceleration (PC:236-239). MPC then substitutes the last valid setpoint (<200 ms) or the failsafe (MPC:612-627).
  Offboard per-axis NaN mixes over uXRCE-DDS are rejected in the same way, as in stock.
- Every validated group is either tracked (finite position or velocity) or acceleration-only.

Condition: classify the setpoint that PC finally accepted, after the MPC:612-627 fallback, not the raw `trajectory_setpoint`.

| source | xy | z | A10 class | correct? |
|---|---|---|---|---|
| Position (ManualAcceleration, SAXY:149-151) | pos lock / vel + acc | pos / vel | INDI / INDI | yes |
| Altitude (FTA:300) | acc only | pos / vel | open / INDI | yes (but see R3-2, R3-4) |
| Orbit (FTO:351-353, :143) | vel + acc, pos NaN | pos or vel | INDI / INDI | yes |
| Auto, Land, Takeoff (vel z through the ramp limit, MPC:575-577) | pos/vel/acc | pos/vel | INDI / INDI | yes |
| Descend, vz valid (FTD:50-53, :64, :72) | acc only | vel | open / INDI | yes |
| Descend, vz invalid (FTD:57-58) | acc only | acc only | open / open | yes (= stock) |
| MPC blind land / blind descent (MPC:689-692, :705-708) | acc only | vel or acc | open / INDI or open | yes |
| VTOL transition (FTT:88, :105) | acc only (`tan(tilt)*g`) | vel | open / INDI | yes, but not listed (R3-6) |
| ground idle (0,0,100) (MPC:522-526) | acc only | acc only | open / open | yes; precedence vs A3/A8 bypass undefined (R3-6) |

Patterns that switch every cycle exist. Two sources: FTD:50 branches on the finiteness of vz, and the failsafe
re-evaluates state validity on every cycle (MPC:681, :699). An EKF velocity-validity flap therefore toggles e7 at the
estimator rate. A10 has no hysteresis, and with R3-1 and R3-3 below each toggle costs a reset and a step (R3-3).

## 2. Group switch continuity (not covered by A3)

- **INDI -> open loop.** This edge drops the drag and model compensation that INDI held implicitly. Stock does the same
  at the same transitions (velocity loop -> open loop, PC:202-204 freezes the integrator), so this is stock-equivalent.
- **Open loop -> INDI.** A3 makes the thrust *state* continuous, but `t_c = t_f + (a_c - a_f)` (LIB:273) applies in one
  cycle the full residual `a_c - a_f` that open loop left standing. That residual is drag plus the ht/k error.
  - Example: Altitude -> Position at cruise. The residual is up to about `g*tan(tilt)` horizontally, bounded only by
    the A4 tilt limit.
  - This is a tilt (and collective) step, and it would fail R24a (2 % at a bypass edge) by design. A10 declares e7 a
    bypass edge covered by A3 tracking, which it is not.
- **Group coupling.** The xy open-loop "share" is not separable in stock: `thr_xy = body_z_xy * collective` and
  `collective = thrust_ned_z / cos` (PC:217-224). With MPC_ACC_DECOUPLE the stock invariant is the *tilt*
  `atan(a_xy/g)`, not the horizontal thrust (PC:213-215). If xy uses `a_xy*ht/g` while z comes from INDI, the tilt per
  stick scales with `T_z_INDI/T_z_stock`, which is the ht or k error, up to ±20 % in the A12 test range. This changes
  the stick -> tilt meaning that A10 claims to restore, and the pitch command of FTT:105.

## 3. A11 acceptability

Acceptable for architecture approval: nothing in A precludes (a), (b) or (c).
- (a) lives in the rate stack.
- (b) is local to the module.
- For (c), `_vel_int` re-enters a_ref at PC:150 and is clamped at PC:146.

Two conditions:
- **Integrator state across e7.** For (b) and (c) the integrator must be *frozen, not reset*, across e7 and on
  acceleration-only groups. PC:202-204 already freezes on a NaN velocity. A11 says "reset only at bypass edges", and
  A10 makes e7 a bypass edge, so the k-gap transient would come back at every Altitude <-> Position switch.
- **Battery sag in the decision test.** The stage-2 decision test drops N3's battery-sag case. A slowly varying k is
  what separates (a) from (b)/(c), so it must stay in the test.

## 4. A12

- **N4: CLOSED.** One condition: detect the e6 gap from the raw timestamp difference, because the MPC dt is clamped
  to 0.04 s (MPC:390-391) and the LIB rejects dt > kMaxDt (LIB:206) before any reset could run.
- **N5: CLOSED.**
- **N6: PARTIAL.**
  - `mc_indi_pos_control start || mc_pos_control start` is a PID fallback beside INDI. That conflicts with the owner
    direction "no PID fallback inside or beside INDI". It also lets a vehicle silently fly a mixed pair (INDI position
    loop over PID rate, or the reverse) with no log or announcement (RC:15-22, :49, :70).
  - The owner must decide: no fallback (refuse to arm), or a fallback that is loud (mavlink critical + logged flag)
    and explicitly accepted.

## 5. Findings table

| id | class | finding | evidence | fix |
|---|---|---|---|---|
| R3-1 | MAJOR | A10 "seed the inactive group's INDI state each cycle" cannot be done per group. `IndiAccelControl::reset(f_b, mean_u)` resets the whole 3-D `_lpf_f`, the scalar `_lpf_u` and `_lpf_j`, so seeding the open group every cycle also resets the active group's filters. In Altitude mode that is permanent, so z INDI would run unfiltered. Seeding is also unnecessary, because `t_f` and `a_f` are measured, not group-specific. | LIB:94-112, :261-270 | Run the LIB on all axes every cycle and override only the output of the open group. No reset at e7. Keep reset for the whole-stage edges e1-e6. |
| R3-2 | MAJOR | LIB rejects the whole update unless p and v are finite on **all** axes. The A10 states (Altitude without GPS, blind land with vxy NaN, blind descent with vz NaN) are exactly where states are NaN, so z cannot "keep INDI". The stage drops to bypass for both groups. That is safe (stock), but A10's claim is false there and it conflicts with the owner's "INDI serves every mode". Also, when v_ref is NaN the LIB still adds `-K_vel*v` (v_sp = 0). | LIB:200-204, :219-223, :257; MPC:681-708 | Validity gate per group (finite v required only on INDI groups). Feed PC's a_ref with K_pos = K_vel = 0, or bypass LIB steps 1-2. Test: Altitude mode with GPS lost. |
| R3-3 | MAJOR | The open -> INDI edge (e7) applies the standing residual `a_c - a_f` (drag, ht/k error) in one cycle, a tilt/collective step up to the A4 tilt limit. A3 does not cover it, and R24a fails by design. Per-cycle flapping (vz validity) repeats it at the estimator rate. | LIB:273; FTD:50; MPC:612-627, :681, :699 | On entry, carry the offset `o = a_f - a_c` into the group and decay it over about 0.3-0.5 s (or rate-limit the increment). Add a dwell (e.g. 0.5 s continuous tracked pattern) before re-entering INDI; leave INDI immediately. Test: Altitude -> Position at 10 m/s, and vz-validity flapping at 5 Hz. |
| R3-4 | MINOR | The xy open-loop share is ill-defined. Stock fixes tilt `atan(a_xy/g)` (decoupled), not `a_xy*ht/g`, so a horizontal share combined with an INDI z gives a stick -> tilt gain error equal to the ht/k error. | PC:213-224 | Define the open xy group as the stock `body_z` *direction*, scaled by the z-group vertical thrust (`thr_xy = body_z_xy / body_z_z * thr_z`), then A4. |
| R3-5 | MINOR | A11 options (b)/(c): integrators must freeze, not reset, at e7. The decision test lacks battery sag. | PC:146, :150, :202-204 | Amend A11 as in section 3. |
| R3-6 | MINOR | Classifier specification gaps: (i) classify the setpoint PC accepted after the MPC fallback; (ii) precedence of the state bypass (A3/A8, ground idle) over e7; (iii) VTOL FlightTaskTransition xy acc-only missing from the source list and the classifier unit test. | MPC:522-526, :612-627; FTT:88, :105 | Add to A10. |
| R3-7 | MINOR | e6 gap detection must use the raw timestamp, because dt is clamped and the LIB rejects a large dt. | MPC:390-391; LIB:206 | As stated. |
| R3-8 | MAJOR | N6's start fallback to mc_pos_control (and the PID rate pair) is a PID fallback beside INDI, against the owner direction. It also makes a silent mixed INDI/PID stack possible. | RC:15-22, :49, :70 | Owner decision. Either no fallback (arming refused) or a loud, logged fallback explicitly accepted as an exception. |

## 6. Verdict

N1, N2, N4, N5 and N7 are CLOSED, N3 is deferred acceptably (A11), and N6 is PARTIAL. A10 is sound in principle. As
written it needs the R3-1/R3-2 implementation corrections and an e7 entry transient rule (R3-3) before the architecture
is approved.

Verdict: no blocking issue.
