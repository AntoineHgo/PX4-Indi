# A-31 fix re-fly (S67): excursion old (double wrench) vs new (single wrench)

Excursion = peak deviation from the 2 s pre-onset reference, from onset to profile end + 3 s.

| profile | rc | runtime add NO | metrics.json | axis | old | new | new/old |
|---|---|---|---|---|---|---|---|
| torque_steps | 0 | yes | yes | roll (deg) | 11.562 | 5.823 | 0.50 |
| torque_steps | 0 | yes | yes | pitch (deg) | 10.671 | 5.657 | 0.53 |
| torque_steps | 0 | yes | yes | yaw (deg) | 4.428 | 2.155 | 0.49 |
| torque_steps | 0 | yes | yes | pos_xy_m (m) | 0.201 | 0.091 | 0.45 |
| torque_steps | 0 | yes | yes | pos_z_m (m) | 0.028 | 0.033 | 1.17 |
| gust_x | 0 | yes | yes | roll (deg) | 0.369 | 0.411 | 1.11 |
| gust_x | 0 | yes | yes | pitch (deg) | 8.546 | 4.346 | 0.51 |
| gust_x | 0 | yes | yes | yaw (deg) | 0.137 | 0.191 | 1.40 |
| gust_x | 0 | yes | yes | pos_xy_m (m) | 0.299 | 0.138 | 0.46 |
| gust_x | 0 | yes | yes | pos_z_m (m) | 0.067 | 0.028 | 0.41 |
| gust_diag | 0 | yes | yes | roll (deg) | 8.081 | 4.120 | 0.51 |
| gust_diag | 0 | yes | yes | pitch (deg) | 1.902 | 1.079 | 0.57 |
| gust_diag | 0 | yes | yes | yaw (deg) | 0.168 | 0.130 | 0.77 |
| gust_diag | 0 | yes | yes | pos_xy_m (m) | 0.205 | 0.114 | 0.56 |
| gust_diag | 0 | yes | yes | pos_z_m (m) | 0.027 | 0.024 | 0.89 |
