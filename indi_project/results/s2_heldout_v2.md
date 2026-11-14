# Held-out set V, v2 controllers: verdict (session 42, FINAL in session 45)

Batch: `bench/s2_heldout_v2.sh` (sec. 8 of `bench/scenarios.md`, frozen in session 36), 14 entries x 10 seeds x
{pid_default, pid_tuned (r1f c05, D-v2pid), indi_v2 (r2 c01, D-v2indi)}, 420 flights, 20:21-22:25 on 2026-11-14.
Table: `python3 indi_project/bench/s2_verdict.py` (paired per seed, Wilcoxon signed-rank, a = pid_tuned, b = indi_v2;
ratio = b/a of means; "b<a" = seeds where INDI is lower).

**Infrastructure fault.** The host suspended at 20:45:31 (journalctl: systemd-logind "The system will suspend now!")
while seed 3 of com_shift and motor_loss_0 was flying. All six runs of that (entry, seed), every controller, stalled
and ended in wall timeouts at 21:34:47 with no metrics. Per O-12 this is a setup/infrastructure fault, not a
controller failure: the six runs are kept in `results/s2_heldout_v2/runs_suspended/` and the (entry, seed) is re-flown
for all three controllers by `bench/s2_heldout_v2_refly.sh`, queued behind the seen set. Until then those two entries
had 9 paired seeds. The re-fly ran 23:49 on 2026-11-14 (HELDOUT_V2_REFLY_DONE); all 14 entries now have 10 paired seeds. With `--final` the stalled runs counted as failures for both controllers (1/1); that line is
superseded by this note. No other run of the batch failed.

## Table (final, 14/14 entries, 10 paired seeds; session 45)

`python3 indi_project/bench/s2_verdict.py indi_project/results/s2_heldout_v2/runs --final --hover-runs indi_project/results/s2_seen_v2/runs`

| entry | primary metric | pid_tuned mean | indi_v2 mean | ratio | b<a | med impr | p | effort ratio | fails pid_tuned/indi_v2 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| v2_tau2_att | attitude_tracking.roll_rms_deg | 3.096 | 3.678 | 1.19 | 0/10 | -20 % | 0.00195 | 0.85 | 0/0 | **worse** |
| v2_tau2_rate | rate_tracking.roll_rms_rad_s | 0.413 | 0.3838 | 0.93 | 10/10 | 7 % | 0.00195 | 1.13 | 0/0 | better < 10 % |
| v2_asym_att | attitude_tracking.roll_rms_deg | 3.102 | 3.658 | 1.18 | 0/10 | -17 % | 0.00195 | 0.77 | 0/0 | **worse** |
| v2_asym_rate | rate_tracking.roll_rms_rad_s | 0.4051 | 0.374 | 0.92 | 10/10 | 8 % | 0.00195 | 1.15 | 0/0 | better < 10 % |
| v2_lat_att | attitude_tracking.roll_rms_deg | 3.126 | 3.63 | 1.16 | 0/10 | -16 % | 0.00195 | 0.76 | 0/0 | **worse** |
| v2_lat_rate | rate_tracking.roll_rms_rad_s | 0.3744 | 0.3462 | 0.92 | 10/10 | 7 % | 0.00195 | 1.09 | 0/0 | better < 10 % |
| v2_drop_att | attitude_tracking.roll_rms_deg | 2.959 | 3.54 | 1.20 | 0/10 | -20 % | 0.00195 | 0.75 | 0/0 | **worse** |
| v2_drop_rate | rate_tracking.roll_rms_rad_s | 0.375 | 0.3465 | 0.92 | 10/10 | 8 % | 0.00195 | 1.10 | 0/0 | better < 10 % |
| v2_vib3_hover | position.rms_3d_m | 0.02512 | 0.03919 | 1.56 | 3/10 | -54 % | 0.0273 | 0.99 | 0/0 | **worse** |
| v2_vib3_att | attitude_tracking.roll_rms_deg | 3.099 | 3.632 | 1.17 | 0/10 | -17 % | 0.00195 | 0.79 | 0/0 | **worse** |
| v2_sag_att | attitude_tracking.roll_rms_deg | 2.946 | 3.485 | 1.18 | 0/10 | -18 % | 0.00195 | 0.72 | 0/0 | **worse** |
| gust_diag | attitude_tracking.rotation_angle_rms_deg | 0.9495 | 0.8869 | 0.93 | 10/10 | 7 % | 0.00195 | 0.99 | 0/0 | better < 10 % |
| com_shift | attitude_tracking.rotation_angle_rms_deg | 0.5248 | 0.2273 | 0.43 | 10/10 | 57 % | 0.00195 | 1.20 | 0/0 | better |
| motor_loss_0 | attitude_tracking.rotation_angle_rms_deg | 8.56 | 16.33 | 1.91 | 0/10 | -91 % | 0.00195 | 0.67 | 0/0 | **worse** |

