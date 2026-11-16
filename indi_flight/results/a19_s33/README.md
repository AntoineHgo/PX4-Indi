# A-19 (S33): what sets the per-run EKF2 yaw error

Scope: 15 speed-4 runs (hover, step_roll, traj_lemniscate x r1..r5) in `indi_flight/results/g16_set_s32/speed4`. Logs only, no sim run, no firmware edit. Script: `a19_mech.py`; full output: `a19_mech.json`, `a19_table.md`.
Convention: err = truth yaw minus EKF yaw (deg). Times are s relative to arm (arming_state 2, at ~30.0 s sim). Mag fusion: 3-axis from cs_mag_3d.

## Mechanism (two parts; part 1 quantitative, part 2 causal direction not proven)
1. Constant offset at mag yaw alignment. cs_yaw_align and cs_mag_hdg go true at arm-9.5 s in all 15 runs. EKF2_MAG_DECL = 3.406 deg (EKF2_DECL_TYPE = 3), and the EKF earth-field declination stays at 3.39-3.42 (hover/step). The sensor field, read through the truth attitude, has declination 2.62 deg (mean over 15 runs). Predicted err = -(3.41 - 2.62) = -0.79. Measured err at align+1 s = -0.86 +/- 0.10 (sd, n=15).
2. Spread across runs from the EKF magnetometer body-x bias state. The bias passes 1 mG within 0.6 s of the cs_mag_3d switch (+6.0 s) in 11 of 15 runs; 2 hover runs never do, 2 step runs do at 25-28 s. Across the 15 runs, err_winb = -0.85 - 295 * magB_x (deg, G); r = -0.998. Predicted sensitivity 1/H = 265 deg/G (H = 0.2166 G, horizontal field along body-y at this heading, so yaw and body-x bias nearly alias). Time-resolved over 0-35 s, r = -0.81 to -0.99 in every run. Scale check: the declination mismatch at alignment leaves H*(sin 3.41 - sin 2.62) = 3.0 mG on body x, the same order as the bias (-0.3 to -13 mG).
3. Large maneuvers (step_roll, traj_lemniscate) drive magB_x to -2 ... -13 mG after ~arm+25 s; err then moves to +0.1 ... +4.2 deg. Window b (15-35 s) for these groups mixes this transient (std 0.3-2.8 deg).
Ruled out or weak: GNSS yaw (cs_gnss_yaw never set in any run; no switch). No step at cs_mag_3d (pre/post 3 s windows differ by <0.2 deg in most runs). Gyro z bias: pooled r = +0.91 but within-group r = 0.29 / 0.77 / 0.15 (confounded with group). EKF decl state: r = -0.94 pooled but driven by group (3.24 traj vs 3.40 other).
gz world: SDF `<magnetic_field>` implies decl 14.6, incl 60.5, |B| 48.3 uT. The sensor sees decl 2.6, incl 63.1, |B| 48.0 uT. So the sensor field is not the SDF field as written (likely WMM from spherical_coordinates; gz source not read, unverified).

