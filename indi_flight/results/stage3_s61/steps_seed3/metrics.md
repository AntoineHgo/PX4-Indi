# INDI vs PID, quad5in, sim v2, 800 Hz, seed 3

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 184 | 12.8 | 682 | 14.7 |
| step_roll | 15 deg | PID | 188 | 0.0 | 405 | 8.8 |
| step_pitch | 15 deg | INDI | 188 | 13.2 | 664 | 14.5 |
| step_pitch | 15 deg | PID | 188 | 0.0 | 412 | 8.9 |
| step_yaw | 45 deg | INDI | 481 | 2.9 | 1273 | 18.0 |
| step_yaw | 45 deg | PID | 669 | 0.3 | 1240 | 8.9 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 13.80 | 195.8 | 4.53 |
| pitch | INDI | 12.66 | 179.4 | 4.16 |
| yaw | INDI | 4.75 | 35.2 | 2.04 |
| roll | PID | 14.70 | 202.1 | 5.67 |
| pitch | PID | 14.86 | 196.4 | 5.74 |
| yaw | PID | 14.35 | 53.9 | 11.77 |
