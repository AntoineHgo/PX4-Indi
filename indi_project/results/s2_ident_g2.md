# O-4: does gz transmit the rotor reaction torque, and how large is G2_y? (session 32)

## Source check

`research/raw/gz_sim8/MulticopterMotorModel.cc` (gz-sim 8, velocity motor type): the plugin computes thrust and
drag torque from the joint velocity x `rotorVelocitySlowdownSim` (10) and applies them as a wrench on the parent
link; it has no explicit rotor-inertia (G2) term. The rotor speed is imposed through `JointVelocityCmd`
(lines 686-690) on a revolute joint `base_link -> rotor_i` with no effort limit (x500_base `model.sdf`), and
the rotor link has izz = 2.65e-5 kg m^2. A velocity command is enforced by the physics engine as a joint
constraint between the two links, so the constraint torque that spins the rotor up reacts on `base_link`, but
at joint speed = true speed / 10. The DART side (gz-physics `SetJointVelocityCommand`) was NOT read; this
step is from memory and is why the data check below was done.

Prediction if transmitted: yaw accel = a * sum s_i w_i^2 + b * sum s_i w_i_dot with
b/a = (J_rotor / 10) / (k_f k_m) = 2.65e-6 / (8.549e-6 * 0.016) = 19.4 s. If not transmitted, b = 0.

## Identification from flight data

Script: `bench/identify_g2.py` (integral form over 50 ms windows: no gyro differentiation; rotor-speed
regressors pass the same 40 Hz 2nd-order low-pass as the logged gyro rate, i.e. matched filtering).
Data: 12 v2 PID `step_yaw` logs (s2 tuning r1/r2/ref), 58 540 windows.

| esc_rpm shift [ms] | a (per w^2) | b (per rad/s^2) | b/a [s] | R^2 | R^2 without b |
|---|---|---|---|---|---|
| -2 | 3.051e-6 | 1.148e-4 | 37.6 | 0.9813 | 0.962 |
| 0 | 3.055e-6 | 1.057e-4 | 34.6 | 0.9810 | 0.965 |
| 1 | 3.058e-6 | 1.011e-4 | 33.1 | 0.9808 | 0.966 |
| 2 | 3.060e-6 | 0.965e-4 | 31.6 | 0.9807 | 0.967 |
| 4 | 3.064e-6 | 0.873e-4 | 28.5 | 0.9810 | 0.970 |

- a matches the SDF exactly enough to validate the method: k_f k_m / a gives Izz = 0.0447 kg m^2
  (base 0.040 + rotors/arms).
- Plausible esc_rpm latency is 0-2 ms (s31 actuator identification): b/a = 32-35 s, b = 1.0e-4.
- **Without filter matching the estimate is confounded**: on the raw logged rate, a 14 ms shift of esc_rpm
  fits as well (R^2 flat 0.981) with b/a 4.7 s. The matched-filter fit above is the one used.

## Conclusion

The simulator DOES transmit a rotor-acceleration reaction torque to the body: a yaw term in sum s_i w_i_dot is
needed (R^2 0.966 -> 0.981), with the expected sign. Its size is ~1.7x the J_rotor/10 prediction (b/a 33 s vs
19.4 s); the excess is unexplained (DART servo internals not read). It is also ~10x smaller than physical
(the joint turns at 1/10 speed), so G2 in this simulator under-represents a real vehicle, where
b/a = J_rotor/(k_f k_m) would be ~194 s for the same rotor.

In the v1 controller's units (MC_INDI_G2_Y, rad/s^2 per unit normalised yaw torque per s), linearising
Delta(sum s w^2) = 2 w_bar Delta(sum s w) at hover (w_bar ~ 769 rad/s) with G1_Y = 7.4:
**MC_INDI_G2_Y ~ (b/a) G1_Y / (2 w_bar) ~ 0.16** (0.15-0.17 over the latency range). This is ~8x the param
description's "~G1_Y x loop period" guideline, and it depends on the thrust level through w_bar, which
disappears in the u = w^2 formulation (O-6), where b is used directly.

NEXT (labelled post-acceptance, as O-3): re-fly the frozen v1 INDI with MC_INDI_G2_Y 0.16 on the tuning
set and H5 (10 seeds), after PID r2 ends and SITL is rebuilt.
