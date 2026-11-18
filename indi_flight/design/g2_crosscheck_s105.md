# G2 model-vs-measured cross-check, INDI v2 rate loop (S105, offline)

## Task 1. Model inputs flagged UNVERIFIED (read against PX4 source)
- AlphaFilter: `src/lib/mathlib/math/filter/AlphaFilter.hpp:69-79` setParameters: alpha = dt/(tau+dt); `setCutoffFreq` (:90-100) uses tau = 1/(2 pi fc); `updateCalculation` (:169) y += alpha (x - y). `bench/margins_models.py:59-63` alpha_coef = T/(T + 1/(2 pi fc)) and `tf_alpha` (:70-72) alpha/(1-(1-alpha) z^-1). MATCH. (Source also has `setCutoffFreq(float)` :103-107 with no alpha update; not used by the model.)
- LowPassFilter2p: `LowPassFilter2p.hpp:77-86`: fr = fs/fc, ohm = tan(pi/fr) (= tan(pi fc/fs)), c = 1 + 2 cos(pi/4) ohm + ohm^2, b0 = ohm^2/c, b1 = 2 b0, b2 = b0, a1 = 2 (ohm^2-1)/c, a2 = (1 - 2 cos(pi/4) ohm + ohm^2)/c. `margins_models.py:50-56` lpf2p_ba: identical expressions (k = 2 cos(pi/4) ohm). MATCH. Cutoff guard (:63-64, fc < fs/2) and the max(fc, 0.001 fs) clamp (:74) are not modelled; irrelevant at 40/20 Hz, 400/800 Hz.
- No fix needed. margins_models.py not edited. The docstring at :60 still says "read from memory ... UNVERIFIED"; this check removes that flag (docstring update is a cosmetic follow-up).
- Not checked here: the firmware wiring of the filters (a21 sec 2 table rows 2,3,6 says it matches; not re-read).

## Task 2. Model runs (bench/margins_models.py, margins_of, host python3, no simulation)
CLI only writes a1_prediction.md and margins_models_table.md (default configs, no roll HEAD config), so the library was called
directly (scratchpad script). Configs: `HEAD_FLIGHT` (meas path, Tb 0, n 1, tau_m 0.05, lead 1, att_p 8, sp_lead on, K 20, G1 320,
gyro 40 Hz, dgyro 20 Hz, tau_r 0.033, lat 0, g 1, eta 1); model-only = same with meas=False (d_m 0).

| fs | variant | GM dB | PM deg | DM ms |
|---|---|---|---|---|
| 800 | measured path, HEAD_FLIGHT | 14.93 | 66.7 | 40.3 |
| 800 | measured, att_p 0 | 15.65 | 83.9 | 54.1 |
| 800 | measured, lat 1 | 13.46 | 64.7 | 39.0 |
| 800 | measured, n 2 | 16.21 | 68.0 | 41.8 |
| 800 | model-only, HEAD_FLIGHT | 12.54 | 74.9 | 41.0 |
| 800 | model-only, att_p 0 | 13.07 | 88.1 | 48.7 |
| 800 | model-only, lat 1 | 10.66 | 71.3 | 38.6 |
| 400 | measured path, HEAD_FLIGHT | 14.98 | 65.8 | 40.6 |
| 400 | measured, lat 1 | 12.31 | 61.7 | 38.1 |
| 400 | measured, n 2 | 16.36 | 68.2 | 43.7 |
| 400 | model-only, HEAD_FLIGHT | 11.69 | 72.7 | 40.3 |
| 400 | model-only, lat 1 | 8.58 | 65.4 | 35.2 |
| 400 | model-only, d_m 1 | 12.91 | 75.3 | 42.6 |

The attitude path (att_p 8) is in the loop at M3a (it costs ~17 deg PM), so HEAD_FLIGHT is the right comparison config.
Pitch uses the roll model (same K 20, G1 320 normalised, att_p 8 assumed for MC_PITCH_P; g = G1_true/G1_set = 1 assumed, UNVERIFIED for pitch: MC_INDI_G1_P 1640 vs G1_R 1757 in the params files, model is normalised).

