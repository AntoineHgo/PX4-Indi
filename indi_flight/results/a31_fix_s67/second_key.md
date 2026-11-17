# A-31 second key: disturbance wrench applied once?

Script: `indi_flight/results/a31_fix_s67/second_key.py` (run with host python3, pyulog and numpy present).

## Method and topics

- Rotor speed: ulog topic `esc_status`, fields `esc[0..3].esc_rpm` (rpm, converted to rad/s). Assumed rotor_i = esc[i]. Other topics seen but not used: `actuator_motors`, `actuator_outputs`, `sim_ground_truth`, `vehicle_angular_velocity_groundtruth`.
- Onset: `disturbance_trigger.json` (`onset_px4_s`), on the PX4 clock, the same clock as `esc_status` timestamps.
- Hover window: onset-5 s to onset. Late window: onset+20 s to onset+25 s (profile is 30 s; output shows settling by about +2.5 s).
- Mass 0.61 kg (SDF base 0.566 + 4 x 0.011). Motor constant k_f = 1.5e-6 is in `indi_flight/sim/models/quad5in/model.sdf`, not in `quad5in_base/model.sdf` (the task brief said base). Rotor positions (+-0.0795 m, diagonal) are from `quad5in_base/model.sdf`.
- Torque: tau_x = sum(y_i k_f w_i^2), tau_y = -sum(x_i k_f w_i^2). Also computed with a hover-calibrated k_f = m g / mean(sum w^2): 1.4997e-6 vs SDF 1.5e-6.
- Disturbance.csv: sample gaps and duplicates in sim_time_s.

## Numbers

payload_add (Fz applied, onset 65.817 s PX4):
- sum(w^2) hover mean 3.9886e6, late mean 4.9818e6, ratio **1.2490**.
- Applied |Fz| = 1.4945 N, so |Fz|/(mg) = **0.2497**; expected 1 + |Fz|/(mg) = 1.2497. Agrees to 0.06%.
- A double application would give about 1.50. Not seen.

com_shift (onset 65.922 s PX4):
- Applied torque from csv: tx = -0.04484 N m, ty = tz = 0.
- Rotor-produced torque change (SDF k_f): delta tx = +0.04453 N m, delta ty = +0.00003 N m. Hover-calibrated k_f: +0.04452 N m. Magnitude agrees to 0.7%; sign is opposite, as expected for a controller countering the applied torque.
- The csv also has Fz = -0.8967 N in this profile. Thrust ratio late/pre = 1.1488 vs expected 1.1498 (|Fz|/(mg) = 0.1498). Agrees to 0.1%.

disturbance.csv sampling (both files):
- 24001 rows, span 30.0000 s.
- Duplicates 0, non-monotonic 0.
- dt min/median/max = 0.0012 / 0.00125 / 0.0013 s. Largest gap is 0.325 of the 0.004 s physics step; 0 intervals above 1.5 steps.
- Wrench updates every 1.25 ms (800 Hz), finer than the physics step.

## Verdict

**AGREE**: the wrench is applied once in both runs. payload_add ratio 1.2490 matches 1 + |Fz|/(mg) = 1.2497. com_shift rotor torque change 0.0445 N m matches the applied 0.0448 N m, and thrust matches its Fz.
