# Outer-loop candidates, review round 2 (independent, 2026-11-15)

Reviewer: Claude Opus 5.5 (claude-opus-5-5). Reviewed: `outer_loop_candidates_r2.md` (A1-A9, R1a-R52, open questions)
against `outer_loop_review_r1.md` and the source on `feat/indi-flight`. No build, no git, no code change.
Abbreviations as r1: MPC = `mc_pos_control/MulticopterPositionControl.cpp`, PC = `PositionControl/PositionControl.cpp`,
LIB = `src/lib/indi_accel_control/indi_accel_control.cpp`, LD = `land_detector/MulticopterLandDetector.cpp`,
FTD = `flight_mode_manager/tasks/Descend/FlightTaskDescend.cpp`, FTA = `.../ManualAltitude/FlightTaskManualAltitude.cpp`.

## 1. Round-1 findings

| id | status | reason (evidence) |
|---|---|---|
| F1 | CLOSED | A2: `setHoverThrust()` only (PC.hpp:127), `updateHoverThrust()` (MPC:428) not called, `resetIntegral()` each cycle (PC.hpp:164); `_vel_int` enters a_ref only at PC:150, so a_ref = ff + P/D. |
| F2 | CLOSED | A1: rewrite in place, rc.mc_apps:49 -> if/else as :17-23, :67-71 removed. Keep `depends on MODULES_MC_POS_CONTROL` (PositionControl and Takeoff libs live there). Residual: N6. |
| F3 | CLOSED | A3 tracking mode + `vehicle_thrust_setpoint` input, edges e1-e5 listed with a test each. Residual: N4 (where tracking runs). |
| F4 | PARTIAL | Gain unified (G = g/ht) and edge continuity specified, but the *offset* consequence of a T_meas scale error is not addressed (N3, Q2). |
| F5 | CLOSED | A4 ports PC:163-186 onto the INDI vector and removes the `(0,0,-c_max)` replacement; stock comparison test defined. |
| F6 | CLOSED | A7 (R52). |
| F7 | PARTIAL | Deferred to a stage-5 prototype with an overturn rule; acceptable, but the overturn criterion targets the wrong risk (N5). |
| F8 | PARTIAL | A5 adds an IMU_ACCEL_CUTOFF copy on T_meas run at the ESC rate; ESC sample timing (irregular, per-motor) is UNVERIFIED and the `sensor_combined` alternative is dropped without reason. A-acceptable. |
| F9 | CLOSED | B only: hold, stop after 3 missed slow cycles. B deferred. |
| F10 | CLOSED | C rejected. |
| F11 | CLOSED | C rejected. |
| F12 | CLOSED | A5: `vehicle_attitude`, stale after 20 ms, fallback bypass. |
| F13 | CLOSED | Accepted as a one-cycle transient; jerk ff off (A6). |
| F14 | CLOSED | A6 `setFeedforward(false)`. |
| F15 | CLOSED | Bring-up go/no-go item (A9). |
| F16 | CLOSED | No action needed in r1. |
| F17 | CLOSED | Superseded by A3 tracking (state follows the commanded thrust while inactive). |

## 2. New findings on amended A

