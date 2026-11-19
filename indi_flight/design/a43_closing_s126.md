# A-43 closing test (S126): quad5in yaw control effectiveness G1_Y, from source

Question: derived G1_Y 205 vs IV fit 163-166 (results/ident_m3a_s123/fit_yaw_s125.md). Independent derivation from the SDF,
the gz motor plugin and the CA_* parameters. Read-only; nothing under indi_project/ was written (the plugin source was read from
indi_project/research/raw/gz_sim8/).

## Extracted values (file:line)
Airframe indi_flight/sim/models/quad5in_base/model.sdf (served as model://quad5in_base):
- base_link mass 0.566 kg (:10); inertia ixx 1.022e-3, iyy 1.122e-3, izz 1.944e-3, products 0 (:12-17).
- rotor_0..3 each: mass 0.011 kg (:235, 293, 351, 409), ixx=iyy 2.5e-5, izz 5e-5 (:237-239 and equivalents),
  link poses (+0.0795,-0.0795), (-0.0795,+0.0795), (+0.0795,+0.0795), (-0.0795,-0.0795), z 0 (:233, 291, 349, 407).
  Joints rotor_k_joint revolute about +z, parent base_link, no effort limit/damping/friction (:272-285).
- No other massive link (sensors only). Total mass 0.566 + 4*0.011 = 0.610 kg.
Motor plugin parameters indi_flight/sim/models/quad5in/model.sdf:7-23 (identical x4):
- plugin gz-sim-multicopter-motor-model-system, motorType velocity, motorConstant 1.5e-6, momentConstant 0.01267,
  maxRotVelocity 2700, timeConstantUp/Down 0.033, rotorDragCoefficient 7.5e-5, rollingMomentCoefficient 5e-8,
  rotorVelocitySlowdownSim 10; turning: rotor_0 ccw, rotor_1 ccw, rotor_2 cw, rotor_3 cw.
Firmware: ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:
- CA_ROTOR0 (+0.0795,+0.0795) KM +0.01267; ROTOR1 (-,-) KM +0.01267; ROTOR2 (+,-) KM -0.01267; ROTOR3 (-,+) KM -0.01267 (FRD).
  Geometry and KM sign map one-to-one onto the SDF (rotor_0 front right ccw ... rotor_3 rear right cw). No CA_ROTORn_CT set (default).
- SIM_GZ_EC_MAX 2700 (= maxRotVelocity), THR_MDL_FAC 1, MPC_THR_HOVER 0.137 ((998.6/2700)^2).
- MC_INDI_W_MAX: not set in the airframe file; bench overlays map CA_R_W_MAX -> MC_INDI_W_MAX (UNVERIFIED value used in the s123 logs;
  roll/pitch agreement implies it equals 2700).

## Plugin mechanics (indi_project/research/raw/gz_sim8/MulticopterMotorModel.cc)
- :564-581 realMotorVelocity = joint relative velocity * rotorVelocitySlowdownSim; thrust = dir*sign*w^2*motorConstant.
- :590 thrust force applied on the rotor link (at the link origin = arm point).
- :655-662 yaw reaction = (0,0,-turningDirection*thrust*momentConstant), rotated and applied to the PARENT link (base_link).
  No slowdown factor in the torque; it uses the unslowed w^2 through thrust.
- :633-637 air drag force -|w|*rotorDragCoefficient*(link velocity perpendicular to the axis) on each rotor link;
  :664-669 rolling moment with rollingMomentCoefficient (in-plane, not about z).
- :686-690 joint velocity command = dir*refMotorRotVel/slowdown (rotor links spin at w/10 relative to the body).
=> Reaction torque per rotor at full command = 1.5e-6*2700^2*0.01267 = 10.935 N * 0.01267 = 0.1385 N m. No hidden factor.

## Firmware normalisation
- indi_flight/bench/derive_g1.py (replicates ControlAllocationPseudoInverse): yaw column scale = signed max of pinv yaw column,
  so normalised yaw 1.0 = every motor +-1.0 in thrust command (a_i = T_i/Tmax). Physical yaw torque at 1.0 = 4*Tmax*KM.
  Roll/pitch column scale gives +-0.7071 per motor at 1.0.
- src/modules/mc_indi_rate_control/IndiMeasuredTorque.cpp:48-53, :182-184: u = (omega/omega_max)^2, torque = E*(u-trim) .* CA scale
  (same matrix and scale the control allocator uses). Linear in thrust, so a thrust-linear command and u agree.
- Tmax: plugin 1.5e-6*2700^2 = 10.935 N; derive_g1 uses m g/(n*0.137) = 10.92 N (0.14 % apart).

## Computed (python, same numbers as above)
Effective inertias (parallel axis, rotor links included): Ixx 1.022e-3 + 4*(2.5e-5 + 0.011*0.0795^2) = 1.400e-3; Iyy 1.500e-3;
Izz 1.944e-3 + 4*(5e-5 + 0.011*2*0.0795^2) = 2.700e-3 kg m^2 (matches ref_airframe_model.md:18).
| axis | torque at normalised 1.0 | inertia | G1 from source | fit |
|---|---|---|---|---|
| roll | 4*10.935*0.0795*0.7071 = 2.459 N m | 1.400e-3 | 1757 | 1752-1768 OK |
| pitch | same 2.459 | 1.500e-3 | 1639 | 1634-1649 OK |
| yaw | 4*10.935*0.01267 = 0.5542 N m | 2.700e-3 | 205.3 | 163-166 (-20 %) |
Method check passed: roll and pitch reproduce both the derivation and the fits within 0.3 %.

## Verdict
The derived 205 is CORRECT for the simulated plant as built from the SDF + plugin + CA params: torque 0.554 N m (no momentConstant vs CA_KM
mismatch: both 0.01267; no slowdown factor in the reaction torque; omega_max equal 2700; signs and layout consistent) and Izz 2.70e-3
(rotor links already included; their spin inertia is only 5e-5/10 relative). The 165 would need Izz_eff = 3.36e-3 (+0.66e-3, +24 %) or torque
0.446 N m; nothing in the model files supplies either. Same chain gives correct roll and pitch, so the chain is not the cause.
The yaw-only deficit therefore points at the fit, not at the parameter. Unverified, ranked:
1. G1/G2 collinearity in the two-regressor yaw IV: the G1-only fit gave 18.3 +-13.6 (fit_yaw_s125.md), so G1 is weakly identified apart
   from G2; G2 (27.5 vs derived 27) is the quantity that checks out. Not tested here.
2. Passive yaw damping from rotor air drag (:633): D ~ 4*|w|*7.5e-5*(0.1124)^2/Izz = 1.4 1/s, yaw only (roll/pitch have none). It
   biases an omitted-rate-term fit by about D^2/(W^2+D^2); negligible for the 1-60 Hz multisine, up to 20 % only if the fit energy sits
   near 0.45 Hz. Cheap test: add the body yaw rate as a third regressor.
3. Yaw saturation or motor clipping during the yaw excitation (not checked).

## Recommended parameter action
Keep G1_Y = 205 (do not lower it to 165). Close A-43 as "fit unresolved, source supports 205". To settle it cheaply, from the existing
ulog: (a) refit with a yaw-rate regressor, (b) open-loop check: regress yaw accel on sum(dir*thrust)*KM/Izz computed from
actuator_motors/esc rpm (no IV), expect slope 1.0 vs 0.8. If (b) gives 0.8 with clean data, only then investigate Gazebo yaw inertia
(measure by releasing the model with a known torque in a bare gz test).
