# S164 G2 outer cells: linear-model cross-check (xcheck)

Script: `python3 indi_flight/bench/g2_outer_model_s164.py` (no args; regenerates this file). Measured: S163 `*_margins.json` (freeze plant). Model margins use the same estimator (`margins_est.margins`, spline over the measured frequency bins 0.2-8 Hz), so the band is the same. Model is not tuned to these data.

## Model (one paragraph)

Small-signal hover, one axis, outer period T = 11.25 ms (88.89 Hz, S163 README). Block list, value, source: (1) velocity/position controller C = (Kvp + Kvi/s)(1 + Kp/s) + Kvd s Fd, xy: MPC_XY_P 0.95, MPC_XY_VEL_P/I/D_ACC 1.8/0.4/0.2; z: MPC_Z_P 1.0, MPC_Z_VEL_P/I/D_ACC 4.0/2.0/0 (the freeze params file does not set MPC_*: stock yaml defaults, `multicopter_position_control_gain_params.yaml`), structure from `PositionControl.cpp` lines 130-204 (the integrator acts on v_sp - v, so the factor (1 + Kp/s) multiplies both P and I; I forward-Euler with one-sample delay, D = backward difference then first-order alpha filter at MPC_VELD_LP 5 Hz, MPC_VEL_LP 0 and notch 0 = no velocity filter, `McIndiPosControl.cpp` 715-770); (2) ZOH of the stage output e^(-sT/2) (module rate; the stage runs in the same callback as PositionControl, so no further sample of delay); (3) INDI stage in accel_only mode (`McIndiPosControl.cpp:297`): t_c = t_f + a_c - a_f, t_f = z_b (-g_t u_f), a_f = R f_b,f + g, u_f = u_meas,f + b, b = LP_tb(u_model,f - u_meas,f), all measurement filters LowPassFilter2p at MC_INDI_POS_LPF 10 Hz sampled at 88.89 Hz, measurement delay MC_INDI_POS_DLY = 1 module sample, MC_INDI_POS_TB 0.3 s (freeze params, `indi_accel_control.cpp` 238-340); lateral axes: t_f and a_f use the same attitude R, so the increment (t_f - a_f)_lat = z_b,lat (u_f g_t - T_act,f) is second order at hover and the stage is an identity a_c -> t_c (E = 0, drag not modelled); vertical: E = F[z^-n M h (1-Bl) + Bl z^-(1+n) - M h] with n = 1 and rotor lag M = 1/(0.033 s + 1) (ASSUMED equal to MC_INDI_ACT_TC), so a_up/a_c = M h/(1-E); (4) attitude/thrust response for lateral axes Gatt = L/(1+L), L = wa e^(-s ta)/s, wa = 2 pi f_c and ta from the measured S162 attitude cell (f_c 1.385/1.40 Hz, PM 54.55/53.9 deg at 800/400, mean of roll+pitch, ASSUMPTION, this is the only place data enter the model); (5) plant integrator v = a/s; the EKF velocity is taken as transparent (see unsourced list). Loops: PT0 (break at a_ref) L0 = C (v/u)/(1-E); PT1 (break at t_c) L1 = C (v/u) - E; for xy E = 0 so the model predicts PT0 = PT1.

## Self-test

- known loop 5 e^(-0.1 s)/s: margins PM 61.35 (analytic 61.35), GM 9.94 (analytic 9.94)
- continuous C(s)/s vs margins_models.outer_factor (T195 key): max |1 + C/s - O| = 8.99e-14
- INDI increment E: |E(0.01 rad/s)| = 1.6e-04, max |E| over 0.01-50 rad/s = 0.265 (-11.5 dB)
- attitude L at 800: model f_c 1.38 Hz PM 54.5 (input 1.385, 54.55)
- attitude L at 400: model f_c 1.40 Hz PM 53.9 (input 1.4, 53.9)

Self-test verdict: PASS

