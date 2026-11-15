# D-SIM-STEP pre-test (session 16)

Fixed 1.25 ms world, quad5in IMU 800 Hz, PID (`pid_default`), seed 1. Scripts: `bench/pretest_simstep_s16.sh`,
`bench/pretest_logpoll_s16.sh`; checks: `bench/check_rates.py <run_dir>`. Raw logs untracked.

| run | speed | logger | flies | params applied | gyro rate (PX4) | logged rates (mean, sim time) | dropouts |
|---|---|---|---|---|---|---|---|
| hover_r800 | 4 | timer 3.5 ms, -b 20 | ok | RATEMAX 800, cutoffs 40/20 | 800/800 | all ~285 Hz | 44, 186 ms |
| hover_r400 | 4 | timer 3.5 ms, -b 20 | ok | RATEMAX 400 | 800/800 | all ~285 Hz (vav median 400) | 38, 154 ms |
| step_roll_r800 | 4 | -p sensor_gyro, -b 200 | ok | RATEMAX 800 | 800/800 | gyro 800, vav 727, torque_sp 735, act_motors 634, esc 773 | 0 |

Confirmed: `physics_step_s` 0.00125 in run.json; the `PX4_PARAM_IMU_GYRO_RATEMAX` env value survives `rc.mc_defaults`
(ULog initial parameters 800 / 400); PX4 measures the gyro at 800 Hz (`vehicle_imu_status`); the vehicle flies hover
and step_roll; wall time ~35-40 s per run at speed 4 (about the same as on the 4 ms world).

Finding: the logger's default 3.5 ms timer logged every 800 Hz topic at ~285 Hz (queue depth 1, samples lost). With
`-p sensor_gyro` the gyro is complete but downstream topics still lose 10-20 % of samples. Open: race with the
publish chain or wall-time limit at speed 4 (run at speed 1 / poll on actuator_motors, below).

| run | speed | logger | flies | logged rates (mean) | dropouts |
|---|---|---|---|---|---|
| step_roll_sp1_sensor_gyro | 1 | -p sensor_gyro | ok | gyro 800, vav 685, torque_sp 693, act_motors 630, esc 758 | 0 |
| step_roll_sp4_actuator_motors | 4 | -p actuator_motors | ok | gyro 800, vav 800, torque_sp 800, act_motors 800, esc 786 | 0 |

Verdict: the loss is a race with the publish chain (speed 1 is no better), not a wall-time limit. Runner default is now
`--log-poll actuator_motors`. At `--rate-hz` 400/267 the gyro is then logged at the controller rate (sensor_gyro at
800 Hz is not needed by any analysis; vehicle_angular_velocity is). Open (ANOMALIES A-S16-1): esc_status 98 % with
zero-dt pairs (dt p1 = 0): duplicate stamps from the gz_bridge motor callback, to be explained before esc_status
feeds a rate-sensitive metric.
