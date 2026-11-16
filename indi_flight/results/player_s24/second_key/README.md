# Second-key check of player_s24 hover runs

Computed by `indi_flight/bench/second_key_player.py` from each `flight.ulg`.
Schedule kinds decoded from `msg/SimScheduleApplied.msg` (arm=1, mode_offboard=3, sp=4).

| Quantity | r1 | r2 | r2 - r1 |
|---|---|---|---|
| first armed (arming_state=2), us | 30006250 | 30006250 | 0 |
| first offboard (nav_state=14), us | 52016250 | 52016250 | 0 |
| armed minus applied arm row, us | 6250 | 6250 | 0 |
| offboard minus applied mode_offboard row, us | 16250 | 16250 | 0 |
| sensor_gyro median period, us | 1250.0 | 1250.0 | 0.0 |
| max abs(applied timestamp - t_sched), us | 0 | 0 | 0 |

Errors: none
