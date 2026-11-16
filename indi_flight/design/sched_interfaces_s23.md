# D-SCHED interface mapping (session 23)

Read-only mapping of the PX4 interfaces a SITL-only schedule-replay module must
reproduce. Checkout: `/home/ahugo/Documents/Drotek/Codes/PX4-Indi`, branch `feat/indi-flight`.
Line numbers refer to the working tree at mapping time. Items marked UNVERIFIED
were not read in this pass.

Goal recap: the replay module publishes on uORB exactly what `MavlinkReceiver`
would publish, so commander and controllers stay unchanged. Decision record:
`indi_flight/DECISIONS.md`, section D-SCHED.

## 1. SET_POSITION_TARGET_LOCAL_NED in offboard

Handler: `src/modules/mavlink/mavlink_receiver.cpp:1236`.

- Gate (1241-1245): `get_forward_externalsp()` must be true, `target_system` matches
  this sysid or is 0, `target_component` matches or is 0.
- Frame: only `MAV_FRAME_LOCAL_NED` is handled. Other frames log an error and return
  (1312-1316). FORCE type-mask bit rejects the message (1323-1329).
- Setpoint fields (`trajectory_setpoint_s setpoint{}`), NaN where the type_mask says ignore:
  position x/y/z, velocity vx/vy/vz, acceleration (from body-frame AFx/AFy/AFz,
  rotated by attitude) and yaw / yawspeed (1313-1346 region; yaw at ~1342, yawspeed at ~1343).
  Note: a position-only message gets acceleration set to NaN (~1365 pattern).
- `fill_offboard_control_mode()` (1223-1233) derives the flags:
  `position`, `velocity`, `acceleration` = vector not all NaN; `attitude` = `isfinite(yaw)`;
  `body_rate` = `isfinite(yawspeed)`.
- Publishes:
  1. `offboard_control_mode` (`_offboard_control_mode_pub`), only if
     `position || velocity || acceleration` (1333). Sets `ocm.timestamp = hrt_absolute_time()` (1334).
     Otherwise logs "invalid" (1347-1349) and publishes nothing.
  2. `trajectory_setpoint` (`_trajectory_setpoint_pub`) at 1339-1343, only when
     `vehicle_status.accepts_offboard_setpoints` is true. The receiver copies
     `vehicle_status` from `_vehicle_status_sub` (1337-1338). Sets `setpoint.timestamp = hrt_absolute_time()` (1341).
- Not published by this handler: no `vehicle_command`, no `vehicle_command_ack`.
- Gotcha for the replay: `trajectory_setpoint` is gated on `accepts_offboard_setpoints`.
  The replay must read `vehicle_status` the same way or it will diverge when not in offboard.
- Same pattern for SET_POSITION_TARGET_GLOBAL_INT at 1367 (publish at 1447-1467).
- Also `offboard_control_mode` is published at 1922-1926 from another path (not analysed).

## 2. Arm / mode commands and commander checks

### What the receiver publishes

`vehicle_command_s` on `_cmd_pub`. Common fields in the COMMAND_LONG path
(`mavlink_receiver.cpp:559-595`):
- `timestamp = hrt_absolute_time()` (560s).
- `param1..param7` copied from the MAVLink message (param5/6 cast to double). Sentinel check
  at 565-572 denies INT32_MAX-looking param5/6.
- `command = cmd_mavlink.command` (MAV_CMD id, e.g. 400 ARM_DISARM, 176 DO_SET_MODE).
- `target_system = mavlink_target_system(msg, cmd_mavlink.target_system)`.
- `target_component = cmd_mavlink.target_component` (raw, not remapped).
- `source_system = msg->sysid`, `source_component = msg->compid`.
- `confirmation = cmd_mavlink.confirmation`.
- `from_external = true` (589).

Dispatch: `handle_message_command_both()` at 719. Generic commands are published at 932
(`_cmd_pub.publish`). DO_SET_MODE is published at 796-798 with `send_ack = false`
(commander sends the ack).

Separate MAVLink `SET_MODE` message path, `handle_message_set_mode` at 1128-1146, builds
a DO_SET_MODE with:
- `param1 = base_mode`, `param2 = custom_mode.main_mode`, `param3 = custom_mode.sub_mode`.
- `command = VEHICLE_CMD_DO_SET_MODE`.
- `target_component = MAV_COMP_ID_ALL` (0).
- `source_system/component` from msg, `confirmation = true`, `from_external = true`.

### Values for ARM and OFFBOARD

- ARM/DISARM (`MAV_CMD_COMPONENT_ARM_DISARM`): param1 = 1 arm, 0 disarm. param2 magic
  21196 means "force" (skips checks). Commander reads `forced` at `Commander.cpp:1113-1114`.
- OFFBOARD custom mode: `px4_custom_mode.h:45-50`, `PX4_CUSTOM_MAIN_MODE_MANUAL = 1` and
  OFFBOARD is the 6th entry (numeric value 6; the enum has no explicit values after MANUAL,
  so verify before hard-coding). Commander itself sends OFFBOARD as
  `send_vehicle_command(DO_SET_MODE, 1, PX4_CUSTOM_MAIN_MODE_OFFBOARD)` at
  `Commander.cpp:508`, so param1 = 1 (custom mode flag), param2 = 6, param3 = 0.