Complete entries (10 paired seeds): 14/14
1. INDI failures in V: 0  (seen/T entries: see the seen set)
2. significantly better (>= 10 %, p < 0.05): 1/14 (needs >= 10)
3. significantly worse by > 10 %: 8 (needs 0)
4. hover effort ratio (T1, v2): 1.26 (needs <= 1.5; n = 10/10)

Outcome on criteria 1-3 (V only; criterion 1 also needs the seen/T entries, criterion 4 hover): INDI does not outperform PID

Criterion 4 is the ratio of the 10-seed mean motor-rate effort on the seen-set hover runs (indi_v2/pid_tuned). The
median of the per-seed ratios is 1.64 (seen table below): one statistic passes, the other would not; the frozen rule is
the ratio of means.

## Reading

- **Outcome under the frozen criteria: INDI v2 does not outperform PID on V.** Criterion 3 fails on 8 entries;
  criterion 2 is met on 1/14 (needs 10). The re-fly of two seeds cannot change this (8 entries are worse on 10/10
  seeds with p = 0.002). Criteria 1 and 4 still need the seen set (`--hover-runs results/s2_seen_v2/runs`).
- **Pattern, not condition-specific.** On every attitude-pattern entry (tau x2, asymmetric motors, eRPM latency,
  eRPM drop-outs, vibration x3, battery sag) INDI's roll attitude RMS is 1.16-1.20x PID's, 0/10 seeds better, with
  0.72-0.85x the effort. On every rate-pulse entry INDI is 0.92-0.93x PID (10/10 seeds), below the 10 % bar, with
  1.09-1.15x effort. The ratios barely move across the six actuator/sensor perturbations, so the V perturbations are
  not what separates the controllers: it is the nominal step behaviour of the two tunings, the same split already
  seen on the tuning set (INDI better on rate pulses, worse on roll steps, D-v2indi). The INDI v2 attitude-step
  response is slower than tuned PID's and it spends less effort doing it; the tuning cost J traded these off.
- **Disturbances:** com_shift 0.43x (9/9 seeds, the v1 strength holds); gust_diag 0.93x (10/10, below 10 %).
- **motor_loss_0 1.91x worse** (rotation-angle RMS, 0/9 seeds); per axis: roll/pitch RMS 8.4 deg vs PID 0.8-0.9,
  yaw 11.7 vs 8.5. The opposite of v1 (T8: roll/pitch 5-9x better). Cause (`results/s2_tilt_diag.md`): after the
  fault, every indi_v2 seed settles at a steady 13-14 deg attitude error (PID < 0.3 deg). v2 INDI takes the actuator
  state from measured eRPM, so its fixed point is t_cmd - t_meas = nu/G1. Motor 0 now reaches only part of its command,
  and that gap (0.086 normalised torque) can only be held by a constant nu, i.e. a standing rate error, which the
  attitude loop turns into a tilt. v1 used a modelled actuator state (t_meas = filtered t_cmd), so the gap was
  integrated away. In v2 the measured actuator state removes INDI's implicit integral action against any
  command-to-output actuator mismatch. This is a structural property of the frozen v2 design, not a harness artefact.
  Seen-set seed 1 shows the same on motor_loss_2 (21.7 deg) and mismatch_combined_rate (36.7 deg).
- **Hover (v2_vib3_hover) 1.56x, 3/10 seeds**, p = 0.03: hover position RMS is the noise-dominated metric (D-hovernoise).
- **Baseline fairness check:** pid_tuned vs pid_default on V: tuned is better on every att entry (0.92-0.94x),
  gust_diag 0.80x, com_shift 0.65x, motor_loss_0 0.88x, equal on rate entries. The retuned PID is a genuinely
  stronger baseline on unseen scenarios, not an artefact of the tuning set.

## Seen set on the v2 controllers (O-7, reported, not part of the V verdict)

