# Implementation log, stage-8 task B (module mc_indi_pos_control)

## Step 1: files written (not yet built)
- New: src/modules/mc_indi_pos_control/{CMakeLists.txt,Kconfig,mc_indi_pos_control_params.yaml,McIndiPosControl.hpp,McIndiPosControl.cpp}, msg/IndiPosStatus.msg.
- Edited: msg/CMakeLists.txt, src/modules/logger/logged_topics.cpp (add_optional_topic indi_pos_status), boards/px4/sitl/default.px4board (CONFIG_MODULES_MC_INDI_POS_CONTROL=y), ROMFS/px4fmu_common/init.d/rc.mc_apps (start if MC_INDIP_EN 1; this is the rc where MC_INDI_EN/mc_raptor start, shared with posix SITL).
- Stock modules untouched.
## Decisions / deviations
- CA_R_W_MAX does not exist in this tree (spec text); the rotor speed at full thrust is MC_INDI_W_MAX (rad/s, owned by mc_indi_rate_control). Read via param_find at runtime (no hard dependency); 0 or missing -> mean_u invalid -> model fallback in the library.
- IndiPosStatus has two extra fields beyond spec: hold_cycles (uint8), failure (bool), to report the hold/mode-failure state (spec: "report mode failure").
- Jerk: a zero or non finite jerk in trajectory_setpoint is passed as NaN so the library uses the a_ref backward difference (MAVLink never writes jerk).
- ESC sample age limit 50 ms (my choice); mean_u needs all 4 motors online and plausible.
- Module runs on vehicle_local_position callback plus a 20 ms ScheduleDelayed backup (arming-check replies, stale detection). Law runs only on new local position samples; hold evaluated on new samples or when local position itself is stale.
- Filter sample rate: measured over the first 50 local position samples (inactive or active), setFilter then; until then the library filter is unconfigured. Re-applied (and library reset) on parameter update.
- Publishes vehicle_rates_setpoint only while nav_state == the registered mode id (stock chain owns it otherwise). setpoint_config timeout_ms = 0 (disabled), my choice.
- Hold state also forces a library reset on the next good cycle.
- No handling of quat_reset_counter (setpoint is replaced every cycle).

## Step 2: build + format
- Fixes: header comment terminator, base class changed to px4::ScheduledWorkItem (WorkItem has no ScheduleDelayed).
- `make px4_sitl_default` via run.sh: success, no warnings in my files (-Werror build). `make format`: passed, git status shows only intended files.
- Not verified: runtime behaviour (no flight), whether commander accepts the mode registration/arming reply sequence, whether MC_INDI_W_MAX is set in the bench airframe/params (needed for measured mean u), esc_status rate in SITL vs the 50 ms age limit, MAVLink trajectory_setpoint rate vs the 100 ms stale limit.
