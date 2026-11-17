# g15_dist_s66 investigation (payload_add thrust, com_shift roll excursion, torque_steps signs)

## Q1 payload_add: applied force is ~50 % of weight, not 25 %
- Injector: payload_add Fz = -0.25*0.610*9.8 = -1.4945 N (csv constant, 24001 rows = 800/s). Published on the one-step topic
  /world/default/wrench once per clock tick (no persistent topic), cleared with wrench/clear at profile end.
- Rotor truth (esc_status rpm, 4 motors equal): before (-8..-1 s) 9536 rpm, during (10..28 s) 11668 rpm. mean(rpm^2) ratio = 1.497.
  Thrust setpoint 0.1367 -> 0.2048 (ratio 1.498), actuator_motors same. THR_MDL_FAC = 1.0, CA_ROTOR*_CT = 6.5 (linear map, so setpoint ratio ~ omega^2 ratio).
  Sim motor: T = 1.5e-6 * omega^2 per rotor (motorConstant). Hover: 4*1.5e-6*(9536*2pi/60)^2 = 5.98 N = m g (0.610 kg), model consistent.
  During: 1.497*5.98 = 8.95 N, altitude held, so applied extra force = 2.97 N = 0.497 m g. Not a nonlinear setpoint map.
- Independent check: ground-truth vertical accel in the first 50 ms after onset (before rotors react) is -4.3..-4.8 m/s^2 (0.25 g would be -2.45).
- Conclusion: applied force fraction ~ 0.50 (2.0x the intended). Mechanism (each wrench message effectively applied twice per step, e.g. held for 2 steps or accumulated) UNVERIFIED: gz ApplyLinkWrench source not checked.
## Q2 com_shift: roll excursion at +26.0 s
- csv wrench is constant (fz -0.897, tx -0.0448) the whole 30 s; no wrench change, no profile end (ends 30.0 s), no nav_state change
  (nav_state changes at -35, -27, -13, +34 s, +44.8 s only, i.e. none near 26 s), no event, no runner segment (run.json phase_log empty).
- Steady state before: motors 0.152/0.204/0.203/0.152, rpm 10057/11642/11642/10042. The rpm^2 differential gives a roll torque of 0.0898 N m = 2.00 x 0.0448 (confirms the doubling of Q1 for torque too).
- Table (t after onset, 0.1 s): 26.0 roll 0.1; 26.1 15.2; 26.2 62.1; 26.3 78.7 (p 0.45 rad/s); 26.4 11.0; 26.5 -21.8; 26.6 -32.2 (min); 27.3 -7.4. Altitude 4.96 -> 5.04 -> 4.66 m.
- Sequence at ms resolution: ground-truth roll rate starts rising at 25.993 (0.164 rad/s at 25.995, ~64-80 rad/s^2) BEFORE any change in nu[0], torque_increment or actuator_motors (first change 25.999).
  The controller then reacts in the right sense (nu0 negative, motors 0/3 up) but the angular accel is already ~64 rad/s^2, rate 6.4 rad/s at 26.1, nu0 runs to -397 rad/s^2, accel saturates, overshoot to -32 deg, recovered by ~27.5 s.
  Motors never saturate below 0.06 / above 0.37. Onset (0.01-0.19 s) and clear (30.01-30.19 s) show the expected step transients; the 26 s event is a third, isolated one. Not seen in payload_add (max |roll| 0.3 deg, |nu0| max 0.7).
- 87.9 rad/s^2 = 0.0898 N m / 1.022e-3 kg m^2: the size of the observed initial accel matches the whole balancing torque suddenly missing.
- Best explanation: disturbance-injection artefact. The gz-side wrench (not the published csv) briefly dropped/changed near sim time 91.34 s, leaving the 0.09 N m
  motor offset unopposed, then the loop saw a large kick. NOT a runner/mode event, not saturation, not a control-law instability (accel precedes command). UNVERIFIED: no gz-side readback of the applied wrench; a one-step-wrench message loss at speed 4 is the hypothesis.
## torque_steps signs
- gz world is ENU (x east, y north, z up); wrench in world frame at base_link CoM. Spawn heading east (hold_yaw ~1.59 rad NED) so body FLU x = world x. PX4 body is FRD: x same, y and z flipped.
  Roll torque about +x agrees; pitch (+y ENU = left) and yaw (+z up) appear as negative in FRD. That explains the opposite signs for pitch and yaw; not a bug in the vehicle, a frame convention in the injector/analysis. UNVERIFIED: not fitted numerically.
