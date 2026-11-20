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
