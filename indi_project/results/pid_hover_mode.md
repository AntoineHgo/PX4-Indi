# Log facts (haiku scan, session 49), not a conclusion

Scan of pid_tuned hover flights (gz_x500 SITL). "High" = roll-loop effort doubled
(hover_cause seeds 1-3, s2_seen_v2 seeds 3-4). "Low" = v3_hover_effort seeds 2-5,
s2_seen_v2 seeds 1, 2, 5. Group membership is taken from the task brief, not re-verified.

Runs:

| label | ulog |
|---|---|
| high_hc_s1 | indi_project/results/hover_cause/runs/hover/pid_tuned/seed1/flight.ulg |
| high_hc_s2 | indi_project/results/hover_cause/runs/hover/pid_tuned/seed2/flight.ulg |
| high_hc_s3 | indi_project/results/hover_cause/runs/hover/pid_tuned/seed3/flight.ulg |
| high_s2_s3 | indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed3/flight.ulg |
| high_s2_s4 | indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed4/flight.ulg |
| low_v3_s2 | indi_project/results/v3_hover_effort/runs/hover/pid_tuned/seed2/flight.ulg |
| low_v3_s3 | indi_project/results/v3_hover_effort/runs/hover/pid_tuned/seed3/flight.ulg |
| low_v3_s4 | indi_project/results/v3_hover_effort/runs/hover/pid_tuned/seed4/flight.ulg |
| low_v3_s5 | indi_project/results/v3_hover_effort/runs/hover/pid_tuned/seed5/flight.ulg |
| low_s2_s1 | indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed1/flight.ulg |
| low_s2_s2 | indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed2/flight.ulg |
| low_s2_s5 | indi_project/results/s2_seen_v2/runs/hover/pid_tuned/seed5/flight.ulg |




## Per-log rows

VAV = vehicle_angular_velocity, RCS = rate_ctrl_status, RSP = vehicle_rates_setpoint, dt = sample interval over the window.

