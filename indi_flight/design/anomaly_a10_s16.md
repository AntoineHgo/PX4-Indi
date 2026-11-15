# Anomaly A-10 (session 16): esc_status sampling in the sim-step pre-test

Log: `indi_flight/results/pretest_simstep_s16/step_roll_sp4_actuator_motors/flight.ulg`
Setup: controller and IMU at 800 Hz, physics step 1.25 ms, logger polls actuator_motors.
Read-only investigation: no simulation, docker or git command, no code edits.

## 1. Log statistics (pyulog, esc_status multi_id 0)

- Only one esc_status instance exists (multi_id 0), 43869 samples; actuator_motors 44649 samples.
- Fields: `counter`, `timestamp`, `esc_count`, `esc_armed_flags`, `esc_online_flags`, `esc_connectiontype`,
  and `esc[0..11]` each with `timestamp`, `esc_rpm`, `esc_current`, `esc_voltage`, `esc_power`,
  `esc_errorcount`, `esc_state`, `esc_temperature`, `motor_temperature`, `actuator_function`, `failures`.
  Field `esc[k].timestamp` exists for every k. Top-level `timestamp` equals `esc[0].timestamp` in 43849 of 43869 rows (20 differ).
- `counter` is 0 in every row (the GZ path never sets it), so it cannot tell publications apart.
- esc_count = 4 (only esc[0..3] are live; esc[4..11] are constant zero). esc_armed_flags takes values 0 and 15.
- diff(timestamp) histogram (us): 1250: 39541; 2500: 2392; 0: 1822; 3750: 112; 8750: 1.
- Zero-dt pairs: 1822. Gaps > 1900 us: 2505 (2392 of 2500 us, 112 of 3750 us, 1 of 8750 us).
- Zero-dt pairs with identical esc_rpm (all 12 esc[k].esc_rpm compared): 1464. With differing esc_rpm: 358.
- Every esc_status stamp lies exactly on the 1.25 ms grid anchored at actuator_motors[0] (residual 0 us for all 43869 rows).
- Slot view: 44669 grid slots spanned; 42047 slots hit; 2622 empty; 1822 slots hit twice (max 2 per slot).
  The shortfall 44649 - 43869 = 780 equals 2622 empty slots minus 1822 doubled slots.
- Neighbours of zero-dt pairs: previous gap 2500 us in 1250 cases, 1250 us in 490, 3750 us in 82;
  next gap 1250 us in 1311 cases, 2500 us in 490, 3750 us in 21.
  Only 490 of the 2392 2500-us gaps directly follow a zero-dt pair; the other ~1900 holes are not paired with a duplicate.
- actuator_motors: 44649 samples, dt 0/1250/2500 at the 1st/50th/99th percentiles, i.e. the 2500-us gaps are not in the
  PX4 output log for this topic, which is what the 1.25 ms grid comparison relies on (its own percentile output shows 0 at p1, a
  measure of the same kind of artifact; see the note in section 3).

## 2. Publication path (source)

- `GZMixingInterfaceESC::motorSpeedCallback` (GZMixingInterfaceESC.cpp:128-193) is the only place esc_status is published.
  Each esc_status is stamped with `hrt_absolute_time()` read inside the callback (lines 141 and 187); the `esc_count > 0` guard
  is the only gate.
- The callback is subscribed to `/<model>/command/motor_speed` (line 52-57). The same topic is advertised for output by
  `GZMixingInterfaceESC::updateOutputs` (lines 60-61, publish at 112-113). So one esc_status is produced per gz `Actuators`
  message delivered on command/motor_speed, i.e. per PX4 output update that has active outputs. It is not a fixed 800 Hz
  timer and not a per-physics-step publish by GZ itself. (Whether gz delivers PX4's own publish back to this node's subscriber
  is inferred from the same-topic subscription, not verified at runtime.)
- The PX4 output update: `MixingOutput` calls `_interface.updateOutputs` at `src/lib/mixer_module/mixer_module.cpp:532`;
  scheduling is set via ScheduleNow / ScheduleOnInterval at mixer_module.cpp:258, 340, 344, 348. Which interval applied in this log is not verified.
- Clock: `GZBridge::clockCallback` (GZBridge.cpp:474-490) sets CLOCK_MONOTONIC (and REALTIME once) from the gz `/world/<w>/clock`
  message on every callback. So hrt_absolute_time() in SITL is the gz sim time at the last clock message: piecewise constant between
  clock messages, not updated per callback. esc_status stamps are gz sim time, not wall clock.
  The rate of the /clock messages (one per physics step?) is not verified in the repo.

## 3. Conclusions

- Zero-dt pairs: two esc_status publications (two motor_speed callbacks) handled between the same two /clock updates, so both
  take the same hrt. Evidence: 358 zero-dt pairs have differing rpm, which excludes a plain duplicate log for those; the other
  1464 have identical rpm, consistent with two publications from the same rotor-speed snapshot (not proven; a logger duplicate
  of one publication is not excluded by this data, because `counter` is 0 and carries no generation information).
- Missing 2 %: esc_status is produced only when the gz callback runs, and its stamp is the clock value at that moment. A
  callback that does not arrive before the clock moves on leaves its 1.25 ms slot empty (2622 empty slots in total); a delivery
  that lands in the same clock tick as the previous one doubles a slot (1822). Net 780 = 2622 - 1822. The PX4 output side
  (actuator_motors) is complete, so the loss is on the GZ/callback delivery side, not in the output update. Mechanism of late/merged
  deliveries: inferred, not verified at runtime.
- Rotor-speed analysis at controller rate must resample esc_status by sample stamp, not by row index: duplicates and holes shift
  row numbers (1822 duplicate rows, 2622 holes). Use: collapse equal stamps (keep last, or check rpm agreement), then zero-order hold
  on the 1.25 ms grid of actuator_motors / vehicle_angular_velocity. Keep the feedback latency of ESC mode 2 as it is, since the
  reply latency is part of the stamped data (GZMixingInterfaceESC.cpp:147-163).

## Unverified
- gz delivery of the node's own motor_speed publish back to its subscriber (inferred from the topic).
- Rate of gz /clock messages and the mixer scheduling interval in this run.
- Whether the 1464 identical zero-dt pairs are two publications or a duplicate log.
- The 2500-us holes not paired with a duplicate (about 1900) and any dependence on feedback mode (esc_feedback value of this run not read).

## Orchestrator correction (S16)
The "correction" above is wrong: it read `timestamp`. By `timestamp_sample` (sim-time sample stamp), the
controller-rate topics are complete in step_roll_sp4_actuator_motors: actuator_motors 0 zero-dt / 16 gaps > 1.9 ms
(n 44649), vehicle_angular_velocity 0 / 20. Their publish `timestamp` jitters by one /clock tick (actuator_motors 892
zero-dt, 903 gaps; vav 257 / 273: pairs, no loss). esc_status has no sample stamp and is stamped at publication
(hrt = gz /clock) from the asynchronous motor-speed callback: 1822 doubled, 2505 empty grid slots, net 780 (1.7 %)
lost. Likely mechanism (UNVERIFIED): two publications between two logger wakes, queue depth 1.
Rule: every analysis uses `timestamp_sample` where it exists; esc_status is resampled on its stamps (collapse equal
stamps, hold over empty slots), with the 1.7 % hold reported. Closing test left: confirm the mechanism (esc_status
publication count vs logged count, e.g. a uORB counter or logger poll on esc_status in one run).
