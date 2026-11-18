# K106: second key of hook B (SIM_GZ_GPS_DLY) and the S106 timestamp fix

Review: `design/gnss_delay_key_s106.md` (sonnet K106). One BLOCKING: with the hook keeping the true
`timestamp_sample` (< `timestamp`), `VehicleGPSPosition::resolveSampleTimestamp`
(`src/modules/sensors/vehicle_gps_position/VehicleGPSPosition.cpp:579-588`) keeps it and ignores
`SENS_GNSS0_DELAY`: every compensation value acted as matched. Confirmed by the orchestrator in the source.
The S94 spec (section 4, "timestamp_sample UNCHANGED") was wrong on this point.

Fix (S106, orchestrator): at release the fix is stamped `timestamp_sample = timestamp` (a receiver that does not
report its latency, the same convention as the undelayed gz path, D-s8-gnss-delay). True age kept as min/max in
`gz_bridge status` (`age0`). Matched compensation = `--gnss-delay` equal to `--gps-dly`.

Flights (hover_long, indi_m3a, quad5in, 800 Hz, seed 1, speed 4, `fly.sh`; M2 by the same command):
| run | firmware | --gps-dly | --gnss-delay | exit | sensor_gnss ts - ts_sample |
|---|---|---|---|---|---|
| M | d52576b02a (pre-fix) | 250 | 250 | ok | median 256250, max 257500 us |
| X | d52576b02a (pre-fix) | 250 | 0 | ok | 252500 us |
| M2 | fix | 250 | 250 | ok | 0 (max 0) |

`lagcheck.py <ulog> <SENS_GNSS0_DELAY ms>`: true generation time of each 1 Hz-logged fix found by matching its
altitude to ground truth (`vehicle_local_position_groundtruth` ref_alt - z) while |vz| > 0.3 m/s (11 fixes per
flight, about +-70 ms per fix from GNSS altitude noise). EKF time error derived from the resolveSampleTimestamp rule
(`vehicle_gps_position` is not logged).
- M (pre-fix): delivery age median 231.6 ms, EKF time error median -25.4 ms (true sample time kept).
- M2 (fix, matched 250): delivery age median 254.3 ms, EKF time error median +4.3 ms; with 0 it would be +254.3 ms.
- Innovation M vs X (pre-fix, both effectively matched): pos RMS 0.0297 vs 0.0313 m, not separable (expected).

Bounds and open points: first release applied 266250 us for 250000 (16.25 ms over, both firmwares); later ages
at 1 Hz logging are +0..+7.5 ms. Bound accepted for G3 (<= 16.25 ms on 80-250 ms, logged per run), not chased.
UNVERIFIED: an estimator-level matched-vs-mismatched separation needs a moving scenario (not flown); the fix has
no second key yet (K107); `sensor_gnss` is logged at 1 Hz only.
