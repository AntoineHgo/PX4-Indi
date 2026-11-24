# Investigation B: draw 264 "joint" (sat 0.351 + weak motor 0.709), INDI LOC vs PID survives

## Summary (5 lines)
1. The joint fault is feasible: post-fault hover needs cmd ~0.39 (motors 0-2) and ~0.55 (weak motor 3), max 1.0; neither stack hits the actuator limit before INDI has already lost attitude.
2. The weak motor creates a thrust-proportional torque bias the allocator does not know (unallocated torque stays 0); INDI commands -0.07 roll/pitch torque and the rpm-measured torque stays ~0, a_f ~0, for ~1 s.
3. Cause: with the rpm measurement in use, INDI anchors the increment on measured torque (indi_rate_control.cpp:356), and with all motors at 0.351 effectiveness that anchor is a leaky, non-integrating loop: the bias is integrated only by the 1 s blend (MC_INDI_ACT_BLD, :340).
4. Weak alone (s=1): measured anchor = exact integrator, bias removed per cycle. Sat alone (b=0): only a 0.54x bandwidth loss. Both together: steady rate error G1*b/K ~ 6 rad/s needed > 3.8 rad/s rate limit -> runaway tilt, then the outer loop raises thrust, the bias grows with it.
5. PID survives because its P (0.03/(rad/s)) is ~2.6x INDI's effective K/G1 (0.011) when a_f~0 and its I term does not depend on actuator effectiveness; fix direction: restore integral action in the measured-anchor path when command and measurement disagree persistently (faster/adaptive blend or model anchor), unverified.

## Fault as injected (logs + indi_flight/bench/g3_run.py:214-219, bench/tests/test_run_scenario_hooks.py:31)
- SIM_GZ_EC_MAX change (rotor-speed ceiling x sqrt(scale)): INDI log t=58.23-58.34 s, PID log t=58.89-59.00 s.
  Motors 1-3: 2700 -> 1600 (thrust x0.351); motor 4 (index 3): 1347 (x0.249 = 0.351*0.709).
- A command->rpm gain change, not a thrust-coefficient change: ESC rpm reports the true rotor speed, so the
  rpm-based measured torque (IndiMeasuredTorque.cpp:182-187, u=(w/MC_INDI_W_MAX)^2, W_MAX=2700) is physically right.
- Pre-fault hover: cmd 0.137, 9542 rpm = 999 rad/s, (999/2700)^2 = 0.137 (thrust-linear command).

## Q1 Feasible set and which stack stays inside it
- Post-fault hover: cmd (999/1600)^2 = 0.39 on motors 0-2, (999/1347)^2 = 0.55 on motor 3. Motor 3 can reach
  1.8x its hover thrust, the others 2.6x: hover plus moderate roll/pitch torque is feasible (total available
  thrust ~0.32 of nominal max, ~2.3x hover at nominal mass; MPC_THR_HOVER 0.137).
- The allocator (CA_METHOD 2) does not know motor 3 is weak: unallocated torque/thrust = 0 throughout (until
  INDI saturates motor 3 at 1.0, t=60.0, unallocated thrust -0.23). The weak motor shows up as a bias: equal rpm
  requires motor 3 cmd = 1.41x the others (observed 0.66 vs 0.46 at 59.0, 0.83 vs 0.59 at 59.35), i.e. a
  torque command of ~-0.07 roll and pitch just to produce zero torque; the bias scales with collective thrust.
- INDI (inv_B/indi_fine.py, series.py): fault at 58.23 during a small tilt manoeuvre (tilt 2-5 deg). From 58.5 to
  59.35: rates p,q = +1.0..+2.4 rad/s against sp -3.8 (MC_*RATE_MAX 220 deg/s saturated), nu -80..-105 rad/s^2,
  a_f ~ 0, measured torque ~0.00, torque sp -0.05..-0.08, increment stuck at ~-0.05 (= nu/G1), blend (t_f - t_meas)
  grows only -0.002 -> -0.036 in 1 s. Tilt 17 -> 2 (passing upright) -> 61 deg at 59.35; 87 deg at 60.0.
  Outer loop raises thrust 0.14 -> 0.65 (59.35) -> 1.0 (60.0) as altitude drops; motor 3 saturates only at 60.0,
  after the loss. So the INDI stack leaves the feasible set only as a consequence, not the cause.
- PID (fault 58.9-59.0, also during a tilt manoeuvre, tilt 13-17 deg at fault): rates bounded (|p,q| <= 1.1 rad/s),
  tilt 14-30 deg, thrust sp peaks 0.60, motor 3 max 0.78 (inside limits), torque sp -0.06..-0.08 roll/pitch
  built from P (0.03/(rad/s)) plus integrator reaching -0.075 by 61.0 (rate_ctrl_status). Altitude 5.0 -> 2.1 m.
  The PID integrator rises at ~0.035/s, about the same rate as the INDI blend: the difference is the
  proportional path, not a faster integrator.

