# Owner review of the stage-8 implementation (2026-11-15, after session 51)

Scope: `src/lib/indi_accel_control` (2fcf22a017), `src/modules/mc_indi_pos_control` (5cc5fcd01f, cd0546173e),
`plan/s8_outer_loop_design.md`, `plan/s8_impl_spec.md`, `results/s8b_activation.md` and the vib0 hover
(98f835a9dc). Code read in full; signs derived by hand; topic rates measured in the activation ULogs.

## Verified correct

- Architecture: O-11 compliant (separate module, stock untouched, default off), same reference stream and
  take-off/landing for both arms.
- Law signs (NED/FRD): a_f = R f_b + g e_z; t_f = -G_T u_f z_b; t_c = t_f + (a_c - a_f) is Tal eq. 20.
- Jerk feedforward: from t = -c z_b, j = -c_dot z_b - c (w_y x_b - w_x y_b), so w_x = j.y_b / c and
  w_y = -j.x_b / c, as coded (`indi_accel_control.cpp:330-331`).
- Implicit integral: command = u_f / K_cmd + delta / (G_T K_cmd); a G_T or mass error only scales the increment
  gain, the measured thrust holds the steady state. The payload / mass x1.15 scenarios are the right test.
- Robustness: finite checks, static memory, bounded buffers, bumpless reset, 569-line gtest.

## Findings (most severe first)

1. **Accelerometer aliasing (critical, already diagnosed by the orchestrator, now confirmed).** The module runs at
   the local-position rate (125 Hz) and takes the latest `sensor_combined` sample (250 Hz, 4 ms average,
   IMU_INTEG_RATE 250). Rotor 1P at ~122.5 Hz (7350 rpm) is attenuated only ~35 % by the 4 ms average and
   subsampling at 125 Hz folds it to ~2.5 Hz, inside the outer-loop band; the 10 Hz LPF (run at 125 Hz) cannot
   remove it. Evidence, hover seed 1: attitude RMS 5.47 deg / position RMS 0.210 m with v2 vibration vs 0.33 deg /
   0.037 m with `--vib-acc 0`. Fix: integrate every `vehicle_imu` delta_velocity between cycles (or use
   `vehicle_acceleration`, filtered upstream at sensor rate) and give u the identical chain. The design draft's
   "raw source plus our own LPF" (sec. 6 Q2) is only valid if that LPF runs at the sensor rate. No comparison flight
   before this is fixed and re-checked with v2 vibration on.

2. **Measured-thrust delay in the wrong direction, unidentified (moderate).** `setMeasurementDelay` /
   `MC_INDIP_DLY` = 1 delays the eRPM mean u; the spec's reason is "eRPM arrives later than the accelerometer".
   Delaying the late signal increases the misalignment: if eRPM lags, the accelerometer path must be delayed. The
   value 1 is copied from the inner loop's MC_INDI_ERPM_DLY (identified at ~1 kHz, ~1 ms, D-erpmdly), but here one
   cycle is 8 ms. Fix: identify the a_f / t_f lag from hover or step logs by cross-correlation (as D-erpmdly), apply
   it to whichever signal leads, record it as a decision. Not tuned (O-5 rule).

3. **Accelerometer bias not removed (moderate, hardware-relevant).** The design says "bias-corrected"; the module
   feeds raw `sensor_combined` (`McIndiPosControl.cpp:427`), without `estimator_sensor_bias` /
   `estimator_states` accel bias. With no velocity integrator a bias b gives a steady position offset
   b / (K_pos K_vel), ~6 cm per 0.1 m/s^2 with the stock MPC gains; the stock PID's velocity integrator removes it.
   Fix: subtract the EKF accel bias (body frame) before the filter, or state the limitation in the report. Check the
   gz IMU bias model to know whether the sim exercises it.

4. **Failure fallback does not level (minor in sim, safety for real flight).** `hold()` after kMaxHoldCycles publishes
   zero body rates (`McIndiPosControl.cpp:323`, commented "level rates"): zero rates freeze the current tilt, so a
   tilted vehicle keeps accelerating sideways. Fix: command a level attitude with the last thrust through
   `_attitude_control`, or release control to the stock pipeline (mode failure). gtest the case.

5. **Feedforward added after the rate limits (minor).** `rates = _attitude_control.update(q) + omega_ff`
   (`McIndiPosControl.cpp:471`): the limit MC_*RATE_MAX is applied before the feedforward, so the sum can exceed it
   (bounded by kMaxOmegaFf = 3 rad/s). Fix: constrain the sum to the same limits.

6. **Attitude metric for INDI POS (known, open).** The module does not publish `vehicle_attitude_setpoint`; the
   attitude RMS of INDI POS runs may be computed against a stale stock setpoint. Publish q_d / thrust as
   `vehicle_attitude_setpoint` (logging only, the module owns the rates) or make metrics.py use `indi_pos_status`.
   Until then use position RMS for INDI POS.

## Pertinence (for the stage-8 freeze)

- Outer INDI's published advantage (Tal, Smeur) is drag and wind rejection at speed. Check what body / rotor drag
  the gz x500 actually applies before freezing O1-O7; if it is negligible, say so and rely on gust, payload, CoM
  and mass-mismatch entries, and do not expect the lemniscate / circle entries to discriminate.
- INDI POS adds a second accelerometer-noise path on top of the inner loop's 1/G1 path: expect the effort criterion
  to be structurally hard (judge it with D-hover-spread pooled medians).
- Apply O-13 when freezing (pid_tuned feasibility pre-check of every entry; only the verdict pair A vs D at 10
  seeds, B and C as labelled context with few seeds) and D-hover-spread (pooled effort medians, >= 10 flights).
