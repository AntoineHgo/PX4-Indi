# O-13 pre-check of the stage-8 set O1-O7 (session 53, 2026-11-15)

pid_tuned (stock pipeline, `results/s2_tuning/pid/r1f/c05/params`), seed 1, v2 sim with vibration, speed 1, entries
flown 4 in parallel. Feasibility only, no verdict. `bench/s8i_o13_precheck.sh`.

| entry | traj rms 3D (m) | attitude rms (deg) | motor saturation | status |
|---|---|---|---|---|
| O1 lemniscate 10x5 m, 6 m/s | 0.44 | 7.9 | 0 | flyable |
| O2 circle r 5 m 8 m/s + 1.5 m vertical | 2.97 | 13.6 | 20 % | REPLACED |
| O3 O1 + gust_x | 0.40 | 6.9 | 0 | flyable |
| O4 O1 + payload_add | 0.74 | 4.7 | 8.7 % | flyable (saturation from carrying the payload through the path) |
| O5 O2 + com_shift | - | - | - | REPLACED: watchdog, height < 0.3 m at sim t 42.6 s |
| O6 vertical sine, mass x1.15 | 0.16 | 0.17 | 0 | flyable |
| O7 O1 + motor tau x2 | 0.44 | 7.9 | 0 | flyable |

Replacement (O-13: an entry pid_tuned cannot fly is replaced, not kept): the circle of O2/O5 is slowed to 6.5 m/s
(centripetal 8.45 m/s^2, about 1.4 g of total thrust, close to O1, which pid_tuned flies without saturation).
Old runs kept in `results/s8i_o13_precheck/replaced_circle_8ms/`. Re-check: `bench/s8i2_o13_circle.sh` ->
`results/s8i_o13_precheck/{o2_circle_z,o5_circle_com_shift}/pid_tuned/seed1/`, log `results/s8i2_o13_circle.log` (ends S8I2_DONE).
