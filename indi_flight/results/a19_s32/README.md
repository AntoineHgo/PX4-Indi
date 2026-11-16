# A-19 check (session 32): truth-minus-EKF yaw offset, H1 vs H2

Files (all in this folder): `a19_check.py` (script), `a19_out.json` (full per-run output). No other file was changed.
Reproduce: `cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g16_sched_set_s26/speed4 && python3 -B /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a19_s32/a19_check.py hover/r{1,2,3,4,5}/flight.ulg step_roll/r{1,2,3,4,5}/flight.ulg --out /home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/a19_s32/a19_out.json --metrics-check hover/r1/flight.ulg step_roll/r1/flight.ulg`

## Verdict

- **H1 as stated (fixed convention or frame mismatch, identical offset in every run): REJECTED.** The offset is not
  constant across runs. Truth yaw is 90.0 deg in all 10 runs (circular mean of the pre-arm window), while the EKF yaw
  before arm is 90.55 to 91.03 deg. The 0.5 deg spread comes from the EKF side. A frame or convention mismatch would
  appear as a 90 or 180 deg offset or a sign flip, not as 0.5 to 1.0 deg, and roll and pitch truth-minus-EKF are
  within 0.02 deg (hover), so the frame mapping itself agrees.
- **H2 (real EKF heading error): SUPPORTED for the offset itself.** The yaw offset is on the EKF side, present at rest
  before arm (pre-arm -0.55 to -1.02 deg), constant within a run (hover window-b std 0.02 to 0.05 deg), and varies
  across runs (window-b mean -0.45 to -1.08 deg). It is not visible in the heading or magnetometer innovations, so the
  second part of H2 (it follows the innovation) is NOT supported.
- **Mechanism: undecided.** The logs cannot separate (i) a run-dependent heading error set at boot and not corrected by
  the mag fusion, from (ii) a constant reference offset (magnetic declination or field frame in the sim) that happens to
  show a run-dependent part. The EKF declination is identical across runs, so the declination setting does not explain
  the run-to-run spread.
- **Bound for the yaw metric:** |truth - EKF| yaw offset is 0.45 to 1.08 deg in all 10 runs; setpoint-minus-EKF yaw is
  at most 0.021 deg. Truth-based yaw tracking error is therefore dominated by an EKF heading offset of about -0.6 to -0.9 deg
  (mean -0.7 deg across 10 runs), not by the controller.
- **Attitude-metric gap (the ~15 %):** explained by the arccos form of the rotation angle, not by rotation-vs-Euler.
  See the gap section.

## Numbers

Window (a) = [arm-5 s, arm]; window (b) = [arm+15 s, arm+35 s]. Arm = first `vehicle_status` sample with
`arming_state == 2` (about 30.00 s in all runs). Yaw offsets are truth minus EKF, wrapped, in deg; mean (std).
Heading innovation mean in deg; r = Pearson correlation of the heading innovation with the window-b yaw offset.
Max |r| is the largest of the three mag-field innovation components against the yaw offset. Absolute EKF yaw is the
pre-arm circular mean, in deg.

