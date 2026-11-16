# G1.6(a) pre-check with the sim-time player (session 24)

5 hovers, pid_default, quad5in, seed 1, speed 4, `--sched` (`bench/g16_sched_hover.sh`). All flew (docker rc 0).
Instants from `bench/second_key_player.py` (`hover_rN/instants.json`), simulation time in us.

| run | arm applied | armed (vehicle_status) | offboard applied | nav_state 14 | offboard - armed |
|---|---|---|---|---|---|
| r1 | 30000000 | 30002500 | 52000000 | 52012500 | 22010000 |
| r2 | 30000000 | 30003750 | 52000000 | 52013750 | 22010000 |
| r3 | 30000000 | 30007500 | 52000000 | 52018750 | 22011250 |
| r4 | 30001250 | 30006250 | 52000000 | 52016250 | 22010000 |
| r5 | 30000000 | 30006250 | 52000000 | 52016250 | 22010000 |

- Applied rows: on time in 14/15 rows; r4 arm applied one IMU period late (probably a sim gyro hole at 30.000 s, A-13; not checked).
- Spread across runs: arm 5.0 ms (4 periods), offboard 6.25 ms (5 periods). Before the player: 7.5-11 ms. Gate (a): 2.5 ms. NOT MET.
- Session-24 pair (`results/player_s24/`) had 0 us spread by chance: both runs had the same phase.
- Offboard minus armed is 22.010 s in 4/5 runs: inside a run, Commander's response keeps a fixed phase; the phase
  changes from run to run. Hypothesis A-17: Commander's 10 ms loop (`px4_usleep` task) wakes at a start-up-dependent
  phase relative to the gyro tick, so every state change lands 0-10 ms after its trigger.
