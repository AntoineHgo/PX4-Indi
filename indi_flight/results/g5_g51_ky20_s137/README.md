# S137 G5.1 acro probe at MC_INDI_K_Y 20 (PROBE, RC113; re-fly at freeze)

Cause of the S136 acro yaw failure (results/g5_g51_s136, 15.0-16.0 deg/s > 10), read on the S136 logs:
- yaw rise t90 0.229 s on the +A edge = 2.3 tau of a first-order lag with tau = 1/K_Y = 0.1 s (K_Y 10);
  0.30 s on the -A reversal.
- no saturation: motor commands 0.08-0.19 (hover 0.137) on all 3 seeds, yaw torque setpoint |tz| <= 0.052;
  MC_INDI_YAW_CUT 0 (yaw low-pass bypassed).
- first-order arithmetic over the gate windows (+A 0.4 s, -A 0.4 s with a 200 deg/s jump, release 0.9 s; window
  starts 0.1 s after the edge): pooled RMS 15.5 deg/s predicted, 15.0-16.0 measured. K_Y 20 predicts about 4 deg/s.
- K_Y 10 was the archive default, never justified; roll/pitch use 20. Decision D-KY: default 20.

Probe: identical to the S136 batch (stick_steps, --stick-mode acro, --stick-pilot, quad5in, sim v2, speed 4, seeds
1-3), params.params = S136 params with MC_INDI_K_Y 20 (MC_INDI_ID_OK 1). Runner: run_batch.sh; checker g51_check.py
(self-test, keyed S136). Full lines: g51_summary.txt.

| seed | roll RMS | pitch RMS | yaw RMS | yaw rise t90 (+A, -A) s | tilt max | verdict |
|---|---|---|---|---|---|---|
| 1 | 1.44 | 1.48 | 3.29 | 0.103, 0.143 | 46.9 | PASS |
| 2 | 1.36 | 1.68 | 3.15 | 0.102, 0.140 | 47.1 | PASS |
| 3 | 1.43 | 1.77 | 3.19 | 0.103, 0.141 | 47.7 | PASS |

Limit 10 deg/s RMS; no LOC. Yaw authority cost (seed 1): lowest motor 0.044 on the -A reversal (0.083 at K_Y 10),
yaw torque setpoint -0.092; no motor at a limit. G2 yaw cells at K_Y 20: results/g2_yaw_ky20_s137 (pass).
Stabilized re-flown at K_Y 20 (same batch, MODES default now acro + stab): PASS 3/3, residual tilt <= 0.14 deg
(limit 3), yaw rate after release <= 0.15 deg/s (limit 10), tilt max 17.8 deg, no LOC. G5.1 row: PASS 6/6 (probe).
