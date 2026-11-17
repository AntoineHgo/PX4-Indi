# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 209 | 1.2 | 380 | 7.8 |
| step_pitch | 15 deg | INDI | 214 | 0.6 | 379 | 7.7 |
| step_yaw | 45 deg | INDI | 551 | 0.4 | 944 | 12.4 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.81 | 189.6 | 3.43 |
| pitch | INDI | 10.59 | 175.7 | 3.17 |
| yaw | INDI | 4.38 | 34.9 | 1.81 |
