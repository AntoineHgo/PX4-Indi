# S70 second-key check: altitude error and thrust (ground truth, from raw ulog)

| run | dz mean [up+10, up+20] s (m) | dz mean, last 10 s of hold (m) | mean abs thrust setpoint, 5 s before up | mean abs thrust setpoint, last 10 s of hold |
|---|---|---|---|---|
| gap085_indi | 0.336 | 0.304 | 0.1367 | 0.1608 |
| gap085_stock | -0.007 | -0.008 | 0.1366 | 0.1608 |
| gap085_stock_htoff_noi | 0.394 | 0.371 | 0.1366 | 0.1609 |
| loss08_indi | 0.196 | 0.188 | 0.1367 | 0.1452 |

Method:
1. dz = truth z (`vehicle_local_position_groundtruth`, NED) minus `hold_pos_ned[2]` from run.json; positive = below hold.
2. t_up and t_hold come from the run.json `events` entries "up" (t_us 70.85 to 70.98 s) and "hold" (+5 s, 40 s long); the hold last 10 s is [t_hold+30, t_hold+40].
3. Time base: run.json times and ulog timestamps are not the same base. The offset is constant per run and was fixed from the offboard anchor (vehicle_status nav_state 14 in ulog vs run.json t_offboard_us), checked against the arm anchor (arming_state 2 vs t_arm_us); the two agree within 0.01 s. Offsets (ulog minus run.json): -0.96, -0.86, -0.83, -0.79 s for indi, stock, stock_htoff_noi, loss08_indi. ulog_time = run.json_time + offset.
4. Thrust: per-sample norm of `vehicle_thrust_setpoint` xyz, then the mean over the window [t_up-5, t_up] and over the hold last 10 s.
5. Sanity: stock hold-last-10 truth z mean is -5.024 m vs setpoint -5.016 m; the INDI run sits ~0.3 m below its setpoint (-4.64 vs -4.94 m) in the same window, consistent with dz.

Caveats: the motor-fault onset is not visible in `actuator_outputs` (out0/mean(out1..3) = 1.000 before and after), so alignment relies on the arm/offboard anchors, not the fault edge. Windows are 10 s, so the sub-0.02 s anchor uncertainty does not affect the means.
