# s8k: T5 with SENS_GNSS0_DELAY 0 (session 56, 2026-11-15)

Question: is the ~100 ms EKF-vs-ground-truth position offset of session 55 a timing artefact, and what does it do to the
T5 comparison? Script `bench/s8k_gnss_delay.sh`, analysis `bench/gt_lag.py` and `bench/s8_track_diag.py`. Seed 1,
v2 sim, seen entry T5 (traj_lemniscate): a diagnosis, not a verdict. Decision: D-s8-gnss-delay.

## Cause

`gt_lag.py` on the session-55 T5 logs (both controllers): ground truth lags the EKF by x +112 / y +92 / z +110 ms in
position but only +4..+14 ms in velocity and -8..-16 ms in attitude. Position and velocity ground truth come from the
same reception-stamped pose_info, so gz_bridge stamping is ruled out. `vehicle_gnss` has timestamp - timestamp_sample
= 110 ms while `sensor_gnss` (from `sensor_gps_sim`) has 0: `VehicleGPSPosition::resolveSampleTimestamp` applies the
stock SENS_GNSS0_DELAY 110 ms because the simulated driver stamps timestamp_sample == timestamp. The EKF treats a
zero-latency fix as 110 ms old and runs ahead of the truth by 110 ms x v.

## With SENS_GNSS0_DELAY 0

EKF vs ground truth lag (gt_lag.py): position x/y/z 0 / 0 / -20 ms (pid_tuned), +4 / +2 / -2 ms (INDI); attitude 0 ms.

| T5 seed 1 | GNSS delay | traj rms h [m] | rms v [m] | max 3d [m] | motor-rate effort | att rms [deg] | along mean / rms [m] | cross rms [m] | shift x / y [ms] |
|---|---|---|---|---|---|---|---|---|---|
| pid_tuned | 110 (s8j) | 0.378 | 0.030 | 1.17 | 0.591 | 7.21 | see s8j | | |
| indi_pos_v3_jlpf | 110 (s8j3) | 0.649 | 0.011 | 1.78 | 0.653 | 3.31 | +0.305 / 0.398 | 0.341 | +30 / +160 |
| pid_tuned | 0 | 0.383 | 0.024 | 1.00 | 0.628 | 8.04 | -0.539 / 0.598 | 0.271 | -110 / -210 |
| indi_pos_v3_jlpf | 0 | **0.262** | 0.011 | 0.91 | 0.704 (1.12x) | 3.93 | -0.097 / 0.117 | 0.083 | -40 / -20 |

(Shift: phase of the vehicle against the reference in the EKF frame, positive = ahead; along/cross on cruise samples
with |v_ref| > 1 m/s.)

## Reading

- pid_tuned is almost unaffected (0.378 -> 0.383 m). It lags the path by 110-210 ms (uncompensated rotor drag, no
  acceleration feedforward through the stock velocity loop), so a shifted estimate changes little.
- INDI POS goes from 0.649 to 0.262 m. The session-55 "lead" (+160 ms on y, a_c leading a_ref by 90 ms) was the
  controller tracking a position estimate that ran 110 ms ahead of the truth while its acceleration feedback (IMU,
  not delayed) had no such shift. With the delay matched, a_c follows the analytic a_ref within 20-30 ms, gain
  1.05-1.09, and the residual along-track lag is -0.10 m. Session 55's cascade-lead explanation (p/r ~
  1/(1 - j tau w^3/K)) is therefore NOT supported as the main cause of the gap. It may still explain the small residual.
- Effort: 1.12x pid_tuned, within the set-O hover criterion of 1.5x (which applies to hover, not T5).
- Consequence for the bench: the stock 110 ms configuration penalised the controller that tracks the estimate more
  tightly. Set O flies with `--gnss-delay 0` for every controller (D-s8-gnss-delay), after the O-13 pre-check is
  re-flown under it (`bench/s8l_o13_gnss0.sh`).