## Task 3. A-21
- `results/stage2_s41/a21_model_vs_measured.md` (S41 T85): INDI, ROLL axis, MODEL-ONLY actuator path, 800 Hz, `--sim v1` (Gazebo v1, no eRPM telemetry), G1_set 320 (before derived G1 1757), MC_INDI_ACT_TC default 0.02, no setpoint lead, firmware of S40/S41. Measured PM 24.0-25.3 deg / GM 4.3-6.0 dB vs as-coded model PM 42.7 / GM 6.1: ~17-18 deg PM gap.
- Cause found (a21 sec 1): the model lacked the attitude P loop (MC_ROLL_P 8, ~-16 deg phase at 4.5 Hz) and a gain g = 1.30 (G1_true/G1_set); a residual ~1 step delay/lag remained (a21 sec 1 item 3-4).
- ANOMALIES_CLOSED.md:12: A-21 CLOSED S48: model with attitude P loop and derived G1 matches S47 measurement within 1.3 deg PM / 0.6 dB GM; flight check tc33_p8/tc33_p3 within 3 deg PM, GM 2-3.5 dB optimistic ("unmodelled delay"). ANOMALIES.md has no open A-21 entry (grep returned only the CLOSED file line).
- Applies to the current v2 path? NO as a gap: it concerned v1/ACT_TC 0.02/G1 320 and was closed by the model fix (att loop + derived G1), which `HEAD_FLIGHT` includes (att_p 8, tau_m 0.05, sp_lead). The residual signature (model GM optimistic by 2-3.5 dB, ~1 step unmodelled delay) is the same one probed below by `lat 1`.

## Task 4. Cross-check table (measured = K100 primary, v2 path HEAD; model = Task 2)
| axis | path | Hz | seed | PM_meas | PM_model | dPM | GM_meas | GM_model | dGM | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| roll | measured | 800 | 1 | 68.2 | 66.7 | 1.5 | 15.89 | 14.93 | 0.96 | OK |
| roll | measured | 800 | 2 | 68.7 | 66.7 | 2.0 | 15.81 | 14.93 | 0.88 | OK |
| roll | measured | 400 | 1 | 70.0 | 65.8 | 4.2 | 13.12 | 14.98 | 1.86 | OK |
| roll | measured | 400 | 2 | 70.0 | 65.8 | 4.2 | 13.23 | 14.98 | 1.75 | OK |
| pitch | measured | 800 | 1 | 69.0 | 66.7 | 2.3 | 15.73 | 14.93 | 0.80 | OK |
| pitch | measured | 800 | 2 | 68.8 | 66.7 | 2.1 | 16.05 | 14.93 | 1.12 | OK |
| pitch | measured | 400 | 1 | 70.2 | 65.8 | 4.4 | 13.32 | 14.98 | 1.66 | OK |
| pitch | measured | 400 | 2 | 70.5 | 65.8 | 4.7 | 13.16 | 14.98 | 1.82 | OK |
| roll | model-only | 800 | 1 | 74.1 | 74.9 | 0.8 | 11.23 | 12.54 | 1.31 | OK |
| roll | model-only | 800 | 2 | 74.1 | 74.9 | 0.8 | 11.26 | 12.54 | 1.28 | OK |
| roll | model-only | 400 | 1 | 73.1 | 72.7 | 0.4 | 10.49 | 11.69 | 1.20 | OK |
| roll | model-only | 400 | 2 | 71.1 | 72.7 | 1.6 | 10.12 | 11.69 | 1.57 | OK |
| pitch | model-only | 800 | 1 | 73.8 | 74.9 | 1.1 | 11.19 | 12.54 | 1.35 | OK |
| pitch | model-only | 800 | 2 | 74.1 | 74.9 | 0.8 | 11.20 | 12.54 | 1.34 | OK |
| pitch | model-only | 400 | 1 | 72.4 | 72.7 | 0.3 | 10.25 | 11.69 | 1.44 | OK |
| pitch | model-only | 400 | 2 | 70.8 | 72.7 | 1.9 | 10.13 | 11.69 | 1.56 | OK |
| yaw | measured | 800 | 1 | 87.1 | n/a | - | 21.53 | n/a | - | NOT MODELLED |
| yaw | measured | 800 | 2 | 87.0 | n/a | - | 21.27 | n/a | - | NOT MODELLED |
| yaw | measured | 400 | 1 | 87.0 | n/a | - | 15.51 | n/a | - | NOT MODELLED |
| yaw | measured | 400 | 2 | 86.5 | n/a | - | 16.17 | n/a | - | NOT MODELLED |
| yaw | model-only | 800 | 1 | 91.0 | n/a | - | 18.43 | n/a | - | NOT MODELLED |
| yaw | model-only | 800 | 2 | 90.0 | n/a | - | 18.40 | n/a | - | NOT MODELLED |
| yaw | model-only | 400 | 1 | 89.6 | n/a | - | 17.84 | n/a | - | NOT MODELLED |
| yaw | model-only | 400 | 2 | 90.2 | n/a | - | 17.79 | n/a | - | NOT MODELLED |

