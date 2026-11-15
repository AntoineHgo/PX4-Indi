# determinism_s12 notes

## Run 1 FAILED (exit 1)

run.json error: RunError: climb not finished by t=34.0 s (sim t=34.01); T_OFFBOARD_S=40.0 would slip

```
RUN FAILED: RunError: climb not finished by t=34.0 s (sim t=34.01); T_OFFBOARD_S=40.0 would slip
METRICS FAILED: no scenario window (no run.json window and no offboard span in log)
```

Runs 2 and 3 not started (stop-on-failure rule). No stray det_s12* containers before run 1.

## Try 1 cause (orchestrator)
px4.log: arm denied 20.0-24.0 s by "Preflight Fail: height estimate not stable"; armed 25.16 s; climb > 8.8 s missed the 34 s deadline. Constants moved: T_ARM_S 30 s, T_OFFBOARD_S 52 s. Try-1 output moved to results/det_s12_try1/.

## Try 2

Runs: `hover`, `pid_default`, `quad5in`, seed 1, speed 1, git commit 84b61e5c75 (dirty: false). All three runs exit 0, `exit_status` "ok", `metrics_status` "ok". Outputs in `indi_flight/results/det_s12/r{1,2,3}/`, stdout in `indi_flight/results/det_s12_r{1,2,3}_stdout.log`. No det_s12* container was running before the first run.

### run.json fields

| field | r1 | r2 | r3 |
|---|---|---|---|
| t_arm_sent_s | 30.0 | 30.0 | 30.004 |
| t_arm_us (s) | 30.280 | 30.612 | 30.596 |
| arm_attempts | 1 | 1 | 1 |
| t_climb_done_s | 40.068 | 39.600 | 39.864 |
| t_hold_s | 51.0 | 51.0 | 51.004 |
| t_offboard_sent_s | 52.0 | 52.0 | 52.004 |
| t_offboard_us (s) | 52.280 | 52.612 | 52.596 |
| hold_pos_ned [m] | (0.0091, -0.0014, -4.9859) | (0.0505, 0.0197, -5.0779) | (0.0196, -0.0060, -5.0224) |
| hold_yaw_rad | 1.58759 | 1.58966 | 1.58532 |
| wall_time_s | 105.3 | 105.6 | 105.6 |
| arm_late_s / offboard_late_s | not in run.json | not in run.json | not in run.json |

Arm time differs by 0.332 s between r1 and r2 with the same seed. The metrics window start has the same 0.332 s spread (see below), but I did not verify a causal link between the two.

### metrics.json spreads

33 numeric leaves, present in all three runs. Rel spread = (max - min) / |mean|. ILL = |mean| < 1e-3 or a position reference.

Top 15 by rel spread:

| leaf | r1 | r2 | r3 | rel % | flag |
|---|---|---|---|---|---|
| allocator.frac_any_actuator_saturation | 0 | 0 | 0 | inf | ILL (all zero) |
| allocator.frac_torque_not_achieved | 0 | 0 | 0 | inf | ILL (all zero) |
| effort.saturation_frac_high | 0 | 0 | 0 | inf | ILL (all zero) |
| effort.saturation_frac_low | 0 | 0 | 0 | inf | ILL (all zero) |
| effort.saturation_frac_motors | 0 | 0 | 0 | inf | ILL (all zero) |
| position.ref_ned[1] | -0.00141 | 0.01970 | -0.00605 | 631 | ILL (ref) |
| position.ref_ned[0] | 0.00909 | 0.05046 | 0.01962 | 157 | ILL (ref) |
| position.max_dev_horizontal_m | 0.03183 | 0.03419 | 0.04071 | 24.9 | |
| attitude_tracking.yaw_rms_deg | 0.01272 | 0.01583 | 0.01351 | 22.2 | |
| attitude_tracking.rotation_angle_rms_deg | 0.03347 | 0.03563 | 0.03989 | 17.7 | |
| position.max_dev_vertical_m | 0.02402 | 0.02048 | 0.02023 | 17.5 | |
| position.max_dev_3d_m | 0.03439 | 0.03818 | 0.04095 | 17.3 | |
| attitude_tracking.roll_rms_deg | 0.03050 | 0.03196 | 0.03423 | 11.6 | |
| position.rms_vertical_m | 0.00797 | 0.00722 | 0.00793 | 9.74 | |
| rate_tracking.roll_rms_rad_s | 0.00102 | 0.00100 | 0.00107 | 6.68 | |

Groups (leaves with rel % shown; abs spread in units of the leaf):

- rate_tracking: roll 6.68 %, pitch 2.13 %, yaw 3.57 % (ILL, mean < 1e-3).
- attitude_tracking: roll_rms 11.6 %, rotation_angle_rms 17.7 %, yaw_rms 22.2 %, pitch_rms 1.53 %.
- position: rms_3d 4.72 %, rms_horizontal 4.92 %, rms_vertical 9.74 %, max_dev_3d 17.3 %, max_dev_vertical 17.5 %, max_dev_horizontal 24.9 %; ref_ned[0], [1] ILL; ref_ned[2] 1.83 % (ILL, reference).
- effort: motor_rate_rms_per_s 2.72 %, motor_mean 0.012 %, motor_spread_mean_abs 2.06 % (ILL, mean < 1e-3); saturation fractions all 0 (ILL).
- window: start_s 55.280 / 55.612 / 55.596 (spread 0.332 s, 0.60 %); end_s spread 0.34 s; duration_s spread 0.008 s; offboard_span_s[1] spread 0.372 s.

### Comparison with session 11 (r1..r3)

Recomputed from `indi_flight/results/det_s11/r{1,2,3}/metrics.json` with the same script:

| quantity | s11 | s12 | direction |
|---|---|---|---|
| attitude roll_rms_deg rel spread | 37.4 % | 11.6 % | down |
| attitude rotation_angle_rms_deg rel spread | 23.8 % | 17.7 % | down |
| position rms_3d_m rel spread | 5.9 % | 4.72 % | down |
| position rms_vertical_m rel spread | 14.7 % | 9.74 % | down |
| rate roll_rms_rad_s rel spread | 8.1 % | 6.68 % | down |
| window.start_s spread | 3.3 s (brief) / 2.2 s (from s11 metrics.json, mean 35.49 s) | 0.332 s | down |

Caveats: the session 11 window start was about 35 s and this session's is about 55 s (T_ARM and T_OFFBOARD changed), so the two sessions are not like-for-like. The 3.3 s figure in the brief does not match the 2.2 s in the s11 files; I did not find the source of 3.3 s. Three samples give a rough spread estimate only.

### Determinism reading

Same seed, same commit, three runs: not identical. Arm time (0.33 s), climb-done time (39.6 to 40.07 s), and all metrics vary; the position reference and window start differ. The spreads are smaller than in session 11 for every quantity listed, but this session does not show bit-level or tolerance-level determinism. The G1.6 pass criterion is not defined in the files I read (not verified).

### Not verified

- arm_late_s and offboard_late_s are absent from run.json; I did not check the runner code that should write them.
- WARN lines in px4.log for r2 and r3 (not read). r1 px4.log WARN lines were read: system power unavailable, no GCS connection, no heading reference, height estimate not stable.
- The causal link between the arm-time spread and the window start spread.
- stdout logs, flight.ulg and sends.csv were not read.
- Session 11 numbers were recomputed from the files, not taken from a prior note.