| label | group | window source | VAV dt mean ms | VAV dt std ms | VAV dt p99 ms | VAV n>2x median | VAV timestamp-timestamp_sample ms | RCS dt mean ms | RCS dt p99 ms | RCS n>2x median | RSP dt mean ms | RSP dt p99 ms | RSP n>2x median | band 2-4 Hz whole (rad/s RMS) | band seg1 0-10 s | band seg2 10-20 s | band seg3 20-30 s | rollspeed_integ mean | rollspeed_integ std | torque x std | boot UTC | wall_time_s | sys / ver / branch / hw |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| high_hc_s1 | high | run.json (run.json=34.08-64.08, metrics.json=34.08-64.08); used 34.08-64.08 s | 3.5 | 0.5083 | 4 | 0 | 0.0001167 | 20 | 21 | 0 | 4.002 | 4 | 2 | 0.006327 | 0.006305 | 0.006327 | 0.006387 | -6.568e-06 | 0.0001212 | 0.0006377 | 2026-11-15 00:30:52 UTC | 84.1 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| high_hc_s2 | high | run.json (run.json=35.33-65.33, metrics.json=35.33-65.33); used 35.33-65.33 s | 3.5 | 0.5014 | 4 | 0 | 0.0001167 | 20 | 21 | 0 | 4.001 | 4 | 2 | 0.004969 | 0.005025 | 0.005189 | 0.004772 | -3.302e-06 | 0.0001176 | 0.0005172 | 2026-11-15 00:32:19 UTC | 85.6 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| high_hc_s3 | high | run.json (run.json=34.95-64.95, metrics.json=34.95-64.95); used 34.95-64.95 s | 3.5 | 0.5037 | 4 | 0 | 0 | 20 | 21 | 0 | 4 | 4 | 0 | 0.005486 | 0.005515 | 0.005353 | 0.005615 | -2.613e-06 | 0.0001141 | 0.0005607 | 2026-11-15 00:33:45 UTC | 85 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| high_s2_s3 | high | run.json (run.json=35.91-65.92, metrics.json=35.91-65.92); used 35.91-65.92 s | 3.5 | 0.5165 | 4 | 0 | 0.0002333 | 20 | 21 | 0 | 4.005 | 4 | 6 | 0.007507 | 0.007462 | 0.007527 | 0.007424 | 9.05e-08 | 0.0001372 | 0.0007454 | 2026-11-14 21:47:46 UTC | 86.6 | PX4 d1b5be2d22 feat/indi-control hw=PX4_SITL |
| high_s2_s4 | high | run.json (run.json=36.09-66.09, metrics.json=36.09-66.09); used 36.09-66.09 s | 3.5 | 0.5138 | 4 | 1 | 0.0005834 | 20 | 21 | 0 | 4.003 | 4 | 3 | 0.007188 | 0.007171 | 0.007183 | 0.007125 | -8.429e-06 | 0.0001397 | 0.0007185 | 2026-11-14 21:55:49 UTC | 86.9 | PX4 d1b5be2d22 feat/indi-control hw=PX4_SITL |
| low_v3_s2 | low | run.json (run.json=31.00-61.00, metrics.json=31.00-61.00); used 31.00-61.00 s | 3.5 | 0.5009 | 4 | 0 | 0 | 20 | 21 | 0 | 4 | 4 | 0 | 0.001232 | 0.001379 | 0.001102 | 0.001424 | -9.299e-07 | 7.931e-05 | 0.0001909 | 2026-11-14 23:47:57 UTC | 81.1 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| low_v3_s3 | low | run.json (run.json=33.29-63.29, metrics.json=33.29-63.29); used 33.29-63.29 s | 3.5 | 0.512 | 4 | 0 | 0.0007 | 20 | 21 | 0 | 4.004 | 4 | 3 | 0.002264 | 0.00233 | 0.002312 | 0.002278 | 2.406e-06 | 0.000103 | 0.0002745 | 2026-11-14 23:49:24 UTC | 84.7 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| low_v3_s4 | low | run.json (run.json=35.66-65.66, metrics.json=35.66-65.66); used 35.66-65.66 s | 3.5 | 0.507 | 4 | 0 | 0.00035 | 20 | 21 | 0 | 4.001 | 4 | 0 | 0.001373 | 0.001459 | 0.001373 | 0.001235 | -3.187e-06 | 7.234e-05 | 0.0001959 | 2026-11-14 23:50:51 UTC | 85.8 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| low_v3_s5 | low | run.json (run.json=34.28-64.28, metrics.json=34.28-64.28); used 34.28-64.28 s | 3.5 | 0.5063 | 4 | 0 | 0.0002333 | 20 | 21 | 0 | 4.003 | 4 | 2 | 0.002107 | 0.002042 | 0.002035 | 0.00223 | -1.118e-06 | 8.381e-05 | 0.0002554 | 2026-11-14 23:52:19 UTC | 85.3 | PX4 f64586465a feat/indi-control hw=PX4_SITL |
| low_s2_s1 | low | run.json (run.json=34.93-64.93, metrics.json=34.93-64.93); used 34.93-64.93 s | 3.5 | 0.5033 | 4 | 0 | 0.0002333 | 20 | 21 | 0 | 4.001 | 4 | 1 | 0.002254 | 0.002335 | 0.002218 | 0.002202 | 7.66e-06 | 8.383e-05 | 0.0002634 | 2026-11-14 21:31:41 UTC | 85.1 | PX4 d1b5be2d22 feat/indi-control hw=PX4_SITL |
| low_s2_s2 | low | run.json (run.json=31.56-61.56, metrics.json=31.56-61.56); used 31.56-61.56 s | 3.5 | 0.5074 | 4 | 0 | 0 | 20 | 21 | 0 | 4.002 | 4 | 0 | 0.002768 | 0.00255 | 0.002647 | 0.003133 | -8.216e-06 | 7.908e-05 | 0.0003106 | 2026-11-14 21:39:29 UTC | 81.8 | PX4 d1b5be2d22 feat/indi-control hw=PX4_SITL |
| low_s2_s5 | low | run.json (run.json=35.74-65.74, metrics.json=35.74-65.74); used 35.74-65.74 s | 3.5 | 0.5067 | 4 | 0 | 0.0001167 | 20 | 21 | 0 | 4.002 | 4 | 3 | 0.0005572 | 0.0008016 | 0.0004113 | 0.0004201 | -2.061e-06 | 6.673e-05 | 0.0001453 | 2026-11-14 22:03:58 UTC | 86.3 | PX4 d1b5be2d22 feat/indi-control hw=PX4_SITL |

## High vs low (mean over runs [min..max])

