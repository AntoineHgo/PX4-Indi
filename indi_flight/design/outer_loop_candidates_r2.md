# Outer-loop architecture candidates, round 2 (session 6, 2026-11-15)

Input: `outer_loop_candidates_r1.md` (structure of A, B, C unchanged unless stated), review round 1
(`outer_loop_review_r1.md`, findings F1-F17), requirements R1-R51 plus the amendments R1a-R52 at the end of this
file (to be folded into `outer_loop_requirements.md` once round 2 confirms them). C stays rejected (F10, F11).
Round 2 reviews **A as amended here**, with B as a deferred trigger change.

## A, amended

### A1. Module, parameter, start (F2, R1, R51)
- The branch module `src/modules/mc_indi_pos_control` (archive external-mode design, R-a rejected, offboard only,
  F-2 not reachable from it) is **rewritten in place** into candidate A. Its old code stays in git history
  (last commit before the rewrite is recorded in `DECISIONS.md`) and in the archive report; nothing under
  `indi_project/` changes. One module, one name, no collision.
- `MC_INDIP_EN` keeps its name; meaning becomes "start `mc_indi_pos_control` instead of `mc_pos_control`".
  rc.mc_apps:49 becomes an if/else like rc.mc_apps:17-23 (rate module); the old block :67-71 is removed.
  Kconfig drops `depends on MODULES_MC_POS_CONTROL` only if the libraries are linkable without it (check).
- VTOL (rc.vtol_apps:20, `vtol` argument) and voxl2 scripts: **not served**, untouched, documented limit (the
  mission is quadcopters). `MC_INDIP_EN` is ignored there.

### A2. Hover thrust enters at one place (F1, F4, R24, R25, R47)
- One value `ht` per cycle: hover_thrust_estimate when valid and state FLIGHT, else MPC_THR_HOVER (same ordering
  as MPC:423-431, :513-515).
- PositionControl gets `ht` through `setHoverThrust()` only. `updateHoverThrust()` is never called, and
  `resetIntegral()` is called every cycle (I gains are 0 anyway): `_vel_int` is a don't-care, so a_ref = ff + P/D
  exactly. Unit test: 100 HTE updates leave a_ref unchanged.
- INDI stage scale: effectiveness `G = g / ht` (specific force per unit normalised collective thrust), the LIB's
  `g_t * k_cmd` product replaced by this single value. T_meas is expressed in the published `thrust_body` scale:
  mean over motors of the normalised actuator state the rate stack inverts on (u = (omega/omega_max)^2, O-6).
  With telemetry the steady state is set by T_meas + increment, so an error in `ht` changes loop gain only (G3
  covers x[0.5, 2]); the bypass thrust and the INDI thrust live on the same scale, which the LD and HTE also use.
- Acceptance (R24 amended): at every bypass->INDI edge the published collective equals the last bypass collective
  within 2 % of hover, with and without telemetry, for ht errors of +-20 %.

### A3. Bumpless INDI entry: tracking while bypassed (F3, F17, R33, R37, R14)
- New input `vehicle_thrust_setpoint` (rate-stack output, what LD and HTE read), stale after 20 ms.
- **While the INDI stage is not active** (PC off, disarmed, ground/idle, RAMPUP, `flying_but_ground_contact`),
  it runs in tracking mode each cycle: modelled actuator state and `IndiAccelControl::reset(f_b, mean_u)` follow the
  last `vehicle_thrust_setpoint` (fresh) or the module's own last published thrust (stale). Jerk history cleared.
- Edges therefore start from the thrust actually commanded, telemetry or not: e1 RAMPUP -> FLIGHT, e2
  ground-contact set/clear (bounce on landing), e3 PC-off -> PC-on in air (Stabilized at 0.7 -> Position), e4 ESC
  stale <-> fresh (O-5 switch: modelled state seeded from the last measured mean_u), e5 IMU stale <-> fresh.
- Tests: one per edge, thrust step < 2 % of hover at the edge, with and without telemetry.

### A4. Saturation and XY margin in the INDI stage (F5, R26, R27)
- PC:163-186 (vertical priority, MPC_THR_XY_MARG) ported onto the INDI thrust vector, margin in thrust units as
  stock. The LIB's `(0,0,-c_max)` replacement at collective saturation is removed. Tilt limit as stock
  (`ControlMath::limitTilt`, slewed tilt from the shell). Test: climb at thr_max with an xy setpoint keeps the
  margin; same test on stock mc_pos_control gives the reference.

