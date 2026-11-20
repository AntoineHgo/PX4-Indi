# S142 G5 events pre-test notes (written as found)
- Physics step 1.25 ms (run.json physics_step_s), not 4 ms. ATTITUDE ticks seen by the runner are 10-20 ms: runner-side applied time is tick-limited.
- G5.6 maybe_landed: land detector needs minimum thrust AND ground_contact (needs commanded descent) -> not forceable by params at 3 m hover. No shell/MAVLink hook. NOT INJECTABLE.
- G5.11: xy via MAV_CMD_EXTERNAL_POSITION_ESTIMATE 43003 (COMMAND_INT, accuracy <1 -> hard reset; ekf2/EKF2.cpp:574, ekf.cpp:286). yaw via 43002 EXTERNAL_ATTITUDE_ESTIMATE (EKF2.cpp:624). z: hard-reset path only resets horizontal -> z NOT INJECTABLE.
- G5.8: RC loss = stop RC_CHANNELS_OVERRIDE (becomes input_rc), link loss = stop GCS HEARTBEAT, offboard loss = stop setpoints; failsafe actions set to Hold, *_EXCEPT = 0.
- G5.9: kill via RC kill switch (RC_MAP_KILL_SW=7 on RC override ch7); stick-gesture kill is one-way (no unkill) and kill is not cleared on disarm -> re-arm denied ("Flight termination active"), so the switch OFF is used to unkill.
