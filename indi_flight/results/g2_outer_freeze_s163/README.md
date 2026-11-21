# S163 G2 outer cells at the stage-6 freeze (D-FREEZE-6 plant)

Recipe: results/g2_outer_tb03_s151/fly.sh on base results/g5_freeze_s157/params.params, matched GNSS 110 ms, G4 typical
noise (--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0). z: AMP 0.04, TP 10, hover_long; xy: AMP 0.08, TP 20,
hover_xlong; NP 5, band 0.2-8 Hz. PT 0 = vel/pos break (stage input a_ref), PT 1 = INDI accel break (stage output t_c).
Command (repo root): `bash indi_flight/results/g2_outer_freeze_s163/batch.sh` (serial, 24 flights, skips done cells).
Margins: pinj_csv.py --margins (PT0 --point input, PT1 output). Holes: hole_report.py, 24/24 PASS. Table: table_s163.md.

| loop (2 seeds x 800/400) | PM deg range | GM dB range | DM s min | Ms max |
|---|---|---|---|---|
| vel/pos x, y (PT0 ax1/2) | 51.0-57.5 | 16.3-16.9 | 0.489 | 1.21 |
| accel x, y (PT1 ax1/2) | 54.0-67.7 | 16.6-17.3 | 0.665 | 1.20 |
| vel/pos z (PT0 ax3) | 66.1-70.9 | no -180 crossing in 0.2-8 Hz; abs L at 8 Hz <= -28.2 dB | 0.260 | 1.20 |
| accel z (PT1 ax3) | 62.3-64.2 | no -180 crossing in 0.2-8 Hz; abs L at 8 Hz <= -17.8 dB | 0.247 | 1.25 |
(The "FAIL" in table_s163.md for ax3 is the tabulator's NaN GM, not a margin failure.)
PM >= 45, GM >= 6 where a crossing exists, DM far above 2 periods (22.5 ms at the 88.9 Hz outer rate) + telemetry
latency: every cell meets the thresholds. xy PM seed spread up to 9 deg (pt1_ax1_r400 54.0/63.0), as in S87.
UNKEYED: no independent outer-cell margin script exists yet (STATE offline G2 todo). Also open: z GM statement needs
the phase plateau check (phase is not stored in margins.json), linear outer-loop model x-check.
