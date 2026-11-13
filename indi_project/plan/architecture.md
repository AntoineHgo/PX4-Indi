# INDI rate controller: architecture (stage 1, inner loop)

Status: v1, session 5 (2026-11-13). Written by the orchestrator from
`px4_analysis_rate.md`, `px4_analysis_integration.md` and the research notes.
Decisions are logged as D-arch-* in `DECISIONS.md`; this file is the design
they add up to. Items marked **[verify]** are assumptions to check in SITL
before the report relies on them.

## 1. Scope

Stage 1 replaces only the angular-rate control law of a quadcopter. The
attitude loop (`mc_att_control`), the position loop, the control allocator
and the gyro filtering stay as they are. Outer-loop (linear-acceleration)
INDI is stage 2 and starts only after stage 1 passes the held-out
scenarios of `bench/scenarios.md`.

## 2. Control law

Notation: `w` body rate (rad/s), `w_sp` rate setpoint, `a_f` filtered
angular acceleration (`vehicle_angular_velocity.xyz_derivative`), `t`
normalised torque (allocator units, dimensionless), `H` the gyro-derivative
filter chain, `A` the actuator model, `G1` diagonal control effectiveness
(rad/s^2 per unit normalised torque), `G2_y` yaw rotor spin-up term.

```
nu      = K .* (w_sp - w) + K_ff .* d(w_sp)/dt          desired angular acceleration
t_act   = A(t_alloc)                                     modelled torque the motors produce now
t_f     = H(t_act)                                       same filter as a_f (synchronisation)
dt_cmd  = G1^-1 (nu - a_f)                               roll, pitch
t_cmd   = t_f + dt_cmd, clamped to [-1, 1]
yaw with G2:  (G1_y + G2_y/Ts) dt_y = nu_y - a_f,y + (G2_y/Ts) (t_f,y - t_f,y[k-1])  (Smeur 2016 form, torque space)
```

- With fixed `G1` and `t_f = H(A(t))` this is the algebraic equivalent of an
  incremental PID (acquatella2017 eq. 29-30). INDI's possible advantage over
  the PX4 PID therefore comes from (i) feeding back the *modelled achieved*
  torque instead of the commanded one, (ii) the measured-acceleration path
  that rejects unmodelled moments (gusts, CoM shift) at the acceleration
  level, (iii) saturation handling without an integrator. The benchmark
  scenarios W*, P*, D* probe these; the report must not attribute gains to
  INDI that a retuned PID also gets.
- `K` is a first-order rate-tracking bandwidth (rad/s). Ideal closed loop:
  `w/w_sp = K/(s+K)`. Initial value 20 rad/s roll/pitch, 10 rad/s yaw
  **[verify]**, then tuned (phase 5). `K_ff` defaults to 0.
- No integrator: the incremental form gives zero steady-state acceleration
  error by construction; a constant moment disturbance is rejected because
  `a_f` measures it.

## 3. Placement in PX4 (D-arch-1, D-arch-2)

- **Torque space, ahead of the allocator.** INDI publishes the same
  `vehicle_torque_setpoint` / `vehicle_thrust_setpoint` as the PID. The
  allocator, its prioritisation (thrust > roll/pitch > yaw) and airmode are
  unchanged. Rejected: actuator-space INDI (`u = u_prev + B^+ (nu - a)`),
  because it needs a new allocator input or bypassing the allocator
  (losing standard flight modes), and the prior PX4 PR #25216 reviewers asked
  for no changes to `ControlAllocator`. Kept as a possible later branch.
- **Inside `mc_rate_control`, law in a new library.** New library
  `src/lib/indi_rate_control/` (+ gtest), PID library
  `rate_control.{hpp,cpp}` untouched. `mc_rate_control` gets one enum
  parameter `MC_RATE_CTL_TYPE`, 0 = PID (default),
  1 = INDI, and a branch around the single call to the law. Selection is
  latched while disarmed: a change in flight takes effect at the next arming
  (switching laws mid-air is a transient nobody needs). Rejected: a separate
  module chosen in the startup script (leaves the PID module byte-identical,
  but duplicates acro-mode setpoint generation, thrust/battery handling,
  autotune hooks and status publishing; two publishers of the torque topic
  are a hazard); external-mode integration like `mc_nn_control`/`mc_raptor`
  (bypasses allocator and standard modes, wrong fit for a rate law).
