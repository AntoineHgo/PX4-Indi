# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 210 | 0.8 | 370 | 7.7 |
| step_roll | 15 deg | PID | 188 | 0.0 | 405 | 8.8 |
| step_pitch | 15 deg | INDI | 211 | 1.0 | 371 | 8.0 |
| step_pitch | 15 deg | PID | 188 | 0.0 | 412 | 8.9 |
| step_yaw | 45 deg | INDI | 551 | 0.5 | 936 | 12.4 |
| step_yaw | 45 deg | PID | 669 | 0.3 | 1240 | 8.9 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.73 | 190.6 | 3.42 |
| pitch | INDI | 10.83 | 176.3 | 3.13 |
| yaw | INDI | 4.37 | 35.5 | 1.80 |
| roll | PID | 14.70 | 202.1 | 5.67 |
| pitch | PID | 14.86 | 196.4 | 5.74 |
| yaw | PID | 14.35 | 53.9 | 11.77 |