Batch `bench/s2_seen_v2.sh`, 14 entries x 10 seeds x 3 controllers, 420 flights, 2026-11-14 22:26-23:47. Three
(entry, seed) pairs re-flown for all controllers (D-v2-refly-seen: one estimator glitch found by `bench/glitch_scan.py`,
two simulator stalls); a second glitch scan over all 420 final runs is clean. Primary metrics as in the v1 summary
(report sec. 8.8). Table: `python3 indi_project/bench/s2_verdict.py indi_project/results/s2_seen_v2/runs --final --seen`.

| entry | primary metric | pid_tuned mean | indi_v2 mean | ratio | b<a | med impr | p | effort ratio | fails pid_tuned/indi_v2 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| hover | position.rms_3d_m | 0.0251 | 0.0344 | 1.37 | 1/10 | -24 % | 0.0488 | 1.64 | 0/0 | **worse** |
| step_roll | attitude_tracking.roll_rms_deg | 3.064 | 3.644 | 1.19 | 0/10 | -19 % | 0.00195 | 0.75 | 0/0 | **worse** |
| step_pitch | attitude_tracking.pitch_rms_deg | 3.852 | 3.205 | 0.83 | 5/10 | -0 % | 0.625 | 0.88 | 0/0 | n.s. |
| step_yaw | attitude_tracking.yaw_rms_deg | 13.77 | 15.87 | 1.15 | 1/10 | -25 % | 0.084 | 0.57 | 0/0 | n.s. |
| rate_step_roll | rate_tracking.roll_rms_rad_s | 0.3771 | 0.3503 | 0.93 | 9/10 | 8 % | 0.00391 | 1.09 | 0/0 | better < 10 % |
| traj_lemniscate | position.rms_3d_m | 2.552 | 2.674 | 1.05 | 0/10 | -5 % | 0.00195 | 1.01 | 0/0 | worse < 10 % |
| gust_x | attitude_tracking.rotation_angle_rms_deg | 1.053 | 0.7736 | 0.73 | 10/10 | 27 % | 0.00195 | 1.09 | 0/0 | better |
| payload_add | attitude_tracking.rotation_angle_rms_deg | 0.1294 | 0.1662 | 1.28 | 4/10 | -29 % | 0.322 | 1.02 | 0/0 | n.s. |
| mismatch_inertia | attitude_tracking.rotation_angle_rms_deg | 3.164 | 3.649 | 1.15 | 0/10 | -15 % | 0.00195 | 0.77 | 0/0 | **worse** |
| traj_circle_fast | position.rms_3d_m | 3.977 | 4.119 | 1.04 | 0/10 | -3 % | 0.00195 | 0.95 | 0/0 | worse < 10 % |
| motor_loss_2 | position.rms_3d_m | 4.394 | 13.78 | 3.14 | 0/10 | -222 % | 0.00195 | 0.29 | 0/0 | **worse** |
| mismatch_combined_att | attitude_tracking.roll_rms_deg | 3.097 | 3.681 | 1.19 | 0/10 | -18 % | 0.00195 | 0.71 | 0/0 | **worse** |
| mismatch_combined_rate | rate_tracking.roll_rms_rad_s | 0.3871 | 0.3677 | 0.95 | 10/10 | 5 % | 0.00195 | 1.25 | 0/0 | better < 10 % |
| step_diag | attitude_tracking.rotation_angle_rms_deg | 5.913 | 6.653 | 1.13 | 0/10 | -13 % | 0.00195 | 0.79 | 0/0 | **worse** |

Complete entries (10 paired seeds): 14/14
1. INDI failures in the seen set: 0  (seen/T entries: see the seen set)
2. significantly better (>= 10 %, p < 0.05): 1/14 (needs >= 10)
3. significantly worse by > 10 %: 6 (needs 0)

Reading: the seen set repeats the V pattern. INDI v2 is worse on every attitude-step entry (step_roll 1.19x,
mismatch_combined_att 1.19x, step_diag 1.13x, mismatch_inertia 1.15x) with 0.7-0.8x the effort and slightly better on
rate pulses (0.93-0.95x). It keeps a clear advantage only on gust_x (0.73x, 10/10). motor_loss_2 (v1 H4 double
failure, where both v1 controllers crashed) is 3.14x worse in position RMS: the tuned PID now holds it
(4.4 m), INDI v2 does not (13.8 m), the integral-action gap of `results/s2_tilt_diag.md` again. 0 run failures for
either controller in the seen set.
