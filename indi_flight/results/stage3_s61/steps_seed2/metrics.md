# INDI vs PID, quad5in, sim v2, 800 Hz, seed 2

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 181 | 14.2 | 870 | 14.8 |
| step_roll | 15 deg | PID | 186 | 0.0 | 408 | 8.6 |
| step_pitch | 15 deg | INDI | 183 | 13.1 | 655 | 14.6 |
| step_pitch | 15 deg | PID | 180 | 0.0 | 408 | 9.1 |
| step_yaw | 45 deg | INDI | 476 | 3.2 | 1316 | 18.0 |
| step_yaw | 45 deg | PID | 656 | 0.3 | 1203 | 9.0 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 12.91 | 189.5 | 4.39 |
| pitch | INDI | 12.37 | 179.6 | 4.08 |
| yaw | INDI | 4.60 | 35.1 | 1.92 |
| roll | PID | 15.13 | 202.3 | 5.70 |
| pitch | PID | 15.53 | 198.1 | 5.75 |
| yaw | PID | 14.37 | 54.3 | 11.82 |
