# G1.6 short repeat on the 1.25 ms world (session 16)

`bench/g16_batch_w125.sh`: PID, quad5in, seed 1, speed 4, rate 800 Hz, IMU 800 Hz, logger -p actuator_motors.
15/15 flights first attempt (traj r1 flown first as pre-test). Spreads: `spread.json` (`bench/g16_spread.py`),
comparison with the 4 ms world (`det_g16_s4`): `compare_s4_vs_w125.txt`.

- Tracking (rate, attitude, position, trajectory truth/estimate RMS): means within the same-seed spread of the 4 ms
  world (largest shift: traj truth horizontal 0.701 -> 0.728 m, +4 %). Same-seed rel spreads of the same order
  (hover attitude 11-26 %, traj horizontal 0-3 %); vertical metrics stay ill-conditioned (17-139 %).
- G1.6(a): window.start_s spread 11.2 ms hover, 7.5 ms step_roll and traj (4 ms world: 16 / 12 / 12 ms). Threshold
  2 IMU periods = 2.5 ms: NOT MET. Cause unchanged (G1.6(c)): mode command over UDP into non-lockstepped gz.
- Effort: `effort.motor_rate_rms_per_s` step_roll 0.204 -> 0.374, traj 0.120 -> 0.276, hover 0.0075 -> 0.0068.
  A derivative of the motor command depends on the logged sample rate (285 Hz timer-decimated before, 800 Hz now);
  ANOMALIES A-11. Effort numbers from the two worlds are not compared until it is closed.
