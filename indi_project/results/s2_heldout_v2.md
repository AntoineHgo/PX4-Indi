# Held-out set V, v2 controllers: verdict (session 42, PRELIMINARY until the seed-3 re-fly)

Batch: `bench/s2_heldout_v2.sh` (sec. 8 of `bench/scenarios.md`, frozen in session 36), 14 entries x 10 seeds x
{pid_default, pid_tuned (r1f c05, D-v2pid), indi_v2 (r2 c01, D-v2indi)}, 420 flights, 20:21-22:25 on 2026-11-14.
Table: `python3 indi_project/bench/s2_verdict.py` (paired per seed, Wilcoxon signed-rank, a = pid_tuned, b = indi_v2;
ratio = b/a of means; "b<a" = seeds where INDI is lower).

**Infrastructure fault.** The host suspended at 20:45:31 (journalctl: systemd-logind "The system will suspend now!")
while seed 3 of com_shift and motor_loss_0 was flying. All six runs of that (entry, seed), every controller, stalled
and ended in wall timeouts at 21:34:47 with no metrics. Per O-12 this is a setup/infrastructure fault, not a
controller failure: the six runs are kept in `results/s2_heldout_v2/runs_suspended/` and the (entry, seed) is re-flown
for all three controllers by `bench/s2_heldout_v2_refly.sh`, queued behind the seen set. Until then those two entries
have 9 paired seeds. With `--final` the stalled runs counted as failures for both controllers (1/1); that line is
superseded by this note. No other run of the batch failed.

## Table (12/14 entries complete, com_shift and motor_loss_0 on 9 seeds)

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
| com_shift | attitude_tracking.rotation_angle_rms_deg | 0.5237 | 0.2268 | 0.43 | 9/9 | 57 % | 0.00391 | 1.19 | 0/0 | better |
| motor_loss_0 | attitude_tracking.rotation_angle_rms_deg | 8.566 | 16.33 | 1.91 | 0/9 | -91 % | 0.00391 | 0.66 | 0/0 | **worse** |

Complete entries (10 paired seeds): 12/14
1. INDI failures in V: 0  (seen/T entries: see the seen set)
2. significantly better (>= 10 %, p < 0.05): 1/14 (needs >= 10)
3. significantly worse by > 10 %: 8 (needs 0)
4. hover effort (T1, v2): pending, pass --hover-runs results/s2_seen_v2/runs

Outcome on criteria 1-3 (V only; criterion 1 also needs the seen/T entries, criterion 4 hover): INDI does not outperform PID

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
- **motor_loss_0 1.91x worse** (rotation-angle RMS, 0/9 seeds). This is the opposite of v1 (T8: roll/pitch 5-9x
  better). Rotation-angle RMS includes yaw, which INDI already lost in v1, but a 1.9x ratio needs a cause before the
  report states one: open item, diagnose with per-axis attitude RMS on the existing logs.
- **Hover (v2_vib3_hover) 1.56x, 3/10 seeds**, p = 0.03: hover position RMS is the noise-dominated metric (D-hovernoise).
- **Baseline fairness check:** pid_tuned vs pid_default on V: tuned is better on every att entry (0.92-0.94x),
  gust_diag 0.80x, com_shift 0.65x, motor_loss_0 0.88x, equal on rate entries. The retuned PID is a genuinely
  stronger baseline on unseen scenarios, not an artefact of the tuning set.
