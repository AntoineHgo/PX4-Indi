# G1 analytic, roll, quad5in (stage 2, S42)

Source and parameter derivation only, no simulation. Units: G1 in rad/s^2 per unit normalised roll torque.

## Result

G1_roll = kT * w_max^2 * sqrt(2) * d / Ixx = 10.935 * 0.11243 / 1.400e-3 = **878 rad/s^2 per unit normalised roll torque**

Regression estimate: 320-435. The analytic value is 2.0-2.7x larger. The MC_INDI_G1_R default (320) sits at the bottom of the regression range.

Factors:

| factor | value | source |
|---|---|---|
| d (rotor arm, x and y) | 0.0795 m | `4040_gz_quad5in` lines 22-35 (CA_ROTORi_PX/PY); `quad5in/model.sdf` rotor joints |
| kT | 1.5e-6 N/(rad/s)^2 | `quad5in/model.sdf` lines 15, 32, 49, 66 (`motorConstant`) |
| w_max | 2700 rad/s | `quad5in/model.sdf` lines 14, 31, 48, 65 (`maxRotVelocity`); `4040_gz_quad5in` lines 49-52 (SIM_GZ_EC_MAX) |
| kT w_max^2 | 10.935 N (physical full-thrust per motor) | product of the two rows above |
| Ixx | 1.400e-3 kg m^2 | `quad5in_base/model.sdf` base ixx 1.022e-3 + 4 x (0.011 kg x 0.0795^2 m^2 + 2.5e-5) = 1.022e-3 + 3.78e-4 |
| CA_ROTORi_CT | not set in the airframe; default 6.5 | `src/modules/control_allocator/module.yaml` lines 207-220 (default 6.5, comment "Thrust = CT * u^2" at line 211) |

## Derivation

1. Allocator matrix. `ActuatorEffectivenessRotors.cpp` lines 194-197: thrust = ct * axis, moment = ct * (position x axis) - ct * km * axis. With axis = (0,0,-1), the roll (x) entry of rotor i is -ct * py_i, so the raw roll column is ct * (-py_i) = +/- ct * d.
2. Physical meaning of the actuator. `4040_gz_quad5in` line 43 and `THR_MDL_FAC` (`src/lib/mixer_module/motor_params.yaml`): rel_thrust = f * s^2 + (1-f) * s, with f = 1 (airframe line 54) so rel_thrust = s^2 with s = w / w_max. The allocator actuator a_i is therefore the normalised thrust u_i = (w_i / w_max)^2, and thrust_i = kT w_max^2 * a_i. This matches `IndiMeasuredTorque.hpp:39` (u = (omega/omega_max)^2).
3. Normalisation of the roll column. `ControlAllocationPseudoInverse.cpp` lines 87-117: with `_normalize_rpy` true, roll_norm_scale = sqrt(||col0||^2 / (n_nz/2)), and scale(0) = scale(1) = max(roll, pitch). Here n_nz = 4, so roll_norm_scale = sqrt(4 CT^2 d^2 / 2) = sqrt(2) CT d. Pitch gives the same value. `ControlAllocationPseudoInverse.cpp` lines 155-160 divide col(0) by scale(0), so the normalised roll entries are -py_i/(sqrt(2) d) = +/- 1/sqrt(2). CT cancels in this ratio.
4. Normalise flag. `ActuatorEffectivenessRotors.hpp` lines 96-99: getNormalizeRPY sets normalize[0] = true. `ControlAllocator.cpp` lines 169-198 passes it to each allocation.
5. Roll-only inversion. The roll row is orthogonal to the thrust, pitch and yaw rows: the dot products vanish, since the signs are (-,+,+,-) for roll, (+,-,+,-) for pitch, (+,+,-,-) for yaw, and (1,1,1,1) for thrust. So the pseudo-inverse solution for a unit normalised roll torque y is a_i = M_norm,i * y / sum_i M_norm,i^2 = M_norm,i * y / 2 = +/- 0.3536 y.
6. Physical roll torque. tau_x = sum_i (-py_i) * kT w_max^2 * a_i = kT w_max^2 * sqrt(2) * d * y = 1.2294 N m per unit y.
7. Angular acceleration. alpha_x = tau_x / Ixx, so G1 = 1.2294 / 1.400e-3 = 878 rad/s^2 per unit y. The sign is positive. The INDI law uses G1 as a per-normalised-torque gain (`indi_rate_control.cpp:381`, dt_cmd = numerator / g1), and McIndiRateControl.cpp:86 sets it from MC_INDI_G1_R/P/Y.

CT check. Physical kT w_max^2 = 10.935 N, while the allocator default CT = 6.5. With normalisation on, the CT factor cancels (step 3), so G1 does not depend on it. The CT mismatch only matters if normalisation is off, which it is not for rotors. Had normalisation been off, tau per unit y would be kT w_max^2 / CT = 1.68 N m and G1 = 1201.

## Why the analytic value is above the regression

The analytic value is 878, and the regression range is 320-435. A factor of 2.0-2.7 is not explained by the static analysis above. Candidate explanations, none checked:
- A regression on lagged data attenuates the static gain. The rotor time constants are 33 ms and the measured loop lag is 44-48 ms (`ref_airframe_model.md`), so the fit gain can sit well below the static gain.
- The regression may have used measured torque (IndiMeasuredTorque) rather than commanded torque, with a different normalisation.
- The regression may have been fitted with a different Ixx or d.

## UNVERIFIED

1. The sim allocator path. I did not read `ControlAllocationPseudoInverse::allocate()` to confirm that actuator = pinv(normalised mix) * control_sp, nor whether the torque setpoint is scaled before allocation.
2. The THR_MDL_FAC inverse. I read the parameter definition and the airframe value, not the code that applies rel_thrust = s^2 to the motor output.
3. Ixx. The sum assumes rotor z offset of 0 and base centre of mass at the origin. Rotor poses were not read from the SDF.
4. Thrust scaling by `rotorVelocitySlowdownSim` (10). The hover check in `ref_airframe_model.md` (eRPM 998.7 rad/s vs predicted 998.6) supports thrust = kT w^2, but I did not re-derive it.
5. The INDI law's torque path. I checked `indi_rate_control.cpp:381` only; I did not check whether the torque command is scaled elsewhere before allocation.
6. IndiMeasuredTorque.cpp lines 52 (emult with scale) and 63-80 (normalisation) were not read, so the measured-torque path's CT handling is unchecked.
7. The regression method and data were not examined. The factor 2.0-2.7 is unexplained.
8. No simulation was run, per the task.