Worst over the 16 modelled cells: |dPM| 4.7 deg (limit 10), |dGM| 1.86 dB (limit 3). Not representable: the 8 yaw cells (model is roll/pitch only, `margins_models.py:162`; no yaw K/G1/att config exists).

## Task 5. Conclusion
1. The linear model (HEAD_FLIGHT config, no fitting) cross-checks all 16 roll/pitch cells within tolerance: worst |dPM| 4.7 deg, |dGM| 1.86 dB.
2. The 8 yaw cells (4 measured, 4 model-only) have NO model cross-check; G2 cannot claim the 24/24 cross-check without a yaw model or an explicit waiver.
3. Pitch rides on the roll model with unverified assumptions (G1 normalised to 1, MC_PITCH_P 8); its agreement (same dPM/dGM range as roll) is supportive, not independent.
4. Model-only GM: model optimistic by 1.3-2.4 dB (12.54 vs 11.2 at 800; 11.69 vs 10.1-10.5 at 400), PM within 0.3-1.9 deg. Same sign as the A-21 closure residual (model GM optimistic, ~1 step unmodelled delay).
5. Measured-path 800 Hz: model slightly pessimistic (GM -0.9 to -1.1 dB, PM -1.5 to -2.3 deg). Measured-path 400 Hz: model GM optimistic +1.7/+1.9 dB, PM pessimistic by 4.2-4.7 deg: the model barely changes 800 to 400 (GM 14.9 vs 15.0) while measurements drop 2.7 dB.
6. Most likely unmodelled element: the rate dependence of the measured-torque path (telemetry/ESC latency taken as 0 and n = 1 sample): with n 2 the model GM goes 16.2/16.4 and PM 68.0/68.2, which fits 800 Hz PM but worsens 400 GM; lat 1 gives GM 13.5/12.3 and PM 64.7/61.7, which fits 400 GM but worsens PM. A latency fixed in ms (not samples) would explain both; UNVERIFIED, no fit done.
7. Eta x motor-state proxy and the filters: filters verified to match source (Task 1); the A-21 comparison found no element mismatch in filters, actuator discretisation or injection point. Eta is 1 in these cells, so the proxy is not exercised. Neither is the likely cause.
8. Model-only lat 1 over-corrects (400 Hz GM 8.58, PM 65.4), so a full-sample extra delay is too much; <= 1 sample at 400 Hz or ~1-2.5 ms is consistent. UNVERIFIED.
9. All differences are far inside the 10 deg / 3 dB tolerance, so the missing explanation does not affect the verdict for roll/pitch.
10. Caveat: measured numbers are single-estimator (K100/K101 second key shares the ulog); model numbers use the HEAD_FLIGHT defaults from margins_models.py without checking them against the S99/S100 params files beyond G1/ACT_TC 0.05/LEAD 1 (UNVERIFIED: MC_PITCH_P, G2_Y, IMU cutoffs).
