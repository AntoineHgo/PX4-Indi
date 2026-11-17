# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 209 | 0.8 | 394 | 8.1 |
| step_roll | 15 deg | PID | 186 | 0.0 | 408 | 8.6 |
| step_pitch | 15 deg | INDI | 209 | 0.6 | 373 | 7.9 |
| step_pitch | 15 deg | PID | 180 | 0.0 | 408 | 9.1 |
| step_yaw | 45 deg | INDI | 540 | 0.6 | 920 | 12.4 |
| step_yaw | 45 deg | PID | 656 | 0.3 | 1203 | 9.0 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.78 | 189.4 | 3.43 |
| pitch | INDI | 10.60 | 176.2 | 3.13 |
| yaw | INDI | 4.33 | 34.8 | 1.79 |
| roll | PID | 15.13 | 202.3 | 5.70 |
| pitch | PID | 15.53 | 198.1 | 5.75 |
| yaw | PID | 14.37 | 54.3 | 11.82 |
