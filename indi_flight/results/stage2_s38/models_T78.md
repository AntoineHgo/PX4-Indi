# T78 linear loop models (gate G2), summary

Files: `indi_flight/bench/margins_models.py`, self-test 4 in `indi_flight/bench/tests/test_margins_selftest.py`,
tables `a1_prediction.md`, `margins_models_table.md` (this directory, from `python3 bench/margins_models.py <out_dir>`).
GM/PM/DM come from `margins_est.margins()` (imported). Break M3a, y = -L x, x = u = c + d, y = c.

## What each function models
- `L_indi(w, fs, ...)`: sampled-data (z = e^{jwT}) INDI rate loop. L = K F Pn + H Va - t_f/u; model-only (`meas=False`, default)
  or measured + blend (`meas=True`; Tb <= 0 is pure measurement, discrete blend ab = T/(Tb+T)). Exact ZOH plant (tau_r),
  PX4 LPF2p biquad F (40 Hz), AlphaFilter (20 Hz), backward-difference derivative, model chain z^-1 (1-a_m)/(1-a_m z^-1) z^-d_m
  (input = previous setpoint, as `torque_allocated_prev`), measurement delay z^-n, extra command latency `lat` (default 0), `eta_m`.
- `L_pid(w, fs, ...)`: (Kp + Ki T z^-1/(1-z^-1)) F G1 Pn + Kd alpha F G1 Va (I from the previous cycle, D = -Kd a_f, G1 = 320 param).
- `L_indi_cont`, `L_pid_cont`: continuous version of note 4.1/4.2 (ZOH = T/2 delay, lags and delays as e^{-sT}).
- `simulate_loop`, `L_timedomain`: sample-by-sample difference equations, Schroeder multisine at the break, `ME.frf_periodic`.
- `a1_poly`, `lowfreq_pole`, `a1_table`, `models_table`: w_n/zeta polynomial, numeric dominant pole (secant on 1+L), the two tables.

## Deviations from the note, and why
1. Source check (`indi_rate_control.cpp`, `mc_indi_rate_control_params.yaml`): all defaults agree (ACT_TC 0.02, DELAY 0, K, H chain =
   LPF2p then alpha, blend ab = dt/(Tb+dt), Tb <= 0 = pure measurement). `a_f` = alpha(DGYRO) of the derivative of the LPF2p-filtered
   gyro (VehicleAngularVelocity.cpp:769-786), consistent with H = F alpha. Measured path is only used with MC_INDI_W_MAX set, so
   `meas=False` is the default here (note default n = 1 applies when meas=True).
2. Note 7.4 literal reduction (n = 0, A_m = A_r -> eta (K/s) F_w A_r for any eta, Tb) is FALSE for eta != 1: the model chain does not
   know eta (residual 0.46 relative in test). It holds when the model chain gain equals eta (`eta_m = eta`). Verified 2.4e-15 on `L_indi_cont`.
3. In the sampled-data model the reduction is NOT exact even then: a_f is the backward-difference average of the torque over [k-1,k],
   the model/measured torque is sampled at k (half-sample skew). Residual is first order in T (0.21, 0.108, 0.055 at 400/800/1600 Hz).
   So 1e-9 is tested on the continuous function, O(T) scaling on the sampled one. This skew is a real extra term in the model.
4. Continuous and sampled-data margins differ by about 0.2 dB / 0.4 deg / 0.7 ms at 800 Hz (model-only: GM 6.3 vs 6.1).

## Self-test 4 (all PASS, `ALL PASS` printed; tests 1-3 unchanged and passing)
(a) analytic vs time-domain L, 26 bins to 316 Hz at 800 Hz and 23 bins to 158 Hz at 400 Hz, 3 configs x 2 rates: max error printed 0.0000 dB / 0.0000 deg
(both implement the same equations, written separately; this proves coding consistency, not that the equations match the firmware).
(b) continuous reduction 2.4e-15, literal-7.4 negative control, sampled O(T). (c) 12 cells of Tb x eta: numeric dominant pole equals the
polynomial to <= 9e-6 relative (limit 5 %); w_n/zeta equal for zeta < 1.
(d) BREAK CHECK done and restored: replaced `- Tf` by `- 0.0 * Tf` (drops the whole t_f term, which includes the H mismatch) in `_assemble`:
test 4a FAILED (14.6 dB, 172 deg at 800 Hz model-only), exit 1; file restored (diff identical to backup), rerun ALL PASS. Only this one perturbation was tried.

## Key numbers (roll, from `margins_models_table.md`; GM dB / PM deg / DM ms; 800 / 400 / 267 Hz)
- INDI model-only, eta 1: 6.1/42.7/36.5 ; 5.8/41.6/35.2 ; 5.5/40.6/34.1 (f_c 3.3 Hz; eta 0.5: GM 3.1, PM 33.6 at 800 Hz)
- INDI measured Tb 0, n 1: 21.1/54.3/55.0 ; 34.8/54.2/55.3 ; 33.6/54.1/55.6
- INDI meas + blend Tb 0.1, eta 1: 18.4/48.3/48.4 ; 18.1/47.6/47.8 ; 17.9/46.9/47.4; eta 0.5: 16.3/52.2/108.7 ; 15.6/51.8/107.7 ; 15.0/51.5/107.0
- PID roll gains: 25.8/67.9/127.4 ; 25.1/67.7/126.9 ; 24.4/67.4/126.5 (f_c 1.5 Hz)
- All DM far above the requirement 2Ts + nTs (3.8 / 7.5 / 11.2 ms INDI). Margin is limited by the model-vs-plant lag mismatch term (tau_m 0.02 vs tau_r 0.033), not the delay.
- A-1 (Tb 0.1, eta 0.25-0.75): w_n 7.1-12.2, zeta 0.53-0.92; Tb 0.03 eta 0.25 zeta 0.52; Tb 1.0 overdamped, slow pole -1.0..-1.25 rad/s. Lowest margins in the
  grid: Tb 0.03 eta 0.25 (GM 2.5 dB, PM 29 deg, Ms 12.6 dB); Tb 0.1 eta 0.25 GM 7.0, PM 41. Tb 0.3-1.0 are better than Tb 0.1 at every eta (linear model only).

## UNVERIFIED
- AlphaFilter alpha = dt/(dt+tau): setCutoffFreq calls setParameters(dt, tau) (read), the alpha formula inside setParameters was not read.
- LPF2p coefficients written from memory of PX4 `LowPassFilter2p` (bilinear Butterworth), not diffed against the header.
- Plant: tau_r 0.033 single lag, no extra gz command/ESC latency (`lat` = 0), torque taken as proportional to rotor-speed lag; real bridge latency unknown.
- PID `i_factor`, integrator anti-windup, gain compression ignored (MC_GC_EN 0); no yaw spin-up term; single axis, no cross-coupling; no EKF/attitude loop.
- `eta`, `g` as pure scalings; the measurement path as eta * motor state (ESC rpm-to-torque dynamics not modelled).
- Time-domain bins limited to 1 Hz and up (Tp 5 s); not exercised at 267 Hz (fs*Tp non-integer; analytic only).
