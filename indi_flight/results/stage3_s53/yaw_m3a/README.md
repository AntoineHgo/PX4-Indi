# S53: yaw M3a pre-test (ACT_TC 0.05, lead 1) -- NO MARGIN READ, anomaly A-27

Binary rebuilt at 7522625b0f (default ACT_TC 0.05), model-only path, quad5in, 800 Hz, MC_INDI_INJ_AX 3, AMP 0.008
(= 0.001 x G1_R/G1_Y, 1757/205, for the same excitation acceleration as roll), seed 1, yaw axis extracted.

- Pre-injection gate PASS (RMS 0.0047/0.0055/0.0003, pin 0); 18/18 bins accepted; injection logged as expected.
- |L| is -0.7 dB at 1 Hz and falls to -40 dB at 50 Hz; phase +157 deg at 1 Hz. No gain crossover in the band, so
  PM/GM/DM are NaN. Ms 8.2 dB at the lowest bin (1 Hz): |1 + L| = 0.39 there, suspicious if the sign is right.
- Next (A-27): bins down to 0.1 Hz and a yaw loop model (K_Y, G2_Y path, MC_YAW_P) before any yaw margin is quoted.
