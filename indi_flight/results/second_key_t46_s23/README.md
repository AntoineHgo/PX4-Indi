# Second-key check of t46 metrics (session 23)

Log: `indi_flight/results/a15_s21/hover/flight.ulg` (PX4 SITL hover, pyulog).
Script: `indi_flight/bench/second_key_t46.py <flight.ulg> <out.json>`.
Raw output: `indi_flight/results/second_key_t46_s23/result.json`.
Scope: independent computation only; `bench/metrics.py`, its tests and `design/t46_*` were not read.

## Windows

vehicle_status nav_state timeline: 4 -> 17 (30.94 s) -> 4 (38.20 s) -> 14 (52.02 s) -> 18 (89.94 s) -> 14 (100.77 s, last 14 sample at 101.77 s).

- **spec** (task definition): first OFFBOARD sample + 5 s to last OFFBOARD sample - 5 s = [57.019 s, 96.770 s], 39.75 s. This spans a non-OFFBOARD interval (nav_state 18, 89.94-100.77 s) that contains a large transient (|dc/dt| peaks near 90.3 s; motor-derivative RMS about 0.11 per s in 90-97 s).
- **contiguous** (first contiguous OFFBOARD run only): [57.019 s, 84.930 s], 27.91 s. Run end = 89.93 s, minus 5 s.

## Results

| Metric | Spec window | Contiguous run | Reference | Contiguous vs ref |
|---|---|---|---|---|
| motor_rate_rms_per_s (timestamp_sample) | 0.061376 | 0.006793 | 0.006790 | +0.04 % AGREE |
| motor_rate_rms_per_s (timestamp) | 0.061339 | 0.006783 | - | - |
| zero-dt pairs, timestamp_sample / timestamp (whole log) | 0 / 856 | 0 / 856 | - | - |
| rate RMS roll (rad/s) | 1.1501e-3 | 7.807e-4 | 7.978e-4 | -2.1 % DISAGREE (marginal) |
| rate RMS pitch (rad/s) | 9.053e-4 | 8.625e-4 | 8.605e-4 | +0.2 % AGREE |
| rate RMS yaw (rad/s) | 3.267e-4 | 3.298e-4 | 3.297e-4 | +0.03 % AGREE |
| sim_ground_truth samples / max gap (ms) | 31794 / 5.0 | 22325 / 5.0 | - | - |
| sensor_gyro samples / max gap (ms) | 31794 / 5.0 | 22325 / 5.0 | - | - |

Motor-rate pairs: 31790 kept in spec, 22320 in contiguous (pairs with dt > 0, assigned to the later sample). Rate samples: 31788 / 22318 (none dropped for lack of a setpoint).

## Notes

- Definition: rate tracking uses `vehicle_angular_velocity.timestamp_sample` against the zero-order-held `vehicle_rates_setpoint` (latest setpoint with `timestamp` <= sample time).
- Explanation for the motor-rate gap: the spec window includes the nav_state 18 segment, which dominates the RMS (0.061 vs 0.0068). The reference matches the contiguous OFFBOARD run (0.006793 vs 0.006790). The reference therefore appears to stop at the first OFFBOARD exit, which is a different window from the literal spec.
- Roll: 2.1 % low against the reference, just over the 2 % bar. Pitch and yaw agree. In the spec window, a strict-before setpoint hold moved roll by -2.6 % (1.150e-3 -> 1.120e-3), so roll is sensitive to the hold convention. That variant was not run on the contiguous window, so the roll gap is not explained.
- Verdict: motor_rate_rms AGREE on the contiguous-run window; the spec window DISAGREE for the motor metric (explained above). Rate pitch and yaw AGREE; roll DISAGREE at 2.1 %.

## Orchestrator check (S23): same window as metrics.py
metrics.py window = [55.019, 85.019] s (logged OFFBOARD entry + 3 s, 30 s). Re-running this script's
`window_metrics` on exactly that window: motor_rate_rms 0.006788 /s (ref 0.006790, -0.03 %), rate rms
roll/pitch/yaw 7.9779e-4 / 8.6054e-4 / 3.2972e-4 rad/s (ref 7.978e-4 / 8.605e-4 / 3.297e-4, all < 0.01 %).
The 2.1 % roll difference above came from the different window, not the definition. VERDICT: AGREE.
Zero-dt pairs: 0 on timestamp_sample, 856 on timestamp. sim_ground_truth and sensor_gyro: 23996 samples, max gap 5.0 ms.