## Q2 Mechanism in the INDI law (src/lib/indi_rate_control/indi_rate_control.cpp)
- :272 model torque = actuator lag on torque_allocated_prev = previous torque sp minus unallocated
  (McIndiRateControl.cpp:226-230); unallocated = 0 here so the model says the commanded -0.07 was produced.
- :302 measured torque (rpm) used once valid (:328, measured_torque_in_use = 1 throughout the logged window).
- :334-356 t_f = t_f_meas + blend, blend = first-order LPF (tc = MC_INDI_ACT_BLD = 1.0 s) of (model - meas).
- :458/:472 t_cmd = t_f + (nu - (1+c) a_f + c spdot)/G1, G1 = 1757/1640 (nominal effectiveness).
- Algebra (per axis, ignore lag): true torque tau = s*(t_cmd - b) with s = 0.351 (sat), b = weak-motor bias in
  command units. With the measured anchor t_cmd_k = tau_{k-1} + Delta = s*t_cmd_{k-1} - s*b + Delta:
  * s = 1 (weak alone): t_cmd integrates (Delta - b) every cycle -> bias removed at sample rate. Survives.
  * b = 0 (sat alone): tau = s*Delta/(1-s) -> loop bandwidth x0.54, no bias, survives.
  * s < 1 and b != 0 (joint): leaky loop, fixed point needs Delta = b, i.e. nu = G1*b ~ 1757*0.07 = 123 rad/s^2,
    rate error ~6 rad/s > the 3.8 rad/s rate-sp limit. Matches the log: Delta ~ -0.05, tau ~ 0, a_f ~ 0.
  Only the blend integrates b, with tc 1 s; meanwhile tilt grows, the outer loop raises thrust, b grows with
  thrust (positive feedback) and the blend never catches up.
- Not causal here: DT_MAX = 1.0 (increment unclamped), no allocator saturation before 60.0, no fault flag.

## Q3 Most likely cause
Single cause: loss of integral action in the measured-torque-anchored INDI rate loop when a uniform effectiveness
loss (s = 0.351) coexists with an unmodelled per-motor bias (weak motor): measured anchoring
(indi_rate_control.cpp:356) makes the loop leaky, and the only integrator left is the 1 s complementary blend (:340).
Evidence: tau_meas ~ 0 and a_f ~ 0 for ~1 s while t_cmd = -0.07 and nu ~ -100; increment pinned at nu/G1; blend
ramps ~0.035/s; each factor alone survives exactly as the algebra predicts.
Falsify: (a) re-fly joint with MC_INDI_ACT_BLD = 0 is not a falsifier (pure meas, worse); instead re-fly joint with
the measured torque disabled (model anchor, e.g. MC_INDI_ERPM_TO tiny or rpm invalid) -> should survive; if it
still diverges the cause is elsewhere. (b) A shorter blend (e.g. 0.1-0.2 s) should survive; (c) weak 0.709 with
sat at s ~ 0.8 should still survive while s ~ 0.35 fails.
Fix direction: keep the low-frequency anchor on the commanded (model) torque so increments integrate, and use the
rpm measurement only for the high-frequency part with a much shorter blend, or detect a persistent
command/measurement gap (per axis, with a_f ~ 0 under large nu) and transfer it into the anchor quickly (or feed a
per-motor effectiveness estimate from rpm vs command to the allocator so b becomes allocatable). Watch interaction
with the outer loop thrust rise (bias grows with thrust).

## Not verified
- rates_sp_applied in indi_rate_status logs 0 while vehicle_rates_setpoint is -3.8 and nu = 20*(-3.8 - p) holds:
  the field seems not to carry the effective setpoint outside injection; not checked in code.
- Exact torque-per-command scale of the bias (b ~ 0.07 inferred from equal-rpm motor commands, not computed from
  the effectiveness matrix); s/(1-s) algebra ignores actuator lag, sync filters and the lead term (c = 0.66).
- No re-fly done (forbidden): the falsification runs above are proposals only.
- Pre-fault tilt manoeuvres differ in phase between the INDI and PID runs (fault at 58.23 vs 58.9 s on the same
  schedule? INDI tilt 2-5 deg at fault, PID 13-17 deg): not traced to the schedule anchor.

## Consistency with earlier write-ups (read last)
- restore264/README.md: sat alone and weak alone remove the LOC, joint keeps it, PID survives joint (max tilt 38 deg).
  Consistent with the algebra above (each factor alone is benign; the product s<1 and b!=0 is not).
- q31_injector_fix_s214/README.md:45-50 already inferred the leaky measured anchor (tau_real ~ 0.54 x increment) and
  framed it as the nominal-W_MAX normalisation of the rpm. Same mathematics; this report differs on two points:
  (1) the rpm measurement itself is physically correct, what changed is the command->torque gain the allocator and
  G1 assume; (2) the 0.54 gain loss alone (sat alone) does not lose control: the decisive element is the weak-motor
  bias b, which a leaky anchor cannot integrate, leaving only the 1 s blend. Q31's open question "why PID recovers
  with the same 0.35" is answered by PID's I and P paths not passing through a measured-torque anchor.
