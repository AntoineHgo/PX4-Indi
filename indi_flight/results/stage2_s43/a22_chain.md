# A-22 roll G1 chain, source trace and per-link gains (S43)

Log: `indi_flight/results/stage2_s41/model_long_s2/flight.ulg`, window 52-82 s, roll injection amplitude 0.005 (MC_INDI_INJ_AX=1, rms inject 0.015, rms u 0.044).
Script: `indi_flight/bench/a22_chain.py` (IV estimator H = S_dy/S_dx with the logged `inject[0]` as instrument, 10 s Hann segments, 50% overlap; lines at 2.5, 5.0, 7.9 Hz). No simulation was run.

## Result in 5 lines

1. The analytic 878 is wrong in two links, not in the plant: link (c) (roll-differential of normalised thrust x=(w/wmax)^2 -> alpha) is 626 measured against 621 analytic (kT, wmax, d, Ixx all confirmed, using ground-truth rate differentiated spectrally).
2. Link (a), torque_sp -> roll-differential of actuator_motors, is 0.92 (per-motor column 0.23, signs -,+,+,-), against 1.414 assumed in the analytic (0.65x). The source reading of the allocator gives 0.707 per motor (2.83 differential), so the log disagrees with the source by 3x. Unresolved.
3. Link (b), actuator_motors -> x=(w/wmax)^2, is 0.59 at hover (DC, a=0.221 gives w=976 rad/s, x=0.131), against 1.0 assumed. `actuator_outputs` (command sent to gz, mean 974 rad/s) shows the loss happens before gz, between actuator_motors and the gz command. Unresolved in source.
4. Product (a)(b)(c) = 0.92 x 0.59 x 626 = about 340 static, which reproduces the regression/default (320-435); 878 x 0.65 x 0.59 = 337. In-band the plant behaves as first order, tau_eff 35-44 ms (phase of u -> d/dt p_gt: -29, -53, -65 deg at 2.5, 5, 7.9 Hz).
5. Use G1 about 340 (static, unit normalised roll torque) for the margin analysis, not 878. The regression is not biased by lag in the way A-22 suspected: it measures the real chain. The cause of links (a) and (b) is not found in the source; see UNVERIFIED.

## Source chain table

| # | link | file:line | small-signal gain at hover from source |
|---|---|---|---|
| 1 | INDI computes c, adds injection d, `torque_sp = c + d` (this is `indi_rate_status.torque_sp`, the injected value) | `src/modules/mc_indi_rate_control/McIndiRateControl.cpp:201-219` | 1 |
| 2 | published as `vehicle_torque_setpoint.xyz[0]` = same u (log: max abs difference to `torque_sp` 7.7e-4, interpolation only) | `McIndiRateControl.cpp:337-352` | 1 |
| 3 | allocator takes `c(0) = _torque_sp(0)`, no extra scaling | `src/modules/control_allocator/ControlAllocator.cpp:379-419` | 1 |
| 4 | mix = geninv(effectiveness); roll column of mix (ct=6.5, d=0.0795) = -/+ 1/(4 ct d) = 0.4838; roll_norm_scale = sqrt(norm2/(n/2)) = 0.684; column divided by it | `src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp:70-117,155-160` | source gives a_i = +/-0.707 u (differential 2.83), NOT 0.354 as in g1_analytic.md step 5 (it normalised the forward matrix; the code normalises the pseudo-inverse). Numerically checked with numpy. Log shows 0.23. |
| 5 | thrust column normalised to a_i = T_sp (scale = norm_sum/n = 0.0385, so a_i = thrust_sp) | `ControlAllocationPseudoInverse.cpp:126-170` | hover a = 0.221 = `vehicle_thrust_setpoint.z` mean -0.2211 = hover estimator 0.2211 (MPC_THR_HOVER=0.137 is not what is flown) |
| 6 | `actuator_motors` published from `_actuator_sp` after clip | `ControlAllocator.cpp:446-458` | 1 |
| 7 | THR_MDL_FAC applied in the mixer output stage: s = -b/(2a)+sqrt(b^2/(4a^2)+a_i/a), f=1 gives s = sqrt(a_i) | `src/lib/mixer_module/functions/FunctionMotors.hpp:81-95`, `mixer_module.cpp:270` | ds/da = 1/(2 sqrt(a)) = 1.06 at a=0.221, so x = s^2 = a (gain 1) |
| 8 | output = interpolate(s, -1..1 -> min..max) (SIM_GZ_EC_MIN 0, MAX 2700, `4040_gz_quad5in`:37-45) | `mixer_module.cpp:565` | w_cmd = 2700 s = 1269 rad/s at a=0.221 |
| 9 | gz_bridge multiplies motor outputs by sqrt(SIM_GZ_THR_SC) (=1.0 in the log parameters, no changed parameters logged) | `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.hpp:82-83`, `GZMixingInterfaceESC.cpp:108` | 1 |
| 10 | gz velocity motor: lag 0.033 s, thrust = kT w^2, kT 1.5e-6, wmax 2700, slowdown 10 | `indi_flight/sim/models/quad5in/model.sdf:12-22` | x = (w/wmax)^2 with first-order lag 33 ms |
| 11 | eRPM telemetry: rpm = rotor joint speed * 60/2pi (`GZMixingInterfaceESC.cpp:206`), eRPM = rpm * pole_pairs (7), converted back to rpm by the dshot-like decode (`:214-240`); so w[rad/s] = esc_rpm * 2pi/60 | `GZMixingInterfaceESC.cpp:136-240` | 1 plus quantisation and a one-frame reply delay |
| 12 | roll torque = sum(-py_i) kT wmax^2 x_i, alpha = tau/Ixx | analytic derivation | 621 rad/s^2 per unit sum(s_i x_i) |
| 13 | alpha_filtered: gyro derivative filtered by LPF2p IMU_DGYRO_CUTOFF=20 Hz in `vehicle_angular_velocity` (`xyz_derivative`), copied by INDI (`McIndiRateControl.cpp:265,221`), `src/modules/sensors/vehicle_angular_velocity/VehicleAngularVelocity.cpp:775-786` | gain 0.99, 0.97, 0.92 and phase -13, -25, -39 deg vs the true derivative at 2.5, 5, 7.9 Hz (measured) |

