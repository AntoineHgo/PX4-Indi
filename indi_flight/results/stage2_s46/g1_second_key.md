# G1 second key (S46), quad5in, independent derivation

Method: derive from PX4 source and the gz model only (derive_g1.py, stage2_s44/s45 not opened).

## Sources (file:line)
- src/modules/control_allocator/VehicleActuatorEffectiveness/ActuatorEffectivenessRotors.cpp:194-197:
  thrust = ct*axis, moment = ct*(position x axis) - ct*km*axis. Axis for multirotor = (0,0,-1) (line 109), so
  column i = ct*(-py_i, +px_i, +km_i | 0,0,-1) (FRD, roll/pitch/yaw rows then thrust xyz).
- src/lib/control_allocation/control_allocation/ControlAllocationPseudoInverse.cpp:69 `geninv(_effectiveness,_mix)`:
  _mix = pinv(6xN effectiveness). Actuator sp = trim + _mix*(control_sp - control_trim) (:192).
- same file :85-120 updateControlAllocationMatrixScale: normalize_rpy true for multirotor
  (ActuatorEffectivenessMultirotor.hpp:54). roll/pitch scale = sqrt(|mix.col|^2/(n_nonzero/2)), max of the two, applied to both;
  yaw scale = mix.col(2).max(). Columns divided by scale at :158-163.
- src/lib/mixer_module/functions/FunctionMotors.hpp:81-90: rel_thrust = f*x^2 + (1-f)*x. With THR_MDL_FAC=1: cmd = sqrt(a).
- ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in: CA_ROTOR0..3 (PX,PY)=(+,+),(-,-),(+,-),(-,+) * 0.0795;
  KM = +,+,-,-  0.01267; no CA_ROTORi_CT set (CT cancels, see below); THR_MDL_FAC 1; EC range 0..2700; MPC_THR_HOVER 0.137.
- indi_flight/sim/models/quad5in/model.sdf: motorConstant 1.5e-6, momentConstant 0.01267, maxRotVelocity 2700,
  time constant 0.033 s, turning ccw,ccw,cw,cw for motors 0..3 (matches KM signs +,+,-,-).
- indi_flight/sim/models/quad5in_base/model.sdf:10-17 base_link m 0.566, I = (1.022e-3, 1.122e-3, 1.944e-3), no inertial pose
  (CoG at origin). Rotor links :229-... m 0.011 each, I = (2.5e-5, 2.5e-5, 5e-5), at (+-0.0795, +-0.0795, 0) (FLU), same z as CoG.
  Total mass 0.566 + 4*0.011 = 0.610.

## Allocation algebra
Rows of the 6xN matrix are mutually orthogonal for this symmetric X quad, so pinv column j = row_j^T/|row_j|^2.
- roll/pitch: mix = s_i/(4 p ct), p=0.0795; scale = sqrt2/(4 p ct); normalised delta = +-1/sqrt2 = +-0.7071 per motor (ct cancels).
- yaw: mix = s_i/(4 km ct); scale = max = 1/(4 km ct); normalised delta = +-1.0 per motor.
- Delta is in thrust space: T_i = a_i*Tmax, a_i = allocator output. THR_MDL_FAC=1 means cmd = sqrt(a), w = 2700 sqrt(a),
  T = kf w^2 = Tmax*a. So thrust is linear in the ALLOCATOR output (not in the motor command, which is the square root).
  The statement "linear in the command" is wrong; the allocator-to-torque map is still exactly linear. No hover-slope correction.
- Tmax = 1.5e-6 * 2700^2 = 10.935 N.
- Unit roll torque: 4*0.7071*Tmax*0.0795 = 2.4588 N m. Unit yaw: 4*1.0*Tmax*0.01267 = 0.55419 N m.
  (Numerically confirmed with numpy pinv of the 6x4 matrix with ct=6.5, identical.)