## Results (measured = both seeds, x and y pooled for xy; worst = min over runs)

| loop | rate | model PM | meas PM worst / mean | dPM worst / mean | model GM | meas GM worst | dGM | model f_c | meas f_c mean | PM verdict | GM verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PT0 x/y | 800 | 53.5 | 52.4 / 54.8 | 1.1 / -1.3 | 11.7 | 16.8 | -5.1 | 0.30 | 0.29 | within 10 deg | OUT |
| PT0 x/y | 400 | 53.6 | 51.0 / 54.0 | 2.6 / -0.3 | 11.5 | 16.3 | -4.8 | 0.30 | 0.27 | within 10 deg | OUT |
| PT0 z | 800 | 59.5 | 66.1 / 68.3 | -6.7 / -8.9 | n/a | n/a | n/a | 0.69 | 0.72 | within 10 deg | agree: no -180 crossing (model top -28.9 dB vs measured -28.2 dB) |
| PT0 z | 400 | 59.5 | 67.9 / 69.4 | -8.5 / -10.0 | n/a | n/a | n/a | 0.69 | 0.72 | within 10 deg | agree: no -180 crossing (model top -28.9 dB vs measured -28.2 dB) |
| PT1 x/y | 800 | 53.5 | 59.7 / 62.9 | -6.2 / -9.4 | 11.7 | 16.8 | -5.0 | 0.30 | 0.23 | within 10 deg | OUT |
| PT1 x/y | 400 | 53.6 | 54.0 / 61.9 | -0.4 / -8.2 | 11.5 | 16.6 | -5.1 | 0.30 | 0.23 | within 10 deg | OUT |
| PT1 z | 800 | 57.3 | 62.3 / 63.2 | -5.0 / -6.0 | n/a | n/a | n/a | 0.66 | 0.67 | within 10 deg | agree: no -180 crossing (model top -12.0 dB vs measured -19.6 dB) |
| PT1 z | 400 | 57.3 | 63.8 / 64.0 | -6.6 / -6.7 | n/a | n/a | n/a | 0.66 | 0.70 | within 10 deg | agree: no -180 crossing (model top -12.0 dB vs measured -17.8 dB) |

Information (not used for verdict): model margins over a wide band 0.05-40 Hz, and with one extra sample of delay (T) in the loop.

| loop | rate | wide PM / GM / f_c | +1 sample PM / GM |
|---|---|---|---|
| PT0 x/y | 800 | 53.5 / -18.5 / 0.30 | 52.3 / 11.3 |
| PT0 x/y | 400 | 53.6 / -18.5 / 0.30 | 52.4 / 11.1 |
| PT0 z | 800 | 59.5 / -21.3 / 0.69 | 56.7 / 27.0 |
| PT0 z | 400 | 59.5 / -21.3 / 0.69 | 56.7 / 27.0 |
| PT1 x/y | 800 | 53.5 / -18.5 / 0.30 | 52.3 / 11.3 |
| PT1 x/y | 400 | 53.6 / -18.5 / 0.30 | 52.4 / 11.1 |
| PT1 z | 800 | 57.2 / -21.0 / 0.66 | 54.6 / 21.9 |
| PT1 z | 400 | 57.2 / -21.0 / 0.66 | 54.6 / 21.9 |

## Out-of-tolerance loops: likely unmodelled element

