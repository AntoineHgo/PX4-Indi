# S45 derived yaw effectiveness G1_Y for quad5in (sim)

Source values (`indi_flight/sim/models/quad5in/model.sdf`, `quad5in_base/model.sdf`):
kT (motorConstant) 1.5e-6 N/(rad/s)^2, wmax 2700 rad/s, momentConstant km 0.01267 m, base Izz 1.944e-3 kg m^2,
4 rotor links 0.011 kg, izz 5e-5, at r = 0.0795 sqrt(2) = 0.1124 m.

- T_max per motor = kT wmax^2 = 10.94 N (hover fraction 5.98 N / 4 / 10.94 = 0.137, matches hover_thrust_estimate).
- gz MulticopterMotorModel applies yaw torque -dir x thrust x km to the parent (body) link: 0.1386 Nm per motor at full.
- Allocator yaw column: 1.0 per motor after normalisation (`results/stage2_s44/a22_links.md`); with out = wmax sqrt(a),
  thrust is linear in a, so normalised yaw u_y = 1 gives 4 x 0.1386 = 0.5545 Nm.
- Izz about the body z: 1.944e-3 + 4 x 0.011 x 0.1124^2 = 2.50e-3 (rotor masses, parallel axis); + 4 x 5e-5 rotor
  spin inertia = 2.70e-3 if the rotor joints transmit it.
- G1_Y = 0.5545 / (2.50e-3 .. 2.70e-3) = 222 .. 205. Flown value: 215. Default MC_INDI_G1_Y = 30, 7x low, i.e. yaw INDI
  increments 7x too large: consistent with yaw torque_sp at the rails (std 0.895) in the S44 chatter flight.

UNVERIFIED: whether the plugin's velocity-commanded rotor joints produce a spin-up reaction torque on the body
(relevant to G2_Y, decision 5); sign convention of CA_ROTORn_KM vs gz turning direction (PID flies, so assumed consistent).