- **Thrust** passes through unchanged (`vehicle_rates_setpoint.thrust_body`).
- **Yaw output LPF** (`MC_YAW_TQ_CUTOFF`) and **battery scaling** are applied
  only on the PID branch. INDI includes its own actuator model; a 2 Hz
  filter after it would break the synchronisation. Battery-voltage effects
  change the effective `G1`, which INDI's incremental form partly absorbs
  (benchmark: no battery model in gz, so not tested **[verify]**).

## 4. Actuator state (D-arch-3)

- Gazebo's `esc_status.esc_rpm` only echoes the command (integration analysis
  2.2), so there is no measured rotor speed in SITL. An onboard model is
  required, as on any vehicle without RPM telemetry.
- **Stage 1: first-order model in torque space.** `t_alloc` = allocated
  torque = `vehicle_torque_setpoint` of the previous cycle minus
  `control_allocator_status.unallocated_torque` (used only when fresher than
  20 ms, else the clamped setpoint). `A`: discrete first-order lag with
  time constant `MC_INDI_ACT_TC` (default 0.02 s, between the x500 values
  0.0125 s up / 0.025 s down) **[verify by step identification]**.
- Why torque space and not per motor: the allocator's normalisation scale is
  not published, so mapping per-motor states back to normalised torque needs
  a copy of the effectiveness matrix. The torque-space lag is exact when the
  motors are not saturated and up/down constants are equal; it is wrong by
  the asymmetry otherwise. Upgrade to a per-motor model only if the
  benchmark shows the approximation limits performance (D-arch-3 records the
  trigger).
- Plant nonlinearity: in gz thrust ~ omega^2 and omega is linear in the motor
  command, while the allocator assumes thrust linear in command
  (THR_MDL_FAC = 0). `G1` is therefore operating-point dependent (about
  proportional to omega at hover). Same mismatch for PID; INDI sees it as a
  `G1` error, which wang2019 shows it tolerates to first order.

## 5. Filter synchronisation (D-arch-4)

- `a_f` is the backward difference of the notch+LPF2p(`IMU_GYRO_CUTOFF`)
  gyro, then `AlphaFilter(IMU_DGYRO_CUTOFF)`, computed at the raw gyro rate.
- `H` applied to `t_act`: `LowPassFilter2p(IMU_GYRO_CUTOFF)` followed by
  `AlphaFilter(IMU_DGYRO_CUTOFF)`, both designed at the controller rate
  (measured `dt`), reading the two IMU parameters so they stay matched
  when tuned. Notches are not replicated (default off; if enabled, INDI must
  replicate them: recorded as a limitation).
- Mismatch left: the sensor filters run at the raw gyro rate, ours at the
  controller rate; for cutoffs <= 40 Hz and >= 250 Hz loop rate the
  continuous-time responses agree within a fraction of a sample **[verify:
  SITL gyro rate and loop rate]**. The sensor side has an extra half raw
  sample of differencing delay and up to one publish period of transport
  delay; a pure delay of `MC_INDI_DELAY` samples (0..4, default 0) on
  `t_act` is provided to absorb this if identification shows it.
- Not changing the shared IMU filter defaults is the default. If tuning
  shows INDI needs a higher `IMU_DGYRO_CUTOFF`, it is a per-controller
  parameter set, and the retuned PID baseline is allowed the same freedom
  (fairness rule, D-session3-1).

## 6. Effectiveness G1, G2 (D-arch-5)

- Fixed, per-axis parameters `MC_INDI_G1_R/P/Y`, `MC_INDI_G2_Y` (default 0).
  Initial values identified in SITL from rate steps: `G1 = d(a)/d(t)` on the
  hover operating point, using the logged `vehicle_angular_velocity` and
  `vehicle_torque_setpoint`. A model-derived cross-check: normalised torque 1
  corresponds to the allocator's max roll moment; `G1_r = M_max/Ixx`.
