# Independent review, delay lines A1/A2 (S102), code vs delay_line_hook_s94.md sec 1,2,3,5,7
Working-tree diff of src/modules/simulation/gz_bridge/. Static reading only: no build, no flight.

## BLOCKING
None found.

## MAJOR
M1. IMU subscription precedes the delay assignment. GZBridge.cpp:90 `subscribeImu(false)` starts callbacks;
`_imu_delay_us` is set at :143, later in init(). Samples arriving in between take the undelayed path, then the
ring switches on: a sample-free gap of D appears at start, and `_imu_delay_us` is written unlocked while a
gz thread reads it (data race). The G3 delay is then not constant at boot, and the first "applied" log may be
misleading. Fix: compute `_imu_delay_us` before :90 (or in the ctor), keep it const afterwards.
M2. IMU release uses `hrt_absolute_time()` (GZBridge.cpp "const uint64_t now"). The code itself says
the sim clock can lag the header stamp (:696), so `now` can trail the newest sample. The stored sample time is
clamped to the same `now`, so the delay stays self-consistent, but it is measured on a clock that ticks in
steps and is set by another thread (clockCallback :480). Cheaper and exact: use the newest sample's own stamp
(`timestamp_sample`) as "now" in the release test (IMU time base only, no cross-topic ordering). If kept, state
that applied delay can exceed requested by one IMU period when the clock lags.

## MINOR
m1. Default 0 is NOT byte-identical: new PX4_INFO lines at boot (GZBridge.cpp:144, GZMixingInterfaceESC.cpp:70)
and a new print_status line (GZBridge.cpp ~1296). Control flow and return values are unchanged
(IMU early return after the same two update() calls; ESC `Publish` returned as before). Acceptable; the
"bit-identical" claim should read "dynamics identical". Optionally skip the logs when 0.
m2. No flush when the mixer stops calling updateOutputs (spec sec 2 asked for a Run() flush). Last commands
then stay in the ring and the previous command stays applied in gz. Quantisation is documented; flush
unneeded while the mixer runs continuously, but a disarm command can be held beyond D if calls stop.
m3. Start of run: for the first D ms no actuator command is published (gz holds its initial value, zero
velocity). Spec sec 7 says publish nothing, which matches; confirm gz applies no motion on zero before arming.
m4. print_status reads rings and counters without the lock (GZBridge.cpp ~1296); benign torn reads. Indexing
[0..2] matches `_MAX_IMU_SENSORS = 3` (GZBridge.hpp:154), ok.
m5. Parameters (module.yaml): unit ms, min 0, max 10, default 0, reboot_required true: all correct. Against
parameters.instructions.md the `long` text restates default and "0 bypasses entirely" (use the stock
"Set to 0 to disable."), and repeats the IMU sentence about timestamp_sample, which is flash cost on
constrained boards. ACT is read via param_get(param_find()) (GZMixingInterfaceESC.hpp:79) while IMU uses
ParamInt: inconsistent but works. SIM_GZ_ERPM_LAT neighbours: placement fine.
m6. Delay is only logged by PX4_INFO (first release, one line per IMU) and no uORB topic or ulog field; sec 5
option (1) is satisfied, but the first-release value `now - ts` hides any clock lag (M2). The run log must
capture the console, otherwise the delay is invisible. Per-sample age is recoverable from
sensor_accel/gyro `timestamp - timestamp_sample`.

## Verified OK (evidence)
- IMU time rule: the stored time is the original `timestamp` (clamped as in the undelayed path); update(o.timestamp_sample,..)
  for accel and gyro. PX4Accelerometer.cpp:143 sets timestamp_sample from the argument, :155 stamps
  `timestamp = hrt_absolute_time()` at release (same in PX4Gyroscope.cpp:142/154). Correct per spec sec 3.
- No sample lost: while-loop releases all due entries in order. Accel/gyro same entry, same delay. Groundtruth
  callbacks untouched. Noise and vibration are added before queuing (RNG order unchanged).
- Applied IMU delay at 800 Hz (1.25 ms) with `now >= ts + D`: D=1 -> 1.25, 2 -> 2.5, 3 -> 3.75, 4 -> 5.0,
  5 -> 5.0, 6 -> 6.25, 7 -> 7.5, 8 -> 8.75, 9 -> 10.0, 10 -> 10.0 ms (ceil to the period, assuming `now`
  equals the sample time at arrival). Steps are coarse, so G3 should use D at multiples of 1.25 ms where possible (5, 10).
- Actuator: due test `now >= t_in + D` (>=, no off-by-one); a new entry is never due with D>0, so the
  minimum applied delay is one call. Mixer at 800 Hz: 1.25 ms grid as above. At 400 Hz (2.5 ms):
  1..2 -> 2.5, 3..5 -> 5, 6..7 -> 7.5, 8..10 -> 10. Latest-wins is implemented (older due entries dropped
  and counted, logged once). Overflow: oldest dropped, counted, warned once. Ring 32: 10 ms needs 8 entries at 800 Hz,
  32 covers 3.2 kHz; IMU ring 32 the same. Both count overflow visibly.
- Lock: updateOutputs runs from Run() under `_node_mutex` (GZMixingInterfaceESC.cpp:194-199); the ring
  is touched only there. The IMU ring has its own mutex; publication inside the lock is fine. No lock-order
  coupling with `_node_mutex`.
- esc_status / eRPM: motorSpeedCallback and the eRPM latency model consume gz motor speed feedback
  (:202-257), not the commands, so they see the physically delayed motors. Consistent with "PX4 -> gz".
  The ERPM_LAT frames add to it.
- Clocking: only hrt_absolute_time() (lockstep sim time) and gz stamps; no wall clock, no rng. Delay is not applied twice
  (IMU and ACT are independent params, split D = act + imu is a campaign choice).

## Verdict
CONDITIONAL PASS: fix M1 before any G3 run (delay not constant at boot, data race); decide M2; the
rest are cosmetic. Default-0 dynamics unchanged.

## Orchestrator resolution (S102)
- M1 fixed: `_imu_delay_us` now set before `subscribeImu` (GZBridge.cpp init).
- M2 fixed: IMU release clock = newest sample gz header stamp, not hrt.
- MINOR no Run() flush: accepted (mixer rate = controller rate, quantisation logged). MINOR delay only in console: runner records dly_*_ms in run.json; per-sample IMU age recoverable from sensor_gyro timestamp - timestamp_sample. Param wording: stage 7 (G7).
- Rebuilt clean, make format clean; committed c6ba02609f. Runner flags --dly-act/--dly-imu added.