- PT0 x/y and PT1 x/y GM (model 11.5-11.7 dB vs measured about 16.3-17.3 dB, dGM -4.8 to -5.1 dB, outside 3 dB): the phase is right (model -180 crossing at 2.36 Hz at 800 Hz, measured 2.31-2.36 Hz; f_c 0.30 Hz vs 0.23-0.31 Hz) but |L| above 1 Hz falls about 10 dB faster in the measurement than in the model (at 2 Hz -15.3 vs -10.7 dB, 5 Hz -31.8 vs -24.3 dB, 8 Hz -45.1 vs -33.7 dB for PT0 ax1 r800 s1). Likely unmodelled element: the attitude/thrust response. The model lumps the S162 phase deficit into a pure delay (unity gain), whereas the real inner chain (attitude P, rate loop K = 20, rotor lag, INDI filters) is lag-like and attenuates, the gap grows with frequency as a first-order lag with a time constant of order 0.07 s would. Other candidates: the EKF velocity output (smoothing), rotor drag acting as extra velocity damping. This is a hypothesis, not tested here (the model was not refitted). Direction of the error is the safe one (model GM is lower than measured), as in A-36 for the attitude cells.
- PT1 x/y PM 800 (model 53.5 vs measured worst 59.7, d = -6.2 deg, mean larger): within 10 deg; the measured PT0 and PT1 xy differ by up to 8 deg in PM and by 0.07 Hz in f_c while the model predicts them identical (E = 0 laterally): the difference between cells is the lateral INDI increment (rotor drag, small tilt coupling), which is not modelled and is within seed spread (up to 9 deg, S163).
- z cells: PM within 10 deg (dPM -5.0 to -8.5, model lower, i.e. conservative); both model and measurement have no -180 crossing in 0.2-8 Hz, so GM is not comparable; model |L| at 8 Hz is -28.9 dB (PT0) and -12.0 dB (PT1) vs measured <= -28.2 and <= -17.8 dB. The model PT1 z is 6 dB above the measured top bin: the E term (blend/delay mismatch, vertical INDI increment) is likely overstated by the assumed rotor lag 0.033 s and unity thrust model, or the real z rotor/IMU chain has extra attenuation. The z PT1 measured phase is not stored in margins.json, so the phase-plateau check remains open (model wide-band phase crossings are listed in the information table).
- GATE reading: PM within 10 deg in all 8 rows; GM within 3 dB in 0 of 4 xy rows (dGM about -5 dB, explained above as an unmodelled attenuation of the thrust/attitude chain, model conservative), n/a (no crossing, agreement) in 4 z rows. Per the gate wording this is a difference to be explained, not yet explained by a test: it needs either the model with the real inner lag (rate loop + rotor model) or a measured attitude-to-acceleration FRF.

## Assumptions NOT sourced from the freeze params / firmware / a measurement

1. MPC_* gains are the stock yaml defaults: the freeze file does not set them (not confirmed against the flown `.params`; the per-run `.params` also carry no MPC_*).
2. Rotor lag 0.033 s taken from MC_INDI_ACT_TC (the controller's belief); the sim rotor time constant was not read. Affects z only.
3. Attitude closed loop = L/(1+L) with L = wa e^(-s ta)/s fitted to two numbers (f_c, PM) of the S162 attitude cell; ta is derived from that PM.
4. EKF velocity treated as transparent (no lag, no GNSS 110 ms delay, no GNSS/IMU complementary-filter dynamics). Near the 0.2-0.5 Hz crossover this is the least safe assumption.
5. Delay of the stage output = ZOH T/2 only; the att_control pick-up (<= 1.25 ms) and local_position publication latency are ignored. A +1 sample variant is listed as information.
6. Lateral INDI increment set to zero (no rotor/body drag, no blade flapping, thrust vector error second order at hover); a_f taken to be the true specific force with no IMU lag.
7. Vertical thrust model: g_t k_cmd = 1 (units of c), T_act = M c without nonlinearity (thrust ~ omega^2 vs u linear ignored); u_meas available fresh every module cycle (ESC telemetry rate not modelled).
8. MC_INDI_POS_DLY counted in module (88.89 Hz) samples; filter sample rate = module rate (`McIndiPosControl.cpp` 156-169 passes the measured rate); not verified for the delay unit.
9. Velocity-derivative filter is AlphaFilter with alpha = Ts/(Ts + 1/(2 pi fc)) (as in margins_models.alpha_coef, itself marked unverified).
