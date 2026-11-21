# A-56 cause search, part 1 (S171): INDI descent body-rate noise under harsh vibration

Probe (no flight): host pyulog read of results/g4_gate_s169/hover_harsh_s2/flight.ulg (ulog time base), 1 s bins.
AUTO_LAND entry at 119.06 s, touchdown (ground_contact) 127.2 s.

| bin (s) | vehicle_rates_setpoint pitch mean (deg/s) | q mean / std | indi_rate_feedforward omega_ff roll, pitch mean (deg/s) | motor cmd min..max |
|---|---|---|---|---|
| 114 (offboard hover) | -0.3 | -0.3 / 0.3 | 0.0, 0.0 | 0.134..0.139 |
| 119 (land entry) | -12.3 | 1.7 / 17.4 | -22.0, 14.3 | 0.110..0.170 |
| 121 | -11.4 | -0.05 / 2.7 | -22.2, 11.9 | 0.100..0.174 |
| 122 | -10.8 | -1.0 / 5.5 | -7.2, 9.1 | 0.097..0.176 |
| 124 | -5.1 | 0.5 / 2.9 | -7.4, 5.8 | 0.109..0.165 |

Reading: no motor saturation (cmd >= 0.097). In AUTO_LAND the INDI position module publishes a body-rate feed-forward
omega_ff of 7-22 deg/s (zero in the offboard hold, where the setpoint carries no acceleration/jerk). The attitude
controller's rate setpoint (-11 deg/s pitch) opposes it, so the net rate is ~0 while a 1-1.5 deg attitude error
persists: the two loops fight, and the result is the 2 Hz q oscillation. PID has no feed-forward path (descent RMS 0.3).
Lead (UNVERIFIED, needs the code): the jerk feed-forward differentiates an AUTO_LAND acceleration setpoint that is
feedback-derived from the vibration-noisy estimate (quiet descent RMS 0.2-0.3, harsh 3-6: scales with vibration).
Next (part 2, next session): read how omega_ff is built in mc_indi_pos_control / indi_accel_control and which modes
feed it; confirm by one harsh descent flight with omega_ff zeroed (param or SITL switch, if one exists); then a
D- entry (gate the FF to setpoint-generated jerk, or filter) as a control-law change (two keys, re-fly G4 + G5 land rows).
