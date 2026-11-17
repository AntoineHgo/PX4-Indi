# T161 second key: s72 thrust-gap flights (ULog, independent)

| Metric | gap085_indi_htoff | loss08_indi |
|---|---|---|
| dz_truth (m, GT - SP, NED) | +0.0201 | -0.0527 |
| dz_est (m, est - SP, NED) | -0.0001 | -0.0402 |
| est_err (m, est - GT) | -0.0202 | +0.0126 |
| mean a_f[2] (m/s^2) | +0.0005 | -0.0031 |
| mean a_c[2] (m/s^2) | +0.0001 | +0.1580 |
| final blend | 0.0240 | 0.0084 |

Logged rate in window (Hz):

| Topic | gap085_indi_htoff | loss08_indi |
|---|---|---|
| vehicle_local_position_groundtruth | 708.2 | 705.5 |
| vehicle_local_position | 88.9 | 88.9 |
| vehicle_local_position_setpoint | 88.9 | 88.9 |
| indi_pos_status | 88.9 | 88.9 |

## Method

- Hold window: last 10 s before landing start. Landing start = first position_setpoint_triplet.current.type == LAND after hold start (cross-checked against vehicle_status nav_state == AUTO_LAND, see the stdout diagnostics).
- Hold start (run.json "hold") is used only to search for the landing start. The window does not use run.json times. Clock check: first actuator_armed differs from run.json t_arm_us by ~0.72 s, so run.json times may be offset from ULog time (the fault time at motor_fault.event_us is affected too).
- Setpoint, truth and estimate z are linearly interpolated onto a common 100 Hz grid over the window; means are over that grid.
- dz_truth = GT z - setpoint z; dz_est = estimate z - setpoint z; est_err = estimate z - GT z (NED, positive = below).
- indi_pos_status a_f[2], a_c[2] are sample means over the window; blend is the last sample in it.
- Truth topic: vehicle_local_position_groundtruth (present in both logs). Setpoint topic: vehicle_local_position_setpoint.
