# A-15 cause analysis (session 20): truth stream misses ~13 % of physics steps

Read-only analysis, no firmware edited. Log analysed: `results/a12_fix_s18/pretest_truth_topics/hover/flight.ulg`
(hover, speed 4, 1.25 ms world). Evidence tags: [SRC] read in source, [LOG] measured on the ULog, [INF] inferred, [UNV] not verified.

## Verdict (revises T41 / STATE.md "gz_bridge pose, not logger")

Most likely cause: the truth samples are PUBLISHED at every step but the LOGGER loses them. The three truth topics are uORB
queue-1 topics, published from the gz-transport receive thread, and the logger copies only the newest sample once per wake.
When two truth publishes land between two logger wakes, the first is overwritten. The IMU is spared because `sensor_gyro`
has a uORB queue of 8. The "gap in timestamp_sample" is then expected: the logged sample is the one that survived.

## Mechanism, with references

1. One thread feeds everything [INF]. `GZBridge` subscribes clock (`GZBridge.cpp:203-212`), IMU (`:233-257`) and
   `dynamic_pose/info` (`:215-227`) through one `gz::transport::Node`; callbacks (`clockCallback :475`, `imuCallback :633`,
   `poseInfoCallback :669`) are plain callbacks with no mutex, no try_lock, no "same timestamp, skip" check, no queue
   [SRC: read, none present]. That gz-transport runs them sequentially on the node's receive thread is [INF] from library
   knowledge, gz-transport source not read.
2. Truth publish is unconditional per pose message [SRC]. `poseInfoCallback` stamps `timestamp = hrt_absolute_time()` (`:671`,
   not the gz message stamp) and publishes attitude (`:700`), angular velocity (`:711`), local position (`:754`) for every
   message that contains the model. Same stamp for the three -> the three gap lists coincide (97-100 % in `results/a15_s20/README.md`) [LOG].
3. Queue depth differs [SRC]. `msg/SensorGyro.msg:19` has `ORB_QUEUE_LENGTH = 8`; VehicleAttitude, VehicleAngularVelocity,
   VehicleLocalPosition have no `ORB_QUEUE_LENGTH` (grep: none) -> queue 1. `PX4Gyroscope::update` therefore never overwrites an
   unread gyro sample under jitter; the truth publishes can.
4. The logger takes one copy per wake [SRC]. `Logger::copy_if_updated` (`logger.cpp:455-475`) calls `sub.update` once per
   subscription per loop; the loop waits on a poll of `-p <topic>` (`logger.cpp:918-935`, here actuator_motors, S16 choice).
   Truth is published by a different thread than the controller chain that wakes the logger, so truth publishes and logger
   wakes are not phase-locked; jitter at speed 4 (312 us wall per step) makes two truth publishes per wake common enough
   to lose 13 %.
5. The logger counted these losses itself [LOG]. `logger.cpp:469` increments `_message_gaps` when a full-rate topic's uORB
   generation jumps by more than 1, and `:1077` writes it to `logger_status`. In this log `message_gaps` max = 24553.
   Sum of per-topic sample gaps from `a15_s20/README.md` for the topics that exist at full rate: attitude_gt 7571 +
   angvel_gt 7741 + lpos_gt 7705 + actuator_motors 787 + vehicle_angular_velocity 325 + torque_setpoint 429 = 24558.
   24553 vs 24558: the match is to 5 counts. A generation jump means the publisher DID publish; the logger skipped it.
   (If gz or gz_bridge had not produced a pose for a step, the generation would not jump and `message_gaps` would not
   count it.) Caveat [INF]: the match could be partly a coincidence of two counts being large; the esc_status gaps
   (2.9k) are not in the sum, so that topic is presumably logged with an interval or counted differently [UNV].
6. Step structure [LOG]. Truth dt histogram over 51.9k samples: 1 step 44115, 2 steps 7814, 3 steps 6; no duplicate
   timestamps. Gaps are almost all single missed steps, evenly spread (490-575 per 5 s over the whole 75 s, flat,
   including on the ground) with median spacing 5 samples. Not a stationary-entity effect and not one big stall.
   sensor_gyro: 59753 samples, 10 double-steps.

