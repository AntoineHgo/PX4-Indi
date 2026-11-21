# S177 G2 outer xy model at the freeze-7 xy gains

Firmware 7dd352bae2: the INDI position module uses MC_INDI_XY_P (1.9, position error -> velocity setpoint) and MC_INDI_XY_VP (3.6, velocity error -> acceleration) for xy in every mode. MPC_XY_VEL_I_ACC and MPC_XY_VEL_D_ACC are still used for xy (`McIndiPosControl.cpp` ~600-603), so Kvi 0.4 / Kvd 0.2 are unchanged. z unchanged (MPC_Z_*).

Commands (from repo root; model is the s164 model, only the xy Kp/Kvp changed):

- new gains: `python3 indi_flight/bench/g2_outer_model_s164.py --out <file>` (defaults 1.9 / 3.6; `--params <file>` reads MC_INDI_XY_P/VP)
- old gains: `python3 indi_flight/bench/g2_outer_model_s164.py --legacy-mpc --out <file>` (0.95 / 1.8; reproduces the s164 numbers)

Model margins, xy (PT0 = break at a_ref, PT1 = break at t_c; the model has E = 0 laterally, so PT0 = PT1). Same estimator and band (0.2-8 Hz bins) as s164. Rate is the attitude-cell rate (800 / 400 Hz).

| gains | rate | model PM (deg) | model GM (dB) | f_c (Hz) | +1 sample delay PM / GM |
|---|---|---|---|---|---|
| s164 old: MPC 0.95 / 1.8 | 800 | 53.5 | 11.7 | 0.30 | 52.3 / 11.3 |
| s164 old: MPC 0.95 / 1.8 | 400 | 53.6 | 11.5 | 0.30 | 52.4 / 11.1 |
| freeze-7: MC_INDI 1.9 / 3.6 | 800 | 46.0 | 7.9 | 0.62 | 43.5 / 7.5 |
| freeze-7: MC_INDI 1.9 / 3.6 | 400 | 46.3 | 7.8 | 0.62 | 43.7 / 7.3 |

Notes
- Predicted loss from the gain change: about -7.5 deg PM, -3.8 dB GM, crossover doubles (0.30 -> 0.62 Hz).
- The s164 measured columns (S163 flights, old gains: GM worst 16.3-16.8 dB, PM worst 51-60 deg) are NOT comparable to the freeze-7 prediction. The s164 xcheck found the model GM 5 dB below the measured one (safe direction); if that bias persists, measured freeze-7 GM would be about 12-13 dB. This is an extrapolation, not tested.
- The wide-band (0.05-40 Hz) GM output is -28 dB (a spurious low-frequency -180 crossing of the double-integrator region); only the 0.2-8 Hz estimator-band values above are meaningful, as in s164.
- Unchanged s164 assumptions apply (EKF velocity transparent, attitude lumped as pure delay from the S162 cell, no lateral INDI increment).
