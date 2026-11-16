VERDICT: BLOCKING

# Independent review r1 of `stage2_margins_s35.md` (11 tool calls, no build/sim)

Confirmed correct: the section 3 sign. With x = post-injection, y = pre-injection, the loop gives y = -L x, so x = d/(1+L) and
L = -G_yd/G_xd. This holds at M1 (gyro) and at M2/M3 (y = u_pre, x = u_post). The blend formula (l.113-114) matches
`indi_rate_control.cpp:320-340`: t_f = t_meas + LPF_Tb(t_model - t_meas), alpha = dt/(Tb+dt), clamp kMaxBlend 2 (`hpp:252`).
The 4.1 model-only L (l.112) is correct for a break at u. The A-chain H = LPF2p(40) -> d/dt -> alpha(20) matches
`VehicleAngularVelocity.cpp:184-189,777-782` (an AlphaFilter on the derivative of the low-passed gyro).

## Findings
1. BLOCKING. Note l.23-24, l.30-31, l.56, l.154. M1 (gyro) is NOT a full break of the INDI rate loop, and "SISO loop gain
   must agree at any break point" is false for INDI. Two feedback paths do not go through the gyro:
   (a) Model path: torque_setpoint -> `_prev_torque_setpoint` (`McIndiRateControl.cpp:331`, read at :181) -> t_act/H -> t_f -> u.
   (b) Measured path: u -> gz rotor -> joint_state rpm (`SIM_GZ_ESC_FB`=1, `run_scenario.py:659`;
       `GZMixingInterfaceESC.cpp:41-47,147`) -> esc_status -> `IndiMeasuredTorque` -> t_f -> u.
   M1 therefore measures L_gyro = L_o/(1+L_i), where L_o is the gyro paths (K*e, a_f) and L_i is the t_f path. M3a measures
   L_u = L_o + L_i. The two share closed-loop poles (1+L_u = (1+L_i)(1+L_gyro)) but their margins differ. At low frequency
   1+L_i ~ 1 - H A_m -> 0, so L_gyro is near double-integrator-like, nothing like (K/s). M2 also leaves path (a) unbroken:
   `_prev_torque_setpoint` is taken before the allocator and gz. M2 cuts (b) only, so it gives a third, different L.
   Correction: for INDI, make M3a the primary, plant-input break; it cuts both paths (see 6). Report M1 as the sensor-side
   loop-at-a-point and model it as L_o/(1+L_i). Drop the M1-vs-M2 agreement key for INDI. Keep it for PID, where the loop is
   single (no internal torque feedback).
2. MAJOR. Note l.120 (4.2): the D sign is wrong. mc_rate_control applies D on the measured acceleration with a minus sign
   (u = Kp e + Ki/s e - Kd w_dot), so -du/dw = Kp + Ki/s + Kd s. Correction: L = [(Kp + Ki/s) F_w + Kd s F_w a_d] G1 eta A_r / s,
   where the D filter is F_w times alpha(IMU_DGYRO 20 Hz), because the derivative is taken after the gyro LPF.
3. MAJOR. Note l.113-118 and 4.3. The default MC_INDI_ACT_BLD is 0.0 (`mc_indi_rate_control_params.yaml:140-145`), and in
   code Tb = 0 means pure MEASUREMENT (`indi_rate_control.cpp:339`, t_f = t_f_meas). In the note's formula, Tb -> 0 gives
   B = 1/(1+sTb) -> 1, which is the MODEL (the same as alpha = 1 in code). The default stack is therefore the B = 0 case
   (Tb -> infinity in the formula), and the formula is discontinuous at Tb = 0. Correction: state the mapping explicitly.
   For the default, the LF reduction is L = eta K/s, with no blend mode.
4. MAJOR. Note l.124-126: the zeta values are wrong. From the note's own polynomial Tb s^2 + eta(1+K Tb)s + eta K, with K = 20:
   - Tb 1.0: zeta = 1.17 (eta 0.25) to 1.66 (eta 0.5), not ~0.75. The mode is overdamped, with real poles at -1.2/-4.1 and
     -1.05/-9.5. That gives a slow pole at ~1 rad/s, a candidate for slow fault recovery that the note does not list.
   - Tb 0.03: zeta = 0.52-0.73, not ~0.3.
   - Tb 0.3: zeta = 0.71-1.01 (the note gives none).
   The Tb 0.1 values (7.1-10 rad/s, zeta 0.53-0.75) check out.