## What was ruled out or not ruled out

- gz-sim SceneBroadcaster wall-clock throttle (`dynamic_pose_hertz` 10000, `server.config` SceneBroadcaster entry): would drop
  steps at the publisher, but then `message_gaps` would not see them. Not excluded by direct measurement, only
  disfavoured by item 5 [INF]. Its exact semantics are [UNV] (gz-sim source not in the repo or image; A-12 note says the same).
- gz-transport drops: ZMQ default high-water mark is far above the backlog here; the same socket carries the IMU with 10 gaps
  in 59.7k [INF].
- The world SDF (`indi_flight/sim/worlds/default.sdf`: step 0.00125, `real_time_update_rate` 800, no pose plugin) does not
  publish poses; the publisher is the SceneBroadcaster in `src/modules/simulation/gz_bridge/server.config` [SRC].
- IMU sync: PX4 is NOT in lockstep with gz (the gz clock only sets CLOCK_MONOTONIC, `GZBridge.cpp:475-491`); IMU samples
  are paced by the stream order, not by a barrier [SRC].

## Fix options

| # | change | effect | risk |
|---|---|---|---|
| F1 | No firmware: run truth-critical logs with the logger polling the truth topic: `--log-poll vehicle_local_position_groundtruth` (flag already exists in `bench/run_scenario.py`, S16). | Logger wakes once per truth publish; expect truth gaps to vanish. Controller topics (queue 1: actuator_motors, vehicle_angular_velocity, torque_setpoint) will then show similar loss to what truth has now, and `sensor_gyro` stays complete (queue 8). | Zero firmware risk. Moves the problem to the controller topics, so G1.1 on those would need a second run. |
| F2 | Sim only, gz_bridge: advertise the three `*_groundtruth` nodes with queue 8 (`orb_advertise_multi_queue`-style call instead of the plain `uORB::Publication`, if the first advertiser sets the node queue size) [UNV: API and the logger draining a queued topic not checked]. | One logged truth sample per step, no loss. The real `vehicle_attitude`/`vehicle_local_position` nodes are separate and unchanged. | Small, only SITL gz_bridge. A queued topic is read oldest-first, so a consumer that falls behind sees stale truth; only the logger and bench read it. |
| F3 | Change `ORB_QUEUE_LENGTH` in the three msg files. | Same as F2. | NOT recommended: the msgs are shared with flight code (`vehicle_attitude` etc.) and change subscriber semantics and RAM on every target. |
| F4 | Run speed 1 for truth-grade gates. | Expected to cut the loss, wall step is 1.25 ms [INF]. | 4x slower runs; may not reach zero. |

Smallest fix that gives one truth sample per step: F1 now (no code), F2 if truth and controller topics must both be complete in
one log. Do not touch the SceneBroadcaster rate again (A-12 already set it to per step).

## Cheap discriminating tests (in order)

1. Zero cost, log already in hand: read `logger_status.message_gaps` per run and compare with the summed per-topic sample gaps
   (done for this log: 24553 vs 24558). If a new log has gaps without a matching `message_gaps`, the loss is upstream.
2. One 40 s hover at speed 4 with `--log-poll vehicle_local_position_groundtruth`: logger-loss hypothesis predicts truth rows
   with no gap (rate ~800 Hz, max gap 1.25 ms) and controller topics gaining gaps; publisher-side loss predicts the same
   13 % truth gaps remain.
3. Same hover at speed 1 with the original poll: logger-loss predicts a large drop in truth gaps; a wall-clock throttle in
   the SceneBroadcaster (which would also vanish at speed 1) is NOT separated by this one, so test 2 is the decisive one.

## Unverified

- gz-sim SceneBroadcaster and gz-transport behaviour (sources not available here).
- That the uORB node queue size of `*_groundtruth` can be set by the advertiser, and that the logger drains a queued topic
  one message per wake without losing the tail.
- Which logger interval the indi profile sets for the truth topics (`logger_topics.txt` is generated by
  `bench/run_scenario.py`; the `message_gaps` counter only applies to interval-0 topics, so a nonzero interval would
  change item 5).