Predicted small-signal G1 from source as read: 2.83 x 1.0 x 621 = 1756 (links 4,7,10,12). The analytic estimate 878 used 1.414 for link 4. The log gives 340. Source and log disagree on links 4 and 7-9.

## Per-link gains from log

Signs of the roll differential: s = (-1,+1,+1,-1) for motors 0..3 (-py_i). IV = instrumented by the injected signal; pooled = sum over the 22 injection lines in 2-10 Hz; LS = plain S_xy/S_xx (closed-loop, slightly biased).

| link | 2.5 Hz | 5.0 Hz | 7.9 Hz | pooled IV 2-10 Hz | LS |
|---|---|---|---|---|---|
| (a) u -> motor0 | 0.203 @ +166 | 0.211 @ -166 | 0.222 @ -167 | 0.228 @ -175 | 0.221 |
| (a) u -> motor1 | 0.231 @ -8 | 0.211 @ +14 | 0.245 @ +22 | 0.239 @ +11 | 0.222 |
| (a) u -> motor2 | 0.331 @ +7 | 0.256 @ -9 | 0.259 @ -19 | 0.233 @ -10 | 0.245 |
| (a) u -> motor3 | 0.339 @ -166 | 0.255 @ +170 | 0.261 @ +171 | 0.230 @ +178 | 0.241 |
| (a) u -> sum s_i motor_i | 1.084 @ +2 | 0.913 @ +1 | 0.947 @ +1 | 0.921 @ +1 | 0.910 |
| (b) motor_i -> x_i (avg of four) | 0.81 @ -30 | 0.52 @ -57 | 0.36 @ -70 | 0.40 @ -40 | 0.45 @ -58 |
| (b) rdiff_m -> rdiff_x | 0.768 @ -32 | 0.526 @ -57 | 0.361 @ -69 | 0.404 @ -39 | 0.468 |
| (c) rdiff_x -> alpha_filtered | 620 @ -11 | 605 @ -24 | 581 @ -37 | 490 | 594 |
| (c) rdiff_x -> d/dt p_gt (ground truth) | 626 @ +2 | 627 @ +2 | 632 @ +2 | n/a | n/a |
| end-to-end u -> alpha_filtered | 517 @ -42 | 290 @ -79 | 198 @ -105 | 183 | 246 |
| end-to-end u -> d/dt p_gt | 521 @ -29 | 301 @ -54 | 216 @ -66 | n/a | n/a |

Static (DC) values from the same log (steady 52-82 s):

| quantity | value |
|---|---|
| mean actuator_motors (all four) | 0.2211 |
| mean esc rpm -> w | 976 rad/s, x = 0.1307 (eRPM conversion w = rpm*2pi/60, WMAX 2700) |
| mean actuator_outputs (command to gz) | 974.5 rad/s (965, 973, 971, 987), consistent with eRPM |
| sqrt(a)*2700 expected at THR_MDL_FAC=1 | 1269 rad/s |
| x / a | 0.591 (command/expected = 0.769 in w) |