5. MINOR. Note l.115 and l.118. The residual term is H eta A_r (1 - e^{-snT}), which vanishes for n = 0 whatever eta is. The
   self-check "eta = 1, Tb any -> L = (K/s) F_w A_r" is wrong: what remains is H (A_r - A_m)/(1+sTb), which is nonzero by
   default because tau_m = 0.02 s (MC_INDI_ACT_TC, yaml:102-107) and tau_r = 0.033 s (quad5in/model.sdf:12-13). Correction:
   the reduction holds only if n = 0 and A_m = A_r.
6. MINOR. Note l.34 (M3a). The injection must be added to `vehicle_torque_setpoint.xyz` before both the publish (:329) and the
   store into `_prev_torque_setpoint` (:331). Otherwise path (a) stays closed and M3a degrades to an M2-like break. Check the
   same point for M3b: whether the accel-loop t_f is built from the post-injection t_c.
7. MINOR. Note l.89-90. The empirical DM check (k samples of gyro delay -> PM drop = w_c k T_s) is exact only for L_gyro (M1),
   where the delay multiplies the whole loop. On L_u (M3a), the delay also desynchronises a_f from t_f and changes |L|.
   Use w_c of the M1 loop.
8. MINOR. Note l.108 and task brief. The reference model is `indi_flight/sim/models/quad5in{,_base}`, not
   `Tools/simulation/gz/models` (`run_scenario.py:31`). The airframe is `ROMFS/.../airframes/4040_gz_quad5in`.
9. MINOR. Note l.138. SIM_GZ_THR_SC scales the rotor speed by sqrt(sc), so thrust and torque both scale by sc. With
   ESC_FB = 1, the measured rpm sees the scale, so the measured path tracks eta and the model path does not. This matches the
   4.1 assumptions. At eta = 0.5 the hover command roughly doubles: check the motor ceiling [.2, .85] (l.72) in the pre-test.

## UNVERIFIED table
| Note line | Item | Status | Evidence / correct fact |
|---|---|---|---|
| 26 | gyro-bias estimator ignores >= 0.5 Hz | UNVERIFIED | not read (EKF2 gyro-bias process noise / IMU cal) |
| 30 | CA_ROTOR*_PX/PY/KM | VERIFIED | 4040_gz_quad5in:19-36, arms +-0.0795 m, KM +-0.01267 = SDF momentConstant |
| 39 | msg versioning for new .msg | UNVERIFIED | not read |
| 45 | offboard accepts velocity-only rows | UNVERIFIED | not read |
| 49 | Python wrench timing | UNVERIFIED | not read |
| 50 | mass from SDF | VERIFIED | quad5in_base/model.sdf:10 0.566 + 4x0.011 (l.235) = 0.610 kg, matches 4040:64 |
| 56 | sensor_gyro 800 Hz | VERIFIED | quad5in_base/model.sdf:174 update_rate 800; run_scenario.py:36 |
| 58 | EKF output rate ~50-100 Hz | VERIFIED (100 Hz) | ekf2/module.yaml EKF2_PREDICT_US default 10000 us; no airframe override seen |
| 87 | MC_INDI_ERPM_DLY default 1 | VERIFIED | mc_indi_rate_control_params.yaml:121-126 |
| 104 | MC_INDI_ACT_TC 0.02, MC_INDI_DELAY 0 | VERIFIED | yaml:102-107, :113-118 |
| 107 | G1_R 320, K_R 20 | VERIFIED | yaml:29-34, :69-74 |
| 108 | gz motor tau | VERIFIED | quad5in/model.sdf:12-13 timeConstantUp/Down 0.033 s (all 4 rotors) |
| 121 | PID gains, MC_*RATE_K | PARTLY | MC_ROLLRATE_P 0.03 (4040:70); I, D, K not read |
| 126 | attitude gain | VERIFIED | MC_ROLL_P 8.0 (4040:79), used by INDI att (McIndiPosControl.cpp:107); w_n 7-10 at Tb 0.1 is near crossover |
| 139 | SIM_GZ_THR_SC scales all motors | VERIFIED | gz_bridge/module.yaml:135-141 ("all motors", rotor speed x sqrt) |
| - | joint_state rpm vs rotorVelocitySlowdownSim 10 scaling | UNVERIFIED | quad5in/model.sdf:21; check gz_bridge rpm conversion before trusting t_meas |
