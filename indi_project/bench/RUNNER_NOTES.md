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

## Disturbance injection (gust_x, payload_add), session 10
- Scenarios `gust_x` (settle 10 s + 28 s profile) and `payload_add` (settle 10 s + 30 s) in scenarios.py (key `disturbance`);
  run through the normal runner / run_batch.sh. `bench/disturbance.py` is spawned by run_scenario.py after PX4 starts,
  loads `gz-sim-apply-link-wrench-system` at runtime via the world service `/world/default/entity/system/add`
  (called through the `gz service` CLI: the python binding cannot build `gz.msgs.Plugin`), waits for
  `disturbance_trigger.json` (onset in PX4 time, written by the runner at the start of the scenario window) and then
  publishes the wrench at every gz clock tick (250 Hz sim time) on `/world/default/wrench` (ONE-STEP topic).
  `/wrench/persistent` ACCUMULATES every message: re-publishing it each tick summed the force (vehicle crashed / flew away,
  gz ODE abort). Output: `disturbance.csv` (sim_time_s, px4_time_s, fx..tz, world frame, applied at the CoM) + `disturbance.log`.
- Wind is along gz world +x (east) = NED +y; vehicle heading at hover is also east, so the gust shows as body pitch.
- ULog-vs-gz time offset: **0 s** (to within one 4 ms physics step). PX4 syncs its clock to /world/default/clock on every
  callback (GZBridge::clockCallback). Checked on the payload_add flight: onset (PX4 time) 44.516 s, motors react 44.536 s.
  `CLOCK_OFFSET_S = 0.0` in disturbance.py; run.json["disturbance"]["onset_us"] is in ULog time.
- Assumptions: Cd*A = 0.06 m^2, rho 1.225, centre of pressure 0.05 m above CoM (torque r x F), vehicle velocity neglected,
  x500 mass 2.0643 kg (2.0 base_link + 4 x 0.016077 rotors), g = 9.8 (world), payload = 0.25 m g = 5.057 N downward,
  weight only (no added inertial mass or inertia). gust_x window = 28 s (the 15 s hold at 3 m/s IS the 15 s after the gust).
- metrics.json["disturbance"]: peak_attitude_dev_deg (tilt vs pre-onset body z), peak roll/pitch dev, peak_position_dev_m
  (horizontal for gust_x, vertical for payload_add), recovery_s = first time >= peak with error <= 0.1 m for 2 s
  (null if never, within the window), final_position_error_m.