### Commander checks

- Target filter, `Commander.cpp:869-871`: `target_system` must equal
  `_vehicle_status.system_id` or be 0; `target_component` must equal
  `component_id` or be 0. Mismatch returns false without ack.
- `from_external` is used at:
  - 1072: MAV_COMP_ID_MISSIONPLANNER (190) special case.
  - 1118-1119: arm reason = `command_external` vs `command_internal`.
  - 1122: `arm(reason, cmd.from_external || !forced)`. A from_external command always
    runs preflight checks, even without the force magic.
- DO_SET_MODE: `Commander.cpp:934` case. Custom main mode OFFBOARD maps to
  `NAVIGATION_STATE_OFFBOARD` at ~1025-1027. Unknown main modes are denied (~1030).
- Offboard setpoint acceptance: `ModeManagement.cpp:770-775`
  `currentModeAcceptsOffboardSetpoints()`. NAVIGATION_STATE_OFFBOARD always returns true.
  This is what gates `vehicle_status.accepts_offboard_setpoints`, read by the receiver at 1337.
- Offboard freshness timeout: `COM_OF_LOSS_T` (`commander_params.yaml:180-190`, float,
  default 1.0 s, unit s). Used in `HealthAndArmingChecks/checks/offboardCheck.cpp:50`:
  `timeout = last_offboard_ts + COM_OF_LOSS_T * 1_s`. The loss-of-offboard failsafe
  action is `COM_OBL_RC_ACT` (per the param description, not read in full).
- `Commander.cpp:3235` updates `_offboard_control_mode_sub`. Offboard `offboard_control_mode`
  must therefore keep arriving within COM_OF_LOSS_T or the check fails.

## 3. MANUAL_CONTROL source selection

Receiver: `handle_message_manual_control` at `mavlink_receiver.cpp:2455`.
- Target filter 2461-2464 (`target` must be 0 or this system).
- Payload type is `manual_control_setpoint_s` (`mavlink_receiver.cpp:2467`), published
  through `_manual_control_input_pub` (publish at 2506; unadvertise at 92). The exact ORB
  topic name is declared in `mavlink_receiver.h`, which was not opened in this pass
  (UNVERIFIED: name expected to be `manual_control_input`).
- Field mapping:
  - `pitch = x / 1000` (2469), `roll = y / 1000` (2471), `throttle = z / 500 - 1` (2476, z in 0..1000),
    `yaw = r / 1000` (2478). Each has a range check.
  - `buttons` copied (2481).
  - `aux1..aux6` gated by `enabled_extensions` bits 2..7 (2483-2499), each `/1000`.
- Source fields:
  - `data_source = SOURCE_MAVLINK_0 + _mavlink.get_instance_id()` (2501).
  - `source_system_id = msg->sysid`, `source_component_id = msg->compid` (2502-2503).
  - `timestamp = timestamp_sample = hrt_absolute_time()` (2504), `valid = true` (2505).

Selection: `src/modules/manual_control/ManualControlSelector.cpp`.
- `isInputValid()` (63-106) switches on `_rc_in_mode` (= COM_RC_IN_MODE, `ManualControl.hpp:153`).
- Modes match on `data_source`. Source enum values: `SOURCE_RC` and `SOURCE_MAVLINK_0..5`
  (`isRc()` 124, `isMavlink()` 128-134).
- `COM_RC_IN_MODE` definition: `commander_params.yaml:62-68`. Enum; priority modes switch
  to a higher-priority source as soon as it is valid. MAVLink 1 is the lower instance.

## 4. Runtime parameter set from C++

- Lookup: `param_find(const char *name)` returns `param_t` (`src/lib/parameters/param.h:99`).
  `param_find_no_notification` also exists (107).
- Set: `param_set(param_t, const void *val)` (`src/lib/parameters/parameters.cpp:520`),
  and `param_set_no_notification` (525). The ioctl path picks between them at
  `parameters_ioctl.cpp:116` and `:119`.
- `parameter_update` publish: `parameters.cpp:176-191` fills `parameter_update_s pup`,
  advertises once (188), then `orb_publish(ORB_ID(parameter_update), ...)` (191). The
  function that calls it was not read in full. Inferred (not verified): `param_set`
  publishes `parameter_update`, `param_set_no_notification` does not.
- `autosave.cpp:57` coalesces saves for multiple `param_set` calls.
- Practical implication: to mimic a receiver-driven or GCS parameter change, use
  `param_set` (publishes `parameter_update`). Use `param_set_no_notification` only to
  avoid the notification.

## 5. gz_bridge clock and sensor_gyro

Clock source, `src/modules/simulation/gz_bridge/GZBridge.cpp`:
- Subscribes to `/world/<world>/clock` at 205-208 with `clockCallback`.
- Waits for the first clock before subscribing other topics (72-77). Comment at 72-73:
  publishing a 0 timestamp breaks the EKF.
