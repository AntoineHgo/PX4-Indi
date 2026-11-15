# Reference airframe check (second key)

Input: `indi_flight/design/ref_airframe_data.md`. No web access; arithmetic, physics plausibility and the gz mapping only.
Sources read for the mapping: `Tools/simulation/gz/models/x500_base/model.sdf`, `Tools/simulation/gz/models/x500/model.sdf`,
`ROMFS/px4fmu_common/init.d-posix/airframes/4001_gz_x500`, `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.{cpp,hpp}`,
`src/lib/mixer_module/motor_params.yaml`, `src/modules/mc_pos_control/*params.yaml`, and the plugin source
`indi_project/research/raw/gz_sim8/MulticopterMotorModel.cc` (read only). Literature numbers (papers, MQTB page) are UNCHECKABLE here
except where they can be recomputed from the quoted table rows.

Verdicts: OK / WRONG (correct value given) / UNCHECKABLE.

## 1. Derived numbers

| # | Item | Table value | Recomputed | Verdict |
|---|------|-------------|------------|---------|
| 1 | W = m g (0.610 kg) | 5.98 N | 5.984 N | OK |
| 2 | T_max = 4 kT wmax^2 | 47.0 N (11.76/motor) | 47.04 N (11.76/motor) | OK |
| 3 | T/W | 7.9 | 7.86 | OK |
| 4 | Hover speed, kT=1.5e-6 | 998 rad/s, 9,540 rpm | 998.7 rad/s, 9,537 rpm | OK |
| 5 | Hover speed, kT=1.25e-6 | 1094 rad/s, 10,450 rpm | 1094.0 rad/s, 10,447 rpm | OK |
| 6 | Hover speed fraction w_h/wmax | 0.36-0.39 | 0.357 / 0.391 | OK |
| 7 | Hover u=(w_h/wmax)^2 (thrust fraction) | 12.7 % | 0.1272 | OK |
| 8 | kQ/kT | 0.0127 m (0.01267 in SDF) | 0.012667 | OK |
| 9 | Kaufmann kQ/kT | 0.01221 | 0.012214 | OK |
| 10 | kT unit conversion | 1.64e-8 N/rpm^2 | 1.645e-8 | OK |
| 11 | MQTB kT per row (10 rows) | 1.535, 1.495, 1.420, 1.241, 1.126, 1.302, 1.321, 1.315, 1.255 (HQ25), 1.089 e-6 | 1.536, 1.495, 1.421, 1.242, 1.127, 1.302, 1.321, 1.316, 1.256, 1.090 e-6 | OK (rounding) |
| 12 | wmax = 2982 x 2400/2550 | 2807 -> 2800 rad/s, 26,740 rpm, eRPM 187,000 | 2806.6; 26,738 rpm; 187,166 eRPM | OK arithmetic |
| 13 | Label of wmax: "14.8 V nominal, loaded" | 2800 | The 2982 rad/s row was measured at 15.42 V (bench supply); the table scales KV only, not voltage. At 14.8 V: 2694 rad/s (T_max 43.5 N, T/W 7.3); at a sagging 14.0 V: 2548 rad/s. 2800 corresponds to ~15.4 V terminal | WRONG: label. Either call 2800 "15.4 V bench/fresh pack" or use 2700 for 14.8 V. Hover and kT unaffected; T_max and all authority numbers scale by (2694/2800)^2 = 0.93 |
| 14 | Voltage scaling 13.2 V / 16.8 V | 2500 / 3180 | 2497 / 3178 (inherits row 13 offset) | OK arithmetic |
| 15 | Loaded/no-load ratio | 0.724 | 0.7241 | OK |
| 16 | Full-throttle cross-check | 54.6 N x 0.886 = 48.4 N | 54.62 x (2400/2550)^2 = 48.38 N | OK |
| 17 | Yaw torque max (2 motors wmax, 2 at 0) | 0.298 N m; 110 rad/s^2 | 2 kQ wmax^2 = 0.2979; /2.7e-3 = 110.3 | OK |
| 18 | Roll torque max (2 motors on one side) | 1.87 N m; 1,340 rad/s^2 | 2 x 11.76 x 0.0795 = 1.870; /1.4e-3 = 1336 | OK |
| 19 | Max reaction torque per motor | not given | kQ wmax^2 = 0.149 N m (417 W mechanical; consistent with 623 W x 0.75 x (2800/2982)^3 = 387 W) | OK |
| 20 | Geometry: a=0.0795 -> diagonal, spacing | 0.225 m, 0.159 m | 0.2249 m, 0.159 m | OK |
| 21 | Inertia (a) Kaufmann x 0.610/0.768 | [1.99, 1.67, 3.42]e-3 | [1.986, 1.668, 3.415]e-3 | OK |
| 22 | Inertia (b) x (0.159/0.18)^2 | [1.55, 1.30, 2.66]e-3 | [1.55, 1.30, 2.66]e-3 | OK |
| 23 | "Chosen = rounded mid of (b) and (c)" | 1.4 / 1.5 / 2.7 e-3 | mids: 1.41 / 1.385 / 2.585 e-3 | OK for Ixx; Iyy +8 %, Izz +4 % above the stated rule, inside the +/-30 % band. Immaterial, but the stated rule is not what was applied |
| 24 | Component-model sum (section 3 item 6) | 610 g | 132+18+70+40+40+190+50+70 = 610 | OK |
| 25 | Agilicious component sum | 436 g | 86+110+20+199+21 = 436 | OK |
| 26 | base_link mass | 0.566 kg | 0.610 - 4x0.011 = 0.566 | OK |
| 27 | Parallel-axis terms | 2.78e-4 (x,y); 5.76e-4 (z) | 4 m a^2 = 2.781e-4; 8 m a^2 + 4x5e-6 = 5.762e-4 | OK |
| 28 | base_link Ixx / Iyy / Izz | 1.12 / 1.22 / 2.12 e-3 | 1.122 / 1.222 / 2.124 e-3 (1.112 / 1.212 if the rotor links' own ixx=iyy=2.5e-6 are also subtracted) | OK (1 % omission of the rotor-link own ixx/iyy, negligible) |
| 29 | x500 comparison (section 3 item 8): T/W 1.74, hover 757 rad/s | 1.74, 757 | Uses 2.0 kg; with the real total 2.0+4x0.016077 = 2.064 kg: T/W 1.69, hover 769.6 rad/s (hover command 0.729 linear) | WRONG (minor, comparison only): 1.69 and 770 rad/s |
| 30 | Spin-up time (section 3 item 5): "50-70 ms for a full-range step" | 50-70 ms | Integrating J dw/dt = Qm - kQ w^2 with J=5e-6: Qm=0.24 N m: t63 = 40 ms, t95 = 72 ms; Qm=0.16 N m: t63 = 64 ms, t95 = 142 ms | WRONG (minor numbers): 72-142 ms to 95 %. Conclusion survives: t63 of 40-64 ms is within a factor 1.2-2 of the measured 33-39 ms, and J_r=1e-5 would double it |
| 31 | DShot timing (row 11): 140 us at DShot300, 70 us at DShot600 | 140 / 70 | 16/300k + 21/375k + 30 us = 139 us; 16/600k + 21/750k + 30 us = 85 us | WRONG: DShot600 ~85 us (30 us gap does not scale) |
| 32 | eRPM period "< 1 ms at 7 pole pairs x 10,000 rpm" | 1.2 kHz | 1167 Hz, period 0.86 ms | OK |
| 33 | NeuroBEM 33 N -> 2345 rad/s; Agilicious 9.5 N -> 2465 rad/s | | 2345 needs kT=1.5e-6 (1.563e-6 gives 2297); 2465 OK with 1.563e-6 | OK (mixed kT, immaterial) |

## 2. Physical plausibility

| # | Item | Check | Verdict |
|---|------|-------|---------|
| P1 | Inertia vs mass/arm: 4 motor+prop masses (4 x 37.5 g = 150 g) at a=0.0795 m give Ixx = 0.150 x 0.0795^2 = 0.95e-3, Izz = 1.9e-3. Adding arms (~30 g effective, ~0.04e-3), battery 190 g with ~20 mm vertical offset (+0.08e-3 + own 0.03e-3), stack and plates (~0.1e-3) gives Ixx ~ 1.2-1.3e-3, Izz ~ 2.3-2.5e-3. Upper bound with all 0.61 kg at the motors: 3.9e-3 / 7.7e-3 | 1.4 / 1.5 / 2.7e-3 is 10-15 % above the component estimate and well below the bound | OK |
| P2 | Perpendicular-axis theorem: Izz <= Ixx + Iyy, deficit = 2 sum(m z^2) | 2.9e-3 - 2.7e-3 = 2e-4 -> sum m z^2 = 1e-4 = e.g. 190 g at 23 mm; physically sensible. Izz/Ixx = 1.93 (planar limit 2) | OK |
| P3 | Ixx < Iyy (battery along x) | consistent with a long battery along x; Ixx/Iyy = 0.93 | OK |
| P4 | Rotor+prop inertia J_r vs 5 g prop, R = 63.5 mm | Rod model: 3 g blades 4.0e-6; all 4.5 g in blades 6.0e-6; 5 g 6.7e-6 (upper bound, a real prop tapers and has a hub). Bell 6.5-10 g at 12.5 mm: 1.0-1.6e-6. Sum 5-8e-6; chosen 5.0e-6 is at the lower end, inside the stated 2e-6..1e-5 | OK |
| P5 | Rotor link mass 0.011 kg (prop 4.5 + bell 6.5) vs J_r bell term using 10 g | Mass and J use different bell masses (6.5 g vs 10 g); J impact is 0.5e-6, immaterial | OK (minor inconsistency, note only) |
| P6 | Time constant physics | See item 30: order of magnitude consistent. Note the plugin filters rotor SPEED (w), so for a small thrust step near hover the thrust time constant is ~tau/2 = 16 ms (dT/T = 2 dw/w). NeuroBEM's 33 ms is a speed constant (matches the plugin); Agilicious's 39.1 ms was fitted on force | OK, with the note |
| P7 | Drag: 4 |w| c at hover | 4 x 998.7 x 7.5e-5 = 0.2996 N s/m (target 0.30). The plugin drag scales with |w|: at wmax it is 0.84 N s/m, at idle-ish speeds near 0. Real linear drag is roughly speed-independent. Acceptable but not equal to the "constant kv=0.30" of the table | OK at hover; note the speed dependence |
| P8 | rollingMomentCoefficient 1e-6 kept from x500 | The plugin applies -|w| c v_perp as a body torque per rotor: 4 x 998.7 x 1e-6 x 10 m/s = 0.040 N m at 10 m/s -> 28.5 rad/s^2 on Ixx=1.4e-3. For the x500 the same coefficient gives 1.4 rad/s^2 (Ixx 0.0217). The effect is 20x larger relative to inertia; scaling by inertia gives 6.5e-8 | WRONG: keep 1e-6 only if that disturbance is wanted; the inertia-scaled value is ~5e-8 (or 0 for a clean baseline) |
| P9 | Rotor spin axis inertia and gz slowdown | The table says the plugin does not use izz. The joint velocity is commanded to w/rotorVelocitySlowdownSim (plugin source: `refMotorRotVel / rotorVelocitySlowdownSim`), so the physics engine does transmit a reaction torque izz x d(w/10)/dt to the base. With izz = 5e-6 the simulated spin-up torque and gyroscopic momentum are 1/10 of the real J_r w. Real full-step value: 5e-6 x 1000/0.033 = 0.15 N m per motor, comparable to the 0.298 N m maximum yaw authority, so it matters for yaw INDI | WRONG (statement and fidelity): to reproduce J_r=5e-6 use izz = 10 x 5e-6 = 5e-5, ixx=iyy >= 2.5e-5 (triangle inequality), subtract those from base_link; or set rotorVelocitySlowdownSim=1 if the aliasing check allows (joint speed 2800 rad/s = 446 Hz exceeds the plugin's aliasing limit 1/(2 dt) for any step above 1.1 ms, e.g. the default 4 ms: not allowed). Needs a gz run to confirm the sign and size |
| P10 | Rotor link inertia isotropic ixx=iyy=2.5e-6, izz=5e-6 | Satisfies izz <= ixx+iyy only with equality (degenerate planar body). The x500 mesh values are rod-like (ixx tiny). Isotropic about the spin axis is the right choice for a rotating link; equality may trigger a physics-engine warning | OK (use e.g. ixx=iyy=2.6e-6 to be strictly valid) |

## 3. SDF mapping against the gz MulticopterMotorModel conventions

Plugin facts read from the source: thrust = turningDirection x sign x w^2 x motorConstant with w the real rotor speed in rad/s
(joint speed x slowdown); yaw reaction torque = -turningDirection x thrust x momentConstant about the rotor axis, applied to the parent;
air drag force = -|w| x rotorDragCoefficient x v_perp (v_perp relative to the joint axis, per rotor); rolling moment = -|w| x rollingMomentCoefficient x v_perp;
command clamp is `min(cmd, maxRotVelocity)` (upper side only); filter is a first-order low-pass on the speed with alpha = exp(-dt/tau), tau up/down in seconds.

| # | Mapping | Table value | Verdict |
|---|---------|-------------|---------|
| M1 | motorConstant = kT (N/(rad/s)^2, not rpm) | 1.5e-06 | OK |
| M2 | momentConstant = kQ/kT in metres | 0.01267 | OK |
| M3 | timeConstantUp/Down seconds, speed filter | 0.033 / 0.033 | OK |
| M4 | maxRotVelocity in rad/s, equal to SIM_GZ_EC_MAX | 2800 and 2800 | OK for equality; see row 13 for the voltage label |
| M5 | rotorVelocitySlowdownSim unchanged (10): only scales the joint velocity, thrust uses real speed | unchanged | OK. Must stay 10 (or any value giving joint speed < Nyquist: 2800/10 = 280 rad/s = 44.6 Hz, fine at the default 4 ms step). The bridge hard-codes ROTOR_VELOCITY_SLOWDOWN_SIM = 10 for eRPM, so changing it breaks SIM_GZ_ESC_FB 1/2 |
| M6 | rotorDragCoefficient 7.5e-05 | 0.30/(4 x 1000) | OK (0.2996 at hover); see P7 |
| M7 | rollingMomentCoefficient 1e-06 | kept | WRONG, see P8 (~5e-8) |
| M8 | turningDirection ccw, ccw, cw, cw unchanged | rotor_0 FR ccw, rotor_1 RL ccw, rotor_2 FL cw, rotor_3 RR cw | OK |
| M9 | Spin sign vs CA_ROTORi_KM | KM = +0.0127 (ccw), -0.0127 (cw) | OK: same sign pattern as the x500 (CA_ROTOR0/1 KM +, CA_ROTOR2/3 KM -, rotor_0/1 ccw, rotor_2/3 cw) |
| M10 | Position mapping gz FLU pose vs PX4 FRD CA_ROTOR PX/PY | rotor_0 (+a,-a)->(+a,+a); rotor_1 (-a,+a)->(-a,-a); rotor_2 (+a,+a)->(+a,-a); rotor_3 (-a,-a)->(-a,+a) | OK: matches x500 pattern (FLU y flips to FRD y) and CA_ROTOR0..3 order PX/PY (+,+),(-,-),(+,-),(-,+) |
| M11 | Motor index: SIM_GZ_EC_FUNC1..4 = 101..104 -> actuator velocity[0..3] -> motorNumber 0..3 | unchanged | OK |
| M12 | base_link mass 0.566, rotor link 0.011 | | OK |
| M13 | base_link inertia | 1.12/1.22/2.12e-3 | OK, but see P9: if izz of the rotor links is raised to 5e-5 (and ixx=iyy=2.5e-5), recompute: Ixx_base = 1.4e-3 - 2.78e-4 - 4x2.5e-5 = 1.22e-3 (x), Iyy_base 1.32e-3, Izz_base = 2.7e-3 - 5.56e-4 - 4x5e-5 = 1.94e-3 |
| M14 | rotor link pose z = 0.0 (x500: 0.06) | 0.0 | OK for thrust; note the rotor drag force (horizontal) then has no moment arm, so no drag-induced pitch/roll moment. A real 5-inch quad has props ~15-25 mm above the CoM: z=+0.02 is a better choice (ASSUMED) |
| M15 | "rotor collision box ... cosmetic only"; base_link collision | Not mentioned: base_link collision box 0.354 x 0.354 x 0.05 and legs at y=+-0.098, z=-0.123..-0.22 (x500 sizes) remain | WRONG: not cosmetic. With a 0.225 m diagonal frame, the x500 landing legs and 0.354 m box dominate ground contact and spawn height (model z 0.24). Resize them (legs ~ 0.03-0.05 m below the body, box <= 0.14 m) or the takeoff/landing contact is unrealistic. Does not affect free flight |
| M16 | `SIM_GZ_EC_MIN` 600 (ESC idle) | 600 | WRONG as a choice with the data given: thrust at idle = 4 x 1.5e-6 x 600^2 = 2.16 N = 36 % of weight (4.6 % of T_max). The vehicle cannot descend or brake in thrust, and with THR_MDL_FAC=1 hover would be 0.033 (below the MPC_THR_HOVER minimum 0.1). Use MIN 0 (exact) or 150 (as x500) |
| M17 | Hover command row 75: 0.32 (MIN 150) / 0.22 (MIN 600) | | WRONG: the 0.22 uses w_h=1094 (kT=1.25e-6) but the SDF uses kT=1.5e-6 so the sim hover is 998.7 rad/s. Correct (linear map, THR_MDL_FAC=0): MIN 0 -> 0.357, MIN 150 -> 0.320, MIN 600 -> 0.181. With THR_MDL_FAC=1: MIN 0 -> 0.127, MIN 150 -> 0.103 (see recommendation) |
| M18 | Command-to-thrust law (missing from the table) | not discussed | WRONG (omission): the bridge passes the mixer output [MIN, MAX] straight to the plugin as rad/s, so with the default THR_MDL_FAC=0 thrust is quadratic in the command while the allocator assumes linear. 4001_gz_x500 does not set THR_MDL_FAC (x500 hover 0.729 vs MPC_THR_HOVER 0.6 shows the mismatch). Exact linearisation needs THR_MDL_FAC=1 with SIM_GZ_EC_MIN=0 (rel_thrust = s^2 and w = wmax s). With MIN>0 and THR_MDL_FAC=1 the residual is real: s=0.357 gives w=150+2650 s=1095 rad/s (1.80 N/motor, +20 % over the 1.496 N hover) |
| M19 | SIM_GZ_THR_SC (this repo's bridge) | not mentioned | OK/UNCHECKABLE: default 1.0 scales the speed command by sqrt(SC) so thrust scales by SC; leave at 1 for the baseline |
| M20 | SIM_GZ_EC_DISn / the allowed minimum of SIM_GZ_EC_MIN | not mentioned | UNCHECKABLE: these params are generated by the mixer module (not in module.yaml); verify at build time that MIN=0 is accepted, else use 1 |

## 4. PX4 parameters for the SITL airframe file (derived from the table, SDF as in section 3)

Frame and allocation (FRD, sign as x500):

| Parameter | Value | Note |
|-----------|-------|------|
| CA_AIRFRAME | 0 | as x500 |
| CA_ROTOR_COUNT | 4 | |
| CA_ROTOR0_PX / PY / KM | +0.0795 / +0.0795 / +0.0127 | rotor_0 FR, ccw |
| CA_ROTOR1_PX / PY / KM | -0.0795 / -0.0795 / +0.0127 | rotor_1 RL, ccw |
| CA_ROTOR2_PX / PY / KM | +0.0795 / -0.0795 / -0.0127 | rotor_2 FL, cw |
| CA_ROTOR3_PX / PY / KM | -0.0795 / +0.0795 / -0.0127 | rotor_3 RR, cw |
| SIM_GZ_EC_FUNC1..4 | 101..104 | as x500 |
| SIM_GZ_EC_MIN1..4 | 0 (recommended; 150 acceptable) | not 600, see M16 |
| SIM_GZ_EC_MAX1..4 | 2800 (= maxRotVelocity; 2700 if a 14.8 V loaded label is wanted, in which case also set maxRotVelocity 2700) | row 13 |
| THR_MDL_FAC | 1 | needed for a thrust-linear command, M18 |
| MPC_THR_HOVER | 0.127 (THR_MDL_FAC=1, MIN=0); 0.103 (MIN=150); 0.320 if THR_MDL_FAC=0 and MIN=150 | param minimum is 0.1 |
| MPC_THR_MIN | 0.05 (parameter minimum; default 0.12 is nearly equal to hover 0.127 and would remove descent authority) | 0.05 x 47 N = 2.4 N = 0.39 W |
| MPC_THR_MAX | 1.0 (default) | |
| SIM_GZ_ESC_FB | 2 (eRPM model; needed if the rotor-speed measurement is to be used) | |
| SIM_GZ_ERPM_POL | 14 | row 8 |
| SIM_GZ_THR_SC | 1.0 | |
| EKF2_BCOEF_X / Y | 0.0 | as x500 |
| EKF2_MCOEF | 0.49 (= 4 w_h c / m = 0.2996/0.610; x500 check: 4 x 769.6 x 8.064e-5 / 2.064 = 0.120 matches its 0.12) | |

SDF values for reference: motorConstant 1.5e-06; momentConstant 0.01267; timeConstantUp/Down 0.033; maxRotVelocity 2800;
rotorDragCoefficient 7.5e-05; rollingMomentCoefficient ~5e-08 (or 0); rotorVelocitySlowdownSim 10; base_link mass 0.566, inertia 1.12e-3 / 1.22e-3 / 2.12e-3
(or 1.22e-3 / 1.32e-3 / 1.94e-3 if the rotor-link izz is raised to 5e-5 to compensate the slowdown); rotor link mass 0.011.

## 5. Tally

WRONG items: 10 (row 13 voltage label, row 29 x500 comparison, row 30 spin-up numbers, row 31 DShot600, P8/M7 rolling moment coefficient,
P9 rotor-spin inertia statement, M15 collision not cosmetic, M16 MIN=600, M17 hover command, M18 missing THR_MDL_FAC).
Most important for the simulation: M18 + M17 + M16 (command law and hover parameter), P9 (spin-up/gyro torque is 1/10 in gz),
P8/M7 (rolling moment 20x too strong relative to inertia), row 13 (T_max is 7 % high at 14.8 V).