| run | yaw TE (a) | yaw TE (b) | yaw setpoint-EKF (b) | roll TE (b) | pitch TE (b) | heading innov (b), r | max abs r mag innov | EKF yaw (a) |
|---|---|---|---|---|---|---|---|---|
| hover r1 | -0.716 (0.057) | -0.582 (0.028) | -0.001 | -0.002 | 0.006 | 0.100, r=0.002 | 0.09 | 90.716 |
| hover r2 | -0.822 (0.014) | -0.660 (0.026) | -0.000 | -0.009 | -0.003 | 0.096, r=-0.005 | 0.09 | 90.822 |
| hover r3 | -0.549 (0.025) | -0.445 (0.020) | -0.001 | 0.008 | -0.019 | 0.095, r=0.009 | 0.06 | 90.549 |
| hover r4 | -1.023 (0.031) | -1.079 (0.046) | 0.000 | 0.005 | -0.007 | 0.083, r=0.020 | 0.05 | 91.023 |
| hover r5 | -0.721 (0.023) | -0.645 (0.049) | 0.000 | 0.006 | 0.021 | 0.099, r=0.085 | 0.06 | 90.721 |
| step_roll r1 | -0.706 (0.033) | -0.447 (0.279) | 0.011 | 0.026 | 0.011 | 0.091, r=-0.164 | 0.20 | 90.706 |
| step_roll r2 | -0.708 (0.023) | -0.535 (0.257) | 0.010 | 0.025 | 0.001 | 0.084, r=-0.054 | 0.14 | 90.708 |
| step_roll r3 | -0.940 (0.018) | -0.601 (0.212) | 0.010 | 0.042 | 0.003 | 0.091, r=-0.081 | 0.30 | 90.940 |
| step_roll r4 | -0.860 (0.015) | -0.814 (0.605) | 0.021 | 0.031 | 0.010 | 0.087, r=-0.151 | 0.18 | 90.860 |
| step_roll r5 | -1.029 (0.017) | -0.649 (0.337) | 0.013 | 0.018 | 0.014 | 0.093, r=-0.003 | 0.15 | 91.029 |

Group summary (mean over runs, spread = std over runs):
- hover: pre-arm yaw offset -0.77 (spread 0.16); window-b yaw offset -0.68 (spread 0.21); setpoint-EKF yaw -0.0003
  deg; roll TE 0.002 deg; pitch TE -0.001 deg; heading innovation r mean 0.02.
- step_roll: pre-arm yaw offset -0.85 (spread 0.13); window-b yaw offset -0.61 (spread 0.12, within-run std
  0.21 to 0.61 deg); setpoint-EKF yaw 0.013 deg; roll TE 0.028 deg; pitch TE 0.008 deg; heading innovation r mean -0.09.

Notes on the numbers:
- The task quoted -0.65 deg (hover r1) and -0.37 deg (step_roll r3). Window (b) gives -0.58 and -0.60. The quoted
  values are not reproduced in this window; they probably come from another window (UNVERIFIED which).
- Pre-arm setpoint equals the EKF yaw exactly (the setpoint follows the EKF while disarmed), so pre-arm setpoint-minus-
  EKF is zero by construction and is not evidence for either hypothesis.
- Heading innovation mean is about +0.09 deg in every run, with no correlation to the offset in hover.
- Mag-innovation correlations: hover |r| is at most 0.09 for all 15 component pairs (sign mixed), so no link. In
  step_roll all 5 runs show a negative correlation with the yaw offset for innovation components 1 and 2
  (|r| 0.10 to 0.30). This is weak, sign-consistent, and only in the dynamic window; it accounts for part of the
  step_roll within-run spread, not for the mean offset. Autocorrelation makes the sample count (about 286) optimistic.

## Truth frame and sources checked

- `sim_ground_truth` q[0..3] and `vehicle_attitude` q[0..3] are both float32, Hamilton w-x-y-z.
- `src/modules/simulation/gz_bridge/GZBridge.cpp` (lines 709-718): truth is converted with `rotateQuaternion` before
  `sim_ground_truth` is published, the same body FRD to NED convention as the vehicle odometry (line 815). The body of
  `rotateQuaternion` was not read (UNVERIFIED).
- EKF parameters (from the ULog): `EKF2_DECL_TYPE=3` (geo-library declination, saved), `EKF2_MAG_DECL=3.406` deg.
  `estimator_status` mag inclination 63.24 to 63.27 deg (reference 63.16); strength 0.4807 to 0.4809 gauss (reference
  0.4824). Same home (47.397971, 8.546164) in all runs, so the declination is identical across runs.

## Attitude-metric gap (hover r1, window b)

