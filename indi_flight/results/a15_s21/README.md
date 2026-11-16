# A-15 fix (session 21): sim_ground_truth topic, queue 16

## Files changed (uncommitted)
- `msg/SimGroundTruth.msg` (new, sim-only): timestamp, timestamp_sample, q[4], angular_velocity[3], x y z vx vy vz, `ORB_QUEUE_LENGTH = 16`.
- `msg/CMakeLists.txt`: `SimGroundTruth.msg` in the non-versioned list (alphabetical, list is sorted anyway).
- `src/modules/simulation/gz_bridge/GZBridge.hpp`: include + `_sim_ground_truth_pub`.
- `src/modules/simulation/gz_bridge/GZBridge.cpp`: in the pose callback, right after the `_lpos_ground_truth_pub.publish`, one
  `sim_ground_truth` sample copied from the values just published (the three stock publications are unchanged).
- `indi_flight/bench/run_scenario.py`: `sim_ground_truth` in LOG_TOPICS.
- `indi_flight/bench/a15_gaps.py`: topic added to the fixed TOPICS list (CLI unchanged).
- `indi_flight/bench/a15_truth_equal.py` (new): equality check on matched timestamp_sample.
- Stock topic queues untouched. `messages.instructions.md` applied: unversioned msg, timestamp + timestamp_sample.

## Build
`indi_project/docker/run.sh -n a15_s21_build -t 1500 -- make px4_sitl_default`: rc 0, 1674 steps, 0 "error" lines (`build.log`).

## Flight
hover, pid_default, quad5in, seed 1, speed 4, rate 800, `-t 300`: rc 0 (`hover/`, `hover_stdout.log`). Logger: 26 topics, log profile
poll `actuator_motors` (runner default). Gap analysis: `gaps.md` (`a15_gaps.py`), equality: `equality.txt`.

## Gap table (after first second of log; gap = dt > 1.9 ms)
| topic | samples | gaps | gap % | max dt (ms) | zero-dt pairs |
|---|---|---|---|---|---|
| sensor_gyro | 56586 | 7 | 0.012 | 5.0 | 0 |
| **sim_ground_truth** | **56578** | **7** | **0.012** | 5.0 | 0 |
| vehicle_attitude_groundtruth (old) | 49150 | 7441 | 15.1 | - | - |
| vehicle_angular_velocity_groundtruth (old) | 49000 | 7591 | 15.5 | - | - |
| vehicle_local_position_groundtruth (old) | 49036 | 7555 | 15.4 | - | - |
| actuator_motors | 56587 | 787 | 1.39 | 6.25 | 777 |
| esc_status | 55535 | 2532 | 4.56 | 6.25 | 1562 |
| vehicle_angular_velocity | 56583 | 309 | 0.55 | - | - |
| vehicle_torque_setpoint | 56582 | 411 | 0.73 | - | - |

Total sim_ground_truth samples (incl. first second) 57390 vs 49819 for the old attitude truth: the old topics still lose ~13 %.
sim_ground_truth gaps coincide with the 7 sensor_gyro gaps (ts_matched 7/7, 5 ms max): they are upstream (sim/sensor), not logger loss.
Logger: 0 dropouts in the ULog (pyulog `ULog.dropouts`), no corruption, no "drop" message in `logged_messages`.

## Equality check (`equality.txt`), matched on timestamp_sample
sim vs vehicle_attitude_groundtruth: 49800 matched, q[0..3] max abs diff 0. vs angular_velocity_groundtruth: 49648 matched,
xyz max abs diff 0. vs local_position_groundtruth: 49685 matched, x y z vx vy vz max abs diff 0. timestamp == timestamp_sample in the new topic.

## Verdict
PASS: sim_ground_truth is complete (56578 vs 56586 gyro samples, 0.012 % gaps < 0.1 %) and bit-identical to the old topics where both exist.
The queue-16 topic removes the A-15 logger loss for the truth.

## Observations / unverified
- actuator_motors (the poll topic) is NOT gap-free by timestamp: 1.39 % gaps and 777 zero-dt pairs (duplicate timestamps, like
  esc_status in A-S16-1: 1562 zero-dt pairs, 4.56 % gaps). So these two are not clean 800 Hz series by timestamp; the cause (publisher
  side duplicates in gz_bridge motor path vs logger) was not investigated. Count-wise they match the gyro (56587 samples).
- Single flight, speed 4 only; `make format` not run; msg docs/ROS translation (`msg/versioned`, px4_msgs) not considered; the topic
  is published on every pose callback in every gz sim (small extra load, ~800 Hz).
- Logger "message_gaps" (ULog sync/dropout stats) not exposed beyond `dropouts` by pyulog: 0.
