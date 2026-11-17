# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 179 | 13.8 | 659 | 14.6 |
| step_roll | 15 deg | PID | 183 | 0.0 | 380 | 9.3 |
| step_pitch | 15 deg | INDI | 184 | 12.6 | 664 | 14.4 |
| step_pitch | 15 deg | PID | 172 | 0.0 | 389 | 9.4 |
| step_yaw | 45 deg | INDI | 476 | 3.4 | 1303 | 18.1 |
| step_yaw | 45 deg | PID | 660 | 0.2 | 1233 | 9.0 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 13.99 | 194.0 | 4.48 |
| pitch | INDI | 12.55 | 178.0 | 4.20 |
| yaw | INDI | 4.84 | 34.8 | 1.98 |
| roll | PID | 14.93 | 203.6 | 5.73 |
| pitch | PID | 15.59 | 197.1 | 5.77 |
| yaw | PID | 14.53 | 54.2 | 11.84 |
