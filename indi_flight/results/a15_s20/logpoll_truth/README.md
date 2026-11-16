# A-15 discriminating flight (S20)

PID hover, quad5in, seed 1, speed 4, 800 Hz, logger polled on `vehicle_local_position_groundtruth` instead of
`actuator_motors` (`--log-poll`). Gaps from `bench/a15_gaps.py hover/flight.ulg` (dt > 1.9 ms, first second ignored):

| topic | samples | gaps |
|---|---|---|
| sensor_gyro | 56580 | 5 |
| vehicle_angular_velocity | 43580 | 13190 |
| actuator_motors | 43572 | 13386 |
| vehicle_torque_setpoint | 43541 | 13271 |
| esc_status | 47726 | 10203 |
| vehicle_*_groundtruth (3 topics) | 56581 | 10 each |

Verdict: the loss moves with the logger poll topic -> logger overwrite of queue-1 topics between wakes (T42), not
the gz pose stream (T41 conclusion withdrawn). Fix needed so both truth and controller topics log every sample
(queue depth on the logged sim/controller topics, or logger change), then re-run g1.1.
