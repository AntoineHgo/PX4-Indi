# A-48 cause search (S147): tilt spike at the thrust-return edge

Time base: events_s in g510.json are absolute log-clock seconds; ulg-relative = event - ulg start_timestamp
(s2: rec 63.371 - 22.4225 = 40.9485; pid_s1: 64.018 - 22.16 = 41.858). Only s2 analysed in depth, pid_s1 step 1 only.

## Step 1 result: NOT commanded. Plant disturbance at the edge, inner loop amplifies it
s2, t = seconds after the rec event (truth = vehicle_attitude_groundtruth tilt, sp = tilt of q_d, thr = |thrust_body|):
- -1.0..+0.12: truth 4.8 -> 1.1 deg, sp 4.4 -> 0.9 deg, thr 0.47-0.49. Nothing unusual before the edge.
- +0.14: truth 1.5, sp 1.0. Rate sp (rates_sp_applied) 0.00 all window. First deviation is a roll/pitch
  angular acceleration step: angular_accel_filtered -54/+51 rad/s2 at +0.14, -98/+94 at +0.16 (antisymmetric roll/pitch).
- +0.20 truth 22.2 / sp 0.8; +0.24 truth 44.8 / sp 1.6; +0.30 truth 64.7 (peak) / sp 15.8; +0.40 truth 47.0 / sp 26.5.
  Truth leads the setpoint by ~0.1 s, so the setpoint cannot be the cause. sp rises (to 27 deg at +0.44) only AFTER the
  truth has tilted (position loop reacting to the displacement). Estimator tilt == truth (64.7 at +0.30).
- Peak body rates (vehicle_angular_velocity) -7.35 / +6.90 rad/s at +0.24 (about 420 deg/s). 60 deg = about 7 rad/s * 0.15 s.
- Motors (actuator_motors, all 0.49 at +0.12): motor0 0.49 -> 0.10 at +0.22, motor1 0.52-0.54, motors 2/3 0.46-0.5, then
  motors 2/3 up to 0.7 and motor0/1 down to 0.2 (a large differential, the rate loop fighting a roll/pitch kick).
- Rate loop at +0.14..+0.28: nu_r 21 -> 224 rad/s2 (peak +0.24), torque_sp max 0.15, torque_increment 0.18; measured
  torque_filtered only 0.056, so measured acceleration/torque lags the demand. Tilt rate reverses at +0.26 (overshoot).
pid_s1 (same scenario, same edge event at +0): motors 0.47 all at 0, at +0.16 [0.23 0.64 0.50 0.50], +0.20 [0.07 0.69 .53 .53]
  (same asymmetric signature: motor0 down, motor1 up). truth +0.2 18.5, +0.3 24.5 (peak ~33 in README), sp +0.3 16.2.
  Same disturbance, PID gives about half the tilt, INDI 65 deg.

## Mechanism (what is verified, what is hypothesis)
Verified: the edge is applied by run_scenario.py fault_apply (indi_flight/bench/run_scenario.py:533-541) as EIGHT separate
MAVLink param sets SIM_GZ_EC_MIN1/MAX1..MIN4/MAX4 (sends.csv:457-464, wall 27.630-27.743 s, ~14 ms apart) raising each
motor ceiling 1413 -> 2700 (thrust ~ x3.6). Motors do not step together. Both PID and INDI show an asymmetric roll/pitch
kick from ~0.12 s after the event with a setpoint that stays at ~1 deg, i.e. the root disturbance is a SIM/test artifact
(sequential per-motor limit change + a 3.6x step in per-command effectiveness), not an outer-loop windup.
Hypothesis (not verified): INDI is worse because rate loop G1 is a constant (MC_INDI_G1_R 1757, MC_INDI_W_MAX 2700;
indi_rate_control.cpp:459 dt_cmd = (nu - (1+c) a_f)/G1) while real effectiveness per command jumps about x1.9-3.6 at the edge,
so the incremental loop gain is multiplied by that factor (with lead c=0.66, K=20) and overshoots (tilt-rate reversal at +0.26).
Not examined: whether the stages after sat leave outer-loop state (a_c) windup; indi_pos_status a_c is not what drives
the tilt in the first 0.3 s (q_d tilt <= 16 deg while truth is at 65 deg). Step 2 (a_c, gap-remover/integrators) therefore not run.

## Decision relevance for G5.10
No evidence that the outer-loop saturation handling needs redesign: the spike is not commanded by the outer loop.
Fix candidates (none edited):
1. Test side: apply the reset atomically (single param-batch with sim paused, or ramp the ceiling over ~0.3 s) in fault_apply, re-fly s2/s3.
   If the spike disappears, A-48 is a scenario artifact.
2. If a real thrust-regain step must be survived: scale rate-loop effectiveness with available thrust / measured rotor speed
   (G1 * (w_max_now/w_max_ref)^2 using erpm, McIndiRateControl.cpp:139 area), or lower the increment gain on a step in
   thrust-per-command.
Unverified: s1/s3 not plotted (README gives 48.9/65.1 tilt, same +0.3 s timing); delay between the param sets and the 0.12 s
onset (sim lockstep timing); sim-side per-motor ceilings actually used. Needs one flight with an atomic/ramped edge.
