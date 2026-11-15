# Determinism s13b: where same-seed runs first differ

Gate G1.6 (determinism). Follows `determinism_s13.md`. Question: at which sim time do two same-seed PX4 SITL runs
(gz, reference airframe quad5in, hover, seed 1) first differ, including the time before arm.

## Status
- Runner change `--log-from-start`: done (uncommitted).
- Runs (`indi_project/docker/run.sh -n det_s13b_rN -t 300`): both `exit_status: ok`, no error, `metrics_status: ok`.
  - r1: `indi_flight/results/det_s13b/r1`, wall 109.3 s, container `px4-indi-det_s13b_r1`, log `indi_flight/results/det_s13b_r1.log`
  - r2: `indi_flight/results/det_s13b/r2`, wall 105.5 s, container `px4-indi-det_s13b_r2`, log `indi_flight/results/det_s13b_r2.log`
  - No stray `det_s13*` container existed before the runs.
- pyulog is not on the host (`ModuleNotFoundError`), so nothing was installed. The comparison ran in the
  `px4-indi-sim` image via `indi_project/docker/run.sh` (the same image the runner's metrics step uses).
- Comparison: done. Lockstep answer: done.

## 1. Runner diff (`indi_flight/bench/run_scenario.py`, only change)
```diff
@@ -488,6 +488,8 @@ def main():
                          "110 ms makes the EKF lead the truth by 110 ms (D-s8-gnss-delay); unset keeps the stock value")
     ap.add_argument("--watchdog", choices=("on", "off"), default="on",
                     help="O-12 run watchdog; 'off' is for diagnosis only, never in a batch")
+    ap.add_argument("--log-from-start", action="store_true",
+                    help="logger starts with -f so the log covers the time before arm (default: from arm)")
     a = ap.parse_args()
@@ -551,7 +553,11 @@ def main():
         # logger reads SDLOG_PROFILE only at start: restart it so the full-rate profile takes effect
         sim.cli("px4-logger", "stop")
         time.sleep(1)
-        sim.cli("px4-logger", "start", "-b", "20", "-t")
+        logger_args = ["px4-logger", "start", "-b", "20", "-t"]
+        if a.log_from_start:
+            logger_args.append("-f")
+            meta["log_from_start"] = True
+        sim.cli(*logger_args)
         sim.wait_log("Ready for takeoff", 180)
```
Meta gets `"log_from_start": true` only when the flag is set, so default runs write the same meta as before.

## 2. Run status
| run | exit | wall s | arm (vehicle_status, arming_state=2) | run.json `t_arm_us` | arm_attempts | arm_late_s |
|---|---|---|---|---|---|---|
| r1 | ok | 109.3 | 30.012 s | 30.332 s | 1 | none |
| r2 | ok | 105.5 | 30.024 s | 30.588 s | 1 | none |

Arm instants differ by 12 ms. `t_arm_us` is read after the "armed" wait and sits 0.3-0.6 s after the real arm, so
`t_arm_us` is not the reference used below.

Logging window (250 Hz topics, `sensor_combined`, `actuator_motors`, `vehicle_angular_velocity`):
- r1: first sample 14.600 s, last 106.344 s.
- r2: first sample 14.696 s, last 102.604 s.
- So `-f` does not give a log from sim 0. Logging starts near 14.5-14.7 s sim (the logger start looks wall-clock
  driven), and the two starts differ by 96 ms.

## 3. Comparison (pyulog, multi_id 0, matched by timestamp, bitwise on float32)
Note: the raw `sensor_gyro` and `sensor_accel` topics are logged at 1 Hz in this profile (91 and 88 samples,
dt = 1 s), so they cannot be compared at 250 Hz. `sensor_combined` (250 Hz, `gyro_rad`, `accelerometer_m_s2`) is
used for gyro and accel. It is keyed by `timestamp`, not `timestamp_sample`.

Table (a), pre-arm = t < 30.012 s (min of the two arm instants):

| topic | pre-arm compared | identical | first differing timestamp |
|---|---|---|---|
| sensor_combined gyro_rad (250 Hz) | 3816 | 0 | 14.696 s (first shared sample) |
| sensor_combined accelerometer (250 Hz) | 3816 | 0 | 14.696 s |
| sensor_gyro raw (1 Hz) | 0 | n/a | no shared timestamp |

First shared gyro sample at 14.696 s: r1 (-1.275e-3, -4.36e-5, 1.04e-3) vs r2 (-3.19e-5, 8.68e-5, -7.95e-4) rad/s.
The 250 Hz streams are not identical before arm. Samples before 14.696 s exist only in r1, so the divergence is at or
before 14.696 s, and the logs cannot localise it further.

Table (b), timestamps:

| topic | n r1 / r2 | timestamps identical | only in r1 | only in r2 | common |
|---|---|---|---|---|---|
| sensor_combined | 22524 / 21598 | no | 1329 | 403 | 21195 |
| actuator_motors | 22392 / 21474 | no | 1442 | 524 | 20950 |
| sensor_gyro raw (1 Hz) | 91 / 88 | no | 91 | 88 | 0 |

The 250 Hz sample grid is the same (4 ms, phase on multiples of 4 ms), so differences are only the logger
start/stop offset. The 1 Hz `sensor_gyro` timestamps differ between runs (15.412 s vs 15.508 s), so none match.

Table (c), first differing sample (sim time, relative to each run's own vehicle_status arm):

| topic | first differing sim time | rel arm r1 (30.012 s) | rel arm r2 (30.024 s) | post-arm first diff |
|---|---|---|---|---|
| actuator_motors control[0..11] | 14.696 s | -15.316 s | -15.328 s | 30.012 s, 0 identical of 17135 post-cutoff samples |
| vehicle_angular_velocity xyz | 14.696 s | -15.316 s | -15.328 s | 30.012 s, 0 identical of 17048 |
| sensor_combined gyro (post-arm at arm) | 14.696 s | | | 30.012 s, max abs diff 1.24e-3 rad/s |
| sensor_combined accel (post-arm at arm) | 14.696 s | | | 30.012 s, max abs diff 1.9e-2 m/s^2 |

actuator_motors at 14.696 s: r1 control[0] 0.00084595, r2 0.00080139. vehicle_angular_velocity at 14.696 s: r1
(-1.02e-3, -1.42e-4, 3.90e-4), r2 (-3.04e-4, -2.14e-4, -6.36e-4) rad/s.

So the first differing sample is before arm in every stream checked, and the arm itself is not the cause.
The s13 note (gyro differs 2.9e-3 rad/s 28 ms after arm) is a window maximum; here the first post-arm sample already
differs by 1.2e-3 rad/s.

## 4. Lockstep answer: free-running, not lockstep
- No gz lockstep anywhere in `src/modules/simulation/gz_bridge` or `Tools/simulation/gz`. The only "lockstep"
  hits in `src/modules/simulation` are in `simulator_mavlink` and `simulator_sih`.
- Sim speed is set by the world: `Tools/simulation/gz/worlds/default.sdf:5-7` (`max_step_size` 0.004,
  `real_time_factor` 1.0, `real_time_update_rate` 250), so gz runs at wall-clock real time.
- PX4 follows the gz clock but does not gate it: `src/modules/simulation/gz_bridge/GZBridge.cpp:474-488`
  (`clockCallback` sets the realtime clock once and syncs CLOCK_MONOTONIC on each callback, no wait); the bridge
  subscribes to `/world/<name>/clock` at `GZBridge.cpp:203-208`.
- Actuator commands are published to gz without waiting for a step ack:
  `src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp:112-113` (`_actuators_pub.Publish`).
- `Tools/simulation/gz/server.config:2-17` loads no lockstep plugin.
- Caveat: `runner_fixed_times_s12.md` (header) calls the sim "lockstep", which refers to the runner's
  MAVLink pump (`sim.run`), not to gz. That wording should be corrected.

## 5. Conclusion
1. The first divergence is in the 250 Hz logs at sim 14.696 s, the first sample shared by both runs. This is
   about 15 s before arm, and the logs cannot show whether it starts earlier.
2. Every pre-arm sample differs (0 of 3816 for gyro, accel, motors and angular velocity), so arm timing is not the
   source. The 12 ms arm offset is a secondary effect.
3. Most likely source: gz is free-running at real_time_factor 1 with no lockstep (`default.sdf:5-7`,
   `GZMixingInterfaceESC.cpp:112`). Plant and sensor-noise steps therefore depend on wall-clock scheduling
   before 14.7 s, which the 96 ms logger start offset already shows.
4. Second candidate, not checked: gz sensor-noise RNG is not seeded from `--seed`, so the noise sequence depends on
   the number of sensor updates before the logger starts.
5. Next step to separate them: log from sim 0 (start the logger before the PX4/gz boot waits), and check whether
   the gz IMU noise has a fixed seed in the model/world. A pass needs lockstep or a fixed step count per sim second.

## Unverified
- The logger start being wall-clock driven (inferred from the 96 ms offset only).
- The noise-seed hypothesis (item 4) and whether `-f` is the only reason logging starts at 14.5 s (not confirmed in
  PX4's logger source).
- Whether the runner's `sim.run` pump makes PX4 and gz step together in practice (inferred from the code, not
  traced at runtime).
- The 1 Hz rate of raw `sensor_gyro`/`sensor_accel` in this profile was seen in the logs, not traced to the
  profile config.
- The 250 Hz comparison uses `sensor_combined`, not the raw topics requested in step 3.
- The analysis ran in the sim image with the pyulog version there; the host has no pyulog.