- Adaptive effectiveness (Smeur 2016 LMS, blaha2024 RLS) is out of stage 1;
  it is the first candidate if the plant-mismatch and payload scenarios
  show `G1` errors dominate.

## 7. Saturation, landing, arming, numerical safety (D-arch-6)

- **No windup by construction:** `t_cmd = t_f + G1^-1 (nu - a_f)` has no
  accumulator; `t_f` tracks what the allocator actually produced
  (`t_alloc`), so a saturated axis cannot accumulate. `t_cmd` is clamped
  to [-1, 1] and `dt_cmd` per axis to [-`MC_INDI_DT_MAX`, +] (default 1).
- **Landed / maybe_landed:** ground contact makes `a_f ~ 0` and the loop
  would integrate. Hold `t_f = 0` (reset `A` and `H` states) so the output
  is the bounded `G1^-1 nu` (acceleration P term), mirroring the PID freezing
  its integrator.
- **Disarmed / first run / selection change:** reset all states to zero.
- **dt:** use the module's clamped dt; recompute filter coefficients when
  the loop rate moves by > 10 % (as `vehicle_angular_velocity` does).
- **Non-finite input** (rate, setpoint, `a_f`, `G1 <= epsilon`): reset
  states, output zero torque increment for that cycle and set a fault flag
  in the status topic; parameters are validated (`G1` lower bound) at update.
- Static memory only; fixed-size `matrix::Vector3f` state.

## 8. Logging

Reuse `rate_ctrl_status` where possible; add the INDI internals (`nu`,
`a_f`, `t_f`, `dt_cmd`) to a new small uORB message `indi_rate_status`
logged by default in the benchmark profile, so tuning and the report can
plot the synchronisation directly.

## 9. Tests

Unit tests (gtest, beside `rate_control_test.cpp`): zero error gives zero
increment at steady state; closed loop with a simulated rigid body + first
order actuator converges to a rate step with the expected time constant
`1/K`; constant moment disturbance rejected without an integrator;
saturated allocator (`t_alloc` held) does not wind up; landed holds `t_f=0`;
NaN inputs give finite bounded output; G2 term reduces to G1-only law when
`G2_y = 0`.

## 10. Open items to verify in SITL before tuning

1. gz IMU and controller loop rate in `gz_x500` (sets filter design rate).
2. Actuator time constant and delay seen from `vehicle_torque_setpoint` to
   `xyz_derivative` (step identification, also gives `G1`).
3. Whether the gz x500 rotor links have inertia (determines if `G2_y` matters).

### Findings on the open items (session 5, from model files, not flown)

- Item 1: the gz x500 IMU runs at 250 Hz (`x500_base/model.sdf:260`), so in
  SITL the raw gyro rate, the filter rate and the rate-loop rate all equal
  250 Hz: the sensor-side and INDI-side filters are designed at the same
  rate. The backward difference adds half a sample (2 ms) on the sensor
  side, which `MC_INDI_DELAY` cannot represent (integer samples); expected
  to be minor, check in identification.
- Item 3: rotor link Izz = 2.65e-5 kg m^2 vs body Izz = 0.04 kg m^2, with
  `rotorVelocitySlowdownSim` 10. Rough hover estimate (omega ~ 757 rad/s,
  per-motor thrust 4.9 N): drag-torque sensitivity 2 km kf omega ~ 2.1e-4
  N m per rad/s, spin-up reaction Ir/tc ~ 2.1e-3 (or 2.1e-4 if the
  slowdown factor scales the joint inertia effect) per rad/s of step. The
  spin-up term is therefore not negligible in yaw transients: identify
  `G2_y` rather than assume 0. How the slowdown factor enters the physics is
  **[verify]** in the gz MulticopterMotorModel source.
- Body inertia Ixx = Iyy = 0.0217, Izz = 0.04 kg m^2, mass 2.0 kg (+ rotors).
