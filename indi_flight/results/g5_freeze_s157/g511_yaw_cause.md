# G5.11 yaw-reset tilt spike: cause (cause search only, no firmware edit)

Logs: g5_events_s1 (INDI), g5_events_s1_pid (PID). Reset instant from vehicle_attitude.quat_reset_counter increment:
INDI 22.590 s, PID 25.044 s in pyulog start-relative time (NOT 45.666 s as briefed; timebase differs, flagged, the event is the same counter edge).

## Samples (vehicle_attitude_setpoint, jump = angle of body z vs pre-reset mean)
INDI: t, tilt, jump, yaw_sp, att rc, local_pos hrc, a_f[0], t_c[0]
22.5825 0.33 0.25 90.61 1 1  +0.04 -0.05
22.5938 1.85 1.94 95.61 2 1  -0.29 +0.31   (spike; yaw_sp already +5 deg this cycle)
22.6050 1.53 1.62 95.61 2 2  -0.27 +0.24
22.6163 0.84 0.92 95.61 2 2  -0.18 +0.09
22.6275 0.29 0.30 95.61 2 2  -0.04 -0.02
PID: jump stays 0.26-0.46 deg through the reset (yaw_sp +5.0 at the same cycle as the INDI case).
Spike: 3 samples above 0.9 deg (about 30 ms), decaying. Input that changed: INDI measured acceleration a_f (indi_pos_status),
a 7-sigma step (pre/post-reset std of a_f[0] is 0.041; step is -0.33). t_f (measured thrust) and a_c did not change, so
t_c = t_f + (a_c - a_f) moved by the a_f step: 0.33/9.8 = 1.9 deg, equal to the spike.
Topics with 'indi': indi_pos_status, indi_rate_feedforward, indi_rate_status (PID log: none).

## Hypotheses
(d) geometric term: no. Pre-reset mean tilt 0.09 deg (PID 0.13), times 0.087 = 0.008 deg.
(b)/(c) frame or cycle mismatch: no. yaw_sp and attitude both change in the same cycle; local_pos hrc lags one cycle (22.5938 vs 22.6050) but q_d yaw is already correct, and the 1-cycle lag does not produce the tilt.
(a) a world-frame state not rotated: no. a_f = R f_bf + g is rotation-invariant about world z for a hover (a_f only rotates 5 deg, <=0.004).
Actual cause: the heading counter re-seeds the accel low-pass filter with a raw accelerometer sample.
Back-computed f_bf = R^T(a_f - g): (0.009,-0.065) at 22.5825 -> (0.03,0.263) at 22.5938, equal to raw vehicle_acceleration xyz
(0.03,0.263) at 22.590 (vibration is +-0.25 m/s^2 raw, filtered ~0.04), then decaying through the LPF (0.24, 0.15, 0.01, -0.07).

## Cause (file:line, confidence high for mechanism, medium-high that it is the whole spike)
- McIndiPosControl.cpp:859-867: reset_counters.heading is fed to _indi_reset_detector (EkfResetDetect.hpp:15,26 includes heading in the OR) -> _indi_reset_pending = true.
- McIndiPosControl.cpp:279-285: _indi.reset(_f_b, ...) -> indi_accel_control.cpp:125 _lpf_f.reset(f) seeds the 3D f_b low-pass with ONE raw noisy sample. a_f (line 341) then carries that noise, t_c (359) -> q_d tilt.
- Stock mc_pos_control has no accel filter state, hence 0.48 deg.
The reset is unneeded for heading: f_b is body-frame, the jerk difference a_ff is not changed by a yaw reset (setpoint yaw only).

## Fix
Remove heading from the stage reset trigger (do not set reset.heading in the detector at 864, or drop it from EkfResetDetect.hpp:26). If a reset is still wanted, seed with the filtered state (_last_f_b) instead of raw _f_b.
Unit test: EkfResetDetectTest: counters with only heading incremented -> update() must return false (fails today). Optional lib test in IndiAccelControlTest: converge on noisy f_b around hover, call reset(raw spike f_b), step once: |a_f - a_f_prev| < 0.05 (fails with reset(raw)).

## Unverified
No rerun with the fix; seeds 2 and 3 not inspected (same 1.78-1.94 expected from the same path); assumes EkfResetDetect.hpp:26 is as read (not opened in full); other resets (xy/z/vxy/vz) also reseed the filter from a raw sample and would show the same spike (xy/vxy/vz events in G5 not checked).