- `bench/metrics.py` `att_track` computes the rotation angle as `2 * arccos(clip(|q_m . q_d|, 0, 1))` (also
  `estimator_error` for truth-minus-EKF). The per-axis RMS are Euler differences (yaw wrapped).
- Same window, same samples (n = 5333):
  - rotation angle (arccos form), metrics.py: **0.0493 deg**
  - per-axis RMS: roll 0.0440, pitch 0.0386, yaw 0.0125 deg
  - sqrt(sum of squared per-axis RMS): **0.0599 deg**
  - RMS of the Euler-error vector norm: 0.0599 deg (identical to the sqrt-sum, as it must be)
  - rotation angle with the stable atan2 form, 2*atan2(|vec(q_d* q_m)|, w): **0.0599 deg** (ratio 1.0000, RMS
    difference to the Euler norm 0.0000 deg)
  - arccos form: 33.8 % of samples have |dot| >= 1 and are clipped to a zero angle; mean angle 0.034 deg against
    0.052 deg for the stable form.
- The file `metrics.json` in the same run reports the same formula over its own window: rotation 0.04555, roll
  0.03877, pitch 0.03787, yaw 0.01349 deg. The sqrt-sum is 0.0558, so the ratio is 0.816 (the same ~18 %).
- step_roll r1 (window b): arccos 1.8910 vs sqrt-sum 1.8912 deg (ratio 0.9999); the gap disappears at larger angles.

Cause: a precision floor, not rotation-vs-Euler. For a 0.05 deg error, theta^2/8 is about 1.4e-7, which is at the
float32 quaternion resolution (about 6e-8 per component, see the float32 dtype above). The arccos of a dot product near
1 therefore clips to zero. The Euler-based total is exact (identity), and the stable rotation angle matches it to
4 decimals. So "rotation angle vs Euler components" is NOT a valid explanation at this error scale.

Fix suggestion (not applied; no file changed): in `att_track` and `estimator_error` (bench/metrics.py), compute the rotation
angle from the relative quaternion, `q_rel = conj(q_ref) * q`, sign-fixed to w >= 0, then `theta = 2*atan2(norm(q_rel[1:]),
q_rel[0])`. Effect: the hover attitude rotation metric rises about 18 % (0.046 to 0.056 deg), the truth-minus-EKF rotation
angle is affected the same way, and step_roll is unchanged (under 0.1 %). Bound on the affected size: below about 0.1 deg
the arccos form underestimates by up to ~20 %.

## Suggested fix or bound for A-19

- Bound the yaw metric: report truth-based yaw error as the closed-loop yaw error plus the per-run pre-arm offset, or
  against the EKF yaw. Use |offset| <= 1.1 deg (all 10 runs) as the bound on the EKF heading error.
- Discriminating test (not run; needs SITL, UNVERIFIED as a result): set `EKF2_MAG_DECL` to the sim world declination
  (value not checked) and repeat a hover pre-arm; if the pre-arm offset goes to zero, the constant part is a declination
  reference (H1-like). If it stays run-dependent, it is a heading error set at boot (H2). A same-seed pair with
  `EKF2_MAG_NOISE` lowered would show whether the spread follows the mag measurement noise.

## UNVERIFIED (not computed from the logs)

- The sim world magnetic declination and field frame (the truth-side reference).
- Correctness of `rotateQuaternion` in GZBridge (only the call site was read).
- The sim's mag measurement noise and its seed handling (EKF2_MAG_NOISE is the EKF tuning parameter, not the sim noise).
- Cause of the step_roll window-b yaw spread (0.2 to 0.6 deg std); not analysed beyond the mag-innovation correlation.
- Which window gives the quoted -0.65 deg (hover r1) and -0.37 deg (step_roll r3).
- Sign convention of `estimator_innovations.heading` (assumed measurement minus prediction).
- The ~0.09 deg positive mean heading innovation: its meaning is not checked.