### A5. Inputs and filters (F8, F12, F13, R33)
- `vehicle_attitude` (full q, stale after 20 ms, HTE precedent) rotates a_meas; `vehicle_acceleration`
  (bias-corrected, IMU_ACCEL_CUTOFF low-pass) gives a_meas; `esc_status` gives T_meas.
- Filter match: T_meas passes through a copy of the IMU_ACCEL_CUTOFF low-pass (same cutoff, run at the ESC sample
  rate) before the common INDI filter. Exact matching at real rates is decision 6 (stage 3); the residual
  mismatch is a modelled delay in the G2 linear model and must agree with the injection measurement.
- Quaternion reset (`quat_reset_counter`): one-cycle a_meas rotation, accepted (F13); jerk feed-forward is off
  (A6), so it is not amplified.
- Every new input has a staleness rule and a fallback (R33 amended): attitude or acceleration stale -> INDI stage
  inactive, tracking mode (A3) and stock PositionControl thrust published (bypass), logged.

### A6. Jerk feed-forward off (F14)
- `vehicle_attitude_setpoint` cannot carry a body-rate feed-forward; `setFeedforward(false)`, no backward
  difference of a_ref. Re-opened only with a rate-carrying interface, which O-11 excludes today.

### A7. Published setpoint reflects the command (F6, R52)
- `vehicle_local_position_setpoint.thrust` = published INDI thrust vector (NED), `.acceleration` = a_ref.

### A8. Take-off ramp under bypass (F7, R14)
- RAMPUP stays on the stock P-only chain in bypass (ramp starts at zero thrust through PC:220, R14a). Without the
  stock velocity integral, lift-off timing differs from stock when MPC_THR_HOVER is wrong. This is the riskiest
  behaviour of A and is **prototyped first** (stage 5): take-off with ht error -20 %, 0, +20 %, measure lift-off
  time vs ramp end and thrust continuity at e1. Overturn: lift-off after the FLIGHT hand-over with -20 %, or a
  thrust step > 2 % at e1; then alternative A8' (INDI active from RAMPUP, ramp acting on a_ref through the
  velocity-limit clamp PC:140, ground contact handled by the tracking mode) is designed and reviewed.

### A9. Unchanged from r1
Shell copy of MulticopterPositionControl (take-off machine, constraints, want_takeoff, failsafe setpoint, EKF
reset handling, tilt slew, GotoControl, silence on missing local position R41/Rnew-5), stock PositionControl for
pos/vel, single work item on `vehicle_local_position` (125 Hz SITL, fact 1). Hardware rate and latency are a
bring-up checklist item with a go/no-go on phase at the design bandwidth (F15).

## B, deferred
The INDI stage is a rate-independent class, so B is a trigger change. If B is ever taken: the fast stage holds
its last output without extrapolation and stops publishing after 3 missed slow cycles (F9); filter matching as
A5 (F8). Taken only if G2's delay margin fails on A.

## Requirement amendments (proposed by review r1, section 3)
- R1a: the branch module `mc_indi_pos_control`, `MC_INDIP_EN` and rc.mc_apps:67-71 are rewritten or removed; a
  board builds and starts at most one position controller.
- R14a: the take-off ramp starts at zero thrust (TO:45 + PC:220), not only at the velocity limit.
- R24a: thrust continuity at every bypass->INDI edge within 2 % of hover, with and without telemetry.
- R25a / R47a: hover thrust enters the replacement at exactly one named place; no loop with zero I gain has its
  integrator moved by an HTE update.
- R33a: inputs include `vehicle_thrust_setpoint` and `vehicle_attitude`; every new input has a staleness rule and
  a fallback.
- R41a: a module with a second trigger states what it publishes when either trigger stops.
- R52: `vehicle_local_position_setpoint.thrust/acceleration` reflect the published command.

## Open for round 2
1. Is tracking mode (A3) sufficient for every edge, including failsafe entry and EKF resets during FLIGHT?
2. Does G = g/ht hold on the published scale through the INDI rate module and the allocator (THR_MDL_FAC, O-6)?
3. Does any mode publish a trajectory setpoint that A's bypass/INDI switch misclassifies?