## Per-run table (err in deg; decl in deg; magB_x in mG, window b means)
| run | align s | mag3d s | err +1s | err arm | err winb (sd) | decl EKF | decl sens | magBx winb | magBx >1mG s | r 0-35s | slope deg/G |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hover/r1 | -9.51 | 6.01 | -1.02 | -1.00 | -0.95 (0.03) | 3.41 | 2.60 | +0.2 | none | -0.57 | -113 |
| hover/r2 | -8.32 | 6.06 | -0.97 | -0.92 | -1.41 (0.11) | 3.42 | 3.07 | +2.1 | 5.99 | -0.94 | -355 |
| hover/r3 | -9.22 | 6.03 | -0.85 | -0.81 | -0.63 (0.03) | 3.41 | 2.38 | -0.6 | 5.95 | -0.83 | -152 |
| hover/r4 | -8.64 | 6.05 | -0.90 | -1.00 | -0.68 (0.06) | 3.40 | 2.31 | -0.6 | none | -0.95 | -250 |
| hover/r5 | -8.38 | 6.03 | -0.90 | -0.96 | -1.18 (0.04) | 3.40 | 2.41 | +1.2 | 5.97 | -0.81 | -183 |
| step/r1 | -9.44 | 6.02 | -0.86 | -0.71 | -0.41 (0.43) | 3.39 | 3.12 | -1.7 | 6.58 | -0.96 | -261 |
| step/r2 | -9.70 | 6.05 | -0.85 | -0.87 | -0.84 (0.43) | 3.39 | 2.42 | +0.1 | 5.98 | -0.97 | -255 |
| step/r3 | -9.49 | 6.04 | -0.73 | -0.66 | -0.48 (0.28) | 3.39 | 2.48 | -1.5 | 24.7 | -0.94 | -246 |
| step/r4 | -9.71 | 6.00 | -0.77 | -0.83 | -0.68 (0.36) | 3.40 | 2.71 | -0.7 | 27.6 | -0.98 | -280 |
| step/r5 | -9.72 | 6.05 | -0.80 | -0.79 | -0.30 (0.43) | 3.39 | 2.64 | -2.1 | 5.98 | -0.99 | -278 |
| traj/r1 | -9.62 | 6.00 | -1.08 | -1.00 | +0.29 (2.80) | 3.24 | 2.53 | -3.7 | 5.94 | -0.99 | -305 |
| traj/r2 | -9.72 | 6.05 | -0.89 | -0.85 | +0.58 (2.74) | 3.23 | 2.72 | -4.7 | 5.98 | -0.99 | -298 |
| traj/r3 | -9.78 | 5.99 | -0.75 | -0.67 | +0.87 (2.61) | 3.24 | 2.62 | -5.8 | 5.92 | -0.99 | -310 |
| traj/r4 | -9.62 | 6.05 | -0.82 | -0.78 | +0.86 (2.48) | 3.24 | 2.86 | -5.6 | 5.98 | -0.99 | -304 |
| traj/r5 | -9.71 | 6.02 | -0.75 | -0.72 | +0.72 (2.77) | 3.24 | 2.40 | -5.3 | 5.95 | -0.99 | -301 |

Q1 answer: alignment is at -9.5 s (not at arm). Error at align+1 s and at arm agree within 0.1 deg in 14 of 15 runs (step/r1: 0.15); the window differs only through parts 2-3.
Q2: vehicle_magnetometer is logged at 2 Hz. Noise sd 0.0025-0.0035 G per axis (about the SDF 3e-7 T = 0.003 G, white). Pre-arm body mean ~ (0.010, -0.216, 0.429) G, i.e. |H| 0.2166 G, dip 63.1 deg.
Q4: EKF mag bias states (estimator_states 19-21) and estimator_sensor_bias mag_bias give identical numbers. Gyro z bias is not a driver (see above).

## Correlations (15 runs, y = err_winb)
- magB_x: r = -0.998, slope -295 deg/G, intercept -0.85 deg (intercept ~ the alignment offset).
- decl EKF: r = -0.94 (group-confounded); decl mismatch (EKF - sensor): r = -0.30; magB_y r = -0.46; magB_z r = -0.23.

## Fix candidate for the bench (SITL params; unverified until tested)
(a) Match the EKF declination to the sensor field: EKF2_DECL_TYPE = 0, EKF2_MAG_DECL = 2.6 (value of the field gz actually uses at lat 47.398, lon 8.546; confirm from gz before use). Removes the -0.8 deg offset (part 1).
(b) Stop body-bias drift: EKF2_MAG_B_NOISE = 0 (check the parameter minimum first). Removes part 2-3 if the bias is the only path.
Closing test: rerun the same 15 speed-4 scenarios (same seeds) with (a)+(b). Pass if |err at align+1 s| < 0.2 deg, |err_winb| < 0.3 deg in hover, and |magB_x| < 0.5 mG at 35 s in all 15 runs. Then run (a) alone on 5 runs to separate the two parts.

## Unverified / flags
- The quoted hover range (-0.59 to -1.54) is not reproduced. Current hover window b: -0.63 to -1.41. The S32 `a19_s32/a19_out.json` (older logs) gives analysis means -0.45 to -1.08. Source of the quoted range is unknown.
- Truth yaw in window b is 89.7-90.4 deg (circular mean); 90.0 holds only pre-arm.
- The EKF input sensor_mag (higher rate) was not analysed; the 2 Hz vehicle_magnetometer limits the pre-arm declination to about +/-0.25 deg per run.
- The 1/H aliasing is inferred from the slope (11% steeper than predicted); not derived from the EKF covariance.
- Causal direction (bias absorbs decl residual vs yaw absorbs bias) is not proven. gz field source not read.
