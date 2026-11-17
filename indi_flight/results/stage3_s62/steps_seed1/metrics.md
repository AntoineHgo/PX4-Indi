# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 205 | 0.9 | 358 | 7.8 |
| step_roll | 15 deg | PID | 183 | 0.0 | 380 | 9.3 |
| step_pitch | 15 deg | INDI | 209 | 0.6 | 387 | 7.8 |
| step_pitch | 15 deg | PID | 172 | 0.0 | 389 | 9.4 |
| step_yaw | 45 deg | INDI | 550 | 0.2 | 926 | 12.3 |
| step_yaw | 45 deg | PID | 660 | 0.2 | 1233 | 9.0 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.87 | 185.3 | 3.46 |
| pitch | INDI | 10.84 | 175.5 | 3.24 |
| yaw | INDI | 4.35 | 34.7 | 1.81 |
| roll | PID | 14.93 | 203.6 | 5.73 |
| pitch | PID | 15.59 | 197.1 | 5.77 |
| yaw | PID | 14.53 | 54.2 | 11.84 |