- `clockCallback` at 475:
  - First call sets `CLOCK_REALTIME` via `px4_clock_settime` (482-485).
  - Every call syncs `CLOCK_MONOTONIC` via `px4_clock_settime` (488-489). Comment at 477:
    PX4-SITL time must stay in sync with gz.
- Sensor timestamps are clamped with `min(timestamp_sample, hrt_absolute_time())` (645).
- `hrt_absolute_time()` is declared in `src/drivers/drv_hrt.h`. The implementation was not
  located by grep under `src/` in this pass. UNVERIFIED: that it reads `CLOCK_MONOTONIC`.
  Inferred from the 488-489 sync. So in SITL, hrt is the gz sim clock, not wall time.

Gyro topic: `sensor_gyro` (`sensor_gyro_s`, included at `src/modules/sensors/vehicle_angular_velocity/VehicleAngularVelocity.hpp:54`).
Also `sensor_gyro_fifo` (56) when the driver publishes FIFO data.

Pattern for SubscriptionCallbackWorkItem scheduling:
- `src/modules/sensors/vehicle_angular_velocity/VehicleAngularVelocity.hpp:65`:
  class derives from `px4::ScheduledWorkItem`.
- `VehicleAngularVelocity.hpp:112` declares a `uORB::SubscriptionCallbackWorkItem`
  (here for `sensor_selection`).
- `VehicleAngularVelocity.cpp:142-154` sets `set_required_updates()` on the gyro subs
  to batch samples. `sensor_gyro` is consumed through `_sensor_sub` (UNVERIFIED: its type
  was not read; the `set_required_updates` calls at 145 indicate a callback sub).
- Not verified: whether GZBridge publishes `sensor_gyro` directly. It was not confirmed in
  this pass.

## 6. Smallest simulation module skeleton

`src/modules/simulation/` folders with file counts (`find -type f`):
battery_simulator 5, gz_bridge 17, gz_msgs 3, gz_plugins 62, pwm_out_sim 6,
sensor_agp_sim 5, sensor_airspeed_sim 5, sensor_baro_sim 5, sensor_gps_sim 5,
sensor_mag_sim 5, simulator_mavlink 8, simulator_sih 10, system_power_simulator 4.

Smallest by file count: `system_power_simulator` (4 files). Its files were not opened.
The 5-file group (`sensor_mag_sim`, `sensor_baro_sim`, `battery_simulator`, ...) is the
best-read template:
- `src/modules/simulation/sensor_mag_sim/Kconfig`: `menuconfig MODULES_SIMULATION_SENSOR_MAG_SIM`,
  `bool "sensor_mag_sim"`, `default n`, `---help---`.
- `src/modules/simulation/sensor_mag_sim/CMakeLists.txt`: `px4_add_module(MODULE ... MAIN ...
  COMPILE_FLAGS SRCS ... MODULE_CONFIG parameters.yaml DEPENDS ...)`. Note the MODULE name
  typo `modules__simulation__senosr_mag_sim` (CMakeLists.txt line `MODULE`). Copy the
  shape but use the correct spelling.
- Files: `SensorMagSim.cpp/.hpp`, `parameters.yaml`.

Recommendation for the replay module: copy `sensor_mag_sim` layout (Kconfig, CMakeLists,
parameters.yaml if needed, one .cpp/.hpp pair). Add `ScheduledWorkItem` plus
`SubscriptionCallbackWorkItem` on `sensor_gyro` as in section 5.

## Summary

- Offboard: SET_POSITION_TARGET_LOCAL_NED publishes `offboard_control_mode` always (when valid) and `trajectory_setpoint` only when `vehicle_status.accepts_offboard_setpoints` (mavlink_receiver.cpp:1333-1343).
- Commands: COMMAND_LONG sets `from_external=true`, `source_*` from msg, `target_component` raw (559-595). ARM: param1 1/0, param2 21196 forces. OFFBOARD: DO_SET_MODE param1=1, param2=6, param3=0.
- Commander: target match 869-871; from_external forces arm checks (1122); OFFBOARD maps to NAV_STATE_OFFBOARD (~1027).
- Offboard freshness: COM_OF_LOSS_T (default 1.0 s) in offboardCheck.cpp:50.
- MANUAL_CONTROL: `manual_control_setpoint_s` with data_source=SOURCE_MAVLINK_0+instance (2501); selection by COM_RC_IN_MODE in ManualControlSelector.cpp:63-106.
- Params: `param_find` + `param_set` (parameters.cpp:520) publishes `parameter_update`; `param_set_no_notification` (525) is the quiet variant.
- Clock: gz clock sets CLOCK_MONOTONIC each callback (GZBridge.cpp:475-489). hrt impl not verified.
- Gyro: `sensor_gyro`, pattern VehicleAngularVelocity.hpp:65/112.
- Skeleton: sensor_mag_sim (Kconfig, CMakeLists, .cpp/.hpp); fix MODULE typo.
- UNVERIFIED: ORB name of `_manual_control_input_pub`; hrt impl; `sensor_gyro` publisher in gz_bridge; COM_OBL_RC_ACT action.