| id | class | finding | evidence | fix (no stock diff needed) |
|---|---|---|---|---|
| N1 | BLOCKING | **Acceleration-only axes change meaning under INDI.** Stock maps an acceleration setpoint open-loop to thrust/tilt (`a*ht/g`), so drag bounds the resulting speed. INDI closes the loop on the measured kinematic acceleration and cancels drag, so a constant a_ref with no velocity term integrates to a speed that keeps growing. Required failsafes hit this: (a) Descend nav state with no vz: `vel_z = NaN, acc_z = +0.3` (FTD:57-58). Stock descends at slightly below hover thrust. INDI descends at a constant 0.3 m/s^2, so from 100 m it hits the ground at about 7.7 m/s. (b) MPC "blind descent" (MPC:~703-708, same +0.3) inside `generateFailsafeSetpoint`, used on setpoint timeout (MPC:454, :624). (c) Descend xy `acc = 0` "stay level" (FTD:72) and MPC "blind land" xy `acc = 0` (MPC:~690): INDI holds the ground speed it had when position was lost instead of letting drag bleed it off. | FTD:52-72, MPC:680-712, LIB:265-270 (increment around the measured state) | Classify per axis. An axis with no finite position or velocity setpoint is open-loop: either the INDI stage is inactive on that axis (stock PC mapping, tracking kept), or z uses the stock `a*ht/g` collective. Test: blind descent from 100 m, same touchdown speed as stock within x %. |
| N2 | MAJOR | **Altitude mode xy (and Descend with RC) is stick -> acceleration, not stick -> tilt.** FTA:300 sets xy from StickTiltXY (`stick * tan(tilt_max) * g`, StickTiltXY.cpp:58-68), with velocity/position xy NaN. Under INDI, releasing the stick holds the current ground speed (no drag braking), and holding the stick accelerates up to the max-tilt drag speed whatever the deflection. The mode stays flyable but its stock semantics are gone, and it is the pilot's fallback when position is lost. | FTA:300, FTD:64, StickTiltXY.cpp:58-68 | Same per-axis rule as N1 (xy open-loop when only acceleration is set, INDI on z). Test: stick step and release in Altitude mode, A vs stock, deceleration within x %. |
| N3 | MAJOR | **T_meas scale error is a steady acceleration bias, not a gain error.** The LIB adds the increment to the *measured* thrust (LIB:265-270). If `(rpm/rpm_max)^2 = k * u_cmd` with k != 1 (because of rpm_max, THR_MDL_FAC applied in mixer_module, or battery sag), the steady state needs `Delta = (1-k) u`, which means `a_ref - a_meas = G(1-k)u ~ g(1-k)` at hover. With A2's I = 0 nothing removes it: k = 0.9 gives about 1 m/s^2, i.e. about 0.25 m/s vz error or a z offset of `bias/(P_vel*P_pos)`. It also drifts with battery voltage. A2's acceptance test (edge continuity) does not see it. The modelled-actuator path (k = 1) is immune. | LIB:97, :265-270; indi_rate_control.hpp:170; mixer_module.hpp (THR_MDL_FAC) | Scale T_meas by an online ratio `k^ = LPF(thrust_sp)/LPF(T_meas)` (HTE-like, slow), or keep a small outer z/xy integral (safe after F1's fix). Add the test: hover bias < 0.2 m/s^2 with rpm_max +-10 % and a 15 % battery sag. |
| N4 | MINOR | Tracking (A3) only runs inside the `vehicle_local_position` callback (MPC:389, A9). After an R41 silence or a PC-off period with no local position, the stored seed is stale. The resume after silence in FLIGHT (e6) is not listed. | MPC:382-389 | Seed from the latest `vehicle_thrust_setpoint` read *in the edge cycle*. Add e6: a gap > N cycles counts as an edge (reset + seed). |
| N5 | MINOR | A8 overturn rule "lift-off after FLIGHT hand-over at -20 %" is benign under INDI: on the ground a_meas ~ 0 against an upward a_ref, so INDI raises thrust. The real e1 risks are +20 % ht (bypass P-only lifts off early and overshoots the ramp) and a LD ground_contact toggle at e1, which drops the vehicle into the (0,0,100) idle (MPC:507, :522-529; LD:242-257). | MPC:505-529, LD:232-257 | Overturn on: climb rate > ramp limit by x %, or `flying_but_ground_contact` set within 1 s after e1. |
| N6 | MINOR | `MC_INDIP_EN` keeps its name but changes meaning: a saved `=1` (archive: run alongside) silently becomes "replace mc_pos_control". The :17-23 pattern also has no fallback if `mc_indi_pos_control start` fails, which leaves no position controller (the same is true of the rate pattern). | rc.mc_apps:17-23, :49, :67-71 | Rename (e.g. `MC_INDIF_EN`) or add a migration note, and add `|| mc_pos_control start` style fallback. |
| N7 | MINOR | Offboard acceleration-only setpoints (pos and vel NaN) become true acceleration tracking, so they are no longer thrust-mapped. This differs from stock and is arguably intended, but it is not stated. Offboard attitude/rate/thrust disable PC, so they fall under e3 and are fine. | PC:146-153 | Document it, or let the N1 rule cover it (then it stays as stock). |

## 3. Answers to "Open for round 2"

1. **Is tracking sufficient for every edge?** Yes for continuity at the inactive -> active edges e1-e5, given N4. During FLIGHT, failsafe entry and EKF resets are not tracking edges, because the INDI stage stays active.
   - EKF resets: position and velocity resets are compensated upstream of a_ref by `adjustSetpointForEKFResets` (MPC:720-780). a_meas comes from the IMU, so it does not step. A heading/quat reset is the one-cycle F13 transient.
   - Failsafe entry: it steps a_ref, as stock does, with no thrust discontinuity beyond G*step.
   - Tracking does not cover what the failsafe *setpoint* means. That is N1, so the answer is no for blind descent and Descend.
2. **Does G = g/ht hold on the published scale?** As a gain, yes. HTE, LD and the bypass all read `thrust_body` / `vehicle_thrust_setpoint` on the same normalised scale, and the allocator keeps that scale (the mixer_module applies THR_MDL_FAC afterwards). The scale of *T_meas* only holds if `(rpm/rpm_max)^2` equals the commanded u, and with an increment added to the measured state any mismatch becomes an offset (N3), not a gain error. UNVERIFIED: whether `mc_indi_rate_control` alters the collective between `vehicle_thrust_setpoint` and the allocator.
3. **Does any mode publish a setpoint that A misclassifies?** Yes, every acceleration-only axis:
   - Altitude mode xy (FTA:300)
   - Descend z without vz (FTD:57-58) and xy (FTD:64, :72)
   - MPC blind land and blind descent (MPC:680-712)
   - offboard acceleration-only

   A switches on the takeoff state and input staleness only, never on the setpoint type (N1, N2, N7). The idle (0,0,100) setpoint and RAMPUP are classified correctly (bypass, MPC:522-529).

## 4. Verdict

A as amended closes 13 of 17 r1 findings (F4, F7, F8 PARTIAL; none OPEN). It still breaks the Descend failsafe and the
MPC blind-descent/blind-land failsafes (N1), and it changes Altitude mode handling (N2). Both are fixable inside the module with a
per-axis "acceleration-only means open-loop" rule, with no stock diff. N3 must be designed before stage 5 tuning.
UNVERIFIED: ESC sample timing (F8), the collective path inside `mc_indi_rate_control` (Q2), and the MPC line numbers marked ~ (from a range read).

BLOCKING findings: 1
