# G5.11 scoring notes (S160 exact test, first scoring)

Tools: bench/osc_detector.py, bench/g511_check.py; tests bench/tests/test_osc_detector.py, test_g511_check.py (all pass).
Topics and rates (host python, pyulog); output g511_check.txt and g5_events_s*/g511_check.json:
- Truth pose and body rates: `sim_ground_truth` (x,y,z, q, angular_velocity[3]), 800 Hz, 1250 us steps, ~9 gaps per 97k samples
  (interpolated to the uniform grid). Band 2-40 Hz unchanged (no rate reduction needed).
- Setpoint: `vehicle_attitude_setpoint.q_d` (body z and yaw from q_d), ~89 Hz.
- Reset counters: `vehicle_attitude.quat_reset_counter`, `vehicle_local_position.xy_reset_counter`; nav_state: `vehicle_status`.
- Other events from run.json `g5_events` (t_applied_us).
Spec issues / choices (none blocking):
- Peak "rate RMS at the peak" is not defined: taken as PSD integrated over peak +-2 bins (Hann main lobe), per axis; a window
  flags if any of p, q, r flags. "Within +-10 %": every window of the run vs the first window of the run.
Results (all validity OK: one increment, nav_state 4 constant, no other event in window; no sustained oscillation):
| run | event | t_a s | tilt jump deg (<=1) | excursion m (<=0.5) | truth yaw chg deg | sp yaw step deg | verdict |
| s1 | ekf_yaw | 45.666 | 1.94 | 0.116 | 0.02 | 5.00 | FAIL |
| s1 | ekf_xy | 54.670 | 5.80 | 0.194 | 0.01 | 0.00 | FAIL |
| s2 | ekf_yaw | 45.435 | 1.78 | 0.065 | -0.05 | 4.99 | FAIL |
| s2 | ekf_xy | 54.435 | 5.68 | 0.155 | 0.01 | 0.00 | FAIL |
| s3 | ekf_yaw | 45.481 | 1.84 | 0.093 | 0.00 | 5.01 | FAIL |
| s3 | ekf_xy | 54.481 | 6.39 | 0.158 | 0.00 | 0.00 | FAIL |
All failures are the 1 deg tilt-command limit only; excursion and oscillation pass.
Unverified: truth/log share one time base (assumed, G1.2); second key (independent recomputation) before the verdict counts; z reset (not tested, per spec); detector thresholds
not calibrated on real hover noise (G4 pre-look); the oscillation detector on the 6 real windows reports no flags but has not
been compared with an independent PSD implementation; ekf_yaw tilt jump of ~1.9 deg is not yet explained (cause not analysed).
