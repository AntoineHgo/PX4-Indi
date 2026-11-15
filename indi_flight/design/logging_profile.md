# Full-rate logging for the bench runner (G1)

## Mechanism (source)
- `src/modules/logger/logged_topics.cpp:644` reads `PX4_STORAGEDIR "/etc/logging/logger_topics.txt"` after the profile adds (`:596-643`).
- SITL `PX4_STORAGEDIR` = `CONFIG_BOARD_ROOT_PATH` = `"./fs"` (`defines.h:106`, `boards/px4/sitl/default.px4board:4`). px4 chdirs to `-w` (`platforms/posix/src/px4/common/main.cpp:325`), so the path is `<rootfs>/fs/etc/logging/logger_topics.txt`, not `<rootfs>/etc/logging/`.
- It ADDS to the profile, it does not replace it. Profile 17 still applies. A listed topic the profile already logs only gets its interval overridden (`:557`).
- Line format `name interval [instance]`. Two fields log all instances (add_topic_multi), which overflows the 255-slot table (`logged_topics.h:79`, warning at `:520`).

## Runner change (indi_flight/bench/run_scenario.py)
- `LOG_TOPICS` (lines 52-59): the requested 18 plus vehicle_local_position_groundtruth, control_allocator_status, indi_pos_status (read by metrics.py).
- `start_px4` writes `topic 0 0` lines (interval 0, instance 0) to `<rootfs>/fs/etc/logging/`.

## Pre-test: hover, pid_default, quad5in, seed 1 (results/pretest_logging_s10)
- Exit ok, 83.1 s wall, "logging 21 topics from logger_topics.txt", 0 overflow warnings. metrics.py and applied_timing.py ran clean.

| topic | median dt | rate (Hz) |
|---|---|---|
| actuator_motors, esc_status, sensor_combined, vehicle_attitude, vehicle_acceleration, vehicle_angular_velocity, vehicle_rates_setpoint, vehicle_thrust/torque_setpoint | 4 ms | 250 |
| vehicle_attitude_setpoint, vehicle_local_position(_setpoint), hover_thrust_estimate, control_allocator_status | 8 ms | 125 |
| trajectory_setpoint, vehicle_local_position_groundtruth | 20 ms | 50 |
| vehicle_status, vehicle_control_mode, vehicle_land_detected, parameter_update | 0.5 s, 1 s, event | 2, 1, - |
| indi_pos_status | absent | not published by pid_default |

- flight.ulg 27.0 MB for 64.7 s (s9 at profile 17: 24.1 MB, vehicle_acceleration ~21 Hz).
- 250 Hz matches the 4 ms sim step. The 125 and 50 Hz topics are their producers' publish rates.

## Unverified
- indi_pos_status rate needs an INDI position run (only mc_indi_pos_control publishes it).
- 250 Hz ceiling inferred from the physics step, not measured against the logger.
- Log size for longer and INDI runs not measured.
- Failed first try kept at results/pretest_logging_s10_try1 (all-instance version, invalid).
