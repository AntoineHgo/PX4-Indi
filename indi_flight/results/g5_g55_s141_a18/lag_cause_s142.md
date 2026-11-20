# G5.5 o1 lag cause search (S142, analysis only, o1 seed 1 ULog)

Q1. o1 = lemniscate ax 5, ay 2.5, w 0.8485 rad/s (scenarios.py:27). Analytic jerk-xy p95 12.3 m/s^2/s (max 12.6),
so the needed rate p95 is jerk/g = 1.26 rad/s on the big axis (|jy|/g 1.24) and 0.39 on the small one (|jx|/g).
Measured omega_ff p95 inside the trajectory window (t 62-91 s): 1.22 on pitch, 0.32 on roll. Whole-log roll 0.31 is
the small axis (heading ~90 deg: roll ~ -ax, pitch ~ -ay). Ratio measured/needed: 0.98 pitch, 0.83 roll.
=> The ff magnitude is NOT undersized; the 0.31 was a heading-axis artefact.
Q2. Jerk source = difference of the setpoint acceleration (setpoint jerk is 0 for the bench stream: nonzero in 0.6 % of
samples, so j_ref=NaN, McIndiPosControl.cpp:1036-1038). updateJerkDifference indi_accel_control.cpp:150-187 (diff of
a_ff over dt_change, hold <= kJerkHold 0.1 s, header :75), then _lpf_j at MC_INDI_POS_LPF 10 Hz (:81,:186) = 16 ms.
omega_ff = j.y_b/c, -j.x_b/c, scale 1, clamp 3 rad/s (:437-438). No factor < 1.
Setpoint stream in the log: dt 30 ms (not 20 ms), so the difference is a 30 ms staircase (backward diff ~15 ms +
hold ~15 ms). Gate: age < 50 ms (IndiRateFeedforwardGate.hpp:47, .cpp:44), publish dt 11-12.5 ms: never stale.
Invalid 25 %: not gating flips. Invalid samples are settle and hold (valid 91.8 % in the traj window; the only
invalid run inside it is the last 2.7 s = hold start, 91.7-94.3 s). McIndiPosControl.cpp:301.
Measured delay of omega_ff after the derivative of the setpoint acceleration: 75 ms (pitch, corr 0.99), 110 ms (roll, 0.91);
sum of the above explains ~45-60 ms; the rest is unresolved (xcorr is weakly conditioned at 3.7 s period).
Q3. Stage filters: all at MC_INDI_POS_LPF 10 Hz (quad5in_indi_defaults.params; f_b, u, u_model, jerk: lib :78-81) =
16 ms each (they sit in parallel on the measurement path, t_c = a_c - g cancels them in the model/measured paths,
:333-337), MC_INDI_POS_DLY 1 sample, MC_INDI_POS_TB 1.0 s blend. Sum 16 + ~4 ms (1 cycle) ~ 20-25 ms: explains
under half of the ~50 ms.
Q4. Yes, a_ff is used but through the stock PositionControl: the INDI stage runs accel_only (McIndiPosControl.cpp:255), so
a_c = a_ref = local_position_setpoint.acceleration = stock (vel P/D + a_ff, :194,:243). Not attenuated by INDI; the
tracking lag then depends on the stock xy position/velocity gains and the stock velocity D filter.
Cross-corr (weak, hit the +-0.25 s search edge) puts roll_sp/pitch_sp ~250 ms behind the trajectory acceleration, and
omega_ff ~190 ms ahead of d(attitude_sp)/dt: i.e. the omega_ff and the attitude setpoint are misaligned by 100-190 ms.
