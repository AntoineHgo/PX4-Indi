# gz x500 drag model check (owner review s8, pertinence of the trajectory entries)

Session 52, 2026-11-15. Read from `Tools/simulation/gz/models/x500_base/model.sdf` and `x500/model.sdf`.

- Body: mass 2.0 kg, `<velocity_decay />` empty on the base link and the rotors, no LiftDrag or other
  aerodynamic plugin: **no body drag**.
- Rotors: `MulticopterMotorModel`, `rotorDragCoefficient` 8.06428e-05 on each of the 4 rotors. In the gz-sim
  plugin this gives a force opposed to the in-plane airspeed, proportional to |omega| (form recalled from the
  plugin source, not re-read in this session: UNVERIFIED).
- Order of magnitude at hover rotor speed (~7350 rpm = 770 rad/s): 4 x 8.06e-5 x 770 = 0.25 N per m/s, i.e.
  0.124 m/s^2 per m/s for 2.0 kg. T5 lemniscate peak 5 m/s: ~0.6 m/s^2; H1 circle 7 m/s: ~0.9 m/s^2 (~9 % g).
- No accelerometer bias in the IMU noise model (only gaussian stddev): the sim does not exercise review
  finding 3 (EKF accel bias) unless the v2 variant adds one.

Consequence for the stage-8 freeze: the drag the outer INDI is meant to reject (Tal, Smeur) is present but modest
(< 1 m/s^2 at the fastest entries, linear in speed, no body drag); a PID with velocity integrator and acceleration
feedforward should absorb most of it. Do not expect the trajectory entries to discriminate strongly; rely on gust,
payload, CoM and mass-mismatch entries for the INDI POS advantage, and say so in the report. An optional check:
fit the drag from a T5 log (a_f residual vs horizontal velocity) to verify the 0.124 figure.
