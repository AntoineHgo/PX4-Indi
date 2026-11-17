# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1

| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |
|---|---|---|---|---|---|---|
| step_roll | 15 deg | INDI | 206 | 1.3 | 388 | 8.0 |
| step_pitch | 15 deg | INDI | 202 | 0.8 | 361 | 8.2 |
| step_yaw | 45 deg | INDI | 545 | 0.2 | 926 | 12.3 |

| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |
|---|---|---|---|---|
| roll | INDI | 11.72 | 187.6 | 3.38 |
| pitch | INDI | 10.98 | 177.5 | 3.18 |
| yaw | INDI | 4.32 | 34.8 | 1.83 |
