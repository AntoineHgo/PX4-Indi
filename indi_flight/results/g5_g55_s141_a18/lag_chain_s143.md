# G5.5 o1 lag chain (S143, analysis only): o1_lemniscate_s1/flight.ulg, script bench/lag_chain.py

Method: LS fit of dc + sin/cos(k*phi(t)), k=1,2, phi from metrics.traj_phase, over the cruise window only
(t_rel 3.0-14.8 s of traj, abs 61.9-73.7 s; t0_us 58.891 s, traj ends 76.7 s: NOT 62-91 s). Delay = phase/(k w), vs analytic
(metrics.traj_pva). Large axis = earth x (k=1, 5 m); small = earth y (k=2 only, 2.5 m). Positive = lag. Truth = sim_ground_truth
(timestamp == timestamp_sample here: identical results). Truth accel = d(vx)/dt. Fit uses the 2 harmonics jointly.

Self-test (`lag_chain.py selftest`): analytic accel delayed 100 ms, amp 0.7, on the real timestamps of 4 topics
(44/89/267/800 Hz): recovered 100.07-100.19 ms, ratio 0.700 exactly. Bias <= 0.2 ms.

| stage | axis x / y | delay ms | amp ratio | logged rate |
|---|---|---|---|---|
| 0 traj_sp.position vs analytic | x / y | 2.6 / 2.7 | 1.00 / 1.00 | 44 Hz (dt 11-30 ms) |
| 1 traj_sp.acceleration | x / y | 2.6 / 2.7 | 1.00 / 1.00 | 44 Hz |
| 2 a_c = local_pos_sp.accel (indi_pos_status a_c identical) | x / y | 97 / 129 | 1.16 / 1.01 | 89 Hz |
| 3 att_sp tilt accel, raw (-g zb_xy/zb_z of q_d) | x / y | 707 / 293 | 1.33 / 1.05 | 89 Hz |
| 3d same, drag-corrected | x / y | 118 / 134 | 1.20 / 1.04 | 89 Hz |
| 4 vehicle_attitude tilt accel, raw | x / y | 781 / 331 | 1.25 / 0.95 | 267 Hz |
| 4d same, drag-corrected | x / y | 146 / 155 | 1.08 / 0.92 | 267 Hz |
| 5 truth accel d(vx,vy)/dt | x / y | 137 / 156 | 1.07 / 0.93 | 800 Hz |
| 5p truth position vs analytic | x / y | 125 / 158 | 1.07 / 0.94 | 800 Hz |
| 6 omega_ff roll(large)/pitch(small) vs analytic jerk | x@w / y@2w | 343 / 82 | 0.84 / 0.91 of jerk/g | 89 Hz |
| 2c indi a_f (measured accel) | x / y | 138 / 159 | 1.07 / 0.93 | 89 Hz |
Truth position vs trajectory_setpoint.position = 125-3 = 122 ms (x), 155 ms (y) (sp.position has the same 2.6 ms vs analytic).
Yaw median 91 deg (roll = earth x = large axis, pitch = earth y = small).

Drag fit (truth, window): a_truth = 1.015 * tilt_acc - 0.514 * v, residual rms 0.14 of 3.84 m/s^2. Linear drag k ~ 0.51 /s
(gz rotorDragCoefficient 7.5e-5 in quad5in model.sdf: the cause, plausible; the fit does not prove it).

Interpretation
1. The reference path is clean: setpoint position and acceleration reach the controller with ~3 ms delay and unit gain; no lag in stage 0-1.
2. The attitude/thrust stage and the plant are not the bottleneck: att_sp -> truth accel adds only ~20 ms (x) and ~20 ms (y)
   once drag is removed (118->137, 134->156); estimator attitude vs truth attitude identical (<2 ms).
3. The 125-158 ms is made at stage 2: a_c lags the reference by 97 / 129 ms with ratio 1.16 on x, i.e. the stock PD feedback
   adds a quadrature term to an unlagged a_ff. That term is feeding the linear drag (-0.51 v, v lags a by 90 deg): the raw tilt
   needed lags a_ref by atan(k/w)/w = 640 ms (x) / 170 ms (y), matching the raw att_sp lag 707 / 293 ms.
4. The ff carries no drag model, so the position PD must build k*v from position error: steady phase-lag error 0.5-0.6 m RMS.
   Candidate fix: a_ff += 0.51 * v_ref (feedforward of drag, from the analytic/setpoint velocity), then re-check.
5. omega_ff: 343 ms behind the analytic jerk on the large axis (roll, amp 0.26 rad/s) and 82 ms on the small (pitch, 1.14 rad/s);
   it is derived from the unlagged a_ff, so a large-axis lag of 343 ms is unexplained (low signal, 0.3 rad/s) - not resolved.

Unverified: (a) drag value comes from a 2-parameter LS fit on this one log, c fitted 1.015 (tilt formula ok); drag-corrected
stages 3d/4d use truth velocity, error ~10-20 ms on the delay; (b) cruise window is 1.6 laps, not integer; fit by
joint harmonics so no leakage bias seen in the self-test; (c) omega_ff axis mapping assumes yaw ~91 deg (checked) and the x@w / y@2w
amplitude pick; (d) the 6b derivative of att_sp tilt was dropped from the table (contaminated by drag, not comparable);
(e) a_c includes both ff and feedback, so stage 2 delay is closed-loop, not a filter delay. Single seed, no flight rerun.
