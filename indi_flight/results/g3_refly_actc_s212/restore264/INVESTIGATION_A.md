# Investigation A: draw 264 joint (sat 0.351 + weak motor 3 at 0.709), why PID survives and INDI loses control

## Summary (5 lines)

1. Neither stack saturates in the LOC window: allocator unallocated torque/thrust = 0 and no saturation flags for INDI until t+1.4 s (tilt already > 60 deg at t+1.1 s); PID never saturates. Saturation priority and yaw are not the mechanism.
2. The weak motor needs a trim torque command of about -0.08 roll/pitch (growing with collective) only to reach zero net torque. INDI has no fast integral action for this trim because its feedback torque is the measured torque, which is about 0 in this window.
3. INDI command = t_meas(about 0) + 1 s blend(-0.04 at t+1.1 s) + increment K*e/G1, which is at most -0.05 for a 250 deg/s error (K=20, G1=1757). So tau_sp stays at -0.08, about the trim. Net torque stays about 0, p,q stay at +28/+20 deg/s against a -220 deg/s setpoint, and tilt diverges.
4. PID survives because its integrator (-0.04 at t+1.0 s, -0.07 at t+2 s) carries the trim and its P gain (0.03 per rad/s) is 2.6x INDI's effective 0.0114 per rad/s. It also commands less thrust (-0.48 vs -0.59 at t+1.0 s), so the trim it needs is smaller.
5. Most likely cause: the measured-torque blend in indi_rate_control.cpp:330-357 (MC_INDI_ACT_BLD 1.0 s) is too slow to give integral action against a weak-motor offset that grows with collective, and the increment is small (nu/G1). Falsify by re-flying joint with ACT_BLD 0.1 s or with measured feedback off (not done here).

## Data and method

- Logs: indi_joint/run_024/flight.ulg (fault 58.23 s) and pid_joint/run_024/flight.ulg (fault 58.89 s). Script: inv_A/compare.py (`python3 inv_A/compare.py <ulg> <t_fault> <t0> <t1> <dt> [-i]`), sampled every 0.1 s (zero-order hold). t below is relative to the fault.
- Fault (g3_scenario_overrides.json): thrust_scale 0.351 on all motors and 0.709 on motor 3. The log is consistent with the sim scaling the motor's thrust command, which the measured rpm shows. Before the fault u=0.14 gives 9528 rpm, and (rpm/omega_max)^2 = 0.137. After the fault, rpm3/rpm0 tracks 0.709*u3/u0 (1.009 vs 1.008 at 59.3 s). So actuator_torque_measured, from rpm with nominal effectiveness (IndiMeasuredTorque.cpp:53, :182-184), reports the true net torque. The hypothesis that the module assumes nominal effectiveness for a weak motor does not hold in this sim (CT match to the gz model is unverified).

## Q1. Why PID survives (pid_joint, fault 58.89 s)

| t | tilt | p,q meas / sp [deg/s] | tau_sp r,p,y | u0..u3 | thrust sp | rate integ r,p |
|---|---|---|---|---|---|---|
| +0.2 | 21 | -48,27 / -31,24 | 0,0,.01 | .20 .20 .17 .18 | -0.19 | -.005 .010 |
| +0.6 | 17 | -22,-27 / -66,-63 | -.05,-.04,-.03 | .33 .32 .33 .45 | -0.36 | -.023 -.020 |
| +1.0 | 18 | 5,31 / -37,-17 | -.06,-.06,-.04 | .44 .44 .43 .61 | -0.48 | -.040 -.038 |
| +1.6 | 25 | 36,45 / -2,-4 | -.08,-.09,-.05 | .54 .55 .53 .77 | -0.60 | -.061 -.062 |
| +2.0 | 29 | 17,-20 / 3,-37 | -.08,-.08,-.06 | .52 .53 .53 .76 | -0.58 | -.072 -.076 |

- No saturation: unallocated torque/thrust 0, flags 0, max u3 0.78. Desaturation, airmode and yaw priority are not involved.
- Mechanism: the rate integrator (MC_ROLLRATE_I 0.06, limit 0.3) builds the weak-motor trim steadily (-0.04 at +1.0 s, -0.07 at +2.0 s). The P term (MC_ROLLRATE_P 0.03 per rad/s) responds to rate error 2.6x more strongly than INDI's proportional path. Rate setpoints stay well inside the 220 deg/s limit, and tilt peaks at 30 deg at +1.9 s, then recovers (38 deg at +7.5 s per README).
- The PID position loop raises thrust more slowly (-0.48 at +1.0 s vs INDI -0.59). The weak-motor trim scales with u3, so PID needs less trim at the same time.
- PID's attitude setpoint is already tilted 17-28 deg in this window, versus 2-16 deg for INDI. Whether it points the same way as the vehicle tilt was not checked (unverified).

## Q2. What INDI does differently (indi_joint, fault 58.23 s)

| t | tilt | p,q meas / sp [deg/s] | tau_sp r,p,y | incr r,p | t_fb r,p | meas tau | u0..u3 | thrust sp |
|---|---|---|---|---|---|---|---|---|
| +0.3 | 14 | 22,77 / -16,51 | -.02,-.01,0 | -.02 -.03 | .00 .01 | .01 | .27 .27 .25 .29 | -0.27 |
| +0.5 | 15 | 95,133 / -112,-110 | -.05,-.06,-.03 | -.05 -.06 | -.01 .00 | .00 | .36 .37 .34 .50 | -0.39 |
| +0.7 | 41 | 62,68 / -220,-220 | -.07,-.07,-.05 | -.05 -.06 | -.02 -.02 | .00 | .43 .43 .42 .63 | -0.48 |
| +1.1 | 60 | 28,20 / -220,-220 | -.08,-.08,-.06 | -.05 -.05 | -.04 -.03 | .00 | .58 .57 .58 .82 | -0.64 |
| +1.4 | 73 | 47,35 / -220,-220 | -.10,-.10,-.07 | -.05 -.05 | -.05 -.05 | .00 | .71 .71 .71 1.00 | -0.83 |

