# SITL benchmark runner v0 - progress log

## Step 1: environment findings (before writing code)
- Container px4-indi-sim: pyulog, numpy, pymavlink importable. `mavsdk` is **v4.1 native binding** (new API, NOT the
  old gRPC `mavsdk.System`/`mavsdk.offboard`; `mavsdk_grpc` is not installed). Decision: use **pymavlink** for the
  runner. Bonus: MAVLink messages carry `time_boot_ms` = PX4 sim time, so setpoint timing is driven from
  sim time directly (no wall-time scaling needed; works for any speed factor).
- pyulog also importable on the host, metrics.py runs anywhere.
- Noise seeding: gz sensor noise (IMU/mag/baro in x500_base/model.sdf) is drawn from gz-math `Rand`, and
  `gz sim --seed N` exists ("Pass a custom seed value to the random number generator"). px4-rc.gzsim attaches to an
  already running world, so run_scenario.py starts `gz sim -r -s --seed N world` itself BEFORE px4. PX4 side:
  SensorBaroSim uses srand(1234) (fixed, not seedable without firmware change; only used by sim baro module).
- PX4 persistent state: the shared build/px4_sitl_default/rootfs keeps parameters.bson between runs, so the runner
  uses a fresh per-run working dir (OUT/rootfs) -> every run starts from airframe defaults; also makes parallel runs safe.
- Logger: SDLOG_PROFILE default (1) logs vehicle_angular_velocity/rates_setpoint at 50 Hz only; runner sets
  SDLOG_PROFILE=17 (default + high rate) so rates/attitude/actuator_motors are logged at full rate.

## Step 2: wrote scenarios.py + run_scenario.py (pymavlink based), first test next
- First end-to-end run OK (step_roll, speed 4, -N network namespace works for gz + px4 + MAVLink; ~31 s wall for ~60 s sim).
  Fix: ULog lives under rootfs/fs/log/..., so the runner globs recursively.
- Findings from first runs: (1) logger must be restarted after setting SDLOG_PROFILE (reads it at start) -> runner does
  `px4-logger stop/start -t`; then actuator_motors/vehicle_angular_velocity/rates_setpoint/attitude are ~250 Hz.
  (2) Arming can be denied right after "Ready for takeoff" ("height estimate not stable") -> arm retried.
  (3) Open-loop thrust=hover_estimate/cos(tilt) drifted 20 m in altitude over a roll scenario (3 % thrust error);
  added a PD altitude loop on the thrust in attitude/rate scenarios (same for all controllers).
  (4) Roll +-15 deg for 3 s drifts the vehicle ~30 m horizontally (open-loop attitude; inherent to the spec'd steps).