## Inertia
Parallel axis, rotors at (+-0.0795, +-0.0795, 0), m_r 0.011, own inertia (2.5e-5, 2.5e-5, 5e-5):
- Ixx = 1.022e-3 + 4*(2.5e-5 + 0.011*0.0795^2) = 1.4001e-3
- Iyy = 1.122e-3 + same 3.781e-4          = 1.5001e-3
- Izz = 1.944e-3 + 4*(5e-5 + 0.011*2*0.0795^2) = 2.7002e-3 (2.5002e-3 if the rotors' own spin Izz 4*5e-5 is left out)
The plant inertia is the TOTAL (base + rotors), not base_link alone: gz simulates all four links as rigid bodies of the vehicle,
and the rotors are 7 % of the mass at the arm tips. Base-only inertia gives G1 = 2406 / 2191 / 285, which is 37 % / 37 % / 39 % too high.

## Results
| axis  | torque/unit (N m) | I used (kg m2) | G1 gz Tmax | G1 hover Tmax | first key | flight-clean |
|-------|-------------------|----------------|-----------|---------------|-----------|--------------|
| roll  | 2.4588 | 1.4001e-3 | 1756.2 | 1753.2 | 1759 | 1756 |
| pitch | 2.4588 | 1.5001e-3 | 1639.1 | 1636.3 | 1602 | 1599 |
| yaw   | 0.55419 | 2.7002e-3 | 205.2 | 204.9 | 221 | 215 |
Yaw with Izz 2.5002e-3 (rotor spin inertia excluded): 221.7.

Tmax cross-check: m g/(4*0.137) = 10.916 N versus kf*w^2 = 10.935 N: hover value is 0.17 % lower (hover fraction would be 0.13676,
kf at w_h=998.6 is 1.4997e-6). Effect on G1 -0.17 %, negligible. Neither Tmax differs materially.

## Verdict (tolerance 5 %)
| axis | mine vs first key | verdict |
|------|-------------------|---------|
| roll  | 1756.2 vs 1759 (-0.2 %) | AGREE |
| pitch | 1639.1 vs 1602 (+2.3 %) | AGREE |
| yaw   | 205.2 vs 221 (-7.1 %) | DISAGREE if rotor spin Izz is counted; AGREE (221.7) if not |

## Inertia discrepancy
- The earlier hand values (Ixx 1.022e-3, Iyy 1.122e-3) are the BASE_LINK-only numbers. With them the allocator torque gives 2406 / 2191,
  not 1756 / 1599. The quoted 1756 / 1599 are only reproduced with the TOTAL inertia (1.400e-3 / 1.538e-3 implied). So the hand note
  most likely printed base inertia but computed with total (UNVERIFIED, I cannot see the hand calc); the two "agree" only through that mislabel.
  The right plant value is the total about the CoG.
- Roll: my Ixx 1.4001e-3 vs first key 1.396e-3 (0.3 %). Pitch: first key's implied Iyy is 1.535e-3 vs my 1.5001e-3 (2.3 %);
  I cannot account for the extra 3.4e-5 from the SDF (UNVERIFIED; it may be a different term, e.g. a measured or cross-checked value).
- Yaw: the first key's implied Izz 2.508e-3 equals base + rotor parallel-axis terms with the rotors' own spin Izz dropped (2.500e-3).
  Whether the rotor's own Izz belongs in the yaw plant depends on how gz drives the rotor joint (UNVERIFIED, plugin source not read):
  if the joint speed is prescribed relative to the body, a body yaw acceleration also accelerates each rotor's Izz, so 2.700e-3 is
  right (G1 205); if the rotor is free to spin and only thrust/reaction torques are applied, it does not (G1 222). The flight with
  yaw 215 hovered cleanly, which sits between and does not discriminate; a yaw-rate step response identification would.

## UNVERIFIED
- gz plugin yaw reaction torque = momentConstant * thrust, sign by turningDirection (standard gz multicopter plugin; not read).
- rotorDragCoefficient / rollingMomentCoefficient (7.5e-5, 5e-8) add small damping/torques not in G1.
- G1 is the DC gain; motor lag 33 ms (on w, not on thrust) is not in G1. Allocator saturation/desaturation and trim not modelled.
- Reaction torque from rotor spin-up (I_rotor dw/dt) not included in the yaw torque.