- measured_torque_in_use = 1 throughout. a_f is about 0 (+/-1.7 rad/s^2) from +0.9 s: the rate is constant, so the net torque is about 0, and the measurement shows this correctly (0.00). Motor 3 is commanded about 1.41x the others (0.709*u3 = u0), so the whole -0.08 command is spent cancelling the weak motor.
- The increment is not clipped (MC_INDI_DT_MAX 1.0). It equals the linear law (indi_rate_control.cpp:462-465): nu = 20 * (-4.4 rad/s) = -87 rad/s^2 (logged -83..-89), divided by G1 1757, gives -0.05. A rate error capped near 250 deg/s can therefore add only about 0.05 torque above the feedback torque t_fb.
- t_fb = t_f_meas + blend (indi_rate_control.cpp:356). t_f_meas is about 0, and the blend is a first-order low-pass of the model-minus-measured gap with MC_INDI_ACT_BLD = 1.0 s (cpp:336-341). It reaches only -0.02 at +0.7 s and -0.04 at +1.1 s. This blend is the law's only integral action while the measurement is in use; the comment at cpp:330-332 says so.
- The trim it has to catch grows: the outer loop ramps thrust sp from -0.15 to -0.64 by +1.1 s (vehicle falling at vz 2.4 m/s), and u3 rises from 0.29 to 0.82. The deficit of 0.29 * u3 grows proportionally, so the slow blend never catches it. The command stays at about the trim, net torque stays about 0, the positive rate persists and tilt crosses 60 deg at +1.1 s.
- Outer loop (indi_pos_status): a_c horizontal grows 0.9 -> 17 -> 45 m/s^2 and t_c reaches 9,8,-31. The thrust demand exceeds the 2x-hover availability: thrust sp reaches -1.0 at +1.8 s, and motor 3 saturates at +1.4 s with unallocated thrust -0.05 to -0.23. This comes after the tilt divergence: it worsens the end of the flight but does not start it. The attitude setpoint stays near level (2-16 deg) while the vehicle tilts, so rate setpoints stay pinned at -220 deg/s.
- Effectiveness loss: the 0.351 scale cuts true torque per unit command to 0.351, but G1 stays nominal. With measured feedback the effective inner bandwidth falls to about 0.54 K (from c = 0.351 c + nu/G1; this is my derivation, not checked against a log).

## Q3. Most likely cause, falsification, fix direction

Most likely cause: with measured-torque feedback, the INDI rate law has no fast integral action against an actuator command offset. Here the offset is the weak motor, which needs a command trim proportional to collective. The command is t_meas (true net torque, about 0) plus a 1 s low-passed model/measurement gap (indi_rate_control.cpp:336-357, MC_INDI_ACT_BLD 1.0), plus an increment of K*e/G1 (cpp:462-472). That increment is at most about 0.05 for the largest rate error the rate setpoint limit allows. When saturation (0.351) and the weak motor act together, motor commands roughly triple (u3 0.14 -> 0.82 in about 1 s), so the trim grows faster than the blend can follow. Alone, sat has no offset and weak needs a small trim at hover-level commands, which is consistent with each restored variant surviving. PID's rate integrator (I 0.06) and stiffer P (0.03 per rad/s vs 0.0114) carry the same trim. Neither stack saturates before INDI's tilt passes 60 deg.

Evidence: tau_sp of about -0.08 equals the trim while a_f and measured torque are about 0; t_fb (blend) lags at -0.04; the increment equals the unclipped linear value; rate setpoints are pinned at -220 deg/s while rates stay positive; there is no allocator saturation before +1.4 s.

What would falsify it:
- INDI joint re-flown with MC_INDI_ACT_BLD small (for example 0.1 s) or with measured feedback disabled (model-only t_f) still loses control with the same signature.
- Or the logged t_f_model vs t_f_meas gap does not hold about 0.08 by +1.0 s. The gap is not logged directly: indi_rate_status logs only t_fb.
- Or INDI sat-only and weak-only logs show a similarly lagging t_fb yet recover (not inspected here).

Candidate fix direction: give the rate law integral action that is not limited by the 1 s blend while the measurement is in use. Options are a faster or adaptive blend time constant, using the model path (commanded-torque feedback) for the low-frequency trim, or an explicit bounded integrator on the rate error with anti-windup tied to allocator saturation. Optionally scale G1 by the observed command-to-measured torque ratio so that increments remain effective under a collective loss. Separately, limit the outer-loop thrust and acceleration demand to the available thrust so the outer loop does not integrate a_c to 45 m/s^2.

Not verified:
- Single run per stack; no repeats.
- Fault times differ by 0.66 s, so the trajectory phase differs (PID was at 14.6 deg tilt at its fault, INDI at 4.5 deg).
- The direction of PID's attitude setpoint relative to the vehicle tilt.
- The sim weak-motor model (thrust vs rpm scaling) is inferred only from the rpm/command ratio.
- The model/measurement gap and blend state are inferred, not logged.
- The 0.54 K effective-bandwidth figure is analytic.
- The sat-only and weak-only INDI logs were not inspected.
- No firmware or sim was run.
