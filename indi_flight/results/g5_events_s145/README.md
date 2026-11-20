# S145 G5.8 / G5.9 hover rows, 3 seeds (probe, RC113: pre-freeze)

Flights: results/g5_events_s144/README.md command, --seed 1..3, --out results/g5_events_s145/sN (serial, one stream).
Scored by bench/g5_rows_check.py (new S145: g5_events.py checks G1.5 injection only; no G5.8/G5.9 row checker
existed). Self-test bench/tests/test_g5_rows_check.py (6 tests). Key2: NOT YET.

| seed | rc_loss | link_loss | offboard_loss | 9a motors 0 | 9b states | 9c 1st s | 9d take-off |
|---|---|---|---|---|---|---|---|
| s1 | PASS | PASS (6 ms) | PASS | NOT-COMPUTED | FAIL* | PASS 0.01 % | PASS 4-4.5 % step, 0 dip |
| s2 | PASS | FAIL* (1008 ms) | PASS | NOT-COMPUTED | FAIL* | PASS | PASS |
| s3 | PASS | FAIL* (1009 ms) | PASS | NOT-COMPUTED | FAIL* | PASS | PASS |
Excursions <= 0.15 m (limit 1 m). 3 m/s case: not flown (needs a moving variant of the flight).

*Test defects found, verdicts not counted:
- link_loss entry is read from vehicle_status, logged at 2 Hz: 1008 ms is one log period from 508 ms. Resolution
  must be below the margin (log vehicle_status / failsafe_flags / telemetry_status at every publication).
- 9a: actuator_motors (controller command) is not zeroed by kill in either stack; the output stage zeroes
  actuator_outputs, logged at 10 Hz -> only "zero within 11-100 ms of the switch". Needs full-rate actuator_outputs.
- 9b: the checker's state set included filtered measurements (a_f[2] = 9.74 = g at rest, angular_accel_filtered).
  Those must track their input, not be zero. "INDI states" = quantities carrying memory from the previous flight
  that are not re-derived from measurements (increments, integrators, gap remover, held commands).

## S145/S146 fix and pre-test (fix_s2, seed 2, same params; flown by the S145 agent, scored S146)
Fix (bench/g5_events.py): failsafe_flags, actuator_outputs, actuator_armed, manual_control_switches, telemetry_status
(instances 0-3) logged at every publication for this flight. Checker fixes S146 (bench/g5_rows_check.py):
9a read output[0..3] by numeric index (lexicographic sort took output[10..12]) and windowed to disarm (the flight
re-arms after the kill); 9b state set = torque_filtered, rate_sp_dot, blend, hold_cycles; torque_increment moved to
"reported": it is algebraic, G1^-1 (nu - a_f) of the current cycle (indi_rate_control.cpp step 8); its yaw memory
_yaw_inc_prev is zeroed by the law while landed.
fix_s2: rc_loss PASS (510 ms), link_loss PASS (2 ms), offboard_loss PASS (26 ms), 9b PASS (0 of 6 + 0 of 2 non-zero;
torque_increment 6.6e-5 reported), 9c PASS 0.01 %, 9d PASS 4.5 %, 0 dip.
9a FAIL: outputs 0 at 5.00 ms after the switch (last non-zero 3.75 ms), limit 1.25 ms. Attribution: actuator_armed.kill
rises 5.00 ms after the switch (commander, stock, O-11), outputs 0 in the same sample as the kill flag (0.00 ms).
The INDI stack adds nothing; the limit as written measures stock commander latency -> Q8 addendum 2.
