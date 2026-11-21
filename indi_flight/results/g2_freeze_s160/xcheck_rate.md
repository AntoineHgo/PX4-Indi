# S165 G2: rate-loop and attitude-yaw cells at the stage-6 freeze, linear-model cross-check

Script: `python3 indi_flight/bench/g2_rate_model_s165.py` (`--selftest` for the synthetic check). Model: `margins_models.L_indi` / `L_indi_yaw` (sampled-data, att path closed for the M3a rate break), attitude yaw = MC_YAW_P 3 x closed yaw rate loop / s. Parameters only from the freeze params (K 20, ACT_TC 0.033, LEAD 1 -> c = 0.66, ACT_BLD 1 s, G2_Y/G1_Y 27/205, MC_ROLL/PITCH_P 8, MC_YAW_P 3, 1 sample measurement delay, gyro/dgyro LPF 40/20 Hz) and the airframe (rotor tc 33 ms). Not tuned. Margins with `margins_est.margins` on the measured bins (rate 1-50 Hz, attitude: log grid 0.2-20 Hz, 40 bins). Measured = mean over seeds (n), delta = model - measured mean. Agree = |PM| within 10 deg and |GM| within 3 dB for every seed (xcheck.md criterion).

| cell | measured GM dB / PM deg / f_c Hz | model GM / PM / f_c | delta | agree? |
|---|---|---|---|---|
| roll800 (n=3) | 18.9 / 56.4 / 3.27 | 17.6 / 58.4 / 3.68 | dGM -1.3 dB, dPM +2.0 (worst 2.2) | yes |
| roll400 (n=3) | 15.0 / 55.8 / 3.08 | 17.9 / 57.3 / 3.61 | dGM 2.9 dB, dPM +1.5 (worst 2.2) | NO |
| pitch800 (n=3) | 18.8 / 56.1 / 3.25 | 17.6 / 58.4 / 3.68 | dGM -1.2 dB, dPM +2.3 (worst 2.5) | yes |
| pitch400 (n=3) | 15.4 / 55.9 / 3.09 | 17.9 / 57.3 / 3.61 | dGM 2.6 dB, dPM +1.4 (worst 1.5) | yes |
| yaw800 (n=2) | 19.9 / 79.1 / 3.01 | 20.1 / 71.5 / 3.41 | dGM 0.3 dB, dPM -7.6 (worst 7.6) | yes |
| yaw400 (n=2) | 15.3 / 81.1 / 2.86 | 21.5 / 71.8 / 3.32 | dGM 6.2 dB, dPM -9.3 (worst 9.6) | NO |
| roll800 model-only (n=2) | 13.8 / 56.0 / 3.57 | 15.5 / 57.9 / 3.76 | dGM 1.7 dB, dPM +1.8 (worst 1.9) | yes |
| roll400 model-only (n=2) | 11.9 / 54.6 / 3.63 | 14.1 / 56.2 / 3.76 | dGM 2.2 dB, dPM +1.6 (worst 1.7) | yes |
| pitch800 model-only (n=2) | 13.8 / 55.8 / 3.56 | 15.5 / 57.9 / 3.76 | dGM 1.8 dB, dPM +2.1 (worst 2.1) | yes |
| pitch400 model-only (n=2) | 12.1 / 54.7 / 3.63 | 14.1 / 56.2 / 3.76 | dGM 2.0 dB, dPM +1.6 (worst 1.7) | yes |
| yaw800 model-only (n=2) | 18.0 / 76.1 / 3.29 | 17.9 / 70.7 / 3.47 | dGM -0.1 dB, dPM -5.4 (worst 5.4) | yes |
| yaw400 model-only (n=2) | 17.0 / 75.6 / 3.29 | 17.9 / 70.3 / 3.45 | dGM 0.8 dB, dPM -5.3 (worst 5.5) | yes |
| roll800 fwdef (n=3) | 16.2 / 54.3 / 1.81 | 17.1 / 65.9 / 1.96 | dGM 0.9 dB, dPM +11.6 (worst 11.6) | NO |
| att yaw 800 (n=2) | 30.5 / 81.4 / 0.47 | 29.9 / 82.2 / 0.47 | dGM -0.6 dB, dPM +0.8 (worst 0.8) | yes |
| att yaw 400 (n=2) | 30.9 / 81.4 / 0.48 | 28.5 / 81.8 / 0.47 | dGM -2.4 dB, dPM +0.4 (worst 0.4) | yes |

Agreement: 12/15 cell groups.