Observations:
- (c) matches the analytic 621 within 1-2% with the ground-truth rate, and its phase is zero, so kT, wmax, d and Ixx are right. `alpha_filtered` differs from the true derivative only by the 20 Hz D-term filter.
- (a) has the correct allocator column pattern (-,+,+,-), real (phase 0 or 180 deg), flat in frequency, magnitude 0.23 per motor. It is a static scaling, not a lag.
- (b) magnitude falls with frequency as 0.59 / sqrt(1+(2 pi f tau)^2) with tau 33 ms at 5 and 7.9 Hz (predicted 0.41 and 0.31 against measured 0.52 and 0.36); phase gives tau_eff 40-52 ms (33 ms motor plus telemetry delay). The 2.5 Hz value is noisy (per-motor 0.57-1.08).
- The multiplicative decomposition closes: at 2.5 Hz 1.084 x 0.768 x 620 = 516 (measured 517), at 5 Hz 0.913 x 0.526 x 605 = 291 (290), at 7.9 Hz 0.947 x 0.361 x 581 = 199 (198).
- Static G1 = (a)(b)(c) = 0.92 x 0.591 x 626 = 341 per unit u.
- Fitting end-to-end u -> d/dt p_gt with tau = 33 ms lag only gives G = 585, 435, 415 at 2.5, 5, 7.9 Hz; the 2.5 Hz value is high, so the regression value depends on which frequencies and what lag are assumed (320-435 is the right order). The in-band magnitude at 2.5 Hz exceeds the DC-derived 341/0.89 = 383, which is not explained (noise in the lowest lines, or a small-signal slope of the a -> command map different from the secant 0.59).
- Window check: static a -> command map in the same log: a = 0.081 gives out/2700 = 0.283 (sqrt(a) = 0.284, matches), a = 0.221 gives 0.361 (sqrt = 0.470). The compression appears only at higher a, so the map is not sqrt(a) times a constant.

## Conclusion

- Predicted small-signal G1 at hover from source as read: 1756 (allocator 0.707/motor), analytic 878 (0.354/motor). Both assume actuator thrust = a.
- Measured G1 from the links: 341 static, 380-600 in-band magnitudes before lag removal (517 at 2.5 Hz falling to 198 at 7.9 Hz because of the 33-44 ms plant lag). The regression 320-435 and MC_INDI_G1_R=320 are consistent with the plant; they are not a lag artefact. The analytic 878 is the wrong number for this sim as run.
- Which assumption was wrong: both (1) the allocator roll column (0.23 measured per motor vs 0.354 assumed, 0.65x) and (2) actuator_motors = normalised thrust (0.59 measured, THR_MDL_FAC=1 and SIM_GZ_THR_SC=1 predict 1.0). Link (c) was correct. Together 0.65 x 0.59 = 0.38; 878 x 0.38 = 337, in the observed 320-435 band.
- For the inner-loop margin analysis use G1 about 340 per unit normalised roll torque with a first-order plant lag tau_eff 35-45 ms, which is what MC_INDI_G1_R=320 approximately encodes; 878 would overstate the loop gain by about 2.6x.

## UNVERIFIED

1. Why `actuator_motors` per unit roll torque is 0.23 per motor when the source gives 0.707 (the log's `ver_sw` is 32500e0276; the checked-out source is at a later commit, and the binary behind the log may differ). Not checked: `ControlAllocationPseudoInverse::allocate()`, `dropDependentAxes`, `setEffectivenessMatrix` normalisation flag path, `ActuatorEffectivenessRotors::getNormalizeRPY`, saturation or airmode (MC_AIRMODE=0), and whether `unallocated_torque` in `control_allocator_status` is non-zero. A direct check of `control_allocator_status.torque_setpoint_achieved` over the window would test saturation.
2. Why actuator_outputs (command to gz, 974 rad/s) is 0.769 of sqrt(a) x 2700 = 1269 at a = 0.221 though THR_MDL_FAC=1 and SIM_GZ_THR_SC=1.0; the map matches sqrt(a) at a=0.08 and departs near hover. The logged parameters show no runtime change. Not checked: `MixingOutput::limitAndUpdateOutputs` motor path (slew, min/max, any idle or battery scaling), whether SIM_GZ_THR_SC is changed at runtime by the bench harness, and the SDF actually loaded by gz. Note also that `MPC_THR_HOVER` (0.137) corresponds to x, while the hover estimator learned 0.221 = 0.137/0.62.
3. In-band small-signal slope of the a -> command map (a = 0.2208 to 0.2326 gives ds/da = 0.63 against 1.06 for sqrt(a) at THR_MDL_FAC=1) was not measured at the injection amplitude.
4. The 2.5 Hz line magnitude (517 end-to-end, vs about 383 predicted from the DC chain) is not explained.
5. The eRPM-to-rad/s conversion was read from `GZMixingInterfaceESC.cpp:206-240` and confirmed by the match between esc rpm (976) and actuator_outputs (974.5); telemetry quantisation was not quantified.
6. Rotor thrust law in gz (kT w^2, slowdown 10) is not re-derived; it is supported by link (c) = 626 against 621.
