# K106 second key: SIM_GZ_GPS_DLY (d52576b02a) review

## Code review vs s94 section 4
- (a) default 0: navSatCallback keeps `_failure_config.update()` then `process_gnss` + publish + return, same order as before; Run() block skipped. Bit-identical path: OK (read, not diffed at binary level; UNVERIFIED by flight).
- (b) timestamp_sample unchanged (GZBridge.cpp:1071 sets it = generation hrt time); release sets o.timestamp = now. OK.
- (c) release rule `now >= timestamp_sample + L`, head/n modular ring, insert at (head+n)%32: correct; overflow path pops head before insert, so n<32 on insert. Ring 32 vs 250 ms at model navsat 30 Hz (model.sdf:226) = 8 entries: OK. Overflow counter increments but warning only first.
- (d) one mutex covers ring + _failure_config + _gnss_stuck in delay mode (callback thread and Run()). In delay mode _failure_config.update() is only called under the mutex. _node_mutex not touched (not nested). Run() holds mutex while publishing: fine. MINOR: _gnss_stuck / _failure_config also used by other callbacks (line 954 VIO uses _failure_config.update() without this mutex) - pre-existing race.
- (e) early return only for instance>=count. gnss_truth (line ~1030) published before ring, undelayed. OK.
- (f) SEE BLOCKING below.

## BLOCKING (f): SENS_GNSS0_DELAY is bypassed when SIM_GZ_GPS_DLY > 0
- GZBridge.cpp:1071 sets timestamp_sample = generation time. src/modules/sensors/vehicle_gps_position/VehicleGPSPosition.cpp:222,579-588
  (resolveSampleTimestamp): if 0 < timestamp_sample < timestamp the driver value is kept and delay_us is NOT applied; only when
  timestamp_sample == timestamp is `timestamp - SENS_GNSS0_DELAY` used. EKF2.cpp:2653 uses vehicle_gnss.timestamp_sample as time_us.
- So with the hook active (timestamp_sample < timestamp) the EKF always sees the true measurement time: any SENS_GNSS0_DELAY value acts
  as "matched". The matched/mismatched test cannot be built from this hook as specified (s94 s4 premise "EKF compares with now - delay" is wrong
  for this path). With L=0 (bypass) the stock path applies SENS_GNSS0_DELAY, so the L=0 baseline is the only place the param acts.
- Proposed fix: for a mismatch experiment, publish timestamp_sample = timestamp (delivery time, or 0) in releaseDelayedGnss (GZBridge.cpp:~1138-1141)
  under an option (e.g. SIM_GZ_GPS_DLY sign or a second param) so SENS_GNSS0_DELAY then subtracts; matched = L, mismatched = other. Alternatively
  keep the hook as "perfectly compensated delay" and document that. Not changed.

## Flights (hover_long, quad5in, 800 Hz, seed 1, speed 4, indi_m3a, --gps-dly 250; M --gnss-delay 250, X --gnss-delay 0), both exit ok
- px4.log: "requested 250000 us (delay line active)"; first release "applied 266250 us for requested 250000 us" (both). No overflow lines.
- sensor_gnss in ulog is logged at ~1 Hz (n 110/111), so age stats are on ~110 samples: M median 256250 min 250000 max 257500; X median/min/max 252500 (all, 0 negative).
  Expected +0/+10000 us: OK (first-release 16 ms is the start-up transient, UNVERIFIED cause; later ages within 7.5 ms).
- EKF innovation over last 50 s of hover (fused fraction 1.0): pos horiz RMS M 0.0297 m, X 0.0313 m; median test_ratio M 1.29e-5, X 1.37e-5;
  vel horiz RMS M 0.0259, X 0.0265 m/s, test_ratio 3.7e-5 vs 3.6e-5. M lower by 5% (pos), within noise; expected sign nominally holds but no real separation,
  consistent with the BLOCKING finding AND with a stationary hover that cannot expose a delay. Truth-vs-estimate error NOT computed (UNVERIFIED).
- Data: indi_flight/results/gnss_delay_key_s106/{M,X}/ (analysis.txt, px4.log, flight.ulg), an.py, fly.sh.
