# A-12 fix (session 18): ground truth at sim-step rate

## Cause (confirmed)
- Truth = `GZBridge::poseInfoCallback`, subscribed to `/world/<w>/pose/info` of the gz SceneBroadcaster. Measured with gz alone
  (`results/a12_fix_s18/pose_topic_hz.txt`, `gz topic -e -n 300`): `/world/default/pose/info` delivers 300 messages in 5.33 s
  (~56 Hz WALL) at RTF 1, and the same with `dynamic_pose_hertz` AND `state_hertz` set to 10000. So that topic is wall-clock
  throttled and neither SceneBroadcaster parameter lifts it (at speed 4 this is ~14 Hz of sim time: the 14.8 Hz of A-12).
  `/world/default/dynamic_pose/info`, by contrast, delivered 300 messages in 0.46 s (>= 650 Hz wall, i.e. one per 1.25 ms step)
  once `dynamic_pose_hertz` was raised (that throttle is wall-clock too, default 60 Hz; above the step rate it is every step).
- Run with only `dynamic_pose_hertz` raised and the old topic: groundtruth still 14.8 Hz, max gap 68.8 ms (`hover_s4_dynpose_only_old_topic`).
- `Tools/simulation/gz` is a git SUBMODULE (detached at a15af96, clean): NOT touched. The runs use
  `indi_flight/sim/worlds/default.sdf` (no plugins) + `src/modules/simulation/gz_bridge/server.config` (main repo).

## Change (2 files, uncommitted)
- `src/modules/simulation/gz_bridge/server.config`: SceneBroadcaster gets `<dynamic_pose_hertz>10000</dynamic_pose_hertz>` (+ comment).
- `src/modules/simulation/gz_bridge/GZBridge.cpp` `subscribePoseInfo`: topic `/world/<w>/dynamic_pose/info` instead of `.../pose/info`
  (+ one comment line). Rebuilt in Docker (`build.log`), no other change. Needs `make format` check (not run).

## Verification (hover, quad5in, pid_default, seed 1, speed factor 4, 1.25 ms world, 800 Hz; `results/a12_fix_s18/hover_s4`)
- exit_status ok, speed 4.0. `gate_g1.sh g1.1`: vehicle_local_position_groundtruth median 800.0 Hz (declared 50, limit gap 60 ms),
  max gap 5.0 ms, PASS (`g1_1_fixed.txt`). Before: 14.8 Hz, 68.8 ms. Mean over the log 694.7 Hz (some 2.5-5 ms gaps; stationary
  entities are not in dynamic_pose, likely on the ground before take-off - not checked).
- G1.1 overall still FAIL for other rows: vehicle_local_position 88.9 Hz vs 125 (separate), 800 Hz rows gap 13.8-15 ms (A-13/A-10).

## Unverified / flags
- Only one flight, one speed (4). Speed 1 not re-run; the topic is per-step so it should be unchanged.
- dynamic_pose omits entities whose pose did not change: truth could pause while the model rests (e.g. before arming); not examined.
  GZBridge `dt` for the angular-velocity derivative is constrained 1..100 ms (unchanged code); at 800 Hz it clamps to 1.25 ms > 1 ms, fine.
- vehicle_attitude_groundtruth / vehicle_angular_velocity_groundtruth are logged at 100 Hz (logger rate, 7146 samples), not 800.
- Higher callback rate (800 Hz) adds PX4 load; flight ran fine at speed 4 (~40 s wall). Other airframes/worlds using the stock
  gz_bridge now also get dynamic_pose (any other consumer of `/pose/info` unaffected: topic still published).
- Source semantics (wall-clock throttle) inferred from measured rates, gz-sim source not in the image.
