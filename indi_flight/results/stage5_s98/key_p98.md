# S98 independent key (raw ULG only)

Script: `indi_flight/results/stage5_s98/key_p98.py` (run in Docker, pyulog).
Ground truth: `vehicle_local_position_groundtruth` (present in all three logs). z is NED as logged (positive = down), so the ~+2.3 m last-10 s values mean 2.3 m below the hold reference.

Fault time: `run.json` -> `motor_fault.event_us` (segment "up", thrust_scale 0.85, all 4 motors, SIM_GZ_EC_MAX 2700 -> 2489). Corroborated by the `sends.csv` SIM_GZ_EC_MAX* rows at the same intended sim time. The ULG timeline is assumed to equal sim time; supported by the logs starting ~21 s, matching the sends.csv sim_time_after of ~21.9 s at the parameter stage.

| flight | fault t [s] | ref z [m] | peak abs(z-ref), fault..fault+20 [m] | peak abs(z-ref), fault..end [m] | mean(z-ref), t+10..t+20 [m] | mean(z-ref), last 10 s before landing [m] | landing t [s] | RMS body rate t+10..t+20 [rad/s] |
|---|---|---|---|---|---|---|---|---|
| A_gap085 | 70.967 | -5.008 | 0.099 | 5.013 | +0.011 | +2.348 | 128.74 | 0.0061 |
| B_altctl | 70.906 | -5.020 | 0.167 | 5.026 | -0.001 | +2.327 | 128.61 | 0.0014 |
| C_altctl_at | 70.972 | -4.954 | 0.133 | 4.959 | -0.002 | +2.285 | 128.65 | 0.0013 |

Notes:
- "Peak to end" is dominated by the landing descent (z goes to ground), so the fault+20 s column is the meaningful fault-response number.
- End point = min(first `vehicle_land_detected.landed == 1` after the fault, first `vehicle_status.arming_state == 1` after the fault); the column is that end time.
