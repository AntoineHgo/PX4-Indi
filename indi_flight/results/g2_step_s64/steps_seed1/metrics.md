# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 206 | 0.7 | 388 | 8.1 |
| step_pitch | 15 deg | INDI | 209 | 1.0 | 371 | 8.0 |
| step_yaw | 45 deg | INDI | 551 | 0.1 | 945 | 12.2 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.34 | 190.6 | 3.25 |
| pitch | INDI | 10.60 | 175.5 | 3.11 |
| yaw | INDI | 4.36 | 34.8 | 1.86 |