| metric | high | low | high/low (means) |
|---|---|---|---|
| VAV dt mean ms | 3.5 [3.5..3.5] | 3.5 [3.5..3.5] | 1 |
| VAV dt std ms | 0.5088 [0.5014..0.5165] | 0.5062 [0.5009..0.512] | 1.005 |
| VAV dt p99 ms | 4 [4..4] | 4 [4..4] | 1 |
| VAV n>2x median | 0.2 [0..1] | 0 [0..0] | nan |
| VAV timestamp-timestamp_sample ms | 0.00021 [0..0.0005834] | 0.0002333 [0..0.0007] | 0.9 |
| RCS dt mean ms | 20 [20..20] | 20 [20..20] | 1 |
| RCS dt p99 ms | 21 [21..21] | 21 [21..21] | 1 |
| RCS n>2x median | 0 [0..0] | 0 [0..0] | nan |
| RSP dt mean ms | 4.002 [4..4.005] | 4.002 [4..4.004] | 1 |
| RSP dt p99 ms | 4 [4..4] | 4 [4..4] | 1 |
| RSP n>2x median | 2.6 [0..6] | 1.286 [0..3] | 2.022 |
| band 2-4 Hz whole (rad/s RMS) | 0.006295 [0.004969..0.007507] | 0.001794 [0.0005572..0.002768] | 3.51 |
| band seg1 0-10 s | 0.006295 [0.005025..0.007462] | 0.001842 [0.0008016..0.00255] | 3.417 |
| band seg2 10-20 s | 0.006316 [0.005189..0.007527] | 0.001728 [0.0004113..0.002647] | 3.654 |
| band seg3 20-30 s | 0.006265 [0.004772..0.007424] | 0.001846 [0.0004201..0.003133] | 3.394 |
| rollspeed_integ mean | -4.164e-06 [-8.429e-06..9.05e-08] | -7.78e-07 [-8.216e-06..7.66e-06] | 5.353 |
| rollspeed_integ std | 0.000126 [0.0001141..0.0001397] | 8.115e-05 [6.673e-05..0.000103] | 1.552 |
| torque x std | 0.0006359 [0.0005172..0.0007454] | 0.0002337 [0.0001453..0.0003106] | 2.721 |

## Named parameters per run (the rest of the ULog parameters are covered by the difference section)

| label | MC_ROLLRATE_P | MC_ROLLRATE_I | MC_ROLLRATE_D | MC_ROLLRATE_K | MC_ROLL_P | IMU_GYRO_CUTOFF | IMU_DGYRO_CUTOFF | MC_INDI_EN |
|---|---|---|---|---|---|---|---|---|
| high_hc_s1 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| high_hc_s2 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| high_hc_s3 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| high_s2_s3 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| high_s2_s4 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_v3_s2 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_v3_s3 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_v3_s4 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_v3_s5 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_s2_s1 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_s2_s2 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |
| low_s2_s5 | 0.1473 | 0.2925 | 0.002356 | 1 | 5.122 | 40 | 20 | 0 |

## Parameter differences, high vs low (CAL_* and *_ID ignored; 0 keys)

| param | high values | low values |
|---|---|---|


Parameters varying within a group (not high-vs-low): none

## Orchestrator reading (session 49), not yet a conclusion

What the scan rules out: parameters (identical in all 12 logs), build (both ver_sw hashes appear in both groups), and
PX4-side loop timing in sim time (gyro interval and sample-to-publish lag equal). The mode is present from the first
10 s of the window, not appearing mid-flight, and the PID terms only follow it (torque std 2.7x, integrator std 1.55x).
Open hypotheses, in the order to test them:
1. Something not in lockstep with the sim clock that is affected by host load. Seen-set seeds 3-4 flew under the host
   overload found in s44, and hover_cause flew as a separate batch on 11-15 00:30. Candidates: the runner's offboard/hold
   setpoint stream (wall-clock rate), and any project gz plugin (eRPM, vibration) that uses wall time. Check the runner's
   hold path and the plugins' clocks in the code, and the inter-arrival times of trajectory_setpoint/offboard messages in
   sim time (high vs low).
2. Sim noise realisation (vibration/eRPM seed) exciting a lightly damped PID mode: check whether the same seed flew low in
   one batch and high in another (hover_cause seed 1 vs seen seed 1 suggests yes, which would weigh against this one).
3. Only if the logs cannot decide: fly pid_tuned hover seeds 1-2 on an idle host and again under a deliberate CPU load
   (O-12 watchdog, side by side).
