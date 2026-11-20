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

## S146 3-seed result with the fix (fix_s1, fix_s2, fix_s3; serial, one stream; key2 AGREES on fix_s2, see key2_rows.md)
| seed | rc_loss (entry - timeout ref) | link_loss | offboard_loss | 9a switch->outputs 0 (kill flag share) | 9b | 9c | 9d step |
|---|---|---|---|---|---|---|---|
| fix_s1 | PASS 510 ms | PASS 9 ms | PASS 26 ms | FAIL 10.00 ms (10.00 commander, 0.00 output) | PASS | PASS 0.01 % | PASS 4.0 % |
| fix_s2 | PASS 510 ms | PASS 2 ms | PASS 26 ms | FAIL 5.00 ms (5.00, 0.00) | PASS | PASS 0.01 % | PASS 4.5 % |
| fix_s3 | PASS 510 ms | PASS 4 ms | PASS 24 ms | FAIL 3.75 ms (3.75, 0.00) | PASS | PASS 0.01 % | PASS 4.5 % |
rc_loss 510 ms = COM_RC_LOSS_T 0.5 s counted from the timeout reference (flag rise - T) + 10 ms to failsafe entry.
G5.8 hover PASS 3/3, G5.9 b/c/d PASS 3/3 (probe, RC113). G5.9a FAIL 3/3, entirely stock commander latency
(switch -> actuator_armed.kill 3.75-10 ms); outputs reach 0 in the sample of the kill flag. Q8 addendum 2 open.
G5.8 3 m/s (moving loss): not flown.
Key2 (bench/g5_rows_key2.py, written without the first checker, S146) on fix_s2: same values on every row (rc 0.51 s,
link 2 ms, offboard 26 ms, switch->outputs 5.0 ms / 0 ms after kill flag, states 0, take-off step 4.5 %, dip 0).
9c by a different definition (output range in the first second, 0.67 % of W_MAX) also PASS. Key2 caveat on the
link_loss margin checked: vehicle_status is logged at each publication (on change + 2 Hz heartbeat; rise sample at
80.6025 s, previous at 80.5825 s), so the 2 ms is a publication instant, not a 2 Hz sample. Limit noted: 9b is weak
evidence, the memory states were already ~0 before the kill (blend 1.4e-4, torque_filtered 2.2e-4): the reset
itself is covered by unit tests (G7), not by this flight.
